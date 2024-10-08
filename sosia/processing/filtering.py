"""Module with a function for filtering authors based on restrictions in the
number of  publications in different periods.
"""

import pandas as pd
from tqdm import tqdm

from sosia.processing.caching import insert_data, retrieve_authors
from sosia.processing import extract_yearly_author_data
from sosia.utils import custom_print


def get_author_yearly_data(group, conn, verbose=False):
    """Filter authors based on restrictions in the number of
    publications in different years, searched by query_size.

    Parameters
    ----------
    group : list of str
        Scopus IDs of authors to be filtered.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    group : list of str
        Scopus IDs of authors passing the publication count requirements.
    """
    authors = pd.DataFrame({"auth_id": group})
    auth_data, missing = retrieve_authors(authors, conn, table="author_year")

    # Add to database
    if missing:
        text = f"Querying Scopus for information for {len(missing):,} " \
               "authors..."
        custom_print(text, verbose)
        to_add = []
        for auth_id in tqdm(missing, disable=not verbose):
            new = extract_yearly_author_data(auth_id)
            to_add.append(new)
        to_add = pd.concat(to_add)
        insert_data(to_add, conn, table="author_year")

    # Retrieve again
    auth_data, missing = retrieve_authors(authors, conn, table="author_year")
    return auth_data


def same_affiliation(original, new, refresh=False):
    """Whether a new scientist shares affiliation(s) with the
    original scientist.
    """
    from sosia.classes import Scientist

    m = Scientist([new], original.year, refresh=refresh,
                  db_path=original.sql_fname)
    return any(str(a) in m.affiliation_id for a in original.search_affiliations)
