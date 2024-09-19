"""Module with utility functions for processing and caching data."""

from sqlite3 import Connection
from typing import Iterable

import pandas as pd


def temporary_merge(conn: Connection,
                    table: pd.DataFrame,
                    merge_cols: Iterable[str]) -> pd.DataFrame:
    """Perform merge with temp table and `table` and retrieve all columns."""
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = f"SELECT b.* FROM temp AS a INNER JOIN {table} AS b ON {conditions};"
    return pd.read_sql_query(q, conn)
