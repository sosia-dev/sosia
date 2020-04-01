#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for processing.utils module."""

from os.path import expanduser

from nose.tools import assert_equal, assert_true, assert_false
from pybliometrics.scopus import ScopusSearch
import pandas as pd

from sosia.establishing import config
from sosia.processing import expand_affiliation, flat_set_from_df, margin_range

refresh = 30

test_cache = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
config["Cache"]["File path"] = test_cache


def test_expand_affiliation():
    auth_id = 6701809842
    pubs = ScopusSearch("AU-ID({})".format(auth_id), refresh=refresh).results
    res = pd.DataFrame(pubs)
    res = expand_affiliation(res)
    assert_true(len(res) >= 180)
    expect_columns = ['source_id', 'author_ids', 'afid']
    assert_equal(set(res.columns.tolist()), set(expect_columns))
    assert_true(any(res.author_ids.str.contains(";")))
    assert_false(any(res.afid.str.contains(";")))


def test_flat_set_from_df():
    d = {'col1': [[1, 2], [10, 20]], "col2": ["a", "b"]}
    df = pd.DataFrame(d)
    expected = [1, 2, 10, 20]
    received = sorted(list(flat_set_from_df(df, "col1")))
    assert_equal(received, expected)


def test_flat_set_from_df_condition():
    d = {'col1': [[1, 2], [10, 20]], "col2": ["a", "b"]}
    df = pd.DataFrame(d)
    condition = df["col2"] == "b"
    expected = [10, 20]
    received = sorted(list(flat_set_from_df(df, "col1", condition)))
    assert_equal(received, expected)


def test_margin_range():
    assert_equal(margin_range(5, 1), range(4, 7))
    assert_equal(margin_range(10, 0.09), range(9, 12))
