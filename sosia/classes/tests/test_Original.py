# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

import warnings
from collections import namedtuple
from os.path import expanduser

import pandas as pd
from nose.tools import assert_equal, assert_true

from sosia.classes import Original

warnings.filterwarnings("ignore")

test_cache = expanduser("~/.sosia/test.sqlite")
refresh = False
test_params = {"refresh": refresh, "sql_fname": test_cache}

# Test objects
# Normal values
scientist1 = Original(55208373700, 2017, cits_margin=200, first_year_margin=1,
                      pub_margin=0.1, coauth_margin=0.1, **test_params)
# Using period and name search mode
scientist2 = Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                      coauth_margin=1, first_year_margin=1, period=3,
                      first_year_search="name", **test_params)
# Using affiliations
affs = ["60010348", "60022109", "60017317"]
scientist3 = Original(55208373700, 2017, cits_margin=200, first_year_margin=1,
                      pub_margin=0.1, affiliations=affs, **test_params)
# Using name search mode and affiliations
affs = ["60002612", "60032111", "60000765"]
scientist4 = Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                      coauth_margin=1, first_year_margin=1, period=3,
                      first_year_search="name", affiliations=affs,
                      **test_params)

# Expected matches
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
        reference_sim=0.0214,
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
        num_coauthors=7,
        num_publications=8,
        num_citations=1,
        country='Peru',
        language='eng; spa',
        reference_sim=0.0,
        abstract_sim=0.1183)]


def test_search_sources():
    scientists_list = [scientist1, scientist2, scientist3, scientist4]
    for s in scientists_list:
        s.define_search_sources()
        search_sources = s.search_sources
        assert_equal(len(search_sources), 65)
        assert_true((14726, "Technovation") in search_sources)
        assert_true((15143, "Regional Studies") in search_sources)


def test_search_sources_change():
    backup = scientist1.search_sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    scientist1.search_sources, _ = zip(*expected)
    assert_equal(scientist1.search_sources, expected)
    scientist1.search_sources = backup


def test_search_group():
    scientist1.define_search_group(refresh=refresh)
    recieved = scientist1.search_group
    assert_true(isinstance(recieved, list))
    assert_true(590 <= len(recieved) <= 620)


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist1.search_group
    assert_true(isinstance(recieved, list))
    assert_true(590 <= len(recieved) <= 620)


def test_search_group_ignore():
    scientist2.define_search_group(refresh=refresh)
    recieved = scientist2.search_group
    assert_true(isinstance(recieved, list))
    assert_true(4800 <= len(recieved) <= 4900)


def test_search_group_ignore_stacked():
    scientist2.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist2.search_group
    assert_true(isinstance(recieved, list))
    assert_true(4800 <= len(recieved) <= 4900)


def test_search_group_affiliations_stacked():
    scientist3.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist3.search_group
    assert_true(isinstance(recieved, list))
    assert_true(15 <= len(recieved) <= 22)


def test_search_group_period_affiliations_ignore_stacked():
    scientist4.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist4.search_group
    assert_true(isinstance(recieved, list))
    assert_true(50 <= len(recieved) <= 60)


def test_find_matches():
    scientist1.find_matches(refresh=refresh)
    expected = [m.ID for m in MATCHES]
    assert_equal(scientist1.matches, expected)


def test_find_matches_stacked():
    scientist1.find_matches(stacked=True, refresh=refresh)
    expected = [m.ID for m in MATCHES]
    assert_equal(scientist1.matches, expected)


def test_find_matches_stacked_affiliations():
    scientist3.find_matches(stacked=True, refresh=refresh)
    expected = [m.ID for m in MATCHES if m.ID != '55804519400']
    assert_equal(scientist3.matches, expected)


def test_find_matches_stacked_period_affiliations():
    scientist4.find_matches(stacked=True, refresh=refresh)
    expected_ids = ['57188695848', '57188709931']
    assert_equal(scientist4.matches, expected_ids)


def test_inform_matches():
    scientist1.inform_matches(refresh=refresh)
    recieved = scientist1.matches
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = ["ID", "name", "first_year", "num_coauthors", "num_publications",
            "country", "reference_sim"]
    df_r = pd.DataFrame(recieved)
    df_r["reference_sim"] = df_r["reference_sim"].round(3)
    df_m = pd.DataFrame(MATCHES)
    df_m["reference_sim"] = df_m["reference_sim"].round(3)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim, float))
        assert_true(0 <= e.abstract_sim <= 1)
