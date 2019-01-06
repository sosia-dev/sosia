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

fields = "ID name first_year num_coauthors num_publications country "\
         "reference_sim abstract_sim"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(ID='42661166900', name='Fosaas, Morten', first_year=2011,
        num_coauthors=4, num_publications=2, country='Norway',
        reference_sim=0.026, abstract_sim=0.1205),
    Match(ID='54893528800', name='Heimonen, Tomi P.', first_year=2011,
        num_coauthors=3, num_publications=3, country='Finland',
        reference_sim=0.0022, abstract_sim=0.1131),
    Match(ID='55268789000', name='Chen, Chun Liang', first_year=2011,
        num_coauthors=3, num_publications=3, country='Taiwan',
        reference_sim=0.0, abstract_sim=0.0889),
    Match(ID='56282273300', name='Rodríguez, José Carlos', first_year=2011,
        num_coauthors=4, num_publications=4, country='Mexico',
        reference_sim=0.0068, abstract_sim=0.1507)]


def test_search_sources():
    scientist1.define_search_sources()
    jour = scientist1.search_sources
    assert_equal(len(jour), 60)
    assert_true(14726 in jour)
    assert_true(22009 in jour)
    for j in scientist1.sources:
        assert_true(j in jour)


def test_search_group():
    scientist1.define_search_group()
    group = scientist1.search_group
    assert_equal(len(group), 227)
    assert_true(isinstance(group, list))


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True)
    group = scientist1.search_group
    assert_equal(len(group), 527)
    assert_true(isinstance(group, list))


def test_find_matches():
    recieved = sorted(scientist1.find_matches())
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = ['ID', 'name', 'first_year', 'num_coauthors', 'num_publications',
            'country', 'reference_sim']
    df_r = pd.DataFrame(recieved)
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim,float))
        assert_true(0 <= e.abstract_sim <= 1)


def test_find_matches_stacked():
    recieved = sorted(scientist1.find_matches(stacked=True))
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    cols = ['ID', 'name', 'first_year', 'num_coauthors', 'num_publications',
            'country', 'reference_sim']
    df_r = pd.DataFrame(recieved)
    df_m = pd.DataFrame(MATCHES)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])
    for e in recieved:
        assert_true(isinstance(e.abstract_sim,float))
        assert_true(0 <= e.abstract_sim <= 1)
