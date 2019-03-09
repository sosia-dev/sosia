import pandas as pd
import copy
import sqlite3
import numpy as np

from sosia.utils import CACHE_SQLITE

conn = sqlite3.connect(CACHE_SQLITE)
c = conn.cursor()
sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))

def sources_in_cache(df):
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
    """
    c.execute('''DROP TABLE IF EXISTS sources_insearch''')
    c.execute('''CREATE TABLE IF NOT EXISTS sources_insearch
             (source_id int, year integer,
             PRIMARY KEY(source_id,year))''')
    query='''INSERT INTO sources_insearch (source_id,year) values (?,?) '''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    incache = pd.read_sql_query("""SELECT a.source_id, a.year, b.auids 
                              from sources_insearch as a 
                              INNER JOIN sources as b on a.source_id=b.source_id
                              and a.year=b.year;""", conn)
    if not incache.empty:
        incache['auids'] = incache.apply(lambda x: x['auids'].split(','), axis=1)
        df = df.set_index(['source_id','year'])
        incache = incache.set_index(['source_id','year'])
        tosearch = df[~(df.index.isin(incache.index))]
        incache.reset_index(inplace=True)
        if not tosearch.empty:
            tosearch.reset_index(inplace=True)[['source_id','year']]
        else:
            tosearch = pd.DataFrame(columns=['source_id','year'])
    else: 
        tosearch = df
    return incache, tosearch

def d_to_df_for_cache(d, source_id):
    """Function to create a DataFrame of sources, years and list of authors
    from a dictionary where keys are the years and values are the list of
    authors.

    Parameters
    ----------
    d : dict
        dictionary where keys are the years and values are the list of authors.
        
    source_id: int
        Scopus identifier of the source.
    """
    d2 = copy.deepcopy(d)
    for y in d2:
        d2[y] = [d2[y]]
    df = pd.DataFrame.from_dict(d2, orient='index')
    df.reset_index(inplace=True)
    df.columns = ['year','auids']
    df['source_id'] = str(source_id)
    return df

def cache_sources(df):
    """Insert new sources and year list of authors in cache.

    Parameters
    ----------
    df : DataFrame
        Dataframe with source, year and list of authors.
    """
    df['auids'] = df.apply(lambda x: ','.join([str(a) for a in x['auids']])
                                     , axis=1)
    df = df[['source_id','year','auids']] 
    query='''INSERT INTO sources (source_id,year,auids) values (?,?,?) '''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()

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
    c.execute('''DROP TABLE IF EXISTS authors_insearch''')
    c.execute('''CREATE TABLE IF NOT EXISTS authors_insearch
             (auth_id int, PRIMARY KEY(auth_id))''')
    query='''INSERT INTO authors_insearch (auth_id) values (?) '''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    incache = pd.read_sql_query("""SELECT b.* from authors_insearch as a 
                              INNER JOIN authors as b on a.auth_id=b.auth_id;
                              """, conn)
    tosearch = df.auth_id.tolist()
    if not incache.empty:
        incache_list = incache.auth_id.tolist()
        tosearch = [au for au in tosearch if au not in incache_list]
    return incache, tosearch


def cache_authors(df):
    """Insert new authors informaiton in cache.

    Parameters
    ----------
    df : DataFrame
        Dataframe with authors information.
    """
    query='''INSERT INTO authors (auth_id, eid, surname, initials,
                    givenname, affiliation, documents, affiliation_id,
                    city, country, areas) values (?,?,?,?,?,?,?,?,?,?,?)'''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()


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
    c.execute('''DROP TABLE IF EXISTS author_year_insearch''')
    c.execute('''CREATE TABLE IF NOT EXISTS author_year_insearch
             (auth_id int, year int, PRIMARY KEY(auth_id, year))''')
    query='''INSERT INTO author_year_insearch (auth_id, year) values (?,?) '''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()
    incache = pd.read_sql_query("""SELECT b.* from author_year_insearch as a 
                              INNER JOIN author_year as b 
                              on a.auth_id=b.auth_id and a.year=b.year;""",
                              conn)
    if not incache.empty:
        df = df.set_index(['auth_id','year'])
        incache = incache.set_index(['auth_id','year'])
        tosearch = df[~(df.index.isin(incache.index))]
        incache.reset_index(inplace=True)
        if not tosearch.empty:
            tosearch.reset_index(inplace=True)
        else:
            tosearch = pd.DataFrame(columns=['auth_id', 'year', 'n_pubs',
                                             'n_coauth', 'first_year'])
    else: 
        tosearch = df
    return incache, tosearch

def cache_author_year(df):
    """Insert new authors publication information up to year in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors publication information up to year of the event.
    """
    query='''INSERT INTO author_year (auth_id, year, first_year, n_pubs, n_coauth)
                                     values (?,?,?,?,?) '''
    conn.executemany(query, df.to_records(index=False))
    conn.commit()