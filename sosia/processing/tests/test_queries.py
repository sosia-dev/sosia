#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for queries module."""

from nose.tools import assert_equal, assert_true
from string import Template

from sosia.processing import query, query_journal, query_year, stacked_query


def test_query():
    auth_id = 53164702100
    # test sizes of results sets
    q = "AU-ID({}) AND PUBYEAR BEF {}".format(auth_id, 2017)
    size = query("docs", q, size_only=True)
    assert_equal(size, 5)
    q = "AU-ID({})".format(auth_id)
    size = query("author", q, size_only=True)
    assert_equal(size, 1)


def test_stacked_query():
    # test a query with one journal-year above 5000
    group = [18400156716, 19300157101, 19400157208, 19400157312, 19500157223,
             19600166213, 19700175482, 19700182353, 19800188009, 19900193211,
             20100195028, 21100208103, 21100225839, 21100228010, 21100244622,
             21100246535, 21100246537, 21100285035, 21100313905, 21100329904,
             21100370441, 21100370876, 21100416121, 21100775937, 21100871308,
             25674]
    template = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(1998))
    joiner = " OR "
    refresh = False
    q_type = "docs"
    res = []
    stacked_query(group, res, template, joiner, q_type, refresh)
    assert_equal(len(res), 6441)


def test_query_journal():
    # test a journal with more than 5k publications in one year
    res = query_journal("11000153773", [2006], refresh=False)
    assert_true(24100 < len(res.get("2006")) < 25000)


def test_query_year():
    # test a journal and year
    res = query_year(2010, [22900], refresh=False, verbose=False)
    assert_equal(res.source_id.tolist(), ['22900'])
    assert_equal(res.year.tolist(), ['2010'])
    assert_true(isinstance(res.auids[0], list))
    assert_true(len(res.auids[0]) > 0)
    # test a journal and year that are not in scopus
    res = query_year(1969, [22900], refresh=False, verbose=False)
    assert_true(res.empty)
    # test a large query (>5000 scopus results)
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]
    res = query_year(1984, source_ids, refresh=False, verbose=True)
    assert_true(len(res[~res.auids.isnull()]) == 17)
    assert_true(isinstance(res.auids[0], list))
    assert_true(len(res.auids[0]) > 0)
