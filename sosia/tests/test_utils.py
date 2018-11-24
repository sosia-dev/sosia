#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for utils module."""

import os

import pandas as pd
from nose.tools import assert_equal, assert_true, raises

from sosia.utils import (FIELDS_SOURCES_LIST, create_fields_sources_list,
    raise_non_empty)


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


def test_raise_non_empty():
    raise_non_empty(list('abcd'), list)
    raise_non_empty(set('abcd'), set)


@raises(Exception)
def test_raise_non_empty_set():
    raise_non_empty(set(), set)


@raises(Exception)
def test_raise_non_empty_list():
    raise_non_empty([], list)

