#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Super class to represent a scientist."""

from collections import Counter

import pandas as pd
from pybliometrics.scopus import AbstractRetrieval

from sosia.processing import build_citation_query, find_coauthors,\
    find_country, query, query_author_data
from sosia.utils import ASJC_2D, FIELDS_SOURCES_LIST, SOURCES_NAMES_LIST,\
    add_source_names, create_fields_sources_list, raise_non_empty, raise_value

__all__ = ["Scientist"]


class Scientist(object):
    @property
    def active_year(self):
        """The scientist's year of first publication, as integer."""
        return self._active_year

    @active_year.setter
    def active_year(self, val):
        if not isinstance(val, int):
            raise Exception("Value must be an integer.")
        self._active_year = val

    @property
    def citations(self):
        """The citations of the scientist until
        the given year.
        """
        return self._citations

    @citations.setter
    def citations(self, val):
        raise_non_empty(val, int)
        self._citations = val

    @property
    def citations_period(self):
        """The citations of the scientist until
        the given year.
        """
        return self._citations_period

    @citations_period.setter
    def citations_period(self, val):
        raise_non_empty(val, int)
        self._citations_period = val

    @property
    def country(self):
        """Country of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        return self._country

    @country.setter
    def country(self, val):
        raise_non_empty(val, str)
        self._country = val

    @property
    def coauthors(self):
        """Set of coauthors of the scientist on all publications until the
        given year.
        """
        return self._coauthors

    @coauthors.setter
    def coauthors(self, val):
        raise_non_empty(val, (set, list, tuple))
        self._coauthors = val

    @property
    def coauthors_period(self):
        """Set of coauthors of the scientist on all publications until the
        given year.
        """
        return self._coauthors_period

    @coauthors_period.setter
    def coauthors_period(self, val):
        raise_non_empty(val, (set, list, tuple))
        self._coauthors_period = val

    @property
    def fields(self):
        """The fields of the scientist until the given year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    def fields(self, val):
        raise_non_empty(val, (set, list, tuple))
        self._fields = val

    @property
    def first_year(self):
        """The scientist's year of first publication, as integer."""
        return self._first_year

    @first_year.setter
    def first_year(self, val):
        raise_value(val, int)
        self._first_year = val

    @property
    def first_name(self):
        """The scientist's first name."""
        return self._first_name

    @first_name.setter
    def first_name(self, val):
        raise_non_empty(val, str)
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
    def name(self, val):
        raise_non_empty(val, str)
        self._name = val

    @property
    def language(self):
        """The language(s) of the documents published until the given year."""
        return self._language

    @language.setter
    def language(self, val):
        raise_non_empty(val, str)
        self._language = val

    @property
    def publications(self):
        """The publications of the scientist published until
        the given year.
        """
        return self._publications

    @publications.setter
    def publications(self, val):
        raise_non_empty(val, (set, list, tuple))
        self._publications = val

    @property
    def publications_period(self):
        """The publications of the scientist published until
        the given year.
        """
        return self._publications_period

    @publications_period.setter
    def publications_period(self, val):
        raise_non_empty(val, (set, list, tuple))
        self._publications_period = val

    @property
    def sources(self):
        """The Scopus IDs of sources (journals, books) in which the
        scientist published until the given year.
        """
        return self._sources

    @sources.setter
    def sources(self, val):
        raise_non_empty(val, (set, list, tuple))
        if not isinstance(list(val)[0], tuple):
            val = add_source_names(val, self.source_names)
        self._sources = val

    @property
    def surname(self):
        """The scientist's surname."""
        return self._surname

    @surname.setter
    def surname(self, val):
        raise_non_empty(val, str)
        self._name = val

    @property
    def subjects(self):
        """The subject areas retrieved from Scopus AuthorSearch.
        """
        return self._subjects

    @subjects.setter
    def subjects(self, val):
        raise_non_empty(val, (set, list, tuple))
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
        self.year = year
        self.period = period
        self.year_period = None

        # Read mapping of fields to sources
        try:
            df = pd.read_csv(FIELDS_SOURCES_LIST)
        except FileNotFoundError:
            create_fields_sources_list()
            df = pd.read_csv(FIELDS_SOURCES_LIST)
        names = pd.read_csv(SOURCES_NAMES_LIST, index_col=0)["title"].to_dict()
        self.field_source = df
        self.source_names = names

        # Load list of publications
        if not eids:
            q = "AU-ID({})".format(") OR AU-ID(".join(identifier))
        else:
            print('eids', eids)
            q = "EID({})".format(" OR ".join(eids))
        res = query("docs", q, refresh)
        try:
            self._publications = [p for p in res if int(p.coverDate[:4]) <=
                                  year]
        except (AttributeError, TypeError):
            res = query("docs", q, True)
            self._publications = [p for p in res if int(p.coverDate[:4]) <=
                                  year]
        if not len(self._publications):
            text = "No publications for author {} until year {}".format(
                "-".join(identifier), year)
            raise Exception(text)
        # if period provided set first year of period, if not smaller than
        # first year of publication
        self._first_year = int(min([p.coverDate[:4] for p in self._publications]))
        if period and year - period + 1 <= self._first_year:
                self.period = None
        elif period:
            self.year_period = year - period + 1

        # if period is int, get publications in period
        if self.period:
            self._publications_period = [p for p in self._publications if
                                         int(p.coverDate[:4]) <= year and
                                         int(p.coverDate[:4]) >=
                                         self.year_period]
            if not len(self._publications_period):
                text = "No publications for author {} until year {} in a {}-"\
                       "years period".format("-".join(identifier), year,
                                             self.year_period)
                raise Exception(text)
        # list of eids if not provided
        if not eids:
            eids = [p.eid for p in self._publications]
        self._eids = eids
        if self.period:
            eids_period = [p.eid for p in self._publications_period]

        # Get count of citations
        params = {"pubyear": self.year+1}
        if not eids:
            params.update({"search_ids": identifier, "exclusion_key": "AU-ID",
                           "exclusion_ids": identifier})
        else:
            params.update({"search_ids": eids, "exclusion_key": "EID",
                           "exclusion_ids": eids})
        q = build_citation_query(**params)
        self._citations = query("docs", q, size_only=True)
        if self.period:
            params.update({"search_ids": eids_period, "exclusion_key": "EID",
                           "exclusion_ids": eids_period})
            q = build_citation_query(**params)
            self._citations_period = query("docs", q, size_only=True)

        # coauthors
        self._coauthors = find_coauthors(self._publications, identifier)
        if self.period:
            self._coauthors_period = find_coauthors(self._publications_period,
                                                    identifier)

        # period counts simply set to total if period is or goes back to None
        if not self.period:
            self._coauthors_period = self._coauthors
            self._publications_period = self._publications
            self._citations_period = self._citations
        # Parse information
        source_ids = set([int(p.source_id) for p in self._publications if p.source_id])
        self._sources = add_source_names(source_ids, names)
        self._active_year = int(max([p.coverDate[:4] for p in self._publications
                                    if int(p.coverDate[:4]) <= year]))
        self._country = find_country(identifier, self._publications, year, refresh)

        # Author search information
        source_ids = set([int(p.source_id) for p in self._publications if p.source_id])
        self._sources = add_source_names(source_ids, names)
        self._fields = df[df["source_id"].isin(source_ids)]["asjc"].tolist()
        self._main_field = _get_main_field(self._fields)
        au = query_author_data(self.identifier, refresh=refresh, verbose=False)
        au = au.sort_values("documents", ascending=True).iloc[0]
        self._subjects = [a.split(" ")[0] for a in au.areas.split("; ")]
        self._name = ", ".join([au.surname, au.givenname])
        self._surname = au.surname
        self._first_name = au.givenname.replace(".", " ").split(" ")[0]
        self._language = None

    def get_publication_languages(self, refresh=False):
        """Parse languages of published documents."""
        langs = []
        for eid in self._eids:
            try:
                lang = AbstractRetrieval(eid, view="FULL", refresh=refresh).language
            except KeyError:  # Document likely not loaded in FULL view
                lang = AbstractRetrieval(eid, view="FULL", refresh=True).language
            langs.append(lang)
        self._language = "; ".join(sorted(list(set(filter(None, langs)))))
        return self


def _get_main_field(fields):
    """Auxiliary function to get code and name of main field.

    We exclude multidisciplinary and give preference to non-general fields.
    """
    c = Counter(fields)
    try:
        c.pop(1000)  # Exclude Multidisciplinary
    except KeyError:
        pass
    top_fields = [f for f, val in c.items() if val == max(c.values())]
    if len(top_fields) == 1:
        main = top_fields[0]
    else:
        non_general_fields = [f for f in top_fields if f % 1000 != 0]
        if non_general_fields:
            main = non_general_fields[0]
        else:
            main = top_fields[0]
    code = int(str(main)[:2])
    return (main, ASJC_2D[code])
