#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

import warnings
from collections import Counter
from math import log
from os.path import exists

import pandas as pd
import scopus as sco

from sosia.utils import ASJC_2D, FIELDS_JOURNALS_LIST


class Original(object):
    @property
    def country(self):
        """Country of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        # List of relevant papers
        papers = []
        max_iter = self.year - self.first_year + 1
        i = 0
        while len(papers) == 0 & i <= max_iter:
            papers = [p for p in self.publications if int(p.coverDate[:4]) == self.year-i]
            i += 1
        if len(papers) == 0:
            return None
        # List of affiliations
        affs = []
        for p in papers:
            authors = p.authid.split(';')
            idx = authors.index(str(self.id))
            aff = p.afid.split(';')[idx].split('-')
            affs.extend(aff)
        affs = [a for a in affs if a != '']
        # Find countries of affiliations
        countries = [sco.ContentAffiliationRetrieval(afid).country for afid in affs]
        return Counter(countries).most_common(1)[0][0]

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
        """The fields of the scientist until the given year, estimated from
        the journal she published in.
        """
        df = self.field_journal
        return df[df['source_id'].isin(self.journals)]['asjc'].tolist()

    @property
    def first_year(self):
        """The scientist's year of first publication, as string."""
        q = 'AU-ID({})'.format(self.id, self.year)
        pubs = sco.ScopusSearch(q, refresh=self.refresh).results
        return int(min([p.coverDate[:4] for p in pubs]))

    @property
    def journals(self):
        """The Scopus IDs of journals and conference proceedings in which the
        scientist published until the given year.
        """
        return set([p.source_id  for p in self.publications])

    @property
    def main_field(self):
        """The scientist's main field of research, as tuple in
        the form (ASJC code, general category).
        """
        main = Counter(self.fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        return (main, ASJC_2D[code])

    @property
    def publications(self):
        """The publications of the scientist published until
        the given year.
        """
        q = 'AU-ID({})'.format(self.id)
        s = sco.ScopusSearch(q, refresh=self.refresh)
        pubs = [p for p in s.results if int(p.coverDate[:4]) < self.year]
        if len(pubs) > 0:
            return pubs
        else:
            text = "No publications for author with ID {} until year {}".format(
                self.id, self.year)
            warnings.warn(text, UserWarning)
            return None

    @property
    def search_group_then(self):
        """Authors of publications in journals in the scientist's field
        in the year of the scientist's first publication.
        """
        authors = set()
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
        for journal in self.search_journals:
            q = 'SOURCE-ID({})'.format(journal)
            try:  # Try complete publication list first
                s = sco.ScopusSearch(q)
                res = [p for p in s.results if int(p.coverDate[:4]) in _years]
            except:  # Fall back to year-wise queries
                for year in _years:
                    q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(journal, year)
                    s = sco.ScopusSearch(q)
                    res = s.results
            new = [x.authid.split(';') for x in res if isinstance(x.authid, str)]
            authors.update([au for sl in new for au in sl])
        return authors

    @property
    def search_group_today(self):
        """Authors of publications in journals in the scientist's field
        in the given year.
        """
        authors = set()
        for journal in self.search_journals:
            q = 'SOURCE-ID({})'.format(journal)
            try:  # Try complete publication list first
                s = sco.ScopusSearch(q)
                res = [p for p in s.results if int(p.coverDate[:4]) == self.year]
            except:  # Fall back to year-wise queries
                q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(journal, self.year)
                s = sco.ScopusSearch(q)
                res = s.results
            new = [x.authid.split(';') for x in res if isinstance(x.authid, str)]
            authors.update([au for sl in new for au in sl])
        return authors

    @property
    def search_group_negative(self):
        """Authors of publications in journals in the scientist's field
        before the year of the scientist's first publication.
        """
        authors = set()
        _min = self.first_year-self.year_margin
        for journal in self.search_journals:
            q = 'SOURCE-ID({})'.format(journal)
            try:
                s = sco.ScopusSearch(q)
                res = [p for p in s.results if int(p.coverDate[:4]) < _min]
            except Exception as e:
                # Do not run year-wise queries for this group
                continue
            new = [x.authid.split(';') for x in res if isinstance(x.authid, str)]
            authors.update([au for sl in new for au in sl])
        return authors

    @property
    def search_journals(self):
        """The set of journals comparable to the journals the scientist
        published in until the given year.
        A journal is comparable if is belongs to the scientist's main field
        but not to fields alien to the scientist.
        """
        df = self.field_journal
        # Select journals in scientist's main field
        journals = df[df['asjc'] == self.main_field[0]]['source_id'].tolist()
        sel = df[df['source_id'].isin(journals)].copy()
        sel['asjc'] = sel['asjc'].astype(str) + " "
        grouped = sel.groupby('source_id').sum()['asjc'].to_frame()
        # Deselect journals with alien fields
        grouped['drop'] = grouped['asjc'].apply(
            lambda s: any(x for x in s.split() if int(x) not in self.fields))
        return grouped[~grouped['drop']].index.tolist()

    def __init__(self, scientist, year, year_margin=1, refresh=False):
        """Class to represent a scientist for which we want to find a control
        group.

        Parameters
        ----------
        scientist : str or int
            Scopus Author ID of the scientist you want to find control
            groups for.

        year : str or numeric
            Year of the event.  Control groups will be matched on trends and
            characteristics of the scientist up to this year.

        year_margin : str or numeric (optional, default=1)
            Number of years by which the search for authors publishing around
            the year of the focal scientist's year of first publication should
            be extend in both directions.
        """
        # Check for existence of fields-journals list
        try:
            self.field_journal = pd.read_csv(FIELDS_JOURNALS_LIST, dtype=int)
        except FileNotFoundError:
            text = "Fields-Journals list not found, but required for sosia "\
                   "to match authors' publications to fields.  Please run "\
                   "sosia.create_fields_journals_list() and initiate "\
                   "the class again."
            warnings.warn(text, UserWarning)

        # Variables
        self.id = str(scientist)
        self.year = int(year)
        self.year_margin = int(year_margin)
        self.refresh = refresh
