#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for cache module."""

from nose.tools import assert_equal, assert_true
from itertools import product
from os.path import expanduser

from scopus import ScopusSearch, AuthorSearch
import pandas as pd
from pandas.testing import assert_frame_equal

from sosia.cache import (authors_in_cache, author_year_in_cache,
                         author_size_in_cache, sources_in_cache,
                         cache_authors, cache_author_year, cache_author_size,
                         cache_sources)
from sosia.processing import query_year
from sosia.utils import build_dict, create_cache
   

def test_authors_in_cache():
    test_file = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
    create_cache(drop=True, file=test_file) 
    # test empty cache
    authors = [53164702100,54411022900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    incache, tosearch = authors_in_cache(authors_df, file=test_file)
    expected_columns = ['auth_id', 'eid', 'surname', 'initials', 'givenname',
                        'affiliation', 'documents', 'affiliation_id', 'city',
                        'country', 'areas']
    assert_equal(tosearch, authors)
    assert_equal(len(incache), 0)
    assert_equal(incache.columns.tolist(), expected_columns)
    # test partial retrieval
    q = 'AU-ID(' + ') OR AU-ID('.join([str(a) for a in authors]) + ')'
    res = AuthorSearch(q).authors
    res = pd.DataFrame(res)
    res["auth_id"] = res.apply(lambda x: x.eid.split("-")[-1], axis=1)
    res = res[["auth_id", "eid", "surname", "initials",
               "givenname", "affiliation", "documents",
               "affiliation_id", "city", "country","areas"]]
    cache_authors(res, file=test_file)
    authors = [53164702100,54411022900,55317901900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    incache, tosearch = authors_in_cache(authors_df, file=test_file)
    assert_equal(tosearch, [55317901900])
    assert_equal(len(incache), 2)
    # test full retrieval
    authors = [53164702100,54411022900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    incache, tosearch = authors_in_cache(authors_df, file=test_file)
    assert_equal(tosearch, [])
    assert_equal(len(incache), 2)


def test_author_year_in_cache():
    test_file = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
    create_cache(drop=True, file=test_file) 
    # test empty cache
    authors = [53164702100,54411022900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    authors_df["year"] = 2016
    author_year_incache, author_year_search = author_year_in_cache(authors_df,
                                                                file=test_file)
    assert_frame_equal(author_year_search, authors_df)
    assert_equal(len(author_year_incache), 0)
    # test partial retrieval
    q = ('AU-ID(' + ') OR AU-ID('.join([str(a) for a in authors]) + ')' +
         " AND PUBYEAR BEF 2017")
    res = ScopusSearch(q).results
    res = build_dict(res, authors)
    res = pd.DataFrame.from_dict(res, orient="index", dtype="int64")
    res["year"] = 2016
    res = res[["year", "first_year", "n_pubs", "n_coauth"]]
    res.reset_index(inplace=True)
    res.columns = ["auth_id", "year", "first_year", "n_pubs", "n_coauth"]
    cache_author_year(res, file=test_file)
    authors = [53164702100,54411022900,55317901900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    authors_df["year"] = 2016
    author_year_incache, author_year_search = author_year_in_cache(authors_df,
                                                                file=test_file)
    assert_equal(author_year_incache.auth_id.tolist(), [53164702100,54411022900])
    assert_equal(author_year_incache.year.tolist(), [2016,2016])
    assert_equal(author_year_search.auth_id.tolist(), [55317901900])
    assert_equal(author_year_search.year.tolist(), [2016])
    # test full retrieval
    authors = [53164702100,54411022900]
    authors_df = pd.DataFrame(authors, columns=["auth_id"], dtype="int64")
    authors_df["year"] = 2016
    author_year_incache, author_year_search = author_year_in_cache(authors_df,
                                                                file=test_file)
    assert_equal(author_year_incache.auth_id.tolist(), [53164702100,54411022900])
    assert_equal(author_year_incache.year.tolist(), [2016,2016])
    assert_true(author_year_search.empty)
    

def test_author_size_in_cache():
    test_file = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
    create_cache(drop=True, file=test_file) 
    # test empty cache
    group = [53164702100]
    years_check = [2010, 2017]
    authors_df = pd.DataFrame(list(product(group, years_check)),
                           columns=["auth_id", "year"])
    types = {"auth_id": int, "year": int}
    authors_df.astype(types, inplace=True)
    authors_size = author_size_in_cache(authors_df, file=test_file)
    assert_equal(len(authors_size), 0)
    assert_true(isinstance(authors_size,pd.DataFrame))
    # test add to cache...
    tp1 = (53164702100, 2010, 0)
    cache_author_size(tp1, file=test_file)
    tp2 = (53164702100, 2017, 6)
    cache_author_size(tp2, file=test_file)
    # ...and retrieve
    authors_size = author_size_in_cache(authors_df, file=test_file)
    assert_equal(len(authors_size), 2)
    assert_frame_equal(authors_size[["auth_id","year"]], authors_df)
    assert_equal(authors_size[authors_size.year==2010]["n_pubs"][0], 0)
    assert_equal(authors_size[authors_size.year==2017]["n_pubs"][1], 6)

    
def test_sources_in_cache():
    test_file = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
    create_cache(drop=True, file=test_file) 
    # test empty cache
    search_sources = [22900]
    _years_search = [2010,2005]
    sources_ys = pd.DataFrame(list(product(search_sources, _years_search)),
                              columns=["source_id", "year"])
    types = {"source_id": int, "year": int}
    sources_ys.astype(types, inplace=True)
    sources_ys_incache, sources_ys_search = sources_in_cache(sources_ys,
                                                             file=test_file)
    assert_frame_equal(sources_ys_search, sources_ys)
    assert_true(sources_ys_incache.empty)
    # test partial retrieval
    res = query_year(2010,search_sources,False,False)
    cache_sources(res, file=test_file)
    sources_ys_incache, sources_ys_search = sources_in_cache(sources_ys,
                                                             file=test_file)
    assert_equal(sources_ys_incache.source_id.tolist(), [22900])
    assert_equal(sources_ys_incache.year.tolist(), [2010])
    assert_equal(sources_ys_search.source_id.tolist(), [22900])
    assert_equal(sources_ys_search.year.tolist(), [2005])
    # test full retrieval
    sources_ys = sources_ys_incache[["source_id","year"]]
    sources_ys_incache, sources_ys_search = sources_in_cache(sources_ys,
                                                             file=test_file)
    assert_equal(sources_ys_incache.source_id.tolist(), [22900])
    assert_equal(sources_ys_incache.year.tolist(), [2010])
    assert_true(sources_ys_search.empty)
    