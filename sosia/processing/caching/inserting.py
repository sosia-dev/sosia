import numpy as np
import pandas as pd
import sqlite3

from sosia.processing.utils import flat_set_from_df
from sosia.processing.caching.utils import connect_sqlite
from sosia.establishing import config

cache_file = config.get('Cache', 'File path')


def cache_insert(data, table, file=cache_file):
    """Insert new authors information in cache.

    Parameters
    ----------
    data : DataFrame or 3-tuple
        Dataframe with authors information or (when table="source") a
        3-element tuple.

    table : string
        The database table to insert into.  The query will be adjusted
        accordingly.
        Allowed values: "authors", "author_cits_size", "author_year",
        "author_size", "sources".

    file : file (optional, default=cache_file)
        The cache file to connect to.

    Raises
    ------
    ValueError
        If parameter table is not one of the allowed values.
    """
    def join_flat_auids(s):
        return ",".join([str(a) for a in s["auids"]])

    # Build query
    if table == 'authors':
        q = """INSERT OR IGNORE INTO authors (auth_id, eid, surname, initials,
            givenname, affiliation, documents, affiliation_id, city, country,
            areas) values (?,?,?,?,?,?,?,?,?,?,?)"""
        if data.empty:
            return None
        data["auth_id"] = data.apply(lambda x: x.eid.split("-")[-1], axis=1)
        cols = ["auth_id", "eid", "surname", "initials", "givenname",
                "affiliation", "documents", "affiliation_id", "city",
                "country", "areas"]
        data = data[cols]
    elif table == 'author_cits_size':
        q = """INSERT OR IGNORE INTO author_cits_size (auth_id, year, n_cits)
            values (?,?,?)"""
    elif table == 'author_year':
        q = """INSERT OR IGNORE INTO author_year (auth_id, year, first_year,
            n_pubs, n_coauth) values (?,?,?,?,?)"""
    elif table == 'author_size':
        q = """INSERT OR IGNORE INTO author_size (auth_id, year, n_pubs)
            values ({},{},{})""".format(data[0], data[1], data[2])
    elif table == "sources":
        if data.empty:
            return None
        if "afid" in data.columns.tolist():
            data = (data.groupby(["source_id", "year"])[["auids"]]
                    .apply(lambda x: list(flat_set_from_df(x, "auids")))
                    .rename("auids")
                    .reset_index())
        data["auids"] = data.apply(join_flat_auids, axis=1)
        data = data[["source_id", "year", "auids"]]
        q = """INSERT OR IGNORE INTO sources (source_id, year, auids)
            VALUES (?,?,?)"""
    elif table == "sources_afids":
        if data.empty:
            return None
        data["auids"] = data.apply(join_flat_auids, axis=1)
        data = data[["source_id", "year", "afid", "auids"]]
        q = """INSERT OR IGNORE INTO sources_afids (source_id, year, afid, auids)
            VALUES (?,?,?,?)"""
    else:
        allowed_tables = ('authors', 'author_cits_size', 'author_year',
                          'author_size', 'sources', 'sources_afids')
        msg = 'table parameter must be one of ' + ', '.join(allowed_tables)
        raise ValueError(msg)
    # Perform caching
    _, conn = connect_sqlite(file=file)
    if table in ("authors", "author_cits_size", "author_year", "sources",
                 "sources_afids"):
        conn.executemany(q, data.to_records(index=False))
    else:
        conn.execute(q)
    conn.commit()


def insert_temporary_table(df, merge_cols, file=cache_file):
    """Temporarily create a table in SQL cache in order to prepare a
    merge with `table`.

    Parameters
    ----------
    data : DataFrame
        Dataframe with authors information that should be entered.

    merge_cols : list of str
        The columns that should be created and filled.  Must correspond in
        length to the number of columns of `df`.

    file : file (optional, default=cache_file)
        The cache file to connect to.
    """
    df = df.astype({c: "int64" for c in merge_cols})
    c, conn = connect_sqlite(file=file)
    # Drop table
    c.execute("DROP TABLE IF EXISTS temp")
    # Create table
    names = ", ".join(merge_cols)
    q = "CREATE TABLE temp ({0}, PRIMARY KEY({0}))".format(names)
    c.execute(q)
    # Insert values
    wildcards = ", ".join(["?"] * len(merge_cols))
    q = "INSERT OR IGNORE INTO temp ({}) values ({})".format(names, wildcards)
    conn.executemany(q, df.to_records(index=False))
    conn.commit()
