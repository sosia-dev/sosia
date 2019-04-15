#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for queries module."""

from nose.tools import assert_equal, assert_true

from sosia.processing import query_journal, query_year


def test_query_journal():
    # test a journal with more than 5k publications in one year
    res = query_journal("11000153773", [2006], refresh=False)
    assert_true(24100 < len(res.get("2006")) < 25000)
    

def test_query_year():
    # test a journal and year
    res = query_year(2010,[22900],refresh=False,verbose=False)
    assert_equal(res.source_id.tolist(), ['22900'])
    assert_equal(res.year.tolist(), ['2010'])
    assert_true(isinstance(res.auids[0], list))
    assert_true(len(res.auids[0])>0)
    # test a journal and year that are not in scopus
    res = query_year(1969,[22900],refresh=False,verbose=False)
    assert_true(res.empty)
    # test a large query (>5000 scopus results)
    source_ids = [13703, 13847, 13945, 14131, 14150, 14156, 14204, 14207,
                  14209, 14346, 14438, 14536, 14539, 15034, 15448, 15510, 15754]  
    res = query_year(1984,source_ids,refresh=False,verbose=True)
    assert_true(len(res[~res.auids.isnull()])==17)
    assert_true(isinstance(res.auids[0], list))
    assert_true(len(res.auids[0])>0)
