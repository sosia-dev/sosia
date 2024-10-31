"""Module that contains functions for retrieving data from a SQLite3 database cache."""

from sqlite3 import Connection
from typing import Optional, Union

import pandas as pd

from sosia.establishing import DB_TABLES


def drop_values(data: pd.DataFrame, conn: Connection, table: str) -> None:
    """Drop values from a database `table`."""
    fields = DB_TABLES[table]["primary"]
    if table == "author_data":
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
    table: str,
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
        raise ValueError(msg)

    # Build query
    cols, _ = zip(*DB_TABLES[table]["columns"])
    values = ["?"] * len(cols)
    q = f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) VALUES ({','.join(values)})"

    # Eventually tweak data
    if table in ('author_info', 'sources'):
        if data.empty:
            return None
    data = data[list(cols)]

    # Execute queries
    cursor = conn.cursor()
    cursor.executemany(q, data.to_records(index=False))
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

    # Query data
    incache = merge_query(df, conn, table=table, merge_cols=cols, join="INNER")
    tosearch = set(df["auth_id"].unique()) - set(incache["auth_id"].unique())
    return incache, sorted(tosearch)


def retrieve_authors_from_sourceyear(
        tosearch: pd.DataFrame,
        conn: Connection,
        drop: Optional[bool] = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Search through sources by year for authors in SQL database.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    drop : bool, int (optional, default=False)
        Whether to drop matching information and replace them with data
        on disk.

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids"), where
        auids is a set of author IDs.

    missing: DataFrame
        DataFrame of source-year-combinations not in SQL database.
    """
    # Drop values if to be refreshed
    if drop:
        drop_values(tosearch, conn, table="sources")

    # Query authors for relevant journal-years
    cols = ["source_id", "year"]
    data = merge_query(tosearch.copy(), conn, table="sources",
                       merge_cols=cols, join="LEFT")

    # Finalize
    mask_missing = data["auids"].isna()
    incache = data[~mask_missing].reset_index(drop=True)
    missing = data.loc[mask_missing, cols].drop_duplicates().reset_index(drop=True)
    return incache, missing


def merge_query(
        df: pd.DataFrame,
        conn: Connection,
        table: str,
        merge_cols: list[str],
        join: str = "INNER"
) -> pd.DataFrame:
    """Query data from `table` matching `df` on `merge_cols`."""
    # Insert "temp" table
    df = df.astype({c: "int64" for c in merge_cols})
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS temp")
    names = ", ".join(merge_cols)
    cursor.execute(f"CREATE TABLE temp ({names}, PRIMARY KEY({names}))")
    wildcards = ", ".join(["?"] * len(merge_cols))
    cursor.executemany(f"INSERT OR IGNORE INTO temp ({names}) VALUES ({wildcards})",
                       df.to_records(index=False))
    conn.commit()
    # Build query
    table_columns = [col[0] for col in DB_TABLES[table]["columns"]]
    b_columns = [col for col in table_columns if col not in merge_cols]
    a_select = ", ".join([f"a.{col}" for col in merge_cols])
    b_select = ", ".join([f"b.{col}" for col in b_columns])
    select_statement = f"{a_select}, {b_select}" if b_select else a_select
    conditions = " and ".join([f"a.{col} = b.{col}" for col in merge_cols])
    query = (
        f"SELECT {select_statement} FROM temp AS a "
        f"{join} JOIN {table} AS b "
        f"ON {conditions};"
    )
    # Retrieve data
    return pd.read_sql_query(query, conn)
