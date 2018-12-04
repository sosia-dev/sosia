#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import Counter, defaultdict, namedtuple
from functools import partial
from math import inf
from string import digits, punctuation, Template

import scopus as sco
from nltk import snowball, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.classes import Scientist
from sosia.utils import ASJC_2D, FIELDS_SOURCES_LIST, compute_cosine,\
    find_country, margin_range, parse_doc, print_progress, query,\
    raise_non_empty, stacked_query

STOPWORDS = list(ENGLISH_STOP_WORDS)
STOPWORDS.extend(punctuation + digits)
_stemmer = snowball.SnowballStemmer('english')


class Original(Scientist):
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

    def __init__(self, scientist, year, year_margin=1, pub_margin=0.1,
                 coauth_margin=0.1, refresh=False, eids=None):
        """Class to represent a scientist for which we want to find a control
        group.

        Parameters
        ----------
        scientist : str, int or list
            Scopus Author ID, or list of Scopus Author IDs, of the scientist
            you want to find control groups for.

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

        eids : list (optional, default=None)
            A list of scopus EIDs of the publications of the scientist you
            want to find a control for.  If it is provided, the scientist
            properties and the control group are set based on this list of
            publications, instead of the list of publications obtained from
            the Scopus Author ID.
        """
        # Internal checks
        if not isinstance(year_margin, (int, float)):
            raise Exception("Argument year_margin must be float or integer.")
        if not isinstance(pub_margin, (int, float)):
            raise Exception("Argument pub_margin must be float or integer.")
        if not isinstance(coauth_margin, (int, float)):
            raise Exception("Argument coauth_margin must be float or integer.")

        # Variables
        if isinstance(scientist, (int, str)):
            scientist = [scientist]
        self.id = [str(auth_id) for auth_id in scientist]
        self.year = int(year)
        self.year_margin = year_margin
        self.pub_margin = pub_margin
        self.coauth_margin = coauth_margin
        self.eids = eids
        self.refresh = refresh

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.id, year, refresh)

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
                      "joiner": " OR ", "refresh": refresh,
                      "func": partial(query, "docs")}
            if verbose:
                params.update({"total": n})
                print("Searching authors in {} sources in {}...".format(
                        len(self.search_sources), self.year))
            # Today
            q = Template("SOURCE-ID($fill) AND PUBYEAR "
                         "IS {}".format(self.year))
            params.update({'query': q, "res": []})
            today.update(_get_authors(stacked_query(**params)[0]))
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
            then.update(_get_authors(stacked_query(**params)[0]))
            # Negative
            if verbose:
                print("Searching authors in {} sources in {}...".format(
                        len(self.search_sources), _min_year-1))
            q = Template("SOURCE-ID($fill) AND PUBYEAR "
                         "IS {}".format(_min_year-1))
            params.update({'query': q, "res": []})
            negative.update(_get_authors(stacked_query(**params)[0]))
        else:
            if verbose:
                print("Searching authors for search_group in {} "
                      "sources...".format(len(self.search_sources)))
                print_progress(0, n)
            for i, s in enumerate(self.search_sources):
                try:  # Try complete publication list first
                    res = query("docs", 'SOURCE-ID({})'.format(s), refresh)
                    pubs = [p for p in res if
                            int(p.coverDate[:4]) == self.year]
                    today.update(_get_authors(pubs))
                    pubs = [p for p in res if
                            int(p.coverDate[:4]) in _years]
                    then.update(_get_authors(pubs))
                    pubs = [p for p in res if
                            int(p.coverDate[:4]) < _min_year]
                    negative.update(_get_authors(pubs))
                    pubs = [p for p in res if
                            int(p.coverDate[:4]) < self.year+1]
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
        mask = (df['asjc'] == self.main_field[0]) &\
               (df['type'].isin(main_types))
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
        res, _ = stacked_query(**params)
        group = [pub.eid.split('-')[-1] for pub in res
                 if pub.areas.startswith(self.main_field[1]) and
                 pub.documents >= str(min(_npapers))]
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
            res, _ = stacked_query(**params)
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
                if len(res) == 0:
                    continue
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
        names = [", ".join([p.surname or "", p.given_name or ""]) for p in profiles]
        countries = [find_country([au], year=self.year,
                                  pubs=query("docs", 'AU-ID({})'.format(au),
                                             refresh))
                     for au in keep['ID']]
        tokens = [parse_doc(au, self.year, refresh, verbose) for au
                  in keep['ID'] + [s for s in self.id]]
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


def _get_authors(pubs):
    """Auxiliary function to get list of author IDs from a list of
    namedtuples representing publications.
    """
    l = [x.authid.split(';') for x in pubs if isinstance(x.authid, str)]
    return [au for sl in l for au in sl]


def _tokenize_and_stem(text):
    """Auxiliary funtion to return stemmed tokens of document"""
    return [_stemmer.stem(t) for t in word_tokenize(text.lower())]
