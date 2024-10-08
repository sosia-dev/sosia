"""Module with functions for retrieving and processing author data."""

from string import Template

import pandas as pd
from tqdm import tqdm

from sosia.processing.extracting import extract_yearly_author_data
from sosia.processing.caching import insert_data, retrieve_authors, \
    retrieve_authors_from_sourceyear
from sosia.processing.querying import query_pubs_by_sourceyear, stacked_query
from sosia.utils import custom_print


def get_author_info(authors, conn, refresh=False, verbose=False):
    """Get author information from authors table and add missing information
    via Scopus Author Search API.

    Parameters
    ----------
    authors : list
       List of Scopus Author IDs to search.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    refresh : bool (optional, default=False)
        Whether to refresh scopus cached files if they exist, or not.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    data : DataFrame
        Data on the provided authors.
    """
    # Retrieve existing data from SQL cache
    authors = pd.DataFrame(authors, columns=["auth_id"], dtype="uint64")
    data, missing = retrieve_authors(authors, conn)
    # Query missing records and insert at the same time
    if missing:
        params = {"group": missing, "refresh": refresh, "joiner": ") OR AU-ID(",
                  "q_type": "author", "template": Template("AU-ID($fill)"),
                  "stacked": True, "verbose": verbose}
        if verbose:
            print("Pre-filtering...")
        res = stacked_query(**params)
        res = pd.DataFrame(res)
        insert_data(res, conn, table="authors")
        data, _ = retrieve_authors(authors, conn)
    return data


def get_author_yearly_data(group, conn, verbose=False):
    """Get author information from author_year table and add missing
    information via Scopus Search API.

    Parameters
    ----------
    group : list of str
        Scopus IDs of authors to be filtered.

    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    group : list of str
        Scopus IDs of authors passing the publication count requirements.
    """
    authors = pd.DataFrame({"auth_id": group})
    auth_data, missing = retrieve_authors(authors, conn, table="author_year")

    # Add to database
    if missing:
        text = f"Querying Scopus for information for {len(missing):,} " \
               "authors..."
        custom_print(text, verbose)
        to_add = []
        for auth_id in tqdm(missing, disable=not verbose):
            new = extract_yearly_author_data(auth_id)
            to_add.append(new)
        to_add = pd.concat(to_add)
        insert_data(to_add, conn, table="author_year")

    # Retrieve again
    auth_data, missing = retrieve_authors(authors, conn, table="author_year")
    return auth_data


def get_authors_from_sourceyear(df, conn, refresh=False, stacked=False,
                                verbose=False):
    """Get authors publishing in specified sourced in specified years.

    Handles retrieving data, and in case of missing data querying for it
    and inserting it into the SQL database.

    Parameters
    ----------
    df : DataFrame
        DataFrame of source-year-combinations to be searched for.

    conn : sqlite3 connection
        Standing connection to an SQLite3 database.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    stacked : bool (optional, default=False)
        Whether to use fewer queries that are not reusable, or to use modular
        queries of the form "SOURCE-ID(<SID>) AND PUBYEAR IS <YYYY>".

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    data : DataFrame
        DataFrame in format ("source_id", "year", "auids", "afid"), where
        entries correspond to an individual paper.
    """
    # Retrieve information in cache
    data, missing = retrieve_authors_from_sourceyear(df, conn, refresh=refresh)

    # Download and add missing data
    to_add = pd.DataFrame()
    empty = []
    for year in missing["year"].unique():
        subset = missing[missing["year"] == year]
        sources = subset["source_id"].unique()
        new = query_pubs_by_sourceyear(sources, year, refresh=refresh,
                                       stacked=stacked, verbose=verbose)
        no_info = set(sources) - set(new["source_id"].unique())
        empty.extend([(s, year) for s in no_info])
        to_add = pd.concat([to_add, new])

    # Format useful information
    if data.empty:
        data = to_add
    else:
        data = pd.concat([data, to_add])
    data = data[data["auids"] != ""]
    data["auids"] = data["auids"].str.replace(";", ",").str.split(",")

    # Insert new information and information on missing data
    if empty:
        sources, years = list(zip(*empty))
        d = {"source_id": sources, "year": years, "auids": [""]*len(sources),
             "afid": [""]*len(sources)}
        to_add = pd.concat([to_add, pd.DataFrame(d)])
    if not to_add.empty:
        to_add["auids"] = to_add["auids"].str.replace(";", ",").str.split(",")
        insert_data(to_add, conn, table="sources_afids")
    return data
