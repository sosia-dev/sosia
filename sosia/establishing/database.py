"""This module provides functions for connecting to and creating a SQLite database."""

import sqlite3

from pathlib import Path
from typing import Optional

from numpy import int32, int64


def connect_database(fname: str) -> sqlite3.Connection:
    """Connect to local SQLite3 database to be used as cache.

    Parameters
    ----------
    fname : str
        The path of the SQLite3 database to connect to.
    """
    for val in (int32, int64):
        sqlite3.register_adapter(val, int)
    return sqlite3.connect(fname)


def make_database(fname: Optional[Path] = None, drop: bool = False) -> None:
    """Make SQLite database with predefined tables and keys.

    Parameters
    ----------
    fname : Path (optional, default=None)
        The path of the SQLite database to connect to.  If None will default
        to `~/.cache/sosia/main.sqlite`.

    drop : boolean (optional, default=False)
        If True, deletes and recreates all tables in cache (irreversible).
    """
    from sosia.establishing.constants import DB_TABLES, DEFAULT_DATABASE

    if not fname:
        fname = DEFAULT_DATABASE

    fname.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(fname)
    cursor = conn.cursor()
    for table, variables in DB_TABLES.items():
        if drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        columns = ", ".join(" ".join(v) for v in variables["columns"])
        q = f"CREATE TABLE IF NOT EXISTS {table} "\
            f"({columns}, PRIMARY KEY({', '.join(variables['primary'])}))"
        cursor.execute(q)
