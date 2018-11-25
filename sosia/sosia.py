#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import Counter, defaultdict, namedtuple
from functools import partial
from math import inf, log
from os.path import exists
from string import digits, punctuation, Template

import pandas as pd
import scopus as sco
from nltk import snowball, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.utils import (ASJC_2D, FIELDS_SOURCES_LIST, clean_abstract,
    compute_cosine, margin_range, print_progress, raise_non_empty, query)

STOPWORDS = list(ENGLISH_STOP_WORDS)
STOPWORDS.extend(punctuation + digits)
_stemmer = snowball.SnowballStemmer('english')


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
    def search_group(self):
        """The set of authors that might be matches to the scientist.  The
        set contains the intersection of all authors publishing in the given
        year as well as authors publishing around the year of first
        publication.  Some authors with too many publications in the given
        year and authors having published too early are removed.

        Notes
        -----
        Property is initiated via .define_search_group().
        """
        try:
            return self._search_group
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
        raise_non_empty(val, list)
        self._search_sources = val

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
            text = "Fields-Sources list not found, but required for sosia "\
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
        res = query("docs", 'AU-ID({})'.format(self.id), self.refresh)
        self._publications = [p for p in res if int(p.coverDate[:4]) < self.year]
        if len(self._publications) == 0:
            text = "No publications for author {} until year {}".format(
                self.id, self.year)
            raise Exception(text)
        self._sources = set([int(p.source_id) for p in self._publications])
        self._fields = df[df['source_id'].isin(self._sources)]['asjc'].tolist()
        main = Counter(self._fields).most_common(1)[0][0]
        code = main // 10 ** (int(log(main, 10)) - 2 + 1)
        self._main_field = (main, ASJC_2D[code])
        self._first_year = int(min([p.coverDate[:4] for p in self._publications]))
        self._coauthors = set([a for p in self._publications
                              for a in p.authid.split(';')])
        self._coauthors.remove(self.id)
        self._country = _find_country(self.id, self._publications, self.year)

    def define_search_group(self, stacked=False, verbose=False, refresh=False):
        """Define search_group.

        Parameters
        ----------
        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files with most likely not be resuable.  Set to True if you
            query in distinct fields or you want to minimize API key usage.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            Whether to refresh cached search files.
        """
        # Checks
        if not self.search_sources:
            text = "No search sources defined.  Please run "\
                   ".define_search_sources() first."
            raise Exception(text)

        # Variables
        today = set()
        then = set()
        negative = set()
        auth_count = []
        _min_year = self.first_year-self.year_margin
        _max_pubs = max(margin_range(len(self.publications), self.pub_margin))
        _years = list(range(_min_year, self.first_year+self.year_margin+1))
        n = len(self.search_sources)

        # Query journals
        if stacked:
            params = {"group": [str(x) for x in sorted(self.search_sources)],
                      "joiner": ") OR SOURCE-ID(", "refresh": refresh,
                      "func": partial(query, "docs")}
            if verbose:
                params.update({"total": n})
                print("Searching authors in {} sources in {}...".format(
                        len(self.search_sources), self.year))
            # Today
            q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(self.year))
            params.update({'query': q, "res": []})
            today.update(_get_authors(_stacked_query(**params)[0]))
            # Then
            if len(_years) == 1:
                q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(
                    _years[0]))
                if verbose:
                    print("Searching authors in {} sources in {}...".format(
                        len(self.search_sources), _years[0]))
            else:
                _min = min(_years)-1
                _max = max(_years)+1
                q = Template("SOURCE-ID($fill) AND PUBYEAR AFT {} AND "
                             "PUBYEAR BEF {}".format(_min, _max))
                if verbose:
                    print("Searching authors in {} sources in {}-{}...".format(
                        len(self.search_sources), _min+1, _max-1))
            params.update({'query': q, "res": []})
            then.update(_get_authors(_stacked_query(**params)[0]))
            # Negative
            if verbose:
                print("Searching authors in {} sources in {}...".format(
                        len(self.search_sources), _min_year-1))
            q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(_min_year-1))
            params.update({'query': q, "res": []})
            negative.update(_get_authors(_stacked_query(**params)[0]))
        else:
            if verbose:
                print("Searching authors for search_group in {} "
                      "sources...".format(len(self.search_sources)))
                print_progress(0, n)
            for i, s in enumerate(self.search_sources):
                try:  # Try complete publication list first
                    res = query("docs", 'SOURCE-ID({})'.format(s), refresh)
                    pubs = [p for p in res if int(p.coverDate[:4]) == self.year]
                    today.update(_get_authors(pubs))
                    pubs = [p for p in res if int(p.coverDate[:4]) in _years]
                    then.update(_get_authors(pubs))
                    pubs = [p for p in res if int(p.coverDate[:4]) < _min_year]
                    negative.update(_get_authors(pubs))
                    pubs = [p for p in res if int(p.coverDate[:4]) < self.year+1]
                    auth_count.extend(_get_authors(pubs))
                except:  # Fall back to year-wise queries
                    q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(s, self.year)
                    today.update(_get_authors(query("docs", q, refresh)))
                    for y in _years:
                        q = 'SOURCE-ID({}) AND PUBYEAR IS {}'.format(s, y)
                        try:
                            pubs = query("docs", q, refresh)
                        except Exception as e:  # Too many publications
                            continue
                        new = [x.authid.split(';') for x in pubs
                               if isinstance(x.authid, str)]
                        then.update([au for sl in new for au in sl])
                if verbose:
                    print_progress(i+1, n)

        # Finalize
        group = today.intersection(then)
        negative.update({a for a, npubs in Counter(auth_count).items()
                         if npubs > _max_pubs})
        self._search_group = sorted(list(group - negative))
        if verbose:
            print("Found {:,} authors for search_group".format(
                len(self._search_group)))
        return self

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
        # Add own sources
        sources = set(grouped[~grouped['drop']].index.tolist())
        sources.update(set(self.sources))
        self._search_sources = sorted(list(sources))
        if verbose:
            types = "; ".join(list(main_types))
            print("Found {} sources for main field {} and source "
                  "type(s) {}".format(len(self._search_sources),
                                      self.main_field[0], types))
        return self

    def find_matches(self, stacked=False, verbose=False, refresh=False,
                     **kwds):
        """Find matches within search_group based on three criteria:
        1. Started publishing in about the same year
        2. Has about the same number of publications in the year of treatment
        3. Has about the same number of coauthors in the year of treatment
        4. Affiliation was in the same country in the year of treatment

        Parameters
        ----------
        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files with most likely not be resuable.  Set to True if you
            query in distinct fields or you want to minimize API key usage.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            Whether to refresh cached search files.

        kwds : keywords
            Parameters to pass to TfidfVectorizer for abstract vectorization.
        """
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year-self.year_margin+1)
        _npapers = margin_range(len(self.publications), self.pub_margin)
        _ncoauth = margin_range(len(self.coauthors), self.coauth_margin)
        if verbose:
            n = len(self.search_group)
            print("Searching through characteristics of {:,} authors".format(n))

        # First round of filtering: minimum publications and main field
        params = {"group": self.search_group, "res": [], "refresh": refresh,
                  "joiner": ") OR AU-ID(", "func": partial(query, "author"),
                  "query": Template("AU-ID($fill)")}
        if verbose:
            print("Pre-filtering...")
            params.update({'total': n})
        res, _ = _stacked_query(**params)
        group = [pub.eid.split('-')[-1] for pub in res
                 if pub.areas.startswith(self.main_field[1])
                 and pub.documents >= str(min(_npapers))]
        group.sort()
        if verbose:
            n = len(group)
            print("Left with {} authors\nFiltering based on provided "
                  "conditions...".format(n))

        # Second round of filtering: All other conditions
        keep = defaultdict(list)
        if stacked:  # Combine searches
            q = Template("AU-ID($fill) AND PUBYEAR BEF {}".format(self.year+1))
            params = {"group": group, "res": [], "query": q, "refresh": refresh,
                      "joiner": ") OR AU-ID(", "func": partial(query, "docs")}
            if verbose:
                params.update({"total": n})
            res, _ = _stacked_query(**params)
            container = _build_dict(res, group)
            # Iterate through container in order to filter results
            for auth, dat in container.items():
                dat['n_coauth'] = len(dat['coauth'])
                dat['n_pubs'] = len(dat['pubs'])
                if (dat['first_year'] in _years and dat['n_pubs'] in
                        _npapers and dat['n_coauth'] in _ncoauth):
                    keep['ID'].append(auth)
                    for key, val in dat.items():
                        keep[key].append(val)
        else:  # Query each author individually
            for i, au in enumerate(group):
                if verbose:
                    print_progress(i+1, n)
                res = query("docs", 'AU-ID({})'.format(au), refresh)
                res = [p for p in res if int(p.coverDate[:4]) < self.year+1]
                # Filter
                min_year = int(min([p.coverDate[:4] for p in res]))
                authors = set([a for p in res for a in p.authid.split(';')])
                n_coauth = len(authors) - 1  # Subtract 1 for focal author
                if ((len(res) not in _npapers) or (min_year not in _years) or
                        (n_coauth not in _ncoauth)):
                    continue
                # Collect information
                info = [('n_pubs', len(res)), ('n_coauth', n_coauth),
                        ('ID', au), ('first_year', min_year)]
                for key, val in info:
                    keep[key].append(val)
        if verbose:
            print("Found {:,} author(s) matching all criteria\nAdding "
                  "other information...".format(len(keep['ID'])))

        # Add other information
        profiles = [sco.AuthorRetrieval(auth, refresh) for auth in keep['ID']]
        names = [", ".join([p.surname, p.given_name]) for p in profiles]
        countries = [_find_country(au, year=self.year,
                        pubs=query("docs", 'AU-ID({})'.format(au), refresh))
                     for au in keep['ID']]
        tokens = [_get_refs(au, self.year, refresh, verbose) for au
                  in keep['ID'] + [self.id]]
        ref_m = TfidfVectorizer().fit_transform([t['refs'] for t in tokens])
        vectorizer = TfidfVectorizer(stop_words=STOPWORDS,
            tokenizer=_tokenize_and_stem, **kwds)
        abs_m = vectorizer.fit_transform([t['abstracts'] for t in tokens])

        # Merge information into namedtuple
        t = zip(keep['ID'], names, keep['first_year'], keep['n_coauth'],
                keep['n_pubs'], countries, compute_cosine(ref_m),
                compute_cosine(abs_m))
        fields = "ID name first_year num_coauthors num_publications country "\
                 "reference_sim abstract_sim"
        match = namedtuple("Match", fields)
        return [match(*tup) for tup in list(t)]


def _build_dict(results, chunk):
    """Create dictionary assigning publication information to authors we
    are looking for.
    """
    d = defaultdict(lambda: {'first_year': inf, 'pubs': set(), 'coauth': set()})
    for pub in results:
        authors = set(pub.authid.split(';'))
        for focal in authors.intersection(chunk):
            d[focal]['coauth'].update(authors)
            d[focal]['coauth'].remove(focal)
            d[focal]['pubs'].add(pub.eid)
            first_year = min(d[focal]['first_year'], int(pub.coverDate[:4]))
            d[focal]['first_year'] = first_year
    return d


def _run(op, *args):
    """Auxiliary function to call a function passed by partial()."""
    return op(*args)


def _stacked_query(group, res, query, joiner, func, refresh, i=0, total=None):
    """Auxiliary function to recursively perform queries until they work.

    Results of each successful query are appended to ´res´.
    """
    try:
        q = query.substitute(fill=joiner.join(group))
        res.extend(_run(func, q, refresh))
        if total:  # Equivalent of verbose
            i += len(group)
            print_progress(i, total)
    except Exception as e:  # Catches two exceptions (long URL + many results)
        mid = len(group) // 2
        params = {"group": group[:mid], "res": res, "query": query, "i": i,
                  "joiner": joiner, "func": func, "total": total,
                  "refresh": refresh}
        res, i = _stacked_query(**params)
        params.update({"group": group[mid:], "i": i})
        res, i = _stacked_query(**params)
    return res, i


def _get_authors(pubs):
    """Auxiliary function to get list of author IDs from a list of
    namedtuples representing publications.
    """
    l = [x.authid.split(';') for x in pubs if isinstance(x.authid, str)]
    return [au for sl in l for au in sl]


def _get_refs(au, year, refresh, verbose):
    """Auxiliary function to return abstract and references of articles
    published up until the given year, both as continuous string.
    """
    res = query("docs", "AU-ID({})".format(au), refresh)
    eids = [p.eid for p in res if int(p.coverDate[:4]) <= year]
    docs = [sco.AbstractRetrieval(eid, view='FULL', refresh=refresh)
            for eid in eids]
    # Filter None's
    absts = [clean_abstract(ab.abstract) for ab in docs if ab.abstract]
    refs = [ab.references for ab in docs if ab.references]
    if verbose:
        miss_abs = len(eids) - len(absts)
        miss_refs = len(eids) - len(refs)
        print("Researcher {}: {} abstract(s) and {} reference list(s) out of "
              "{} documents missing".format(au, miss_abs, miss_refs, len(eids)))
    return {'refs': " ".join([ref.id for sl in refs for ref in sl]),
            'abstracts': " ".join(absts)}


def _find_country(auth_id, pubs, year):
    """Auxiliary function to find the country of the most recent affiliation
    of a scientist.
    """
    # Available papers of most recent year with publications
    papers = []
    i = 0
    while len(papers) == 0 & i <= len(pubs):
        papers = [p for p in pubs if int(p.coverDate[:4]) == year-i]
        i += 1
    if len(papers) == 0:
        return None
    # List of affiliations on these papers belonging to the actual author
    affs = []
    for p in papers:
        authors = p.authid.split(';')
        idx = authors.index(str(auth_id))
        aff = p.afid.split(';')[idx].split('-')
        affs.extend(aff)
    affs = [a for a in affs if a != '']
    # Find most often listed country of affiliations
    countries = [sco.ContentAffiliationRetrieval(afid).country
                 for afid in affs]
    return Counter(countries).most_common(1)[0][0]


def _tokenize_and_stem(text):
    """Auxiliary funtion to return stemmed tokens of document"""
    return [_stemmer.stem(t) for t in word_tokenize(text.lower())]
