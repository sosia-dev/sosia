"""Tests for processing.initializing module."""

from pandas import DataFrame

from sosia.classes import Scientist
from sosia.processing.initializing import add_source_names, \
    read_fields_sources_list


def test_add_source_names(test_cache):
    s = Scientist([55208373700], 2017, db_path=test_cache)
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    ids, names = zip(*expected)
    received = add_source_names(ids, s.source_names)
    assert received == expected


def test_read_fields_sources_list():
    sources, names = read_fields_sources_list()
    assert isinstance(sources, DataFrame)
    assert isinstance(sources, DataFrame)
