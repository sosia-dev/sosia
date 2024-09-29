"""Module with functions for finding matches within a search group based on various criteria
such as publications, citations, coauthors, and affiliations.
"""

from itertools import product
from string import Template

import pandas as pd
from tqdm import tqdm

from sosia.processing.caching import insert_data, retrieve_author_info
from sosia.processing.filtering import filter_pub_counts, same_affiliation
from sosia.processing.getting import get_authors_from_sourceyear, get_authors
from sosia.processing.querying import count_citations, stacked_query
from sosia.processing.utils import build_dict, flat_set_from_df, margin_range
from sosia.utils import custom_print


def find_matches(original, stacked, verbose, refresh):
    """Find matches within the search group.

    Parameters
    ----------
    original : sosia.Original()
        The object containing information for the original scientist to
        search for.  Attribute search_group needs to exist.
    
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
    # Variables
    _years = range(original.first_year-original.first_year_margin,
                   original.first_year+original.first_year_margin+1)
    _npapers = margin_range(len(original.publications), original.pub_margin)
    _max_papers = max(_npapers)
    _ncits = margin_range(original.citations, original.cits_margin)
    _max_cits = max(_ncits)
    _ncoauth = margin_range(len(original.coauthors), original.coauth_margin)
    _max_coauth = max(_ncoauth)
    text = "Searching through characteristics of "\
           f"{len(original.search_group):,} authors..."
    custom_print(text, verbose)
    conn = original.sql_conn

    # First round of filtering: minimum publications and main field
    # create df of authors
    authors = get_authors(original.search_group, original.sql_conn, verbose=verbose)
    same_field = authors['areas'].str.startswith(original.main_field[1])
    enough_pubs = authors['documents'].astype(int) >= int(min(_npapers))
    group = sorted(authors.loc[same_field & enough_pubs, "auth_id"].tolist())
    text = f"Left with {len(group):,} authors with sufficient "\
           "number of publications and same main field"
    custom_print(text, verbose)

    # Second round of filtering:
    # Check having no publications before minimum year
    group = filter_pub_counts(
        group=group,
        ybefore=min(_years)-1,
        yupto=original.year,
        npapers=_npapers,
        verbose=verbose,
        conn=conn
    )
    text = f"Left with {len(group):,} researchers"
    custom_print(text, verbose)

    # Third round of filtering: citations
    authors = pd.DataFrame({"auth_id": group, "year": original.year})
    auth_cits, missing = retrieve_author_info(authors, conn, "author_ncits")
    if not missing.empty:
        total = missing.shape[0]
        text = f"Counting citations of {total:,} authors..."
        custom_print(text, verbose)
        missing['n_cits'] = 0
        start = 0
        for i, au in tqdm(missing.iterrows(), disable=not verbose, total=total):
            n_cits = count_citations([str(au['auth_id'])], original.year+1)
            missing.at[i, 'n_cits'] = n_cits
            if i % 100 == 0 or i == len(missing) - 1:
                insert_data(missing.iloc[start:i+1], conn, table="author_ncits")
                start = i
    auth_cits = pd.concat([auth_cits, missing])
    auth_cits['auth_id'] = auth_cits['auth_id'].astype("uint64")
    # Keep if citations are in range
    custom_print("Filtering based on count of citations...", verbose)
    mask = auth_cits["n_cits"].between(min(_ncits), _max_cits)
    group = auth_cits.loc[mask, 'auth_id'].tolist()

    # Fourth round of filtering: Download publications, verify coauthors
    # and first year
    text = f"Left with {len(group):,} authors\nFiltering based on "\
           "coauthor count..."
    custom_print(text, verbose)
    authors = pd.DataFrame({"auth_id": group, "year": original.year},
                           dtype="uint64")
    _, author_year_search = retrieve_author_info(authors, conn, "author_year")

    if not author_year_search.empty:
        q = Template(f"AU-ID($fill) AND PUBYEAR BEF {original.year + 1}")
        auth_year_group = author_year_search["auth_id"].tolist()
        params = {"group": auth_year_group, "template": q, "refresh": refresh,
                  "joiner": ") OR AU-ID(", "q_type": "docs",
                  "verbose": verbose, "stacked": stacked}
        res = stacked_query(**params)
        res = build_dict(res, auth_year_group)
        if res:
            # res can become empty after build_dict if an au_id is old
            res = pd.DataFrame.from_dict(res, orient="index")
            res["year"] = original.year
            res = res[["year", "first_year", "n_pubs", "n_coauth"]]
            res.index.name = "auth_id"
            res = res.reset_index()
            insert_data(res, original.sql_conn, table="author_year")
    authors_year, _ = retrieve_author_info(authors, conn, "author_year")
    # Check for number of coauthors within margin
    same_authcount = authors_year["n_coauth"].between(min(_ncoauth), _max_coauth)
    # Check for year of first publication within range
    same_start = authors_year["first_year"].between(min(_years), max(_years))
    # Filter
    mask = same_authcount & same_start
    matches = sorted(authors_year[mask]["auth_id"].tolist())

    text = f"Left with {len(matches)} authors"
    custom_print(text, verbose)

    # Eventually filter on affiliations
    if original.search_affiliations:
        text = "Filtering based on affiliations..."
        custom_print(text, verbose)
        matches[:] = [m for m in matches if same_affiliation(original, m, refresh)]
    return matches


def search_group_from_sources(original, stacked=False, verbose=False,
                              refresh=False):
    """Define groups of authors based on publications from a set of sources.

    Parameters
    ----------
    original : sosia.Original
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
        first publication, and not before them.
    """
    # Define variables
    search_sources, _ = zip(*original.search_sources)
    text = f"Defining 'search_group' using up to {len(search_sources):,} sources..."
    custom_print(text, verbose)

    # Retrieve author list for today
    sources_today = pd.DataFrame(product(search_sources, [original.active_year]),
                                 columns=["source_id", "year"])
    auth_today = get_authors_from_sourceyear(sources_today, original.sql_conn,
        refresh=refresh, stacked=stacked, verbose=verbose)
    mask = None
    if original.search_affiliations:
        mask = auth_today["afid"].isin(original.search_affiliations)
    today = flat_set_from_df(auth_today, "auids", condition=mask)

    # Authors active around year of first publication
    min_year = original.first_year - original.first_year_margin
    max_year = original.first_year + original.first_year_margin
    then_years = [min_year-1]
    then_years.extend(range(min_year, max_year+1))
    sources_then = pd.DataFrame(product(search_sources, then_years),
                                columns=["source_id", "year"])
    auth_then = get_authors_from_sourceyear(sources_then, original.sql_conn,
        refresh=refresh, stacked=stacked, verbose=verbose)
    mask = auth_then["year"].between(min_year, max_year)
    then = flat_set_from_df(auth_then, "auids", condition=mask)

    # Remove authors active before
    mask = auth_then["year"] < min_year
    before = flat_set_from_df(auth_then, "auids", condition=mask)
    today -= before

    # Compile group
    group = today.intersection(then)
    return {int(a) for a in group}
