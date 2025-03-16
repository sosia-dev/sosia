"""Module with functions for retrieving and processing author data."""

from string import Template

import pandas as pd
from tqdm import tqdm

from sosia.processing.constants import QUERY_MAX_LEN
from sosia.processing.extracting import extract_yearly_author_data
from sosia.processing.caching import insert_data, retrieve_from_author_table, \
    retrieve_authors_from_sourceyear
from sosia.processing.querying import base_query, count_citations, \
    create_queries, query_pubs_by_sourceyear
from sosia.utils import custom_print, get_ending


def get_author_info(authors, conn, verbose=False, refresh=False) -> pd.DataFrame:
    """Get author information from author_info table and add missing
    information via Author Search API.

    Parameters
    ----------
    authors : list
       List of Scopus Author IDs to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    refresh : bool, int (optional, default=False)
        How to handle existing information in database and on disk.  If True,
        or int is passed, will replace all matching information in database
        with information on disk.  If int is passed, information on disk
        will be refreshed if older than int days.  If True, will refresh
        information on disk in any case.

    Returns
    -------
    info : DataFrame
        DataFrame with general information on requested authors.
    """
    # Retrieve information from SQL database
    authors = pd.DataFrame(authors, columns=["auth_id"], dtype="uint64")
    info, missing = retrieve_from_author_table(authors, conn,
        table="author_info", refresh=refresh)

    # Query missing records and insert at the same time
    if missing:
        total = len(missing)
        ending = get_ending(total)
        text = f"Downloading information for {total:,} candidate{ending}..."
        custom_print(text, verbose)
        template = Template("AU-ID($fill)")
        queries = create_queries(missing, joiner=") OR AU-ID(",
                                 template=template, maxlen=QUERY_MAX_LEN)
        with tqdm(total=total, disable=not verbose) as pbar:
            for query, group in queries:
                res = base_query("author", query, refresh=refresh)
                pbar.update(len(group))
                if not res:  # Likely author IDs do not exist anymore
                    continue
                res = pd.DataFrame(res)
                res = res.drop_duplicates(subset="eid")
                res["auth_id"] = res['eid'].str.split('-').str[-1].astype("int64")
                res = res[info.columns]
                insert_data(res, conn, table="author_info")
                info = pd.concat([info, res])
    return info


def get_author_data(group, conn, verbose=False, refresh=False, batch_size=100) -> pd.DataFrame:
    """Get author information from author_data table and add missing
    information via Scopus Search API.

    Parameters
    ----------
    group : list of str
        Scopus IDs of authors to be filtered.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    refresh : bool, int (optional, default=False)
        How to handle existing information in database and on disk.  If True,
        or int is passed, will replace all matching information in database
        with information on disk.  If int is passed, information on disk
        will be refreshed if older than int days.  If True, will refresh
        information on disk in any case.

    batch_size : int (optional, default=100)
        Number of authors to store at once.  Will balance SQL database overhead
        from insertion and risk of losing data in case of an error.

    Returns
    -------
    data : DataFrame
        DataFrame with yearly information on requested authors.
    """
    # Retrieve information from SQL database
    authors = pd.DataFrame({"auth_id": group})
    data, missing = retrieve_from_author_table(authors, conn,
        table="author_data", refresh=refresh)

    # Add to database
    if missing:
        total = len(missing)
        ending = get_ending(total)
        text = f"Querying Scopus for information for {total:,} author{ending}..."
        custom_print(text, verbose)
        to_add = []
        for i, auth_id in tqdm(enumerate(missing, start=1),
                               disable=not verbose, total=total):
            try:
                new = extract_yearly_author_data(auth_id, refresh=refresh)
                to_add.append(new)
            except KeyError:
                continue
            if i % batch_size == 0 or i == total:
                to_add_df = pd.concat(to_add)
                insert_data(to_add_df, conn, table="author_data")
                data = pd.concat([data, to_add_df])
                to_add = []
    return data


def get_authors_from_sourceyear(df, conn, refresh=False, *args, **kwargs):
    """Get authors publishing in specified sourced in specified years.

    Handles retrieving data, and in case of missing data querying for it
    and inserting it into the SQL database.

    Parameters
    ----------
    df : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to an SQLite3 database.

    refresh : bool, int (optional, default=False)
        How to handle existing information in database and on disk.  If True,
        or int is passed, will replace all matching information in database
        with information on disk.  If int is passed, information on disk
        will be refreshed if older than int days.  If True, will refresh
        information on disk in any case.

    *args, **kwargs : tuple or dict (optional)
        Additional options passed on to `query_pubs_by_sourceyear()`:
        `verbose`, and `stacked`.

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids"), where
        auids is a string of author IDs joined on semicolon.
    """
    # Retrieve information from SQL database
    drop = refresh is not False  # becomes True for all values unless False
    data, missing = retrieve_authors_from_sourceyear(df, conn, drop=drop)

    # Download and add missing data
    to_add = pd.DataFrame()
    empty = []
    for year in missing["year"].unique():
        subset = missing[missing["year"] == year]
        sources = subset["source_id"].unique()
        new = query_pubs_by_sourceyear(sources, year, refresh=refresh,
                                       *args, **kwargs)
        no_info = set(sources) - set(new["source_id"].unique())
        assert new["source_id"].nunique() + len(no_info) == len(sources)
        empty.extend([(s, year) for s in no_info])
        to_add = pd.concat([to_add, new])

    # Insert new information and information on missing data
    if empty:
        sources, years = list(zip(*empty))
        d = {"source_id": sources, "year": years, "auids": [""] * len(sources)}
        to_add = pd.concat([to_add, pd.DataFrame(d)])
    if not to_add.empty:
        insert_data(to_add, conn, table="sources")

    # Return data
    data = pd.concat([data, to_add])
    data = data[data["auids"] != ""]
    data["auids"] = data["auids"].str.split(";")
    return data


def get_citations(authors, year, conn, verbose=False, refresh=False):
    """Get citations net of self-citations in particular `year` for
    a group of `authors`.

    Parameters
    ----------
    authors : list
       List of Scopus Author IDs for whom to return citation information.

    year : int
        The year in which citations must be counted.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    refresh : bool, int (optional, default=False)
        Whether to refresh cached results (if they exist) or not, with
        Scopus data that is at most `refresh` days old (True = 0).

    Returns
    -------
    citations : DataFrame
        Data on the provided authors.
    """
    df = pd.DataFrame({"auth_id": authors, "year": year})
    citations, missing = retrieve_from_author_table(df, conn,
        table="author_citations", refresh=refresh)
    # Add citations
    if missing:
        text = f"Counting citations of {len(missing):,} candidates..."
        custom_print(text, verbose)
        to_add = []
        for auth_id in tqdm(missing, disable=not verbose):
            n_cits = count_citations([auth_id], year + 1)
            to_add.append(n_cits)
        to_add = pd.DataFrame({"auth_id": missing, "year": year, "n_cits": to_add})
        insert_data(to_add, conn, table="author_citations")
        citations = pd.concat([citations, to_add])
    # Filter on year
    citations = citations[citations["year"] == year].drop(columns="year")
    return citations.astype("uint64")
