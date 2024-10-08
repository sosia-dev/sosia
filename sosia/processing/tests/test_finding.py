"""Tests for processing.filtering module."""

from sosia.classes import Original
from sosia.processing.finding import same_affiliation


def test_same_affiliation(test_cache, refresh_interval):
    original = Original(55208373700, 2019, affiliations=[60105007],
                        db_path=test_cache, refresh=refresh_interval)
    assert same_affiliation(original, 57209617104)
