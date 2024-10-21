"""Module with functions related to initializing the sosia processing."""

from typing import Optional, Union

from pandas import read_csv

from sosia.establishing.constants import FIELD_SOURCE_MAP, SOURCE_INFO
from sosia.establishing.fields_sources import get_field_source_information


def add_source_names(
        source_ids: list[Union[str, int, tuple]],
        names: dict
) -> list[tuple[Union[str, int, tuple], Optional[str]]]:
    """Add names of sources to list of source IDs turning the list into a
    list of tuples.
    """
    if isinstance(source_ids[0], tuple):
        return source_ids
    else:
        return [(s_id, names.get(int(s_id))) for s_id in sorted(set(source_ids))]


def read_fields_sources_list():
    """Auxiliary function to read FIELD_SOURCE_MAP and create it before,
    if necessary.
    """
    try:
        field = read_csv(FIELD_SOURCE_MAP)
        info = read_csv(SOURCE_INFO)
    except FileNotFoundError:
        get_field_source_information()
        field = read_csv(FIELD_SOURCE_MAP)
        info = read_csv(SOURCE_INFO)
    return field, info
