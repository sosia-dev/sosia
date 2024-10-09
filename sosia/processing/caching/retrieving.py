"""Module that contains functions for retrieving data from a SQLite3 database cache."""

from sqlite3 import Connection
from typing import Iterable

import pandas as pd

from sosia.processing.caching.inserting import insert_temporary_table


def retrieve_from_author_table(
        df: pd.DataFrame,
        conn: Connection,
        table: str
) -> tuple[pd.DataFrame, list]:
    """Retrieve data on authors from specific `table` in SQL cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    table : str
        The table of the SQLite3 database on which to perform the merge.

    Returns
    -------
    incache : DataFrame
        Results found in cache.

    tosearch: list
        Results not found in cache.
    """
    if table == "author_citations":
        cols = ["auth_id", "year"]
    else:
        cols = ["auth_id"]
    insert_temporary_table(df, merge_cols=cols, conn=conn)
    incache = temporary_merge(conn, table=table, merge_cols=cols)
    tosearch = set(df["auth_id"].unique()) - set(incache["auth_id"].unique())
    return incache, sorted(tosearch)


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

    # Query authors for relevant journal-years
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


def temporary_merge(conn: Connection,
                    table: pd.DataFrame,
                    merge_cols: Iterable[str]) -> pd.DataFrame:
    """Perform merge with temp table and `table` and retrieve all columns."""
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = f"SELECT b.* FROM temp AS a INNER JOIN {table} AS b ON {conditions};"
    return pd.read_sql_query(q, conn)
