# -*- coding: utf-8 -*-
"""Tests for class `Original`."""

import warnings
from os.path import expanduser

import mock
from nose.tools import assert_equal, assert_true, assert_false

from sosia.classes import Disambiguator

warnings.filterwarnings("ignore")

test_cache = expanduser("~/.sosia/test.sqlite")
refresh = False
test_params = {"refresh": refresh, "sql_fname": test_cache}

# Test objects
scientist_unique = Disambiguator(55208373700)
scientist1 = Disambiguator(56408947300)
scientist2 = Disambiguator(56408947300, in_subjects=False)
fields = ["first_year", "num_publications", "num_citations", "num_coauthors"]
scientist3 = Disambiguator(7402594593, homonym_fields=fields)
scientist4 = Disambiguator(7402594593, homonym_fields=fields, limit=85)


def test_homonyms_num():
    assert_equal(scientist_unique.homonyms_num, 0)
    assert_equal(scientist1.homonyms_num, 4)
    assert_equal(scientist2.homonyms_num, 10)
    assert_equal(scientist3.homonyms_num, 82)
    assert_equal(scientist4.homonyms_num, 41)


def test_homonyms():
    # unique
    assert_true(scientist_unique.homonyms.empty)
    # 1
    expected = ['56708258300', '57210253022', '56818365000', '57217210913']
    cols = ['surname', 'initials', 'givenname', 'affiliation', 'documents',
            'affiliation_id', 'city', 'country', 'areas', 'ID', 'first_year',
            'num_publications', 'num_citations', 'num_coauthors',
            'reference_sim', 'abstract_sim', 'cross_citations']
    assert_equal(scientist1.homonyms.ID.tolist(), expected)
    assert_equal(scientist1.homonyms.columns.tolist(), cols)
    # 2 (in_subjects = False)
    expected = ['57189045584', '56708258300', '57209105951', '57210253022',
                '57206034883', '56818365000', '57217210913', '57198260240',
                '57198260239', '56709712700']
    assert_equal(scientist2.homonyms.ID.tolist(), expected)
    # 3 (less fields)
    assert_true(scientist3.homonyms.empty)
    # 4 (less fields, higher limit for number of homonyms)
    expected = ['57203322376', '57198984555', '57117072300', '57199865447',
                '9233480100', '57211748047', '36570881000', '7402594766',
                '57215598612', '57214382058', '57214382052', '56174116400',
                '57207832036', '57216170427', '7402595118', '57189024795',
                '56359701800', '57207213853', '57197366160', '18838299400',
                '57214382056', '36779276500', '57197366161', '57200672122',
                '55973105600', '57010681100', '57189160837', '57189308928',
                '57190650852', '57198984584', '57198984639', '57211839097',
                '57208588936', '57208588938', '57211988207', '57215609025',
                '57216300148', '57217161739', '57219744840', '57220739018',
                '55416603200']
    cols = ['surname', 'initials', 'givenname', 'affiliation', 'documents',
            'affiliation_id', 'city', 'country', 'areas', 'ID', 'first_year',
            'num_publications', 'num_citations', 'num_coauthors']
    assert_equal(scientist4.homonyms.ID.tolist(), expected)
    assert_equal(scientist4.homonyms.columns.tolist(), cols)


def test_uniqueness():
    assert_equal(scientist_unique.uniqueness, 1)
    assert_equal(scientist1.uniqueness, 0.05025125628140704)
    assert_equal(scientist2.uniqueness, 0.045871559633027525)
    assert_equal(scientist3.uniqueness, None)
    assert_equal(scientist4.uniqueness, 0.03203203203203203)


def test_name_compatible():
    # 1
    func = scientist1.name_compatible()
    assert_true(func("Giacomo M."))
    # 3
    func = scientist3.name_compatible()
    assert_true(func("Michael"))
    assert_true(func("Michael Dude"))
    assert_false(func("Michael J."))
    assert_false(func("Michael J."))


def test_disambiguate():
    # the actions are chosen randomly (not based on an actual disambiguation)
    # exit immediately (the main ID remains the only one returned)
    expected = ['56408947300']
    actions = ['', 'e']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate()
    assert_equal(scientist1.disambiguated_ids, expected)
    # drop all (same result)
    expected = ['56408947300']
    actions = ['', 'd']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate()
    assert_equal(scientist1.disambiguated_ids, expected)
    # keep all
    expected = ['56408947300', '56708258300', '57210253022', '56818365000',
                '57217210913']
    actions = ['', 'k']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate()
    assert_equal(scientist1.disambiguated_ids, expected)
    # keep and drop some ID
    expected = ['56408947300', '56708258300']
    actions = ['', 'k 56708258300', 'd 57210253022,56818365000',
               'e']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate()
    assert_equal(scientist1.disambiguated_ids, expected)
    # try something and abort
    expected = ['56408947300']
    actions = ['', 'k 56708258300', 'a']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate()
    assert_equal(scientist1.disambiguated_ids, expected)


def test_disambiguate_show_main():
    # the actions are chosen randomly (not based on an actual disambiguation)
    # suppress showing main scientist
    expected = ['56408947300']
    actions = ['k 56708258300', 'a']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate(show_main=False)
    assert_equal(scientist1.disambiguated_ids, expected)


def test_disambiguate_search_cv():
    # the actions are chosen randomly (not based on an actual disambiguation)
    # searching for cv at the same time
    expected = ['56408947300']
    actions = ['', 'http://mock/link', 'k 56708258300', 'a']
    with mock.patch('builtins.input', side_effect=actions):
        scientist1.disambiguate(show_main=False, search_cv=True)
    assert_equal(scientist1.disambiguated_ids, expected)
    assert_equal(scientist1.cv_file_id, 'Rossi_Giacomo_56408947300')
    assert_equal(scientist1.cv_link, "http://mock/link")
