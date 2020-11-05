# -*- coding: utf-8 -*-
"""Tests for processing.querying module."""

from os.path import expanduser

from nose.tools import assert_equal, assert_true
from string import Template

from sosia.establishing import connect_database
from sosia.processing import base_query, count_citations, create_queries,\
    query_pubs_by_sourceyear, stacked_query

test_cache = expanduser("~/.sosia/test.sqlite")
test_conn = connect_database(test_cache)
test_id = 53164702100
year = 2017
refresh = 30
query_missing_sourceid = "EID(2-s2.0-85042244066)"


def test_base_query():
    q = f"AU-ID({test_id}) AND PUBYEAR BEF {year}"
    size = base_query("docs", q, size_only=True)
    assert_equal(size, 5)


def test_base_query_author():
    query = f"AU-ID({test_id})"
    size = base_query("author", query, size_only=True)
    assert_equal(size, 1)
    # test robustness to missing source IDs
    fields = ["eid", "author_ids", "coverDate", "source_id"]
    res = base_query("docs", query_missing_sourceid, refresh, fields=fields)
    assert_equal(res[0].source_id, None)


def test_count_citations():
    identifier = ["55208373700", "55208373700"]
    count1 = count_citations(identifier, 2017)
    assert_equal(count1, 23)
    eids = ["2-s2.0-84959420483", "2-s2.0-84949113230"]
    count2 = count_citations(eids, 2017, exclusion_ids=identifier)
    assert_equal(count2, 1)
    eids_long = eids * 100
    count3 = count_citations(eids_long, 2017, exclusion_ids=identifier)
    assert_equal(count3, 1)


def test_create_queries_long():
    # Set variables
    group = list(range(1, 2000))
    template = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year+1}")
    joiner = " OR "
    maxlen = 200
    # Run test
    received = create_queries(group, joiner, template, maxlen)
    query_maxlen = max([len(q[0]) for q in received])
    # Compare
    assert_true(isinstance(received, list))
    assert_true(isinstance(received[0], tuple))
    assert_true(query_maxlen <= maxlen)
    expected = 'SOURCE-ID(1 OR 10 OR 100 OR 1000 OR 1001 OR 1002 OR 1003 OR '\
               '1004 OR 1005 OR 1006 OR 1007 OR 1008 OR 1009 OR 101 OR 1010 '\
               'OR 1011 OR 1012 OR 1013 OR 1014 OR 1015 OR 1016 OR 1017) '\
               'AND PUBYEAR IS 2018'
    sub_group = ['1', '10', '100', '1000', '1001', '1002', '1003', '1004',
                 '1005', '1006', '1007', '1008', '1009', '101', '1010', '1011',
                 '1012', '1013', '1014', '1015', '1016', '1017']
    assert_equal(received[0][0], expected)
    assert_equal(received[0][1], sub_group)


def test_create_queries_short():
    # Set variables
    group = list(range(1, 2000))
    template = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year+1}")
    joiner = " OR "
    maxlen = 1
    # Run test
    received = create_queries(group, joiner, template, maxlen)
    group_maxlen = max([len(q[1]) for q in received])
    # Compare
    assert_true(isinstance(received, list))
    assert_true(isinstance(received[0], tuple))
    assert_true(group_maxlen <= maxlen)
    expected = 'SOURCE-ID(1) AND PUBYEAR IS 2018'
    sub_group = ['1']
    assert_equal(received[0][0], expected)
    assert_equal(received[0][1], sub_group)    


def test_query_sources_by_year():
    # Test a journal and year
    res = query_pubs_by_sourceyear([22900], 2010, refresh=refresh)
    assert_equal(res["source_id"].unique(), ['22900'])
    assert_equal(res["year"].unique(), [2010])
    assert_true(isinstance(res["auids"][0], str))
    assert_true(len(res["auids"][0]) > 0)
    # Test a journal and year that are not in Scopus
    res = query_pubs_by_sourceyear([22900], 1969, refresh=refresh)
    assert_true(res.empty)
    # Test a large query (>5000 results)
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]
    res = query_pubs_by_sourceyear(source_ids, 1984, refresh=refresh)
    assert_true(3380 < res.dropna(subset=["auids"]).shape[0] < 3400)
    assert_true(res.columns.tolist(), ['source_id', 'year', 'afid', 'auids'])
    assert_true(isinstance(res["auids"][0], str))
    assert_true(len(res["auids"][0]) > 0)


def test_query_sources_by_year_stacked():
    # Test a journal and year
    res = query_pubs_by_sourceyear([22900], 2010, refresh=refresh, stacked=True)
    assert_equal(res["source_id"].unique(), ['22900'])
    assert_equal(res["year"].unique(), [2010])
    assert_true(isinstance(res["auids"][0], str))
    assert_true(len(res["auids"][0]) > 0)
    # Test a journal and year that are not in Scopus
    res = query_pubs_by_sourceyear([22900], 1969, refresh=refresh, stacked=True)
    assert_true(res.empty)
    # Test a large query (>5000 results)
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]
    res = query_pubs_by_sourceyear(source_ids, 1984, refresh=refresh, stacked=True)
    assert_true(3380 < res.dropna(subset=["auids"]).shape[0] < 3400)
    assert_true(res.columns.tolist(), ['source_id', 'year', 'afid', 'auids'])
    assert_true(isinstance(res["auids"][0], str))
    assert_true(len(res["auids"][0]) > 0)


def test_stacked_query():
    group = [18400156716, 19300157101, 19400157208, 19400157312, 19500157223,
             19600166213, 19700175482, 19700182353, 19800188009, 19900193211]
    template = Template(f"SOURCE-ID($fill) AND PUBYEAR IS {year+1}")
    res = stacked_query(group, template, joiner=" OR ", q_type="docs",
                        refresh=False, stacked=True, verbose=False)
    assert_equal(len(res), 797)
