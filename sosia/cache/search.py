import numpy as np
import pandas as pd
import sqlite3

from sosia.utils import CACHE_SQLITE

conn = sqlite3.connect(CACHE_SQLITE)
c = conn.cursor()
sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))


def authors_in_cache(df):
    """Search authors in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
        
    tosearch: list
        List of authors not in cache. 
    """
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
        tosearch = [au for au in tosearch if au not in incache_list]
    return incache, tosearch


def author_year_in_cache(df):
    """Search authors publication information up to year of event in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors to search with year of the event as second column.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
        
    tosearch: DataFrame
        DataFrame of authors not in cache with year of the event as second
        column. 
    """
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
        if not tosearch.empty:
            tosearch.reset_index(inplace=True)
        else:
            cols = ["auth_id", "year", "n_pubs", "n_coauth", "first_year"]
            tosearch = pd.DataFrame(columns=cols)
    else:
        tosearch = df
    return incache, tosearch


def sources_in_cache(df, refresh=False):
    """Search sources by year in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of sources and years combinations to search.

    Returns
    -------
    incache : DataFrame
        DataFrame of results found in cache.
        
    tosearch: DataFrame
        DataFrame of sources and years combinations not in cache.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files. 
    """
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
        if not tosearch.empty:
            tosearch.reset_index(inplace=True)[["source_id", "year"]]
        else:
            tosearch = pd.DataFrame(columns=["source_id", "year"])
    else:
        tosearch = df
    if refresh:
        if not incache.empty:
            auth_incache = set([au for l in incache.auids.tolist() for au in l])
            auth_incache = pd.DataFrame(auth_incache, columns=["auth_id"], dtype="int64")
            df.reset_index(inplace=True)
            query = "DELETE FROM authors WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            query = "DELETE FROM author_year WHERE auth_id=? "
            conn.executemany(query, auth_incache.to_records(index=False))
            query = """DELETE FROM sources WHERE source_id=? AND year=?"""
            conn.executemany(query, df.to_records(index=False))
            incache = pd.DataFrame(columns=["source_id", "year"])
        tosearch = df
    return incache, tosearch
