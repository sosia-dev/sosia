#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for queries module."""

from nose.tools import assert_equal
from scopus import ScopusSearch

from sosia.utils import find_country


def test_find_country():
    pubs = ScopusSearch('AU-ID(6701809842)').results
    received = find_country(['6701809842'], pubs, 2000)
    assert_equal(received, 'Germany')
