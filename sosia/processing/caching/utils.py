"""Module with utility functions for processing and caching data."""

from collections.abc import Iterable
from copy import deepcopy
from sqlite3 import Connection
from typing import Dict

import pandas as pd


def d_to_df_for_cache(d: Dict, source_id: int) -> pd.DataFrame:
    """Function to create a DataFrame of sources, years and list of authors
    from a dictionary where keys are the years and values are the list of
    authors.

    Parameters
    ----------
    d : dict
        Dictionary of year-list of author pairs.

    source_id: int
        Scopus identifier of the source.
    """
    d2 = deepcopy(d)
    for y in d2:
        d2[y] = [d2[y]]
    df = pd.DataFrame.from_dict(d2, orient="index").reset_index()
    df.columns = ["year", "auids"]
    df["source_id"] = str(source_id)
    return df


def temporary_merge(conn: Connection,
                    table: pd.DataFrame,
                    merge_cols: Iterable[str]) -> pd.DataFrame:
    """Perform merge with temp table and `table` and retrieve all columns."""
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = f"SELECT b.* FROM temp AS a INNER JOIN {table} AS b ON {conditions};"
    return pd.read_sql_query(q, conn)
