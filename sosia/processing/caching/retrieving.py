"""Module that contains functions for retrieving data from a SQLite3 database cache."""

from sqlite3 import Connection

import pandas as pd

from sosia.processing.caching.inserting import insert_temporary_table
from sosia.processing.caching.utils import temporary_merge


def retrieve_authors(df: pd.DataFrame, conn: Connection) -> tuple[pd.DataFrame, list]:
    """Search authors in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: list
        List of authors not in cache.
    """
    cols = ["auth_id"]
    insert_temporary_table(df, merge_cols=cols, conn=conn)
    incache = temporary_merge(conn, "authors", merge_cols=cols)
    tosearch = df['auth_id'].tolist()
    if not incache.empty:
        incache_list = incache["auth_id"].tolist()
        tosearch = [au for au in tosearch if au not in incache_list]
    return incache, tosearch


def retrieve_author_info(df: pd.DataFrame,
                         conn: Connection,
                         table) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retrieve information by author and year from specific table of
    SQLite3 database.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    table : str
        The table of the SQLite3 database on which to perform the merge.

    Returns
    -------
    incache : DataFrame()
        DataFrame of results found in `conn`.

    tosearch : DataFrame()
        DataFrame of results not found in `conn`.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, conn, merge_cols=cols)
    incache = temporary_merge(conn, table, merge_cols=cols)
    if not incache.empty:
        merged = df.merge(incache, on=cols, how='left', indicator=True)
        tosearch = merged[merged['_merge'] == 'left_only'].drop(columns='_merge')
    else:
        tosearch = df
    return incache, tosearch


def retrieve_authors_from_sourceyear(tosearch: pd.DataFrame,
                                     conn: Connection,
                                     refresh: bool = False):
    """Search through sources by year for authors in SQL database.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids", "afid"), where
        entries correspond to an individual paper.

    missing: DataFrame
        DataFrame of source-year-combinations not in SQL database.
    """
    # Preparation
    cursor = conn.cursor()
    if not isinstance(refresh, bool) or refresh:
        q = "DELETE FROM sources_afids WHERE source_id=? AND year=?"
        cursor.executemany(q, tosearch.to_records(index=False))
        conn.commit()

    # Query selected data using left join
    cols = ["source_id", "year"]
    insert_temporary_table(tosearch.copy(), conn, merge_cols=cols)
    q = "SELECT a.source_id, a.year, b.auids, b.afid FROM temp AS a "\
        "LEFT JOIN sources_afids AS b "\
        "ON a.source_id=b.source_id AND a.year=b.year;"
    data = pd.read_sql_query(q, conn)
    data = data.sort_values(["source_id", "year"]).reset_index(drop=True)

    # Finalize
    mask_missing = data["auids"].isna()
    incache = data[~mask_missing].reset_index(drop=True)
    missing = data.loc[mask_missing, cols].drop_duplicates().reset_index(drop=True)
    return incache, missing
