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

    pip install git+git://github.com/sosia-dev/sosia

Functioning
===========

.. inclusion-marker-start

sosia performs a series of queries in the Scopus database using the `scopus package 
<http://scopus.readthedocs.io/>`_.  After configuring your local scopus (providing access credentials and eventually setting cache directories), you can use sosia:

.. code-block:: python

    >>> import sosia
    >>> sosia.create_fields_sources_list()  # Necessary only once
    >>> sosia.create_cache()  # Necessary only once
    >>> stefano = sosia.Original(55208373700, 2017)  # Scopus ID and year
    >>> stefano.define_search_sources()  # Sources similiar to scientist
    >>> stefano.define_search_group()  # Authors publishing in similar sources
    >>> matches = stefano.find_matches()  # List of namedtuples
    >>> matches[0]
    Match(ID='53164702100', name='Sapprasert, Koson', first_year=2011,
    num_coauthors=7, num_publications=6, country='Norway', language='eng',
    reference_sim=0.0212, abstract_sim=0.1695)

.. inclusion-marker-end

Change log
==========

Please see `CHANGES.rst <CHANGES.rst>`_.

Contributing
============

Please see `CONTRIBUTING.rst <CONTRIBUTING.rst>`_. For a list of contributors see
`AUTHORS.rst <AUTHORS.rst>`_.

License
=======

MIT License; see `LICENSE <LICENSE>`_.
