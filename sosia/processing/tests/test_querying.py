# -*- coding: utf-8 -*-
"""Tests for processing.querying module."""

from os.path import expanduser

import pandas as pd
from nose.tools import assert_equal, assert_true
from string import Template

from sosia.establishing import connect_database
from sosia.processing import base_query, count_citations, query_author_data,\
    query_journal, query_year, stacked_query

test_cache = expanduser("~/.sosia/test.sqlite")
test_conn = connect_database(test_cache)
test_id = 53164702100
year = 2017
refresh = 30


def test_base_query():
    q = f"AU-ID({test_id}) AND PUBYEAR BEF {year}"
    size = base_query("docs", q, size_only=True)
    assert_equal(size, 5)


def test_base_query_author():
    query = f"AU-ID({test_id})"
    size = base_query("author", query, size_only=True)
    assert_equal(size, 1)


def test_count_citations():
    identifier = ["55208373700", "55208373700"]
    count1 = count_citations(identifier, 2017)
    assert_equal(count1, 23)
    eids = ["2-s2.0-84959420483", "2-s2.0-84949113230"]
    count2 = count_citations(eids, 2017, exclusion_ids=identifier)
    assert_equal(count2, 1)
    eids_long = eids * 200
    count3 = count_citations(eids_long, 2017, exclusion_ids=identifier)
    assert_equal(count3, 4)


def test_query_author_data():
    auth_list = [6701809842, 55208373700]
    auth_data = query_author_data(auth_list, test_conn, refresh=refresh)
    assert_true(isinstance(auth_data,  pd.DataFrame))
    expected_cols = ["auth_id", "eid", "surname", "initials", "givenname",
                     "affiliation", "documents", "affiliation_id", "city",
                     "country", "areas"]
    assert_equal(auth_data.columns.tolist(), expected_cols)
    assert_equal(auth_data["auth_id"].tolist(), auth_list)
    assert_equal(auth_data["surname"].tolist(), ["Harhoff", "Baruffaldi"])


def test_query_journal():
    # test a journal with more than 5k publications in one year
    res = query_journal("11000153773", [2006], refresh=refresh)
    assert_true(24100 < len(res.get("2006")) < 25000)


def test_query_year():
    # test a journal and year
    res = query_year(2010, [22900], refresh=refresh, verbose=False)
    assert_equal(res["source_id"].tolist(), ['22900'])
    assert_equal(res["year"].tolist(), ['2010'])
    assert_true(isinstance(res["auids"][0], list))
    assert_true(len(res["auids"][0]) > 0)
    # test a journal and year that are not in Scopus
    res = query_year(1969, [22900], refresh=refresh, verbose=False)
    assert_true(res.empty)
    # test a large query (>5000 scopus results)
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]
    res = query_year(1984, source_ids, refresh=refresh, verbose=False)
    assert_true(len(res[~res["auids"].isnull()]) == 17)
    assert_true(isinstance(res["auids"][0], list))
    assert_true(len(res["auids"][0]) > 0)


def test_query_year_afid():
    # test keeping affiliation id column
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]
    res = query_year(1984, source_ids, refresh=refresh, verbose=True, afid=True)
    expected = range(3395-5, 3395+5)
    assert_true(len(res[~res["auids"].isnull()]) in expected)
    assert_true(res.columns.tolist(), ['source_id', 'year', 'afid', 'auids'])
    assert_true(len(res["auids"][0]) > 0)


def test_stacked_query():
    # test a query with one journal-year above 5000
    group = [18400156716, 19300157101, 19400157208, 19400157312, 19500157223,
             19600166213, 19700175482, 19700182353, 19800188009, 19900193211,
             20100195028, 21100208103, 21100225839, 21100228010, 21100244622,
             21100246535, 21100246537, 21100285035, 21100313905, 21100329904,
             21100370441, 21100370876, 21100416121, 21100775937, 21100871308,
             25674]
    template = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year+1}")
    res = []
    stacked_query(group, res, template, joiner=" OR ", q_type="docs",
                  refresh=refresh)
    assert_equal(len(res), 25909)