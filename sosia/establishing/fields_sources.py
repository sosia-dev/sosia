import pandas as pd

from sosia.establishing.constants import DATA_REPO_URL, FIELDS_SOURCES_LIST,\
    SOURCES_NAMES_LIST
from sosia.utils import custom_print


def create_fields_sources_list(verbose=False):
    """Download two files from sosia-data folder:
    1. List of Scopus source IDs
    2. Mapping of sources to ASJC codes

    Parameters
    ----------
    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.
    """
    fname = DATA_REPO_URL + "main/sources/sources_names.csv"
    names = pd.read_csv(fname, index_col=0)
    try:
        names.to_csv(SOURCES_NAMES_LIST)
    except OSError:
        SOURCES_NAMES_LIST.parent.mkdir()
        names.to_csv(SOURCES_NAMES_LIST)

    fname = DATA_REPO_URL + "main/sources/field_sources_list.csv"
    fields = pd.read_csv(fname, index_col=0)
    fields.to_csv(FIELDS_SOURCES_LIST)

    text = f"Stored information for {names.shape[0]:,} sources as well as "\
        f"{fields.shape[0]:,} field-source assigments in {SOURCES_NAMES_LIST.parent}/"
    custom_print(text, verbose)
