#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for class `Scientist`."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true

from sosia.classes import Scientist

scientist1 = Scientist(['6701809842'], 2001)
scientist2 = Scientist(['55208373700', '55208373700', '99'], 2017)
eids = ['2-s2.0-84959420483', '2-s2.0-84949113230']
scientist3 = Scientist(['55208373700'], 2017, eids=eids)


def test_country():
    assert_equal(scientist1.country, 'Germany')
    assert_equal(scientist2.country, 'Switzerland')
    assert_equal(scientist3.country, 'Switzerland')


def test_coauthors():
    assert_true(isinstance(scientist1.coauthors, set))
    expected = {'7101829476', '6506756510', '6701494844', '7005044638',
                '6506426539', '35838036900', '7004064836', '6506571902',
                '11042582400'}
    assert_equal(len(scientist1.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist1.coauthors)
    assert_true(isinstance(scientist2.coauthors, set))
    expected = {'55875219200', '54929867200', '36617057700', '24781156100',
                '54930777900'}
    assert_equal(len(scientist2.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist2.coauthors)
    assert_true(isinstance(scientist3.coauthors, set))
    expected = {'36617057700', '55875219200', '54930777900', '54929867200'}
    assert_equal(len(scientist3.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist3.coauthors)


def test_fields():
    expected = [1803, 1408, 1405, 1803, 1408, 3301, 2002, 2003, 2002,
                3317, 2002, 1400, 2002, 1400, 1402, 2002, 2200]
    assert_equal(scientist1.fields, expected)
    expected = [1803, 1408, 1405, 1400, 1405, 2002, 2200]
    assert_equal(scientist2.fields, expected)
    expected = [1803, 1408, 1405, 2002, 2200]
    assert_equal(scientist3.fields, expected)


def test_first_year():
    assert_equal(scientist1.first_year, 1996)
    assert_equal(scientist2.first_year, 2012)
    assert_equal(scientist3.first_year, 2016)


def test_sources():
    received = scientist1.sources
    expected = {17472, 28994, 24389, 24204, 22900, 21307, 26878}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist2.sources
    expected = {18769, 22900, 23013}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist3.sources
    expected = {18769, 22900}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)


def test_main_field():
    assert_equal(scientist1.main_field, (2002, 'ECON'))
    assert_equal(scientist2.main_field, (1405, 'BUSI'))
    assert_equal(scientist3.main_field, (1803, 'DECI'))


def test_name():
    assert_equal(scientist1.name, 'Harhoff, Dietmar')
    assert_equal(scientist2.name, 'Baruffaldi, Stefano Horst')
    assert_equal(scientist3.name, 'Baruffaldi, Stefano Horst')


def test_publications():
    fields = 'eid doi pii title subtype creator authname authid afid  '\
             'coverDate coverDisplayDate publicationName issn source_id '\
             'aggregationType volume issueIdentifier pageRange '\
             'citedby_count openaccess'
    doc = namedtuple('Document', fields)
    received = scientist1.publications
    assert_equal(len(received), 8)
    expected = doc(eid='2-s2.0-0001093103', pii='S004873339900089X',
        title='Technology policy for a world of skew-distributed outcomes',
        doi='10.1016/S0048-7333(99)00089-X', source_id='22900',
        creator='Scherer F.', authname='Scherer F.;Harhoff D.', subtype='ar',
        authid='7004064836;6701809842', afid='60006332;60028717',
        volume='29', coverDate='2000-01-01', coverDisplayDate='April 2000',
        openaccess='0', publicationName='Research Policy', issn='00487333',
        citedby_count='228', aggregationType='Journal',
        pageRange='559-566', issueIdentifier='4-5')
    assert_equal(received[0], expected)
    received = scientist2.publications
    assert_equal(len(received), 4)
    expected = doc(eid='2-s2.0-84866317084', aggregationType='Journal',
        doi='10.1016/j.respol.2012.04.005', pii='S004873331200114X',
        title='Return mobility and scientific productivity of researchers working abroad: The role of home country linkages',
        subtype='ar', creator='Baruffaldi S.', source_id='22900',
        authname='Baruffaldi S.;Landoni P.', authid='55208373700;24781156100',
        afid='60097412;60023256', coverDate='2012-11-01', issn='00487333',
        coverDisplayDate='November 2012', publicationName='Research Policy',
        volume='41', issueIdentifier='9', pageRange='1655-1665',
        citedby_count='38', openaccess='0')
    assert_equal(received[-1], expected)
    received = scientist3.publications
    assert_equal(len(received), 2)
    expected = doc(eid='2-s2.0-84959420483', volume='45', issueIdentifier='4',
        doi='10.1016/j.respol.2015.12.006', pii='S0048733315002000',
        title="The productivity of science &amp; engineering PhD students hired from supervisors' networks",
        subtype='ar', creator='Baruffaldi S.', citedby_count='5',
        authname='Baruffaldi S.;Visentin F.;Conti A.', pageRange='785-796',
        authid='55208373700;55875219200;36617057700', openaccess='0',
        afid='60028186;60028186-106299773;60019647', coverDate='2016-05-01',
        coverDisplayDate='1 May 2016', publicationName='Research Policy',
        issn='00487333', source_id='22900', aggregationType='Journal')
    assert_equal(received[0], expected)

def test_language():
    assert_equal(scientist1.language, None)
    scientist1.get_publication_languages()
    assert_equal(scientist1.language, "eng")
    scientist3.get_publication_languages()
    assert_equal(scientist3.language, "eng")
