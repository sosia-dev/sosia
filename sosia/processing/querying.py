"""Module with functions for querying and processing data from Scopus."""

from string import Template

import pandas as pd
from pybliometrics.scopus.exception import Scopus400Error
from tqdm import tqdm

from sosia.establishing import ScopusLogger
from sosia.processing.constants import AUTHOR_SEARCH_MAX_COUNT, QUERY_MAX_LEN, \
    RESEARCH_TYPES
from sosia.utils import custom_print


def base_query(q_type, query, refresh=False, view="COMPLETE", fields=None,
               size_only=False):
    """Wrapper function to perform a particular search query.

    Parameters
    ----------
    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    query : str
        The query string.

    refresh : bool or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If
            int is passed, results will be refreshed if they are older
            than that value in number of days.

    fields : list of field names (optional, default=None)
        Fields in the Scopus query that must always present.  To be passed
        onto pybliometrics.scopus.ScopusSearch.  Will be ignored
        when q_type = "author".

    size_only : bool (optional, default=False)
        Whether to not download results and return the number
        of results instead.

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

    from pybliometrics.scopus import AuthorSearch, ScopusSearch, init

    init()

    params = {"query": query, "refresh": refresh, "download": not size_only}

    if q_type == "author":
        params["count"] = AUTHOR_SEARCH_MAX_COUNT
        with ScopusLogger("Author Search", params) as sl:
            au = AuthorSearch(**params)
            sl.scopus_obj = au
        if size_only:
            return au.get_results_size()
        else:
            return au.authors or []
    elif q_type == "docs":
        params["integrity_fields"] = fields
        params["view"] = view
        if size_only:
            with ScopusLogger("Scopus Search", params) as sl:
                ss = ScopusSearch(**params)
                sl.scopus_obj = ss
            return ss.get_results_size()
        try:
            with ScopusLogger("Scopus Search", params) as sl:
                ss = ScopusSearch(**params)
                sl.scopus_obj = ss
            docs = ss.results or []
            docs = [d for d in docs if d.subtype in RESEARCH_TYPES]
            return docs
        except AttributeError:
            params.pop("integrity_fields")
            params["refresh"] = True
            with ScopusLogger("Scopus Search", params) as sl:
                ss = ScopusSearch(**params)
                sl.scopus_obj = ss
            docs = ss.results or []
            return docs


def count_citations(search_ids, pubyear, exclusion_ids=None):
    """Auxiliary function to count non-self citations up to a year."""
    if not exclusion_ids:
        exclusion_ids = search_ids
    exclusion_ids = [str(i) for i in exclusion_ids]
    q = f"REF({' OR '.join([str(i) for i in search_ids])}) AND PUBYEAR BEF "\
        f"{pubyear} AND NOT AU-ID({') AND NOT AU-ID('.join(exclusion_ids)})"
    # Download if too long
    if len(q) > QUERY_MAX_LEN:
        template = Template(f"REF($fill) AND PUBYEAR BEF {pubyear} AND NOT"
                            f" (AU-ID({') OR AU-ID('.join(exclusion_ids)}))")
        queries = create_queries(search_ids, " OR ", template, QUERY_MAX_LEN)
        res = []
        for q in queries:
            r = long_query(q, "docs", template, view="STANDARD")
            res.extend(r)
        res = pd.DataFrame(res)
        return res["eid"].nunique()
    return base_query("docs", q, size_only=True)


def create_queries(group, joiner, template, maxlen):
    """Create queries combining `maxlen` entities of a `group` to search for.

    Parameters
    ----------
    group : list
        Entities (authors, documents, etc.) to search for on Scopus.

    joiner : str
        On which the group elements should be joined to fill the query.

    template : string.Template()
        A string template with one parameter named `fill` which will be used
        as search query.

    maxlen : int
        The maximum length a query can be. If equal 1, one element at the time
        is used per query.

    Returns
    -------
    queries : list of tuples
        A list of tuples where the first element of each tuple is a query
        and the second is the list of elements searched by the query.
    """
    group = sorted([str(g) for g in group])
    queries = []
    start = 0
    for i, g in enumerate(group):
        sub_group = group[start:i+2]
        query = template.substitute(fill=joiner.join(sub_group))
        if maxlen == 1 or len(query) > maxlen or i+1 == len(group):
            sub_group = group[start:i+1]
            query = template.substitute(fill=joiner.join(sub_group))
            queries.append((query, sub_group))
            start = i + 1
    return queries


def long_query(query, q_type, template, *args, **kwargs):
    """Run one query from create_queries output, and revert to
    one-by-one queries of each element if Scopus400Error is returned.

    Parameters
    ----------
    query : str
        The query string.

    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    template : string.Template()
        A string template with one parameter named `fill` which will be used
        as search query.

    *args, **kwargs : tuple or dict (optional)
        Additional parameters to be passed to `base_query()`: `refresh`,
        and `view`.
    """
    try:
        return base_query(q_type, query[0], *args, **kwargs)
    except Scopus400Error:
        res = []
        for element in query[1]:
            q = template.substitute(fill=element)
            res = base_query(q_type, q, *args, **kwargs)
            res.extend(res)
        return res


def query_pubs_by_sourceyear(source_ids, year, verbose=False, *args, **kwargs):
    """Get authors lists for each source in a particular year.

    Parameters
    ----------
    source_ids : list
        List of Scopus IDs of sources to search.

    year : str or int
        The year of the search.

    verbose : bool or int (default = False)
        Whether to report on the progress of the process.

    *args, **kwargs : tuple or dict (optional)
        Additional options passed to stacked_query(): `stacked`, and
        `refresh`.
    """
    # Search authors
    msg = f"... parsing Scopus information for {year}..."
    custom_print(msg, verbose)
    q = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year}")
    res = stacked_query(
        group=[str(x) for x in sorted(source_ids)],
        joiner=" OR ",
        q_type="docs",
        verbose=verbose,
        template=q,
        *args, **kwargs
    )

    # Verify data is not empty
    dummy = pd.DataFrame(columns=["source_id", "year", "auids"])
    if res:
        res = pd.DataFrame(res).dropna(subset=["author_ids"])
        if res.empty:
            return dummy
    else:
        return dummy

    # Group data
    data = {"source_id": [],
            "year": year,
            "auids": []}
    for source_id, subset in res.groupby("source_id"):
        groups = subset["author_ids"].dropna().tolist()
        authors = sorted(set([item for sublist in groups for item in sublist.split(";")]))
        data["source_id"].append(int(source_id))
        data["auids"].append(";".join(authors))
    data = pd.DataFrame(data)
    return data


def stacked_query(group, template, joiner, q_type, stacked=False,
                  verbose=False, *args, **kwargs):
    """Auxiliary function to query list of items.

    Parameters
    ----------
    group : list of str
        Scopus IDs (of authors or sources) for which the stacked query should
        be conducted.

    template : string.Template()
        A string template with one parameter named `fill` which will be used
        as search query.

    joiner : str
        On which the group elements should be joined to fill the query.

    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    stacked: bool (optional, default=False)
        If True search for queries as close as possible to the maximum length
        QUERY_MAX_LEN.  If False, search elements in group one by one.

    verbose : bool (optional, default=False)
        If True, prints a progress bar for the download sections.

    *args, **kwargs : dict (optional)
        Additional options passed on to `long_query()`: `refresh`.

    Returns
    -------
    res : list
        A list of namedtuples representing publications.
    """
    maxlen = 1
    if stacked:
        maxlen = QUERY_MAX_LEN
    queries = create_queries(group, joiner, template, maxlen)
    res = []
    for q in tqdm(queries, disable=not verbose):
        res.extend(long_query(q, q_type, template, *args, **kwargs))
    return res

