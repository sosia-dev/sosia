from collections import defaultdict
from string import Template
import urllib
from time import sleep
import pandas as pd

from scopus import AuthorSearch, ScopusSearch
from scopus.exception import Scopus400Error, ScopusQueryError,\
    Scopus500Error, Scopus404Error, Scopus429Error
    
from sosia.processing.extraction import get_authors, get_auth_from_df
from sosia.utils import print_progress


def query(q_type, q, refresh=False, tsleep=0):
    """Wrapper function to perform a particular search query.

    Parameters
    ----------
    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    q : str
        The query string.

    refresh : bool (optional, default=False)
        Whether to refresh cached files if they exist, or not.

    tsleep: float
        Seconds to wait in case of failure due to errors.

    Returns
    -------
    res : list of namedtuples
        Documents represented by namedtuples as returned from scopus.

    Raises
    ------
    ValueError:
        If q_type is none of the allowed values.
    """
    try:
        if q_type == "author":
            res = AuthorSearch(q, refresh=refresh).authors or []
        elif q_type == "docs":
            res = ScopusSearch(q, refresh=refresh).results or []
            if not valid_results(res):
                sleep(tsleep)
                if tsleep <= 10:
                    tsleep = tsleep+2.5
                    return query(q_type, q, True, tsleep)
                else:
                    return []
        return res
    except (KeyError, UnicodeDecodeError, urllib.error.HTTPError, TypeError):
        sleep(tsleep)
        if tsleep <= 10:
            tsleep = tsleep+2.5
            return query(q_type, q, True, tsleep)
        else:
            return []


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
        res = query("docs", q, refresh=refresh)
    except (ScopusQueryError, Scopus500Error):  # Fall back to year-wise queries
        res = []
        for year in years:
            q = Template("SOURCE-ID({}) AND PUBYEAR IS $fill".format(source_id))
            ext, _ = stacked_query([year], [], q, "", "docs",
                refresh=refresh)
            if not valid_results(ext):  # Reload queries with missing years
                ext, _ = stacked_query([year], [], q, "",
                    "docs", refresh=True)
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


def query_year(year, source_ids, refresh, verbose):
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
    """
    params = {
        "group": [str(x) for x in sorted(source_ids)],
        "joiner": " OR ",
        "refresh": refresh,
        "q_type": "docs",
    }
    if verbose:
        params.update({"total": len(source_ids)})
        print("Searching authors in {} sources in {}...".format(
            len(source_ids), year))
    q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(year))
    params.update({"template": q, "res": []})
    res, _ = stacked_query(**params)
    res = pd.DataFrame(res)
    if not res.empty:
        res = res[~res.author_ids.isnull()]
    if not res.empty:
        res["Year"] = year
        res = res.astype(str)
        res = (res.groupby(["source_id", "Year"])[["author_ids"]]
                  .apply(get_auth_from_df)
                  .reset_index())
        res.columns = ["source_id", "year", "auids"]  # can be avoided by naming as in pubs
    return res


def stacked_query(group, res, template, joiner, q_type, refresh, i=0, total=None):
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
        if query_size(q_type,q,refresh)>5000 and len(group)>1:
            raise ScopusQueryError()
        res.extend(query(q_type, q, refresh, False))
        if total:  # Equivalent of verbose
            i += len(group)
            print_progress(i, total)
    except (Scopus400Error, Scopus500Error, ScopusQueryError) as e:
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