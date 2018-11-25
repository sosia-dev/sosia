#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for utils module."""

import os

import pandas as pd
from nose.tools import assert_equal, assert_true, raises
from numpy import array
from scipy.sparse import csr_matrix

from sosia.utils import (FIELDS_SOURCES_LIST, clean_abstract, compute_cosine,
    create_fields_sources_list, margin_range, raise_non_empty)


def test_clean_abstract():
    expected = "Lorem ipsum."
    assert_equal(clean_abstract("Lorem ipsum. © dolor sit."), expected)
    assert_equal(clean_abstract("© dolor sit. Lorem ipsum."), expected)
    assert_equal(clean_abstract(expected), expected)


def test_compute_cosine():
    expected = [0.6875, 1.0625]
    received = compute_cosine(csr_matrix(array([[0.5, 0.75], [1, 0.25]])))
    assert_equal(list(received), expected)


def test_create_fields_sources_list():
    try:
        os.remove(FIELDS_SOURCES_LIST)
    except FileNotFoundError:
        pass
    create_fields_sources_list()
    df = pd.read_csv(FIELDS_SOURCES_LIST)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ['asjc', 'source_id', 'type'])
    assert_true(df.shape[0] > 55130)


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

