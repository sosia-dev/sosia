Change Log
----------

.. toctree::

0.4.1
~~~~~

2020-12-08

* Fix bug when creating a new config.ini.
* Require pybliometrics >= 2.7.2.

0.4
~~~

2020-12-04

* End support for Python 3.5.
* Reorganize config.ini.
* In `Original()`, add parameters "sql_name" and "first_year_search", and rename parameters: "year": "treatment_year", "year_margin": "first_year_margin", "search_affiliations": "affiliations".
* In `Original().find_matches()`, remove parameter "ignore_first_id".
* In `Original()`, change default values for parameters: "year_margin": 0.2, "pub_margin": 0.2, "cits_margin": 0.2, "coauth_margin": 0.2.
* Rename function `create_cache()` to `make_database()`.
* Rename tables in MySQL database: `author_size` becomes `author_pubs`, `author_cits_size` becomes `author_ncits`.
* In `Original().find_matches()` remove parameters "information", "stop_words", "tfidf_kwds"; always create a plain list.
* Add property `.matches` to `Original()`.
* Create new method `Original().inform_matches()` to add additional information to matches.
* Use externally provided list of sources and their fields.
* Remove unused property `Original().city`.
* Raise warning if there are too few publications to determine a field.
* Allow integer values for "refresh" in all instances, require pybliometrics >= 2.7.
* Require numpy.
* Fix bug originating from missing reference EIDs.
* Fix bug originating from missing source IDs.
* Improve documentaton, add tutorial.
* Add citation dunder.

0.3.1
~~~~~

2020-03-17

* Update docs w.r.t. the usage of pybliometrics.
* Add support for Python 3.8 and Python 3.9.
* Add missing required package lxml and require sklearn>=0.22.1.
* Correct verbose output of `.find_matches()` w.r.t. completeness of reference lists and abstracts of matches.
* Check for existence of the search group in `.find_machtes()`.
* In `.find_matches()`, fix bug when attempting to compute the cosine similarity when reference lists or abstracts are completely missing.
* In `.get_publication_language()`, fix bug resulting from bad downloads of abstracts.
* In `Original()`, fix bug resulting from unclean source ID information in Scopus search results.

0.3
~~~

2019-11-26

* Introduce internal SQLite database to store results from stacked queries.
* Comply with pybliometrics 2.2 or higher to make use of integrity_fields.
* In `Original()`, add parameter "num_citations" to filter on the number of citations as well.
* In `Original()`, add paramater "period" to allow for matching on information derived from used-provided period only.
* In `Original()`, add parameter "search_affiliations" to enable subsetting on matches from a list of specific affiliations.
* Add "num_citations" to information of matches.
* Introduce internal config file.
* Attempt to download most recent sources list from scopus.com during `.create_fields_sources_list()`.
* In `find_country()`, add "refresh" parameter and fix bugs related to wrong views and not continuing the search.
* In `get_main_field()` return most common 2-digit ASJC code and most commont 4-digit ASJC field.
* Attempt to extract URL for the Scopus source list via webscraping.
* In `find_matches()`, provide only desired information.
* In `find_matches()`, fix bug with missing references or abstracts.
* Use decorators for methods.

0.2
~~~

2019-02-21

* Introduce new class `Scientist()` to be used as parent class of `Original()` and others.
* Add property `language` to `Scientist()` (and thus `Original()` and matches).
* Allow setting of properties of `Original()` and `Scientist()`.
* Make the provision of additional information of matches optional.
* Add source names to `.sources` and `.search_sources`.
* Re-Download abstract if language information aren't present.
* In `Original()`, allow list of Author IDs.
* In `Original()`, add optional parameter to condition retrieved information on list of EIDs.
* Exclude "multidisciplinary" from list of fields for main field determination.
* Give preference to non-general field during main field determination.
* Use most recent affiliation to identify country.
* Filter focal researcher from `.search_group`.
* Fix bug in computation of relevant year range.
* Fix bug resulting from missing source IDs.
* Fix bug resulting in redundant counts during `.define_search_group()`.
* Use pair-wise tfidf-vectorization (instead of group-wise vectorization).
* When the focal's publications are empty, do not compute similiarity measures.
* In `clean_abstracts()`, remove copyright statement in next-to-last sentence as well.
* Use error messages from scopus to for case-specific error handling.
* Simplify functions and classes and refactor internally.
* Make `stacked_query` robust to group as list of int.
* Enable internal function `query_journal()` to perform stacked queries.

0.1.1
~~~~~

2018-11-25

* Activate method chaining.
* Outsource functions `compute_cosine`, `print_progress`, `margin_range`, `raise_non_empty` and `query` to `utils.py` and add tests for them.
* Fix bugs in `.define_search_group()`, `margin_range()` and `_get_refs()`.
* Implement `clean_abstracts()` to remove copyright statements from abstracts.
* Use sklearn's default settings for tfidf-vectorization of abstracts by default.
* Simplify code.

0.1.0
~~~~~

2018-11-23

* Initial release.
