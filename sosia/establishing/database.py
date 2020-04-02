import sqlite3
from os.path import exists, expanduser
import configparser

import pandas as pd

from sosia.establishing.constants import CACHE_TABLES, CONFIG_FILE

# Configuration setup
file_exists = exists(CONFIG_FILE)
config = configparser.ConfigParser()
config.optionxform = str
if not file_exists:
    config.add_section('Cache')
    _cache_default = expanduser("~/.sosia/") + "cache_sqlite.sqlite"
    config.set('Cache', 'File path', _cache_default)
    try:
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    except FileNotFoundError:  # Fix for sphinx build
        pass
else:
    config.read(CONFIG_FILE)


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
