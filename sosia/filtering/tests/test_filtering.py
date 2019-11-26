#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for filtering module."""

from nose.tools import assert_equal, assert_true
from string import Template
import pandas as pd

from sosia.filtering import filter_pub_counts


def test_filter_pub_counts():
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    npapers = range(2, 60)
    g, pubs, older = filter_pub_counts(group, 1993, 2005, npapers)
    assert_equal(sorted(g), [6602070937, 6701809842, 35097480000])
    assert_equal(sorted(pubs), [3, 15, 18])
    assert_equal(sorted(older), [20434039300, 54984906100, 56148489300])


def test_filter_pub_counts_period():
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    npapers = range(2, 60)
    g, pubs, older = filter_pub_counts(group, 1993, 2005, npapers, yfrom=2005)
    assert_equal(sorted(g), [6602070937])
    assert_equal(sorted(pubs), [2])
    assert_equal(sorted(older), [20434039300, 54984906100, 56148489300])
