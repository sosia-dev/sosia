"""Module with functions for inserting data into a SQL database."""

from sqlite3 import Connection
from typing import Literal

import pandas as pd

from sosia.establishing import DB_TABLES
from sosia.processing.utils import flat_set_from_df, robust_join


def insert_data(
    data: pd.DataFrame,
    conn: Connection,
    table: Literal[
        "authors",
        "author_ncits",
        "author_year",
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
        Allowed values: "authors", "author_ncits", "author_pubs",
        "author_year", "sources_afids".

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
    q = f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) "\
        f"VALUES ({','.join(values)})"

    # Eventually tweak data
    if table in ('authors', 'sources_afids'):
        if data.empty:
            return None
        if table == 'authors':
            data["auth_id"] = data['eid'].str.split('-').str[-1]
        elif table == 'sources_afids':
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
