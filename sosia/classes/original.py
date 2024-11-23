"""Main module of `sosia` containing the `Original` class."""

from math import ceil
from itertools import product
from pathlib import Path
from typing import Iterable, Literal, Optional, Union

from pandas import DataFrame
from typing_extensions import Self

from sosia.classes import Scientist
from sosia.establishing import create_logger, DEFAULT_LOG
from sosia.processing import add_source_names, chunk_list, compute_margins, \
    flat_set_from_df, get_author_data, get_author_info, \
    get_authors_from_sourceyear, get_citations, generate_filter_message, \
    inform_matches
from sosia.utils import accepts, custom_print, get_ending, validate_param


class Original(Scientist):
    """Representation of a scientist for whom to find a control scientist."""
    @property
    def candidates(self) -> Optional[list[int]]:
        """The set of authors that might be matches to the scientist.  The
        set contains the intersection of all authors publishing in the
        treatment year as well as authors publishing around the year of first
        publication.  Some authors with too many publications in the
        treatment year and authors having published too early are removed.

        Notes
        -----
        Property is initiated via .identify_candidates_from_sources().
        """
        return self._candidates

    @property
    def matches(self) -> Optional[list]:
        """List of Scopus IDs or list of namedtuples representing matches
        of the original scientist in the treatment year.

        Notes
        -----
        Property is initiated via .find_matches().
        """
        return self._matches

    @property
    def search_sources(self) -> Optional[Union[set, list, tuple]]:
        """The set of sources comparable to those of the Original.

        A source (journal, book, etc.) is comparable if it belongs to
        the Original's main field, and if the types of the sources are those
        the Original publishes in.

        Notes
        -----
        Property is initiated via .define_search_sources().
        """
        return self._search_sources

    @search_sources.setter
    @accepts((set, list, tuple))
    def search_sources(self, val: Union[set, list, tuple]) -> None:
        self._search_sources = add_source_names(val, self.source_names)

    def __init__(
        self,
        scientist: Union[str, int, list[Union[str, int]]],
        match_year: Union[str, int],
        eids: Optional[list[Union[str, int]]] = None,
        refresh: Union[bool, int] = False,
        db_path: Optional[Union[str, Path]] = None,
        log_path: Optional[Union[str, Path]] = None,
        verbose: Optional[bool] = False
    ) -> None:
        """Representation of a scientist for whom to find matches (= Original).

        Parameters
        ----------
        scientist : str, int or list of str or int
            Scopus Author ID, or list of Scopus Author IDs, of the scientist
            to find a control scientist for.

        match_year : str or numeric
            Year in which the comparison takes place.  Control scientist will
            be matched on trends and characteristics of the original
            scientist up to this year.

        eids : list (optional, default=None)
            A list of Scopus EIDs of the publications to consinder.  If it
            is provided, all properties will be derived from them, and the
            control group is based on them. If None, will use all
            research-type publications published until the match year.

        refresh : boolean (optional, default=False)
            Whether to refresh cached results (if they exist) or not.  If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        db_path : str or pathlib.Path (optional, default=None)
            The path of the SQLite database to connect to.  If None,
            will default to `~/.cache/sosia/main.sqlite`.  Will be created
            if the database doesn't exist.

        log_path : str or pathlib.Path (optional, default=None)
            The path of the log file using logging.  If None, will default
             to `~/.cache/sosia/sosia.log`.

        verbose : bool (optional, default=False)
            Whether to report on the initialization process.
        """
        # Variables
        if not isinstance(scientist, list):
            scientist = [scientist]
        self.identifier = [int(auth_id) for auth_id in scientist]
        self.match_year = int(match_year)
        self.eids = eids
        self.sql_fname = db_path
        self._search_sources = None
        self._candidates = None
        self._matches = None

        # Create logger
        log_path = log_path or DEFAULT_LOG
        create_logger(Path(log_path))

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, match_year, refresh=refresh,
                           db_path=self.sql_fname, verbose=verbose)

    def identify_candidates_from_sources(
        self,
        first_year_margin: int,
        frequency: Optional[int] = None,
        stacked: bool = False,
        verbose: bool = False,
        refresh: Union[bool, int] = False,
    ) -> Self:
        """Define a search group of authors based on their publication
        activity in the search sources between the first year and the
        match year.

        Parameters
        ----------
        first_year_margin : int
            The left margin for year of first publication to identify
            match candidates.

        frequency : int (optional, default=None)
            The maximum gap in number of years between publications of
            suitable candidates, i.e. the average frequency with which they
            publish in these sources.  If not given, will take the average
            frequency (rounded up) of the Orignal:
            `max[1, (match_year - first_year) / number of publications.]`
            Must not be smaller than the first_year_margin.
            To find candidates, the method considers chunks of consecutive
            volumes, and requires candidates to publish at least once in
            each (!) of these chunks.  That is, it generates sets of authors
            publishing in the search sources during specific years, and
            considers only the intersection of these. If the last chunk is
            smaller than half the target chunk size, it will be merged
            with the previous chunk.

        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files will most likely not be reusable.  Set to True if you
            query in distinct fields or to minimize API key usage.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            refresh : bool or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not.  If
            int is passed, results will be refreshed if they are older
            than that value in number of days.

        Notes
        -----
        If candidates have been identified, they are accessible through
        property .candidates.
        """
        # Checks
        if not self.search_sources:
            text = "No search sources defined.  Please run "\
                   ".define_search_sources() first."
            raise RuntimeError(text)
        validate_param(first_year_margin, "first_year_margin", (int,))
        if not frequency:
            n_pubs = len(self.publications)
            frequency = max(1, ceil((self.match_year - self.first_year) / n_pubs))

        # Define variables
        search_sources, _ = zip(*self.search_sources)
        text = f"Identifying candidates using up to {len(search_sources):,} sources..."
        custom_print(text, verbose)

        # Get years to look through
        years = range(self.first_year, self.match_year)
        chunks = chunk_list(years, frequency)
        chunks[0] = range(self.first_year - first_year_margin,
                          max(chunks[0]) + 1)

        # Get authors
        groups = []
        for years in chunks:
            volumes = DataFrame(product(search_sources, years),
                                columns=["source_id", "year"])
            authors = get_authors_from_sourceyear(
                volumes,
                self.sql_conn,
                stacked=stacked,
                refresh=refresh,
                verbose=verbose
            )
            groups.append(flat_set_from_df(authors, "auids"))

        # Compile group
        candidates = set.intersection(*groups)
        candidates = set(map(int, candidates))
        candidates -= set(self.identifier)
        candidates -= set(self.coauthors)

        # Finalize
        self._candidates = sorted(candidates)
        n_candidates = len(candidates)
        text = f"Found {n_candidates:,} candidate{get_ending(n_candidates)}"
        custom_print(text, verbose)
        return self

    def define_search_sources(
            self,
            verbose: bool = False,
            mode: Literal["narrow", "wide"] = "narrow"
    ) -> Self:
        """Define search sources related to the Original.

        Search sources are the set of sources where sosia will search for
        possible candidates.  Search source are of the same types (journal,
        conference proceeding, etc.) the Original published in, and is
        related to the main field (ASCJ-4) of the Original.

        Parameters
        ----------
        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        mode : str (optional, default="narrow")
            Accepted values: "narrow", "wide".
            A "narrow" definition of search sources excludes search sources
            that are also associated to fields (ASJC-4) not among the fields
            of the Original.  A "wide" defintion includes all those sources.

        Notes
        -----
        Search sources are available through property `.search_sources`.
        """
        if mode not in {"narrow", "wide"}:
            raise TypeError("Argument mode must be 'narrow' or 'wide'.")

        field_df = self.field_source
        info_df = self.source_info
        # Sources in scientist's main field
        mask_same_field = field_df["asjc"] == self.main_field[0]
        same_field = set(field_df[mask_same_field]["source_id"].unique())
        # Types of Scientist's sources
        own_source_ids, _ = zip(*self.sources)
        same_sources = info_df["source_id"].isin(own_source_ids)
        main_types = info_df[same_sources]["type"].unique()
        mask_same_types = info_df["type"].isin(main_types)
        same_type = info_df[mask_same_types]["source_id"].unique()
        # Select source IDs
        selected_ids = same_field.intersection(same_type)
        selected = field_df[field_df["source_id"].isin(selected_ids)].copy()
        grouped = selected.groupby("source_id")["asjc"].unique().to_frame()
        # Deselect sources with alien fields
        if mode == "narrow":
            fields = set(self.fields)
            no_alien_field = grouped["asjc"].apply(lambda s: len(set(s) - fields) == 0)
            grouped = grouped[no_alien_field]
        grouped = grouped.drop(columns="asjc")
        # Add source names
        sources = grouped.join(info_df.set_index("source_id")["title"])
        sources = set(sources.reset_index().itertuples(index=False, name=None))
        # Add own sources
        sources.update(self.sources)
        # Finalize
        self._search_sources = sorted(sources, key=lambda x: x[0])
        text = f"Found {len(sources):,} sources of " \
               f"type{get_ending(len(main_types))} " \
               f"{', '.join(main_types)} matching main field "\
               f"{self.main_field[0]} {mode}ly"
        custom_print(text, verbose)
        return self

    def filter_candidates(
            self,
            first_year_margin: Optional[int] = None,
            pub_margin: Optional[Union[float, int]] = None,
            coauth_margin: Optional[Union[float, int]] = None,
            cits_margin: Optional[Union[float, int]] = None,
            same_discipline: Optional[bool] = False,
            verbose: bool = False,
            refresh: Union[bool, int] = False
    ) -> None:
        """Find matches within candidates based on up to five criteria:
        1. Work mainly in the same discipline (as of date of retrieval)
        2. Started publishing in about the same year
        3. Have about the same number of publications in the match year
        4. Have about the same number of coauthors in the match year
        5. Have about the same number of citations in the match year

        Parameters
        ----------
        first_year_margin : numeric (optional, default=None)
            The left and right margin for year of first publication to match
            candidates and the scientist on. If the value is not given,
            sosia will not filter on the first year of publication.

        pub_margin : numeric (optional, default=None)
            The left and right margin for the number of publications to match
            candidates and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientist's number of
            publications and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of publications.
            If the value is not given, sosia will not filter on the number
            of publications.

        coauth_margin : numeric (optional, default=None)
            The left and right margin for the number of coauthors to match
            candidates and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            coauthors and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of coauthors.
            If the value is not given, sosia will not filter on the number
            of coauthors.

        cits_margin : numeric (optional, default=None)
            The left and right margin for the number of citations to match
            candidates and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of citations.
            If the value is not given, sosia will not filter on the number
            of citations.

        same_discipline : boolean (optional, default=False)
            Whether to restrict candidates to the same main discipline (ASJC2)
            as the original scientist or not.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If
            int is passed, results will be refreshed if they are older
            than that value in number of days.

        Notes
        -----
        Matches are available through property `.matches`.
        """
        # Checks
        if not self.candidates:
            text = "No candidates defined.  Please define candidates first."
            raise RuntimeError(text)
        validate_param(first_year_margin, "first_year_margin", (int,))
        validate_param(pub_margin, "pub_margin")
        validate_param(coauth_margin, "coauth_margin")
        validate_param(cits_margin, "cits_margin")

        # Find matches
        group = self.candidates
        text = f"Filtering {len(group):,} candidates..."
        custom_print(text, verbose)

        # First round of filtering: minimum publications and main field
        if same_discipline or pub_margin is not None:
            info = get_author_info(group, self.sql_conn, verbose=verbose,
                                   refresh=refresh)
            if same_discipline:
                same_discipline = info['areas'].str.startswith(self.main_field[1])
                info = info[same_discipline]
                text = (f"... left with {info.shape[0]:,} candidates with same "
                        f"main discipline ({self.main_field[1]})")
                custom_print(text, verbose)
            if pub_margin is not None:
                min_papers = compute_margins(len(self.publications), pub_margin)[0]
                enough_pubs = info['documents'].astype(int) >= min_papers
                info = info[enough_pubs]
                text = (f"... left with {info.shape[0]:,} candidates with "
                        f"sufficient total publications ({min_papers:,})")
                custom_print(text, verbose)
            group = sorted(info["auth_id"].unique())

        # Second round of filtering: first year, publication count, coauthor count
        second_round = (
                (first_year_margin is not None) or
                (pub_margin is not None) or
                (coauth_margin is not None)
        )
        if second_round:
            data = get_author_data(group=group, verbose=verbose,
                                   conn=self.sql_conn, refresh=refresh)
            data = data[data["year"] <= self.match_year]
            if first_year_margin is not None:
                _years = compute_margins(self.first_year, first_year_margin)
                similar_start = data["first_year"].between(*_years)
                data = data[similar_start]
                text = generate_filter_message(data['auth_id'].nunique(), _years,
                                               "year of first publication")
                custom_print(text, verbose)
            data = (data.drop(columns="first_year")
                        .drop_duplicates("auth_id", keep="last"))
            if pub_margin is not None:
                _npapers = compute_margins(len(self.publications), pub_margin)
                similar_pubcount = data["n_pubs"].between(*_npapers)
                data = data[similar_pubcount]
                text = generate_filter_message(data.shape[0], _npapers,
                                               "number of publications")
                custom_print(text, verbose)
            if coauth_margin is not None:
                _ncoauth = compute_margins(len(self.coauthors), coauth_margin)
                similar_coauthcount = data["n_coauth"].between(*_ncoauth)
                data = data[similar_coauthcount]
                text = generate_filter_message(data.shape[0], _ncoauth,
                                               "number of coauthors")
                custom_print(text, verbose)
            group = sorted(data["auth_id"].unique())

        # Third round of filtering: citations
        if cits_margin is not None:
            citations = get_citations(group, self.year, refresh=refresh,
                                      verbose=verbose, conn=self.sql_conn)
            _ncits = compute_margins(self.citations, cits_margin)
            similar_citcount = citations["n_cits"].between(*_ncits)
            citations = citations[similar_citcount]
            text = generate_filter_message(citations.shape[0], _ncits,
                                           "number of citations")
            custom_print(text, verbose)
            group = sorted(citations['auth_id'].unique())

        # Status update
        n_matches = len(group)
        text = f"Found {n_matches:,} match{get_ending(n_matches, 'es')}"
        custom_print(text, verbose)
        self._matches = sorted([int(auth_id) for auth_id in group])

    def inform_matches(
        self,
        fields: Optional[Iterable] = None,
        verbose: bool = False,
        refresh: Union[bool, int] = False,
    ) -> None:
        """Add information to matches to aid in selection process.

        Parameters
        ----------
        fields : iterable (optional, default=None)
            Which information to provide.  Allowed values are "first_name",
            "surname", "first_year", "last_year", "num_coauthors",
            "num_publications", "num_citations", "subjects",
            "affiliation_country", "affiliation_id", "affiliation_name",
            "affiliation_type", "language", "num_cited_refs".  If None, will
            use all available fields.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If
            int is passed, results will be refreshed if they are older
            than that value in number of days.

        Notes
        -----
        Matches including corresponding information are available through
        property `.matches`.

        Raises
        ------
        ValueError
            If `fields` contains invalid keywords.
        """
        # Checks
        if not self._matches:
            text = "No matches defined.  Please run .find_matches() first."
            raise RuntimeError(text)
        allowed_fields = ["first_name", "surname", "first_year", "last_year",
                          "num_coauthors", "num_publications", "num_citations",
                          "subjects", "affiliation_country", "affiliation_id",
                          "affiliation_name", "affiliation_type", "language",
                          "num_cited_refs"]
        if fields:
            invalid = [x for x in fields if x not in allowed_fields]
            if invalid:
                text = "Parameter fields contains invalid keywords: " +\
                       ", ".join(invalid)
                raise ValueError(text)
        else:
            fields = allowed_fields

        n_matches = len(self._matches)
        text = f"Providing information for {n_matches:,} " \
               f"match{get_ending(n_matches, 'es')}..."
        custom_print(text, verbose)
        matches = inform_matches(self, fields, verbose, refresh)
        self._matches = matches
