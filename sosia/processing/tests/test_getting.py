"""Tests for processing.getting module."""

from pathlib import Path

from pandas import DataFrame

from sosia.establishing import connect_database, make_database
from sosia.processing import get_author_data
from sosia.processing.getting import get_author_info

test_cache = Path.home()/".cache/sosia/test.sqlite"
refresh = 30


def test_get_author_data():
    make_database(test_cache, drop=True)
    test_conn = connect_database(test_cache)
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    data = get_author_data(group, test_conn)
    assert isinstance(data, DataFrame)
    expected_cols = ['auth_id', 'year', 'first_year', 'n_pubs', 'n_coauth']
    assert list(data.columns) == expected_cols
    assert data.shape[0] > 200
    assert data["auth_id"].nunique() == len(group)


def test_query_authors():
    auth_list = [6701809842, 55208373700]
    test_conn = connect_database(test_cache)
    auth_data = get_author_info(auth_list, test_conn, refresh=refresh)
    assert isinstance(auth_data,  DataFrame)
    expected_cols = ["auth_id", "eid", "surname", "initials", "givenname",
                     "affiliation", "documents", "affiliation_id", "city",
                     "country", "areas"]
    assert auth_data.columns.tolist() == expected_cols
    assert auth_data["auth_id"].tolist() == auth_list
    assert auth_data["surname"].tolist() == ["Harhoff", "Baruffaldi"]