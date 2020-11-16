# -*- coding: utf-8 -*-
"""Tests for processing.utils module."""

import pandas as pd
from nose.tools import assert_equal, assert_true
from pybliometrics.scopus import ScopusSearch

from sosia.processing import expand_affiliation, flat_set_from_df, margin_range

refresh = 30


def test_expand_affiliation():
    pubs = ScopusSearch(f"AU-ID(6701809842)", refresh=refresh).results
    res = pd.DataFrame(pubs)
    res = expand_affiliation(res)
    assert_true(len(res) >= 180)
    expect_columns = ['source_id', 'author_ids', 'afid']
    assert_equal(set(res.columns), set(expect_columns))
    assert_true(any(res['author_ids'].str.contains(";")))
    assert_true(all(isinstance(x, (int, float)) for x in res['afid'].unique()))


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
