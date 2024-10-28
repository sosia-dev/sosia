"""Tests for class `Original`."""

import warnings
from collections import namedtuple

import pandas as pd

warnings.filterwarnings("ignore")

# Expected matches
fields = "ID name first_year num_coauthors num_publications num_citations "\
         "affiliation_country language num_cited_refs"
Match = namedtuple("Match", fields)
MATCHES = [
    Match(
        ID=37080157400,
        name='Buchanan, Sean',
        first_year=2011,
        num_coauthors=5,
        num_publications=6,
        num_citations=45,
        affiliation_country='Canada',
        language='eng',
        num_cited_refs=1),
    Match(
        ID=55567912500,
        name='Eling, Katrin',
        first_year=2013,
        num_coauthors=9,
        num_publications=8,
        num_citations=56,
        affiliation_country='Netherlands',
        language='eng',
        num_cited_refs=0)
]


def test_search_sources(original1, original2):
    for o in [original1, original2]:
        o.define_search_sources()
        search_sources = o.search_sources
        assert len(search_sources) == 206
        assert (20206, "Academy of Management Review") in search_sources
        assert (15143, "Regional Studies") in search_sources


def test_search_sources_change(original1):
    backup = original1.search_sources
    expected = [(14351, "Brain Research Reviews"),
                (18632, "Progress in Brain Research")]
    original1.search_sources, _ = zip(*expected)
    assert original1.search_sources == expected
    original1.search_sources = backup


def test_search_group(original1, refresh_interval):
    original1.define_search_group(chunk_size=2, refresh=refresh_interval)
    recieved = original1.search_group
    assert isinstance(recieved, list)
    assert 700 <= len(recieved) <= 800


def test_search_group_stacked(original1, refresh_interval):
    original1.define_search_group(chunk_size=2, stacked=True,
                                  refresh=refresh_interval)
    recieved = original1.search_group
    assert isinstance(recieved, list)
    assert 700 <= len(recieved) <= 800


def test_search_group_affiliations_stacked(original2, refresh_interval):
    original2.define_search_group(chunk_size=2, stacked=True,
                                  refresh=refresh_interval)
    recieved = original2.search_group
    assert isinstance(recieved, list)
    assert 2 <= len(recieved) <= 10


def test_find_matches(original1, refresh_interval):
    original1.find_matches(refresh=refresh_interval)
    expected = [m.ID for m in MATCHES]
    assert original1.matches == expected


def test_find_matches_affiliations(original2, refresh_interval):
    original2.find_matches(refresh=refresh_interval)
    expected = []
    assert original2.matches == expected


def test_inform_matches(original1, refresh_interval):
    original1.inform_matches(refresh=refresh_interval)
    recieved = original1.matches
    assert len(recieved) == len(MATCHES)
    assert isinstance(recieved, list)
    cols = ["ID", "name", "first_year", "num_coauthors", "num_publications",
            "affiliation_country", "num_cited_refs"]
    df_r = pd.DataFrame(recieved)
    df_r["num_cited_refs"] = df_r["num_cited_refs"].round(3)
    df_m = pd.DataFrame(MATCHES)
    df_m["num_cited_refs"] = df_m["num_cited_refs"].round(3)
    df_m["ID"] = df_m["ID"].astype("uint64")
    pd.testing.assert_frame_equal(df_r[cols], df_m[cols])

