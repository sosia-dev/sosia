import pandas as pd

from sosia.establishing.constants import DATA_REPO_URL, FIELDS_SOURCES_LIST,\
    SOURCES_NAMES_LIST


def create_fields_sources_list(verbose=False):
    """Download two files from sosia-data folder:
    1. List of Scopus source IDs
    2. Mapping of sources to ASJC codes
    """
    fname = DATA_REPO_URL + "main/sources/sources_names.csv"
    names = pd.read_csv(fname, index_col=0)
    try:
        names.to_csv(SOURCES_NAMES_LIST)
    except OSError:
        SOURCES_NAMES_LIST.parent.mkdir()
        names.to_csv(SOURCES_NAMES_LIST)
    print(f">>> Downloaded {names.shape[0]} names of sources")

    fname = DATA_REPO_URL + "main/sources/field_sources_list.csv"
    fields = pd.read_csv(fname, index_col=0)
    fields.to_csv(FIELDS_SOURCES_LIST)
    print(f">>> Downloaded {fields.shape[0]} field-source assigments")
