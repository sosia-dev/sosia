#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for queries module."""

from nose.tools import assert_equal, assert_true

from sosia.processing import query_journal


def test_query_journal():
    # test a journal with more than 5k publications in one year
    res = query_journal("11000153773", [2006], refresh=False)
    assert_true(24100 < len(res.get("2006")) < 25000)
