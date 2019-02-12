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
    expected = {(24389, 'Journal of Industrial Economics'),
        (17472, 'Journal of Banking and Finance'),
        (24204, 'Review of Economics and Statistics'),
        (21307, 'Management Science'), (22900, 'Research Policy'),
        (26878, 'Journal of Population Economics'),
        (28994, 'Journal of Evolutionary Economics')}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist2.sources
    expected = {(18769, 'Applied Economics Letters'),
        (22900, 'Research Policy'), (23013, 'Industry and Innovation')}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)
    received = scientist3.sources
    expected = {(18769, 'Applied Economics Letters'), (22900, 'Research Policy')}
    assert_equal(len(received), len(expected))
    for e in expected:
        assert_true(e in received)


def test_sources_change():
    backup = scientist1.sources
    expected = {(14351, 'Brain Research Reviews'),
                (18632, 'Progress in Brain Research')}
    scientist1.sources, _ = zip(*expected)
    assert_equal(scientist1.sources, expected)
    scientist1.sources = backup


def test_main_field():
    assert_equal(scientist1.main_field, (2002, 'ECON'))
    assert_equal(scientist2.main_field, (1405, 'BUSI'))
    assert_equal(scientist3.main_field, (1803, 'DECI'))


def test_name():
    assert_equal(scientist1.name, 'Harhoff, Dietmar')
    assert_equal(scientist2.name, 'Baruffaldi, Stefano Horst')
    assert_equal(scientist3.name, 'Baruffaldi, Stefano Horst')


def test_publications():
    fields = 'eid doi pii pubmed_id title subtype creator afid affilname '\
        'affiliation_city affiliation_country author_count author_names '\
        'author_ids author_afids coverDate coverDisplayDate '\
        'publicationName issn source_id eIssn aggregationType volume '\
        'issueIdentifier article_number pageRange description authkeywords '\
        'citedby_count openaccess fund_acr fund_no fund_sponsor'
    doc = namedtuple('Document', fields)
    # scientist1
    received = scientist1.publications
    assert_equal(len(received), 8)
    abstract = 'This paper draws implications for technology policy from '\
        'evidence on the size distribution of returns from eight sets of '\
        'data on inventions and innovations attributable to private sector '\
        'firms and universities. The distributions are all highly skew; the '\
        'top 10% of sample members captured from 48 to 93 percent of total '\
        'sample returns. It follows that programs seeking to advance '\
        'technology should not be judged negatively if they lead to '\
        'numerous economic failures; rather, emphasis should be placed on '\
        'the relatively few big successes. To achieve noteworthy success '\
        'with appreciable confidence, a sizeable array of projects must '\
        'often be supported. The outcome distributions are sufficiently '\
        'skewed that, even with large numbers of projects, it is not '\
        'possible to diversify away substantial residual variability '\
        'through portfolio strategies.'
    expected = doc(eid='2-s2.0-0001093103', doi='10.1016/S0048-7333(99)00089-X',
        pii='S004873339900089X', pubmed_id=None, title='Technology policy for a world of skew-distributed outcomes',
        subtype='ar', creator='Scherer F.', afid='60006332;60028717',
        affilname='John F. Kennedy School of Government;Ludwig-Maximilians-Universität München',
        affiliation_city='Cambridge;Munich', affiliation_country='United States;Germany',
        author_count='2', author_names='Scherer, F. M.;Harhoff, Dietmar',
        author_ids='7004064836;6701809842', author_afids='60006332;60028717',
        coverDate='2000-01-01', coverDisplayDate='April 2000',
        publicationName='Research Policy', issn='00487333', source_id='22900',
        eIssn=None, aggregationType='Journal', volume='29', issueIdentifier='4-5',
        article_number=None, pageRange='559-566', description=abstract,
        authkeywords='Innovation | Portfolio strategies | Risk | Skewness',
        citedby_count='235', openaccess='0', fund_acr=None, fund_no='undefined',
        fund_sponsor='Alfred P. Sloan Foundation')
    assert_equal(received[0], expected)
    # scientist2
    received = scientist2.publications
    assert_equal(len(received), 4)
    abstract = 'Through an analysis of 497 foreign researchers in Italy and '\
        'Portugal we verify the impact of home linkages on return mobility '\
        'choices and scientific productivity. We consider the presence of '\
        'several different types of linkages of the researchers working '\
        'abroad with their country of origin and control for the most '\
        'relevant contextual factors (age, research area, position in the '\
        'host country, etc.). The probability of return to their home '\
        'country and scientific productivity in the host country are both '\
        'higher for researchers that maintain home linkages. We conclude '\
        'that the presence of home linkages directly benefits both '\
        'countries in addition to the indirect benefit of expanding the '\
        'scientific networks. Policy implications and suggestions for '\
        'further research are discussed. © 2012 Elsevier B.V. All rights reserved.'
    title = 'Return mobility and scientific productivity of researchers '\
            'working abroad: The role of home country linkages'
    expected = doc(eid='2-s2.0-84866317084', doi='10.1016/j.respol.2012.04.005',
        pii='S004873331200114X', pubmed_id=None, title=title,
        subtype='ar', creator='Baruffaldi S.', afid='60097412;60023256',
        affilname='CDM;Politecnico di Milano', affiliation_city='Cambridge;Milan',
        affiliation_country='United States;Italy', author_count='2',
        author_names='Baruffaldi, Stefano H.;Landoni, Paolo',
        author_ids='55208373700;24781156100', author_afids='60097412;60023256',
        coverDate='2012-11-01', coverDisplayDate='November 2012',
        publicationName='Research Policy', issn='00487333', source_id='22900',
        eIssn=None, aggregationType='Journal', volume='41', issueIdentifier='9',
        article_number=None, pageRange='1655-1665', description=abstract,
        authkeywords='Brain drain | Home country linkages | Migration | Mobility',
        citedby_count='39', openaccess='0', fund_acr=None, fund_no='undefined',
        fund_sponsor=None)
    assert_equal(received[-1], expected)
    # scientist3
    received = scientist3.publications
    assert_equal(len(received), 2)
    abstract = "© 2016 Elsevier B.V. All rights reserved. We compare the "\
        "scientific productivity of PhD students who are hired from a "\
        "fine-grained set of mutually exclusive affiliation types: a PhD "\
        "supervisor's affiliation, an external affiliation from which the "\
        "supervisor derives her coauthors, and an external affiliation with "\
        "which the supervisor has no coauthorship ties. Using a novel "\
        "dataset of science and engineering PhD students who graduated from "\
        "two major Swiss universities, we find that the most productive PhD "\
        "category is the one made of students who are affiliated with "\
        "universities other than their supervisors' affiliation, but from "\
        "which the PhD supervisors derive their coauthors. This result "\
        "suggests an inverted U-shaped relationship between PhD students' "\
        "productivity and the social distance from their supervisors. "\
        "Additionally, we find evidence consistent with the role of "\
        "supervisors' coauthor networks in resolving information "\
        "asymmetries regarding PhD talent."
    title = "The productivity of science &amp; engineering PhD students "\
            "hired from supervisors' networks"
    expected = doc(eid='2-s2.0-84959420483', doi='10.1016/j.respol.2015.12.006',
        pii='S0048733315002000', pubmed_id=None, title=title,
        subtype='ar', creator='Baruffaldi S.', afid='60028186;106299773;60019647',
        affilname='Swiss Federal Institute of Technology EPFL, Lausanne;BRICK;Georgia Institute of Technology',
        affiliation_city='Lausanne;Torino;Atlanta',
        affiliation_country='Switzerland;Italy;United States', author_count='4',
        author_names='Baruffaldi, Stefano;Visentin, Fabiana;Conti, Annamaria',
        author_ids='55208373700;55875219200;36617057700',
        author_afids='60028186;60028186-106299773;60019647',
        coverDate='2016-05-01', coverDisplayDate='1 May 2016',
        publicationName='Research Policy', issn='00487333', source_id='22900',
        eIssn=None, aggregationType='Journal', volume='45', issueIdentifier='4',
        article_number=None, pageRange='785-796', description=abstract,
        authkeywords="PhD students | Scientific productivity | Supervisors' networks",
        citedby_count='5', openaccess='0', fund_acr='UNIL', fund_no='149931',
        fund_sponsor='Université de Lausanne')
    assert_equal(received[0], expected)

def test_language():
    assert_equal(scientist1.language, None)
    scientist1.get_publication_languages()
    assert_equal(scientist1.language, "eng")
    scientist3.get_publication_languages()
    assert_equal(scientist3.language, "eng")
