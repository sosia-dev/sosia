"""Module with functions for inserting data into a SQL database."""

from sqlite3 import Connection
from typing import Literal, Union

import pandas as pd

from sosia.establishing import DB_TABLES
from sosia.processing.utils import flat_set_from_df, robust_join


def auth_npubs_retrieve_insert(auth_id: int, year: int, conn: Connection) -> int:
    """Retrieve an author's publication count until a given year, and insert."""
    from sosia.processing.querying import base_query

    docs = base_query("docs", f"AU-ID({auth_id})")
    data = pd.DataFrame(docs)[["eid", "coverDate"]]
    data["coverDate"] = data["coverDate"].str[:4].astype("uint16")
    min_year = data["coverDate"].min()
    if year < min_year:
        return 0
    data = (data.rename(columns={"coverDate": "year", "eid": "n_pubs"})
                .groupby("year")["n_pubs"].nunique().reset_index())
    all_years = pd.DataFrame({"year": range(min_year, data["year"].max() + 1)})
    data = pd.merge(all_years, data, on="year", how="left").fillna(0)
    data["n_pubs"] = data["n_pubs"].cumsum().astype(int)
    data["auth_id"] = int(auth_id)
    insert_data(data[["auth_id", "year", "n_pubs"]], conn, table="author_pubs")
    return data.loc[data["year"] == year, "n_pubs"].iloc[0]


def insert_data(
    data: pd.DataFrame,
    conn: Connection,
    table: Literal[
        "authors",
        "author_ncits",
        "author_pubs",
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
