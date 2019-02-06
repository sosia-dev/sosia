Functioning
===========

Overview
--------

`sosia` (Italian for `doppelgänger <https://en.wikipedia.org/wiki/Doppelg%C3%A4nger>`_) is intended to create control groups for Diff-in-Diff analysis of scientists:  Some treatment happens to a scientist, and you need "similar" scientists to whom nothing happened.  Similiar means:

1. Publishes in sources (journals, book series, etc.) the scientist publishes too
2. Publishes in sources associated with the scientist's main field
3. Publishes in the year of treatment
4. Is not a co-author in the pre-treatment phase
5. In the year of treatment, has about the same number of publications
6. Started publishing around the same year as the scientist
7. In the year of treatment, has about the same number of co-authors

You obtain results after only four steps:

1. Initiate the class
2. Define search sources
3. Define a first search group
4. Filter the search group to obtain a matching group

Depending on the number of search sources and the first search group, one query may take up to 6 hours.  Each query on the Scopus database will make use of your API Key, which allows 5000 requests per week.  `scopus` makes sure that all information are cached, so that subsequent queries will take less than a minute.  The main classes and all methods have a boolean `refresh` parameter, which steers whether to refresh the cached queries (default is `False`).

Initial set-up
--------------

`sosia` infers the scientist's (main )field of research from the field-associations of the sources she publishes in.  To this end, a sources-field list has to be created once.  It will be stored in `~/.sosia/` (that is, in your home drive - on Unix systems this will be a hidden folder).  Create the list like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.create_fields_sources_list()

Step-by-Step
------------

The main class is :doc:`Original <../reference/sosia.Original>`.  You initiate it with the Scopus Author ID, or a list of Scopus Author IDs, of the researcher you are looking for, and the year of treatment:

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2017)

You can provide a list of Scopus Author IDs, in the case the author you are interested in has more than one. All properties and the control group will be based on the publications associated to all Scopus Author IDs and published before the year you provide. You can also set as an optional parameter a list of Scopus EIDs corresponding to a list of publications. If you do so, all properties of the scientists and the control group will be based on the publications in this list only, published before they year you provide: 

.. code-block:: python
   
    >>> eids=['2-s2.0-84959420483', '2-s2.0-84949113230', '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(55208373700, 2017, eids=eids)

A number of optional parameters will be used throughout the query process in order to define "about" similarity.  There are margins for the first year of publication, the number of co-authors and the number of publications:

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2017, year_margin=2,
                           coauth_margin=0.2, pub_margin=0.2)

This will find matches who started publishing the year of the scientist's first publication plus or minus 2 years, who in the year of treatment have the same number of coauthors plus or minus 20% of that number (at least 1), and who in the year of treatment have the same number of publications plus or minus 20% of that number (at least 1).  If the last two parameters receive integers rather than floats, they will be interpreted as absolute margin.

Upon initation, `scopus` performs queries on the Scopus database under the hood.  The information is valid in the year of treatment and used to find similarities:

.. code-block:: python

    >>> stefano.country
    'Switzerland'
    >>> stefano.coauthors
    {'54929867200', '54930777900', '36617057700', '24781156100', '55875219200'}
    >>> stefano.fields
    [1803, 1408, 1405, 1400, 1405, 2002, 2200]
    >>> stefano.first_year
    2012
    >>> stefano.sources
    {18769, 22900, 23013}
    >>> stefano.main_field
    (1405, 'BUSI')
    
Additionally, `stefano.publications` is a list of namedtuples storing information about the indexed publications.  Each property can be manually overriden:

.. code-block:: python

    >>> stefano.country = 'Germany'
    >>> stefano.country
    'Germany'
    >>> stefano.main_field = (1406, 'ECON')
    >>> stefano.main_field
    (1406, 'ECON')

The next step is to define a list of sources similar (in type and area) to the sources the scientist published until the year of treatment.  A source is similar if (i) it is associated to the scientist's main field, (ii) is of the same type(s) of the scientist's sources and (iii) is not associated to fields alien to the scientist.  You define the list of search sources with a method to the class and access the results using a property:

.. code-block:: python

    >>> stefano = Original(55208373700, 2017)
    >>> stefano.define_search_sources()
    >>> stefano.search_sources
    [14726, 16680, 17047, 18769, 19929, 20057, 20206, 20639, 20842, 22009,
    22322, 22369, 22714, 22900, 22949, 23013, 23143, 23656, 24928, 27679,
    28573, 28581, 28988, 29823, 29933, 30858, 36058, 36062, 36921, 38085,
    38845, 50127, 53328, 54314, 55221, 69129, 70932, 84544, 89669, 99221,
    144668, 144961, 145514, 3900148221, 4400151707, 5000156909, 6800153107,
    9500153991, 11600153421, 12100155405, 17700156704, 19700188275,
    19900192158, 21100218364, 21100220151, 21100235612, 21100255419,
    21100307471, 21100431996, 21100874277]

The results is a list of Scopus Source IDs.  As before, you can override (or predefine )your own set of search_sources.

Using `verbose=True` you receive additional information:

.. code-block:: python

    >>> stefano.define_search_sources(verbose=True)
    Found 60 sources for main field 1405 and source type(s) journal

The next step is to define a first search group that adhere to conditions 1 to 4 above and do not violate condition 5 (in the sense that we remove authors have too many publications).


.. code-block:: python

    >>> stefano.define_search_group(verbose=True)
    Searching authors for search_group in 60 sources...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Found 313 authors for search_group

You can inspect the search group using `stefano.search_group`, which you can also override, pre-define or edit.

An alternative search process will try to minimize the number of queries.  The downside is that the resulting query cannot be reused for other searches (of other scientists).  Activate this by setting `stacked=True`:

.. code-block:: python

    >>> stefano.define_search_group(verbose=True, stacked=True)
    Searching authors in 60 sources in 2017...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Searching authors in 60 sources in 2011-2013...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Searching authors in 60 sources in 2010...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Found 527 authors for search_group

The number differs because less information is available.

The final step is to search within this search group for authors that fulfill criteria 5 through 6.  The returned results are a list of `namedtuples <https://docs.python.org/2/library/collections.html#collections.namedtuple>`_ with additional information.  These may help you assess the fit with the researcher.

.. code-block:: python

    >>> matches = stefano.find_matches(verbose=True)
    Searching through characteristics of 527 authors
    Pre-filtering...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Left with 108 authors
    Filtering based on provided conditions...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Found 7 author(s) matching all criteria
    Adding other information...
    Researcher 42661166900: 0 abstract(s) and 0 reference list(s)
    out of 2 documents missing
    Researcher 54893528800: 0 abstract(s) and 0 reference list(s)
    out of 3 documents missing
    Researcher 55268789000: 0 abstract(s) and 0 reference list(s)
    out of 3 documents missing
    Researcher 55353556300: 3 abstract(s) and 0 reference list(s)
    out of 4 documents missing
    Researcher 55611347500: 0 abstract(s) and 0 reference list(s)
    out of 2 documents missing
    Researcher 55916383400: 1 abstract(s) and 0 reference list(s)
    out of 2 documents missing
    Researcher 56282273300: 0 abstract(s) and 0 reference list(s)
    out of 4 documents missing
    Researcher 55208373700 (focal): 0 abstract(s) and 0 reference list(s) out of 4 documents missing
    >>> for m in matches:
    ....    print(m)
    >>> matches
    Match(ID='42661166900', name='Fosaas, Morten', first_year=2011, num_coauthors=4, num_publications=2,
    country='Norway', language='eng', reference_sim=0.0308, abstract_sim=0.0667)
    Match(ID='54893528800', name='Heimonen, Tomi P.', first_year=2011, num_coauthors=3, num_publications=3,
    country='Finland', language='eng', reference_sim=0.0035, abstract_sim=0.0492)
    Match(ID='55268789000', name='Chen, Chun Liang', first_year=2011, num_coauthors=3, num_publications=3,
    country='Taiwan', language='eng', reference_sim=0.0, abstract_sim=0.0298)
    Match(ID='55353556300', name='Rosellon, Maureen Ane D.', first_year=2012, num_coauthors=3, num_publications=4,
    country='Philippines', language='eng', reference_sim=0.0, abstract_sim=0.0314)
    Match(ID='55611347500', name='Zhao, Yingxin', first_year=2013, num_coauthors=4, num_publications=2,
    country='China', language='eng', reference_sim=0.0, abstract_sim=0.0298)
    Match(ID='55916383400', name='Del Prado, Fatima Lourdes E.', first_year=2012, num_coauthors=3, num_publications=2,
    country='Philippines', language='eng', reference_sim=0.0, abstract_sim=0.1004)
    Match(ID='56282273300', name='Rodríguez, José Carlos', first_year=2011, num_coauthors=4, num_publications=4,
    country='Mexico', language='eng', reference_sim=0.0087, abstract_sim=0.1047)

`sosia` provides the following information:

* `ID`: The Scopus Author ID of the match
* `name`: The name of the profile
* `first_year`: The year of the first recorded publication
* `num_coauthors`: The number of coauthors (Scopus Author profiles) in the year of treatment
* `num_publications`: The number of indexed publications in the year of treatment
* `country`: The most frequent country of all affiliations listed on publications most recent to the year of treatment
* `language`: The language(s) of the published documents of an author up until the year of treatment
* `reference_sim`: The cosine similarity of references listed in publications up until the year of treatment between the matched scientist and the scientist (references may be missing)
* `abstract_sim`: The cosine similarity of words used in abstract of publications up until the year of treatment between the matched scientist and the scientist, approriately filtered and stemmed using `nltk <https://www.nltk.org/>`_ and `sklearn <https://scikit-learn.org//>`_ (abstracts my be missing)

It is easy to work with namedtuples.  For example, using `pandas <https://pandas.pydata.org/>`_ you easily turn the list into a pandas DataFrame:

.. code-block:: python

    >>> import pandas as pd
    >>> pd.set_option('display.max_columns', None)
    >>> df = pd.DataFrame(matches)
    >>> df = df.set_index('ID')
    >>> df
                                         name  first_year  num_coauthors  \
    ID                                                                     
    42661166900                Fosaas, Morten        2011              4   
    54893528800             Heimonen, Tomi P.        2011              3   
    55268789000              Chen, Chun Liang        2011              3   
    55353556300      Rosellon, Maureen Ane D.        2012              3   
    55611347500                 Zhao, Yingxin        2013              4   
    55916383400  Del Prado, Fatima Lourdes E.        2012              3   
    56282273300        Rodríguez, José Carlos        2011              4   

                 num_publications      country language  reference_sim  \
    ID                                                                   
    42661166900                 2       Norway      eng         0.0308   
    54893528800                 3      Finland      eng         0.0035   
    55268789000                 3       Taiwan      eng         0.0000   
    55353556300                 4  Philippines      eng         0.0000   
    55611347500                 2        China      eng         0.0000   
    55916383400                 2  Philippines      eng         0.0000   
    56282273300                 4       Mexico      eng         0.0087   

                 abstract_sim  
    ID                         
    42661166900        0.0667  
    54893528800        0.0492  
    55268789000        0.0298  
    55353556300        0.0314  
    55611347500        0.0298  
    55916383400        0.1004  
    56282273300        0.1047

