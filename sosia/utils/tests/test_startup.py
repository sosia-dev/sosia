#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for startup module."""

from os import remove

import pandas as pd
from nose.tools import assert_equal, assert_true

from sosia.utils.constants import FIELDS_SOURCES_LIST
from sosia.utils.startup import create_fields_sources_list


def test_create_fields_sources_list():
    try:
        remove(FIELDS_SOURCES_LIST)
    except FileNotFoundError:
        pass
    create_fields_sources_list()
    df = pd.read_csv(FIELDS_SOURCES_LIST)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ['asjc', 'source_id', 'type'])
    assert_true(df.shape[0] > 55130)
