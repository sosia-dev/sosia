from sosia.establishing.constants import FIELD_SOURCE_MAP, SOURCE_INFO
from sosia.establishing.fields_sources import get_field_source_information


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
    """Auxiliary function to read FIELD_SOURCE_MAP and create it before,
    if necessary.
    """
    from pandas import read_csv
    try:
        field = read_csv(FIELD_SOURCE_MAP)
        info = read_csv(SOURCE_INFO)
    except FileNotFoundError:
        get_field_source_information()
        field = read_csv(FIELD_SOURCE_MAP)
        info = read_csv(SOURCE_INFO)
    return field, info
