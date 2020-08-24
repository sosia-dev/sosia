from itertools import product
from string import Template

from pandas import DataFrame

from sosia.processing.caching import insert_data, retrieve_author_cits,\
    retrieve_authors_year, retrieve_sources
from sosia.processing.extracting import get_authors
from sosia.processing.filtering import filter_pub_counts
from sosia.processing.querying import base_query, count_citations,\
    query_authors, query_pubs_by_sourceyear, stacked_query
from sosia.processing.utils import build_dict, flat_set_from_df, margin_range
from sosia.utils import custom_print, print_progress


def find_matches(self, stacked, verbose, refresh):
    """Find matches within the search group.

    Parameters
    ----------
    stacked : bool (optional, default=False)
        Whether to combine searches in few queries or not.  Cached
        files will most likely not be reusable.  Set to True if you
        query in distinct fields or you want to minimize API key usage.

    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.

    refresh : bool (optional, default=False)
        Whether to refresh cached results (if they exist) or not. If int
        is passed and stacked=False, results will be refreshed if they are
        older than that value in number of days.
    """
    from sosia.classes import Scientist

    # Variables
    _years = range(self.first_year-self.year_margin,
                   self.first_year+self.year_margin+1)
    if self.period:
        _npapers = margin_range(len(self.publications_period), self.pub_margin)
        _ncits = margin_range(self.citations_period, self.cits_margin)
        _ncoauth = margin_range(len(self.coauthors_period), self.coauth_margin)
        _npapers_full = margin_range(len(self.publications), self.pub_margin)
        _ncits_full = margin_range(self.citations, self.cits_margin)
        _ncoauth_full = margin_range(len(self.coauthors), self.coauth_margin)
    else:
        _npapers = margin_range(len(self.publications), self.pub_margin)
        _ncits = margin_range(self.citations, self.cits_margin)
        _ncoauth = margin_range(len(self.coauthors), self.coauth_margin)
    text = "Searching through characteristics of "\
           f"{len(self.search_group):,} authors..."
    custom_print(text, verbose)

    # First round of filtering: minimum publications and main field
    # create df of authors
    authors = query_authors(self.search_group, self.sql_conn, verbose=verbose)
    same_field = authors['areas'].str.startswith(self.main_field[1])
    enough_pubs = authors['documents'].astype(int) >= int(min(_npapers))
    group = sorted(authors[same_field & enough_pubs]["auth_id"].tolist())
    text = f"Left with {len(group):,} authors with sufficient "\
           "number of publications and same main field"
    custom_print(text, verbose)

    # Second round of filtering:
    # Check having no publications before minimum year, and if 0, the
    # number of publications in the relevant period.
    params = {"group": group, "ybefore": min(_years)-1,
              "yupto": self.year, "npapers": _npapers,
              "yfrom": self.year_period, "verbose": verbose,
              "conn": self.sql_conn}
    group, _, _ = filter_pub_counts(**params)
    # Also screen out ids with too many publications over the full period
    if self.period:
        params.update({"npapers": [1, max(_npapers_full)], "yfrom": None,
                       "group": group})
        group, _, _ = filter_pub_counts(**params)
    text = f"Left with {len(group):,} researchers"
    custom_print(text, verbose)

    # Third round of filtering: citations (in the FULL period)
    authors = DataFrame({"auth_id": group, "year": self.year})
    auth_cits, missing = retrieve_author_cits(authors, self.sql_conn)
    if not missing.empty:
        total = missing.shape[0]
        text = f"Counting citations of {total:,} authors..."
        custom_print(text, verbose)
        missing['n_cits'] = 0
        print_progress(0, total, verbose)
        start = 0
        for i, au in missing.iterrows():
            n_cits = count_citations([str(au['auth_id'])], self.year+1)
            missing.at[i, 'n_cits'] = n_cits
            print_progress(i + 1, total, verbose)
            if i % 100 == 0 or i >= len(missing):
                insert_data(missing.iloc[start:i], self.sql_conn, table="author_ncits")
                start = i
    auth_cits = auth_cits.append(missing)
    auth_cits['auth_id'] = auth_cits['auth_id'].astype("uint64")
    # Keep if citations are in range
    custom_print("Filtering based on count of citations...", verbose)
    max_cits = max(_ncits)
    if self.period:
        max_cits = max(_ncits_full)
    mask = auth_cits["n_cits"].between(min(_ncits), max_cits)
    group = auth_cits[mask]['auth_id'].tolist()

    # Fourth round of filtering: Download publications, verify coauthors
    # (in the FULL period) and first year.
    text = f"Left with {len(group):,} authors\nFiltering based on "\
           "coauthors number..."
    custom_print(text, verbose)
    authors = DataFrame({"auth_id": group, "year": self.year}, dtype="uint64")
    _, author_year_search = retrieve_authors_year(authors, self.sql_conn)
    matches = []
    if stacked:  # Combine searches
        if not author_year_search.empty:
            q = Template(f"AU-ID($fill) AND PUBYEAR BEF {self.year + 1}")
            auth_year_group = author_year_search["auth_id"].tolist()
            params = {"group": auth_year_group, "res": [],
                      "template": q, "refresh": refresh,
                      "joiner": ") OR AU-ID(", "q_type": "docs"}
            if verbose:
                params.update({"total": len(auth_year_group)})
            res, _ = stacked_query(**params)
            res = build_dict(res, auth_year_group)
            if res:
                # res can become empty after build_dict if a au_id is old
                res = DataFrame.from_dict(res, orient="index")
                res["year"] = self.year
                res = res[["year", "first_year", "n_pubs", "n_coauth"]]
                res.index.name = "auth_id"
                res = res.reset_index()
                insert_data(res, self.sql_conn, table="author_year")
        authors_year, _ = retrieve_authors_year(authors, self.sql_conn)
        # Check for number of coauthors within margin
        if self._ignore_first_id or self.period:
            coauth_max = max(_ncoauth_full)
        else:
            coauth_max = max(_ncoauth)
        mask = authors_year["n_coauth"].between(min(_ncoauth), coauth_max)
        # Check for year of first publication within range
        if not self._ignore_first_id:
            same_start = authors_year["first_year"].between(min(_years), max(_years))
            mask = mask & same_start
        # Filter
        matches = sorted(authors_year[mask]["auth_id"].tolist())
    else:  # Query each author individually
        for i, auth_id in enumerate(group):
            print_progress(i + 1, len(group), verbose)
            res = base_query("docs", f"AU-ID({auth_id})", refresh=refresh)
            res = [p for p in res if p.coverDate and
                   int(p.coverDate[:4]) <= self.year]
            # Filter
            min_year = int(min([p.coverDate[:4] for p in res]))
            authids = [p.author_ids for p in res if p.author_ids]
            authors = set([a for p in authids for a in p.split(";")])
            n_coauth = len(authors) - 1  # Subtract 1 for focal author
            if self._ignore_first_id and (n_coauth < max(_ncoauth)):
                # Only number of coauthors should be big enough
                continue
            elif (self.period and ((n_coauth < max(_ncoauth)) or
                  (min_year not in _years))):
                # Number of coauthors should be "big enough" and first year
                # in window
                continue
            elif ((len(res) not in _npapers) or (min_year not in _years) or
                    (n_coauth not in _ncoauth)):
                continue
            matches.append(auth_id)

    if self.period:
        text = f"Left with {len(matches)} authors\nFiltering based on "\
               "exact period citations and coauthors..."
        custom_print(text, verbose)
        # Further screen matches based on period cits and coauths
        to_loop = [m for m in matches]  # temporary copy
        for m in to_loop:
            res = base_query("docs", f"AU-ID({m})", refresh=refresh,
                             fields=["eid", "author_ids", "coverDate"])
            pubs = [p for p in res if
                    self.year >= int(p.coverDate[:4]) >= self.year_period]
            coauths = set(get_authors(pubs)) - {str(m)}
            if not (min(_ncoauth) <= len(coauths) <= max(_ncoauth)):
                matches.remove(m)
                continue
            eids_period = [p.eid for p in pubs]
            n_cits = count_citations(eids_period, self.year+1, [str(m)])
            if not (min(_ncits) <= n_cits <= max(_ncits)):
                matches.remove(m)

    # Eventually filter on affiliations
    matches_copy = matches.copy()
    if self.search_affiliations:
        text = f"Left with {len(matches)} authors\nFiltering based on "\
               "affiliations..."
        custom_print(text, verbose)
        for auth_id in matches_copy:
            m = Scientist([str(auth_id)], self.year, period=self.period,
                          refresh=refresh, sql_fname=self.sql_fname)
            aff_ids = set(m.affiliation_id.replace(" ", "").split(";"))
            if not aff_ids.intersection(self.search_affiliations):
                matches.remove(auth_id)
    return matches


def search_group_from_sources(self, stacked=False, verbose=False, refresh=False):
    """Define groups of authors based on publications from a set of sources.

    Parameters
    ----------
    self : sosia.Original
        The object of the Scientist to search information for.

    stacked : bool (optional, default=False)
        Whether to use fewer queries that are not reusable, or to use modular
        queries of the form "SOURCE-ID(<SID>) AND PUBYEAR IS <YYYY>".

    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    Returns
    -------
    group : set
        Set of authors publishing in year of treatment, in years around
        first publication, and not before the latter period.
    """
    # Define variables
    search_sources, _ = zip(*self.search_sources)
    params = {"refresh": refresh, "verbose": verbose, "stacked": stacked}

    # Verbose variables
    text = f"Searching authors for search_group in {len(search_sources):,} sources..."
    custom_print(text, verbose)

    # Retrieve author-year-affiliation information
    sources_today = DataFrame(product(search_sources, [self.active_year]),
                              columns=["source_id", "year"])
    auth_today, missing = retrieve_sources(sources_today, self.sql_conn,
                                           refresh=refresh, afid=True)
    res = query_pubs_by_sourceyear(missing["source_id"].unique(), self.active_year,
                                   afid=True, **params)
    insert_data(res, self.sql_conn, table="sources_afids")
    auth_today = auth_today.append(res)

    # Authors active in year of treatment( and provided location)
    mask = None
    if self.search_affiliations:
        mask = auth_today["afid"].astype(str).isin(self.search_affiliations)
    today = flat_set_from_df(auth_today, "auids", condition=mask)

    # Authors active around year of first publication
    min_year = self.first_year - self.year_margin
    max_year = self.first_year + self.year_margin
    then_years = [min_year-1]
    if not self._ignore_first_id:
        then_years.extend(range(min_year, max_year+1))
    sources_then = DataFrame(product(search_sources, then_years),
                             columns=["source_id", "year"])
    auth_then, missing = retrieve_sources(sources_then, self.sql_conn,
                                          refresh=refresh)
    for y in missing["year"].unique():
        missing_sources = missing[missing["year"] == y]["source_id"].unique()
        res = query_pubs_by_sourceyear(missing_sources, y, **params)
        insert_data(res, self.sql_conn, table="sources")
    auth_then = auth_then.append(res)
    mask = auth_then["year"].between(min_year, max_year, inclusive=True)
    then = flat_set_from_df(auth_then, "auids", condition=mask)

    # Remove authors active before
    mask = auth_then["year"] < min_year
    before = flat_set_from_df(auth_then, "auids", condition=mask)
    today -= before

    # Compile group
    group = today
    if not self._ignore_first_id:
        group = today.intersection(then)
    return group
