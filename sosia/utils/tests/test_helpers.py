#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for helpers module."""

import pandas as pd
from nose.tools import assert_equal, assert_true, raises

from sosia.classes import Scientist
from sosia.utils.helpers import add_source_names, margin_range, raise_non_empty


def test_add_source_names():
    s = Scientist(["55208373700"], 2017)
    expected = {(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")}
    ids, names = zip(*expected)
    received = add_source_names(ids, s.source_names)
    assert_equal(received, expected)


def test_margin_range():
    assert_equal(margin_range(5, 1), range(4, 7))
    assert_equal(margin_range(10, 0.09), range(9, 12))


def test_raise_non_empty():
    raise_non_empty(list("abcd"), list)
    raise_non_empty(set("abcd"), set)
    raise_non_empty(set("abcd"), (set, list))


@raises(Exception)
def test_raise_non_empty_set():
    raise_non_empty(set(), set)


@raises(Exception)
def test_raise_non_empty_list():
    raise_non_empty([], list)
