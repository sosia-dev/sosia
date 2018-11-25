Change Log
----------

.. toctree::

0.1.1
~~~~~

2018-11-25

* Activate method chaining
* Outsource functions `compute_cosine`, `print_progress`, `margin_range`, `raise_non_empty` and `query` to `utils.py` and add tests for them.
* Fix bugs in `.define_search_group()`, `margin_range()` and `_get_refs()`.
* Implement `clean_abstracts()` to remove copyright statements from abstracts.
* Use sklearn's default settings for tfidf-vectorization of abstracts by default.
* Simplify code.

0.1.0
~~~~~

2018-11-23

* Initial release.
