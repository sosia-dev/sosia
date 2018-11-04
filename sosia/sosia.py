#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import Counter, defaultdict
from math import ceil, floor, log
from os.path import exists

import pandas as pd
import scopus as sco

from sosia.utils import ASJC_2D, FIELDS_SOURCES_LIST

MAX_LENGTH = 3893  # Maximum character length of a query


class Original(object):
    @property
    def country(self):
        """Country of the scientist's most frequent affiliation
        in the most recent year (before the given year) that
        the scientist published.
        """
        return self._country

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
        return self._coauthors

    @coauthors.setter
    def coauthors(self, val):
        if not isinstance(val, set) or len(val) == 0:
            raise Exception("Value must be a non-empty set.")
        self._coauthors = val

    @property
    def fields(self):
        """The fields of the scientist until the given year, estimated from
        the sources (journals, books, etc.) she published in.
        """
        return self._fields

    @fields.setter
    def fields(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
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
    def publications(self):
        """The publications of the scientist published until
        the given year.
        """
        return self._publications

    @publications.setter
    def publications(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
        self._publications = val

    @property
    def search_group_then(self):
        """Authors of publications in sources in the scientist's field
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
        """Authors of publications in sources in the scientist's field
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
        sources already in the given year and authors of publications
        in sources in the scientist's field before the year of the
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
    def search_sources(self):
        """The set of sources (journals, books) comparable to the sources
        the scientist published in until the given year.
        A sources is comparable if is belongs to the scientist's main field
        but not to fields alien to the scientist, and if the types of the
        sources are the same as the types of the sources in the scientist's
        main field where she published in.

        Notes
        -----
        Property is initiated via .define_search_sources().
        """
        try:
            return self._search_sources
        except AttributeError:
            return None

    @search_sources.setter
    def search_sources(self, val):
        if not isinstance(val, list) or len(val) == 0:
            raise Exception("Value must be a non-empty list.")
        self._search_sources = val

    @property
    def sources(self):
        """The Scopus IDs of sources (journals, books) in which the
        scientist published until the given year.
        """
        return self._sources

    @sources.setter
    def sources(self, val):
        if not isinstance(val, set) or len(val) == 0:
            raise Exception("Value must be a non-empty set.")
        self._sources = val

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
        # Check for existence of fields-sources list
        try:
            self.field_source = pd.read_csv(FIELDS_SOURCES_LIST)
            df = self.field_source
        except FileNotFoundError:
            text = "Fields-Journals list not found, but required for sosia "\
                   "to match authors' publications to fields.  Please run "\
                   "sosia.create_fields_sources_list() and initiate "\
                   "the class again."
            raise Exception(text)

        # Internal checks
        if not isinstance(year, int):
            raise Exception("Argument year must be an integer.")
        if not isinstance(year_margin, (int, float)):
            raise Exception("Argument year_margin must be float or integer.")
        if not isinstance(pub_margin, (int, float)):
            raise Exception("Argument pub_margin must be float or integer.")
        if not isinstance(coauth_margin, (int, float)):
            raise Exception("Argument coauth_margin must be float or integer.")

        # Variables
        self.id = str(scientist)
        self.year = int(year)
        self.year_margin = year_margin
        self.pub_margin = pub_margin
        self.coauth_margin = coauth_margin
        self.refresh = refresh

        # Own information
        res = _query_docs('AU-ID({})'.format(self.id), refresh=self.refresh)
        self._publications = [p for p in res if int(p.coverDate[:4]) < self.year]
        if len(self._publications) == 0:
            text = "No publications for author {} until year {}".format(
                self.id, self.year)
            raise Exception(text)
        self._sources = set([p.source_id for p in self._publications])
        self._fields = df[df['source_id'].isin(self._sources)]['asjc'].tolist()
        main = Counter(self._fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        self._main_field = (main, ASJC_2D[code])
        self._first_year = int(min([p.coverDate[:4] for p in self._publications]))
        self._coauthors = set([a for p in self._publications
                              for a in p.authid.split(';')])
        self._coauthors.remove(self.id)
        self._country = _find_country(self.id, self._publications,
                                      self.year, self._first_year)

    def define_search_groups(self, verbose=False):
        """Define search groups: search_group_today, search_group_then
        and search_group_negative.

        Parameters
        ----------
        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.
        """
        if not self.search_sources:
            text = "No search sources defined.  Please run "\
                   ".define_search_sources() first."
            raise Exception(text)
        # Today
        if verbose:
            print("Searching authors for search_group_today in {} "\
                  "sources".format(len(self.search_sources)))
        today = _find_search_group(self.search_sources, [self.year],
                                   refresh=self.refresh, verbose=verbose)
        self._search_group_today = today
        if verbose:
            print("Found {:,} authors".format(len(today)))
        # Then
        if verbose:
            print("Searching authors for search_group_then in {} "\
                  "sources".format(len(self.search_sources)))
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
        then = _find_search_group(self.search_sources, _years,
                                  refresh=self.refresh, verbose=verbose)
        self._search_group_then = then
        if verbose:
            print("Found {:,} authors".format(len(then)))
        # Negative
        try:
            _npapers = _get_value_range(len(self.publications), self.pub_margin)
        except TypeError:
            raise ValueError('Value pub_margin must be float or integer.')
        if verbose:
            print("Searching authors for search_group_negative in {} "\
                  "sources".format(len(self.search_sources)))
        max_pubs = max(_npapers)
        too_young = set()
        authors = []
        _min = self.first_year-self.year_margin
        n = len(self.search_sources)
        if verbose:
            _print_progress(0, n)
        for i, source in enumerate(self.search_sources):
            q = 'SOURCE-ID({})'.format(source)
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
            if verbose:
                _print_progress(i+1, n)
        too_many = {a for a, npubs in Counter(authors).items()
                    if npubs > max_pubs}
        self._search_group_negative = too_young.union(too_many)
        if verbose:
            print("Found {:,} authors for search_group_negative".format(
                len(self._search_group_negative)))

    def define_search_sources(self, verbose=False):
        """Define .search_sources.

        Parameters
        ----------
        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.
        """
        df = self.field_source
        # Select types of sources of scientist's publications in main field
        mask = (df['source_id'].isin(self.sources)) &\
               (df['asjc'] == self.main_field[0])
        main_types = set(df[mask]['type'])
        # Select sources in scientist's main field
        mask = (df['asjc'] == self.main_field[0]) & (df['type'].isin(main_types))
        sources = df[mask]['source_id'].tolist()
        sel = df[df['source_id'].isin(sources)].copy()
        sel['asjc'] = sel['asjc'].astype(str) + " "
        grouped = sel.groupby('source_id').sum()['asjc'].to_frame()
        # Deselect sources with alien fields
        grouped['drop'] = grouped['asjc'].apply(
            lambda s: any(x for x in s.split() if int(x) not in self.fields))
        self._search_sources = grouped[~grouped['drop']].index.tolist()
        if verbose:
            types = "; ".join(list(main_types))
            print("Found {} sources for main field {} and source"\
                  " type(s) {}".format(len(self._search_sources),
                                       self.main_field[0], types))

    def find_matches(self, stacked=False, verbose=False):
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

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.
        """
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year-self.year_margin+1)
        _npapers = _get_value_range(len(self.publications), self.pub_margin)
        _ncoauth = _get_value_range(len(self.coauthors), self.coauth_margin)

        # Define search group
        group = self.search_group_then.intersection(self.search_group_today)
        group = sorted(list(group - self.search_group_negative))
        n = len(group)
        if verbose:
            print("Searching through characteristics of {:,} authors".format(n))

        # First stage of filtering: minimum publications and main field
        df = pd.DataFrame()
        i = 0
        if verbose:
            print("Pre-filtering...")
            _print_progress(i, n)
        for chunk in _chunker(group, floor((MAX_LENGTH-30)/27)):
            while len(chunk) > 0:
                half = floor(len(chunk)/2)
                try:
                    q = "AU-ID(" + ") OR AU-ID(".join(chunk) + ")"
                    df = df.append(_query_author(q))
                    if verbose:
                        i += len(chunk)
                        _print_progress(i, n)
                    chunk = []
                except:  # Rerun query with half the list
                    q = "AU-ID(" + ") OR AU-ID(".join(chunk[:half]) + ")"
                    df = df.append(_query_author(q))
                    if verbose:
                        i += len(chunk[:half])
                        _print_progress(i, n)
                    chunk = chunk[half:]
        df = df[df['areas'].str.startswith(self.main_field[1])]
        df['documents'] = pd.to_numeric(df['documents'], errors='coerce').fillna(0)
        df = df[df['documents'].astype(int) >= min(_npapers)]
        n = df.shape[0]
        if verbose:
            print("Left with {} authors".format(n))

        # Second round of filtering
        df['id'] = df['eid'].str.split('-').str[-1]
        group = sorted(df['id'].tolist())
        keep = []
        if verbose:
            print("Filtering based on provided conditions...")
            i = 0
            _print_progress(0, n)
        if stacked:  # Combine searches
            d = {}
            f = self.first_year
            for chunk in _chunker(group, floor((MAX_LENGTH-21-30)/27)):
                while len(chunk) > 0:
                    h = floor(len(chunk)/2)
                    try:
                        q = "AU-ID({}) AND PUBYEAR BEF {}".format(
                            ") OR AU-ID(".join(chunk), self.year+1)
                        new = _query_docs(q, refresh=self.refresh)
                        d.update(_build_dict(new, f, chunk))
                        if verbose:
                            i += len(chunk)
                            _print_progress(i, n)
                        chunk = []
                    except Exception as e:  # Rerun query with half the list
                        q = "AU-ID({}) AND PUBYEAR BEF {}".format(
                            ") OR AU-ID(".join(chunk[:h]), self.year+1)
                        new = _query_docs(q, refresh=self.refresh)
                        d.update(_build_dict(new, f, chunk))
                        if verbose:
                            i += len(chunk)
                            _print_progress(i, n)
                        chunk = chunk[h:]
            # Iterate through container
            for auth, dat in d.items():
                if (dat['pub_year'] in _years and dat['n_pubs'] in
                        _npapers and len(dat['coauth']) in _ncoauth):
                    keep.append(auth)
        else:  # Query each author individually
            for i, au in enumerate(group):
                if verbose:
                    _print_progress(i+1, n)
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
        if verbose:
            print("Found {:,} author(s) matching all criteria".format(len(keep)))
        return keep


def _build_dict(results, year, chunk):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
    d = defaultdict(lambda: {'pub_year': year, 'n_pubs': 0, 'coauth': set()})
    for pub in results:
        authors = set(pub.authid.split(';'))
        for focal in authors.intersection(chunk):
            authors.remove(focal)
            d[focal]['coauth'].update(authors)
            d[focal]['n_pubs'] += 1
            pub_year = int(pub.coverDate[:4])
            d[focal]['pub_year'] = min(d[focal]['pub_year'], pub_year)
            authors.add(focal)
    return d


def _chunker(l, n):
    """Auxiliary function to break a list into chunks of at most size n"""
    # From https://stackoverflow.com/a/312464/3621464
    for i in range(0, len(l), n):
        yield l[i:i+n]


def _get_value_range(base, val):
    """Auxiliary function to create a range of margins around a base value."""
    if isinstance(val, float):
        margin = ceil(val*base)
        r = range(base-margin, base+margin+1)
    elif isinstance(val, int):
        r = range(base-margin, base+margin+1)
    return r


def _find_country(auth_id, pubs, year, first_year):
    """Auxiliary function to find the country of the most recent affiliation
    of a scientist.
    """
    # List of relevant papers
    papers = []
    max_iter = year - first_year + 1
    i = 0
    while len(papers) == 0 & i <= max_iter:
        papers = [p for p in pubs if int(p.coverDate[:4]) == year-i]
        i += 1
    if len(papers) == 0:
        return None
    # List of affiliations
    affs = []
    for p in papers:
        authors = p.authid.split(';')
        idx = authors.index(str(auth_id))
        aff = p.afid.split(';')[idx].split('-')
        affs.extend(aff)
    affs = [a for a in affs if a != '']
    # Find countries of affiliations
    countries = [sco.ContentAffiliationRetrieval(afid).country
                 for afid in affs]
    return Counter(countries).most_common(1)[0][0]


def _find_search_group(sources, years, refresh=False, verbose=False):
    """Auxiliary function to query multiple sources and years."""
    authors = set()
    n = len(sources)
    if verbose:
        _print_progress(0, n)
    for i, s in enumerate(sources):
        q = 'SOURCE-ID({})'.format(s)
        try:  # Try complete publication list first
            res = _query_docs(q, refresh=refresh)
            res = [p for p in res if int(p.coverDate[:4]) in years]
        except:  # Fall back to year-wise queries
            for y in years:
                q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(s, y)
                res = _query_docs(q, refresh=refresh)
        new = [x.authid.split(';') for x in res if isinstance(x.authid, str)]
        authors.update([au for sl in new for au in sl])
        if verbose:
            _print_progress(i+1, n)
    return authors


def _print_progress(iteration, total, prefix='Progress:', suffix='Complete',
                    decimals=2, length=50, fill='█'):
    """Print terminal progress bar."""
    percent = round(100 * (iteration / float(total)), decimals)
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    if iteration == total:
        print()


def _query_author(q, refresh=False):
    """Auxiliary function to perform a search query for authors."""
    try:
        return sco.AuthorSearch(q, refresh=refresh).authors
    except KeyError:
        return sco.AuthorSearch(q, refresh=True).authors


def _query_docs(q, refresh=False):
    """Auxiliary function to perform a search query for documents."""
    try:
        return sco.ScopusSearch(q, refresh=refresh).results
    except KeyError:
        return sco.ScopusSearch(q, refresh=True).results
