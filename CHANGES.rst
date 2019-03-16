Change Log
----------

.. toctree::

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
