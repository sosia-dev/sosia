import sqlite3

import pandas as pd

from sosia.establishing.constants import CACHE_TABLES


def connect_database(fname):
    """Connect to local SQLite3 database to be used as cache.

    Parameters
    ----------
    fname : str
        The path of the SQLite3 database to connect to.
    """
    import sqlite3
    from numpy import int32, int64
    for val in (int32, int64):
        sqlite3.register_adapter(val, int)
    return sqlite3.connect(fname)


def create_cache(fname, drop=False):
    """Create or recreate tables in cache file.

    Parameters
    ----------
    fname : str
        The path of the SQLite database to connect to.

    drop : boolean (optional, default=False)
        If True, deletes and recreates all tables in cache (irreversible).
    """
    conn = sqlite3.connect(fname)
    cursor = conn.cursor()
    for table, variables in CACHE_TABLES.items():
        if drop:
            q = "DROP TABLE IF EXISTS {}".format(table)
            cursor.execute(q)
        columns = ", ".join(" ".join(v) for v in variables["columns"])
        prim_keys = ", ".join(variables["primary"])
        q = "CREATE TABLE IF NOT EXISTS {} ({}, PRIMARY KEY({}))".format(
            table, columns, prim_keys)
        cursor.execute(q)
