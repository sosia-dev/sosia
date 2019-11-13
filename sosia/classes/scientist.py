#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Super class to represent a scientist."""

from pybliometrics.scopus import AbstractRetrieval

from sosia.processing import count_citations, base_query, find_location,\
    get_authors, query_author_data
from sosia.utils import accepts, add_source_names, get_main_field,\
    maybe_add_source_names, read_fields_sources_list


class Scientist(object):
    @property
    def active_year(self):
        """The scientist's year of first publication, as integer."""
        return self._active_year

    @active_year.setter
    @accepts(int)
    def active_year(self, val):
        self._active_year = val

    @property
    def affiliation_id(self):
        """The affiliation ID (as string) of the scientist's most frequent
        affiliation in the most recent year (before the given year) that
        the scientist published.
        """
        return self._affiliation_id

    @affiliation_id.setter
    @accepts(str)
    def affiliation_id(self, val):
        self._affiliation_id = val

    @property
    def citations(self):
        """The citations of the scientist until the given year."""
        return self._citations

    @citations.setter
    @accepts(int)
    def citations(self, val):
        self._citations = val

    @property
    def citations_period(self):
        """The citations of the scientist until during the given period."""
        return self._citations_period

    @citations_period.setter
    @accepts(int)
    def citations_period(self, val):
        self._citations_period = val

    @property
    def city(self):
        """City of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        return self._city

    @city.setter
    @accepts(str)
    def city(self, val):
        self._city = val

    @property
    def country(self):
        """Country of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        return self._country

    @country.setter
    @accepts(str)
    def country(self, val):
        self._country = val

    @property
    def coauthors(self):
        """Set of coauthors of the scientist on all publications until the
        given year.
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
        """The fields of the scientist until the given year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    @accepts((set, list, tuple))
    def fields(self, val):
        self._fields = val

    @property
    def first_year(self):
        """The scientist's year of first publication, as integer."""
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
            raise Exception("Value must be a two-element tuple.")
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
        """The language(s) of the documents published until the given year."""
        return self._language

    @language.setter
    @accepts(str)
    def language(self, val):
        self._language = val

    @property
    def organization(self):
        """The affiliation name of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        return self._organization

    @organization.setter
    @accepts(str)
    def organization(self, val):
        self._organization = val

    @property
    def publications(self):
        """The publications of the scientist published until
        the given year.
        """
        return self._publications

    @publications.setter
    @accepts((set, list, tuple))
    def publications(self, val):
        self._publications = val

    @property
    def publications_period(self):
        """The publications of the scientist published until
        the given year.
        """
        return self._publications_period

    @publications_period.setter
    @accepts((set, list, tuple))
    def publications_period(self, val):
        self._publications_period = val

    @property
    def sources(self):
        """The Scopus IDs of sources (journals, books) in which the
        scientist published until the given year.
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
        """The subject areas retrieved from Scopus AuthorSearch.
        """
        return self._subjects

    @subjects.setter
    @accepts((set, list, tuple))
    def subjects(self, val):
        self._subjects = val

    def __init__(self, identifier, year, refresh=False, period=None, eids=None):
        """Class to represent a scientist.

        Parameters
        ----------
        identifier : list of str
            List of Scopus Author IDs of the scientist.

        year : str or numeric
            Year for which characteristics should be defined for.

        refresh : boolean (optional, default=False)
            Whether to refresh all cached files or not.

        eids : list (optional, default=None)
            A list of scopus EIDs of the publications of the scientist.  If
            it is provided, the scientist's properties are set based on these
            publications, instead of the list of publications obtained from
            the Scopus Author ID(s).

        period: int (optional, default=None)
            The period in which to consider publications. If not provided,
            all publications are considered.

        Raises
        ------
        Exeption
            When there are no publications for the author until the
            given year.
        """
        self.identifier = identifier
        self.year = int(year)
        self.period = period
        self.year_period = None

        # Read mapping of fields to sources
        df, names = read_fields_sources_list()
        self.field_source = df
        self.source_names = names.set_index("source_id")["title"].to_dict()

        # Load list of publications
        if not eids:
            q = "AU-ID({})".format(") OR AU-ID(".join(identifier))
        else:
            q = "EID({})".format(" OR ".join(eids))
        res = base_query("docs", q, refresh,
            fields=["eid", "author_ids", "coverDate"])
        self._publications = [p for p in res if int(p.coverDate[:4]) <= year]
        if not len(self._publications):
            text = "No publications for author {} until year {}".format(
                "-".join(identifier), year)
            raise Exception(text)
        self._eids = eids or [p.eid for p in self._publications]

        # Fist year (if period provided set first year of period, if
        # not smaller than first year of publication
        pub_years = [p.coverDate[:4] for p in self._publications]
        self._first_year = int(min(pub_years))
        if period and year-period+1 <= self._first_year:
            self.period = None

        # Count of citations
        search_ids = eids or identifier
        self._citations = count_citations(search_ids=search_ids,
            pubyear=self.year+1, exclusion_key="AU-ID", exclusion_ids=identifier)

        # Coauthors
        self._coauthors = set(get_authors(self._publications)) - set(identifier)

        # Period counts simply set to total if period is or goes back to None
        if self.period:
            self.year_period = year-period+1
            pubs = [p for p in self._publications if
                    int(p.coverDate[:4]) <= year and
                    int(p.coverDate[:4]) >= self.year_period]
            self._publications_period = pubs
            if not len(self._publications_period):
                text = "No publications for author {} until year {} in a {}-"\
                       "years period".format("-".join(identifier), year,
                                             self.year_period)
                raise Exception(text)
            eids_period = [p.eid for p in self._publications_period]
            self._citations_period = count_citations(search_ids=eids_period,
                pubyear=self.year+1, exclusion_key="AU-ID",
                exclusion_ids=identifier)
            self._coauthors_period = set(get_authors(self._publications_period))
            self._coauthors_period -= set(identifier)
        else:
            self._coauthors_period = self._coauthors
            self._publications_period = self._publications
            self._citations_period = self._citations

        # Author search information
        source_ids = set([int(p.source_id) for p in self._publications
                          if p.source_id])
        self._sources = add_source_names(source_ids, self.source_names)
        self._active_year = int(max(pub_years))
        self._fields = df[df["source_id"].isin(source_ids)]["asjc"].tolist()
        self._main_field = get_main_field(self._fields)

        # Most recent geolocation
        ctry, afid, org = find_location(identifier, self._publications,
                                        year, refresh=refresh)
        self._country = ctry
        self._affiliation_id = afid
        self._organization = org
        self._language = None

        # Author name from profile with most documents
        au = query_author_data(self.identifier, refresh=refresh, verbose=False)
        au = au.sort_values("documents", ascending=False).iloc[0]
        self._subjects = [a.split(" ")[0] for a in au.areas.split("; ")]
        self._surname = au.surname or None
        if au.givenname:
            self._first_name = au.givenname.replace(".", " ").split(" ")[0]
        else:
            self._first_name = None
        if self._surname and au.givenname:
            self._name = ", ".join([self._surname, au.givenname])
        else:
            self._name = None

    def get_publication_languages(self, refresh=False):
        """Parse languages of published documents."""
        langs = []
        for eid in self._eids:
            l = AbstractRetrieval(eid, view="FULL", refresh=refresh).language
            langs.append(l)
        self._language = "; ".join(sorted(list(set(filter(None, langs)))))
        return self
