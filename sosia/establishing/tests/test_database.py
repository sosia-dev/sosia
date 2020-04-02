# -*- coding: utf-8 -*-
"""Tests for establishing.database module."""

from os.path import expanduser, isfile

from nose.tools import assert_true

from sosia.establishing.database import create_cache

test_cache = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"


def test_create_cache():
    create_cache(test_cache)
    assert_true(isfile(test_cache))
