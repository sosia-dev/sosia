from pathlib import Path

DATA_REPO_URL = "https://raw.githubusercontent.com/sosia-dev/sosia-data/"
_cache_folder = Path.home()/".cache/sosia/"
FIELD_SOURCE_MAP = _cache_folder / "field_sources_list.csv"
SOURCE_INFO = _cache_folder / "source_info.csv"
DEFAULT_DATABASE = _cache_folder/'main.sqlite'

DB_TABLES = {
    "author_ncits":
        {"columns": (("auth_id", "int"), ("year", "int"), ("n_cits", "int")),
         "primary": ("auth_id", "year")},
    "author_pubs":
        {"columns": (("auth_id", "int"), ("year", "int"), ("n_pubs", "int")),
         "primary": ("auth_id", "year")},
    "author_year":
        {"columns": (("auth_id", "int"), ("year", "int"), ("first_year", "int"),
                     ("n_pubs", "int"), ("n_coauth", "int")),
         "primary": ("auth_id", "year")},
    "authors":
        {"columns": (("auth_id", "int"), ("eid", "text"), ("surname", "text"),
                     ("initials", "text"), ("givenname", "text"),
                     ("affiliation", "text"), ("documents", "text"),
                     ("affiliation_id", "text"), ("city", "text"),
                     ("country", "text"), ("areas", "text")),
         "primary": ("auth_id",)},
    "sources":
        {"columns": (("source_id", "int"), ("year", "int"), ("auids", "text")),
         "primary": ("source_id", "year")},
    "sources_afids":
        {"columns": (("source_id", "int"), ("year", "int"), ("afid", "int"),
                     ("auids", "text")),
         "primary": ("source_id", "year", "afid")}}
