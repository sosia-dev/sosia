import pandas as pd
from collections import defaultdict
from string import Template
from time import sleep
from urllib.error import HTTPError

from pybliometrics.scopus import AuthorSearch, ScopusSearch
from pybliometrics.scopus.exception import Scopus400Error, ScopusQueryError,\
    Scopus500Error

from sosia.processing.extraction import get_authors, get_auth_from_df,\
    expand_affiliation
from sosia.utils import print_progress
from sosia.cache import authors_in_cache, cache_insert


def base_query(q_type, query, refresh=False, fields=None, size_only=False):
    """Wrapper function to perform a particular search query.

    Parameters
    ----------
    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    query : str
        The query string.

    refresh : bool (optional, default=False)
        Whether to refresh cached files if they exist, or not.

    fields : list of field names (optional, default=None)
        Fields in the Scopus query that must always present.  To be passed
         onto pybliometrics.scopus.ScopusSearch.  Will be ignored
         when q_type = "author".

    size_only : bool (optional, default=False)
        Whether to not download results and return the number
        of results instead.

    tsleep: float
        Seconds to wait in case of failure due to errors.

    Returns
    -------
    res : list of namedtuples (if size_only is False) or int
        Documents represented by namedtuples as returned from scopus or
        number of search results.

    Raises
    ------
    ValueError:
        If q_type is none of the allowed values.
    """
    params = {"query": query, "refresh": refresh, "download": not size_only}
    # Download query until server is available
    try:
        if q_type == "author":
            obj = AuthorSearch(**params)
        elif q_type == "docs":
            params["integrity_fields"] = fields
            obj = ScopusSearch(**params)
    except (AttributeError, Scopus500Error, KeyError, HTTPError):
        # exception of all errors here has to be maintained due to the
        # occurrence of not replicable errors (e.g. 'cursor', HTTPError)
        sleep(2.0)
        return base_query(q_type, query, refresh=True, fields=None,
                          size_only=size_only)
    if size_only:
        return obj.get_results_size()
    # Parse results, refresh once if integrity check fails or when server
    # sends bad results (in this case pause querying for a while)
    try:
        if q_type == "author":
            res = obj.authors or []
        elif q_type == "docs":
            res = obj.results or []
    except (AttributeError, Scopus500Error, KeyError, HTTPError):
        # exception of all errors here has to be maintained due to the
        # occurrence of not replicable errors (e.g. 'cursor', HTTPError)
        return base_query(q_type, query, refresh=True, fields=None,
                          size_only=size_only)
    return res


def count_citations(search_ids, pubyear, exclusion_key, exclusion_ids):
    """Auxiliary function to count non-self citations up to a year."""
    q_search_ids = " OR ".join(search_ids)
    joiner = " OR "
    if exclusion_key == "AU-ID":
        joiner = ") AND NOT AU-ID("
    q_exclusion_ids = joiner.join(exclusion_ids)
    s = Template("REF($search_ids) AND PUBYEAR BEF $pubyear AND NOT "
                 "$exclusion_key($exclusion_ids)")
    q = s.substitute(search_ids=q_search_ids, pubyear=pubyear,
                     exclusion_key=exclusion_key, exclusion_ids=q_exclusion_ids)
    # break query if too long
    if len(q) > 3785:
        mid = len(search_ids) // 2
        count1 = count_citations(search_ids[:mid], pubyear, exclusion_key,
                                 exclusion_ids)
        count2 = count_citations(search_ids[mid:], pubyear, exclusion_key,
                                 exclusion_ids)
        return count1 + count2
    return base_query("docs", q, size_only=True)


def query_author_data(authors_list, refresh=False, verbose=False):
    """Wrapper function to search author data for a list of authors, searching
    first in cache and then via stacked search.

    Parameters
    ----------
    authors_list : list
       List of Scopus Author IDs to search.

    refresh : bool (optional, default=False)
        Whether to refresh scopus cached files if they exist, or not.

    verbose : bool (optional)
        Whether to print information on the search progress.

    Returns
    -------
    authors_data : DataFrame
        A dataframe with authors data from AuthorSearch for the list provided.
    """
    authors = pd.DataFrame(authors_list, columns=["auth_id"], dtype="int64")
    # merge existing data in cache and separate missing records
    auth_done, auth_missing = authors_in_cache(authors)
    if auth_missing:
        params = {"group": auth_missing, "res": [],
                  "refresh": refresh, "joiner": ") OR AU-ID(",
                  "q_type": "author", "template": Template("AU-ID($fill)")}
        if verbose:
            print("Pre-filtering...")
            params.update({"total": len(auth_missing)})
        res, _ = stacked_query(**params)
        res = pd.DataFrame(res)
        cache_insert(res, table="authors")
        auth_done, _ = authors_in_cache(authors)
    return auth_done


def query_journal(source_id, years, refresh):
    """Get authors by year for a particular source.

    Parameters
    ----------
    source_id : str or int
        The Scopus ID of the source.

    years : container of int or container of str
        The relevant pulication years to search for.

    refresh : bool (optional)
        Whether to refresh cached files if they exist, or not.

    Returns
    -------
    d : dict
        Dictionary keyed by year listing all authors who published in
        that year.
    """
    try:  # Try complete publication list first
        q = "SOURCE-ID({})".format(source_id)
        if base_query("docs", q, size_only=True) > 5000:
            raise ScopusQueryError()
        res = base_query("docs", q, refresh=refresh)
    except (ScopusQueryError, Scopus500Error):  # Fall back to year-wise queries
        res = []
        for year in years:
            q = Template("SOURCE-ID({}) AND PUBYEAR IS $fill".format(source_id))
            params = {"group": [year], "res": [], "template": q,
                      "joiner": "", "q_type": "docs", "refresh": refresh}
            ext, _ = stacked_query(**params)
            if not valid_results(ext):  # Reload queries with missing years
                params.update({"refresh": True})
                ext, _ = stacked_query(**params)
            res.extend(ext)
    # Sort authors by year
    d = defaultdict(list)
    for pub in res:
        try:
            year = pub.coverDate[:4]
        except TypeError:  # missing year
            continue
        d[year].extend(get_authors([pub]))  # Populate dict
    return d


def query_year(year, source_ids, refresh, verbose, afid=False):
    """Get authors lists for each source in a list and in a particular year.

    Parameters
    ----------
    year : int
        The year of the search.

    source_ids : list
        List of Scopus IDs of sources to search.

    refresh : bool (optional)
        Whether to refresh cached files if they exist, or not.

    verbose : bool (optional)
        Whether to print information on the search progress.

    afid : bool (optional)
        If True, mantains information on the Scopus affiliation ID in res.
    """
    params = {"group": [str(x) for x in sorted(source_ids)],
              "joiner": " OR ", "refresh": refresh, "q_type": "docs"}
    if verbose:
        params.update({"total": len(source_ids)})
        print("Searching authors in {} sources in {}...".format(
            len(source_ids), year))
    q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(year))
    params.update({"template": q, "res": []})
    res, _ = stacked_query(**params)
    res = pd.DataFrame(res)
    if res.empty:
        return res
    res = res.dropna(subset=["author_ids"])
    if res.empty:
        return res
    grouping_cols = ["source_id", "year"]
    if afid:
        res = expand_affiliation(res)
        grouping_cols.append("afid")
    res["year"] = year
    res = (res.astype(str)
              .groupby(grouping_cols)[["author_ids"]]
              .apply(get_auth_from_df)
              .reset_index()
              .rename(columns={0: "auids"}))
    return res

def stacked_query(group, res, template, joiner, q_type, refresh,
                  i=0, total=None):
    """Auxiliary function to recursively perform queries until they work.

    Parameters
    ----------
    group : list of str
        Scopus IDs (of authors or sources) for which the stacked query should
        be conducted.

    res : list
        (Initially empty )Container to which the query results will be
        appended.

    template : Template()
        A string template with one paramter named `fill` which will be used
        as search query.

    joiner : str
        On wich the group elements should be joined to fill the query.

    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    refresh : bool
        Whether the cached files should be refreshed or not.

    i : int (optional, default=0)
        A count variable to be used for printing the progress bar.

    total : int (optional, default=None)
        The total number of elements in the group.  If provided, a progress
        bar will be printed.

    Returns
    -------
    res : list
        A list of namedtuples representing publications.

    i : int
        A running variable to indicate the progress.

    Notes
    -----
    Results of each successful query are appended to ´res´.
    """
    group = [str(g) for g in group]  # make robust to passing int
    q = template.substitute(fill=joiner.join(group))
    try:
        n = base_query(q_type, q, size_only=True)
        if n > 5000 and len(group) > 1:
            raise ScopusQueryError()
        res.extend(base_query(q_type, q, refresh=refresh))
        verbose = total is not None
        i += len(group)
        print_progress(i, total, verbose)
    except (Scopus400Error, Scopus500Error, ScopusQueryError) as e:
        # Split query group into two equally sized groups
        mid = len(group) // 2
        params = {"group": group[:mid], "res": res, "template": template,
                  "i": i, "joiner": joiner, "q_type": q_type, "total": total,
                  "refresh": refresh}
        res, i = stacked_query(**params)
        params.update({"group": group[mid:], "i": i})
        res, i = stacked_query(**params)
    return res, i


def valid_results(res):
    """Verify that each element ScopusSearch in `res` contains year info."""
    try:
        _ = [p for p in res if p.subtype == "ar" and int(p.coverDate[:4])]
        return True
    except:
        return False
