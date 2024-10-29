"""Module with super class to represent a `Scientist`."""

from pathlib import Path
from typing import Optional, Union
from warnings import warn

from typing_extensions import Self

from pybliometrics.scopus import AbstractRetrieval, AffiliationRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from sosia.establishing import connect_database, DEFAULT_DATABASE
from sosia.processing import add_source_names, base_query, count_citations, \
    extract_authors, find_main_affiliation, get_author_info, determine_main_field, \
    read_fields_sources_list
from sosia.utils import accepts


class Scientist(object):
    """Class to represent a scientist.
    """
    @property
    def affiliation_country(self) -> Optional[str]:
        """The country of the scientist's affiliation."""
        return self._affiliation_country

    @affiliation_country.setter
    @accepts(str)
    def affiliation_country(self, val: str) -> None:
        self._affiliation_country = val

    @property
    def affiliation_id(self) -> Optional[str]:
        """The affiliation ID (as string) of the scientist's most frequent
        affiliation in the active year.
        """
        return self._affiliation_id

    @affiliation_id.setter
    @accepts(str)
    def affiliation_id(self, val: str) -> None:
        self._affiliation_id = val

    @property
    def affiliation_name(self) -> Optional[str]:
        """The name of the scientist's affiliation."""
        return self._affiliation_name

    @affiliation_name.setter
    @accepts(str)
    def affiliation_name(self, val: str) -> None:
        self._affiliation_name = val

    @property
    def affiliation_type(self) -> Optional[str]:
        """The type of the scientist's affiliation."""
        return self._affiliation_type

    @affiliation_type.setter
    @accepts(str)
    def affiliation_type(self, val: str) -> None:
        self.affiliation_type = val

    @property
    def citations(self) -> Optional[int]:
        """The citation count of the scientist until the provided year."""
        return self._citations

    @citations.setter
    @accepts(int)
    def citations(self, val: int) -> None:
        self._citations = val

    @property
    def coauthors(self) -> list:
        """Sorted list of coauthors of the scientist on all publications
        until the comparison year.
        """
        return self._coauthors

    @coauthors.setter
    @accepts((set, list, tuple))
    def coauthors(self, val: list) -> None:
        self._coauthors = sorted(val)

    @property
    def fields(self) -> Union[set, list, tuple]:
        """The fields of the scientist until the provided year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    @accepts((set, list, tuple))
    def fields(self, val: Union[set, list, tuple]) -> None:
        self._fields = val

    @property
    def first_year(self) -> int:
        """The scientist's year of first publication."""
        return self._first_year

    @first_year.setter
    @accepts(int)
    def first_year(self, val: int) -> None:
        self._first_year = val

    @property
    def first_name(self) -> Optional[str]:
        """The scientist's first name."""
        return self._first_name

    @first_name.setter
    @accepts(str)
    def first_name(self, val: str) -> None:
        self._name = val

    @property
    def main_field(self) -> tuple:
        """The scientist's main field of research, as tuple in
        the form (ASJC code, general category).

        The main field is the field with the most publications, provided it
        is not Multidisciplinary (ASJC code 1000).  In case of an equal number
        of publications, preference is given to non-general fields (those
        whose ASJC ends on a digit other than 0).
        """
        return self._main_field

    @main_field.setter
    def main_field(self, val: tuple) -> None:
        if not isinstance(val, tuple) or len(val) != 2:
            raise TypeError("Value must be a two-element tuple.")
        self._main_field = val

    @property
    def name(self) -> Optional[str]:
        """The scientist's complete name."""
        return self._name

    @name.setter
    @accepts(str)
    def name(self, val: str) -> None:
        self._name = val

    @property
    def language(self) -> Optional[str]:
        """The language(s) the scientist published in."""
        return self._language

    @language.setter
    @accepts(str)
    def language(self, val: str) -> None:
        self._language = val

    @property
    def last_year(self) -> int:
        """The scientist's most recent year with publication(s) before the
         match year (which may be the same).
         """
        return self._last_year

    @last_year.setter
    @accepts(int)
    def last_year(self, val: int) -> None:
        self._last_year = val

    @property
    def publications(self) -> Union[set, list, tuple]:
        """List of the scientists' publications."""
        return self._publications

    @publications.setter
    @accepts((set, list, tuple))
    def publications(self, val: Union[set, list, tuple]) -> None:
        self._publications = val

    @property
    def sources(self) -> Union[list, tuple]:
        """The Scopus IDs of sources (journals, books, etc.) in which the
        scientist published in.
        """
        return self._sources

    @sources.setter
    @accepts((list, tuple))
    def sources(self, val: Union[list, tuple]) -> None:
        self._sources = add_source_names(val, self.source_names)

    @property
    def surname(self) -> Optional[str]:
        """The scientist's surname."""
        return self._surname

    @surname.setter
    @accepts(str)
    def surname(self, val: str):
        self._name = val

    @property
    def subjects(self) -> Union[set, list, tuple]:
        """The subject areas of the scientist's publications."""
        return self._subjects

    @subjects.setter
    @accepts((set, list, tuple))
    def subjects(self, val: Union[set, list, tuple]) -> None:
        self._subjects = val

    def __init__(
        self,
        identifier: list[int],
        year: Union[str, int],
        refresh: Union[bool, int] = False,
        eids: Optional[list[str]] = None,
        db_path: Optional[Union[str, Path]] = None,
        verbose: Optional[bool] = False
    ) -> None:
        """Class to represent a scientist.

        Parameters
        ----------
        identifier : list of int
            List of Scopus Author IDs of the scientist.

        year : str or numeric
            Year for which characteristics should be defined for.

        refresh : boolean or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        eids : list (optional, default=None)
            A list of Scopus EIDs of the publications of the scientist.  If
            provided, the scientist's properties are inferred from these
            publications, instead of the list of publications obtained from
            the Scopus Author ID(s).

        db_path : str or pathlib.Path (optional, default=None)
            The path of the local SQLite database to connect to.  If None,
            will default to `~/.cache/sosia/main.sqlite`.  Will be created
            if the database doesn't exist.

        verbose : bool (optional, default=False)
            Whether to report on the initialization process.

        Raises
        ------
        Exception
            When there are no publications for the author until the
            provided year.
        """
        self.identifier = identifier
        self.year = int(year)

        # Local database (cache)
        if not db_path:
            db_path = DEFAULT_DATABASE
        db_path = Path(db_path)
        self.sql_conn = connect_database(db_path, verbose=verbose)

        # Read mapping of fields to sources
        fields, info = read_fields_sources_list(verbose=verbose)
        self.field_source = fields
        self.source_info = info
        source_names = self.source_info.set_index("source_id")["title"].to_dict()
        self.source_names = source_names

        # Load list of publications
        if eids:
            q = f"EID({' OR '.join(eids)})"
        else:
            q = f"AU-ID({') OR AU-ID('.join([str(i) for i in identifier])})"
        integrity_fields = ["eid", "author_ids", "coverDate", "source_id"]
        res = base_query("docs", q, refresh, fields=integrity_fields)
        self._publications = [p for p in res if int(p.coverDate[:4]) <= int(year)]
        if not self._publications:
            text = "No publications found for author "\
                   f"{'-'.join([str(i) for i in identifier])} until {self.year}"
            raise ValueError(text)
        self._eids = eids or [p.eid for p in self._publications]

        # Publication range
        pub_years = [int(p.coverDate[:4]) for p in self._publications if p.coverDate]
        self._first_year = min(pub_years)
        self._last_year = max(pub_years)

        # Count of citations
        search_ids = eids or identifier
        self._citations = count_citations(search_ids, self.year+1, identifier)

        # Coauthors
        self._coauthors = sorted(set(extract_authors(self._publications)) - set(identifier))

        # Author search information
        source_ids = set([int(p.source_id) for p in self._publications
                          if p.source_id])
        self._sources = add_source_names(sorted(source_ids), self.source_names)
        mask = fields["source_id"].isin(source_ids)
        self._fields = fields[mask]["asjc"].astype(int).tolist()
        self._main_field = determine_main_field(self._fields)
        if not self._main_field[0]:
            text = "Not possible to determine research field(s) of "\
                   "researcher.  Functionality is reduced."
            warn(text, UserWarning)

        # Most recent geolocation
        afid = find_main_affiliation(identifier, self._publications, year)
        self._affiliation_id = afid
        try:
            aff = AffiliationRetrieval(afid, refresh=refresh)
            self._affiliation_country = aff.country
            self._affiliation_name = aff.affiliation_name
            self._affiliation_type = aff.org_type
        except (Scopus404Error, ValueError):
            self._affiliation_country = None
            self._affiliation_name = None
            self._affiliation_type = None
        self._language = None

        # Author name from profile with most documents
        df = get_author_info(self.identifier, self.sql_conn,
                             refresh=refresh, verbose=False)
        au = df.sort_values("documents", ascending=False).iloc[0]
        self._subjects = [a.split(" ")[0] for a in au.areas.split("; ")]
        self._surname = au.surname or None
        self._first_name = au.givenname or None
        name = ", ".join([self._surname or "", au.givenname or ""])
        if name == ", ":
            name = None
        self._name = name

    def get_publication_languages(self, refresh: bool = False) -> Self:
        """Parse languages of published documents."""
        langs = set()
        for eid in self._eids:
            try:
                ab = AbstractRetrieval(eid, view="FULL", refresh=refresh)
            except Scopus404Error:
                continue
            langs.add(ab.language)
        self._language = "; ".join(sorted(filter(None, langs)))
        return self
