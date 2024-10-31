"""Shared pytest fixtures and configurations for the test suite."""

import pytest
from pathlib import Path

from pybliometrics.scopus import init
from sosia.classes import Original, Scientist
from sosia.establishing import connect_database, make_database

init()


@pytest.fixture(scope="session")
def test_cache():
    test_cache = Path.home() / ".cache" / "sosia" / "test.sqlite"
    test_cache.unlink(missing_ok=True)
    make_database(test_cache)
    return test_cache


@pytest.fixture
def test_conn(test_cache):
    conn = connect_database(test_cache, verbose=False)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def refresh_interval():
    return 30


@pytest.fixture(scope="session")
def scientist1(test_cache, refresh_interval):
    return Scientist([6701809842], 2001, refresh=refresh_interval,
                     db_path=test_cache)


@pytest.fixture(scope="session")
def scientist2(test_cache, refresh_interval):
    return Scientist([55208373700, 55208373700], 2017,
                     refresh=refresh_interval, db_path=test_cache)


@pytest.fixture(scope="session")
def scientist3(test_cache, refresh_interval):
    eids = ["2-s2.0-84959420483", "2-s2.0-84949113230"]
    return Scientist([55208373700], 2017, eids=eids,
                     refresh=refresh_interval, db_path=test_cache)


@pytest.fixture(scope="session")
def scientist4(test_cache, refresh_interval):
    return Scientist([55208373700], 2015, refresh=refresh_interval,
                     db_path=test_cache)


@pytest.fixture(scope="session")
def original1(test_cache, refresh_interval):
    return Original(55208373700, 2018, db_path=test_cache,
                    refresh=refresh_interval, cits_margin=0.15, same_discipline=True,
                    first_year_margin=1, pub_margin=0.2, coauth_margin=0.2)
