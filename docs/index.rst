sosia: Automatic author matching in Scopus on-line
==================================================

sosia is a Python library match authors in the Scopus database, using the `scopus package <https://scopus.readthedocs.io/en/latest/index.html>`_.

.. include:: installation.rst


=======
Example
=======

.. code-block:: python

    >>> import sosia
    >>> sosia.create_fields_sources_list()  # Necessary only once
    >>> stefano = sosia.Original(55208373700, 2017)  # Scopus ID and year
    >>> stefano.define_search_sources()  # Sources similiar to scientist
    >>> stefano.define_search_group()  # Authors publishing in similar sources
    >>> matches = stefano.find_matches()  # List of namedtuples
    >>> matches[0]
    Match(ID='42661166900', name='Fosaas, Morten', first_year=2011,
    num_coauthors=4, num_publications=3, country='Norway', reference_sim=0.0238,
    abstract_sim=0.1264)


Full reference:

.. currentmodule:: sosia

.. autosummary::

    Original


==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. Hidden links for Navigation side panel
.. toctree::
   :maxdepth: 2
   :hidden:

   functioning
   reference
   changelog
   authors
   contributing
