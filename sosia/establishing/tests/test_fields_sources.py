# -*- coding: utf-8 -*-
"""Tests for establishing.fields_sources module."""

from os import remove

import pandas as pd
from nose.tools import assert_equal, assert_true

from sosia.establishing.constants import FIELDS_SOURCES_LIST, SOURCES_NAMES_LIST
from sosia.establishing.fields_sources import create_fields_sources_list

try:
    remove(FIELDS_SOURCES_LIST)
except FileNotFoundError:
    pass
try:
    remove(SOURCES_NAMES_LIST)
except FileNotFoundError:
    pass
create_fields_sources_list()


def test_fields_sources_list():
    df = pd.read_csv(FIELDS_SOURCES_LIST)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ["asjc", "source_id", "type"])
    assert_true(df.shape[0] > 55130)


def test_sources_names_list():
    df = pd.read_csv(SOURCES_NAMES_LIST, index_col=0)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ["title"])
    assert_true(df.shape[0] > 74000)
    assert_equal(df.loc[12005].title, "Journal of Traumatic Stress")
    assert_equal(df.loc[21100875102].title, "Diagnostyka")
