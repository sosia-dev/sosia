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


def make_database(fname, drop=False):
    """Make SQLite database with predefined tables and keys.

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
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        columns = ", ".join(" ".join(v) for v in variables["columns"])
        q = f"CREATE TABLE IF NOT EXISTS {table} "\
            f"({columns}, PRIMARY KEY({', '.join(variables['primary'])}))"
        cursor.execute(q)
