from os import makedirs
from os.path import exists, expanduser

import pandas as pd
    
URL_SOURCES = 'https://elsevier.com/?a=734751'
URL_EXT_LIST = 'https://www.elsevier.com/__data/assets/excel_doc/0015/91122/ext_list_April_2018_2017_Metrics.xlsx'
FIELDS_JOURNALS_LIST = expanduser('~/.sosia/') + 'field_journal_list.csv'


def create_fields_journals_list():
    """Download scopus files and create list of all journals with ids and
    field information.
    """
    # Get Information from Scopus Sources list
    sheets_sources = pd.read_excel(URL_SOURCES, sheet_name=None, header=1)    
    for drop in ['About CiteScore', 'ASJC Codes', 'Sheet1']:
        try:
            sheets_sources.pop(drop)
        except KeyError:
            continue
    cols = ['Scopus SourceID', 'Scopus ASJC Code (Sub-subject Area)']
    out = pd.concat([df[cols] for df in sheets_sources.values()])
    out = out.drop_duplicates(subset=cols)
    out.columns = ['source_id', 'asjc']
    
    # Add information from list of external publication titles
    sheets_external = pd.read_excel(URL_EXT_LIST, sheet_name=None)
    for drop in ['More info Medline', 'ASJC classification codes']:
        try:
            sheets_external.pop(drop)
        except KeyError:
            continue

    def _clean(x):
        x = x.replace(';', ' ').replace(',', ' ').replace('  ', ' ').strip()

    keeps = ['Sourcerecord id', 'ASJC code']
    cols = ['source_id', 'asjc']
    rename = {'All Science Journal Classification Codes (ASJC)': 'ASJC code'}
    for df in sheets_external.values():
        subset = df.rename(columns=rename)[keeps]
        subset['ASJC code'] = (subset['ASJC code'].astype(str).apply(_clean)
                                                  .str.split())
        subset = subset.set_index('Sourcerecord id')
        subset = subset['ASJC code'].apply(pd.Series).stack()
        subset = subset.reset_index().drop('level_1', axis=1)
        subset.columns = cols
        out = pd.concat([out, subset], sort=True)

    # Write out
    out = out.astype(int).drop_duplicates()
    path = expanduser('~/.sosia/')
    if not exists(path):
       makedirs(path)
    out.to_csv(FIELDS_JOURNALS_LIST, index=False)
