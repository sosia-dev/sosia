"""Tests for class `Scientist`."""

from collections import namedtuple
from pathlib import Path

from nose.tools import assert_equal, assert_true, assert_false

from sosia.classes import Scientist
from sosia.establishing import make_database

test_cache = Path.home()/".cache/sosia/test.sqlite"
refresh = False
test_params = {"refresh": refresh, "sql_fname": test_cache}

scientist1 = Scientist([6701809842], 2001, **test_params)
scientist2 = Scientist([55208373700, 55208373700], 2017, **test_params)
eids = ["2-s2.0-84959420483", "2-s2.0-84949113230"]
scientist3 = Scientist([55208373700], 2017, eids=eids, **test_params)
scientist4 = Scientist([55208373700], 2015, **test_params)
scientist5 = Scientist([55208373700], 2018, period=2, **test_params)


def test_active_year():
    assert_equal(scientist1.active_year, 2001)
    assert_equal(scientist2.active_year, 2017)
    assert_equal(scientist3.active_year, 2016)
    assert_equal(scientist4.active_year, 2012)
    assert_equal(scientist5.active_year, 2018)


def test_affiliation_country():
    assert_equal(scientist1.affiliation_country, "Germany")
    assert_equal(scientist2.affiliation_country, "Switzerland")
    assert_equal(scientist3.affiliation_country, "Switzerland")
    assert_equal(scientist4.affiliation_country, "Switzerland")
    assert_equal(scientist5.affiliation_country, "Germany")


def test_affiliation_id():
    assert_equal(scientist1.affiliation_id, '60028717')
    assert_equal(scientist2.affiliation_id, '60028186')
    assert_equal(scientist3.affiliation_id, '60028186')
    assert_equal(scientist4.affiliation_id, '60028186')
    assert_equal(scientist5.affiliation_id, '60105007')


def test_affiliation_name():
    assert_equal(scientist1.affiliation_name,
                 'Ludwig-Maximilians-Universität München')
    epfl = 'Ecole Polytechnique Fédérale de Lausanne'
    assert_equal(scientist2.affiliation_name, epfl)
    assert_equal(scientist3.affiliation_name, epfl)
    assert_equal(scientist4.affiliation_name, epfl)
    assert_equal(scientist5.affiliation_name,
                 'Max Planck Institute for Innovation and Competition')


def test_affiliation_type():
    assert_equal(scientist1.affiliation_type, 'univ')
    assert_equal(scientist2.affiliation_type, 'univ')
    assert_equal(scientist3.affiliation_type, 'univ')
    assert_equal(scientist4.affiliation_type, 'univ')
    assert_equal(scientist5.affiliation_type, 'resi')


def test_citations():
    assert_true(scientist1.citations >= 47)
    assert_true(scientist2.citations >= 28)
    assert_true(scientist3.citations >= 2)
    assert_true(scientist4.citations >= 19)
    assert_true(scientist5.citations >= 44)


def test_citations_period():
    assert_equal(scientist2.citations_period, None)
    assert_equal(scientist5.citations_period, 3)


def test_coauthors():
    assert_true(isinstance(scientist1.coauthors, set))
    expected = {7005044638, 6602701792, 35838036900, 6506756510,
                24364642400, 6506571902, 6506426539, 6701494844,
                11042582400, 7004064836, 7101829476}
    assert_equal(len(scientist1.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist1.coauthors)
    assert_true(isinstance(scientist2.coauthors, set))
    expected = {24464562500, 24781156100, 36617057700, 54929867200,
                54930777900, 55875219200, 57217825601}
    assert_equal(len(scientist2.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist2.coauthors)
    assert_true(isinstance(scientist3.coauthors, set))
    expected = {36617057700, 55875219200, 54930777900, 54929867200}
    assert_equal(len(scientist3.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist3.coauthors)
    expected = {36617057700, 54929867200, 54930777900, 55875219200}
    assert_equal(len(scientist3.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors)
    expected = {24464562500, 24781156100, 36617057700, 54929867200,
                54930777900, 55875219200, 57131011400, 57217825601}
    assert_equal(len(scientist5.coauthors), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors)


def test_coauthors_period():
    assert_equal(scientist3.coauthors_period, None)
    expected = {24464562500, 24781156100, 54930777900,
                55875219200, 57131011400, 57217825601}
    assert_equal(len(scientist5.coauthors_period), len(expected))
    for coauth in expected:
        assert_true(coauth in scientist5.coauthors_period)


def test_fields():
    expected = [2002, 2003, 2002, 2308, 1408, 1803, 1405, 1408, 1803, 2002,
                3301, 1400, 1402, 2002, 2002, 3317, 1400, 2002, 1405, 2000]
    assert_equal(set(scientist1.fields), set(expected))
    expected = [2300, 3300, 2002, 1405, 1408, 1803, 1400, 1405]
    assert_equal(set(scientist2.fields), set(expected))
    expected = [2002, 1405, 1408, 1803]
    assert_equal(set(scientist3.fields), set(expected))


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
    assert_equal(scientist3.main_field, (2002, "BUSI"))


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


def test_publication_languages():
    assert_equal(scientist1.language, None)
    scientist1.get_publication_languages()
    assert_equal(scientist1.language, "eng")
    scientist3.get_publication_languages()
    assert_equal(scientist3.language, "eng")


def test_publications_period():
    assert_equal(scientist1.publications_period, None)
    assert_equal(len(scientist5.publications_period), 4)
