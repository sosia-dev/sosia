from collections import defaultdict
from itertools import product
from string import Template
import urllib
from time import sleep
import pandas as pd

from scopus import AuthorSearch, ScopusSearch
from scopus.exception import Scopus400Error, ScopusQueryError,\
    Scopus500Error, Scopus404Error, Scopus429Error

from sosia.processing.extraction import get_authors, get_auth_from_df
from sosia.utils import custom_print, print_progress
from sosia.cache import (authors_in_cache, author_size_in_cache, cache_insert)


def query(q_type, q, refresh=False, size_only=False, tsleep=0):
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
    params = {"query": q, "refresh": refresh, "download": not size_only}
    if q_type == "author":
        obj = AuthorSearch(**params)
    elif q_type == "docs":
        obj = ScopusSearch(**params)
    if size_only:
        return obj.get_results_size()
    else:
        try:
            if q_type == "author":
                res = obj.authors or []
            elif q_type == "docs":
                res = obj.results or []
                if not valid_results(res):
                    raise TypeError
        except (KeyError, UnicodeDecodeError, urllib.error.HTTPError, TypeError):
            sleep(tsleep)
            if tsleep <= 10:
                tsleep = tsleep+2.5
                res = query(q_type, q, True, size_only, tsleep)
            else:
                res = []
        return res


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
    else:
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
        if query("docs", q, size_only=True) > 5000:
            raise ScopusQueryError()
        res = query("docs", q, refresh=refresh)
    except (ScopusQueryError, Scopus500Error):  # Fall back to year-wise queries
        res = []
        for year in years:
            q = Template("SOURCE-ID({}) AND PUBYEAR IS $fill".format(source_id))
            ext, _ = stacked_query([year], [], q, "", "docs", refresh=refresh)
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
    if not res.empty:
        res = res[~res.author_ids.isnull()]
    if not res.empty:
        res["Year"] = year
        res = res.astype(str)
        res = (res.groupby(["source_id", "Year"])[["author_ids"]]
                  .apply(get_auth_from_df)
                  .reset_index())
        # The following can be avoided by naming as in pubs
        res.columns = ["source_id", "year", "auids"]
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
        n = query(q_type, q, size_only=True)
        if n > 5000 and len(group) > 1:
            raise ScopusQueryError()
        res.extend(query(q_type, q, refresh=refresh))
        verbose = total is not None
        i += len(group)
        print_progress(i, total, verbose)
    except (Scopus400Error, Scopus500Error, ScopusQueryError) as e:
        # Split query into two equally sized ones
        mid = len(group) // 2
        params = {"group": group[:mid], "res": res, "template": template,
                  "i": i, "joiner": joiner, "q_type": q_type, "total": total,
                  "refresh": refresh}
        res, i = stacked_query(**params)
        params.update({"group": group[mid:], "i": i})
        res, i = stacked_query(**params)
    return res, i


def screen_pub_counts(group, ybefore, yupto, npapers, yfrom=None,
                      verbose=False):
    """Function to filter authors based on restrictions in the number of
    publications in different periods, searched by query_size.

    Parameters
    ----------
    group : list of str
        Scopus IDs of authors to be filtered.

    ybefore : int
        Year to be used as first year. Publications on this year and before
        need to be 0.

    yupto : int
        Year up to which to count publications.

    npapers : list
        List of count of publications, minimum and maximum.

    yfrom : int (optional, default=None)
        If provided, publications are counted only after this year.
        Publications are still set to 0 before ybefore.

    Returns
    -------
    group : list of str
        Scopus IDs filtered.

    pubs_counts : list of int
        List of count of publications within the period provided for authors
        in group.

    older_authors : list of str
        Scopus IDs filtered out because have publications before ybefore.

    Notes
    -----
    It uses cached values first, and searches for more data if needed.
    """
    group = [int(x) for x in group]
    years_check = [ybefore, yupto]
    if yfrom:
        years_check.extend([yfrom - 1])
    authors = pd.DataFrame(list(product(group, years_check)),
                           columns=["auth_id", "year"], dtype="int64")
    types = {"auth_id": int, "year": int}
    authors.astype(types, inplace=True)
    authors_size = author_size_in_cache(authors)
    au_skip = []
    au_remove = []
    group_tocheck = [x for x in group]
    older_authors = []
    pubs_counts = []
    # use information in cache
    if not authors_size.empty:
        # authors that can be already removed because older
        mask = ((authors_size.year <= ybefore) & (authors_size.n_pubs > 0))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        older_authors.extend(remove)
        au_remove.extend(remove)
        # remove if number of pubs in year is in any case too small
        mask = ((authors_size.year >= yupto) &
                (authors_size.n_pubs < min(npapers)))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        au_remove.extend(remove)
        # authors with no pubs before min year
        mask = (((authors_size.year == ybefore) &
                (authors_size.n_pubs == 0)))
        au_ok_miny = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        # check publications in range
        if yfrom:
            # adjust count by substracting the count before period; keep
            # only authors for which it is possible
            mask = (authors_size.year == yfrom - 1)
            authors_size_bef = authors_size[mask]
            authors_size_bef["year"] = yupto
            authors_size_bef.columns = ["auth_id", "year", "n_pubs_bef"]
            mask = ((authors_size.auth_id.isin(authors_size_bef.
                    auth_id.tolist())) & (authors_size.year == yupto))
            authors_size = authors_size[mask]
            authors_size = authors_size.merge(authors_size_bef,
                             on=["auth_id", "year"], how='left').fillna(0)
            authors_size["n_pubs"] = (authors_size["n_pubs"] -
                                      authors_size["n_pubs_bef"])
        # authors that can be already removed because of pubs count
        mask = (((authors_size.year >= yupto) &
                 (authors_size.n_pubs < min(npapers))) |
                ((authors_size.year <= yupto) &
                 (authors_size.n_pubs > max(npapers))))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        au_remove.extend(remove)
        # authors with pubs count within the range before the given year
        mask = (((authors_size.year == yupto) &
                 (authors_size.n_pubs >= min(npapers))) &
                (authors_size.n_pubs <= max(npapers)))
        au_ok_year = (authors_size[mask][["auth_id","n_pubs"]].drop_duplicates())
        # authors ok (match both conditions)
        au_ok = list(set(au_ok_miny).intersection(au_ok_year.auth_id.tolist()))
        pubs_counts = au_ok_year[au_ok_year.auth_id.isin(au_ok)].n_pubs.tolist()
        # authors that match only the first condition, but the second is
        # not known, can skip the first cindition check.
        au_skip = [x for x in au_ok_miny if x not in au_remove + au_ok]
        group = [x for x in group if x not in au_remove]
        group_tocheck = [x for x in group if x not in au_skip + au_ok]
    text = "Left with {} authors based on size information already in "\
           "cache.\n{} to check\n".format(len(group), len(group_tocheck))
    custom_print(text, verbose)
    # Verify the publications before minimum year are 0
    if group_tocheck:
        text = ("Searching through characteristics of {:,} authors \n"
                .format(len(group_tocheck)))
        custom_print(text, verbose)
        print_progress(0, len(group_tocheck), verbose)
        to_loop = [x for x in group_tocheck] # Temporary copy
        for i, au in enumerate(to_loop):
            q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, ybefore + 1)
            size = query("docs", q, size_only=True)
            tp = (au, ybefore, size)
            cache_insert(tp, table="author_size")
            print_progress(i + 1, len(to_loop), verbose)
            if not size == 0:
                group.remove(au)
                group_tocheck.remove(au)
                older_authors.append(au)
        text = "Left with {} authors based on size information before "\
               "minium year\n Filtering based on size query before "\
               "provided year\n".format(len(group))
        custom_print(text, verbose)
    # check the publications before the given year are in range
    group_tocheck.extend(au_skip)
    n = len(group_tocheck)
    if group_tocheck:
        text = "Searching through characteristics of {:,} authors".format(
            len(group_tocheck))
        custom_print(text, verbose)
        print_progress(0, n, verbose)
        for i, au in enumerate(group_tocheck):
            q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, yupto + 1)
            size = query("docs", q, size_only=True)
            tp = (au, yupto, size)
            cache_insert(tp, table="author_size")
            if yfrom and size >= min(npapers):
                q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, yfrom)
                size2 = query("docs", q, size_only=True)
                tp = (au, yfrom - 1, size2)
                cache_insert(tp, table="author_size")
                size = size - size2
            if size < min(npapers) or size > max(npapers):
                group.remove(au)
            else:
                pubs_counts.append(size)
            print_progress(i + 1, n, verbose)
    return group, pubs_counts, older_authors


def valid_results(res):
    """Verify that each element ScopusSearch in `res` contains year info."""
    try:
        _ = [p for p in res if p.subtype == "ar" and int(p.coverDate[:4])]
        return True
    except:
        return False
