#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for class `Scientist`."""

from collections import namedtuple
from nose.tools import assert_equal, assert_true, assert_false

from sosia.classes import Scientist

scientist1 = Scientist(["6701809842"], 2001, refresh=True)
scientist2 = Scientist(["55208373700", "55208373700"], 2017, refresh=True)
eids = ["2-s2.0-84959420483", "2-s2.0-84949113230"]
scientist3 = Scientist(["55208373700"], 2017, eids=eids, refresh=True)
scientist4 = Scientist(["55208373700"], 2015, refresh=True)
scientist5 = Scientist(["55208373700"], 2018, period=2, refresh=True)


def test_affiliation():
    org = 'University of Essex; Universität München'
    assert_equal(scientist1.organization, org)
    org = 'École Polytechnique Fédérale de Lausanne (EPFL)'
    assert_equal(scientist2.organization, org)
    org = 'Department of Economics and Management of Innovation, '\
          'École Polytechnique Fédérale de Lausanne'
    assert_equal(scientist3.organization, org)
    org = 'École Polytechnique Fédérale de Lausanne, CEMI, CDM MTEI-GE'
    assert_equal(scientist4.organization, org)
    org = 'Max Planck Institute for Innovation and Competition'
    assert_equal(scientist5.organization, org)


def test_affiliation_id():
    assert_equal(scientist1.affiliation_id, '60001359; 60028717')
    assert_equal(scientist2.affiliation_id, '60028186')
    assert_equal(scientist3.affiliation_id, '60028186')
    assert_equal(scientist4.affiliation_id, '60028186')
    assert_equal(scientist5.affiliation_id, '60105007')


def test_active_year():
    assert_equal(scientist1.active_year, 2001)
    assert_equal(scientist2.active_year, 2017)
    assert_equal(scientist3.active_year, 2016)
    assert_equal(scientist4.active_year, 2012)
    assert_equal(scientist5.active_year, 2018)


def test_country():
    assert_equal(scientist1.country, "United Kingdom")
    assert_equal(scientist2.country, "Switzerland")
    assert_equal(scientist3.country, "Switzerland")
    assert_equal(scientist4.country, "Switzerland")
    assert_equal(scientist5.country, "Germany")


def test_citations():
    assert_true(scientist1.citations >= 47)
    assert_true(scientist2.citations >= 28)
    assert_true(scientist3.citations >= 2)
    assert_true(scientist4.citations >= 19)
    assert_true(scientist5.citations >= 44)


def test_citations_period():
    assert_equal(scientist1.citations_period, scientist1.citations)
    assert_equal(scientist2.citations_period, scientist2.citations)
    assert_equal(scientist3.citations_period, scientist3.citations)
    assert_equal(scientist4.citations_period, scientist4.citations)
    assert_equal(scientist5.citations_period, 2)


def test_coauthors():
    assert_true(isinstance(scientist1.coauthors, set))
    expected = {'7005044638', '6602701792', '35838036900', '6506756510',
                '24364642400', '6506571902', '6506426539', '6701494844',
                '11042582400', '7004064836', '7101829476'}
    assert_equal(len(scientist1.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist1.coauthors)
    assert_true(isinstance(scientist2.coauthors, set))
    expected = {'55875219200', '54929867200', '57191249971', '36617057700',
                '24464562500', '54930777900', '24781156100'}
    assert_equal(len(scientist2.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist2.coauthors)
    assert_true(isinstance(scientist3.coauthors, set))
    expected = {'36617057700', '55875219200', '54930777900', '54929867200'}
    assert_equal(len(scientist3.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist3.coauthors)
    expected = {'36617057700', '54929867200', '54930777900', '55875219200'}
    assert_equal(len(scientist3.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors)
    expected = {'24464562500', '24781156100', '36617057700', '54929867200',
                '54930777900', '55875219200', '57131011400', '57191249971'}
    assert_equal(len(scientist5.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors)


def test_coauthors_period():
    assert_equal(scientist1.coauthors_period, scientist1.coauthors)
    assert_equal(scientist2.coauthors_period, scientist2.coauthors)
    assert_equal(scientist3.coauthors_period, scientist3.coauthors)
    assert_equal(scientist4.coauthors_period, scientist4.coauthors)
    expected = {"24464562500", "24781156100", "54930777900", "55875219200",
                "57131011400", "57191249971"}
    assert_equal(len(scientist5.coauthors_period), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors_period)


def test_fields():
    expected = [1803, 1405, 1408, 1803, 1408, 3301, 2002, 2002, 2308, 2003,
                2002, 2000, 1405, 3317, 2002, 1400, 2002, 1402, 1400, 2002,
                2200, 2308, 2002, 1405, 2000, 2002, 2003, 2002, 1400, 2002,
                1400, 1402, 2002, 3317, 1803, 1408, 1405, 1803, 1408, 2002,
                3301]
    assert_equal(scientist1.fields, expected)
    expected = [1803, 1405, 1408, 3300, 2300, 1400, 1405, 2002, 2200, 2002,
                1405, 1400, 3300, 2300, 1405, 1803, 1408]
    assert_equal(scientist2.fields, expected)
    expected = [1803, 1405, 1408, 2002, 2200, 2002, 1405, 1803, 1408]
    assert_equal(scientist3.fields, expected)


def test_first_year():
    assert_equal(scientist1.first_year, 1996)
    assert_equal(scientist2.first_year, 2012)
    assert_equal(scientist3.first_year, 2016)


def test_sources():
    received = scientist1.sources
    expected = [(17472, 'Journal of Banking and Finance'),
                (20022, 'Economic Policy'),
                (21307, 'Management Science'),
                (22900, 'Research Policy'),
                (24204, 'Review of Economics and Statistics'),
                (24389, 'Journal of Industrial Economics'),
                (26878, 'Journal of Population Economics'),
                (28994, 'Journal of Evolutionary Economics'),
                (10600153365, 'Economics of Innovation and New Technology')]
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist2.sources
    expected = [(23013, 'Industry and Innovation'),
                (21100858668, None),
                (15143, 'Regional Studies'),
                (18769, 'Applied Economics Letters'),
                (22900, 'Research Policy')]
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist3.sources
    expected = [(18769, "Applied Economics Letters"),
                (22900, "Research Policy")]
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)


def test_sources_change():
    backup = scientist1.sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    scientist1.sources, _ = zip(*expected)
    assert_equal(scientist1.sources, expected)
    scientist1.sources = backup


def test_main_field():
    assert_equal(scientist1.main_field, (2002, "ECON"))
    assert_equal(scientist2.main_field, (1405, "BUSI"))
    assert_equal(scientist3.main_field, (1803, "BUSI"))


def test_name():
    assert_equal(scientist1.name, "Harhoff, Dietmar")
    assert_equal(scientist2.name, "Baruffaldi, Stefano Horst")
    assert_equal(scientist3.name, "Baruffaldi, Stefano Horst")


def test_publications():
    cols = ["eid", "affiliation_country", "author_names", "author_ids",
            "author_afids", "coverDate", "authkeywords",
            "citedby_count", "description"]
    # scientist1
    received = scientist1.publications
    assert_true(len(received) >= 11)
    assert_equal(received[2].eid, '2-s2.0-0001093103')
    for p in received:
        assert_true(all(c in p._fields for c in cols))
    # scientist2
    received = scientist2.publications
    assert_true(len(received) >= 7)
    assert_equal(received[-1].eid, "2-s2.0-84866317084")
    for p in received:
        assert_true(all(c in p._fields for c in cols))
    # scientist3
    received = scientist3.publications
    assert_true(len(received) >= 2)
    received = scientist2.publications
    assert_true(len(received) >= 7)
    assert_equal(received[0].eid, "2-s2.0-85015636484")
    for p in received:
        assert_true(all(c in p._fields for c in cols))


def test_publications_period():
    assert_equal(scientist1.publications_period, scientist1.publications)
    assert_equal(scientist2.publications_period, scientist2.publications)
    assert_equal(scientist3.publications_period, scientist3.publications)
    assert_equal(scientist4.publications_period, scientist4.publications)
    assert_equal(len(scientist5.publications_period), 4)


def test_language():
    assert_equal(scientist1.language, None)
    scientist1.get_publication_languages()
    assert_equal(scientist1.language, "eng")
    scientist3.get_publication_languages()
    assert_equal(scientist3.language, "eng")
