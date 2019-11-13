#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from string import digits, punctuation, Template
from warnings import warn
import pandas as pd

from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS

from sosia.cache import author_cits_in_cache, author_year_in_cache, cache_insert
from sosia.classes import Scientist
from sosia.filtering import search_group_from_sources, filter_pub_counts
from sosia.processing import count_citations, get_authors, base_query,\
    inform_matches, query_author_data, stacked_query
from sosia.utils import accepts, build_dict, custom_print, margin_range,\
    maybe_add_source_names, print_progress

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
    @accepts((set, list, tuple))
    def search_sources(self, val):
        self._search_sources = maybe_add_source_names(val, self.source_names)

    def __init__(self, scientist, year, year_margin=1, pub_margin=0.1,
                 cits_margin=0.1, coauth_margin=0.1, period=None, refresh=False,
                 eids=None, search_affiliations=None):
        """Class to represent a scientist for which we want to find a control
        group.

        Parameters
        ----------
        scientist : str, int or list or str or int
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

        cits_margin : numeric (optional, default=0.1)
            The left and right margin for the number of citations to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of citations.

        coauth_margin : numeric (optional, default=0.1)
            The left and right margin for the number of coauthors to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            coauthors and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of coauthors.

        period: int (optional, default=None)
            The period in which to consider publications. If not provided,
            all publications are considered.

        refresh : boolean (optional, default=False)
            Whether to refresh all cached files or not.

        eids : list (optional, default=None)
            A list of scopus EIDs of the publications of the scientist you
            want to find a control for.  If it is provided, the scientist
            properties and the control group are set based on this list of
            publications, instead of the list of publications obtained from
            the Scopus Author ID.

        affiliations : list (optional, default=None)
            A list of scopus affiliation IDs. If provided, sosia searches
            for matches within this affiliation in the year provided.
        """
        # Internal checks
        if not isinstance(year_margin, (int, float)):
            raise Exception("Argument year_margin must be float or integer.")
        if not isinstance(pub_margin, (int, float)):
            raise Exception("Argument pub_margin must be float or integer.")
        if not isinstance(coauth_margin, (int, float)):
            raise Exception("Argument coauth_margin must be float or integer.")

        # Variables
        if not isinstance(scientist, list):
            scientist = [scientist]
        self.identifier = [str(auth_id) for auth_id in scientist]
        self.year = int(year)
        self.year_margin = year_margin
        self.pub_margin = pub_margin
        self.cits_margin = cits_margin
        self.coauth_margin = coauth_margin
        self.period = period
        self.eids = eids
        if isinstance(search_affiliations, (int, str)):
            search_affiliations = [search_affiliations]
        if search_affiliations:
            search_affiliations = [int(a) for a in search_affiliations]
        self.search_affiliations = search_affiliations
        self.refresh = refresh

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, year, refresh, period)

    def define_search_group(self, stacked=False, verbose=False, refresh=False,
                            ignore_first_id=False):
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

        ignore_first_id: boolean (optional, default=False)
            If True, the authors in the first year of publication of the
            scientist are not selected based on their Author ID but based on
            their surname and first name.
        """
        # Checks
        if not self.search_sources:
            text = "No search sources defined.  Please run "\
                   ".define_search_sources() first."
            raise Exception(text)
        self._ignore_first_id = ignore_first_id
        if ignore_first_id and not self.period:
            self._ignore_first_id = False
            warn("ignore_first_id set back to False: period is None or "
                 "the first year of the period is before the first year "
                 "of publication of the scientist.")

        # Query journals
        params = {"self": self, "stacked": stacked,
                  "refresh": refresh, "verbose": verbose}
        today, then, negative = search_group_from_sources(**params)

        # Finalize and select
        group = today
        if not self._ignore_first_id:
            group = today.intersection(then)
        negative.update({str(i) for i in self.identifier})
        negative.update({str(i) for i in self.coauthors})
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
            lambda s: any(x for x in s.split() if int(x) not in self.fields))
        grouped = grouped[~mask]
        sources = set((s, self.source_names.get(s)) for s in grouped.index)
        # Add own sources
        sources.update(self.sources)
        # Finalize
        self._search_sources = sorted(list(sources))
        types = "; ".join(list(main_types))
        text = "Found {} sources matching main field {} and type(s) {}".format(
            len(self._search_sources), self.main_field[0], types)
        custom_print(text, verbose)
        return self

    def find_matches(self, stacked=False, verbose=False, stop_words=STOPWORDS,
                     information=True, refresh=False, **tfidf_kwds):
        """Find matches within search_group based on four criteria:
        1. Started publishing in about the same year
        2. Has about the same number of publications in the year of treatment
        3. Has about the same number of coauthors in the year of treatment
        4. Has about the same number of citations in the year of treatment
        5. Works in the same field as the scientist's main field

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

        information : bool or iterable (optional, default=True)
            Whether to return additional information on the matches that may
            help in the selection process.  If an iterable of keywords is
            provied, only return information for these keywords.  Allowed
            values are "first_year", "num_coauthors", "num_publications",
            "num_citations", "country", "language",
            "reference_sim", "abstract_sim".

        refresh : bool (optional, default=False)
            Whether to refresh cached search files.

        tfidf_kwds : keywords
            Parameters to pass to TfidfVectorizer from the sklearn package
            for abstract vectorization.  Not used when `information=False` or
            or when "abstract_sim" is not in `information`.  See
            https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
            for possible values.

        Returns
        -------
        matches : list
            A list of Scopus IDs of scientists matching all the criteria (if
            information is False) or a list of namedtuples with the Scopus ID
            and additional information (if information is True).

        Raises
        ------
        ValueError
            If information is not bool and contains invalid keywords.
        """
        # Checks
        info_keys = ["first_name", "surname", "first_year", "num_coauthors",
                     "num_publications", "num_citations", "num_coauthors_period",
                     "num_publications_period", "num_citations_period",
                     "subjects", "country", "affiliation_id", "affiliation",
                     "language", "reference_sim", "abstract_sim"]
        if isinstance(information, bool):
            if information:
                keywords = info_keys
            elif self.search_affiliations:
                information = True
                keywords = ["affiliation_id"]
            else:
                keywords = None
        else:
            keywords = information
            invalid = [x for x in keywords if x not in info_keys]
            if invalid:
                text = ("Parameter information contains invalid keywords: ",
                        ", ".join(invalid))
                raise ValueError(text)
            if self.search_affiliations and "affiliation_id" not in keywords:
                keywords.append("affiliation_id")
        # Variables
        _years = range(self.first_year-self.year_margin,
                       self.first_year+self.year_margin+1)
        if self.period:
            _npapers = margin_range(len(self.publications_period), self.pub_margin)
            _ncits = margin_range(self.citations_period, self.cits_margin)
            _ncoauth = margin_range(len(self.coauthors_period), self.coauth_margin)
            _npapers_full = margin_range(len(self.publications), self.pub_margin)
            _ncits_full = margin_range(self.citations, self.cits_margin)
            _ncoauth_full = margin_range(len(self.coauthors), self.coauth_margin)
        else:
            _npapers = margin_range(len(self.publications), self.pub_margin)
            _ncits = margin_range(self.citations, self.cits_margin)
            _ncoauth = margin_range(len(self.coauthors), self.coauth_margin)
        n = len(self.search_group)
        text = "Searching through characteristics of {:,} authors".format(n)
        custom_print(text, verbose)

        # First round of filtering: minimum publications and main field
        # create df of authors
        authors = query_author_data(self.search_group, verbose=verbose)
        same_field = (authors.areas.str.startswith(self.main_field[1]))
        enough_pubs = (authors.documents.astype(int) >= int(min(_npapers)))
        group = authors[same_field & enough_pubs]["auth_id"].tolist()
        group.sort()
        n = len(group)
        text = "Left with {} authors\nFiltering based on provided "\
               "conditions...".format(n)
        custom_print(text, verbose)

        # Second round of filtering:
        # Check having no publications before minimum year, and if 0, the
        # number of publications in the relevant period.
        params = {"group": group, "ybefore": min(_years)-1,
                  "yupto": self.year, "npapers": _npapers,
                  "yfrom": self.year_period, "verbose": verbose}
        group, _, _ = filter_pub_counts(**params)
        # Also screen out ids with too many publications over the full period
        if self.period:
            params.update({"npapers": [1, max(_npapers_full)], "yfrom": None,
                           "group": group})
            group, _, _ = filter_pub_counts(**params)

        # Third round of filtering: citations (in the FULL period).
        authors = pd.DataFrame({"auth_id": group, "year": self.year})
        _, authors_cits_search = author_cits_in_cache(authors)
        text = "Search and filter based on count of citations\n{} to search "\
               "out of {}\n".format(len(authors_cits_search), len(group))
        custom_print(text, verbose)
        if not authors_cits_search.empty:
            authors_cits_search['n_cits'] = 0
            print_progress(0, len(authors_cits_search), verbose)
            for i, au in authors_cits_search.iterrows():
                q = "REF({}) AND PUBYEAR BEF {} AND NOT AU-ID({})".format(
                    au['auth_id'], self.year + 1, au['auth_id'])
                n = base_query("docs", q, size_only=True)
                authors_cits_search.at[i, 'n_cits'] = n
                print_progress(i + 1, len(authors_cits_search), verbose)
            cache_insert(authors_cits_search, table="author_cits_size")
        auth_cits_incache, _ = author_cits_in_cache(authors[["auth_id", "year"]])
        # keep if citations are in range
        mask = ((auth_cits_incache.n_cits <= max(_ncits)) &
                (auth_cits_incache.n_cits >= min(_ncits)))
        if self.period:
            mask = ((auth_cits_incache.n_cits >= min(_ncits)) &
                    (auth_cits_incache.n_cits <= max(_ncits_full)))
        group = (auth_cits_incache[mask]['auth_id'].tolist())

        # Fourth round of filtering: Download publications, verify coauthors
        # (in the FULL period) and first year.
        n = len(group)
        text = "Left with {} authors\nFiltering based on coauthors "\
               "number...".format(n)
        custom_print(text, verbose)
        authors = pd.DataFrame({"auth_id": group, "year": self.year},
                               dtype="uint64")
        _, author_year_search = author_year_in_cache(authors)
        matches = []
        if stacked:  # Combine searches
            if not author_year_search.empty:
                q = Template("AU-ID($fill) AND PUBYEAR BEF {}".format(
                    self.year + 1))
                auth_year_group = author_year_search.auth_id.tolist()
                params = {"group": auth_year_group, "res": [],
                          "template": q, "refresh": refresh,
                          "joiner": ") OR AU-ID(", "q_type": "docs"}
                if verbose:
                    params.update({"total": len(auth_year_group)})
                res, _ = stacked_query(**params)
                res = build_dict(res, auth_year_group)
                if res:
                    # res can become empty after build_dict if a au_id is old
                    res = pd.DataFrame.from_dict(res, orient="index")
                    res["year"] = self.year
                    res = res[["year", "first_year", "n_pubs", "n_coauth"]]
                    res.index.name = "auth_id"
                    res = res.reset_index()
                    cache_insert(res, table="author_year")
            author_year_cache, _ = author_year_in_cache(authors)
            if self._ignore_first_id:
                # only number of coauthors should be big enough
                enough = (author_year_cache.n_coauth >= min(_ncoauth))
                notoomany = (author_year_cache.n_coauth <= max(_ncoauth_full))
                mask = enough & notoomany
            elif self.period:
                # number of coauthors should be "big enough" and first year in
                # window
                same_start = (author_year_cache.first_year.between(min(_years),
                              max(_years)))
                enough = (author_year_cache.n_coauth >= min(_ncoauth))
                notoomany = (author_year_cache.n_coauth <= max(_ncoauth_full))
                mask = same_start & enough & notoomany
            else:
                # all restrictions apply
                same_start = (author_year_cache.first_year.between(min(_years),
                              max(_years)))
                same_coauths = (author_year_cache.n_coauth.between(min(_ncoauth),
                                max(_ncoauth)))
                mask = same_start & same_coauths
            matches = author_year_cache[mask]["auth_id"].tolist()
        else:  # Query each author individually
            for i, au in enumerate(group):
                print_progress(i + 1, len(group), verbose)
                res = base_query("docs", "AU-ID({})".format(au), refresh=refresh)
                res = [p for p in res if p.coverDate and
                       int(p.coverDate[:4]) <= self.year]
                # Filter
                min_year = int(min([p.coverDate[:4] for p in res]))
                authids = [p.author_ids for p in res if p.author_ids]
                authors = set([a for p in authids for a in p.split(";")])
                n_coauth = len(authors) - 1  # Subtract 1 for focal author
                if self._ignore_first_id and (n_coauth < max(_ncoauth)):
                    # only number of coauthors should be big enough
                    continue
                elif (self.period and ((n_coauth < max(_ncoauth)) or
                      (min_year not in _years))):
                    # number of coauthors should be "big enough" and first year
                    # in window
                    continue
                elif ((len(res) not in _npapers) or (min_year not in _years) or
                        (n_coauth not in _ncoauth)):
                    continue
                matches.append(au)

        if self.period:
            text = "Left with {} authors\nFiltering based on exact period "\
                   "citations and coauthors...".format(len(matches))
            custom_print(text, verbose)
            # Further screen matches based on period cits and coauths
            to_loop = [m for m in matches]  # temporary copy
            for m in to_loop:
                q = "AU-ID({})".format(m)
                res = base_query("docs", "AU-ID({})".format(m), refresh=refresh,
                    fields=["eid", "author_ids", "coverDate"])
                pubs = [p for p in res if int(p.coverDate[:4]) <= self.year and
                        int(p.coverDate[:4]) >= self.year_period]
                coauths = set(get_authors(pubs)) - {str(m)}
                if not (min(_ncoauth) <= len(coauths) <= max(_ncoauth)):
                    matches.remove(m)
                    continue
                eids_period = [p.eid for p in pubs]
                cits = count_citations(search_ids=eids_period,
                        pubyear=self.year+1, exclusion_key="AU-ID",
                        exclusion_ids=[str(m)])
                if not (min(_ncits) <= cits <= max(_ncits)):
                    matches.remove(m)
        text = "Found {:,} author(s) matching all criteria".format(len(matches))
        custom_print(text, verbose)

        # Possibly add information to matches
        if keywords and len(matches) > 0:
            custom_print("Providing additional information...", verbose)
            profiles = [Scientist([str(a)], self.year, period=self.period,
                                  refresh=refresh) for a in matches]
            matches = inform_matches(profiles, self, keywords, stop_words,
                                     verbose, refresh, **tfidf_kwds)
        if self.search_affiliations:
            matches = [m for m in matches if 
                       len(set(m.affiliation_id.replace(" ","").split(";"))
                       .intersection([str(a) for a in
                                      self.search_affiliations]))]
        return matches
