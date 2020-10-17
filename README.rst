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

sosia performs a series of queries in the Scopus database using the `pybliometrics package 
<http://pybliometrics.readthedocs.io/>`_.  After configuring your local pybliometrics (providing access credentials and eventually setting cache directories), you can use sosia:

.. inclusion-marker-start
.. code-block:: python

    >>> import sosia
    >>> 
    >>> sosia.create_fields_sources_list()  # Necessary only once
    >>> sosia.make_database()  # Necessary only once
    >>> 
    >>> stefano = sosia.Original(55208373700, 2019)  # Scopus ID and year
    >>> stefano.define_search_sources()  # Sources similiar to scientist
    >>> stefano.define_search_group()  # Authors publishing in similar sources
    >>> stefano.find_matches()  # Find matches satisfying all criteria
    >>> print(stefano.matches)
    >>> ['55022752500', '55810688700', '55824607400']
    >>> stefano.inform_matches()  # Optional step to provide additional information
    >>> print(stefano.matches[0])
    Match(ID='55022752500', name='Van der Borgh, Michel', first_name='Michel',
    surname='Van der Borgh', first_year=2012, num_coauthors=6, num_publications=5,
    num_citations=33, num_coauthors_period=6, num_publications_period=5,
    num_citations_period=33, subjects=['BUSI', 'COMP', 'SOCI'], country='Netherlands',
    affiliation_id='60032882', affiliation='Eindhoven University of Technology,
    Department of Industrial Engineering & Innovation Sciences', language='eng',
    reference_sim=0.0, abstract_sim=0.1217)


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
