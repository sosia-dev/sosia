from math import ceil, inf
from collections import Counter, defaultdict

from pandas import read_csv

from sosia.utils.constants import ASJC_2D, FIELDS_SOURCES_LIST,\
    SOURCES_NAMES_LIST
from sosia.utils.startup import create_fields_sources_list


def add_source_names(source_ids, names):
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    return sorted([(s_id, names.get(int(s_id))) for s_id in set(source_ids)])


def build_dict(results, chunk):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
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


def custom_print(text, verbose):
    """Print text if verbose."""
    if verbose:
        print(text)


def flat_set_from_df(df, col, condition=None):
    """Flatten Series from DataFrame which contains lists and
    return as set, optionally after filtering the DataFrame.
    """
    if condition is not None:
        df = df[condition]
    lists = df[col].tolist()
    return set([item for l in lists for item in l])


def get_main_field(fields):
    """Get main 4-digit ASJC field (code) and main 2-digit ASJC field (name).


    Parameters
    ----------
    fields : iterable of int
        Lists of fields the researcher is active in.

    Returns
    -------
    t : tuple
        A 2-element tuple where the first element is the most common 4-digit
        ASJC field and the second element the short name of the most common
        2-digit ASJC field.

    Note
    ----
    We exclude multidisciplinary and give preference to non-general fields.
    """
    # 4 digit field
    c = Counter(fields)
    try:
        c.pop(1000)  # Exclude Multidisciplinary
    except KeyError:
        pass
    top_fields = [f for f, val in c.items() if val == max(c.values())]
    if len(top_fields) == 1:
        main_4 = top_fields[0]
    else:
        non_general_fields = [f for f in top_fields if f % 1000 != 0]
        if non_general_fields:
            main_4 = non_general_fields[0]
        else:
            main_4 = top_fields[0]
    # 2 digit field
    c = Counter([str(f)[:2] for f in fields])
    try:
        c.pop(10)  # Exclude Multidisciplinary
    except KeyError:
        pass
    main_2 = int(c.most_common(1)[0][0])
    return (main_4, ASJC_2D[main_2])


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
        raise Exception("Value must be either float or int.")
    return r


def maybe_add_source_names(source_ids, names):
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    if isinstance(source_ids[0], tuple):
        return source_ids
    else:
        return add_source_names(source_ids, names)


def print_progress(iteration, total, verbose=True, length=50):
    """Print terminal progress bar."""
    if not verbose:
        return None
    percent = 100 * (iteration / float(total))
    filled_len = int(length * iteration // total)
    bar = "█" * filled_len + "-" * (length - filled_len)
    print("\rProgress: |{}| {:.2f}% Complete".format(bar, percent), end="\r")
    if iteration == total:
        print()


def read_fields_sources_list():
    """Auxiliary function to read FIELDS_SOURCES_LIST and create it before,
    if necessary.
    """
    try:
        sources = read_csv(FIELDS_SOURCES_LIST)
        names = read_csv(SOURCES_NAMES_LIST)
    except FileNotFoundError:
        create_fields_sources_list()
        sources = read_csv(FIELDS_SOURCES_LIST)
        names = read_csv(SOURCES_NAMES_LIST)
    return sources, names


def run(op, *args):
    """Call a function passed by partial()."""
    return op(*args)


def _get_obj_name(obj):
    """Auxiliary function to retrieve the name of an object."""
    name = str(obj).replace("class ", "")
    return name.translate(str.maketrans({c: "" for c in "(<>),'"}))
