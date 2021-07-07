# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

import warnings
from collections import namedtuple
import numpy as np
from os.path import expanduser
from types import GeneratorType

import mock
import pandas as pd
from pandas.testing import assert_frame_equal
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
# To test disambiguation
scientist5 = Original(55208373700, 2017, cits_margin=200, first_year_margin=2,
                      pub_margin=0.2, coauth_margin=0.2, **test_params)
scientist5.matches = ['35324709800', '36195966900', '53164702100',
                      '55022752500', '55071051800', '55212317400',
                      '55308662800', '55317901900', '55515260500',
                      '55567912500', '55694169400', '55804519400',
                      '55810688700', '55824607400', '55930211600',
                      '55963523600', '55991142100', '56132478200',
                      '56282273300', '56856438600', '57189495106']


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

# expected disambiuguation results for matches of scientists5
Match_disambiguated = namedtuple("Match_disambiguated", "ID all_IDs")
MATCHES_DISAMBIGUATED = [
    Match_disambiguated(ID=['35324709800'], all_IDs=['35324709800']),
    Match_disambiguated(ID=['36195966900'], all_IDs=['36195966900']),
    Match_disambiguated(ID=['53164702100'], all_IDs=['53164702100']),
    Match_disambiguated(ID=['55022752500'], all_IDs=['55022752500']),
    Match_disambiguated(ID=['55071051800'], all_IDs=['55071051800']),
    Match_disambiguated(ID=['55212317400'], all_IDs=['55212317400']),
    Match_disambiguated(ID=['55308662800'], all_IDs=['55308662800']),
    Match_disambiguated(ID=['55317901900'], all_IDs=['55317901900']),
    Match_disambiguated(ID=['55567912500'], all_IDs=['55567912500']),
    Match_disambiguated(ID=['55694169400'], all_IDs=['55694169400']),
    Match_disambiguated(ID=['55810688700'], all_IDs=['55810688700']),
    Match_disambiguated(ID=['55824607400'], all_IDs=['55824607400']),
    Match_disambiguated(ID=['55930211600'], all_IDs=['55930211600']),
    Match_disambiguated(ID=['55963523600'], all_IDs=['55963523600']),
    Match_disambiguated(ID=['55991142100'], all_IDs=['55991142100']),
    Match_disambiguated(ID=['56856438600'],
                        all_IDs=['56856438600', '57220585789', '57211907197',
                                 '57196653055']),
    Match_disambiguated(ID=['57189495106'],
                        all_IDs=['57189495106', '56223966400'])]


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


def test_matches_disambiguator():
    # within same subjects
    # create only a generator of dismbiguators
    scientist5.matches_disambiguator()
    assert_true(isinstance(scientist5.m_disambiguators, GeneratorType))


def test_disambiguate_matches():
    # the actions are chosen randomly (not based on an actual disambiguation)
    actions = ["", "k"]
    with mock.patch('builtins.input', side_effect=actions):
        scientist5.disambiguate_matches()
    assert_equal(len(scientist5.matches_disambiguated), 15)


def test_matches_disambiguator_compile_info():
    # compile information
    scientist1.matches_disambiguator(compile_info=True)
    _dic = {"ID": ['53164702100', '55071051800', '55317901900', '55804519400'],
            "uniqueness": [1.0, 1.0, 1.0, np.nan],
            "homonyms_num": [0, 0, 0, 203]}
    expect_uniqueness = pd.DataFrame(_dic)
    assert_frame_equal(scientist1.matches_uniqueness, expect_uniqueness)
    assert_true(scientist1.matches_homonyms.empty)

    # scientist5 (to test more features)
    scientist5.matches_disambiguator(compile_info=True)
    assert_true(isinstance(scientist5.matches_homonyms, pd.DataFrame))
    cols = ['ID', 'ID_homonym', 'surname', 'initials', 'givenname',
            'affiliation', 'documents', 'affiliation_id', 'city',
            'country', 'areas', 'first_year', 'num_publications',
            'num_citations', 'num_coauthors', 'reference_sim',
            'abstract_sim', 'cross_citations']
    assert_equal(scientist5.matches_homonyms.columns.tolist(), cols)
    expected = ['55515260500', '55515260500', '55515260500', '55515260500',
                '55515260500', '55515260500']
    assert_equal(scientist5.matches_homonyms.ID.tolist(), expected)
    expected = ['56424167900', '56139234900', '57191843211', '55856793100',
                '51565022800', '57209260852']
    assert_equal(scientist5.matches_homonyms.ID_homonym.tolist(), expected)


def test_matches_disambiguator_limit():
    # increase limit (and reduce fields)
    fields = ["first_year", "num_publications", "reference_sim"]
    scientist5.matches_disambiguator(homonym_fields=fields, compile_info=True,
                                     limit=16, verbose=True)
    expected = ['35324709800', '36195966900', '53164702100', '55022752500',
                '55071051800', '55212317400', '55308662800', '55317901900',
                '55515260500', '55567912500', '55694169400', '55804519400',
                '55810688700', '55824607400', '55930211600', '55963523600',
                '55991142100', '56132478200', '56282273300', '56856438600',
                '57189495106']
    assert_equal(scientist5.matches_uniqueness.ID.tolist(), expected)
    cols = ['ID', 'ID_homonym', 'surname', 'initials', 'givenname',
            'affiliation', 'documents', 'affiliation_id', 'city',
            'country', 'areas', 'first_year', 'num_publications',
            'reference_sim']
    assert_equal(scientist5.matches_homonyms.columns.tolist(), cols)
    expected = ['55515260500', '55515260500', '55515260500', '55515260500',
                '55515260500', '55515260500', '56856438600', '56856438600',
                '56856438600', '56856438600', '56856438600', '56856438600',
                '56856438600', '56856438600', '56856438600', '56856438600',
                '57189495106', '57189495106', '57189495106', '57189495106',
                '57189495106', '57189495106', '57189495106', '57189495106',
                '57189495106', '57189495106', '57189495106']
    assert_equal(scientist5.matches_homonyms.ID.tolist(), expected)
    expected = ['56424167900', '56139234900', '57191843211', '55856793100',
                '51565022800', '57209260852', '57165222700', '57189284830',
                '7401607961', '57220585789', '57211907197', '57196653055',
                '57196653042', '57191768971', '56987166100', '35621870200',
                '56388278900', '56926663500', '51663886900', '57189307598',
                '56223966400', '57212959804', '57212959811', '56381003000',
                '57195356113', '57196843037', '56409399300']
    assert_equal(scientist5.matches_homonyms.ID_homonym.tolist(), expected)


def test_disambiguate_matches_compile_info():
    # the actions are chosen randomly (not based on an actual disambiguation)
    actions = ["", "k", "", "d", "k", "", "d", "k 56223966400", "d"]
    with mock.patch('builtins.input', side_effect=actions):
        scientist5.disambiguate_matches()
    assert_equal(scientist5.matches_disambiguated, MATCHES_DISAMBIGUATED)


def test_disambiguate_matches_stop_at():
    # stop if enough found (but it keeps searching for unique ones)
    # the actions are chosen randomly (not based on an actual disambiguation)
    actions = ["", "k", "", "d", "k", "", "d", "k 56223966400", "d"]
    with mock.patch('builtins.input', side_effect=actions):
        scientist5.disambiguate_matches(stop_at=5)
    assert_true(5 <= len(scientist5.matches_disambiguated) < 17)


def test_disambiguate_matches_invalid_keep():
    # also matches that are not valid based on additional IDs are maintained
    # the actions are chosen randomly (not based on an actual disambiguation)
    actions = ["", "k", "k 57196653055", "d", "", "k 57196653042",
               "d", "k 57220585789", "d", "", "k", "d"]
    with mock.patch('builtins.input', side_effect=actions):
        scientist5.disambiguate_matches(invalid="keep")
    assert_true(len(scientist5.matches_disambiguated), 24)
    check_match = scientist5.matches_disambiguated[-4]
    expected = ['56856438600', '57196653042', '57220585789']
    assert_true(check_match.all_IDs, expected)
