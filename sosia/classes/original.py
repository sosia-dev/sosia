#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from string import Template
from warnings import warn
import pandas as pd

from sosia.classes import Scientist
from sosia.processing import base_query, build_dict, count_citations,\
    filter_pub_counts, get_authors, inform_matches, insert_data,\
    margin_range, maybe_add_source_names, query_author_data,\
    retrieve_author_cits, retrieve_authors_year, search_group_from_sources,\
    stacked_query
from sosia.utils import accepts, custom_print, print_progress


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
                 eids=None, search_affiliations=None, sql_fname=None):
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
            Whether to refresh cached results (if they exist) or not. If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        eids : list (optional, default=None)
            A list of scopus EIDs of the publications of the scientist you
            want to find a control for.  If it is provided, the scientist
            properties and the control group are set based on this list of
            publications, instead of the list of publications obtained from
            the Scopus Author ID.

        search_affiliations : list (optional, default=None)
            A list of Scopus affiliation IDs. If provided, sosia searches
            for matches within this affiliation in the year provided.

        sql_fname : str (optional, default=None)
            The path of the SQLite database to connect to.  If None, will use
            the path specified in config.ini.
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
            search_affiliations = [str(a) for a in search_affiliations]
        self.search_affiliations = search_affiliations
        self.refresh = refresh
        self.sql_fname = sql_fname

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, year, refresh=refresh,
                           period=period, sql_fname=self.sql_fname)

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
            Whether to refresh cached results (if they exist) or not.

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
        if not isinstance(refresh, bool):
            refresh = False
            warn("refresh must be boolean.  Continuing with refresh=False.")

        # Query journals
        params = {"self": self, "stacked": stacked,
                  "refresh": refresh, "verbose": verbose}
        search_group = search_group_from_sources(**params)

        # Remove own IDs and coauthors
        search_group -= set(self.identifier)
        search_group -= {str(i) for i in self.coauthors}

        # Finalize
        self._search_group = sorted(search_group)
        text = f"Found {len(search_group):,} authors for search_group"
        custom_print(text, verbose)
        return self

    def define_search_sources(self, verbose=False):
        """Define .search_sources.

        Within the list of search sources sosia will search for matching
        scientists.  A search source is of the same main field as
        the original scientist, the same types (journal, conference
        proceeding, etc.), and must not be related to fields alien to the
        original scientist.

        Parameters
        ----------
        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.
        """
        df = self.field_source
        # Sources in scientist's main field
        same_field = df["asjc"] == self.main_field[0]
        # Types of Scientist's sources
        own_source_ids, _ = zip(*self.sources)
        same_sources = df["source_id"].isin(own_source_ids)
        main_types = df[same_sources]["type"].unique()
        same_type = df["type"].isin(main_types)
        # Select source IDs
        selected_ids = df[same_field & same_type]["source_id"].unique()
        selected = df[df["source_id"].isin(selected_ids)].copy()
        selected["asjc"] = selected["asjc"].astype(str) + " "
        grouped = (selected.groupby("source_id")
                           .sum()["asjc"]
                           .to_frame())
        # Deselect sources with alien fields
        grouped["asjc"] = grouped["asjc"].str.split().apply(set)
        fields = set(str(f) for f in self.fields)
        no_alien_field = grouped["asjc"].apply(lambda s: len(s - fields) == 0)
        grouped = grouped[no_alien_field]
        # Add source names
        sources = set((s, self.source_names.get(s)) for s in grouped.index)
        # Add own sources
        sources.update(self.sources)
        # Finalize
        self._search_sources = sorted(sources)
        text = f"Found {len(sources):,} sources matching main field "\
               f"{self.main_field[0]} and source type(s) {'; '.join(main_types)}"
        custom_print(text, verbose)
        return self

    def find_matches(self, stacked=False, verbose=False, refresh=False):
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

        refresh : bool (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed and stacked=False, results will be refreshed if they are
            older than that value in number of days.

        Notes
        -----
        Matches are available through property `.matches`.
        """
        # Checks
        if not self.search_group:
            text = "No search group defined.  Please run "\
                   ".define_search_group() first."
            raise Exception(text)
        if not isinstance(refresh, bool) and stacked:
            refresh = False
            warn("refresh parameter must be boolean when stacked=True.  "
                 "Continuing with refresh=False.")

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
        text = "Searching through characteristics of "\
               f"{len(self.search_group):,} authors..."
        custom_print(text, verbose)

        # First round of filtering: minimum publications and main field
        # create df of authors
        authors = query_author_data(self.search_group, self.sql_conn, verbose=verbose)
        same_field = (authors.areas.str.startswith(self.main_field[1]))
        enough_pubs = (authors.documents.astype(int) >= int(min(_npapers)))
        group = authors[same_field & enough_pubs]["auth_id"].tolist()
        group.sort()
        text = f"Left with {len(group):,} authors with sufficient "\
               "number of publications and same main field"
        custom_print(text, verbose)

        # Second round of filtering:
        # Check having no publications before minimum year, and if 0, the
        # number of publications in the relevant period.
        params = {"group": group, "ybefore": min(_years)-1,
                  "yupto": self.year, "npapers": _npapers,
                  "yfrom": self.year_period, "verbose": verbose,
                  "conn": self.sql_conn}
        group, _, _ = filter_pub_counts(**params)
        # Also screen out ids with too many publications over the full period
        if self.period:
            params.update({"npapers": [1, max(_npapers_full)], "yfrom": None,
                           "group": group})
            group, _, _ = filter_pub_counts(**params)
        text = f"Left with {len(group):,} researchers"

        # Third round of filtering: citations (in the FULL period).
        authors = pd.DataFrame({"auth_id": group, "year": self.year})
        _, authors_cits_search = retrieve_author_cits(authors, self.sql_conn)
        if not authors_cits_search.empty:
            text = f"Counting citations of {len(authors_cits_search):,}..."
            custom_print(text, verbose)
            authors_cits_search['n_cits'] = 0
            print_progress(0, len(authors_cits_search), verbose)
            for i, au in authors_cits_search.iterrows():
                n_cits = count_citations([str(au['auth_id'])], self.year+1)
                authors_cits_search.at[i, 'n_cits'] = n_cits
                print_progress(i + 1, len(authors_cits_search), verbose)
            insert_data(authors_cits_search, self.sql_conn,
                         table="author_ncits")
        auth_cits_incache, _ = retrieve_author_cits(authors[["auth_id", "year"]],
                                                    self.sql_conn)
        # Keep if citations are in range
        custom_print("Filtering based on count of citations...", verbose)
        mask = ((auth_cits_incache.n_cits <= max(_ncits)) &
                (auth_cits_incache.n_cits >= min(_ncits)))
        if self.period:
            mask = ((auth_cits_incache.n_cits >= min(_ncits)) &
                    (auth_cits_incache.n_cits <= max(_ncits_full)))
        group = (auth_cits_incache[mask]['auth_id'].tolist())

        # Fourth round of filtering: Download publications, verify coauthors
        # (in the FULL period) and first year.
        text = f"Left with {len(group):,} authors\nFiltering based on "\
               "coauthors number..."
        custom_print(text, verbose)
        authors = pd.DataFrame({"auth_id": group, "year": self.year},
                               dtype="uint64")
        _, author_year_search = retrieve_authors_year(authors, self.sql_conn)
        matches = []
        if stacked:  # Combine searches
            if not author_year_search.empty:
                q = Template(f"AU-ID($fill) AND PUBYEAR BEF {self.year + 1}")
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
                    insert_data(res, self.sql_conn, table="author_year")
            author_year_cache, _ = retrieve_authors_year(authors, self.sql_conn)
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
                res = base_query("docs", f"AU-ID({au})", refresh=refresh)
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
            text = f"Left with {len(matches)} authors\nFiltering based on "\
                   "exact period citations and coauthors..."
            custom_print(text, verbose)
            # Further screen matches based on period cits and coauths
            to_loop = [m for m in matches]  # temporary copy
            for m in to_loop:
                res = base_query("docs", f"AU-ID({m})", refresh=refresh,
                                 fields=["eid", "author_ids", "coverDate"])
                pubs = [p for p in res if int(p.coverDate[:4]) <= self.year and
                        int(p.coverDate[:4]) >= self.year_period]
                coauths = set(get_authors(pubs)) - {str(m)}
                if not (min(_ncoauth) <= len(coauths) <= max(_ncoauth)):
                    matches.remove(m)
                    continue
                eids_period = [p.eid for p in pubs]
                n_cits = count_citations(eids_period, self.year+1, [str(m)])
                if not (min(_ncits) <= n_cits <= max(_ncits)):
                    matches.remove(m)

        # Eventually filter on affiliations
        matches_copy = matches.copy()
        if self.search_affiliations:
            text = f"Left with {len(matches)} authors\nFiltering based on "\
                   "affiliations..."
            custom_print(text, verbose)
            for auth_id in matches_copy:
                m = Scientist([str(auth_id)], self.year, period=self.period,
                              refresh=refresh, sql_fname=self.sql_fname)
                aff_ids = set(m.affiliation_id.replace(" ", "").split(";"))
                if not aff_ids.intersection(self.search_affiliations):
                    matches.remove(auth_id)

        # Finalize
        text = f"Found {len(matches):,} author(s) matching all criteria"
        custom_print(text, verbose)
        self.matches = sorted([str(auth_id) for auth_id in matches])

    def inform_matches(self, fields=None, verbose=False, refresh=False,
                       stop_words=None, **tfidf_kwds):
        """Add information to matches to aid in selection process.

        Parameters
        ----------
        fields : iterable (optional, default=None)
            Which information to provide. Allowed values are "first_year",
            "num_coauthors", "num_publications", "num_citations", "country",
            "language", "reference_sim", "abstract_sim".  If None, will
            use all available fields.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed and stacked=False, results will be refreshed if they are
            older than that value in number of days.

        stop_words : list (optional, default=None)
            A list of words that should be filtered in the analysis of
            abstracts.  If None uses the list of English stopwords
            by nltk, augmented with numbers and interpunctuation.

        tfidf_kwds : keywords
            Parameters to pass to TfidfVectorizer from the sklearn package
            for abstract vectorization.  Not used when `information=False` or
            or when "abstract_sim" is not in `information`.  See
            https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
            for possible values.

        Notes
        -----
        Matches including corresponding information are available through
        property `.matches`.

        Raises
        ------
        fields
            If fields contains invalid keywords.
        """
        # Checks
        if not self.matches:
            text = "No matches defined.  Please run .find_matches() first."
            raise Exception(text)
        allowed_fields = ["first_name", "surname", "first_year",
                          "num_coauthors", "num_publications", "num_citations",
                          "num_coauthors_period", "num_publications_period",
                          "num_citations_period", "subjects", "country",
                          "affiliation_id", "affiliation", "language",
                          "reference_sim", "abstract_sim"]
        if fields:
            invalid = [x for x in fields if x not in allowed_fields]
            if invalid:
                text = "Parameter fields contains invalid keywords: " +\
                       ", ".join(invalid)
                raise ValueError(text)
        else:
            fields = allowed_fields

        # Possibly add information to matches
        custom_print("Providing additional information...", verbose)
        profiles = [Scientist([a], self.year, period=self.period,
                              refresh=refresh, sql_fname=self.sql_fname)
                    for a in self.matches]
        self.matches = inform_matches(profiles, self, fields, stop_words,
                                      verbose, refresh, **tfidf_kwds)
