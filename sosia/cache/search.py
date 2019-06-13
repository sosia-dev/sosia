import numpy as np
import pandas as pd

from sosia.utils import CACHE_SQLITE
from sosia.cache import cache_connect


def author_cits_in_cache(df, file=CACHE_SQLITE):
    """Search authors citations in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search in a year.

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: pd.DataFrame
        List of authors not in cache.
    """
    types = {"auth_id": int, "year": int}
    df.astype(types, inplace=True)
    c, conn = cache_connect(file=file)
    c.execute("""DROP TABLE IF EXISTS author_year_insearch""")
    c.execute("""CREATE TABLE IF NOT EXISTS author_year_insearch
        (auth_id int, year int, PRIMARY KEY(auth_id, year))""")
    query = """INSERT INTO author_year_insearch (auth_id, year) values (?,?)"""
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    query = """SELECT b.* from author_year_insearch as a INNER JOIN 
        author_cits_size as b on a.auth_id=b.auth_id and a.year=b.year;"""
    incache = pd.read_sql_query(query, conn)
    if not incache.empty:
        df = df.set_index(["auth_id", "year"])
        incache = incache.set_index(["auth_id", "year"])
        tosearch = df[~(df.index.isin(incache.index))]
        incache.reset_index(inplace=True)
        tosearch.reset_index(inplace=True)
    else:
        tosearch = df
    return incache, tosearch


def authors_in_cache(df, file=CACHE_SQLITE):
    """Search authors in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.

    tosearch: list
        List of authors not in cache.
    """
    types = {"auth_id": int}
    df.astype(types, inplace=True)
    c, conn = cache_connect(file=file)
    c.execute("""DROP TABLE IF EXISTS authors_insearch""")
    c.execute("""CREATE TABLE IF NOT EXISTS authors_insearch
              (auth_id int, PRIMARY KEY(auth_id))""")
    query = """INSERT OR IGNORE INTO authors_insearch (auth_id) values (?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    query = """SELECT b.* from authors_insearch as a
        INNER JOIN authors as b on a.auth_id=b.auth_id;"""
    incache = pd.read_sql_query(query, conn)
    tosearch = df.auth_id.tolist()
    if not incache.empty:
        incache_list = incache.auth_id.tolist()
        tosearch = [int(au) for au in tosearch if int(au) not in incache_list]
    return incache, tosearch


def author_year_in_cache(df, file=CACHE_SQLITE):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
        
    tosearch: DataFrame
        DataFrame of authors not in cache with year of the event as second
        column. 
    """
    types = {"auth_id": int, "year": int}
    df.astype(types, inplace=True)
    c, conn = cache_connect(file=file)
    c.execute("""DROP TABLE IF EXISTS author_year_insearch""")
    c.execute("""CREATE TABLE IF NOT EXISTS author_year_insearch
        (auth_id int, year int, PRIMARY KEY(auth_id, year))""")
    query = """INSERT INTO author_year_insearch (auth_id, year) values (?,?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    query = """SELECT b.* from author_year_insearch as a INNER JOIN 
        author_year as b on a.auth_id=b.auth_id and a.year=b.year;"""
    incache = pd.read_sql_query(query, conn)
    if not incache.empty:
        df = df.set_index(["auth_id", "year"])
        incache = incache.set_index(["auth_id", "year"])
        tosearch = df[~(df.index.isin(incache.index))]
        incache.reset_index(inplace=True)
        tosearch.reset_index(inplace=True)
        if tosearch.empty:
            cols = ["auth_id", "year", "n_pubs", "n_coauth", "first_year"]
            tosearch = pd.DataFrame(columns=cols)
    else:
        tosearch = df
    return incache, tosearch


def author_size_in_cache(df, file=CACHE_SQLITE):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
    """
    types = {"auth_id": int, "year": int}
    df.astype(types, inplace=True)
    c, conn = cache_connect(file=file)
    c.execute("""DROP TABLE IF EXISTS author_year_insearch""")
    c.execute("""CREATE TABLE IF NOT EXISTS author_year_insearch
        (auth_id int, year int, PRIMARY KEY(auth_id, year))""")
    query = """INSERT INTO author_year_insearch (auth_id, year) values (?,?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    query = """SELECT b.* from author_year_insearch as a INNER JOIN 
        author_size as b on a.auth_id=b.auth_id and a.year=b.year;"""
    incache = pd.read_sql_query(query, conn)
    if incache.empty:
        incache = pd.DataFrame()
    return incache


def sources_in_cache(df, refresh=False, file=CACHE_SQLITE):
    """Search sources by year in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of sources and years combinations to search.

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
        
    tosearch: DataFrame
        DataFrame of sources and years combinations not in cache.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files. 
    """
    types = {"source_id": int, "year": int}
    df.astype(types, inplace=True)
    c, conn = cache_connect(file=file)
    c.execute("""DROP TABLE IF EXISTS sources_insearch""")
    c.execute(
        """CREATE TABLE IF NOT EXISTS sources_insearch
             (source_id int, year integer,
             PRIMARY KEY(source_id,year))"""
    )      
    query = """INSERT INTO sources_insearch (source_id,year) values (?,?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    query = """SELECT a.source_id, a.year, b.auids 
        from sources_insearch as a 
        INNER JOIN sources as b on a.source_id=b.source_id
        and a.year=b.year;"""
    incache = pd.read_sql_query(query, conn)
    if not incache.empty:
        incache["auids"] = incache.apply(lambda x: x["auids"].split(","), axis=1)
        df = df.set_index(["source_id", "year"])
        incache = incache.set_index(["source_id", "year"])
        tosearch = df[~(df.index.isin(incache.index))]
        incache.reset_index(inplace=True)
        tosearch.reset_index(inplace=True)
        if tosearch.empty:
            tosearch = pd.DataFrame(columns=["source_id", "year"])
    else:
        tosearch = df
    if refresh:
        if not incache.empty:
            auth_incache = list(set([au for l in incache.auids.tolist() for au in l]))
            auth_incache = pd.DataFrame(auth_incache, columns=["auth_id"], dtype="int64")
            df.reset_index(inplace=True)
            query = "DELETE FROM authors WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            conn.commit()
            query = "DELETE FROM author_size WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            conn.commit()
            query = "DELETE FROM author_cits_size WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            conn.commit()
            query = "DELETE FROM author_year WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            conn.commit()
            query = """DELETE FROM sources WHERE source_id=? AND year=?"""
            conn.executemany(query, df.to_records(index=False))
            conn.commit()
            incache = pd.DataFrame(columns=["source_id", "year"])
        tosearch = df
    return incache, tosearch
