sosia
=====

Match authors automatically in Scopus on-line

Documentation: https://sosia.readthedocs.io

Development: https://github.com/sosia-dev/sosia

.. image:: https://badge.fury.io/py/sosia.svg
    :target: https://badge.fury.io/py/sosia

.. image:: https://readthedocs.org/projects/sosia/badge/?version=latest
    :target: https://readthedocs.org/projects/sosia/badge/?version=latest

.. image:: https://img.shields.io/pypi/pyversions/sosia.svg
    :target: https://img.shields.io/pypi/pyversions/sosia.svg

.. image:: https://img.shields.io/pypi/l/sosia.svg
    :target: https://img.shields.io/pypi/l/sosia.svg

.. image:: https://api.codeclimate.com/v1/badges/3e10a47fefae831b973a/maintainability
   :target: https://codeclimate.com/github/sosia-dev/sosia/maintainability

Installation
============

Install stable version from PyPI:

.. code:: bash

    pip install sosia

or development version from GitHub repository:

.. code:: bash

    pip install git+https://github.com/sosia-dev/sosia

Functioning
===========

sosia performs a series of queries in the Scopus database using the `pybliometrics package 
<http://pybliometrics.readthedocs.io/>`_.  After configuring your local pybliometrics (providing access credentials and eventually setting cache directories), you are ready to use sosia:

.. inclusion-marker-start
.. code-block:: python

    >>> import sosia
    >>> 
    >>> # You need the Scopus ID and the year, then set the similarity parameters
    >>> stefano = sosia.Original(55208373700, 2019, same_field=True, first_year_margin=2,
    >>>                          pub_margin=0.2, cits_margin=0.2, coauth_margin=0.2)
    >>> stefano.define_search_sources()  # Sources similiar to scientist
    >>> stefano.define_search_group(chunk_size=2)  # Authors publishing in similar sources every 2 years
    >>> stefano.find_matches()  # Find matches satisfying all criteria
    >>> print(stefano.matches)
    >>> [55320703900, 55817553500, 56113324000, 56276429200]
    >>> stefano.inform_matches()  # Optional step to provide additional information
    >>> print(stefano.matches[0])
    Match(ID=55320703900, name='Arts, Sam', first_name='Sam', surname='Arts',
          first_year=2012, num_coauthors=9, num_publications=8, num_citations=74,
          num_coauthors_period=None, num_publications_period=None, num_citations_period=None, subjects=['BUSI', 'ECON', 'DECI'],
          affiliation_country='Belgium', affiliation_id='60025063',
          affiliation_name='KU Leuven', affiliation_type='univ',
          language='eng', num_cited_refs=28)


.. inclusion-marker-end

Change log
==========

Please see `CHANGES.rst <./meta/CHANGES.rst>`_.

Contributing
============

Please see `CONTRIBUTING.rst <CONTRIBUTING.rst>`_.  For the list of contributors see
`AUTHORS.rst <./meta/AUTHORS.rst>`_.

License
=======

MIT License; see `LICENSE <LICENSE>`_.
