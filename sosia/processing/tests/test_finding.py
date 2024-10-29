"""Tests for processing.filtering module."""

from sosia.processing.finding import same_affiliation


def test_same_affiliation(test_cache, refresh_interval):
    assert same_affiliation([60105007], 57209617104, 2019,
                            db_path=test_cache, refresh=refresh_interval)
