#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import Counter
from itertools import product
from math import inf
from string import digits, punctuation, Template
import pandas as pd

from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.classes import Scientist
from sosia.processing import (get_authors, inform_matches, query,
    query_journal, query_year, stacked_query)
from sosia.utils import (add_source_names, build_dict, custom_print,
    margin_range, print_progress, raise_non_empty, CACHE_SQLITE)
from sosia.cache import (cache_sources, sources_in_cache,
    authors_in_cache, cache_authors, author_year_in_cache, cache_author_year)

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
        raise_non_empty(val, (set, list, tuple))
        if not isinstance(list(val)[0], tuple):
            val = add_source_names(val, self.source_names)
        self._search_sources = val

    def __init__(self, scientist, year, year_margin=1, pub_margin=0.1,
                 coauth_margin=0.1, refresh=False, eids=None,):
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
        self.identifier = [str(auth_id) for auth_id in scientist]
        self.year = int(year)
        self.year_margin = year_margin
        self.pub_margin = pub_margin
        self.coauth_margin = coauth_margin
        self.eids = eids
        self.refresh = refresh

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, year, refresh)

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
        _min_year = self.first_year - self.year_margin
        _max_year = self.first_year + self.year_margin
        _max_pubs = max(margin_range(len(self.publications), self.pub_margin))
        _years = list(range(_min_year, _max_year + 1))
        _years_search = list(range(_min_year, _max_year + 1))
        _years_search.extend([_min_year - 1, self.year])
        search_sources, _ = zip(*self.search_sources)
        n = len(search_sources)

        # create df of sources by year to search
        sources_ys = pd.DataFrame(list(product(search_sources, _years_search)),
                                  columns=["source_id", "year"])
        types = {"source_id": int, "year": int}
        sources_ys.astype(types, inplace=True)
        # merge existing data in cache and separate missing records
        _, sources_ys_search = sources_in_cache(sources_ys, refresh=refresh)

        # Query journals
        text = "Searching authors for search_group in {} sources...".format(n)
        custom_print(text, verbose)
        if stacked:  # Make use of SQL cache
            _years_search = set(sources_ys_search.year.tolist())
            for y in _years_search:
                mask = sources_ys_search.year == y
                _sources_search = sources_ys_search[mask].source_id.tolist()
                res = query_year(y, _sources_search, refresh, verbose)
                if not res.empty:
                    cache_sources(res)
            sources_ys, _ = sources_in_cache(sources_ys, refresh=False)
            # Authors publishing in provided year
            mask = sources_ys.year == self.year
            today = set([au for l in sources_ys[mask].auids.tolist()
                         for au in l])
            # Authors publishing in year(s) of first publication
            mask = sources_ys.year.between(_min_year, _max_year, inclusive=True)
            auids = sources_ys[mask].auids.tolist()
            then = set([au for l in auids for au in l])
            # Authors with too many publications
            auids = sources_ys[sources_ys.year < _min_year].auids.tolist()
            negative = set([au for l in auids for au in l])
        else:
            today = set()
            then = set()
            negative = set()
            auth_count = []
            print_progress(0, n, verbose)
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
                print_progress(i + 1, n, verbose)
            c = Counter(auth_count)
            negative.update({a for a, npub in c.items() if npub > _max_pubs})

        # Finalize
        group = today.intersection(then)
        negative.update({str(i) for i in self.identifier})
        self._search_group = sorted(list(group - negative))
        text = "Found {:,} authors for search_group".format(len(self._search_group))
        custom_print(text, verbose)
        return self

    def define_search_sources(self, verbose=False):
        """Define .search_sources.

        Parameters
        ----------
        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.
        """
        # Get list of source IDs of scientist's own sources
        own_source_ids, _ = zip(*self.sources)
        # Select sources in scientist's main field
        df = self.field_source
        same_field = df["asjc"] == self.main_field[0]
        # Select sources of same type as those in scientist's main field
        same_sources = same_field & df["source_id"].isin(own_source_ids)
        main_types = set(df[same_sources]["type"])
        same_type = same_field & df["type"].isin(main_types)
        source_ids = df[same_type]["source_id"].unique()
        selected = df[df["source_id"].isin(source_ids)].copy()
        selected["asjc"] = selected["asjc"].astype(str) + " "
        grouped = selected.groupby("source_id").sum()["asjc"].to_frame()
        # Deselect sources with alien fields
        mask = grouped["asjc"].apply(
            lambda s: any(x for x in s.split() if int(x) not in self.fields)
        )
        grouped = grouped[~mask]
        sources = set((s, self.source_names.get(s)) for s in grouped.index)
        # Add own sources
        sources.update(self.sources)
        # Finalize
        self._search_sources = sorted(list(sources))
        types = "; ".join(list(main_types))
        text = "Found {} sources matching main field {} and type(s) {}".format(
            len(self._search_sources), self.main_field[0], types
        )
        custom_print(text, verbose)
        return self

    def find_matches(self, stacked=False, verbose=False, stop_words=STOPWORDS,
                     information=True, refresh=False, **kwds):
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

        information : bool (optional, default=True)
            Whether to return additional information on the matches that may
            help in the selection process.

        refresh : bool (optional, default=False)
            Whether to refresh cached search files.

        kwds : keywords
            Parameters to pass to TfidfVectorizer for abstract vectorization.

        Returns
        -------
        matches : list
            A list of Scopus IDs of scientists matching all the criteria (if
            information is False) or a list of namedtuples with the Scopus ID
            and additional information (if information is True).
        """
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
        _npapers = margin_range(len(self.publications), self.pub_margin)
        _ncoauth = margin_range(len(self.coauthors), self.coauth_margin)
        n = len(self.search_group)
        text = "Searching through characteristics of {:,} authors".format(n)
        custom_print(text, verbose)

        # First round of filtering: minimum publications and main field
        # create df of authors
        authors = pd.DataFrame(self.search_group, columns=["auth_id"], dtype="int64")

        # merge existing data in cache and separate missing records
        _, authors_search = authors_in_cache(authors)
        if authors_search:
            params = {
                "group": authors_search,
                "res": [],
                "refresh": refresh,
                "joiner": ") OR AU-ID(",
                "q_type": "author",
                "template": Template("AU-ID($fill)"),
            }
            if verbose:
                print("Pre-filtering...")
                params.update({"total": len(authors_search)})
            res, _ = stacked_query(**params)
            res = pd.DataFrame(res)
            if not res.empty:
                res["auth_id"] = res.apply(lambda x: x.eid.split("-")[-1], axis=1)
                res = res[["auth_id", "eid", "surname", "initials",
                           "givenname", "affiliation", "documents",
                           "affiliation_id", "city", "country","areas"]]
                cache_authors(res)
        authors_cache, _ = authors_in_cache(authors)
        same_field = (authors_cache.areas.str.startswith(self.main_field[1]))
        enough_pubs = (authors_cache.documents.astype(int) >= int(min(_npapers)))
        group = authors_cache[same_field & enough_pubs]["auth_id"].tolist()
        group.sort()
        n = len(group)
        text = ("Left with {} authors\nFiltering based on provided "
                "conditions...".format(n))
        custom_print(text, verbose)

        # Second round of filtering: All other conditions

        # create df of authors and year of the event
        authors = pd.DataFrame(group, columns=["auth_id"], dtype="int64")
        authors["year"] = int(self.year)

        # merge existing data in cache and separate missing records
        _, author_year_search = author_year_in_cache(authors)

        matches = []
        if stacked:  # Combine searches
            if not author_year_search.empty:
                q = Template("AU-ID($fill) AND PUBYEAR BEF {}".format(self.year + 1))
                auth_year_group = author_year_search.auth_id.tolist()
                params = {
                    "group": auth_year_group,
                    "res": [],
                    "template": q,
                    "refresh": refresh,
                    "joiner": ") OR AU-ID(",
                    "q_type": "docs",
                }
                if verbose:
                    params.update({"total": n})
                res, _ = stacked_query(**params)
                res = build_dict(res, auth_year_group)
                res = pd.DataFrame.from_dict(res, orient="index", dtype="int64")
                res["year"] = self.year
                res = res[["year", "first_year", "n_pubs", "n_coauth"]]
                res.reset_index(inplace=True)
                res.columns = ["auth_id", "year", "first_year", "n_pubs", "n_coauth"]
                cache_author_year(res)
            author_year_cache, _ = author_year_in_cache(authors)
            same_start = (author_year_cache.first_year.between(min(_years), max(_years)))
            same_pubs = (author_year_cache.n_pubs.between(min(_npapers), max(_npapers)))
            same_coauths = (author_year_cache.n_coauth.between(min(_ncoauth), max(_ncoauth)))
            mask = same_start & same_pubs & same_coauths
            matches = author_year_cache[mask][["auth_id", "first_year", "n_coauth", "n_pubs"]]
            matches.columns = ["ID", "first_year", "num_coauthors", "num_publications"]
        else:  # Query each author individually
            for i, au in enumerate(group):
                print_progress(i + 1, n, verbose)
                res = query("docs", "AU-ID({})".format(au), refresh=refresh)
                res = [p for p in res if p.coverDate and
                       int(p.coverDate[:4]) <= self.year]
                # Filter
                min_year = int(min([p.coverDate[:4] for p in res]))
                authids = [p.author_ids for p in res if p.author_ids]
                authors = set([a for p in authids for a in p.split(";")])
                n_coauth = len(authors) - 1  # Subtract 1 for focal author
                if ((len(res) not in _npapers) or (min_year not in _years)
                        or (n_coauth not in _ncoauth)):
                    continue
                matches.append(au)
        text = "Found {:,} author(s) matching all criteria".format(len(matches))
        custom_print(text, verbose)

        if information and len(matches) > 0 and not stacked:
            custom_print("Providing additional information...", verbose)
            profiles = [Scientist([str(au)], self.year, refresh) for au in matches]
            return inform_matches(profiles, self, stop_words, verbose, refresh, **kwds)
        elif information and len(matches) > 0 and stacked:
            matches = matches["ID"].tolist()
            custom_print("Providing additional information...", verbose)
            profiles = [Scientist([str(au)], self.year, refresh) for au in matches]
            return inform_matches(profiles, self, stop_words, verbose, refresh, **kwds)
        else:
            return matches
