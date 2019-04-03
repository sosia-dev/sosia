from copy import deepcopy

import numpy as np
import pandas as pd
import sqlite3

from sosia.utils import CACHE_SQLITE

conn = sqlite3.connect(CACHE_SQLITE)
c = conn.cursor()
sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))


def cache_sources(df):
    """Insert new sources and year list of authors in cache.

    Parameters
    ----------
    df : DataFrame
        Dataframe with source, year and list of authors.
    """
    df["auids"] = df.apply(lambda x: ",".join([str(a) for a in x["auids"]]), axis=1)
    df = df[["source_id", "year", "auids"]]
    query = """INSERT INTO sources (source_id,year,auids) values (?,?,?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()


def cache_authors(df):
    """Insert new authors informaiton in cache.

    Parameters
    ----------
    df : DataFrame
        Dataframe with authors information.
    """
    query = """INSERT OR IGNORE INTO authors (auth_id, eid, surname, initials,
        givenname, affiliation, documents, affiliation_id, city, country,
        areas) values (?,?,?,?,?,?,?,?,?,?,?)"""
    conn.executemany(query, df.to_records(index=False))
    conn.commit()


def cache_author_year(df):
    """Insert new authors' publication information up to year in cache.

    Parameters
    ----------
    df : DataFrame
        DataFrame of authors publication information up to year of the event.
    """
    query = """INSERT INTO author_year (auth_id, year, first_year, n_pubs,
        n_coauth) values (?,?,?,?,?) """
    conn.executemany(query, df.to_records(index=False))
    conn.commit()


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
    d2 = deepcopy(d)
    for y in d2:
        d2[y] = [d2[y]]
    df = pd.DataFrame.from_dict(d2, orient="index").reset_index()
    df.columns = ["year", "auids"]
    df["source_id"] = str(source_id)
    return df
