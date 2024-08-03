"""Tests for class `Original`."""

import warnings
from collections import namedtuple
from pathlib import Path

import pandas as pd

from sosia.classes import Original
from sosia.establishing import make_database

warnings.filterwarnings("ignore")

test_cache = Path.home()/".cache/sosia/test.sqlite"
test_cache.unlink(missing_ok=True)
make_database(test_cache)
refresh = False
test_params = {"refresh": refresh, "sql_fname": test_cache}

# Test objects
# Normal values
scientist1 = Original(55208373700, 2017, cits_margin=200, first_year_margin=1,
                      pub_margin=0.1, coauth_margin=0.1, **test_params)
# Using period and name search mode
scientist2 = Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                      coauth_margin=1, first_year_margin=1, period=3,
                      first_year_search="name", **test_params)
# Using affiliations
affs = [60010348, 60022109, 60017317, 60071236]
scientist3 = Original(55208373700, 2017, cits_margin=200, first_year_margin=1,
                      pub_margin=0.1, affiliations=affs, **test_params)

# Expected matches
fields = "ID name first_year num_coauthors num_publications num_citations "\
         "affiliation_country language num_cited_refs"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(
        ID=53164702100,
        name='Sapprasert, Koson',
        first_year=2011,
        num_coauthors=7,
        num_publications=6,
        num_citations=190,
        affiliation_country='Norway',
        language='eng',
        num_cited_refs=4),
    Match(
        ID=55071051800,
        name='Doldor, Elena',
        first_year=2013,
        num_coauthors=6,
        num_publications=8,
        num_citations=19,
        affiliation_country='United Kingdom',
        language='eng',
        num_cited_refs=0),
    Match(
        ID=55804519400,
        name='González Álvarez, Miguel Domingo',
        first_year=2013,
        num_coauthors=7,
        num_publications=8,
        num_citations=1,
        affiliation_country='Peru',
        language='eng; spa',
        num_cited_refs=0)]


def test_search_sources():
    scientists_list = [scientist1, scientist2, scientist3]
    for s in scientists_list:
        s.define_search_sources()
        search_sources = s.search_sources
        assert len(search_sources) == 61
        assert (20206, "Academy of Management Review") in search_sources
        assert (15143, "Regional Studies") in search_sources


def test_search_sources_change():
    backup = scientist1.search_sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    scientist1.search_sources, _ = zip(*expected)
    assert scientist1.search_sources == expected
    scientist1.search_sources = backup


def test_search_group():
    scientist1.define_search_group(refresh=refresh)
    recieved = scientist1.search_group
    assert isinstance(recieved, list)
    assert 570 <= len(recieved) <= 680


def test_search_group_stacked():
    scientist1.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist1.search_group
    assert isinstance(recieved, list)
    assert 570 <= len(recieved) <= 680


def test_search_group_ignore():
    scientist2.define_search_group(refresh=refresh)
    recieved = scientist2.search_group
    assert isinstance(recieved, list)
    assert 4000 <= len(recieved) <= 4500


def test_search_group_ignore_stacked():
    scientist2.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist2.search_group
    assert isinstance(recieved, list)
    assert 4200 <= len(recieved) <= 4300


def test_search_group_affiliations_stacked():
    scientist3.define_search_group(stacked=True, refresh=refresh)
    recieved = scientist3.search_group
    assert isinstance(recieved, list)
    assert 15 <= len(recieved) <= 25


def test_find_matches():
    scientist1.find_matches(refresh=refresh)
    expected = [m.ID for m in MATCHES]
    assert scientist1.matches == expected


def test_find_matches_stacked():
    scientist1.find_matches(stacked=True, refresh=refresh)
    expected = [m.ID for m in MATCHES]
    assert scientist1.matches == expected


def test_find_matches_stacked_affiliations():
    scientist3.find_matches(stacked=True, refresh=refresh)
    expected = [m.ID for m in MATCHES]
    assert scientist3.matches == expected


def test_inform_matches():
    scientist1.inform_matches(refresh=refresh)
    recieved = scientist1.matches
    assert len(recieved) == len(MATCHES)
    assert isinstance(recieved, list)
    cols = ["ID", "name", "first_year", "num_coauthors", "num_publications",
            "affiliation_country", "num_cited_refs"]
    df_r = pd.DataFrame(recieved)
    df_r["num_cited_refs"] = df_r["num_cited_refs"].round(3)
    df_m = pd.DataFrame(MATCHES)
    df_m["num_cited_refs"] = df_m["num_cited_refs"].round(3)
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])

