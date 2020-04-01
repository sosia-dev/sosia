# -*- coding: utf-8 -*-
"""Tests for processing.initializing module."""

import pandas as pd
from nose.tools import assert_equal

from sosia.classes import Scientist
from sosia.processing.initializing import add_source_names,\
    read_fields_sources_list


def test_add_source_names():
    s = Scientist(["55208373700"], 2017)
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    ids, names = zip(*expected)
    received = add_source_names(ids, s.source_names)
    assert_equal(received, expected)


def test_read_fields_sources_list():
    sources, names = read_fields_sources_list()
    assert_equal(str(type(sources)), "<class 'pandas.core.frame.DataFrame'>")
    assert_equal(str(type(names)), "<class 'pandas.core.frame.DataFrame'>")
