"""Module that provides functions for downloading and storing field-source information from the
sosia-dev/sosia-data repository.
"""

import pandas as pd

from sosia.establishing.constants import DATA_REPO_URL, FIELD_SOURCE_MAP, \
    SOURCE_INFO
from sosia.utils import custom_print


def get_field_source_information(verbose: bool = False) -> None:
    """Download two files from sosia-dev/sosia-data repository:
    1. List of Scopus source IDs with additional information
    2. Mapping of sources to ASJC codes

    Parameters
    ----------
    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.
    """
    fname = DATA_REPO_URL + "main/sources/source_info.csv"
    info = pd.read_csv(fname, index_col=0)
    SOURCE_INFO.parent.mkdir(parents=True, exist_ok=True)
    info.to_csv(SOURCE_INFO)

    fname = DATA_REPO_URL + "main/sources/field_sources_map.csv"
    fields = pd.read_csv(fname, index_col=0)
    fields.to_csv(FIELD_SOURCE_MAP)

    text = f"Stored information for {info.shape[0]:,} sources as well as "\
        f"{fields.shape[0]:,} field-source assignments in {SOURCE_INFO.parent}"
    custom_print(text, verbose)
