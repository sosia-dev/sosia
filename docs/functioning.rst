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
8. In the year of treatment, has about the same number of citations (excluding self-ciations)
9. Optional: is affiliated to a similar institution (from a user-provided list of affiliations)

You obtain results after only four steps:

1. Initiate the class
2. Define search sources
3. Define a first search group
4. Filter the search group to obtain a matching group

Depending on the number of search sources and the first search group, one query may take up to 6 hours.  Each query on the Scopus database will make use of your API Key, which allows 5000 requests per week. `sosia` and `scopus` makes sure that all information are cached, so that subsequent queries will take less than a minute.  The main classes and all methods have a boolean `refresh` parameter, which steers whether to refresh the cached queries (default is `False`).

Initial set-up
--------------

`sosia` infers the scientist's (main )field of research from the field-associations of the sources she publishes in.  To this end, a sources-field list has to be created once.  It will be stored in `~/.sosia/` (that is, in your home drive - on Unix systems this will be a hidden folder).  Create the list like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.create_fields_sources_list()
    >>> sosia.create_cache()

There will also be a list linking source titles and source IDs.

Step-by-Step
------------

The main class is :doc:`Original <../reference/sosia.Original>`.  You initiate it with the Scopus Author ID, or a list of Scopus Author IDs, of the researcher you are looking for, and the year of treatment:

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2017)

You can provide a list of Scopus Author IDs, in the case the author you are interested in has more than one. All properties and the control group will be based on the publications associated to all Scopus Author IDs and published before the year you provide. You can also set as an optional parameter a list of Scopus EIDs corresponding to a list of publications. If you do so, all properties of the scientists and the control group will be based on the publications in this list only, published before they year you provide: 

.. code-block:: python
   
    >>> eids=['2-s2.0-84959420483', '2-s2.0-84949113230',
              '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(552083s73700, 2017, eids=eids)

A number of optional parameters will be used throughout the query process in order to define "about" similarity.  There are margins for the first year of publication, the number of co-authors and the number of publications:

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2017, year_margin=2,
                           coauth_margin=0.2, pub_margin=0.2,
                           cits_margin=0.2)

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
    {(21100858668, None), (22900, 'Research Policy'),
    (23013, 'Industry and Innovation'), (18769, 'Applied Economics Letters'),
    (15143, 'Regional Studies')}
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

    >>> stefano = Original(55208373700, 2017, cits_margin=200)
    >>> stefano.define_search_sources()
    >>> stefano.search_sources
    [(14726, 'Technovation'), (15143, 'Regional Studies'),
    (16680, 'Engineering Science and Education Journal'),
    (17047, 'Chronicle of Higher Education'), (18769, 'Applied Economics Letters'),
    # 57 more sources omitted
    (21100889873, 'International Journal of Recent Technology and Engineering'),
    (21100898637, 'Research Policy: X')]

Property `search_sources` is a list of tuples storing source ID and source title.  As before, you can override (or predefine) your own set of search_sources.  This can be a list of tuples as well or a list of source IDs only.  For example, you can set the search sources equal to the source the scientist publishes in: `stefano.search_sources = stefano.sources`.

Using `verbose=True` you receive additional information on this operation:

.. code-block:: python

    >>> stefano.define_search_sources(verbose=True)
    Found 65 sources matching main field 1405 and type(s) journal

The next step is to define a first search group that adhere to conditions 1 to 4 above and do not violate condition 5 (in the sense that we remove authors have too many publications).


.. code-block:: python

    >>> stefano.define_search_group(verbose=True)
    Searching authors for search_group in 65 sources...
    Progress: |██████████████████████████████████████████████████| 100.0% Complete
    Found 376 authors for search_group

You can inspect the search group using `stefano.search_group`, which you can also override, pre-define or edit.

An alternative search process will try to minimize the number of queries.  The downside is that the resulting query cannot be reused for other searches (of other scientists).  Activate this by setting `stacked=True`:

.. code-block:: python

    >>> stefano.define_search_group(verbose=True, stacked=True)
    Searching authors for search_group in 65 sources...
    Searching authors in 30 sources in 2017...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Searching authors in 32 sources in 2010...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Searching authors in 32 sources in 2011...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Searching authors in 32 sources in 2012...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Searching authors in 31 sources in 2013...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Found 629 authors for search_group

The number differs because less information is available.

The final step is to search within this search group for authors that fulfill criteria 5 through 6.  The returned results are a list of `namedtuples <https://docs.python.org/2/library/collections.html#collections.namedtuple>`_ with additional information.  These may help you assess the fit with the researcher.

.. code-block:: python

    >>> matches = stefano.find_matches(verbose=True)
    Searching through characteristics of 629 authors
    Pre-filtering...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Left with 386 authors
    Filtering based on provided conditions...
    Left with 15 authors based on size information 
    already in cache.
     0 to check.

    Left with 15 authors based on all size information.
    Downloading publications and filtering based on coauthors

    Search and filter based on count of citations
    0 to search out of 15.

    Found 2 author(s) matching all criteria----------------------| 3.63% Complete
    Providing additional information...
    Progress: |██████████████████████████████████████████████████| 100.00% Complete
    Researcher 53164702100: 1 abstract(s) and 0 reference list(s) out of 6 documents missing
    Researcher 55317901900: 0 abstract(s) and 0 reference list(s) out of 7 documents missing
    Researcher 55208373700 (focal): 1 abstract(s) and 0 reference list(s) out of 7 documents missing
    >>> for m in matches:
    ....    print(m)
    >>> matches
    Match(ID='53164702100', name='Sapprasert, Koson', first_year=2011,
    num_coauthors=7, num_publications=6, num_citations=190, country='Norway',
    language='eng', reference_sim=0.0212, abstract_sim=0.1695)
    Match(ID='55317901900', name='Siepel, Josh', first_year=2013,
    num_coauthors=8, num_publications=7, num_citations=52, country='United
    Kingdom', language='eng', reference_sim=0.0079, abstract_sim=0.1275)

Additional search options are available to the user. First, the user can restrict the search of potential matches to authors affiliated to given institutions. This is achieved by providing a list of Scopus Affiliation IDs as value of the optional parameter `search_affiliations` in the class `Original`. For instance:

.. code-block:: python

    >>> affiliations = [60002612, 60032111, 60000765]
    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                                          coauth_margin=1, period=3,
                                          search_affiliations=affiliations)

A second option allows to change the window of time within which the similarity between scientist and potential matches is considered. With default settings, `sosia` searches for matches that are similar to the scientist provided, based on indicators constructed over the entire period between the first year of publication of the scientist until the year provided as year of treatment. It is possible to change this behavior in order to focus on a shorter period of time before the year of treatment. This is done by initiating the class :doc:`Original <../reference/sosia.Original>` and setting the option `period` equal to the desired number of years,

.. code-block:: python

    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                                          coauth_margin=1, period=3)

and then proceeding normally with the other steps. `sosia` will return authors starting publishing within 1 year before or after the first year of publication, with maximum 1 publication more or less, 1 citation more or less and 1 coauthor more or less the scientists, between 2017 and 2015 included. More precisely, for citations and coauthors, `sosia` counts: only citations (excluding self-citations) up to 2017 to papers published within the period; the number of unique coauthors in publications within the period. It is left to the user to further restrict the sample of matches based on similarity over the full period (the necessary variables can be obtained as output).

By default, `sosia` provides the following information (which you switch off using `information=False` to simply return a list of Scopus IDs):

* `first_year`: The year of the first recorded publication
* `num_coauthors`: The number of coauthors (Scopus Author profiles) up to the year of treatment
* `num_publications`: The number of indexed publications up to the year of treatment
* `num_citations`: The number of citations up until up to year of treatment
* `num_coauthors_period`: The number of coauthors (Scopus Author profiles) within the `period` desired (if not provided, equal to num_coauthors)
* `num_publications_period`: The number of indexed publications within the `period` desired (if not provided, equal to num_publications)
* `num_citations_period`: The number of citations within the `period` desired  (if not provided, equal to num_citations)
* `country`: The most frequent country of all affiliations listed on publications most recent to the year of treatment
* `subjects`: List of research subjects in which the matched author has published up to the year of treatment
* `affiliation_id`: The most frequent Scopus Affiliation ID of all affiliations listed on publications most recent to the year of treatment
* `affiliation`: The most frequent affiliation of all affiliations listed on publications most recent to the year of treatment
* `language`: The language(s) of the published documents of an author up until the year of treatment
* `reference_sim`: The cosine similarity of references listed in publications up until the year of treatment between the matched scientist and the scientist (references may be missing)
* `abstract_sim`: The cosine similarity of words used in abstracts of publications up until the year of treatment between the matched scientist and the scientist, approriately filtered and stemmed using `nltk <https://www.nltk.org/>`_ and `sklearn <https://scikit-learn.org//>`_ (abstracts my be missing)

Alternatively, you can provide a list of above keywords to only obtain information on these keywords.  This is helpful as some information takes time to gather.

It is easy to work with namedtuples.  For example, using `pandas <https://pandas.pydata.org/>`_ you easily turn the list into a pandas DataFrame:

.. code-block:: python

    >>> import pandas as pd
    >>> pd.set_option('display.max_columns', None)
    >>> df = pd.DataFrame(matches)
    >>> df = df.set_index('ID')
    >>> df
                ID               name  first_year  num_coauthors  \
    0  53164702100  Sapprasert, Koson        2011              7   
    1  55317901900       Siepel, Josh        2013              8   

       num_publications  num_citations         country language  reference_sim  \
    0                 6            190          Norway      eng         0.0212   
    1                 7             52  United Kingdom      eng         0.0079   

       abstract_sim  
    0        0.1695  
    1        0.1275

Finally, for demanding users, there exists an option to attenuate the issue of disambiguation of names in Scopus. Scopus Author IDs are curated and fairly correct, on average. However, in some cases they are incorrect. In most of these cases, more than one Author ID is associated to one same author. In `sosia` it is left to the user to verify whether the Author IDs obtained in the list of matches are precise. At the same time, with default settings, there may be a "hypothetical author" that is in theory a good match, but that is not found because she does not have a unique Author ID. This is the type of error that can be attenuated. First, use the option `period` to base the search on a shorter period. This increases the likelihood of finding one Author ID of the "hypothetical author" which is valid within the period. Second, set the option `ignore_first_id` equal to `True` in the function `define_search_group`.

.. code-block:: python

    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1, pub_margin=1,
                                          coauth_margin=1, period=3)
    >>> scientist_period.define_search_group(ignore_first_id=True)

This allows to ignore whether or not the same Author ID is valid for the full period down to the first year of publication of the target scientist. `sosia` will still filter out Author IDs whose first year of publication is too old, but it will maintain as potential matches Author IDs whose first year of publication is after the year margin provided (this is, the first year of publication of the Author IDs can be later than the upper margin of first year of publication of the target scientist). By now, it is left to the user to complete the profiles of the authors obtained and to reevaluate in a second stage whether they are indeed good matches.