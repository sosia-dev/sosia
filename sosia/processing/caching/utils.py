import pandas as pd


def connect_sqlite(fname):
    """Connect to cache file.

    Parameters
    ----------
    fname : str
        The path of the SQLite database to connect to.
    """
    import sqlite3
    from numpy import int32, int64
    sqlite3.register_adapter(int64, lambda val: int(val))
    sqlite3.register_adapter(int32, lambda val: int(val))
    return sqlite3.connect(fname)


def d_to_df_for_cache(d, source_id):
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
    from copy import deepcopy
    d2 = deepcopy(d)
    for y in d2:
        d2[y] = [d2[y]]
    df = pd.DataFrame.from_dict(d2, orient="index").reset_index()
    df.columns = ["year", "auids"]
    df["source_id"] = str(source_id)
    return df


def temporary_merge(df, conn, table, merge_cols):
    """Perform merge with temp table and `table` and retrieve all columns."""
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = "SELECT b.* FROM temp AS a INNER JOIN {} AS b ON {};".format(
        table, conditions)
    return pd.read_sql_query(q, conn)
