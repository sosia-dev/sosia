from math import ceil


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


def print_progress(iteration, total, decimals=2, length=50):
    """Print terminal progress bar."""
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
        obj_name = str(obj).split("'")[1]
        raise Exception("Value must be a non-empty {}.".format(obj_name))


def run(op, *args):
    """Call a function passed by partial()."""
    return op(*args)
