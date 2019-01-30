#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Super class to represent a scientist."""

from collections import Counter
from math import log

import pandas as pd
from scopus import AbstractRetrieval, AuthorRetrieval

from sosia.utils import (ASJC_2D, FIELDS_SOURCES_LIST,
    create_fields_sources_list, find_country, query, raise_non_empty)


class Scientist(object):
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
        raise_non_empty(val, set)
        self._coauthors = val

    @property
    def fields(self):
        """The fields of the scientist until the given year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    def fields(self, val):
        raise_non_empty(val, set)
        self._fields = val

    @property
    def first_year(self):
        """The scientist's year of first publication, as integer."""
        return self._first_year

    @first_year.setter
    def first_year(self, val):
        if not isinstance(val, int):
            raise Exception("Value must be an integer.")
        self._first_year = val

    @property
    def main_field(self):
        """The scientist's main field of research, as tuple in
        the form (ASJC code, general category).
        """
        return self._main_field

    @main_field.setter
    def main_field(self, val):
        if not isinstance(val, tuple) or len(val) != 2:
            raise Exception("Value must be a two-element tuple.")
        self._main_field = val

    @property
    def name(self):
        """The scientist's name."""
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
        raise_non_empty(val, set)
        self._publications = val

    @property
    def sources(self):
        """The Scopus IDs of sources (journals, books) in which the
        scientist published until the given year.
        """
        return self._sources

    @sources.setter
    def sources(self, val):
        raise_non_empty(val, set)
        self._sources = val

    def __init__(self, identifier, year, refresh=False, eids=None):
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

        Raises
        ------
        Exeption
            When there are no publications for the author until the
            given year.
        """
        # Read mapping of fields to sources
        try:
            df = pd.read_csv(FIELDS_SOURCES_LIST)
        except FileNotFoundError:
            create_fields_sources_list()
            df = pd.read_csv(FIELDS_SOURCES_LIST)
        self.field_source = df

        # Load list of publications
        if not eids:
            q = 'AU-ID({})'.format(') OR AU-ID('.join(identifier))
        else:
            q = 'EID({})'.format(' OR '.join(eids))
        res = query("docs", q, refresh)
        self._publications = [p for p in res if int(p.coverDate[:4]) < year]
        if len(self._publications) == 0:
            text = "No publications for author {} until year {}".format(
                '-'.join(identifier), year)
            raise Exception(text)
        if not eids:
            eids = [p.eid for p in self._publications]
        self._eids = eids

        # Parse information
        self._sources = set([int(p.source_id) for p in self._publications])
        self._fields = df[df['source_id'].isin(self._sources)]['asjc'].tolist()
        main = Counter(self._fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        self._main_field = (main, ASJC_2D[code])
        self._first_year = int(min([p.coverDate[:4] for p in self._publications]))
        self._coauthors = set([a for p in self._publications for a
                               in p.author_ids.split(';') if a not in identifier])
        self._country = find_country(identifier, self._publications, year)
        au = AuthorRetrieval(identifier[0], refresh=refresh)
        self._name = ", ".join([au.surname, au.given_name])
        self._language = None

    def get_publication_languages(self, refresh=False):
        """Parse languages of published documents."""
        langs = []
        for eid in self._eids:
            try:
                langs.append(AbstractRetrieval(eid, view="FULL", refresh=refresh).language)
            except KeyError:
                langs.append(AbstractRetrieval(eid, view="FULL", refresh=True).language)
        self._language = "; ".join(sorted(list(set(langs))))
        return self
