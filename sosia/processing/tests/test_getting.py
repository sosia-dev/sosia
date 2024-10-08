"""Tests for processing.getting module."""

from pandas import DataFrame

from sosia.processing import get_author_data
from sosia.processing.getting import get_author_info


def test_get_author_data(test_conn):
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    data = get_author_data(group, test_conn)
    assert isinstance(data, DataFrame)
    expected_cols = ['auth_id', 'year', 'first_year', 'n_pubs', 'n_coauth']
    assert list(data.columns) == expected_cols
    assert data.shape[0] > 200
    assert data["auth_id"].nunique() == len(group)


def test_query_authors(test_conn, refresh_interval):
    auth_list = [6701809842, 55208373700]
    auth_data = get_author_info(auth_list, test_conn, refresh=refresh_interval)
    assert isinstance(auth_data,  DataFrame)
    expected_cols = ["auth_id", "eid", "surname", "initials", "givenname",
                     "affiliation", "documents", "affiliation_id", "city",
                     "country", "areas"]
    assert auth_data.columns.tolist() == expected_cols
    assert auth_data["auth_id"].tolist() == auth_list
    assert auth_data["surname"].tolist() == ["Harhoff", "Baruffaldi"]