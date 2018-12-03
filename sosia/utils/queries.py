from collections import Counter
from scopus import AuthorSearch, ContentAffiliationRetrieval, ScopusSearch

from sosia.utils import print_progress, run


def find_country(auth_ids, pubs, year):
    """Find the most common country of affiliations of a scientist using her
    most recent publications.

    Parameters
    ----------
    auth_ids : list of str
        A list of Scopus Author Profile IDs for which the affiliation should
        be searched for.

    pubs : list of namedtuple
        The publications associated with the Author IDs as returned from a
        scopus query.

    year : int
        The year for which we would like to have the country.

    Returns
    -------
    country : str or None
        The country of the scientist in a given year (or valid in previous
        years).  Is None when no valid publications are found.
    """
    # Available papers of most recent year with publications
    papers = []
    i = 0
    while len(papers) == 0 & i <= len(pubs):
        papers = [p for p in pubs if int(p.coverDate[:4]) == year-i]
        i += 1
    if len(papers) == 0:
        return None
    # List of affiliations on these papers belonging to the actual author
    affs = []
    for p in papers:
        authors = p.authid.split(';')
        au_id = [au for au in auth_ids if au in authors][0]
        idx = authors.index(str(au_id))
        aff = p.afid.split(';')[idx].split('-')
        affs.extend(aff)
    affs = [af for af in affs if af != '']
    # Find most often listed country of affiliations
    countries = [ContentAffiliationRetrieval(afid).country
                 for afid in affs]
    return Counter(countries).most_common(1)[0][0]


def query(q_type, q, refresh=False, first_try=True):
    """Wrapper function to perform a particular search query

    Parameters
    ----------
    q_type : str
        Determines the query search that will be used.  Allowed values:
        "author", "docs".

    q : str
        The query string.

    refresh : bool (optional, default=False)
        Whether to refresh cached files if they exist, or not.

    first_try: bool (optional, default=True)
        A flag parameter to indicate whether the function has been called
        for the first time.  If False, KeyErrors will result in abortion.

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
            return AuthorSearch(q, refresh=refresh).authors
        elif q_type == "docs":
            return ScopusSearch(q, refresh=refresh).results
        else:
            raise Exception("Unknown value provided.")
    except KeyError:  # Cached file broken
        if first_try:
            return query(q_type, q, True, False)
        else:
            pass


def stacked_query(group, res, query, joiner, func, refresh, i=0, total=None):
    """Auxiliary function to recursively perform queries until they work.

    Parameters
    ----------
    group : list of str
        Scopus IDs (of authors or sources) for which the stacked query should
        be conducted.

    res : list
        (Initially empty )Container to which the query results will be
        appended.

    query : Template()
        A string template with one paramter named `fill` which will be used
        as search query.

    joiner : str
        On wich the group elements should be joined to fill the query.

    func : function object
        The function to be used (ScopusSearch, AuthorSearch).  Should be
        provided with partial and additional parameters.

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
    try:
        q = query.substitute(fill=joiner.join(group))
        res.extend(run(func, q, refresh))
        if total:  # Equivalent of verbose
            i += len(group)
            print_progress(i, total)
    except Exception as e:  # Catches two exceptions (long URL + many results)
        mid = len(group) // 2
        params = {"group": group[:mid], "res": res, "query": query, "i": i,
                  "joiner": joiner, "func": func, "total": total,
                  "refresh": refresh}
        res, i = stacked_query(**params)
        params.update({"group": group[mid:], "i": i})
        res, i = stacked_query(**params)
    return res, i
