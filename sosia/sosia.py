#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

import warnings
from os.path import exists

import pandas as pd
import scopus as sco

from sosia.utils import FIELDS_JOURNALS_LIST


class Original(object):
    @property
    def coauthors(self):
        """Set of coauthors of the scientist on all publications until the
        given year.
        """
        coauth = set([a for p in self.publications for a in p.authid.split(';')])
        coauth.remove(self.id)
        return coauth

    @property
    def fields(self):
        """The fields of the scientiest until the given year, estimated from
        the journal she published in.
        """
        df = self.field_journal
        return df[df['source_id'].isin(self.journals)]['asjc'].tolist()

    @property
    def first_year(self):
        """The scientist's year of first publication, as string."""
        q = 'AU-ID({}) AND PUBYEAR BEF {}'.format(self.id, self.year)
        pubs = sco.ScopusSearch(q, refresh=self.refresh).results
        return min([p.coverDate[:4] for p in pubs])

    @property
    def journals(self):
        """The Scopus IDs of journals and conference proceedings in which the
        scientist published until the given year.
        """
        return set([p.source_id  for p in self.publications])

    @property
    def publications(self):
        """The publications of the scientist published until before
        the given year.
        """
        q = 'AU-ID({}) AND PUBYEAR BEF {}'.format(self.id, self.year)
        pubs = sco.ScopusSearch(q, refresh=self.refresh).results
        if len(pubs) > 0:
            return pubs
        else:
            text = "No publications for author with ID {} until year {}".format(
                self.id, self.year)
            warnings.warn(text, UserWarning)
            return None

    def __init__(self, scientist, year, refresh=False):
        """Class to represent a scientist for which we want to find a control
        group.

        Parameters
        ----------
        scientist : str or int
            Scopus Author ID of the scientist you want to find control
            groups for.

        year : str or int
            Year of the event.  Control groups will be matched on trends and
            characteristics of the scientist up to this year.
        """
        # Check for existence of fields-journals list
        try:
            self.field_journal = pd.read_csv(FIELDS_JOURNALS_LIST)
        except FileNotFoundError:
            text = "Fields-Journals list not found, but required for sosia "\
                   "to match authors' publications to fields.  Please run "\
                   "sosia.create_fields_journals_list() and initiate "\
                   "the class again."
            warnings.warn(text, UserWarning)

        # Variables
        self.id = str(scientist)
        self.year = int(year)
        self.refresh = refresh
