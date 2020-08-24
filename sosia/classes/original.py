#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from warnings import warn

from sosia.classes import Scientist
from sosia.processing import find_matches, inform_matches,\
    maybe_add_source_names, search_group_from_sources
from sosia.utils import accepts, custom_print


class Original(Scientist):
    @property
    def matches(self):
        """List of Scopus IDs or list of namedtuples representing matches
        of the original scientist in the year of treatment.

        Notes
        -----
        Property is initiated via .find_matches().
        """
        try:
            return self._matches
        except AttributeError:
            return None

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

    def __init__(self, scientist, year, year_margin=2, pub_margin=0.2,
                 cits_margin=0.2, coauth_margin=0.2, period=None, refresh=False,
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

        year_margin : numeric (optional, default=2)
            Number of years by which the search for authors publishing around
            the year of the focal scientist's year of first publication should
            be extend in both directions.

        pub_margin : numeric (optional, default=0.2)
            The left and right margin for the number of publications to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of publications.

        cits_margin : numeric (optional, default=0.2)
            The left and right margin for the number of citations to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer it is interpreted as fixed number of citations.

        coauth_margin : numeric (optional, default=0.2)
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
            files with most likely not be reusable.  Set to True if you
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
        grouped["asjc"] = grouped["asjc"].astype(str).str.split().apply(set)
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
            files will most likely not be reusable.  Set to True if you
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

        # Find matches
        matches = find_matches(self, stacked, verbose, refresh)
        text = f"Found {len(matches):,} author(s) matching all criteria"
        custom_print(text, verbose)
        self._matches = sorted([str(auth_id) for auth_id in matches])

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
        if not self._matches:
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

        custom_print("Providing additional information...", verbose)
        matches = inform_matches(self, fields, stop_words, verbose, refresh,
                                 **tfidf_kwds)
        self._matches = matches
