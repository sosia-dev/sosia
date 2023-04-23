"""Tests for processing.getting module."""

from pathlib import Path

from nose.tools import assert_equal, assert_true
from pandas import DataFrame

from sosia.establishing import connect_database, make_database
from sosia.processing.getting import get_authors

test_cache = Path.home()/".cache/sosia/test.sqlite"
refresh = 30


def test_query_authors():
    auth_list = [6701809842, 55208373700]
    test_conn = connect_database(test_cache)
    auth_data = get_authors(auth_list, test_conn, refresh=refresh)
    assert_true(isinstance(auth_data,  DataFrame))
    expected_cols = ["auth_id", "eid", "surname", "initials", "givenname",
                     "affiliation", "documents", "affiliation_id", "city",
                     "country", "areas"]
    assert_equal(auth_data.columns.tolist(), expected_cols)
    assert_equal(auth_data["auth_id"].tolist(), auth_list)
    assert_equal(auth_data["surname"].tolist(), ["Harhoff", "Baruffaldi"])
