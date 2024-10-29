"""Tests for class `Scientist`."""


def test_affiliation_country(scientist1, scientist2, scientist3, scientist4):
    assert scientist1.affiliation_country == "Germany"
    assert scientist2.affiliation_country == "Switzerland"
    assert scientist3.affiliation_country == "Switzerland"
    assert scientist4.affiliation_country == "Switzerland"


def test_affiliation_id(scientist1, scientist2, scientist3, scientist4):
    assert scientist1.affiliation_id == '60028717'
    assert scientist2.affiliation_id == '60028186'
    assert scientist3.affiliation_id == '60028186'
    assert scientist4.affiliation_id == '60028186'


def test_affiliation_name(scientist1, scientist2, scientist3, scientist4):
    lmu = 'Ludwig-Maximilians-Universität München'
    assert scientist1.affiliation_name == lmu
    epfl = 'École Polytechnique Fédérale de Lausanne'
    assert scientist2.affiliation_name == epfl
    assert scientist3.affiliation_name == epfl
    assert scientist4.affiliation_name == epfl


def test_affiliation_type(scientist1, scientist2, scientist3, scientist4):
    assert scientist1.affiliation_type == 'univ'
    assert scientist2.affiliation_type == 'univ'
    assert scientist3.affiliation_type == 'univ'
    assert scientist4.affiliation_type == 'univ'


def test_citations(scientist1, scientist2, scientist3, scientist4):
    assert scientist1.citations >= 47
    assert scientist2.citations >= 28
    assert scientist3.citations >= 2
    assert scientist4.citations >= 19


def test_coauthors(scientist1, scientist2, scientist3):
    assert isinstance(scientist1.coauthors, list)
    expected = [6506426539, 6506571902, 6506756510, 6602701792, 6701494844,
                7004064836, 7005044638, 7101829476, 11042582400, 24364642400,
                35838036900]
    assert len(scientist1.coauthors) == len(expected)
    for coauth in expected:
        assert coauth in scientist1.coauthors
    assert isinstance(scientist2.coauthors, list)
    expected = [24464562500, 24781156100, 36617057700, 54929867200,
                54930777900, 55875219200, 57217825601]
    assert len(scientist2.coauthors) == len(expected)
    for coauth in expected:
        assert coauth in scientist2.coauthors
    assert isinstance(scientist3.coauthors, list)
    expected = [36617057700, 54929867200, 54930777900, 55875219200]
    assert len(scientist3.coauthors) == len(expected)
    for coauth in expected:
        assert coauth in scientist3.coauthors
    expected = [36617057700, 54929867200, 54930777900, 55875219200]
    assert len(scientist3.coauthors) == len(expected)


def test_fields(scientist1, scientist2, scientist3):
    expected = [2002, 2003, 2002, 2308, 1408, 1803, 1405, 1408, 1803, 2002,
                3301, 1400, 1402, 2002, 2002, 3317, 1400, 2002, 1405, 2000]
    assert set(scientist1.fields) == set(expected)
    expected = [2300, 3300, 2002, 1405, 1408, 1803, 1400, 1405]
    assert set(scientist2.fields) == set(expected)
    expected = [2002, 1405, 1408, 1803]
    assert set(scientist3.fields) == set(expected)


def test_first_year(scientist1, scientist2, scientist3):
    assert scientist1.first_year == 1996
    assert scientist2.first_year == 2012
    assert scientist3.first_year == 2016


def test_last_year(scientist1, scientist2, scientist3, scientist4):
    assert scientist1.last_year == 2001
    assert scientist2.last_year == 2017
    assert scientist3.last_year == 2016
    assert scientist4.last_year == 2012


def test_sources(scientist1, scientist2, scientist3):
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
    assert len(received) == len(expected)
    for e in expected:
        assert e in received
    received = scientist2.sources
    expected = [(23013, 'Industry and Innovation'),
                (21100858668, None),
                (15143, 'Regional Studies'),
                (18769, 'Applied Economics Letters'),
                (22900, 'Research Policy')]
    assert len(received) == len(expected)
    for e in expected:
        assert e in received
    received = scientist3.sources
    expected = [(18769, "Applied Economics Letters"),
                (22900, "Research Policy")]
    assert len(received) == len(expected)
    for e in expected:
        assert e in received


def test_sources_change(scientist1):
    backup = scientist1.sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    scientist1.sources, _ = zip(*expected)
    assert scientist1.sources == expected
    scientist1.sources = backup


def test_main_field(scientist1, scientist2, scientist3):
    assert scientist1.main_field == (2002, "ECON")
    assert scientist2.main_field == (1405, "BUSI")
    assert scientist3.main_field == (2002, "BUSI")


def test_name(scientist1, scientist2, scientist3):
    assert scientist1.name == "Harhoff, Dietmar"
    assert scientist2.name == "Baruffaldi, Stefano Horst"
    assert scientist3.name == "Baruffaldi, Stefano Horst"


def test_publications(scientist1, scientist2, scientist3):
    cols = ["eid", "affiliation_country", "author_names", "author_ids",
            "author_afids", "coverDate", "authkeywords",
            "citedby_count", "description"]
    # scientist1
    received = scientist1.publications
    assert len(received) >= 11
    assert received[2].eid == '2-s2.0-0001093103'
    for p in received:
        assert all(c in p._fields for c in cols)
    # scientist2
    received = scientist2.publications
    assert len(received) >= 7
    assert received[-1].eid == "2-s2.0-84866317084"
    for p in received:
        assert all(c in p._fields for c in cols)
    # scientist3
    received = scientist3.publications
    assert len(received) >= 2
    received = scientist2.publications
    assert len(received) >= 7
    assert received[0].eid == "2-s2.0-85015636484"
    for p in received:
        assert all(c in p._fields for c in cols)


def test_publication_languages(scientist1, scientist2, scientist3):
    assert scientist1.language is None
    scientist1.get_publication_languages()
    assert scientist1.language == "eng"
    scientist3.get_publication_languages()
    assert scientist3.language == "eng"
