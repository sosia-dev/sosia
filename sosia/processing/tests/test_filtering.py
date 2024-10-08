"""Tests for processing.filtering module."""

from pathlib import Path

import pandas as pd

from sosia.classes import Original
from sosia.establishing import make_database, connect_database
from sosia.processing.filtering import get_author_yearly_data, same_affiliation

test_cache = Path.home() / ".cache" / "sosia" / "test.sqlite"
refresh = 30


def test_get_author_yearly_data():
    make_database(test_cache, drop=True)
    test_conn = connect_database(test_cache)
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    data = get_author_yearly_data(group, test_conn)
    assert isinstance(data, pd.DataFrame)
    expected_cols = ['auth_id', 'year', 'first_year', 'n_pubs', 'n_coauth']
    assert list(data.columns) == expected_cols
    assert data.shape[0] > 200
    assert data["auth_id"].nunique() == len(group)


def test_same_affiliation():
    original = Original(55208373700, 2019, affiliations=[60105007],
                        db_path=test_cache)
    assert same_affiliation(original, 57209617104)
