"""Tests for processing.initializing module."""

from pathlib import Path

import pandas as pd

from sosia.classes import Scientist
from sosia.establishing import make_database
from sosia.processing.initializing import add_source_names,\
    read_fields_sources_list

test_cache = Path.home()/".cache/sosia/test.sqlite"

def test_add_source_names():
    s = Scientist([55208373700], 2017, sql_fname=test_cache)
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    ids, names = zip(*expected)
    received = add_source_names(ids, s.source_names)
    assert received == expected


def test_read_fields_sources_list():
    sources, names = read_fields_sources_list()
    assert str(type(sources)) == "<class 'pandas.core.frame.DataFrame'>"
    assert str(type(names)) == "<class 'pandas.core.frame.DataFrame'>"
