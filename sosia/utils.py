from os import makedirs
from os.path import exists, expanduser

import pandas as pd
    
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
