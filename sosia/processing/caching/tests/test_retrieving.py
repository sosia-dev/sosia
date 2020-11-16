# -*- coding: utf-8 -*-
"""Tests for processing.caching.retrieving module."""

from itertools import product
from nose.tools import assert_equal, assert_true
import numpy as np
from os.path import expanduser

import pandas as pd
from pybliometrics.scopus import ScopusSearch, AuthorSearch
from pandas.testing import assert_frame_equal

from sosia.establishing import connect_database, make_database
from sosia.processing import build_dict, insert_data, retrieve_authors,\
    retrieve_author_info, retrieve_authors_from_sourceyear, robust_join,\
    query_pubs_by_sourceyear

test_cache = expanduser("~/.sosia/test.sqlite")
refresh = 30


def test_retrieve_authors():
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    expected_auth = [53164702100, 57197093438]
    df = pd.DataFrame(expected_auth, columns=["auth_id"], dtype="int64")
    expected_cols = ['auth_id', 'eid', 'surname', 'initials', 'givenname',
                     'affiliation', 'documents', 'affiliation_id', 'city',
                     'country', 'areas']
    # Retrieve data
    incache, missing = retrieve_authors(df, conn)
    assert_equal(incache.shape[0], 0)
    assert_equal(incache.columns.to_list(), expected_cols)
    assert_equal(missing, expected_auth)


def test_retrieve_authors_insert():
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
    res = pd.DataFrame(AuthorSearch(q, refresh=refresh).authors, dtype="int64")
    res["auth_id"] = res["eid"].str.split("-").str[-1]
    res = res[expected_cols]
    insert_data(res, conn, table="authors")
    # Retrieve data
    df = pd.DataFrame(expected_auth + search_auth, columns=["auth_id"],
                      dtype="int64")
    incache, missing = retrieve_authors(df, conn)
    assert_equal(incache.shape[0], 2)
    assert_equal(missing, [55317901900])


def test_retrieve_author_info_authorpubs():
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    table = "author_pubs"
    data = {"auth_id": [53164702100, 53164702100],
            "year": [2010, 2017], "n_pubs": [0, 6]}
    expected = pd.DataFrame(data, dtype="int64")
    # Insert data
    insert_data(expected.iloc[0].values, conn, table=table)
    insert_data(expected.iloc[1].values, conn, table=table)
    # Retrieve data
    cols = ["auth_id", "year"]
    incache, tosearch = retrieve_author_info(expected[cols], conn, table)
    assert_frame_equal(incache, expected)
    assert_true(tosearch.empty)


def test_retrieve_author_info_authorncits():
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    table = "author_ncits"
    data = {"auth_id": [53164702100, 53164702100],
            "year": [2010, 2017], "n_cits": [0, 6]}
    expected = pd.DataFrame(data, dtype="int64")
    # Insert data
    insert_data(expected, conn, table=table)
    # Retrieve data
    cols = ["auth_id", "year"]
    incache, tosearch = retrieve_author_info(expected[cols], conn, table)
    assert_frame_equal(incache, expected)
    assert_true(tosearch.empty)


def test_retrieve_author_info_authoryear():
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    table = "author_year"
    expected_auth = [53164702100, 57197093438]
    search_auth = [55317901900]
    year = 2016
    df2 = pd.DataFrame(expected_auth + search_auth,
                       columns=["auth_id"], dtype="int64")
    df2["year"] = year
    # Insert data
    fill = robust_join(expected_auth, sep=') OR AU-ID(')
    q = f"(AU-ID({fill})) AND PUBYEAR BEF {year+1}"
    d = build_dict(ScopusSearch(q, refresh=refresh).results, expected_auth)
    expected = pd.DataFrame.from_dict(d, orient="index", dtype="int64")
    expected = expected.sort_index().rename_axis('auth_id').reset_index()
    expected["year"] = year
    expected = expected[['auth_id', 'year', 'first_year', 'n_pubs', 'n_coauth']]
    insert_data(expected, conn, table=table)
    # Retrieve data
    incache, missing = retrieve_author_info(df2, conn, table)
    assert_frame_equal(incache, expected)
    assert_equal(missing['auth_id'].tolist(), search_auth)
    assert_equal(missing['year'].tolist(), [year])


def test_retrieve_authors_from_sourceyear():
    make_database(test_cache, drop=True)
    conn = connect_database(test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2005, 2010]
    df = pd.DataFrame(product(expected_sources, expected_years),
                      columns=["source_id", "year"], dtype="int64")
    # Populate cache
    expected = query_pubs_by_sourceyear(expected_sources, expected_years[0],
                                        refresh=refresh)
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
