from itertools import product

from pandas import DataFrame

from sosia.processing.caching import insert_data, retrieve_author_pubs,\
    retrieve_authors_year
from sosia.processing.querying import base_query
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

    Returns
    -------
    group : list of str
        Scopus IDs filtered.

    pubs_counts : list of int
        List of count of publications within the period provided for authors
        in group.

    older_authors : list of str
        Scopus IDs filtered out because have publications before ybefore.

    Notes
    -----
    It uses cached values first, and searches for more data if needed.
    """
    group = [int(x) for x in group]
    years_check = [ybefore, yupto]
    if yfrom:
        years_check.extend([yfrom - 1])
    authors = DataFrame(product(group, years_check), dtype="int64",
                        columns=["auth_id", "year"])
    authors_size = retrieve_author_pubs(authors, conn)
    au_skip = []
    group_tocheck = set(group)
    older_authors = []
    pubs_counts = []
    # Use information in cache
    if not authors_size.empty:
        # Remove authors based on age
        mask = ((authors_size.year <= ybefore) & (authors_size.n_pubs > 0))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        older_authors.extend(remove)
        au_remove = set(remove)
        # Remove if number of pubs in year is in any case too small
        mask = ((authors_size.year >= yupto) &
                (authors_size.n_pubs < min(npapers)))
        au_remove.update(authors_size[mask]["auth_id"])
        # Authors with no pubs before min year
        mask = (((authors_size.year == ybefore) & (authors_size.n_pubs == 0)))
        au_ok_miny = set(authors_size[mask]["auth_id"].unique())
        # Check publications in range
        if yfrom:
            # Adjust count by substracting the count before period; keep
            # only authors for which this is possible
            mask = (authors_size.year == yfrom-1)
            rename = {"n_pubs": "n_pubs_bef"}
            authors_size_bef = authors_size[mask].copy().rename(columns=rename)
            authors_size_bef["year"] = yupto
            authors_size = (authors_size.merge(authors_size_bef, "inner",
                                               on=["auth_id", "year"])
                                        .fillna(0))
            authors_size["n_pubs"] -= authors_size["n_pubs_bef"]
        # Remove authors because of their publication count
        mask = (((authors_size.year >= yupto) &
                 (authors_size.n_pubs < min(npapers))) |
                ((authors_size.year <= yupto) &
                 (authors_size.n_pubs > max(npapers))))
        remove = authors_size[mask]["auth_id"]
        au_remove.update(remove)
        # Authors with pubs count within the range before the given year
        mask = (((authors_size.year == yupto) &
                 (authors_size.n_pubs >= min(npapers))) &
                (authors_size.n_pubs <= max(npapers)))
        au_ok_year = authors_size[mask][["auth_id", "n_pubs"]].drop_duplicates()
        # Keep authors that match both conditions
        au_ok = au_ok_miny.intersection(au_ok_year["auth_id"])
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
               "information in cache..."
        custom_print(text, verbose)
        print_progress(0, n, verbose)
        to_loop = [x for x in group_tocheck]  # Temporary copy
        for i, au in enumerate(to_loop):
            q = f"AU-ID({au}) AND PUBYEAR BEF {ybefore+1}"
            size = base_query("docs", q, size_only=True)
            tp = (au, ybefore, size)
            insert_data(tp, conn, table="author_pubs")
            if size > 0:
                group.remove(au)
                group_tocheck.remove(au)
                older_authors.append(au)
            print_progress(i+1, len(to_loop), verbose)
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
            q = f"AU-ID({au}) AND PUBYEAR BEF {yupto+1}"
            n_pubs_yupto = base_query("docs", q, size_only=True)
            tp = (au, yupto, n_pubs_yupto)
            insert_data(tp, conn, table="author_pubs")
            # Eventually decrease publication count
            if yfrom and n_pubs_yupto >= min(npapers):
                q = f"AU-ID({au}) AND PUBYEAR BEF {yfrom}"
                n_pubs_yfrom = base_query("docs", q, size_only=True)
                tp = (au, yfrom-1, n_pubs_yfrom)
                insert_data(tp, conn, table="author_pubs")
                n_pubs_yupto -= n_pubs_yfrom
            if n_pubs_yupto < min(npapers) or n_pubs_yupto > max(npapers):
                group.remove(au)
            else:
                pubs_counts.append(n_pubs_yupto)
            print_progress(i+1, n, verbose)
    return group, pubs_counts, older_authors
