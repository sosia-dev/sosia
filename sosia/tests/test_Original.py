#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true
import warnings
import pandas as pd

import sosia

warnings.filterwarnings("ignore")
scientist1 = sosia.Original(55208373700, 2017)

fields = (
    "ID name first_year num_coauthors num_publications country "
    "language reference_sim abstract_sim"
)
Match = namedtuple("Match", fields)
MATCHES = [
    Match(
        ID="53164702100",
        name="Sapprasert, Koson",
        first_year=2011,
        num_coauthors=7,
        num_publications=6,
        country="Norway",
        language="eng",
        reference_sim=0.0212,
        abstract_sim=0.1695,
    ),
    Match(
        ID="54411022900",
        name="Martinelli, Arianna",
        first_year=2011,
        num_coauthors=7,
        num_publications=6,
        country="Italy",
        language="eng",
        reference_sim=0.0041,
        abstract_sim=0.1966,
    ),
    Match(
        ID="55317901900",
        name="Siepel, Josh",
        first_year=2013,
        num_coauthors=8,
        num_publications=7,
        country="United Kingdom",
        language="eng",
        reference_sim=0.0079,
        abstract_sim=0.1275,
    ),
]


def test_search_sources():
    scientist1.define_search_sources()
    search_sources = scientist1.search_sources
    assert_equal(len(search_sources), 63)
    assert_true((14726, "Technovation") in search_sources)
    assert_true((22009, "Corporate Governance (Oxford)") in search_sources)
    for j in scientist1.sources:
        assert_true(j in search_sources)


def test_search_sources_change():
    backup = scientist1.search_sources
    expected = {
        (14351, "Brain Research Reviews"),
        (18632, "Progress in Brain Research"),
    }
    scientist1.search_sources, _ = zip(*expected)
    assert_equal(scientist1.search_sources, expected)
    scientist1.search_sources = backup


def test_search_group():
    scientist1.define_search_group()
    group = scientist1.search_group
    assert_equal(len(group), 374)
    assert_true(isinstance(group, list))


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True)
    group = scientist1.search_group
    assert_equal(len(group), 631)
    assert_true(isinstance(group, list))


def test_find_matches():
    recieved = sorted(scientist1.find_matches())
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = [
        "ID",
        "name",
        "first_year",
        "num_coauthors",
        "num_publications",
        "country",
        "reference_sim",
    ]
    df_r = pd.DataFrame(recieved)
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim, float))
        assert_true(0 <= e.abstract_sim <= 1)


def test_find_matches_stacked():
    recieved = sorted(scientist1.find_matches(stacked=True))
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = [
        "ID",
        "name",
        "first_year",
        "num_coauthors",
        "num_publications",
        "country",
        "reference_sim",
    ]
    df_r = pd.DataFrame(recieved)
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim, float))
        assert_true(0 <= e.abstract_sim <= 1)


def test_find_matches_noinfo():
    recieved = sorted(scientist1.find_matches(information=False))
    assert_equal(recieved, [m.ID for m in MATCHES])
