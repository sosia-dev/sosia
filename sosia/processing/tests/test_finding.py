"""Tests for processing.filtering module."""

from pathlib import Path

from sosia.classes import Original
from sosia.processing.finding import same_affiliation

test_cache = Path.home() / ".cache" / "sosia" / "test.sqlite"
refresh = 30


def test_same_affiliation():
    original = Original(55208373700, 2019, affiliations=[60105007],
                        db_path=test_cache)
    assert same_affiliation(original, 57209617104)
