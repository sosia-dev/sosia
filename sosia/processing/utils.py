"""Module with utility functions for processing data in sosia."""

from math import ceil


def compute_overlap(left, right):
    """Compute overlap of two sets in a robust way."""
    if not left and not right:
        return None
    return len(left.intersection(right))


def expand_affiliation(df):
    """Auxiliary function to expand the information about the affiliation
    in publications from ScopusSearch.
    """
    temp = df.set_index(["source_id", "author_ids"])[["afid"]]
    temp = (temp["afid"].str.split(";", expand=True)
                .stack().dropna().reset_index()
                .drop("level_2", axis=1)
                .rename(columns={0: "afid"}))
    temp['afid'] = temp['afid'].astype(float)
    return temp


def flat_set_from_df(df, col):
    """Flatten Series from DataFrame which contains lists and
    return as set, optionally after filtering the DataFrame.
    """
    lists = df[col].tolist()
    return set([item for sublist in lists for item in sublist])


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
    if isinstance(val, float):
        margin = ceil(val * base)
        r = range(base - margin, base + margin + 1)
    elif isinstance(val, int):
        r = range(base - val, base + val + 1)
    else:
        raise TypeError("Value must be either float or int.")
    return r
