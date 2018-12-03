#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true
import warnings

import sosia

warnings.filterwarnings("ignore")
scientist1 = sosia.Original(55208373700, 2017)

fields = "ID name first_year num_coauthors num_publications country "\
         "reference_sim abstract_sim"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(ID='42661166900', name='Fosaas, Morten', first_year=2011,
        num_coauthors=4, num_publications=3, country='Norway',
        reference_sim=0.0233, abstract_sim=0.1264), 
    Match(ID='54893528800', name='Heimonen, Tomi P.', first_year=2011,
        num_coauthors=5, num_publications=4, country='France',
        reference_sim=0.0013, abstract_sim=0.1128),
    Match(ID='55268789000', name='Chen, Chun Liang', first_year=2011,
        num_coauthors=4, num_publications=5, country='Taiwan',
        reference_sim=0.0, abstract_sim=0.0887),
    Match(ID='56282273300', name='Rodríguez, José Carlos', first_year=2011,
        num_coauthors=5, num_publications=5, country='Mexico',
        reference_sim=0.0043, abstract_sim=0.1503)]


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
    assert_equal(len(group), 310)
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
    for e in MATCHES:
        print(e)
        assert_true(e in recieved)


def test_find_matches_stacked():
    recieved = sorted(scientist1.find_matches(stacked=True))
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    for e in MATCHES:
        assert_true(e in recieved)
