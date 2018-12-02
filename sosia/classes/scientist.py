#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Super class to represent a scientist."""

from collections import Counter
from math import log

import pandas as pd

from sosia.utils import (ASJC_2D, FIELDS_SOURCES_LIST,
    create_fields_sources_list, find_country, query)


class Scientist(object):
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

        # Parse information
        self._sources = set([int(p.source_id) for p in self._publications])
        self._fields = df[df['source_id'].isin(self._sources)]['asjc'].tolist()
        main = Counter(self._fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        self._main_field = (main, ASJC_2D[code])
        self._first_year = int(min([p.coverDate[:4] for p in self._publications]))
        self._coauthors = set([a for p in self._publications
                               for a in p.authid.split(';') if a not in identifier])
        self._country = find_country(identifier, self._publications, year)
