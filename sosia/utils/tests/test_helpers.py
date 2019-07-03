#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for helpers module."""

import pandas as pd
from nose.tools import assert_equal, assert_true, raises

from sosia.classes import Scientist
from sosia.utils.helpers import add_source_names, flat_set_from_df,\
    margin_range, read_fields_sources_list


def test_add_source_names():
    s = Scientist(["55208373700"], 2017)
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    ids, names = zip(*expected)
    received = add_source_names(ids, s.source_names)
    assert_equal(received, expected)


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


def test_read_fields_sources_list():
    sources, names = read_fields_sources_list()
    assert_equal(str(type(sources)), "<class 'pandas.core.frame.DataFrame'>")
    assert_equal(str(type(names)), "<class 'pandas.core.frame.DataFrame'>")
