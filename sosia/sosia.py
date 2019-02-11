#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import Counter, namedtuple
from functools import partial
from string import digits, punctuation, Template

from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.classes import Scientist
from sosia.utils import build_dict, get_authors, margin_range, parse_doc,\
    print_progress, query, query_journal, raise_non_empty, stacked_query,\
    tfidf_cos

STOPWORDS = list(ENGLISH_STOP_WORDS)
STOPWORDS.extend(punctuation + digits)


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
        _min_year = self.first_year-self.year_margin
        _max_pubs = max(margin_range(len(self.publications), self.pub_margin))
        _years = list(range(_min_year, self.first_year+self.year_margin+1))
        if isinstance(self.search_sources[0], tuple):
            search_sources = [s[0] for s in self.search_sources]
        else:
            search_sources = self.search_sources
        n = len(search_sources)

        # Query journals
        if stacked:
            params = {"group": [str(x) for x in sorted(search_sources)],
                      "joiner": " OR ", "refresh": refresh,
                      "func": partial(query, "docs")}
            if verbose:
                params.update({"total": n})
                print("Searching authors in {} sources in {}...".format(
                      n, self.year))
            # Today
            q = Template("SOURCE-ID($fill) AND PUBYEAR "
                         "IS {}".format(self.year))
            params.update({'query': q, "res": []})
            today = set(get_authors(stacked_query(**params)[0]))
            # Then
            if len(_years) == 1:
                q = Template("SOURCE-ID($fill) AND PUBYEAR IS {}".format(
                    _years[0]))
                if verbose:
                    print("Searching authors in {} sources in {}...".format(
                          n, _years[0]))
            else:
                _min = min(_years)-1
                _max = max(_years)+1
                q = Template("SOURCE-ID($fill) AND PUBYEAR AFT {} AND "
                             "PUBYEAR BEF {}".format(_min, _max))
                if verbose:
                    print("Searching authors in {} sources in {}-{}...".format(
                          n, _min+1, _max-1))
            params.update({'query': q, "res": []})
            then = set(get_authors(stacked_query(**params)[0]))
            # Negative
            if verbose:
                print("Searching authors in {} sources in {}...".format(
                      n, _min_year-1))
            q = Template("SOURCE-ID($fill) AND PUBYEAR "
                         "IS {}".format(_min_year-1))
            params.update({'query': q, "res": []})
            negative = set(get_authors(stacked_query(**params)[0]))
        else:
            today = set()
            then = set()
            negative = set()
            auth_count = []
            if verbose:
                print("Searching authors for search_group in {} "
                      "sources...".format(n))
                print_progress(0, n)
            for i, source_id in enumerate(search_sources):
                d = query_journal(source_id, [self.year] + _years, refresh)
                today.update(d[str(self.year)])
                for y in _years:
                    then.update(d[str(y)])
                for y in range(int(min(d.keys())), _min_year):
                    negative.update(d[str(y)])
                for y in d:
                    if int(y) <= self.year:
                        auth_count.extend(d[str(y)])
                print_progress(i+1, n, verbose)
            negative.update({a for a, npubs in Counter(auth_count).items()
                             if npubs > _max_pubs})

        # Finalize
        group = today.intersection(then)
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
        # Get list of source IDs of scientist's own sources
        if isinstance(list(self.sources)[0], tuple):
            own_source_ids = [s[0] for s in self.sources]
            own_sources = self.sources
        else:
            own_source_ids = self.sources
            own_sources = set((s, self.source_names.get(s)) for s in self.sources)
        # Select sources in scientist's main field
        df = self.field_source
        same_field = df['asjc'] == self.main_field[0]
        # Select sources of same type as those in scientist's main field
        same_sources = same_field & df['source_id'].isin(own_source_ids)
        main_types = set(df[same_sources]['type'])
        same_type = same_field & df['type'].isin(main_types)
        source_ids = df[same_type]['source_id'].unique()
        selected = df[df['source_id'].isin(source_ids)].copy()
        selected['asjc'] = selected['asjc'].astype(str) + " "
        grouped = selected.groupby('source_id').sum()['asjc'].to_frame()
        # Deselect sources with alien fields
        mask = grouped['asjc'].apply(lambda s: any(x for x in s.split() if
                                                   int(x) not in self.fields))
        grouped = grouped[~mask]
        sources = set((s, self.source_names.get(s)) for s in grouped.index)
        # Add own sources
        sources.update(own_sources)
        # Finalize
        self._search_sources = sorted(list(sources))
        if verbose:
            types = "; ".join(list(main_types))
            text = "Found {} sources matching main field {} and type(s) {}".format(
                len(self._search_sources), self.main_field[0], types)
            print(text)
        return self

    def find_matches(self, stacked=False, verbose=False, stop_words=STOPWORDS,
                     refresh=False, **kwds):
        """Find matches within search_group based on four criteria:
        1. Started publishing in about the same year
        2. Has about the same number of publications in the year of treatment
        3. Has about the same number of coauthors in the year of treatment
        4. Works in the same field as the scientist's main field

        Parameters
        ----------
        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files will most likely not be resuable.  Set to True if you
            query in distinct fields or you want to minimize API key usage.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        stop_words : list (optional, default=STOPWORDS)
            A list of words that should be filtered in the analysis of
            abstracts.  Default list is the list of english stopwords
            by nltk, augmented with numbers and interpunctuation.

        refresh : bool (optional, default=False)
            Whether to refresh cached search files.

        kwds : keywords
            Parameters to pass to TfidfVectorizer for abstract vectorization.
        """
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
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
                 if self.main_field[1] in pub.areas.split(" ") and
                 pub.documents >= str(min(_npapers))]
        group.sort()
        n = len(group)
        if verbose:
            print("Left with {} authors\nFiltering based on provided "
                  "conditions...".format(n))

        # Second round of filtering: All other conditions
        matches = []
        if stacked:  # Combine searches
            q = Template("AU-ID($fill) AND PUBYEAR BEF {}".format(self.year+1))
            params = {"group": group, "res": [], "query": q, "refresh": refresh,
                      "joiner": ") OR AU-ID(", "func": partial(query, "docs")}
            if verbose:
                params.update({"total": n})
            res, _ = stacked_query(**params)
            container = build_dict(res, group)
            # Iterate through container and filter results
            for auth, dat in container.items():
                dat['n_coauth'] = len(dat['coauth'])
                dat['n_pubs'] = len(dat['pubs'])
                if (dat['first_year'] in _years and dat['n_pubs'] in
                        _npapers and dat['n_coauth'] in _ncoauth):
                    matches.append(auth)
        else:  # Query each author individually
            for i, au in enumerate(group):
                print_progress(i+1, n, verbose)
                res = query("docs", 'AU-ID({})'.format(au), refresh=refresh)
                res = [p for p in res if p.coverDate and
                       int(p.coverDate[:4]) <= self.year]
                # Filter
                min_year = int(min([p.coverDate[:4] for p in res]))
                authids = [p.author_ids for p in res if p.author_ids]
                authors = set([a for p in authids for a in p.split(';')])
                n_coauth = len(authors) - 1  # Subtract 1 for focal author
                if ((len(res) not in _npapers) or (min_year not in _years) or
                        (n_coauth not in _ncoauth)):
                    continue
                matches.append(au)
        if verbose:
            print("Found {:,} author(s) matching all criteria\nAdding "
                  "other information...".format(len(matches)))

        # Add characteristics
        profiles = [Scientist([auth], self.year, refresh) for auth in matches]
        names = [p.name for p in profiles]
        first_years = [p.first_year for p in profiles]
        n_coauths = [len(p.coauthors) for p in profiles]
        n_pubs = [len(p.publications) for p in profiles]
        countries = [p.country for p in profiles]
        languages = [p.get_publication_languages().language for p in profiles]
        # Add content analysis
        pubs = [[d.eid for d in p.publications] for p in profiles]
        pubs.append([d.eid for d in self.publications])
        tokens = [parse_doc(pub, refresh) for pub in pubs]
        ref_cos = tfidf_cos([d["refs"] for d in tokens], **kwds)
        abs_cos = tfidf_cos([d["abstracts"] for d in tokens],
                            stop_words=stop_words, tokenize=True, **kwds)
        if verbose:
            for auth_id, d in zip(matches, tokens):
                _print_missing_docs(auth_id, d)
            label = ";".join(self.id) + " (focal)"
            _print_missing_docs(label, tokens[-1])  # focal researcher

        # Merge information into namedtuple
        t = zip(matches, names, first_years, n_coauths, n_pubs, countries,
                languages, ref_cos, abs_cos)
        fields = "ID name first_year num_coauthors num_publications country "\
                 "language reference_sim abstract_sim"
        match = namedtuple("Match", fields)
        return [match(*tup) for tup in list(t)]


def _print_missing_docs(auth_id, info):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    print("Researcher {}: {} abstract(s) and {} reference list(s) out of "
          "{} documents missing".format(auth_id, info["miss_abs"],
                                        info["miss_refs"], info["total"]))
