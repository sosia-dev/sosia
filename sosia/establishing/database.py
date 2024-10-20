"""This module provides functions for connecting to and creating a SQLite database."""

import sqlite3
from pathlib import Path
from typing import Optional

from numpy import int32, int64


def connect_database(fname: Path, **kwds) -> sqlite3.Connection:
    """Connect to local SQLite3 database to be used as cache.

    Parameters
    ----------
    fname : pathlib.Path
        The path of the SQLite3 database to connect to.

    kwds : keyword arguments
        Additional arguments to pass to the make_database function.
    """
    for val in (int32, int64):
        sqlite3.register_adapter(val, int)

    if not fname.exists():
        make_database(fname, **kwds)

    return sqlite3.connect(fname)


def make_database(
        fname: Optional[Path] = None,
        verbose: bool = False,
        drop: bool = False
) -> None:
    """Make SQLite database with predefined tables and keys.

    Parameters
    ----------
    fname : pathlib.Path (optional, default=None)
        The path of the SQLite database to connect to.  If None, will default
        to `~/.cache/sosia/main.sqlite`.

    verbose : boolean (optional, default=False)
        Whether to report on the progess of the process.

    drop : boolean (optional, default=False)
        If True, deletes and recreates all tables in cache (irreversible).
    """
    from sosia.establishing.constants import DB_TABLES, DEFAULT_DATABASE

    if not fname:
        fname = DEFAULT_DATABASE

    # Create database
    existed = fname.exists()
    fname.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(fname)

    # Create tables
    cursor = conn.cursor()
    for table, variables in DB_TABLES.items():
        if drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        columns = ", ".join(" ".join(v) for v in variables["columns"])
        q = f"CREATE TABLE IF NOT EXISTS {table} "\
            f"({columns}, PRIMARY KEY({', '.join(variables['primary'])}))"
        cursor.execute(q)

    # Report progress
    if fname.exists():
        if existed:
            if drop:
                msg = f"Local database '{fname}' re-created successfully"
            else:
                msg = f"Local database '{fname}' not changed"
        else:
            msg = f"Local database '{fname}' created successfully"
    else:
        msg = f"Failed to create the local database '{fname}'"
    if verbose:
        print(msg)
