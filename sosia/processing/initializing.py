from sosia.establishing.constants import FIELDS_SOURCES_LIST, SOURCES_NAMES_LIST
from sosia.establishing.fields_sources import create_fields_sources_list


def add_source_names(source_ids, names):
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    return sorted([(s_id, names.get(int(s_id))) for s_id in set(source_ids)])


def maybe_add_source_names(source_ids, names):
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    if isinstance(source_ids[0], tuple):
        return source_ids
    else:
        return add_source_names(source_ids, names)


def read_fields_sources_list():
    """Auxiliary function to read FIELDS_SOURCES_LIST and create it before,
    if necessary.
    """
    from pandas import read_csv
    try:
        sources = read_csv(FIELDS_SOURCES_LIST)
        names = read_csv(SOURCES_NAMES_LIST)
    except FileNotFoundError:
        create_fields_sources_list()
        sources = read_csv(FIELDS_SOURCES_LIST)
        names = read_csv(SOURCES_NAMES_LIST)
    return sources, names
