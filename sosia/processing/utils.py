"""Module with utility functions for processing data in sosia."""

from itertools import islice
from math import ceil
from typing import Union


def chunk_list(data: list, size: int) -> list[list]:
    """Chunk a list into bins of a given size and merge the last if necessary."""
    data_iter = iter(data)
    chunks = list(iter(lambda: list(islice(data_iter, size)), []))

    # Merge last chunk into previous if smaller than half the chunk size
    if len(chunks[-1]) <= size // 2 and len(chunks) > 1:
        chunks[-2].extend(chunks.pop())

    return chunks


def compute_overlap(left, right):
    """Compute overlap of two sets in a robust way."""
    if not left and not right:
        return None
    return len(left.intersection(right))


def flat_set_from_df(df, col):
    """Flatten Series from DataFrame which contains lists and
    return as set, optionally after filtering the DataFrame.
    """
    lists = df[col].tolist()
    return set([item for sublist in lists for item in sublist])


def generate_filter_message(number: int, condition: range, label: str):
    """Generate filter progress message."""
    if number == 1:
        plural = ""
    else:
        plural = "s"
    if len(condition) == 1:
        qualifier = "same"
        if "year" in label:
            suffix = condition[0]
        else:
            suffix = f"{condition[0]:,}"
    else:
        qualifier = "similar"
        if "year" in label:
            suffix = f"{min(condition)} to {max(condition)}"
        else:
            suffix = f"{min(condition):,} to {max(condition):,}"
    text = (f"... left with {number:,} candidate{plural} with "
            f"{qualifier} {label} ({suffix})")
    return text


def margin_range(base: int, val: Union[float, int]):
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
        r = range(max(base - margin, 0), base + margin + 1)
    elif isinstance(val, int):
        r = range(max(base - val, 0), base + val + 1)
    else:
        raise TypeError("Value must be either float or int.")
    return r
