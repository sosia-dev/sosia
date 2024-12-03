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
    >>> # You need the Scopus ID and the year, optionally set a database path
    >>> stefano = sosia.Original(55208373700, 2018)
    >>> # Sources similiar to those stefano publishes in
    >>> stefano.define_search_sources()
    >>> # Authors publishing in search sources every 2 years
    >>> stefano.identify_candidates_from_sources(first_year_margin=1,
    >>>                                          frequency=2)
    >>> # Find candidates whose characteristics fall within margins
    >>> stefano.filter_candidates(same_discipline=True, pub_margin=0.2,
    >>>                           first_year_margin=1, cits_margin=0.2,
    >>>                           coauth_margin=0.15)
    >>> print(stefano.matches)
    >>> [55567912500]
    >>> # Optional step to provide additional information
    >>> stefano.inform_matches()
    >>> print(stefano.matches[0])
    Match(ID=55567912500, name='Eling, Katrin', first_name='Katrin',
          surname='Eling', first_year=2013, last_year=2018, num_coauthors=9,
          num_publications=8, num_citations=56, subjects=['BUSI', 'COMP', 'ENGI'],
          affiliation_country='Netherlands', affiliation_id='60032882',
          affiliation_name='Technische Universiteit Eindhoven',
          affiliation_type='univ', language='eng', num_cited_refs=0)

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
