#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for nlp module."""

from string import digits, punctuation
import warnings

from nose.tools import assert_equal, assert_true
from numpy import array
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.processing import clean_abstract, compute_cos, tokenize_and_stem

warnings.filterwarnings("ignore")
STOPWORDS = list(ENGLISH_STOP_WORDS)
STOPWORDS.extend(punctuation + digits)


def test_clean_abstract():
    expected = "Lorem ipsum."
    assert_equal(clean_abstract("Lorem ipsum. © dolor sit."), expected)
    assert_equal(clean_abstract("© dolor sit. Lorem ipsum."), expected)
    assert_equal(clean_abstract(expected), expected)


def test_compute_cos():
    expected = 0.6875
    received = compute_cos(csr_matrix(array([[0.5, 0.75], [1, 0.25]])))
    assert_equal(received, expected)


def test_tokenize_and_stem():
    expected = ["lorem", "1", "2", "3", "ipsum"]
    received = tokenize_and_stem("Lorem 1 2 3 Ipsum")
    assert_equal(received, expected)
