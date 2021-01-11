#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Main class for sosia."""

from collections import namedtuple

from warnings import warn

import pandas as pd

from sosia.classes import Scientist
from sosia.processing import find_matches, inform_matches,\
    maybe_add_source_names, search_group_from_sources
from sosia.utils import accepts, custom_print


class Original(Scientist):
    @property
    def matches(self):
        """List of Scopus IDs or list of namedtuples representing matches
        of the original scientist in the treatment year.

        Notes
        -----
        Property is initiated via .find_matches().
        """
        try:
            return self._matches
        except AttributeError:
            return None

    @matches.setter
    @accepts(list)
    def matches(self, val):
        self._matches = val

    @property
    def matches_disambiguated(self):
        """List of Scopus IDs or list of namedtuples representing matches
        of the original scientist in the treatment year, after disambiguation.

        Notes
        -----
        Property is initiated via .disambiguate_matches().
        """
        try:
            return self._matches_disambiguated
        except AttributeError:
            return None

    @matches_disambiguated.setter
    @accepts(list)
    def matches_disambiguated(self, val):
        self._matches_disambiguated = val

    @property
    def search_group(self):
        """The set of authors that might be matches to the scientist.  The
        set contains the intersection of all authors publishing in the
        treatment year as well as authors publishing around the year of first
        publication.  Some authors with too many publications in the
        treatment year and authors having published too early are removed.

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
        the scientist published in until the treatment year.
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

    def __init__(self, scientist, treatment_year, first_year_margin=2,
                 pub_margin=0.2, cits_margin=0.2, coauth_margin=0.2,
                 affiliations=None, period=None, first_year_search="ID",
                 eids=None, refresh=False, sql_fname=None):
        """Representation of a scientist for whom to find a control scientist.

        Parameters
        ----------
        scientist : str, int or list of str or int
            Scopus Author ID, or list of Scopus Author IDs, of the scientist
            to find a control scientist for.

        treatment_year : str or numeric
            Year of the event.  Control scientist will be matched on trends and
            characteristics of the original scientist up to this year.

        first_year_margin : numeric (optional, default=2)
            Number of years by which the search for authors publishing around
            the year of the original scientist's year of first publication
            should be extend in both directions.

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

        affiliations : list (optional, default=None)
            A list of Scopus affiliation IDs.  If provided, sosia conditions
            the match procedure on affiliation with these IDs in the
            treatment year.

        period: int (optional, default=None)
            An additional period prior to the publication year on which to
            match scientists.
            Note: If the value is larger than the publication range, period
            sets back to None.

        first_year_search: str (optional, default="ID")
            How to determine characteristics of possible control scientists
            in the first year of publication.  Mode "ID" uses Scopus Author
            IDs only.  Mode "name" will select relevant profiles based on
            their surname and first name but only when "period" is not None.
            Select this mode to counter potential incompleteness of
            author profiles.

        eids : list (optional, default=None)
            A list of scopus EIDs of the publications of the scientist you
            want to find a control for.  If it is provided, the scientist
            properties and the control group are set based on this list of
            publications, instead of the list of publications obtained from
            the Scopus Author ID.

        refresh : boolean (optional, default=False)
            Whether to refresh cached results (if they exist) or not.  If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        sql_fname : str (optional, default=None)
            The path of the SQLite database to connect to.  If None, will use
            the path specified in config.ini.
        """
        # Internal checks
        if not isinstance(first_year_margin, (int, float)):
            raise Exception("Argument first_year_margin must be float or integer.")
        if not isinstance(pub_margin, (int, float)):
            raise Exception("Argument pub_margin must be float or integer.")
        if not isinstance(coauth_margin, (int, float)):
            raise Exception("Argument coauth_margin must be float or integer.")
        if first_year_search not in ("ID", "name"):
            raise Exception("Argument first_year_search must be either ID or name.")
        if first_year_search == "name" and not period:
            first_year_search = "ID"
            text = "Argument first_year_search set to ID: Argument period "\
                   "must not be None"
            warn(text)

        # Variables
        if not isinstance(scientist, list):
            scientist = [scientist]
        self.identifier = [str(auth_id) for auth_id in scientist]
        self.treatment_year = int(treatment_year)
        self.first_year_margin = first_year_margin
        self.pub_margin = pub_margin
        self.cits_margin = cits_margin
        self.coauth_margin = coauth_margin
        self.period = period
        self.first_year_name_search = first_year_search == "name"
        self.eids = eids
        if isinstance(affiliations, (int, str)):
            affiliations = [affiliations]
        if affiliations:
            affiliations = [int(a) for a in affiliations]
        self.search_affiliations = affiliations
        self.refresh = refresh
        self.sql_fname = sql_fname

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, treatment_year,
                           refresh=refresh, period=period, eids=self.eids,
                           sql_fname=self.sql_fname)

    def define_search_group(self, stacked=False, verbose=False, refresh=False):
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
        """
        # Checks
        if not self.search_sources:
            text = "No search sources defined.  Please run "\
                   ".define_search_sources() first."
            raise Exception(text)

        # Query journals
        params = {"original": self, "stacked": stacked,
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
        selected["asjc"] = selected["asjc"].astype(int).astype(str) + " "
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
        2. Has about the same number of publications in the treatment year
        3. Has about the same number of coauthors in the treatment year
        4. Has about the same number of citations in the treatment year
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
                          "reference_sim", "abstract_sim", "cross_citations"]
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

    def matches_disambiguator(self, homonym_fields=None, compile_info=False,
                              in_subjects=True, limit=10, verbose=False,
                              refresh=False, sql_fname=None):
        """ For each match found create a Disambiguator class object and store
        the list in self.m_disambiguators. If compile_info is True, loop the
        list a compile the information on matches uniqueness and homonyms and
        create the attributes self.matches_uniqueness and
        self.matches_homonyms.

        Parameters
        ----------
        homonym_fields : None or List (optional, default=None)
            If a list is provided, additional information is added to the list
            of homonyms. Allowed fields are: "first_year", "num_publications",
            "num_citations", "num_coauthors", "reference_sim", "abstract_sim".
            If None, will use all available fields.

        compile_info : boolean, (optional, default=False)
            If True, compile the information on matches uniqueness and
            homonyms and create the attributes self.matches_uniqueness and
            self.matches_homonyms.

        in_subjects : boolean (optional, default=True)
            Whether to restrict the search for homonyms to the same subject
            area of the scientists.

        limit : int (default=10)
            The maximum number of homonyms to consider. If higher, no further
            information is downlaoded.

        refresh : boolean or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        sql_fname : str (optional, default=None)
            The path of the SQLite database to connect to.  If None, will use
            the path specified in config.ini.
        """
        from sosia.classes import Disambiguator

        d_params = {"in_subjects": in_subjects,
                    "homonym_fields": homonym_fields, "limit": limit,
                    "verbose": verbose, "refresh": refresh,
                    "sql_fname": sql_fname}

        mIDs = self.matches
        if not isinstance(self.matches[0], str):
            # if inform_matches has been used
            mIDs = [m.ID for m in self.matches]
        if verbose:
            print("Creating disambiguators generator...")
        self.m_disambiguators = (Disambiguator(ID, **d_params) for ID in mIDs)

        if compile_info:
            self.m_disambiguators = [d for d in self.m_disambiguators
                                     if d.surname]
            _list = [[d.identifier[0], d.uniqueness, d.homonyms_num]
                     for d in self.m_disambiguators if d]
            cols = ["ID", "uniqueness", "homonyms_num"]
            self.matches_uniqueness = pd.DataFrame(_list, columns=cols)

            def build_df(d):
                _df = d.homonyms
                _df = _df.rename(columns={"ID": "ID_homonym"})
                _df["ID"] = d.identifier[0]
                _df = _df.set_index(["ID", "ID_homonym"]).reset_index()
                return _df
            _list = [build_df(d) for d in self.m_disambiguators
                     if d and not d.homonyms.empty]
            self.matches_homonyms = pd.DataFrame()
            if len(_list):
                self.matches_homonyms = pd.concat(_list)

    def disambiguate_matches(self, stop_at=None, invalid="drop"):

        """ Request user input to screen each match homonyms information and
        eliminate matches that are revealed to be not good.

        Parameters
        ----------
        stop_at : int or None (optional, default=None)
            If provided, the screening stops except for matches that are
            already unique.

        invalid : str, (optional, default="drop")
            Whether to "keep" or "drop" matches found to be not valid after
            the disambiguation.

        Notes
        -------
        Set the attribute self.matches_disambiguated reporting the list
        of valid matches with the list of additional IDs found for each,
        if any.

        """
        _years = range(self.first_year-self.first_year_margin,
                       self.first_year+self.first_year_margin+1)
        match_dis = namedtuple("Match_disambiguated", "ID all_IDs")
        self._matches_disambiguated = []
        first = True
        print("\n\n-------------------------------------\n"
              f"   Original - ID: {','.join(self.identifier)}\n"
              "-------------------------------------\n"
              f"   First year: {self.first_year}     \n")
        for i, d in enumerate(self.m_disambiguators):
            all_ids = []
            print("\n.........................................\n"
                  f"   Match {i+1} of {len(self.matches)}"
                  f" - ID: {','.join(d.identifier)}\n"
                  ".........................................\n")
            if d.homonyms_num > d.limit:
                print(f"{d.identifier} has homonyms above limit.")
                if invalid == "keep":
                    m = match_dis(ID=d.identifier, all_IDs=[])
                    self._matches_disambiguated.append(m)
                continue
            if d.homonyms_num == 0:
                print(f"{d.identifier} is unique")
                m = match_dis(ID=d.identifier, all_IDs=d.identifier)
                self._matches_disambiguated.append(m)
                continue
            if stop_at and stop_at <= len(self.matches_disambiguated):
                if first:
                    print(f"{stop_at} matches or more are valid.\n"
                          "Checking for other unique matches...")
                    first = False
                continue
            old = d.homonyms[d.homonyms.first_year < min(_years)].ID.tolist()
            # TODO: add "too productive in period" in old group
            if len(old):
                instructions =\
                       f"\n\n---  Screen {len(old)} too old homonyms ---\n\n"\
                       "\nAs action, type:\n"\
                       "'(k)eep' if ANY is the same person"\
                       " (the match will be discarded).\n"\
                       "'(d)rop' or (e)xit if NONE is the same person"\
                       "(the match will be maintained).\n"\
                       "'(s)copus' to browse all homonyms in Scopus\n"\
                       "'(g)oogle' to browse name and affilaition in Google\n"\
                       "'(a)bort' to stop AND discard the match)\n"\
                       "Add space and a comma-sep list of homonyms to perform"\
                       "an action on a subset."
                if invalid == "keep":
                    instructions = \
                       f"\n\n---  Screen {len(old)} too old homonyms ---\n\n"\
                       "\nAs action, type:\n"\
                       "'(k)eep' to keep all homonyms.\n"\
                       "'(d)rop' to drop all homonyms\n"\
                       "'(s)copus' to browse all homonyms in Scopus\n"\
                       "'(g)oogle' to browse name and affilaition in Google\n"\
                       "'(e)xit' to exit (current results preserved)\n"\
                       "'(a)bort' to stop AND discard the match)\n"\
                       "Add space and a comma-sep list of homonyms to perform"\
                       "an action on a subset."
                d.disambiguate(subset=old, instructions=instructions)
                if not d.disambiguated_ids or len(d.disambiguated_ids) > 1:
                    if invalid == "keep":
                        all_ids.extend(d.disambiguated_ids)
                        m = match_dis(ID=d.identifier, all_IDs=all_ids)
                        self._matches_disambiguated.append(m)
                    else:
                        print(f"{d.identifier} is discarded.")
                        continue
            # TODO: add one group check for when "first_year_search="name""
            # TODO: add reassessing balance
            # TODO: add assessing full period when period option used
            other = [h for h in d.homonyms[~d.homonyms.isin(old)].ID.tolist()
                     if str(h).isnumeric()]
            if other:
                instructions =\
                    f"\n\n---  Screen {len(other)} other homonyms ---\n\n"\
                    "\nAs action, type:\n"\
                    "'(k)eep' to keep all homonyms.\n"\
                    "'(d)rop' all homonyms\n"\
                    "'(s)copus' to browse all homonyms in Scopus\n"\
                    "'(g)oogle' to browse name and affilaition in Google\n"\
                    "'(e)xit' to exit (previous commands are saved)\n"\
                    "'(a)bort' to stop AND discard the match\n"\
                    "Add space and a comma-sep list of homonyms to perform"\
                    "an action on a subset."
                d.disambiguate(subset=other, instructions=instructions,
                               show_main=not len(old))
                if not d.disambiguated_ids:
                    print(f"{d.identifier} is dropped.")
                    continue
                all_ids.extend([i for i in d.disambiguated_ids if i not in
                                all_ids])
                m = match_dis(ID=d.identifier, all_IDs=d.disambiguated_ids)
                self._matches_disambiguated.append(m)
            # TODO: update all matches information based on possible additional
            # ids found.
            # TODO: add option to search for cvs and add files names and
            # links to disambiguated_ids
        print(f"len({self._matches_disambiguated}) matches disambiguated.")
