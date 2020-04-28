Functioning
===========

`sosia` (Italian for `doppelgänger <https://en.wikipedia.org/wiki/Doppelg%C3%A4nger>`_) is intended to create control groups for Diff-in-Diff analysis of scientists:  Some treatment happens to a scientist, and you need "similar" scientists to whom nothing happened.  Similiar means:

1. Publishes in sources (journals, book series, etc.) the scientist publishes too
2. Publishes in sources associated with the scientist's main field
3. Publishes in the year of treatment
4. Is not a co-author in the pre-treatment phase
5. In the year of treatment, has about the same number of publications
6. Started publishing around the same year as the scientist
7. In the year of treatment, has about the same number of co-authors
8. In the year of treatment, has about the same number of citations (excluding self-ciations)
9. Optional: is affiliated to a similar institution (from a user-provided list of affiliations)

You obtain results after only four steps:

1. Initiate the class
2. Define search sources
3. Define a first search group
4. Filter the search group to obtain a matching group

Depending on the number of search sources and the first search group, one query may take up to 6 hours.  Each query on the Scopus database will make use of your API Key, which allows 5000 requests per week. `sosia` and `pybliometrics` makes sure that all information are cached, so that subsequent queries will take less than a minute.  The main classes and all methods have a boolean `refresh` parameter, which steers whether to refresh the cached queries (default is `False`).
