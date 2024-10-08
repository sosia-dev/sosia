"""Tests for processing.extracting module."""

import pandas as pd
from pybliometrics.scopus import ScopusSearch

from sosia.processing import extract_yearly_author_data, \
    find_main_affiliation, get_main_field, parse_docs

test_id = 6701809842


def test_extract_yearly_author_data():
    received = extract_yearly_author_data(test_id)
    assert isinstance(received, pd.DataFrame)
    assert received.shape[0] > 20
    assert received["year"].nunique() == received.shape[0]
    expected_cols = ['auth_id', 'year', 'first_year', 'n_pubs', 'n_coauth']
    assert list(received.columns) == expected_cols


def test_find_main_affiliation(refresh_interval):
    pubs = ScopusSearch(f"AU-ID({test_id})", refresh=refresh_interval).results
    aff_id = find_main_affiliation([test_id], pubs, 2000)
    assert aff_id == "60028717"


def test_get_main_field():
    fields = [1000, 1000, 2000, 2000, 2020, 2020]
    received = get_main_field(fields)
    expected = (2020, "ECON")
    assert received == expected


def test_parse_docs(refresh_interval):
    eids = ["2-s2.0-84866317084"]
    received = parse_docs(eids, refresh=refresh_interval)
    expected_refs = set(['67650248718', '57849112238', '51249091642',
        '70449099678', '84865231386', '8744256776', '0004256525', '0035654590',
        '84866333650', '78650692566', '0002969912', '0007622058', '0000169440',
        '0003685848', '43049125937', '43149086011', '4243112264', '0942299814',
        '27744606594', '2442709303', '84866309814', '0033675552', '0034424078',
        '0029824384', '34548317343', '3142544611', '84981198417', '0003457562',
        '0032394091', '0001116544', '84866324358', '23944478214', '0039484749',
        '0001275239', '34249696486', '70449641263', '0035654659', '0041099301',
        '0027767147',  '40749109418', '15944370019','2442654430', '0004164119',
        '35348862941', '0030559826', '34547860480', '77953702055', 
        '18144372897', '0004062815', '84972591424', '34248571923',
        '29144486677', '84866332328', '39149084479', '29144517611', 
        '85015576166', '33645383647', '84981213068', '84920182751',
        '23044470851', '78649697033', '55049124635', '33845620645',
        '30444461409', '0034435025', '47949124687',  '84887864855',
        '84866332329', '84984932935', '0034423919', '0141625872'])
    assert sorted(received[0]) == sorted(expected_refs)
