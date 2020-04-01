# -*- coding: utf-8 -*-
"""Tests for establishing.database module."""

from os.path import expanduser, isfile

from nose.tools import assert_true

from sosia.establishing.database import create_cache


def test_create_cache():
    cache_file = expanduser("~/.sosia/") + "cache_sqlite.sqlite"
    cache_file_test = expanduser("~/.sosia/") + "cache_sqlite_test.sqlite"
    create_cache()
    assert_true(isfile(cache_file))
    create_cache(file=cache_file_test)
    assert_true(isfile(cache_file_test))
