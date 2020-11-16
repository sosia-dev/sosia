import pandas as pd
from string import Template

from pybliometrics.scopus.exception import Scopus400Error

from sosia.processing.utils import expand_affiliation, handle_scopus_errors
from sosia.processing.constants import QUERY_MAX_LEN
from sosia.utils import custom_print, print_progress


@handle_scopus_errors
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

    refresh : bool (optional, default=False)
        Whether to refresh cached files if they exist, or not.

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

    from pybliometrics.scopus import AuthorSearch, ScopusSearch

    params = {"query": query, "refresh": refresh, "download": not size_only}

    def create_obj(params):
        if q_type == "author":
            return AuthorSearch(**params)
        elif q_type == "docs":
            params["integrity_fields"] = fields
            params["view"] = view
            return ScopusSearch(**params)

    def get_res(obj, size_only):
        if size_only:
            return obj.get_results_size()
        elif q_type == "author":
            return obj.authors or []
        elif q_type == "docs":
            return obj.results or []

    obj = create_obj(params)
    return get_res(obj, size_only)


def count_citations(search_ids, pubyear, exclusion_ids=None, size_only=True):
    """Auxiliary function to count non-self citations up to a year."""
    if not exclusion_ids:
        exclusion_ids = search_ids
    q = f"REF({' OR '.join(search_ids)}) AND PUBYEAR BEF "\
        f"{pubyear} AND NOT AU-ID({') AND NOT AU-ID('.join(exclusion_ids)})"
    # Download if too long
    if len(q) > QUERY_MAX_LEN:
        template = Template(f"REF($fill) AND PUBYEAR BEF {pubyear} AND NOT"\
                            f" (AU-ID({') OR AU-ID('.join(exclusion_ids)}))")
        queries = create_queries(search_ids, " OR ", template, QUERY_MAX_LEN)
        res = []
        for q in queries:
            r = long_query(q, "docs", template, view="STANDARD")
            res.extend(r)
        res = pd.DataFrame(res)
        return len(res.eid.unique())
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
    group = sorted([str(g) for g in group])  # make robust to passing int
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


def long_query(query, q_type, template, view="COMPLETE"):
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

    view : str
        Which Scopus API view to use in the query.
    """
    try:
        return base_query(q_type, query[0], view=view)
    except Scopus400Error:
        res = []
        for element in query[1]:
            q = template.substitute(fill=element)
            res = base_query(q_type, q)
            res.extend(res)
        return res


def query_pubs_by_sourceyear(source_ids, year, stacked=False, refresh=False,
                             verbose=False):
    """Get authors lists for each source in a particular year.

    Parameters
    ----------
    source_ids : list
        List of Scopus IDs of sources to search.

    year : str or int
        The year of the search.

    stacked : bool (optional, default=False)
        Whether to use fewer queries that are not reusable, or to use modular
        queries of the form "SOURCE-ID(<SID>) AND PUBYEAR IS <YYYY>".

    refresh : bool (optional, default=False)
        Whether to refresh cached files if they exist, or not.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.
    """
    # Dummy return value
    columns = ["source_id", "year", "auids", "afid"]
    dummy = pd.DataFrame(columns=columns)

    # Search authors
    msg = f"... parsing Scopus information for {year}..."
    custom_print(msg, verbose)
    q = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year}")
    params = {"group": [str(x) for x in sorted(source_ids)],
              "joiner": " OR ", "refresh": refresh, "q_type": "docs",
              "template": q, "verbose": verbose, "stacked": stacked}
    res = stacked_query(**params)

    # Verify data is not empty
    if res:
        res = pd.DataFrame(res).dropna(subset=["author_ids"])
        if res.empty:
            return dummy
    else:
        return dummy

    # Group data
    res = expand_affiliation(res)
    if res.empty:
        return dummy
    res["year"] = year
    res["author_ids"] = res["author_ids"] + ";"
    grouping_cols = ["source_id", "year", "afid"]
    res = (res.groupby(grouping_cols)[["author_ids"]].apply(sum)
              .reset_index()
              .rename(columns={"author_ids": "auids"}))
    res["auids"] = res["auids"].str.strip(";")
    return res


def stacked_query(group, template, joiner, q_type, refresh, stacked, verbose):
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

    refresh : bool
        Whether the cached files should be refreshed or not.

    stacked: bool
        If True search for queries as close as possible to the maximum length
        QUERY_MAX_LEN.  If False, search elements in group one by one.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    res : list
        A list of namedtuples representing publications.
    """
    maxlen = 1
    if stacked:
        maxlen = QUERY_MAX_LEN
    queries = create_queries(group, joiner, template, maxlen)
    total = len(queries)
    print_progress(0, total, verbose)
    res = []
    for i, q in enumerate(queries):
        print_progress(i+1, total, verbose)
        res.extend(long_query(q, q_type, template))
    return res


def valid_results(res):
    """Verify that each element ScopusSearch in `res` contains year info."""
    try:
        _ = [p for p in res if p.subtype == "ar" and int(p.coverDate[:4])]
        return True
    except:
        return False
