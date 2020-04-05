# -*- coding: utf-8 -*-
"""Tests for establishing.database module."""

from os.path import expanduser, isfile

from nose.tools import assert_true

from sosia.establishing.database import make_database

test_cache = expanduser("~/.sosia/test.sqlite")


def test_make_database():
    make_database(test_cache)
    assert_true(isfile(test_cache))
