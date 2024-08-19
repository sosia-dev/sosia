"""Tests for establishing.fields_sources module."""

import pandas as pd

from sosia.establishing.constants import FIELD_SOURCE_MAP, SOURCE_INFO
from sosia.establishing.fields_sources import get_field_source_information

FIELD_SOURCE_MAP.unlink(missing_ok=True)
FIELD_SOURCE_MAP.unlink(missing_ok=True)
get_field_source_information()


def test_fields_sources_list():
    df = pd.read_csv(FIELD_SOURCE_MAP)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["source_id", "asjc"]
    assert df.shape[0] > 200_000


def test_sources_names_list():
    df = pd.read_csv(SOURCE_INFO, index_col=0)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["type", "title"]
    assert df.shape[0] > 90_000
    assert df.loc[12005, "type"] == "jr"
    assert df.loc[12005, "title"] == "Journal of Traumatic Stress"
    assert df.loc[90641, "type"] == "cp"
    expected_title = "Proceedings of the Conference on Traffic and Transportation Studies, ICTTS"
    assert df.loc[90641, "title"] == expected_title
