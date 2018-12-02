from collections import Counter
from math import ceil
from os import makedirs
from os.path import exists, expanduser

import pandas as pd
from scopus import AuthorSearch, ContentAffiliationRetrieval, ScopusSearch

URL_SOURCES = 'https://elsevier.com/?a=734751'
URL_EXT_LIST = 'https://www.elsevier.com/__data/assets/excel_doc/0015/91122/ext_list_September_2018.xlsx'
FIELDS_SOURCES_LIST = expanduser('~/.sosia/') + 'field_sources_list.csv'

ASJC_2D = {10: "MULT", 11: "AGRI", 12: "ARTS", 13: "BIOC", 14: "BUSI", 
           15: "CENG", 16: "CHEM", 17: "COMP", 18: "DECI", 19: "EART",
           20: "ECON", 21: "ENER", 22: "ENGI", 23: "ENVI", 24: "IMMU",
           25: "MATE", 26: "MATH", 27: "MEDI", 28: "NEUR", 29: "NURS",
           30: "PHAR", 31: "PHYS", 32: "PSYC", 33: "SOCI", 34: "VETE",
           35: "DENT", 36: "HEAL"}


def create_fields_sources_list():
    """Download scopus files and create list of all sources with ids and
    field information.
    """
    # Get Information from Scopus Sources list
    sheets_sources = pd.read_excel(URL_SOURCES, sheet_name=None, header=1)    
    for drop in ['About CiteScore', 'ASJC Codes', 'Sheet1']:
        try:
            sheets_sources.pop(drop)
        except KeyError:
            continue
    cols = ['Scopus SourceID', 'Scopus ASJC Code (Sub-subject Area)', 'Type']
    out = pd.concat([df[cols].dropna() for df in sheets_sources.values()])
    out = out.drop_duplicates(subset=cols)
    out.columns = ['source_id', 'asjc','type']
    out['type'] = out['type'].str.lower().str.strip()
    
    # Add information from list of external publication titles
    sheets_external = pd.read_excel(URL_EXT_LIST, sheet_name=None)
    for drop in ['More info Medline', 'ASJC classification codes']:
        try:
            sheets_external.pop(drop)
        except KeyError:
            continue

    def _clean(x):
        return x.replace(';', ' ').replace(',', ' ').replace('  ', ' ').strip()

    keeps = ['Sourcerecord id', 'ASJC code', 'Source Type']
    cols = ['source_id', 'type', 'asjc']
    rename = {'All Science Journal Classification Codes (ASJC)': 'ASJC code'}
    for df in sheets_external.values():
        if not 'Source Type' in df.columns:
            df['Source Type'] = 'conference proceedings'
        subset = df.rename(columns=rename)[keeps].dropna()
        subset['ASJC code'] = (subset['ASJC code'].astype(str).apply(_clean)
                                                  .str.split())
        subset = subset.set_index(['Sourcerecord id', 'Source Type'])
        subset = subset['ASJC code'].apply(pd.Series).stack()
        subset = subset.reset_index().drop('level_2', axis=1)
        subset['Source Type'] = subset['Source Type'].str.lower().str.strip()
        subset.columns = cols
        out = pd.concat([out, subset], sort=True)

    # Write out
    out['asjc'] = out['asjc'].astype(int)
    out = out.drop_duplicates()
    path = expanduser('~/.sosia/')
    if not exists(path):
       makedirs(path)
    out.to_csv(FIELDS_SOURCES_LIST, index=False)


def clean_abstract(s):
    """Auxiliary function to clean an abstract of a document."""
    # Remove copyright statement, which can be leading or trailing
    tokens = s.split(". ")
    if "©" in tokens[0]:
        return ". ".join(tokens[1:])
    if "©" in tokens[-1]:
        return ". ".join(tokens[:-1]) + "."
    else:
        return s


def compute_cosine(matrix, digits=4):
    """Auxiliary function to return last column of cosine matrix."""
    return (matrix * matrix.T).toarray().round(digits)[-1]


def find_country(auth_ids, pubs, year):
    """Auxiliary function to find the most commont country of affiliations
    of a scientist using her most recent publications.
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


def margin_range(base, val):
    """Auxiliary function to create a range of margins around a base value."""
    if isinstance(val, float):
        margin = ceil(val*base)
        r = range(base-margin, base+margin+1)
    elif isinstance(val, int):
        r = range(base-val, base+val+1)
    else:
        raise Exception("Value must be either float or int.")
    return r


def print_progress(iteration, total, decimals=2, length=50):
    """Print terminal progress bar."""
    percent = round(100 * (iteration / float(total)), decimals)
    filled_len = int(length * iteration // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    print('\rProgress: |{}| {}% Complete'.format(bar, percent), end='\r')
    if iteration == total:
        print()


def query(q_type, q, refresh=False, first_try=True):
    """Auxiliary wrapper function to perform a particular search query."""
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


def raise_non_empty(val, obj):
    """Auxiliary function to raise exception if provided value is empty or
    not of the desired object type.
    """
    if not isinstance(val, obj) or len(val) == 0:
        obj_name = str(obj).split("'")[1]
        raise Exception("Value must be a non-empty {}.".format(obj_name))


def run(op, *args):
    """Auxiliary function to call a function passed by partial()."""
    return op(*args)


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
