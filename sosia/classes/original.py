"""Main module of `sosia` containing the `Original` class."""

from pathlib import Path
from itertools import product
from typing import Iterable, Literal, Optional, Union

from pandas import DataFrame
from typing_extensions import Self

from sosia.classes import Scientist
from sosia.processing import add_source_names, chunk_list, find_matches, \
    flat_set_from_df, get_authors_from_sourceyear, inform_matches
from sosia.utils import accepts, custom_print


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
        """The set of sources (journals, books) comparable to the sources
        the scientist published in until the treatment year.
        A source is comparable if it belongs to the scientist's main field
        but not to fields alien to the scientist, and if the types of the
        sources are the same as the types of the sources in the scientist's
        main field where she published in.

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
        first_year_margin: Optional[int] = None,
        pub_margin: Optional[Union[float, int]] = None,
        coauth_margin: Optional[Union[float, int]] = None,
        cits_margin: Optional[Union[float, int]] = None,
        same_discipline: Optional[bool] = False,
        eids: Optional[list[Union[str, int]]] = None,
        refresh: Union[bool, int] = False,
        db_path: Optional[Union[str, Path]] = None,
        verbose: Optional[bool] = False
    ) -> None:
        """Representation of a scientist for whom to find matches.

        Parameters
        ----------
        scientist : str, int or list of str or int
            Scopus Author ID, or list of Scopus Author IDs, of the scientist
            to find a control scientist for.

        match_year : str or numeric
            Year in which the comparison takes place.  Control scientist will
            be matched on trends and characteristics of the original
            scientist up to this year.

        first_year_margin : numeric (optional, default=None)
            The left and right margin for year of first publication to match
            possible matches and the scientist on. If the value is not given,
            sosia will not filter on the first year of publication.

        pub_margin : numeric (optional, default=None)
            The left and right margin for the number of publications to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientist's number of
            publications and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of publications.
            If the value is not given, sosia will not filter on the number
            of publications.

        coauth_margin : numeric (optional, default=None)
            The left and right margin for the number of coauthors to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            coauthors and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of coauthors.
            If the value is not given, sosia will not filter on the number
            of coauthors.

        cits_margin : numeric (optional, default=None)
            The left and right margin for the number of citations to match
            possible matches and the scientist on.  If the value is a float,
            it is interpreted as percentage of the scientists number of
            publications and the resulting value is rounded up.  If the value
            is an integer, it is interpreted as fixed number of citations.
            If the value is not given, sosia will not filter on the number
            of citations.

        same_discipline : boolean (optional, default=False)
            Whether to restrict candidates to the same main discipline (ASJC2)
            as the original scientist or not.

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

        db_path : str or pathlib.Path (optional, default=None)
            The path of the SQLite database to connect to.  If None,
            will default to `~/.cache/sosia/main.sqlite`.  Will be created
            if the database doesn't exist.

        verbose : bool (optional, default=False)
            Whether to report on the initialization process.
        """
        # Internal checks
        if first_year_margin is not None and not isinstance(first_year_margin, (int, float)):
            raise TypeError("Argument first_year_margin must be float or integer.")
        if pub_margin is not None and not isinstance(pub_margin, (int, float)):
            raise TypeError("Argument pub_margin must be float or integer.")
        if coauth_margin is not None and not isinstance(coauth_margin, (int, float)):
            raise TypeError("Argument coauth_margin must be float or integer.")
        if cits_margin is not None and not isinstance(cits_margin, (int, float)):
            raise TypeError("Argument cits_margin must be float or integer.")

        # Variables
        if not isinstance(scientist, list):
            scientist = [scientist]
        self.identifier = [int(auth_id) for auth_id in scientist]
        self.match_year = int(match_year)
        self.first_year_margin = first_year_margin
        self.pub_margin = pub_margin
        self.coauth_margin = coauth_margin
        self.cits_margin = cits_margin
        self.same_discipline = same_discipline
        self.eids = eids
        self.refresh = refresh
        self.sql_fname = db_path
        self._search_sources = None
        self._candidates = None
        self._matches = None

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, match_year, refresh=refresh,
                           db_path=self.sql_fname, verbose=verbose)

    def identify_candidates_from_sources(
        self,
        chunk_size: int = 2,
        stacked: bool = False,
        verbose: bool = False,
        refresh: Union[bool, int] = False,
    ) -> Self:
        """Define a search group of authors based on their publication
        activity in the Orginal's search sources between the first year
        and the match year.  To find candidates, the method considers
        chunks of consecutive volumes, and requires candidates to publish
        at least once in each (!) of these chunks.  That is, it generates
        sets of authors publishing in the search sources during specific
        years, and considers only the intersection of these.

        Parameters
        ----------
        chunk_size : int (optional, default=2)
            The size of each set in terms of years, i.e. how many years
            each chunk will contain.  Must not be smaller than the
            first_year_margin.  If the last chunk is smaller than half the
            target chunk size, it will be merged with the previous chunk.
            Put differently: candidates need to appear in the search sources
            on average at least every `chunk_size` years.

        stacked : bool (optional, default=False)
            Whether to combine searches in few queries or not.  Cached
            files will most likely not be reusable.  Set to True if you
            query in distinct fields or you want to minimize API key usage.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            refresh : bool or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not.  If
            int is passed, results will be refreshed if they are older
            than that value in number of days.

        Raises
        ------
        ValueError
            If the chunk_size is smaller than the first_year_margin.

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
        if chunk_size < self.first_year_margin:
            msg = f"Parameter 'chunk_size' must not be smaller " \
                  f"than {self.first_year_margin} ('first_year_margin')."
            raise ValueError(msg)

        # Define variables
        search_sources, _ = zip(*self.search_sources)
        text = f"Identifying candidates using up to {len(search_sources):,} sources..."
        custom_print(text, verbose)

        # Get years to look through
        years = range(self.first_year, self.match_year)
        chunks = chunk_list(years, chunk_size)
        chunks[0] = range(self.first_year - self.first_year_margin,
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
        text = f"Found {len(candidates):,} candidates"
        custom_print(text, verbose)
        return self

    def define_search_sources(
            self,
            verbose: bool = False,
            mode: Literal["narrow", "wide"] = "narrow"
    ) -> Self:
        """Define .search_sources.

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
        suffix = "" if len(main_types) == 1 else "s"
        text = f"Found {len(sources):,} sources of type{suffix} " \
               f"{', '.join(main_types)} matching main field "\
               f"{self.main_field[0]} {mode}ly"
        custom_print(text, verbose)
        return self

    def filter_candidates(
            self,
            verbose: bool = False,
            refresh: Union[bool, int] = False
    ) -> None:
        """Find matches within candidates based on up to five criteria:
        1. Work mainly in the same discipline
        2. Started publishing in about the same year
        3. Have about the same number of publications in the match year
        4. Have about the same number of coauthors in the match year
        5. Have about the same number of citations in the match year

        Parameters
        ----------
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

        # Find matches
        matches = find_matches(self, verbose, refresh)
        if len(matches) == 1:
            ending = ""
        else:
            ending = "es"
        text = f"Found {len(matches):,} match{ending}"
        custom_print(text, verbose)
        self._matches = sorted([auth_id for auth_id in matches])

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

        text = f"Providing information for {len(self._matches):,} matches..."
        custom_print(text, verbose)
        matches = inform_matches(self, fields, verbose, refresh)
        self._matches = matches
