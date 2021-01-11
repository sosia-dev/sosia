# -*- coding: utf-8 -*-
"""Tests for utils.helpers module."""

from sosia.utils import clean_name

from nose.tools import assert_equal


def test_clean_name():
    name_test = "Smith, John(Jr.)"
    name_clean = "Smith, John Jr."
    assert_equal(clean_name(name_test), name_clean)
