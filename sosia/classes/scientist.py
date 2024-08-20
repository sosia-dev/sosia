"""Module with super class to represent a `Scientist`."""

from warnings import warn

from pybliometrics.scopus import AbstractRetrieval, AffiliationRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from sosia.establishing import connect_database, DEFAULT_DATABASE
from sosia.processing import add_source_names, base_query, count_citations, \
    extract_authors, find_main_affiliation, get_authors, get_main_field, \
    maybe_add_source_names, read_fields_sources_list
from sosia.utils import accepts


class Scientist(object):
    """Class to represent a scientist.
    """
    @property
    def active_year(self):
        """The scientist's most recent year with publication(s) before
         provided year (which may be the same).
         """
        return self._active_year

    @active_year.setter
    @accepts(int)
    def active_year(self, val):
        self._active_year = val

    @property
    def affiliation_country(self):
        """The country of the scientist's affiliation."""
        return self._affiliation_country

    @affiliation_country.setter
    @accepts(str)
    def affiliation_country(self, val):
        self._affiliation_country = val

    @property
    def affiliation_id(self):
        """The affiliation ID (as string) of the scientist's most frequent
        affiliation in the active year.
        """
        return self._affiliation_id

    @affiliation_id.setter
    @accepts(str)
    def affiliation_id(self, val):
        self._affiliation_id = val

    @property
    def affiliation_name(self):
        """The name of the scientist's affiliation."""
        return self._affiliation_name

    @affiliation_name.setter
    @accepts(str)
    def affiliation_name(self, val):
        self._affiliation_name = val

    @property
    def affiliation_type(self):
        """The type of the scientist's affiliation."""
        return self._affiliation_type

    @affiliation_type.setter
    @accepts(str)
    def affiliation_type(self, val):
        self.affiliation_type = val

    @property
    def citations(self):
        """The citation count of the scientist until the provided year."""
        return self._citations

    @citations.setter
    @accepts(int)
    def citations(self, val):
        self._citations = val

    @property
    def citations_period(self):
        """The citation count of the scientist during the given period."""
        return self._citations_period

    @citations_period.setter
    @accepts(int)
    def citations_period(self, val):
        self._citations_period = val

    @property
    def coauthors(self):
        """Set of coauthors of the scientist on all publications until the
        comparison year.
        """
        return self._coauthors

    @coauthors.setter
    @accepts((set, list, tuple))
    def coauthors(self, val):
        self._coauthors = val

    @property
    def coauthors_period(self):
        """Set of coauthors of the scientist on all publications during the
        given period.
        """
        return self._coauthors_period

    @coauthors_period.setter
    @accepts((set, list, tuple))
    def coauthors_period(self, val):
        self._coauthors_period = val

    @property
    def fields(self):
        """The fields of the scientist until the provided year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    @accepts((set, list, tuple))
    def fields(self, val):
        self._fields = val

    @property
    def first_year(self):
        """The scientist's year of first publication."""
        return self._first_year

    @first_year.setter
    @accepts(int)
    def first_year(self, val):
        self._first_year = val

    @property
    def first_name(self):
        """The scientist's first name."""
        return self._first_name

    @first_name.setter
    @accepts(str)
    def first_name(self, val):
        self._name = val

    @property
    def main_field(self):
        """The scientist's main field of research, as tuple in
        the form (ASJC code, general category).

        The main field is the field with the most publications, provided it
        is not Multidisciplinary (ASJC code 1000).  In case of an equal number
        of publications, preference is given to non-general fields (those
        whose ASJC ends on a digit other than 0).
        """
        return self._main_field

    @main_field.setter
    def main_field(self, val):
        if not isinstance(val, tuple) or len(val) != 2:
            raise TypeError("Value must be a two-element tuple.")
        self._main_field = val

    @property
    def name(self):
        """The scientist's complete name."""
        return self._name

    @name.setter
    @accepts(str)
    def name(self, val):
        self._name = val

    @property
    def language(self):
        """The language(s) the scientist published in."""
        return self._language

    @language.setter
    @accepts(str)
    def language(self, val):
        self._language = val

    @property
    def publications(self):
        """List of the scientists' publications."""
        return self._publications

    @publications.setter
    @accepts((set, list, tuple))
    def publications(self, val):
        self._publications = val

    @property
    def publications_period(self):
        """The publications of the scientist published during
        the given period.
        """
        return self._publications_period

    @publications_period.setter
    @accepts((set, list, tuple))
    def publications_period(self, val):
        self._publications_period = val

    @property
    def sources(self):
        """The Scopus IDs of sources (journals, books, etc.) in which the
        scientist published in.
        """
        return self._sources

    @sources.setter
    @accepts((list, tuple))
    def sources(self, val):
        self._sources = maybe_add_source_names(val, self.source_names)

    @property
    def surname(self):
        """The scientist's surname."""
        return self._surname

    @surname.setter
    @accepts(str)
    def surname(self, val):
        self._name = val

    @property
    def subjects(self):
        """The subject areas of the scientist's publications."""
        return self._subjects

    @subjects.setter
    @accepts((set, list, tuple))
    def subjects(self, val):
        self._subjects = val

    def __init__(self, identifier, year, refresh=False, period=None, eids=None,
                 sql_fname=None):
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

        period: int (optional, default=None)
            An additional point in time to match characteristics on.  Will
            fe interpreted as number years prior to the comparison year.

        sql_fname : str (optional or pathlib.Path(), default=None)
            The path of the local SQLite database to connect to.  If None,
            will default to `~/.cache/sosia/main.sqlite`.

        Raises
        ------
        Exception
            When there are no publications for the author until the
            provided year.
        """
        self.identifier = identifier
        self.year = int(year)
        if not sql_fname:
            sql_fname = DEFAULT_DATABASE
        self.sql_conn = connect_database(sql_fname)

        # Read mapping of fields to sources
        fields, info = read_fields_sources_list()
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
        self._publications = [p for p in res if int(p.coverDate[:4]) <= year]
        if not self._publications:
            text = "No publications found for author "\
                   f"{'-'.join([str(i) for i in identifier])} until {year}"
            raise ValueError(text)
        self._eids = eids or [p.eid for p in self._publications]

        # First year of publication
        pub_years = [p.coverDate[:4] for p in self._publications]
        self._first_year = int(min(pub_years))
        self._period_year = self.year - (period or (self.year+1)) + 1
        if self._period_year < self._first_year:
            self._period_year = 0

        # Count of citations
        search_ids = eids or identifier
        self._citations = count_citations(search_ids, self.year+1, identifier)

        # Coauthors
        self._coauthors = set(extract_authors(self._publications)) - set(identifier)

        # Period counts simply set to total if period is or goes back to None
        if self._period_year:
            pubs = [p for p in self._publications if
                    self._period_year <= int(p.coverDate[:4]) <= year]
            self._publications_period = pubs
            if not self._publications_period:
                text = "No publications found for author "\
                       f"{'-'.join([str(i) for i in identifier])} until "\
                       f"{year} in a {self._period_year}-years period"
                raise ValueError(text)
            eids_period = [p.eid for p in self._publications_period]
            n_cits = count_citations(eids_period, self.year+1, identifier)
            self._citations_period = n_cits
            self._coauthors_period = set(extract_authors(self._publications_period))
            self._coauthors_period -= set(identifier)
        else:
            self._coauthors_period = None
            self._publications_period = None
            self._citations_period = None

        # Author search information
        source_ids = set([int(p.source_id) for p in self._publications
                          if p.source_id])
        self._sources = add_source_names(source_ids, self.source_names)
        self._active_year = int(max(pub_years))
        mask = fields["source_id"].isin(source_ids)
        self._fields = fields[mask]["asjc"].astype(int).tolist()
        self._main_field = get_main_field(self._fields)
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
        df = get_authors(self.identifier, self.sql_conn,
                         refresh=refresh, verbose=False)
        au = df.sort_values("documents", ascending=False).iloc[0]
        self._subjects = [a.split(" ")[0] for a in au.areas.split("; ")]
        self._surname = au.surname or None
        self._first_name = au.givenname or None
        name = ", ".join([self._surname or "", au.givenname or ""])
        if name == ", ":
            name = None
        self._name = name

    def get_publication_languages(self, refresh=False):
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
