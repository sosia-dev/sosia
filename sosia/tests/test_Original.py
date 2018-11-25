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
match = namedtuple("Match", fields)
MATCHES = [
    match(ID='42661166900', name='Fosaas, Morten', first_year=2011,
        num_coauthors=4, num_publications=3, country='Norway',
        reference_sim=0.0233, abstract_sim=0.1264),
    match(ID='54893528800', name='Heimonen, Tomi P.', first_year=2011,
        num_coauthors=5, num_publications=4, country='France',
        reference_sim=0.0013, abstract_sim=0.1128),
    match(ID='55268789000', name='Chen, Chun Liang', first_year=2011,
        num_coauthors=4, num_publications=5, country='Taiwan',
        reference_sim=0.0, abstract_sim=0.0887),
    match(ID='56282273300', name='Rodríguez, José Carlos', first_year=2011,
        num_coauthors=5, num_publications=5, country='Mexico',
        reference_sim=0.0043, abstract_sim=0.1503)]


def test_country():
    assert_equal(scientist1.country, 'Switzerland')


def test_coauthors():
    assert_true(isinstance(scientist1.coauthors, set))
    expected = ['36617057700', '54930777900', '54929867200',
                '24781156100', '55875219200']
    assert_equal(len(scientist1.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist1.coauthors)


def test_fields():
    expected = sorted([1400, 1405, 1405, 1408, 1803, 2002, 2200])
    assert_equal(sorted(scientist1.fields), expected)


def test_first_year():
    assert_equal(scientist1.first_year, 2012)


def test_sources():
    sources = scientist1.sources
    assert_equal(len(sources), 3)
    assert_true(22900 in sources)
    assert_true(23013 in sources)
    assert_true(18769 in sources)


def test_main_field():
    expected = (1405, 'BUSI')
    assert_equal(scientist1.main_field, expected)


def test_publications():
    pubs = scientist1.publications
    assert_equal(len(pubs), 4)
    fields = 'eid doi pii title subtype creator authname authid afid coverDate '\
             'coverDisplayDate publicationName issn source_id aggregationType'\
             ' volume issueIdentifier pageRange citedby_count openaccess'
    doc = namedtuple('Document', fields)
    expected = doc(eid='2-s2.0-84959420483', doi='10.1016/j.respol.2015.12.006',
        pii='S0048733315002000', title="The productivity of science &amp; engineering PhD students hired from supervisors' networks",
        subtype='ar', creator='Baruffaldi S.', citedby_count='5',
        authname='Baruffaldi S.;Visentin F.;Conti A.',
        authid='55208373700;55875219200;36617057700', openaccess='0',
        afid='60028186;60028186-106299773;60019647', coverDate='2016-05-01',
        coverDisplayDate='1 May 2016', publicationName='Research Policy',
        issn='00487333', source_id='22900', aggregationType='Journal',
        volume='45', issueIdentifier='4', pageRange='785-796')
    assert_equal(pubs[0], expected)


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
    assert_equal(len(group), 313)
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
        assert_true(e in recieved)


def test_find_matches_stacked():
    recieved = sorted(scientist1.find_matches(stacked=True))
    assert_equal(len(recieved), len(MATCHES))
    assert_true(isinstance(recieved, list))
    for e in MATCHES:
        assert_true(e in recieved)
