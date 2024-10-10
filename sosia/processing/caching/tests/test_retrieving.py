"""Tests for processing.caching.retrieving module."""

from itertools import product

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from pybliometrics.scopus import AuthorSearch

from sosia.establishing import connect_database, make_database
from sosia.processing import insert_data, retrieve_from_author_table, \
    retrieve_authors_from_sourceyear, robust_join, query_pubs_by_sourceyear


def test_retrieve_from_author_table(test_cache):
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    expected_auth = [53164702100, 57197093438]
    df = pd.DataFrame(expected_auth, columns=["auth_id"], dtype="int64")
    expected_cols = ['auth_id', 'surname', 'givenname', 'documents', 'areas']
    # Retrieve data
    incache, missing = retrieve_from_author_table(df, conn, table="author_info")
    assert incache.shape[0] == 0
    assert incache.columns.to_list() == expected_cols
    assert missing == expected_auth


def test_retrieve_from_author_table_insert(test_cache, refresh_interval):
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    expected_auth = [53164702100, 57197093438]
    search_auth = [55317901900]
    expected_cols = ['auth_id', 'eid', 'surname', 'initials', 'givenname',
                     'affiliation', 'documents', 'affiliation_id', 'city',
                     'country', 'areas']
    # Insert data
    q = f"AU-ID({robust_join(expected_auth, sep=') OR AU-ID(')})"
    res = pd.DataFrame(AuthorSearch(q, refresh=refresh_interval).authors)
    res["auth_id"] = res["eid"].str.split("-").str[-1].astype("int64")
    res["affiliation_id"] = res["affiliation_id"].astype(float)
    res = res[expected_cols]
    insert_data(res, conn, table="author_info")
    # Retrieve data
    df = pd.DataFrame(expected_auth + search_auth, columns=["auth_id"],
                      dtype="uint64")
    incache, missing = retrieve_from_author_table(df, conn, table="author_info")
    assert incache.shape[0] == 2
    assert missing == [55317901900]


def test_retrieve_authors_from_sourceyear(test_cache, refresh_interval):
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2005, 2010]
    df = pd.DataFrame(product(expected_sources, expected_years),
                      columns=["source_id", "year"], dtype="int64")
    # Populate cache
    expected = query_pubs_by_sourceyear(expected_sources, expected_years[0],
                                        refresh=refresh_interval)
    expected["source_id"] = expected["source_id"].astype(np.int64)
    expected["afid"] = expected["afid"].astype(int).astype(str)
    expected = expected.sort_values(["auids", "afid"]).reset_index(drop=True)
    expected = expected[['source_id', 'year', 'auids', 'afid']]
    expected["auids"] = expected["auids"].str.split(";")
    insert_data(expected, conn, table="sources_afids")
    # Retrieve from cache
    incache, missing = retrieve_authors_from_sourceyear(df, conn)
    incache["afid"] = incache["afid"].astype(int).astype(str)
    incache = incache.sort_values(["auids", "afid"]).reset_index(drop=True)
    assert_frame_equal(incache, expected)
    assert_frame_equal(missing, df.tail(1).reset_index(drop=True))
