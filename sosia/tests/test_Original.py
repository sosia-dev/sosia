#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true
import warnings
import pandas as pd

import sosia

refresh = False
warnings.filterwarnings("ignore")
scientist1 = sosia.Original(55208373700, 2017, cits_margin=200, refresh=refresh)
scientist2 = sosia.Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                            coauth_margin=1, period=3, refresh=refresh)
fields = "ID name first_year num_coauthors num_publications num_citations "\
         "country language reference_sim abstract_sim"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(
        ID='53164702100',
        name='Sapprasert, Koson',
        first_year=2011,
        num_coauthors=7,
        num_publications=6,
        num_citations=190,
        country='Norway',
        language='eng',
        reference_sim=0.0212,
        abstract_sim=0.1702),
    Match(
        ID='55071051800',
        name='Doldor, Elena',
        first_year=2013,
        num_coauthors=6,
        num_publications=8,
        num_citations=19,
        country='United Kingdom',
        language='eng',
        reference_sim=0.0,
        abstract_sim=0.1021),
    Match(
        ID='55317901900',
        name='Siepel, Josh',
        first_year=2013,
        num_coauthors=8,
        num_publications=7,
        num_citations=52,
        country='United Kingdom',
        language='eng',
        reference_sim=0.0079,
        abstract_sim=0.1274),
    Match(
        ID='55804519400',
        name='González, Domingo',
        first_year=2013,
        num_coauthors=6,
        num_publications=7,
        num_citations=1,
        country='Peru',
        language='eng; spa',
        reference_sim=0.0,
        abstract_sim=0.1183)]


def test_search_sources():
    # scientist 1
    scientist1.define_search_sources()
    search_sources = scientist1.search_sources
    assert_equal(len(search_sources), 65)
    assert_true((14726, "Technovation") in search_sources)
    assert_true((15143, "Regional Studies") in search_sources)
    for j in scientist1.sources:
        assert_true(j in search_sources)
    # scientist2
    scientist2.define_search_sources()
    search_sources = scientist2.search_sources
    assert_equal(len(search_sources), 65)
    assert_true((14726, "Technovation") in search_sources)
    assert_true((15143, "Regional Studies") in search_sources)
    for j in scientist2.sources:
        assert_true(j in search_sources)


def test_search_sources_change():
    backup = scientist1.search_sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    scientist1.search_sources, _ = zip(*expected)
    assert_equal(scientist1.search_sources, expected)
    scientist1.search_sources = backup


def test_search_group():
    scientist1.define_search_group(refresh=refresh)
    group = scientist1.search_group
    assert_true(365 <= len(group) <= 375)
    assert_true(isinstance(group, list))


def test_search_group_period():
    scientist2.define_search_group(ignore_first_id=True, refresh=refresh)
    group = scientist2.search_group
    assert_true(4355 <= len(group) <= 4365)
    assert_true(isinstance(group, list))


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True, refresh=refresh)
    group = scientist1.search_group
    assert_true(620 <= len(group) <= 630)
    assert_true(isinstance(group, list))


def test_search_group_stacked_period():
    scientist2.define_search_group(stacked=True, ignore_first_id=True, refresh=refresh)
    group = scientist2.search_group
    assert_true(4960 <= len(group) <= 5000)
    assert_true(isinstance(group, list))


def test_find_matches():
    recieved = sorted(scientist1.find_matches(refresh=refresh))
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = ["ID", "name", "first_year", "num_coauthors", "num_publications",
            "country", "reference_sim"]
    df_r = pd.DataFrame(recieved)
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim, float))
        assert_true(0 <= e.abstract_sim <= 1)


def test_find_matches_stacked():
    recieved = scientist1.find_matches(stacked=True, refresh=refresh,
                                       verbose=True)
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = ["ID", "name", "first_year", "num_coauthors", "num_publications",
            "country", "reference_sim"]
    df_r = pd.DataFrame(sorted(recieved))
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim, float))
        assert_true(0 <= e.abstract_sim <= 1)


def test_find_matches_stacked():
    recieved = scientist2.find_matches(stacked=True, information=False,
                                       refresh=refresh, verbose=True)
    expected = [36998825200, 56049973600, 56896085200, 57188695848, 57188709931]
    assert_equal(sorted(recieved), expected)


def test_find_matches_noinfo():
    recieved = scientist1.find_matches(information=False, refresh=refresh)
    assert_equal(sorted(recieved), [int(m.ID) for m in MATCHES])
