from collections import Counter
from itertools import product

from pandas import DataFrame

from sosia.cache import cache_insert, sources_in_cache
from sosia.processing.queries import query_journal, query_year
from sosia.utils import custom_print, margin_range, print_progress


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
