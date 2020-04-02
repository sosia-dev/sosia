import pandas as pd

from sosia.processing.utils import flat_set_from_df
from sosia.processing.caching.inserting import insert_temporary_table
from sosia.processing.caching.utils import temporary_merge


def retrieve_author_cits(df, conn):
    """Search authors citations in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search in a year.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: pd.DataFrame
        List of authors not in cache.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, conn, merge_cols=cols)
    incache = temporary_merge(df, conn, "author_cits_size", merge_cols=cols)
    if not incache.empty:
        df = df.set_index(cols)
        incache = incache.set_index(cols)
        tosearch = df[~(df.index.isin(incache.index))]
        incache = incache.reset_index()
        tosearch = tosearch.reset_index()
    else:
        tosearch = df
    return incache, tosearch


def retrieve_authors(df, conn):
    """Search authors in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: list
        List of authors not in cache.
    """
    cols = ["auth_id"]
    insert_temporary_table(df, merge_cols=cols, conn=conn)
    incache = temporary_merge(df, conn, "authors", merge_cols=cols)
    tosearch = df.auth_id.tolist()
    if not incache.empty:
        incache_list = incache.auth_id.tolist()
        tosearch = [int(au) for au in tosearch if int(au) not in incache_list]
    return incache, tosearch


def retrieve_authors_year(df, conn):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: DataFrame
        DataFrame of authors not in cache with year of the event as second
        column.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, conn, merge_cols=cols)
    incache = temporary_merge(df, conn, "author_year", merge_cols=cols)
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


def retrieve_author_pubs(df, conn):
    """Search author's publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
    """
    cols = ["auth_id", "year"]
    insert_temporary_table(df, conn, merge_cols=cols)
    incache = temporary_merge(df, conn, "author_size", merge_cols=cols)
    if incache.empty:
        incache = pd.DataFrame()
    return incache


def retrieve_sources(tosearch, conn, refresh=False, afid=False):
    """Search sources by year in SQL database.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of sources and years combinations to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    afid : bool (optional, default=False)
        If True, search in sources_afids table.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in database.

    tosearch: DataFrame
        DataFrame of sources and years combinations not in database.
    """
    cursor = conn.cursor()
    cols = ["source_id", "year"]
    insert_temporary_table(tosearch, conn, merge_cols=cols)
    table = "sources"
    select = "a.source_id, a.year, b.auids"
    if afid:
        table += "_afids"
        select += ", b.afid"
    q = f"SELECT {select} FROM temp AS a INNER JOIN {table} AS b "\
        "ON a.source_id=b.source_id AND a.year=b.year;"
    incache = pd.read_sql_query(q, conn)
    if not incache.empty:
        incache["auids"] = incache["auids"].str.split(",")
        tosearch = tosearch.merge(incache, "left", on=cols, indicator=True)
        tosearch = tosearch[tosearch["_merge"] == "left_only"][cols]
        if refresh:
            auth_incache = pd.DataFrame(flat_set_from_df(incache, "auids"),
                                        columns=["auth_id"], dtype="uint64")
            tables = ("authors", "author_size", "author_cits_size", "author_year")
            for table in tables:
                q = f"DELETE FROM {table} WHERE auth_id=?"
                cursor.executemany(q, auth_incache.to_records(index=False))
                conn.commit()
            tables = ("sources", "sources_afids")
            for table in tables:
                q = f"DELETE FROM {table} WHERE source_id=? AND year=?"
                cursor.executemany(q, tosearch.to_records(index=False))
                conn.commit()
            incache = pd.DataFrame(columns=incache.columns)
    if tosearch.empty:
        tosearch = pd.DataFrame(columns=cols)
    return incache, tosearch
