import sqlite3


def connect_database(fname):
    """Connect to local SQLite3 database to be used as cache.

    Parameters
    ----------
    fname : str
        The path of the SQLite3 database to connect to.
    """
    from numpy import int32, int64
    for val in (int32, int64):
        sqlite3.register_adapter(val, int)
    return sqlite3.connect(fname)


def make_database(fname=None, drop=False):
    """Make SQLite database with predefined tables and keys.

    Parameters
    ----------
    fname : str (optional, default=None)
        The path of the SQLite database to connect to.  If None will use
        the path provided in `~/.sosia/config.ini`.

    drop : boolean (optional, default=False)
        If True, deletes and recreates all tables in cache (irreversible).
    """
    from sosia.establishing.constants import DB_TABLES
    from sosia.establishing.config import config

    if not fname:
        fname = config.get('Filepaths', 'Database')
    conn = sqlite3.connect(fname)
    cursor = conn.cursor()
    for table, variables in DB_TABLES.items():
        if drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        columns = ", ".join(" ".join(v) for v in variables["columns"])
        q = f"CREATE TABLE IF NOT EXISTS {table} "\
            f"({columns}, PRIMARY KEY({', '.join(variables['primary'])}))"
        cursor.execute(q)
