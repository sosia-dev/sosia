"""Tests for processing.extracting module."""

import pandas as pd
from pybliometrics.scopus import ScopusSearch

from sosia.processing import extract_yearly_author_data, \
    find_main_affiliation, determine_main_field, parse_docs

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


def test_determine_main_field():
    fields = [1000, 1000, 2000, 2000, 2020, 2020]
    received = determine_main_field(fields)
    expected = (2020, "ECON")
    assert received == expected


def test_parse_docs(refresh_interval):
    eids = ["2-s2.0-84866317084"]
    received = parse_docs(eids, refresh=refresh_interval)
    expected_refs = {'0000169440', '0001116544', '0001275239', '0002969912',
        '0003457562', '0003685848', '0004062815', '0004164119', '0004256525',
        '0004561494',  '0007622058', '0027767147', '0029824384', '0030559826',
        '0032394091', '0033675552', '0034423919', '0034424078', '0034435025',
        '0035654590', '0035654659', '0039484749', '0041099301', '0141625872',
        '0942299814', '15944370019', '18144372897', '23044470851', '23944478214',
        '2442709303', '27744606594', '29144486677','29144517611', '30444461409',
        '3142544611', '33645383647', '33845620645', '34248571923', '34249696486',
        '34547860480', '34548317343', '35348862941', '39149084479',
        '40749109418', '4243112264', '43049125937', '43149086011',
        '47949124687', '51249091642', '55049124635', '57849112238',
        '67650248718', '70449099678', '70449641263', '77953702055',
        '78649697033','78650692566', '84865231386', '84866309814',
        '84866332329', '84866333650', '84887864855', '84920182751',
        '84972591424', '84981198417', '84981213068', '84984932935',
        '85015576166', '85204467065', '85204471326', '8744256776'}
    assert sorted(received[0]) == sorted(expected_refs)
