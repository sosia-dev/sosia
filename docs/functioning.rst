Functioning
===========

`sosia` (Italian for `doppelgänger <https://en.wikipedia.org/wiki/Doppelg%C3%A4nger>`_) is intended to create control groups for Diff-in-Diff analysis of scientists:  Some treatment happens to a scientist, and you need "similar" scientists to whom nothing happened.  Similiar means:

1. Publishes in sources (journals, book series, etc.) the scientist publishes too
2. Publishes in sources associated with the scientist's main field
3. Publishes in the latest year the scientist did as well
4. Is not a co-author in the pre-phase
5. Optional: The main field (ASJC2) is the same as that of the scientist
6. Optional: Started publishing around the same year as the scientist
7. Optional: In the year of comparison, has about the same number of publications
8. Optional: In the year of comparison, has about the same number of co-authors
9. Optional: In the year of comparison, has about the same number of citations (excluding self-ciations)
10. Optional: is affiliated to a similar institution (from a user-provided list of affiliations)

That steps 5 through 10 are optional means that there are no default values, and that you may want to choose to not use a particular filter.  Of course, it would not make sense to not use any of these filters.  Most authors will want to use steps 5 through 9, as this aligns most closely with the literature.

You obtain results after only four steps:

1. Initiate the class
2. Define search sources
3. Define a first search group
4. Filter the search group to obtain a matching group

Depending on the number of search sources and the first search group, one query may take up to 6 hours.  Each query on the Scopus database will make use of your API Key, which allows 5000 requests per week. `sosia` and `pybliometrics` makes sure that all information are cached, so that subsequent queries will take less than a minute.  The main classes and all methods have a boolean `refresh` parameter, which steers whether to refresh the cached queries (default is `False`).
