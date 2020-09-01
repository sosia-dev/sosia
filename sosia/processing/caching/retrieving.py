import pandas as pd

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
    incache = temporary_merge(conn, "author_ncits", merge_cols=cols)
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
    incache = temporary_merge(conn, "authors", merge_cols=cols)
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
    incache = temporary_merge(conn, "author_year", merge_cols=cols)
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
    incache = temporary_merge(conn, "author_pubs", merge_cols=cols)
    if incache.empty:
        incache = pd.DataFrame()
    return incache


def retrieve_authors_from_sourceyear(tosearch, conn, refresh=False, stacked=False):
    """Search through sources by year for authors in SQL database.

    Parameters
    ----------
    tosearch : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    stacked : bool (optional, default=False)
        Whether to use fewer queries that are not reusable, or to use modular
        queries of the form "SOURCE-ID(<SID>) AND PUBYEAR IS <YYYY>".

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids", "afid"), where
        entries correspond to an individual paper.

    missing: DataFrame
        DataFrame of source-year-combinations not in SQL database.
    """
    # Preparation
    cursor = conn.cursor()
    if refresh:
        tables = ("sources", "sources_afids")
        for table in tables:
            q = f"DELETE FROM {table} WHERE source_id=? AND year=?"
            cursor.executemany(q, tosearch.to_records(index=False))
            conn.commit()

    # Query selected data using left join
    cols = ["source_id", "year"]
    insert_temporary_table(tosearch.copy(), conn, merge_cols=cols)
    q = "SELECT a.source_id, a.year, b.auids, b.afid FROM temp AS a "\
        "LEFT JOIN sources_afids AS b "\
        "ON a.source_id=b.source_id AND a.year=b.year;"
    data = pd.read_sql_query(q, conn)
    data = data.sort_values(["source_id", "year"]).reset_index(drop=True)

    # Finalize
    mask_missing = data["auids"].isna()
    incache = data[~mask_missing]
    missing = data.loc[mask_missing, cols].drop_duplicates()
    return incache, missing
