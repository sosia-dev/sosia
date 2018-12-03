#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for helpers module."""

import pandas as pd
from nose.tools import assert_equal, assert_true, raises

from sosia.utils.helpers import margin_range, raise_non_empty


def test_margin_range():
    assert_equal(margin_range(5, 1), range(4, 7))
    assert_equal(margin_range(10, 0.09), range(9, 12))


def test_raise_non_empty():
    raise_non_empty(list('abcd'), list)
    raise_non_empty(set('abcd'), set)


@raises(Exception)
def test_raise_non_empty_set():
    raise_non_empty(set(), set)


@raises(Exception)
def test_raise_non_empty_list():
    raise_non_empty([], list)
