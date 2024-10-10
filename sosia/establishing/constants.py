"""Module of constants used to establish the connection to the data."""

from pathlib import Path

DATA_REPO_URL = "https://raw.githubusercontent.com/sosia-dev/sosia-data/"
_cache_folder = Path.home() / ".cache" / "sosia/"
FIELD_SOURCE_MAP = _cache_folder / "field_sources_list.csv"
SOURCE_INFO = _cache_folder / "source_info.csv"
DEFAULT_DATABASE = _cache_folder / 'main.sqlite'

DB_TABLES = {
    "author_citations":
        {"columns": (("auth_id", "INTEGER"), ("year", "INTEGER"),
                     ("n_cits", "INTEGER")),
         "primary": ("auth_id", "year")},
    "author_data":
        {"columns": (("auth_id", "INTEGER"), ("year", "INTEGER"),
                     ("first_year", "INTEGER"), ("n_pubs", "INTEGER"),
                     ("n_coauth", "INTEGER")),
         "primary": ("auth_id", "year")},
    "author_info":
        {"columns": (("auth_id", "INTEGER"), ("surname", "TEXT"),
                     ("givenname", "TEXT"), ("documents", "INTEGER"),
                     ("areas", "TEXT")),
         "primary": ("auth_id",)},
    "sources_afids":
        {"columns": (("source_id", "INTEGER"), ("year", "INTEGER"),
                     ("afid", "INTEGER"), ("auids", "TEXT")),
         "primary": ("source_id", "year", "afid")}}
