from os import makedirs
from os.path import exists, expanduser

import pandas as pd

from sosia.establishing.constants import FIELDS_SOURCES_LIST, SOURCES_NAMES_LIST,\
    URL_CONTENT, URL_SOURCES


def create_fields_sources_list():
    """Download Scopus files with information on covered sources and create
    one list of all sources with ids and one with field information.
    """
    # Set up
    path = expanduser("~/.sosia/")
    if not exists(path):
        makedirs(path)
    rename = {
        "All Science Journal Classification Codes (ASJC)": "asjc",
        "Scopus ASJC Code (Sub-subject Area)": "asjc",
        "ASJC code": "asjc",
        "Source Type": "type",
        "Type": "type",
        "Sourcerecord id": "source_id",
        "Scopus Source ID": "source_id",
        "Scopus SourceID": "source_id",
        "Title": "title",
        "Source title": "title",
    }
    keeps = list(set(rename.values()))

    # Get Information from Scopus Sources list
    sources = pd.read_excel(URL_SOURCES, sheet_name=None, header=1)
    _drop_sheets(sources, ["About CiteScore", "ASJC Codes", "Sheet1"])
    dfs = [df.rename(columns=rename)[keeps].dropna() for df in sources.values()]
    out = pd.concat(dfs).drop_duplicates()

    # Add information from list of external publication titles
    external = pd.read_excel(_get_source_title_url(), sheet_name=None)
    _drop_sheets(external, ["More info Medline", "ASJC classification codes"])

    for df in external.values():
        _update_dict(rename, df.columns, "source title", "title")
        if "Source Type" not in df.columns:
            df["type"] = "conference proceedings"
        subset = df.rename(columns=rename)[keeps].dropna()
        subset["asjc"] = subset["asjc"].astype(str).apply(_clean).str.split()
        subset = (subset.set_index(["source_id", "title", "type"])
                        .asjc.apply(pd.Series)
                        .stack()
                        .rename("asjc")
                        .reset_index()
                        .drop("level_3", axis=1))
        out = pd.concat([out, subset], sort=True)

    # Write list of names
    order = ["source_id", "title"]
    names = out[order].drop_duplicates().sort_values("source_id")
    names.to_csv(SOURCES_NAMES_LIST, index=False)

    # Write list of fields by source
    out["type"] = out["type"].str.lower().str.strip()
    out.drop("title", axis=1).to_csv(FIELDS_SOURCES_LIST, index=False)


def _clean(x):
    """Auxiliary function to clean a string Series."""
    return x.replace(";", " ").replace(",", " ").replace("  ", " ").strip()


def _drop_sheets(sheets, drops):
    """Auxiliary function to drop sheets from an Excel DataFrame."""
    for drop in drops:
        try:
            sheets.pop(drop)
        except KeyError:
            continue


def _get_source_title_url():
    """Extract the link to the most recent Scopus sources list."""
    import requests
    from bs4 import BeautifulSoup
    resp = requests.get(URL_CONTENT)
    soup = BeautifulSoup(resp.text, "lxml")
    try:
        return soup.find("a", {"title": "source list"})["href"]
    except AttributeError:
        raise ValueError("Link to sources list not found.")


def _update_dict(d, lst, key, replacement):
    """Auxiliary function to add keys to a dictionary if a given string is
    included in the key.
    """
    for c in lst:
        if c.lower().startswith(key):
            d[c] = replacement
