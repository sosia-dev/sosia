"""Tests for establishing.database module."""

from pathlib import Path

from nose.tools import assert_true

from sosia.establishing.database import make_database

test_cache = Path.home()/".cache/sosia/test_database.sqlite"

def setup_module():
    test_cache.unlink(missing_ok=True)


def test_make_database():
    make_database(test_cache)
    assert_true(test_cache.is_file())


def teardown_module():
    test_cache.unlink(missing_ok=True)
