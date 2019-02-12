from math import ceil, inf
from collections import defaultdict


def add_source_names(source_ids, names):
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    return set([(s_id, names.get(s_id)) for s_id in source_ids])


def build_dict(results, chunk):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
    d = defaultdict(lambda: {'first_year': inf, 'pubs': set(), 'coauth': set()})
    for pub in results:
        authors = set(pub.author_ids.split(';'))
        for focal in authors.intersection(chunk):
            d[focal]['coauth'].update(authors)
            d[focal]['coauth'].remove(focal)
            d[focal]['pubs'].add(pub.eid)
            first_year = min(d[focal]['first_year'], int(pub.coverDate[:4]))
            d[focal]['first_year'] = first_year
    return d


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
        margin = ceil(val*base)
        r = range(base-margin, base+margin+1)
    elif isinstance(val, int):
        r = range(base-val, base+val+1)
    else:
        raise Exception("Value must be either float or int.")
    return r


def print_progress(iteration, total, verbose=True, decimals=2, length=50):
    """Print terminal progress bar."""
    if not verbose:
        return None
    percent = round(100 * (iteration / float(total)), decimals)
    filled_len = int(length * iteration // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    print('\rProgress: |{}| {}% Complete'.format(bar, percent), end='\r')
    if iteration == total:
        print()


def raise_non_empty(val, obj):
    """Raise exception if provided value is empty,
    or not of the desired object type.
    """
    if not isinstance(val, obj) or len(val) == 0:
        obj_name = str(obj).replace("class ", "")
        obj_name = obj_name.translate(str.maketrans({c: "" for c in "(<>),'"}))
        label = " or ".join(obj_name.split())
        raise Exception("Value must be a non-empty {}.".format(label))


def run(op, *args):
    """Call a function passed by partial()."""
    return op(*args)
