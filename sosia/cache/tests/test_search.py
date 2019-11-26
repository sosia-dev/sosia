#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for cache module."""

from nose.tools import assert_equal, assert_true
from itertools import product
from os.path import expanduser

import pandas as pd
from pybliometrics.scopus import ScopusSearch, AuthorSearch
from pandas.testing import assert_frame_equal
from sosia.utils import config

from sosia.cache import authors_in_cache, author_size_in_cache,\
    author_year_in_cache, cache_insert, sources_in_cache
from sosia.processing import query_year
from sosia.utils import build_dict, create_cache


test_cache = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
config["Cache"]["File path"] = test_cache

def test_authors_in_cache():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_auth = ["53164702100", "57197093438"]
    search_auth = ["55317901900"]
    # Test empty cache
    df1 = pd.DataFrame(expected_auth, columns=["auth_id"], dtype="int64")
    incache, tosearch = authors_in_cache(df1, file=test_cache)
    expected_cols = ['auth_id', 'eid', 'surname', 'initials', 'givenname',
                     'affiliation', 'documents', 'affiliation_id', 'city',
                     'country', 'areas']
    expected_auth = [int(au) for au in expected_auth]
    assert_equal(tosearch, expected_auth)
    assert_equal(len(incache), 0)
    assert_equal(incache.columns.tolist(), expected_cols)
    # Test partial retrieval
    q = "AU-ID({})".format(') OR AU-ID('.join([str(a) for a in expected_auth]))
    res = pd.DataFrame(AuthorSearch(q).authors, dtype="int64")
    res["auth_id"] = res["eid"].str.split("-").str[-1]
    res = res[expected_cols]
    cache_insert(res, table="authors", file=test_cache)
    df2 = pd.DataFrame(expected_auth + search_auth, columns=["auth_id"],
                       dtype="int64")
    incache, tosearch = authors_in_cache(df2, file=test_cache)
    assert_equal(tosearch, [55317901900])
    assert_equal(len(incache), 2)
    # Test full retrieval
    incache, tosearch = authors_in_cache(df1, file=test_cache)
    assert_equal(tosearch, [])
    assert_equal(len(incache), 2)


def test_author_year_in_cache():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_auth = ["53164702100", "57197093438"]
    search_auth = ["55317901900"]
    year = 2016
    # Test empty cache
    df1 = pd.DataFrame(expected_auth, columns=["auth_id"],
                       dtype="int64")
    df1["year"] = year
    auth_y_incache, auth_y_search = author_year_in_cache(df1, file=test_cache)
    assert_frame_equal(auth_y_search, df1)
    assert_equal(len(auth_y_incache), 0)
    # Test partial retrieval
    fill = ') OR AU-ID('.join([str(a) for a in expected_auth])
    q = "(AU-ID({})) AND PUBYEAR BEF {}".format(fill, year+1)
    res = build_dict(ScopusSearch(q).results, expected_auth)
    res = pd.DataFrame.from_dict(res, orient="index", dtype="int64")
    res["year"] = year
    cols = ["year", "first_year", "n_pubs", "n_coauth"]
    res = res[cols].reset_index().rename(columns={"index": "auth_id"})
    cache_insert(res, table="author_year", file=test_cache)
    df2 = pd.DataFrame(expected_auth + search_auth,
                       columns=["auth_id"], dtype="int64")
    df2["year"] = year
    auth_y_incache, auth_y_search = author_year_in_cache(df2, file=test_cache)
    expected_auth = [int(au) for au in expected_auth]
    search_auth = [int(au) for au in search_auth]
    assert_equal(sorted(auth_y_incache.auth_id.tolist()), expected_auth)
    assert_equal(auth_y_incache.year.tolist(), [year, year])
    assert_equal(auth_y_search.auth_id.tolist(), search_auth)
    assert_equal(auth_y_search.year.tolist(), [year])
    # Test full retrieval
    auth_year_incache, auth_year_search = author_year_in_cache(df1, file=test_cache)
    assert_equal(sorted(auth_year_incache.auth_id.tolist()), expected_auth)
    assert_equal(auth_year_incache.year.tolist(), [year, year])
    assert_true(auth_year_search.empty)


def test_author_size_in_cache():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_auth = 53164702100
    expected_years = [2010, 2017]
    pubs1 = 0
    pubs2 = 6
    cols = ["auth_id", "year"]
    df = pd.DataFrame(list(product([expected_auth], expected_years)),
                      columns=cols, dtype="int64")
    # Test empty cache
    size = author_size_in_cache(df, file=test_cache)
    assert_equal(len(size), 0)
    assert_true(isinstance(size, pd.DataFrame))
    # Test adding to and retrieving from cache
    tp1 = (expected_auth, expected_years[0], pubs1)
    cache_insert(tp1, table="author_size", file=test_cache)
    tp2 = (expected_auth, expected_years[1], pubs2)
    cache_insert(tp2, table="author_size", file=test_cache)
    size = author_size_in_cache(df, file=test_cache)
    assert_equal(len(size), 2)
    assert_frame_equal(size[cols], df)
    assert_equal(size[size.year == expected_years[0]]["n_pubs"][0], pubs1)
    assert_equal(size[size.year == expected_years[1]]["n_pubs"][1], pubs2)


def test_sources_in_cache_empty():
    create_cache(drop=True, file=test_cache)
    df = pd.DataFrame(list(product([22900], [2010, 2005])),
                      columns=["source_id", "year"], dtype="int64")
    sources_ys_incache, sources_ys_search = sources_in_cache(df, file=test_cache)
    assert_frame_equal(sources_ys_search, df)
    assert_true(sources_ys_incache.empty)


def test_sources_in_cache_partial():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2010, 2005]
    df = pd.DataFrame(list(product(expected_sources, expected_years)),
                      columns=["source_id", "year"], dtype="int64")
    # Populate cache
    res = query_year(expected_years[0], expected_sources, False, False)
    cache_insert(res, table="sources", file=test_cache)
    # Retrieve from cache
    sources_ys_incache, sources_ys_search = sources_in_cache(df, file=test_cache)
    expected_sources = [int(s) for s in expected_sources]
    assert_equal(sources_ys_incache.source_id.tolist(), expected_sources)
    assert_equal(sources_ys_incache.year.tolist(), [expected_years[0]])
    assert_equal(sources_ys_search.source_id.tolist(), expected_sources)
    assert_equal(sources_ys_search.year.tolist(), [expected_years[1]])


def test_sources_in_cache_full():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2010, 2005]
    cols = ["source_id", "year"]
    df = pd.DataFrame(list(product(expected_sources, expected_years)),
                      columns=cols, dtype="int64")
    # Populate cache
    res = query_year(expected_years[0], expected_sources, False, False)
    cache_insert(res, table="sources", file=test_cache)
    sources_ys_incache, sources_ys_search = sources_in_cache(df, file=test_cache)
    # Retrieve from cache
    sources_ys = sources_ys_incache[cols]
    sources_ys_incache, sources_ys_search = sources_in_cache(sources_ys,
                                                             file=test_cache)
    expected_sources = [int(s) for s in expected_sources]
    assert_equal(sources_ys_incache.source_id.tolist(), expected_sources)
    assert_equal(sources_ys_incache.year.tolist(), [expected_years[0]])
    assert_true(sources_ys_search.empty)
    

def test_sources_afids_in_cache_empty():
    create_cache(drop=True, file=test_cache)
    df = pd.DataFrame(list(product([22900], [2010, 2005])),
                      columns=["source_id", "year"], dtype="int64")
    sa_incache, sa_search = sources_in_cache(df, file=test_cache, afid=True)
    assert_frame_equal(sa_search, df)
    assert_true(sa_incache.empty)


def test_sources_afids_in_cache_partial():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2010, 2005]
    df = pd.DataFrame(list(product(expected_sources, expected_years)),
                      columns=["source_id", "year"], dtype="int64")
    sa_incache, sa_search = sources_in_cache(df, file=test_cache, afid=True)
    # Populate cache
    res = query_year(expected_years[0], expected_sources, False, False, afid=True)
    cache_insert(res, table="sources_afids", file=test_cache)
    # Retrieve from cache
    sa_incache, sa_search = sources_in_cache(df, file=test_cache, afid=True)
    expected_sources = set([int(s) for s in expected_sources])
    assert_equal(set(sa_incache.source_id.tolist()), set(expected_sources))
    assert_equal(set(sa_incache.year.tolist()), set([expected_years[0]]))
    assert_equal(set(sa_search.source_id.tolist()), set(expected_sources))
    assert_equal(set(sa_search.year.tolist()), set([expected_years[1]]))
    expected = range(182-5, 182+5)
    assert_true(len(sa_incache) in expected)
    assert_true(len(sa_incache.afid.drop_duplicates()) in expected)


def test_sources_afids_in_cache_full():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2010, 2005]
    cols = ["source_id", "year"]
    df = pd.DataFrame(list(product(expected_sources, expected_years)),
                      columns=cols, dtype="int64")
    # Populate cache
    res = query_year(expected_years[0], expected_sources, False, False, afid=True)
    cache_insert(res, table="sources_afids", file=test_cache)
    # Retrieve from cache
    sa_incache, sa_search = sources_in_cache(df, file=test_cache, afid=True)
    sources_ys = sa_incache[cols].drop_duplicates()
    sa_incache, sa_search = sources_in_cache(sources_ys, file=test_cache,
                                             afid=True)
    expected_sources = set([int(s) for s in expected_sources])
    assert_equal(set(sa_incache.source_id.tolist()), set(expected_sources))
    assert_equal(set(sa_incache.year.tolist()), set([expected_years[0]]))
    expected = range(182-5, 182+5)
    assert_true(len(sa_incache) in expected)
    assert_true(len(sa_incache.afid.drop_duplicates()) in expected)
    assert_true(sa_search.empty)


def test_sources_afids_in_sources_cache():
    create_cache(drop=True, file=test_cache)
    # Variables
    expected_sources = [22900]
    expected_years = [2010, 2005]
    df = pd.DataFrame(list(product(expected_sources, expected_years)),
                      columns=["source_id", "year"], dtype="int64")
    # Populate cache
    res = query_year(expected_years[0], expected_sources, False, False, afid=True)
    cache_insert(res, table="sources", file=test_cache)
    # Retrieve from cache
    sources_ys_incache, sources_ys_search = sources_in_cache(df, file=test_cache)
    expected_sources = [int(s) for s in expected_sources]
    assert_equal(sources_ys_incache.source_id.tolist(), expected_sources)
    assert_equal(sources_ys_incache.year.tolist(), [expected_years[0]])
    assert_equal(sources_ys_search.source_id.tolist(), expected_sources)
    assert_equal(sources_ys_search.year.tolist(), [expected_years[1]])

