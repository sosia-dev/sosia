from os import makedirs
from os.path import exists, expanduser

import pandas as pd

from sosia.utils import FIELDS_SOURCES_LIST, SOURCES_NAMES_LIST,\
    URL_EXT_LIST, URL_SOURCES, CACHE_SQLITE

import sqlite3


def create_cache(drop=False):
    """Create or recreate tables in cache file.
    """
    conn = sqlite3.connect(CACHE_SQLITE)
    c = conn.cursor()
    # to refresh all cache
    if drop:
        c.execute('''DROP TABLE IF EXISTS sources''')
        c.execute('''DROP TABLE IF EXISTS authors''')
        c.execute('''DROP TABLE IF EXISTS author_year''')
    # table for sources
    c.execute('''CREATE TABLE IF NOT EXISTS sources
              (source_id int, year int, auids text,
              PRIMARY KEY(source_id,year))''')
    # table for authors
    c.execute('''CREATE TABLE IF NOT EXISTS authors
              (auth_id int, eid text, surname text, initials text,
              givenname text, affiliation text, documents text,
              affiliation_id text, city text, country text, areas text,
              PRIMARY KEY(auth_id))''')
    # table for author year publication information
    c.execute('''CREATE TABLE IF NOT EXISTS author_year
              (auth_id int, year int, first_year int, n_pubs int, n_coauth int,
              PRIMARY KEY(auth_id, year))''')


def create_fields_sources_list():
    """Download Scopus files with information on covered sources and create
    one list of all sources with ids and one with field information.
    """
    # Set up
    path = expanduser('~/.sosia/')
    if not exists(path):
        makedirs(path)
    rename = {'All Science Journal Classification Codes (ASJC)': 'asjc',
              'Scopus ASJC Code (Sub-subject Area)': 'asjc',
              'ASJC code': 'asjc', 'Source Type': 'type', 'Type': 'type',
              'Sourcerecord id': 'source_id', 'Scopus SourceID': 'source_id',
              'Title': 'title', 'Source title': 'title'}
    keeps = list(set(rename.values()))

    # Get Information from Scopus Sources list
    sources = pd.read_excel(URL_SOURCES, sheet_name=None, header=1)
    _drop_sheets(sources, ['About CiteScore', 'ASJC Codes', 'Sheet1'])
    out = pd.concat([df.rename(columns=rename)[keeps].dropna() for
                     df in sources.values()])
    out = out.drop_duplicates()

    # Add information from list of external publication titles
    external = pd.read_excel(URL_EXT_LIST, sheet_name=None)
    _drop_sheets(external, ['More info Medline', 'ASJC classification codes'])

    for df in external.values():
        _update_dict(rename, df.columns, 'source title', 'title')
        if 'Source Type' not in df.columns:
            df['type'] = 'conference proceedings'
        subset = df.rename(columns=rename)[keeps].dropna()
        subset['asjc'] = subset['asjc'].astype(str).apply(_clean).str.split()
        subset = (subset.set_index(['source_id', "title", 'type'])
                        .asjc.apply(pd.Series).stack()
                        .rename('asjc').reset_index().drop('level_3', axis=1))
        out = pd.concat([out, subset], sort=True)

    # Write list of names
    names = out[['source_id', 'title']].drop_duplicates().sort_values("source_id")
    names.to_csv(SOURCES_NAMES_LIST, index=False)

    # Write list of fields by source
    out['type'] = out['type'].str.lower().str.strip()
    out.drop('title', axis=1).to_csv(FIELDS_SOURCES_LIST, index=False)


def _clean(x):
    """Auxiliary function to clean a string Series."""
    return x.replace(';', ' ').replace(',', ' ').replace('  ', ' ').strip()


def _drop_sheets(sheets, drops):
    """Auxiliary function to drop sheets from an Excel DataFrame."""
    for drop in drops:
        try:
            sheets.pop(drop)
        except KeyError:
            continue


def _update_dict(d, lst, key, replacement):
    """Auxiliary function to add keys to a dictionary if a given string is
    included in the key.
    """
    for c in lst:
        if c.lower().startswith(key):
            d[c] = replacement
