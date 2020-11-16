import functools
from time import sleep
from urllib.error import HTTPError

from pybliometrics.scopus.exception import (Scopus400Error, Scopus500Error)
from sosia.processing.constants import QUERY_MAX_TRIES


class AttemptFailed(Exception):
    pass


def build_dict(results, chunk):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
    from math import inf
    from collections import defaultdict
    chunk = [int(au) for au in chunk]
    d = defaultdict(
        lambda: {"first_year": inf, "pubs": set(), "coauth": set(),
                 "n_coauth": inf, "n_pubs": inf})
    for pub in results:
        if not pub.author_ids:
            continue
        authors = set([int(au) for au in pub.author_ids.split(";")])
        for focal in authors.intersection(chunk):
            d[focal]["coauth"].update(authors)
            d[focal]["coauth"].remove(focal)
            d[focal]["pubs"].add(pub.eid)
            d[focal]["n_pubs"] = len(d[focal]["pubs"])
            d[focal]["n_coauth"] = len(d[focal]["coauth"])
            if not pub.coverDate:
                continue
            first_year = min(d[focal]["first_year"], int(pub.coverDate[:4]))
            d[focal]["first_year"] = first_year
    return d


def expand_affiliation(df):
    """Auxiliary function to expand the information about the affiliation
    in publications from ScopusSearch.
    """
    from pandas import Series
    res = df[["source_id", "author_ids", "afid"]].copy()
    res['afid'] = res["afid"].str.split(';')
    res = (res["afid"].apply(Series)
              .merge(res, right_index=True, left_index=True)
              .drop(["afid"], axis=1)
              .melt(id_vars=['source_id', 'author_ids'], value_name="afid")
              .drop("variable", axis=1)
              .dropna())
    res['afid'] = res['afid'].astype(float)
    return res


def flat_set_from_df(df, col, condition=None):
    """Flatten Series from DataFrame which contains lists and
    return as set, optionally after filtering the DataFrame.
    """
    if condition is not None:
        df = df[condition]
    lists = df[col].tolist()
    return set([item for sublist in lists for item in sublist])


def handle_scopus_errors(func):
    """ A decorator to handle errors returned by scopus """
    @functools.wraps(func)
    def try_query(*args, **kwargs):
        tries = 1
        while tries <= QUERY_MAX_TRIES:
            try:
                return func(*args, **kwargs)
            except (Scopus500Error, KeyError, HTTPError):
                # exception of all errors here has to be maintained due to the
                # occurrence of unreplicable errors (e.g. 'cursor', HTTPError)
                sleep(2.0)
                tries += 1
                continue
            except AttributeError:
                # try refreshing, or dropping "source_id" integrity if present
                args = (args[0], args[1], True)
                try:
                    return func(*args, **kwargs)
                except AttributeError:
                    if "source_id" in kwargs["fields"]:
                        kwargs["fields"].remove("source_id")
        text = f"Max number of query attempts reached: {QUERY_MAX_TRIES}.\n"\
               "Verify your connection and settings or wait for the Scopus"\
               "server to return responsive."
        raise AttemptFailed(text)
    return try_query


def robust_join(s, sep=','):
    """Join an iterable converting each element to str first."""
    return sep.join([str(e) for e in s])


def margin_range(base, val):
    """Create a range of margins around a base value.

    Parameters
    ----------
    base : int
        The value around which a margin should be created.

    val : int or float
        The margin size.  If float, val will be interpreted as percentage.

    Returns
    -------
    r : range
        A range object representing the margin range.
    """
    from math import ceil
    if isinstance(val, float):
        margin = ceil(val * base)
        r = range(base - margin, base + margin + 1)
    elif isinstance(val, int):
        r = range(base - val, base + val + 1)
    else:
        raise Exception("Value must be either float or int.")
    return r
