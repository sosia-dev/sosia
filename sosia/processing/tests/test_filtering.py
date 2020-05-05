# -*- coding: utf-8 -*-
"""Tests for processing.filtering module."""

from os.path import expanduser

from nose.tools import assert_equal

from sosia.establishing import connect_database
from sosia.processing.filtering import filter_pub_counts

test_cache = expanduser("~/.sosia/test.sqlite")
test_conn = connect_database(test_cache)


def test_filter_pub_counts():
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    npapers = range(2, 60)
    g, pubs, older = filter_pub_counts(group, test_conn, 1993, 2005, npapers)
    assert_equal(sorted(g), [6602070937, 6701809842, 35097480000])
    assert_equal(sorted(pubs), [3, 15, 17])
    assert_equal(sorted(older), [20434039300, 54984906100, 56148489300])


def test_filter_pub_counts_period():
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    npapers = range(2, 60)
    g, pubs, older = filter_pub_counts(group, test_conn, 1993, 2005, npapers, yfrom=2005)
    assert_equal(sorted(g), [6602070937])
    assert_equal(sorted(pubs), [2])
    assert_equal(sorted(older), [20434039300, 54984906100, 56148489300])
