"""Module that contains functions for retrieving data from a SQLite3 database cache."""

from sqlite3 import Connection
from typing import Iterable, Literal, Optional, Union

import pandas as pd

from sosia.establishing import DB_TABLES
from sosia.processing.utils import logger, robust_join


def drop_values(data: pd.DataFrame, conn: Connection, table: str) -> None:
    """Drop values from a database `table`."""
    if table == "sources_afids":
        fields = ("source_id", "year")
    elif table == "author_citations":
        fields = ("auth_id", "year")
    else:
        fields = ("auth_id",)
    cursor = conn.cursor()
    if len(fields) == 1:
        values = data[fields[0]]
        q = f"DELETE FROM {table} WHERE {fields[0]} IN ({','.join(['?'] * len(values))})"
        cursor.execute(q, tuple(values))
    else:
        q = f"DELETE FROM {table} WHERE " + "=? AND ".join(fields) + "=?"
        cursor.executemany(q, data.to_records(index=False))
    conn.commit()


def insert_data(
    data: pd.DataFrame,
    conn: Connection,
    table: Literal[
        "author_citations",
        "author_data",
        "author_info",
        "sources_afids",
    ],
) -> None:
    """Insert new information in SQL database.

    Parameters
    ----------
    data : DataFrame or 3-tuple
        Dataframe with author information.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    table : string
        The database table to insert into.  The query will be adjusted
        accordingly.

    Raises
    ------
    ValueError
        If parameter table is not one of the allowed values.
    """
    # Checks
    if table not in DB_TABLES:
        msg = f"table parameter must be one of {', '.join(DB_TABLES.keys())}"
        logger.critical(msg)
        raise ValueError(msg)

    # Build query
    cols, _ = zip(*DB_TABLES[table]["columns"])
    values = ["?"] * len(cols)
    q = f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) VALUES ({','.join(values)})"

    # Eventually tweak data
    if table in ('author_info', 'sources_afids'):
        if data.empty:
            return None
        if table == 'sources_afids':
            data["auids"] = data["auids"].apply(robust_join)
    data = data[list(cols)]

    # Execute queries
    cursor = conn.cursor()
    cursor.executemany(q, data.to_records(index=False))
    conn.commit()


def insert_temporary_table(df: pd.DataFrame,
                           conn: Connection,
                           merge_cols: list[str]) -> None:
    """Temporarily create a table in SQL database in order to prepare a
    merge with `merge_cols`.

    Parameters
    ----------
    df : DataFrame
        Dataframe with authors information that should be entered.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    merge_cols : list of str
        The columns that should be created and filled.  Must correspond in
        length to the number of columns of `df`.
    """
    df = df.astype({c: "int64" for c in merge_cols})
    # Drop table
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS temp")
    # Create table
    names = ", ".join(merge_cols)
    q = f"CREATE TABLE temp ({names}, PRIMARY KEY({names}))"
    cursor.execute(q)
    # Insert values
    wildcards = ", ".join(["?"] * len(merge_cols))
    q = f"INSERT OR IGNORE INTO temp ({names}) values ({wildcards})"
    cursor.executemany(q, df.to_records(index=False))
    conn.commit()


def retrieve_from_author_table(
        df: pd.DataFrame,
        conn: Connection,
        table: str,
        refresh: Union[bool, int] = False
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

    refresh : bool, int (optional, default=False)
        All values other than False will lead to dropping database
        entries matching `df`.

    Returns
    -------
    incache : DataFrame
        Results found in cache.

    tosearch: list
        Results not found in cache.
    """
    # Set columns
    if table == "author_citations":
        cols = ["auth_id", "year"]
    else:
        cols = ["auth_id"]

    # Drop values if to be refreshed
    if not isinstance(refresh, bool) or refresh:
        drop_values(df, conn, table=table)

    insert_temporary_table(df, merge_cols=cols, conn=conn)
    incache = temporary_merge(conn, table=table, merge_cols=cols)
    tosearch = set(df["auth_id"].unique()) - set(incache["auth_id"].unique())
    return incache, sorted(tosearch)


def retrieve_authors_from_sourceyear(tosearch: pd.DataFrame,
                                     conn: Connection,
                                     drop: Optional[bool] = False):
    """Search through sources by year for authors in SQL database.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    refresh : bool, int (optional, default=False)
        Whether to refresh cached results (if they exist) or not, with
        Scopus data that is at most `refresh` days old (True = 0).

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids", "afid"), where
        entries correspond to an individual paper.

    missing: DataFrame
        DataFrame of source-year-combinations not in SQL database.
    """
    # Drop values if to be refreshed
    if drop:
        drop_values(tosearch, conn, table="sources_afids")

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
                    table: str,
                    merge_cols: Iterable[str]) -> pd.DataFrame:
    """Perform merge with temp table and `table` and retrieve all columns."""
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = f"SELECT b.* FROM temp AS a INNER JOIN {table} AS b ON {conditions};"
    return pd.read_sql_query(q, conn)
