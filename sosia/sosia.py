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
    def first_year(self):
        au = sco.AuthorRetrieval(self.id)
        return au.publication_range[0]

    @property
    def journals(self):
        """The journals and conference proceedings in which the scientist
        published until the given year year."""
        return set([p.publicationName for p in self.publications])

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
