import pandas as pd

from sosia.utils import config, flat_set_from_df
from sosia.cache import cache_connect, insert_temporary_table


cache_file = config.get('Cache', 'File path')


def author_cits_in_cache(df, file=cache_file):
    """Search authors citations in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search in a year.

    file : file (optional, default=cache_file)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: pd.DataFrame
        List of authors not in cache.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, merge_cols=cols, file=file)
    incache = temporary_merge(df, "author_cits_size", merge_cols=cols,
                              file=file)
    if not incache.empty:
        df = df.set_index(cols)
        incache = incache.set_index(cols)
        tosearch = df[~(df.index.isin(incache.index))]
        incache = incache.reset_index()
        tosearch = tosearch.reset_index()
    else:
        tosearch = df
    return incache, tosearch


def authors_in_cache(df, file=cache_file):
    """Search authors in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    file : file (optional, default=cache_file)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: list
        List of authors not in cache.
    """
    cols = ["auth_id"]
    insert_temporary_table(df, merge_cols=cols, file=file)
    incache = temporary_merge(df, "authors", merge_cols=cols, file=file)
    tosearch = df.auth_id.tolist()
    if not incache.empty:
        incache_list = incache.auth_id.tolist()
        tosearch = [int(au) for au in tosearch if int(au) not in incache_list]
    return incache, tosearch


def author_year_in_cache(df, file=cache_file):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    file : file (optional, default=cache_file)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: DataFrame
        DataFrame of authors not in cache with year of the event as second
        column.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, merge_cols=cols, file=file)
    incache = temporary_merge(df, "author_year", merge_cols=cols, file=file)
    if not incache.empty:
        df = df.set_index(cols)
        incache = incache.set_index(cols)
        tosearch = df[~(df.index.isin(incache.index))]
        incache = incache.reset_index()
        tosearch = tosearch.reset_index()
        if tosearch.empty:
            cols = ["auth_id", "year", "n_pubs", "n_coauth", "first_year"]
            tosearch = pd.DataFrame(columns=cols)
    else:
        tosearch = df
    return incache, tosearch


def author_size_in_cache(df, file=cache_file):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    file : file (optional, default=cache_file)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, merge_cols=cols, file=file)
    incache = temporary_merge(df, "author_size", merge_cols=cols, file=file)
    if incache.empty:
        incache = pd.DataFrame()
    return incache


def sources_in_cache(tosearch, refresh=False, file=cache_file, afid=False):
    """Search sources by year in cache.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of sources and years combinations to search.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    file : file (optional, default=cache_file)
        The cache file to connect to.

    afid : bool (optional, default=False)
        If True, search in sources_afids table.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: DataFrame
        DataFrame of sources and years combinations not in cache.
    """
    cols = ["source_id", "year"]
    insert_temporary_table(tosearch, merge_cols=cols, file=file)
    c, conn = cache_connect(file=file)
    table = "sources"
    select = "a.source_id, a.year, b.auids"
    if afid:
        table = "sources_afids"
        select = "a.source_id, a.year, b.afid, b.auids"
    q = """SELECT {} FROM temp AS a
        INNER JOIN {} AS b ON a.source_id=b.source_id
        AND a.year=b.year;""".format(select, table)
    incache = pd.read_sql_query(q, conn)
    if not incache.empty:
        incache["auids"] = incache["auids"].str.split(",")
        tosearch = tosearch.merge(incache, "left", on=cols, indicator=True)
        tosearch = tosearch[tosearch["_merge"] == "left_only"].drop("_merge", axis=1)
        tosearch = tosearch[["source_id", "year"]]
        if refresh:
            auth_incache = pd.DataFrame(flat_set_from_df(incache, "auids"),
                                        columns=["auth_id"], dtype="uint64")
            tables = ("authors", "author_size", "author_cits_size", "author_year")
            for table in tables:
                q = "DELETE FROM {} WHERE auth_id=?".format(table)
                conn.executemany(q, auth_incache.to_records(index=False))
                conn.commit()
            tables = ("sources", "sources_afids")
            for table in tables:
                q = "DELETE FROM {} WHERE source_id=? AND year=?".format(table)
                conn.executemany(q, tosearch.to_records(index=False))
                conn.commit()
            incache = pd.DataFrame(columns=cols)
    if tosearch.empty:
        tosearch = pd.DataFrame(columns=cols)
    return incache, tosearch


def temporary_merge(df, table, merge_cols, file):
    """Perform merge with temp table and `table` and retrieve all columns."""
    c, conn = cache_connect(file=file)
    conditions = " and ".join(["a.{0}=b.{0}".format(c) for c in merge_cols])
    q = "SELECT b.* FROM temp AS a INNER JOIN {} AS b ON {};".format(
        table, conditions)
    return pd.read_sql_query(q, conn)
