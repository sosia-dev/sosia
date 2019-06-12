from copy import deepcopy

import numpy as np
import pandas as pd
import sqlite3

from sosia.utils import CACHE_SQLITE


def cache_connect(file=CACHE_SQLITE):
    """Connect to cache file.

    Parameters
    ----------
    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.
    """
    conn = sqlite3.connect(file)
    c = conn.cursor()
    sqlite3.register_adapter(np.int64, lambda val: int(val))
    sqlite3.register_adapter(np.int32, lambda val: int(val))
    return c, conn


def cache_insert(data, table, file=CACHE_SQLITE):
    """Insert new authors information in cache.

    Parameters
    ----------
    data : DataFrame or 3-tuple
        Dataframe with authors information or (when table="source") a
        3-element tuple.

    table : string
        The database table to insert into.  The query will be adjusted
        accordingly.
        Allowed values: "authors", "author_cits_size", "author_year",
        "author_size", "sources".

    file : file (optional, default=CACHE_SQLITE)
        The cache file to connect to.

    Raises
    ------
    ValueError
        If parameter table is not one of the allowed values.
    """
    # Build query
    if table == 'authors':
        q = """INSERT OR IGNORE INTO authors (auth_id, eid, surname, initials,
            givenname, affiliation, documents, affiliation_id, city, country,
            areas) values (?,?,?,?,?,?,?,?,?,?,?)"""
        if data.empty:
            return None
        data["auth_id"] = data.apply(lambda x: x.eid.split("-")[-1], axis=1)
        cols = ["auth_id", "eid", "surname", "initials", "givenname",
                "affiliation", "documents", "affiliation_id", "city",
                "country", "areas"]
        data = data[cols]
    elif table == 'author_cits_size':
        q = """INSERT OR IGNORE INTO author_cits_size (auth_id, year, n_cits)
            values (?,?,?)"""
    elif table == 'author_year':
        q = """INSERT OR IGNORE INTO author_year (auth_id, year, first_year, n_pubs,
            n_coauth) values (?,?,?,?,?) """
    elif table == 'author_size':
        q = """INSERT OR IGNORE INTO author_size (auth_id, year, n_pubs)
            values ({},{},{}) """.format(data[0], data[1], data[2])
    elif table == "sources":
        if data.empty:
            return None
        data["auids"] = data.apply(lambda x: ",".join([str(a) for a in x["auids"]]), axis=1)
        data = data[["source_id", "year", "auids"]]
        q = """INSERT OR IGNORE INTO sources (source_id, year, auids) values 
            (?,?,?) """
    else:
        allowed_tables = ('authors', 'author_cits_size', 'author_year',
                          'author_size', 'sources')
        msg = 'table parameter must be one of ' + ', '.join(allowed_tables)
        raise ValueError(msg)
    # Perform caching
    _, conn = cache_connect(file=file)
    if table in ("authors", "author_cits_size", "author_year", "sources"):
        conn.executemany(q, data.to_records(index=False))
    else:
        conn.execute(q)
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
