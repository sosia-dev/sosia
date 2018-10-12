#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `AbstractRetrieval` module."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true

import sosia

scientist1 = sosia.Original(55208373700, 2017)


def test_coauthors():
    assert_true(isinstance(scientist1.coauthors, set))
    assert_equal(len(scientist1.coauthors), 5)
    assert_true('36617057700' in scientist1.coauthors)
    assert_true('54930777900' in scientist1.coauthors)
    assert_true('54929867200' in scientist1.coauthors)
    assert_true('24781156100' in scientist1.coauthors)
    assert_true('55875219200' in scientist1.coauthors)


def test_fields():
    expected = sorted([1400, 1405, 1405, 1408, 1803, 2002, 2200])
    assert_equal(sorted(scientist1.fields), expected)


def test_first_year():
    assert_equal(scientist1.first_year, '2012')


def test_journals():
    journals = scientist1.journals
    assert_equal(len(journals), 3)
    assert_true('22900' in journals)
    assert_true('23013' in journals)
    assert_true('18769' in journals)


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
