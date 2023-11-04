"""Tests for establishing.fields_sources module."""

import pandas as pd
from nose.tools import assert_equal, assert_true

from sosia.establishing.constants import FIELD_SOURCE_MAP, SOURCE_INFO
from sosia.establishing.fields_sources import get_field_source_information

FIELD_SOURCE_MAP.unlink(missing_ok=True)
FIELD_SOURCE_MAP.unlink(missing_ok=True)
get_field_source_information()


def test_fields_sources_list():
    df = pd.read_csv(FIELD_SOURCE_MAP)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ["source_id", "asjc"])
    assert_true(df.shape[0] > 200_000)


def test_sources_names_list():
    df = pd.read_csv(SOURCE_INFO, index_col=0)
    assert_true(isinstance(df, pd.DataFrame))
    assert_equal(list(df.columns), ["type", "title"])
    assert_true(df.shape[0] > 90_000)
    assert_equal(df.loc[12005, "type"], "jr")
    assert_equal(df.loc[12005, "title"], "Journal of Traumatic Stress")
    assert_equal(df.loc[12200, "type"], "cp")
    assert_equal(df.loc[12200, "title"], "Proceedings of the Summer Computer Simulation Conference")
