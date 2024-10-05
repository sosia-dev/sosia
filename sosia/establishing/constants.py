"""Module of constants used to establish the connection to the data."""

from pathlib import Path

DATA_REPO_URL = "https://raw.githubusercontent.com/sosia-dev/sosia-data/"
_cache_folder = Path.home()/".cache/sosia/"
FIELD_SOURCE_MAP = _cache_folder / "field_sources_list.csv"
SOURCE_INFO = _cache_folder / "source_info.csv"
DEFAULT_DATABASE = _cache_folder/'main.sqlite'

DB_TABLES = {
    "author_ncits":
        {"columns": (("auth_id", "INTEGER"), ("year", "INTEGER"), ("n_cits", "INTEGER")),
         "primary": ("auth_id", "year")},
    "author_pubs":
        {"columns": (("auth_id", "INTEGER"), ("year", "INTEGER"), ("n_pubs", "INTEGER")),
         "primary": ("auth_id", "year")},
    "author_year":
        {"columns": (("auth_id", "INTEGER"), ("year", "INTEGER"), ("first_year", "INTEGER"),
                     ("n_pubs", "INTEGER"), ("n_coauth", "INTEGER")),
         "primary": ("auth_id", "year")},
    "authors":
        {"columns": (("auth_id", "INTEGER"), ("eid", "text"), ("surname", "text"),
                     ("initials", "text"), ("givenname", "text"),
                     ("affiliation", "text"), ("documents", "text"),
                     ("affiliation_id", "text"), ("city", "text"),
                     ("country", "text"), ("areas", "text")),
         "primary": ("auth_id",)},
    "sources_afids":
        {"columns": (("source_id", "INTEGER"), ("year", "INTEGER"), ("afid", "INTEGER"),
                     ("auids", "text")),
         "primary": ("source_id", "year", "afid")}}
