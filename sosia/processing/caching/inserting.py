import numpy as np
import pandas as pd
import sqlite3

from sosia.establishing import CACHE_TABLES
from sosia.processing.utils import flat_set_from_df, robust_join


def insert_data(data, conn, table):
    """Insert new information in SQL database.

    Parameters
    ----------
    data : DataFrame or 3-tuple
        Dataframe with authors information or (when table="source") a
        3-element tuple.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    table : string
        The database table to insert into.  The query will be adjusted
        accordingly.
        Allowed values: "authors", "author_cits_size", "author_year",
        "author_size", "sources".

    Raises
    ------
    ValueError
        If parameter table is not one of the allowed values.
    """
    # Checks
    if table not in CACHE_TABLES.keys():
        msg = f"table parameter must be one of {', '.join(CACHE_TABLES.keys())}"
        raise ValueError(msg)

    # Build query
    cols, _ = zip(*CACHE_TABLES[table]["columns"])
    wildcard_tables = {"author_cits_size", "author_year", "authors",
                       "sources", "sources_afids"}
    if table in wildcard_tables:
        values = ["?"]*len(cols)
    else:
        values = (str(d) for d in data)
    q = f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) "\
        f"VALUES ({','.join(values)})"

    # Eventually tweak data
    if table in ('authors', 'sources', 'sources_afids'):
        if data.empty:
            return None
        if table == 'authors':
            data["auth_id"] = data.apply(lambda x: x.eid.split("-")[-1], axis=1)
        elif table in ('sources', 'sources_afids'):
            if table == 'sources' and "afid" in data.columns:
                data = (data.groupby(["source_id", "year"])[["auids"]]
                            .apply(lambda x: list(flat_set_from_df(x, "auids")))
                            .rename("auids")
                            .reset_index())
            data["auids"] = data["auids"].apply(robust_join)
        data = data[list(cols)]

    # Execute queries
    cursor = conn.cursor()
    if table in wildcard_tables:
        cursor.executemany(q, data.to_records(index=False))
    else:
        cursor.execute(q)
    conn.commit()


def insert_temporary_table(df, conn, merge_cols):
    """Temporarily create a table in SQL cache in order to prepare a
    merge with `table`.

    Parameters
    ----------
    data : DataFrame
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
