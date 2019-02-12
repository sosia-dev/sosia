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
         "language reference_sim abstract_sim"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(ID='42661166900', name='Fosaas, Morten', first_year=2011,
        num_coauthors=4, num_publications=2, country='Norway', language='eng',
        reference_sim=0.0308, abstract_sim=0.0667),
    Match(ID='54893528800', name='Heimonen, Tomi P.', first_year=2011,
        num_coauthors=3, num_publications=3, country='Finland', language='eng',
        reference_sim=0.0035, abstract_sim=0.0492),
    Match(ID='55268789000', name='Chen, Chun Liang', first_year=2011,
        num_coauthors=3, num_publications=3, country='Taiwan', language='eng',
        reference_sim=0.0, abstract_sim=0.0298),
    Match(ID='55353556300', name='Rosellon, Maureen Ane D.', first_year=2012,
        num_coauthors=3, num_publications=4, country='Philippines', language='eng',
        reference_sim=0.0, abstract_sim=0.0314),
    Match(ID='55611347500', name='Zhao, Yingxin', first_year=2013,
        num_coauthors=4, num_publications=2, country='China', language='eng',
        reference_sim=0.0, abstract_sim=0.0298),
    Match(ID='55916383400', name='Del Prado, Fatima Lourdes E.', first_year=2012,
        num_coauthors=3, num_publications=2, country='Philippines', language='eng',
        reference_sim=0.0, abstract_sim=0.1004),
    Match(ID='56282273300', name='Rodríguez, José Carlos', first_year=2011,
        num_coauthors=4, num_publications=4, country='Mexico', language='eng',
        reference_sim=0.0087, abstract_sim=0.1047)]


def test_search_sources():
    scientist1.define_search_sources()
    search_sources = scientist1.search_sources
    assert_equal(len(search_sources), 60)
    assert_true((14726, 'Technovation') in search_sources)
    assert_true((22009, 'Corporate Governance (Oxford)') in search_sources)
    for j in scientist1.sources:
        assert_true(j in search_sources)


def test_search_sources_change():
    backup = scientist1.search_sources
    expected = {(14351, 'Brain Research Reviews'),
                (18632, 'Progress in Brain Research')}
    scientist1.search_sources, _ = zip(*expected)
    assert_equal(scientist1.search_sources, expected)
    scientist1.search_sources = backup


def test_search_group():
    scientist1.define_search_group()
    group = scientist1.search_group
    assert_equal(len(group), 302)
    assert_true(isinstance(group, list))


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True)
    group = scientist1.search_group
    assert_equal(len(group), 524)
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
