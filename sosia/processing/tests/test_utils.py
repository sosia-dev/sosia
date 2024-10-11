"""Tests for processing.utils module."""

import pandas as pd
from pybliometrics.scopus import ScopusSearch

from sosia.processing import compute_overlap, expand_affiliation,\
    flat_set_from_df, margin_range


def test_compute_overlap():
    set1 = set("abc")
    set2 = set("cde")
    assert compute_overlap(set1, set2) == 1


def test_expand_affiliation(refresh_interval):
    pubs = ScopusSearch(f"AU-ID(6701809842)", refresh=refresh_interval).results
    res = pd.DataFrame(pubs)
    res = expand_affiliation(res)
    assert len(res) >= 180
    expect_columns = ['source_id', 'author_ids', 'afid']
    assert set(res.columns) == set(expect_columns)
    assert any(res['author_ids'].str.contains(";"))
    assert all(isinstance(x, (int, float)) for x in res['afid'].unique())


def test_flat_set_from_df():
    d = {'col1': [[1, 2], [10, 20]], "col2": ["a", "b"]}
    df = pd.DataFrame(d)
    expected = [1, 2, 10, 20]
    received = sorted(list(flat_set_from_df(df, "col1")))
    assert received == expected


def test_margin_range():
    assert margin_range(5, 1) == range(4, 7)
    assert margin_range(10, 0.09) == range(9, 12)
