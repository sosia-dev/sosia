from collections import Counter
from itertools import product

from pandas import DataFrame

from sosia.cache import cache_insert, author_size_in_cache, sources_in_cache
from sosia.processing.queries import query_journal, query_year
from sosia.utils import custom_print, margin_range, print_progress


def filter_pub_counts(group, ybefore, yupto, npapers, yfrom=None,
                      verbose=False):
    """Filter authors based on restrictions in the number of
    publications in different periods, searched by query_size.

    Parameters
    ----------
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
    authors = DataFrame(list(product(group, years_check)),
                        columns=["auth_id", "year"], dtype="int64")
    authors_size = author_size_in_cache(authors)
    au_skip = []
    au_remove = []
    group_tocheck = [x for x in group]
    older_authors = []
    pubs_counts = []
    # use information in cache
    if not authors_size.empty:
        # authors that can be already removed because older
        mask = ((authors_size.year <= ybefore) & (authors_size.n_pubs > 0))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        older_authors.extend(remove)
        au_remove.extend(remove)
        # remove if number of pubs in year is in any case too small
        mask = ((authors_size.year >= yupto) &
                (authors_size.n_pubs < min(npapers)))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        au_remove.extend(remove)
        # authors with no pubs before min year
        mask = (((authors_size.year == ybefore) &
                (authors_size.n_pubs == 0)))
        au_ok_miny = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        # check publications in range
        if yfrom:
            # adjust count by substracting the count before period; keep
            # only authors for which it is possible
            mask = (authors_size.year == yfrom - 1)
            authors_size_bef = authors_size[mask]
            authors_size_bef["year"] = yupto
            authors_size_bef.columns = ["auth_id", "year", "n_pubs_bef"]
            mask = ((authors_size.auth_id.isin(authors_size_bef.
                    auth_id.tolist())) & (authors_size.year == yupto))
            authors_size = authors_size[mask]
            authors_size = authors_size.merge(authors_size_bef,
                on=["auth_id", "year"], how='left').fillna(0)
            authors_size["n_pubs"] = (authors_size["n_pubs"] -
                                      authors_size["n_pubs_bef"])
        # authors that can be already removed because of pubs count
        mask = (((authors_size.year >= yupto) &
                 (authors_size.n_pubs < min(npapers))) |
                ((authors_size.year <= yupto) &
                 (authors_size.n_pubs > max(npapers))))
        remove = (authors_size[mask]["auth_id"].drop_duplicates().tolist())
        au_remove.extend(remove)
        # authors with pubs count within the range before the given year
        mask = (((authors_size.year == yupto) &
                 (authors_size.n_pubs >= min(npapers))) &
                (authors_size.n_pubs <= max(npapers)))
        au_ok_year = (authors_size[mask][["auth_id","n_pubs"]].drop_duplicates())
        # authors ok (match both conditions)
        au_ok = list(set(au_ok_miny).intersection(au_ok_year.auth_id.tolist()))
        pubs_counts = au_ok_year[au_ok_year.auth_id.isin(au_ok)].n_pubs.tolist()
        # authors that match only the first condition, but the second is
        # not known, can skip the first cindition check.
        au_skip = [x for x in au_ok_miny if x not in au_remove + au_ok]
        group = [x for x in group if x not in au_remove]
        group_tocheck = [x for x in group if x not in au_skip + au_ok]
    text = "Left with {} authors based on size information already in "\
           "cache.\n{} to check\n".format(len(group), len(group_tocheck))
    custom_print(text, verbose)
    # Verify the publications before minimum year are 0
    if group_tocheck:
        text = ("Searching through characteristics of {:,} authors \n"
                .format(len(group_tocheck)))
        custom_print(text, verbose)
        print_progress(0, len(group_tocheck), verbose)
        to_loop = [x for x in group_tocheck] # Temporary copy
        for i, au in enumerate(to_loop):
            q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, ybefore + 1)
            size = query("docs", q, size_only=True)
            tp = (au, ybefore, size)
            cache_insert(tp, table="author_size")
            print_progress(i + 1, len(to_loop), verbose)
            if not size == 0:
                group.remove(au)
                group_tocheck.remove(au)
                older_authors.append(au)
        text = "Left with {} authors based on size information before "\
               "minium year\n Filtering based on size query before "\
               "provided year\n".format(len(group))
        custom_print(text, verbose)
    # check the publications before the given year are in range
    group_tocheck.extend(au_skip)
    n = len(group_tocheck)
    if group_tocheck:
        text = "Searching through characteristics of {:,} authors".format(
            len(group_tocheck))
        custom_print(text, verbose)
        print_progress(0, n, verbose)
        for i, au in enumerate(group_tocheck):
            q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, yupto + 1)
            size = query("docs", q, size_only=True)
            tp = (au, yupto, size)
            cache_insert(tp, table="author_size")
            if yfrom and size >= min(npapers):
                q = "AU-ID({}) AND PUBYEAR BEF {}".format(au, yfrom)
                size2 = query("docs", q, size_only=True)
                tp = (au, yfrom - 1, size2)
                cache_insert(tp, table="author_size")
                size = size - size2
            if size < min(npapers) or size > max(npapers):
                group.remove(au)
            else:
                pubs_counts.append(size)
            print_progress(i + 1, n, verbose)
    return group, pubs_counts, older_authors


def search_group_from_sources(self, stacked, verbose, refresh=False):
    """Define groups of authors based on publications from a set of sources.

    Parameters
    ----------
    self : sosia.Original
        The object of the Scientist to search information for.

    verbose : bool (optional, default=False)
        Whether to report on the progress of the process.

    refresh : bool (optional, default=False)
        Whether to refresh cached search files.

    Returns
    -------
    today, then, negative : set
        Set of authors publishing in three periods: During the year of
        treatment, during years to match on, and during years before the
        first publication.
    """
    # Filtering variables
    min_year = self.first_year - self.year_margin
    max_year = self.first_year + self.year_margin
    if self.period:
        max_pubs = max(margin_range(len(self.publications_period),
                       self.pub_margin))
    else:
        max_pubs = max(margin_range(len(self.publications), self.pub_margin))
    years = list(range(min_year, max_year+1))
    today_year = self.year
    search_years = [min_year-1, self.active_year]
    if not self._ignore_first_id:
        search_years.extend(range(min_year, max_year+1))
    search_sources, _ = zip(*self.search_sources)

    # Verbose variables
    n = len(search_sources)
    text = "Searching authors for search_group in {} sources...".format(n)
    custom_print(text, verbose)

    if stacked:  # Make use of SQL cache
        # Get already cached sources from cache
        sources_ys = DataFrame(list(product(search_sources, search_years)),
                               columns=["source_id", "year"])
        _, sources_ys_search = sources_in_cache(sources_ys, refresh=refresh)
        missing_years = set(sources_ys_search.year.tolist())
        # Eventually add information for missing years to cache
        for y in missing_years:
            mask = sources_ys_search.year == y
            _sources_search = sources_ys_search[mask].source_id.tolist()
            res = query_year(y, _sources_search, refresh, verbose)
            cache_insert(res, table="sources")
        # Get full cache
        sources_ys, _ = sources_in_cache(sources_ys, refresh=False)
        # Authors publishing in provided year
        mask = sources_ys.year == self.year
        today = set([au for l in sources_ys[mask].auids.tolist()
                     for au in l])
        # Authors publishing in year(s) of first publication
        if not self._ignore_first_id:
            mask = sources_ys.year.between(min_year, max_year,
                                           inclusive=True)
            auids = sources_ys[mask].auids.tolist()
            then = set([au for l in auids for au in l])
        # Authors with publications before
        auids = sources_ys[sources_ys.year < min_year].auids.tolist()
        negative = set([au for l in auids for au in l])
    else:
        today = set()
        then = set()
        negative = set()
        auth_count = []
        print_progress(0, n, verbose)
        for i, source_id in enumerate(search_sources):
            d = query_journal(source_id, [self.year] + years, refresh)
            today.update(d[str(self.year)])
            if not self._ignore_first_id:
                for y in years:
                    then.update(d[str(y)])
            for y in range(int(min(d.keys())), min_year):
                negative.update(d[str(y)])
            for y in d:
                if int(y) <= self.year:
                    auth_count.extend(d[str(y)])
            print_progress(i + 1, n, verbose)
        c = Counter(auth_count)
        negative.update({a for a, npub in c.items() if npub > max_pubs})

    return today, then, negative
