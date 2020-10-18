from os import makedirs
from os.path import exists, expanduser

import pandas as pd

from sosia.establishing.constants import DATA_REPO_URL, FIELDS_SOURCES_LIST,\
    SOURCES_NAMES_LIST


def create_fields_sources_list(verbose=False):
    """Download Scopus files with information on covered sources and create
    one list of all sources with ids and one with field information.
    """
    path = expanduser("~/.sosia/")
    if not exists(path):
        makedirs(path)

    fname = DATA_REPO_URL + "main/sources/sources_names.csv"
    names = pd.read_csv(fname, index_col=0)
    names.to_csv(SOURCES_NAMES_LIST)
    print(f">>> Downloaded {names.shape[0]} names of sources")

    fname = DATA_REPO_URL + "main/sources/field_sources_list.csv"
    fields = pd.read_csv(fname, index_col=0)
    fields.to_csv(FIELDS_SOURCES_LIST)
    print(f">>> Downloaded {fields.shape[0]} field-source assigments")
