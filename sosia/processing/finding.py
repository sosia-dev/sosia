"""Module with functions for finding matches within the set of candidates."""

from sosia.processing.getting import get_author_data, get_author_info, \
    get_citations
from sosia.processing.utils import compute_margins, generate_filter_message
from sosia.utils import custom_print


def find_matches(original, verbose, refresh):
    """Find matches within the set of candidates.

    Parameters
    ----------
    original : sosia.Original()
        The object containing information for the original scientist to
        search for.  Attribute .candidates needs to exist.

    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.

    refresh : bool, int (optional, default=False)
        Whether to refresh cached results (if they exist) or not, with
        Scopus data that is at most `refresh` days old (True = 0).
    """
    # Variables
    text = f"Filtering {len(original.candidates):,} candidates..."
    custom_print(text, verbose)
    conn = original.sql_conn

    # First round of filtering: minimum publications and main field
    if original.same_discipline or original.pub_margin is not None:
        info = get_author_info(original.candidates, original.sql_conn,
                               verbose=verbose, refresh=refresh)
        if original.same_discipline:
            same_discipline = info['areas'].str.startswith(original.main_field[1])
            info = info[same_discipline]
            text = (f"... left with {info.shape[0]:,} candidates with same "
                    f"main discipline ({original.main_field[1]})")
            custom_print(text, verbose)
        if original.pub_margin is not None:
            min_papers = compute_margins(len(original.publications), original.pub_margin)[0]
            enough_pubs = info['documents'].astype(int) >= min_papers
            info = info[enough_pubs]
            text = (f"... left with {info.shape[0]:,} candidates with "
                    f"sufficient total publications ({min_papers:,})")
            custom_print(text, verbose)
        group = sorted(info["auth_id"].unique())
    else:
        group = original.candidates
    if not group:
        return group

    # Second round of filtering: first year, publication count, coauthor count
    second_round = (
        (original.first_year_margin is not None) or
        (original.pub_margin is not None) or
        (original.coauth_margin is not None)
    )
    if second_round:
        data = get_author_data(group=group, verbose=verbose, conn=conn,
                               refresh=refresh)
        data = data[data["year"] <= original.match_year]
        if original.first_year_margin is not None:
            _years = compute_margins(original.first_year, original.first_year_margin)
            similar_start = data["first_year"].between(*_years)
            data = data[similar_start]
            text = generate_filter_message(data['auth_id'].nunique(), _years,
                                           "year of first publication")
            custom_print(text, verbose)
        data = (data.drop(columns="first_year")
                    .drop_duplicates("auth_id", keep="last"))
        if data.empty:
            return set()
        if original.pub_margin is not None:
            _npapers = compute_margins(len(original.publications), original.pub_margin)
            similar_pubcount = data["n_pubs"].between(*_npapers)
            data = data[similar_pubcount]
            text = generate_filter_message(data.shape[0], _npapers,
                                           "number of publications")
            custom_print(text, verbose)
        if data.empty:
            return set()
        if original.coauth_margin is not None:
            _ncoauth = compute_margins(len(original.coauthors), original.coauth_margin)
            similar_coauthcount = data["n_coauth"].between(*_ncoauth)
            data = data[similar_coauthcount]
            text = generate_filter_message(data.shape[0], _ncoauth,
                                           "number of coauthors")
            custom_print(text, verbose)
        group = sorted(data["auth_id"].unique())
    if not group:
        return group

    # Third round of filtering: citations
    if original.cits_margin is not None:
        citations = get_citations(group, original.year, refresh=refresh,
                                  verbose=verbose, conn=conn)
        _ncits = compute_margins(original.citations, original.cits_margin)
        similar_citcount = citations["n_cits"].between(*_ncits)
        citations = citations[similar_citcount]
        text = generate_filter_message(citations.shape[0], _ncits,
                                       "number of citations")
        custom_print(text, verbose)
        group = sorted(citations['auth_id'].unique())
    if not group:
        return group

    return group
