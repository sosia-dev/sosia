"""Tests for processing.filtering module."""

from pathlib import Path

from sosia.classes import Original
from sosia.establishing import make_database, connect_database
from sosia.processing.filtering import filter_pub_counts, same_affiliation

test_cache = Path.home() / ".cache" / "sosia" / "test.sqlite"


def test_filter_pub_counts():
    make_database(test_cache, drop=True)
    test_conn = connect_database(test_cache)
    group = [6701809842, 16319073600, 54984906100, 56148489300, 57131011400,
             57194816659, 35097480000, 56055501900, 20434039300, 6602070937]
    npapers = range(2, 60)
    g, pubs, older = filter_pub_counts(group, test_conn, 1993, 2005, npapers)
    assert sorted(g) == [6602070937, 6701809842, 35097480000]
    assert sorted(pubs) == [3, 15, 17]
    assert sorted(older) == [20434039300, 54984906100, 56148489300]


def test_same_affiliation():
    original = Original(55208373700, 2019, affiliations=[60105007],
                        db_path=test_cache)
    assert same_affiliation(original, 57209617104)
