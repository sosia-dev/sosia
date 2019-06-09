from os.path import expanduser

URL_CONTENT = "https://www.elsevier.com/solutions/scopus/how-scopus-works/content"
URL_SOURCES = "https://elsevier.com/?a=734751"

CACHE_SQLITE = expanduser("~/.sosia/") + "cache_sqlite.sqlite"
FIELDS_SOURCES_LIST = expanduser("~/.sosia/") + "field_sources_list.csv"
SOURCES_NAMES_LIST = expanduser("~/.sosia/") + "sources_names.csv"

ASJC_2D = {10: "MULT", 11: "AGRI", 12: "ARTS", 13: "BIOC", 14: "BUSI",
           15: "CENG", 16: "CHEM", 17: "COMP", 18: "DECI", 19: "EART",
           20: "ECON", 21: "ENER", 22: "ENGI", 23: "ENVI", 24: "IMMU",
           25: "MATE", 26: "MATH", 27: "MEDI", 28: "NEUR", 29: "NURS",
           30: "PHAR", 31: "PHYS", 32: "PSYC", 33: "SOCI", 34: "VETE",
           35: "DENT", 36: "HEAL"}
