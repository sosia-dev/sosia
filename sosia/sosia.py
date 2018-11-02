#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

import warnings
from collections import Counter
from math import ceil, floor, log
from operator import attrgetter
from os.path import exists

import pandas as pd
import scopus as sco

from sosia.utils import ASJC_2D, FIELDS_JOURNALS_LIST

MAX_LENGTH = 3893  # Maximum character length of a query


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
            papers = [p for p in self.publications if
                      int(p.coverDate[:4]) == self.year-i]
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
        countries = [sco.ContentAffiliationRetrieval(afid).country
                     for afid in affs]
        return Counter(countries).most_common(1)[0][0]

    @country.setter
    def country(self, val):
        if not isinstance(val, str):
            raise Exception("Value must be a string.")
        self._country = val

    @property
    def coauthors(self):
        """Set of coauthors of the scientist on all publications until the
        given year.
        """
        coauth = set([a for p in self.publications
                      for a in p.authid.split(';')])
        coauth.remove(self.id)
        return coauth

    @coauthors.setter
    def coauthors(self, val):
        if not isinstance(val, set) or len(val) == 0:
            raise Exception("Value must be a non-empty set.")
        self._coauthors = val

    @property
    def fields(self):
        """The fields of the scientist until the given year, estimated from
        the journal she published in.
        """
        df = self.field_journal
        return df[df['source_id'].isin(self.journals)]['asjc'].tolist()

    @fields.setter
    def fields(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
        self._fields = val

    @property
    def first_year(self):
        """The scientist's year of first publication, as integer."""
        return int(min([p.coverDate[:4] for p in self.publications]))

    @first_year.setter
    def first_year(self, val):
        if not isinstance(val, int):
            raise Exception("Value must be an integer.")
        self._first_year = val

    @property
    def journals(self):
        """The Scopus IDs of journals and conference proceedings in which the
        scientist published until the given year.
        """
        return set([p.source_id for p in self.publications])

    @journals.setter
    def journals(self, val):
        if not isinstance(val, set) or len(val) == 0:
            raise Exception("Value must be a non-empty set.")
        self._journals = val

    @property
    def main_field(self):
        """The scientist's main field of research, as tuple in
        the form (ASJC code, general category).
        """
        main = Counter(self.fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        return (main, ASJC_2D[code])

    @main_field.setter
    def main_field(self, val):
        if not isinstance(val, tuple) or len(val) != 2:
            raise Exception("Value must be a two-element tuple.")
        self._main_field = val

    @property
    def publications(self):
        """The publications of the scientist published until
        the given year.
        """
        res = _query_docs('AU-ID({})'.format(self.id), refresh=self.refresh)
        pubs = [p for p in res if int(p.coverDate[:4]) < self.year]
        if len(pubs) > 0:
            return pubs
        else:
            text = "No publications for author {} until year {}".format(
                self.id, self.year)
            warnings.warn(text, UserWarning)
            return None

    @publications.setter
    def publications(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
        self._publications = val

    @property
    def search_group_then(self):
        """Authors of publications in journals in the scientist's field
        in the year of the scientist's first publication.

        Notes
        -----
        Property is initiated via .define_search_groups().
        """
        try:
            return self._search_group_then
        except AttributeError:
            return None

    @property
    def search_group_today(self):
        """Authors of publications in journals in the scientist's field
        in the given year.

        Notes
        -----
        Property is initiated via .define_search_groups().
        """
        try:
            return self._search_group_today
        except AttributeError:
            return None

    @property
    def search_group_negative(self):
        """Authors with too many publications in the scientist's search
        journals already in the given year and authors of publications
        in journals in the scientist's field before the year of the 
        scientist's first publication.

        Notes
        -----
        Property is initiated via .define_search_groups().
        """
        try:
            return self._search_group_negative
        except AttributeError:
            return None

    @property
    def search_journals(self):
        """The set of journals comparable to the journals the scientist
        published in until the given year.
        A journal is comparable if is belongs to the scientist's main field
        but not to fields alien to the scientist.
        """
        try:
            return self._search_journals
        except AttributeError:
            return None

    @search_journals.setter
    def search_journals(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
        self._search_journals = val

    def __init__(self, scientist, year, year_margin=1, pub_margin=0.1,
                 coauth_margin=0.1, refresh=False):
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

        year_margin : numeric (optional, default=1)
            Number of years by which the search for authors publishing around
            the year of the focal scientist's year of first publication should
            be extend in both directions.

        pub_margin : numeric (optional, default=0.1)
            The left and right margin for the number of publications to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of publications.

        coauth_margin : numeric (optional, default=0.1)
            The left and right margin for the number of coauthors to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            coauthors and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of coauthors.

        refresh : boolean (optional, default=False)
            Whether to refresh all cached files or not.
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
        self.year_margin = year_margin
        self.pub_margin = pub_margin
        self.coauth_margin = coauth_margin
        self.refresh = refresh

    year_margin = property(attrgetter('_year_margin'))
    @year_margin.setter
    def year_margin(self, val):
        if not isinstance(val, (int, float)):
            raise Exception("Value must be float or integer.")
        self._year_margin = int(val)

    pub_margin = property(attrgetter('_pub_margin'))
    @pub_margin.setter
    def pub_margin(self, val):
        if not isinstance(val, (int, float)):
            raise Exception("Value must be float or integer.")
        self._pub_margin = val

    coauth_margin = property(attrgetter('_coauth_margin'))
    @coauth_margin.setter
    def coauth_margin(self, val):
        if not isinstance(val, (int, float)):
            raise Exception("Value must be float or integer.")
        self._coauth_margin = val

    def define_search_groups(self):
        """Define search groups: search_group_today, search_group_then
        and search_group_negative.
        """
        if not self.search_journals:
            text = "No search journals defined.  Please run "\
                   ".define_search_journals() first."
            raise Exception(text)
        # Today
        today = _find_search_group(self.search_journals, [self.year],
                                   refresh=self.refresh)
        self._search_group_today = today
        # Then
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
        then = _find_search_group(self.search_journals, _years,
                                  refresh=self.refresh)
        self._search_group_then = then
        # Negative
        try:
            _npapers = _get_value_range(len(self.publications), self.pub_margin)
        except TypeError:
            raise ValueError('Value pub_margin must be float or integer.')
        max_pubs = max(_npapers)
        too_young = set()
        authors = []
        _min = self.first_year-self.year_margin
        for journal in self.search_journals:
            q = 'SOURCE-ID({})'.format(journal)
            try:
                docs = _query_docs(q, refresh=self.refresh)
                res1 = [p for p in docs if int(p.coverDate[:4]) < _min]
                res2 = [p for p in docs if int(p.coverDate[:4]) < self.year]
            except Exception as e:
                # Do not run year-wise queries for this group
                continue
            # Authors publishing too early
            new = [x.authid.split(';') for x in res1 if isinstance(x.authid, str)]
            too_young.update([au for sl in new for au in sl])
            # Author count
            new = [x.authid.split(';') for x in res2 if isinstance(x.authid, str)]
            authors.extend([au for sl in new for au in sl])
        too_many = {a for a, npubs in Counter(authors).items()
                    if npubs > max_pubs}
        self._search_group_negative = too_young.union(too_many)

    def define_search_journals(self):
        """Define search journals: Journals whose authors will be
        considered as possible matches.
        """
        df = self.field_journal
        # Select types of journals of scientist's publications in main field
        mask = (df['source_id'].isin(self.journals)) &\
               (df['asjc'] == self.main_field[0])
        main_types = set(df[mask]['type'])
        # Select journals in scientist's main field
        mask = (df['asjc'] == self.main_field[0]) & (df['type'].isin(main_types))
        journals = df[mask]['source_id'].tolist()
        sel = df[df['source_id'].isin(journals)].copy()
        sel['asjc'] = sel['asjc'].astype(str) + " "
        grouped = sel.groupby('source_id').sum()['asjc'].to_frame()
        # Deselect journals with alien fields
        grouped['drop'] = grouped['asjc'].apply(
            lambda s: any(x for x in s.split() if int(x) not in self.fields))
        self._search_journals = grouped[~grouped['drop']].index.tolist()

    def find_matches(self, stacked=False):
        """Find matches from a search group based on three criteria:
        1. Started publishing in about the same year
        2. Has about the same number of publications in the year of treatment
        3. Has about the same number of coauthors in the year of treatment
        The search group is defined as intersection of `search_group_today`
        and `search_group_then`, minus `search_group_negative`.

        Parameters
        ----------
        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files with most likely not be resuable.  Set to true if you
            query in distinct fields or you want to minimize API key usage.
        """
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year-self.year_margin+1)
        _npapers = _get_value_range(len(self.publications), self.pub_margin)
        _ncoauth = _get_value_range(len(self.coauthors), self.coauth_margin)

        # Define search group
        group = self.search_group_then.intersection(self.search_group_today)
        group = sorted(list(group - self.search_group_negative))

        # First stage of filtering: minimum publications and main field
        df = pd.DataFrame()
        for chunk in _chunker(group, floor((MAX_LENGTH-30)/27)):
            while len(chunk) > 0:
                half = floor(len(chunk)/2)
                try:
                    q = "AU-ID(" + ") OR AU-ID(".join(chunk) + ")"
                    df = df.append(_query_author(q))
                    chunk = []
                except:  # Rerun query with half the list
                    q = "AU-ID(" + ") OR AU-ID(".join(chunk[:half]) + ")"
                    df = df.append(_query_author(q))
                    chunk = chunk[half:]
        df = df[df['areas'].str.startswith(self.main_field[1])]
        df['documents'] = pd.to_numeric(df['documents'], errors='coerce').fillna(0)
        df = df[df['documents'].astype(int) >= min(_npapers)]

        # Second round of filtering
        df['id'] = df['eid'].str.split('-').str[-1]
        group = df['id'].tolist()
        keep = []
        if stacked:  # Combine searches
            d = {}
            y = self.first_year
            for chunk in _chunker(group, floor((MAX_LENGTH-21-30)/27)):
                while len(chunk) > 0:
                    h = floor(len(chunk)/2)
                    try:
                        q = "AU-ID({}) AND PUBYEAR BEF {}".format(
                            ") OR AU-ID(".join(chunk), cur_year+1)
                        d.update(_build_dict(_query_docs(q), y))
                        chunk = []
                    except Exception as e:  # Rerun query with half the list
                        q = "AU-ID({}) AND PUBYEAR BEF {}".format(
                            ") OR AU-ID(".join(chunk[:h]), cur_year+1)
                        d.update(_build_dict(_query_docs(q), y))
                        chunk = chunk[h:]
            # Iterate through container
            for auth, dat in d.items():
                if (dat['pub_year'] in _years and dat['n_pubs'] in
                        _npapers and len(dat['coauth']) in _ncoauth):
                    keep.append(auth)
        else:  # Query each author individually
            for au in group:
                res = _query_docs('AU-ID({})'.format(au), refresh=self.refresh)
                res = [p for p in res if int(p.coverDate[:4]) < self.year+1]
                # Filter based on age (first publication year)
                min_year = int(min([p.coverDate[:4] for p in res]))
                if min_year not in _years:
                    continue
                # Filter based on number of publications in t
                if len(res) not in _npapers:
                    continue
                # Filter based on number of coauthors
                coauth = set([a for p in res for a in p.authid.split(';')])
                coauth.remove(au)
                if len(coauth) not in _ncoauth:
                    continue
                keep.append(au)
        return keep


def _build_dict(results, year):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
    d = defaultdict(lambda: {'pub_year': year, 'n_pubs': 0, 'coauth': set()})
    for pub in results:
        authors = set(pub.authid.split(';'))
        try:
            focal = next(iter(authors.intersection(chunk)))
        except StopIteration:
            continue
        authors.remove(focal)
        d[focal]['coauth'].update(authors)
        d[focal]['n_pubs'] += 1
        pub_year = int(pub.coverDate[:4])
        d[focal]['pub_year'] = min(d[focal]['pub_year'], pub_year)
    return d


def _chunker(l, n):
    """Auxiliary function to break a list into chunks of at most size n"""
    # From https://stackoverflow.com/a/312464/3621464
    for i in range(0, len(l), n):
        yield l[i:i+n]


def _find_search_group(journals, years, refresh=False):
    """Auxiliary function to query multiple journals and years."""
    authors = set()
    for j in journals:
        q = 'SOURCE-ID({})'.format(j)
        try:  # Try complete publication list first
            res = _query_docs(q, refresh=refresh)
            res = [p for p in res if int(p.coverDate[:4]) in years]
        except:  # Fall back to year-wise queries
            for y in years:
                q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(j, y)
                res = _query_docs(q, refresh=refresh)
        new = [x.authid.split(';') for x in res if isinstance(x.authid, str)]
        authors.update([au for sl in new for au in sl])
    return authors


def _query_author(q, refresh=False):
    """Auxiliary function to perform a search query for authors."""
    try:
        return sco.AuthorSearch(q, refresh=False).authors
    except KeyError:
        return sco.AuthorSearch(q, refresh=True).authors


def _query_docs(q, refresh=False):
    """Auxiliary function to perform a search query for documents."""
    try:
        return sco.ScopusSearch(q, refresh=refresh).results
    except KeyError:
        return sco.ScopusSearch(q, refresh=True).results


def _get_value_range(base, val):
    """Auxiliary function to create a range of margins around a base value."""
    if isinstance(val, float):
        margin = ceil(val*base)
        r = range(base-margin, base+margin+1)
    elif isinstance(val, int):
        r = range(base-margin, base+margin+1)
    return r
