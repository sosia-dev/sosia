from itertools import product

from pandas import DataFrame

from sosia.processing.caching import auth_npubs_retrieve_insert,\
    retrieve_author_info
from sosia.utils import custom_print, print_progress


def filter_pub_counts(group, conn, ybefore, yupto, npapers, yfrom=None,
                      verbose=False):
    """Filter authors based on restrictions in the number of
    publications in different periods, searched by query_size.

    Parameters
    ----------
    conn : sqlite3 connection
        Standing connection to a SQLite3 database.

    group : list of str
        Scopus IDs of authors to be filtered.

    ybefore : int
        Year to be used as first year. Publications on this year and before
        need to be 0.

    yupto : int
        Year up to which to count publications.

    npapers : list
        List of count of publications, minimum and maximum.

    yfrom : int (optional, default=None)
        If provided, publications are counted only after this year.
        Publications are still set to 0 before ybefore.

    verbose : bool (optional, default=False)
        Whether to print information on the search progress.

    Returns
    -------
    group : list of str
        Scopus IDs filtered.

    pubs_counts : list of int
        List of count of publications within the period provided for authors
        in group.

    older_authors : list of str
        Scopus IDs filtered out because have publications before ybefore.
    """
    group = [int(x) for x in group]
    years_check = [ybefore, yupto]
    if yfrom:
        years_check.extend([yfrom - 1])
    authors = DataFrame(product(group, years_check), dtype="int64",
                        columns=["auth_id", "year"])
    auth_npubs, _ = retrieve_author_info(authors, conn, "author_pubs")
    au_skip = []
    group_tocheck = set(group)
    older_authors = []
    pubs_counts = []
    # Use information in database
    if not auth_npubs.empty:
        # Remove authors based on age
        mask = ((auth_npubs["year"] <= ybefore) & (auth_npubs["n_pubs"] > 0))
        au_remove = set(auth_npubs[mask]["auth_id"].unique())
        older_authors.extend(au_remove)
        # Remove if number of pubs in year is in any case too small
        mask = ((auth_npubs["year"] >= yupto) &
                (auth_npubs["n_pubs"] < min(npapers)))
        au_remove.update(auth_npubs[mask]["auth_id"])
        # Authors with no pubs before min year
        mask = ((auth_npubs["year"] == ybefore) & (auth_npubs["n_pubs"] == 0))
        au_ok_miny = set(auth_npubs[mask]["auth_id"].unique())
        # Check publications in range
        if yfrom:
            # Keep authors where subtracting publications from before period
            # from publication count is possible
            mask = auth_npubs["year"] == yfrom-1
            rename = {"n_pubs": "n_pubs_bef"}
            auth_npubs_bef = auth_npubs[mask].copy().rename(columns=rename)
            auth_npubs_bef["year"] = yupto
            auth_npubs = (auth_npubs.merge(auth_npubs_bef, "inner",
                                           on=["auth_id", "year"])
                                    .fillna(0))
            auth_npubs["n_pubs"] -= auth_npubs["n_pubs_bef"]
        # Remove authors because of their publication count
        mask = (((auth_npubs["year"] >= yupto) &
                 (auth_npubs["n_pubs"] < min(npapers))) |
                ((auth_npubs["year"] <= yupto) &
                 (auth_npubs["n_pubs"] > max(npapers))))
        remove = auth_npubs[mask]["auth_id"]
        au_remove.update(remove)
        # Authors with pubs count within the range before the given year
        mask = (((auth_npubs["year"] == yupto) &
                 (auth_npubs["n_pubs"] >= min(npapers))) &
                (auth_npubs["n_pubs"] <= max(npapers)))
        au_ok_year = auth_npubs[mask][["auth_id", "n_pubs"]].drop_duplicates()
        # Keep authors that match both conditions
        au_ok = au_ok_miny.intersection(au_ok_year["auth_id"].unique())
        mask = au_ok_year["auth_id"].isin(au_ok)
        pubs_counts = au_ok_year[mask]["n_pubs"].tolist()
        # Skip citation check for authors that match only the first condition,
        # with the second being unknown
        au_skip = set([x for x in au_ok_miny if x not in au_remove | au_ok])
        group = [x for x in group if x not in au_remove]
        group_tocheck = set([x for x in group if x not in au_skip | au_ok])

    # Verify that publications before minimum year are 0
    if group_tocheck:
        n = len(group_tocheck)
        text = f"Obtaining information for {n:,} authors without sufficient "\
               "information in database..."
        custom_print(text, verbose)
        print_progress(0, n, verbose)
        to_loop = [x for x in group_tocheck]  # Temporary copy
        for i, auth_id in enumerate(to_loop):
            npubs_ybefore = auth_npubs_retrieve_insert(auth_id, ybefore, conn)
            if npubs_ybefore:
                group.remove(auth_id)
                group_tocheck.remove(auth_id)
                older_authors.append(auth_id)
            print_progress(i+1, n, verbose)
        text = f"Left with {len(group):,} authors based on publication "\
               f"information before {ybefore}"
        custom_print(text, verbose)

    # Verify that publications before the given year fall in range
    group_tocheck.update(au_skip)
    if group_tocheck:
        n = len(group_tocheck)
        text = f"Counting publications of {n:,} authors before {yupto+1}..."
        custom_print(text, verbose)
        print_progress(0, n, verbose)
        for i, au in enumerate(group_tocheck):
            n_pubs_yupto = auth_npubs_retrieve_insert(au, yupto, conn)
            # Eventually decrease publication count
            if yfrom and n_pubs_yupto >= min(npapers):
                n_pubs_yfrom = auth_npubs_retrieve_insert(au, yfrom-1, conn)
                n_pubs_yupto -= n_pubs_yfrom
            if n_pubs_yupto < min(npapers) or n_pubs_yupto > max(npapers):
                group.remove(au)
            else:
                pubs_counts.append(n_pubs_yupto)
            print_progress(i+1, n, verbose)
    return group, pubs_counts, older_authors


def same_affiliation(original, new, refresh=False):
    """Whether a new scientist shares affiliation(s) with the
    original scientist.
    """
    from sosia.classes import Scientist

    period = original.year + 1 - original._period_year
    m = Scientist([str(new)], original.year, period=period, refresh=refresh,
                  sql_fname=original.sql_fname)
    return any(str(a) in m.affiliation_id for a in original.search_affiliations)
