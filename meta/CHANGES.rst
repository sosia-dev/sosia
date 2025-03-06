Change Log
##########

.. toctree::

1.0.1
*****

2025-03-06

* Fix potential bug during extraction of yearly author data due to malformatted response.
* Insert author information and yearly author data into local database more often.
* Fix mistakes in documentation.

1.0.0
*****

2024-11-23

* In `Original()`, rename parameter `sql_fname` to `db_path` and parameter `treatment_year` to `match_year`; add parameter `verbose`; drop parameters `affiliations`, `cits_margin`, `coauth_margin`, `first_year_margin`, `first_year_search`, `period`, `pub_margin`, `same_field`; rename properties `.active_year` to `.last_year` and `.search_group` to `.candidates`.
* In method `Original().define_search_sources`, add parameter `mode` for narrow and wide definition of search sources.
* Rename method `Original().define_search_group()` to `Original().identify_candidates_from_sources()` and add optional parameter `frequency` to use a specified overlap of authors publishing in the search sources (rather than the publication around the first year and the active/last year).
* Rename method `Original().find_matches()` to `Original().filter_candidates()`; drop parameter `stacked`; add parameters `same_discipline`, `first_year_margin`, `pub_margin`, `coauth_margin`, `cits_margin`.
* `Original().coauthors` is now a sorted list.
* Restrict all analysis to research-type articles.
* Fix bug with incomplete bulk author searches.
* Fix bug with progress bars in verbose mode.
* Fix bug with citations filter step not being refreshed.
* Fix bug with coauthor count using own ID.
* Fix bug with missing author information due to nonexistent profiles.
* In `Scientist()`, add parameter `verbose`.
* `Original()` now invokes `make_database()` if the provided SQLite database doesn't exist, as well as `get_field_source_information()` if source definitions do not exist.
* In `Original.inform_matches()`, add field `last_year`.
* In `get_field_source_information()`, add parameter `verbose`.
* In `make_database()`, add parameter `verbose`.
* Drop support for Python 3.6, 3.7, and 3.8; add support for Python 3.10, 3.11, and 3.12.
* Refactor locally used SQLite database.
* Log all Scopus queries using the logging module.
* Optimize Scopus queries.
* Make verbose statements more explicit and use actually used values.
* Improve all documentation and document all classes and methods.
* Introduce type hints for all functions and methods.

Migration Guide
===============

There are four changes users need to be aware of going from 0.6.2 to 1.0:
1. User neither needs to invoke `sosia.get_field_source_information()` nor `sosia.make_database()` themselves. If the relevant files aren't present, a simple call of `Original()` will invoke the required functions. It may still make sense to use the function manually: `sosia.get_field_source_information()` should be used to update the source information (in spring and in fall each year, check out `this repo <https://github.com/sosia-dev/sosia-data>_`), and `sosia.make_database()` can be used to drop tables.
2. All search parameters previously used in `Scientist()` have been moved to the respective functions. Users thus pass match margins where they are used.
3. There are no more default values for the search parameters in `Original().filter_candidates()`. If no values are passed, the respective filter won't apply!
4. Some functions have been renamed: `Original().define_search_group()` became `Original().identify_candidates_from_sources()`, and `Original().find_matches()` became `Original().filter_candidates()`.

In sum, the previous snippet

.. code-block:: python

    >>> import sosia

    >>> sosia.get_field_source_information()
    >>> sosia.make_database()

    >>> stefano = sosia.Original(55208373700, 2019)
    >>> stefano.define_search_sources()
    >>> stefano.define_search_group()
    >>> stefano.find_matches()
    >>> stefano.inform_matches()

becomes this snippet:

.. code-block:: python

    >>> import sosia

    >>> stefano = sosia.Original(55208373700, 2019)
    >>> stefano.define_search_sources()
    >>> stefano.identify_candidates_from_sources(
    >>>     first_year_margin=0.2, frequency=4)
    >>> stefano.filter_candidates(same_discipline=True,
    >>>     first_year_margin=2, pub_margin=0.2,
    >>>     coauth_margin=0.2, cits_margin=0.2)
    >>> stefano.inform_matches()

However, this will not yield quite the same matches, as the definition of candidates (formerly search group) underwent a drastic change. Previously, `sosia` considered only authors that published in two periods: The exact same year when the focal author published for the last time (the last year, formerly the active year), and in the provided margin around the first year.

Now, to be considered a candidate, an author must have publications in multiple periods, each matching the 'frequency' parameter in length. Think of this as the average publication duration of an author. If "frequency" is not given, `sosia` infers the publication frequency of the focal author by dividing the number of publications through the number of years between the match year and the inferred first year.

0.6.2
*****

2024-08-13

* Fix bug related to searching information for authors in the search group via Scopus Author Search API.
* Fix bugs related to the progress bars.
* Improve, update and fix documentation.

0.6.1
*****

2023-11-05

* Rename `.create_fields_sources_list()` to `.get_field_source_information()`.
* Use `tqdm` to print progress bars.
* Adopt improved format of field-source assignment and source information.
* Upgrade third-party code usage.
* Improve documentation, add copy-code button, update code examples.

0.6
***

2023-04-23

* Drop usage of configuration file and recommend project-specific databases.
* In class `Scientist()`, rename properties: `.country` -> `.affiliation_country`, `.affiliation` -> `.affiliation_name`.
* In class `Scientist()`, create property `.affiliation_type`.
* In `.create_fields_sources_list()`, make use of parameter "verbose".
* Make retrieval of affiliation related information robust to missing information (404 error).
* Pass on "refresh" parameter from `inform_matches()`.
* Use pyproject.toml for packaging, drop `pbr` (PEP 621).
* Use XDG compliant file storage for support files in `~/.cache/sosia/`.
* Improve various methods and functions for stability and speed.

0.5
***

2022-01-20

* In `.inform_matches()`, remove abstract similarity and reference list similarity computation and corresponding keywords "abstract_sim" and "reference_sim"; do not require `nltk` and `scikit-learn` anymore.
* In `.inform_matches()`, add "num_cited_refs" as number of jointly cited references up until provided year.
* Increase robustness to Scopus server problems.
* Allow to refresh downloaded results when using very large stacked source-based searches.
* Fix bug with integer conversion when using pandas > 1.1.5.
* Require pybliometrics >= 3.2.0.

0.4.1
*****

2020-12-08

* Fix bug when creating a new config.ini.
* Require pybliometrics >= 2.7.2.

0.4
***

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
* Improve documentation, add tutorial.
* Add citation dunder.

0.3.1
*****

2020-03-17

* Update docs w.r.t. the usage of pybliometrics.
* Add support for Python 3.8 and Python 3.9.
* Add missing required package lxml and require sklearn>=0.22.1.
* Correct verbose output of `.find_matches()` w.r.t. completeness of reference lists and abstracts of matches.
* Check for existence of the search group in `.find_matches()`.
* In `.find_matches()`, fix bug when attempting to compute the cosine similarity when reference lists or abstracts are completely missing.
* In `.get_publication_language()`, fix bug resulting from bad downloads of abstracts.
* In `Original()`, fix bug resulting from unclean source ID information in Scopus search results.

0.3
***

2019-11-26

* Introduce internal SQLite database to store results from stacked queries.
* Comply with pybliometrics 2.2 or higher to make use of integrity_fields.
* In `Original()`, add parameter "num_citations" to filter on the number of citations as well.
* In `Original()`, add parameter "period" to allow for matching on information derived from user-provided period only.
* In `Original()`, add parameter "search_affiliations" to enable subsetting on matches from a list of specific affiliations.
* Add "num_citations" to information of matches.
* Introduce internal config file.
* Attempt to download the most recent sources list from scopus.com during `.create_fields_sources_list()`.
* In `find_country()`, add "refresh" parameter and fix bugs related to wrong views and not continuing the search.
* In `get_main_field()` return the most common 2-digit ASJC code and the most common 4-digit ASJC field.
* Attempt to extract URL for the Scopus source list via web scraping.
* In `find_matches()`, provide only desired information.
* In `find_matches()`, fix bug with missing references or abstracts.
* Use decorators for methods.

0.2
***

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
* When the focal's publications are empty, do not compute similarity measures.
* In `clean_abstracts()`, remove copyright statement in next-to-last sentence as well.
* Use error messages from scopus for case-specific error handling.
* Simplify functions and classes and refactor internally.
* Make `stacked_query` robust to group as list of int.
* Enable internal function `query_journal()` to perform stacked queries.

0.1.1
*****

2018-11-25

* Activate method chaining.
* Outsource functions `compute_cosine`, `print_progress`, `margin_range`, `raise_non_empty` and `query` to `utils.py` and add tests for them.
* Fix bugs in `.define_search_group()`, `margin_range()` and `_get_refs()`.
* Implement `clean_abstracts()` to remove copyright statements from abstracts.
* Use sklearn's default settings for tfidf-vectorization of abstracts by default.
* Simplify code.

0.1.0
*****

2018-11-23

* Initial release.
