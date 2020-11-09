------------------------
Using sosia step-by-step
------------------------


Characteristics of the scientist
--------------------------------

The main class is :doc:`Original <../reference/sosia.Original>`.  You initiate it with the Scopus Author ID, or a list of Scopus Author IDs, of the researcher you are looking for, and the year of treatment:

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2017)

You can provide a list of Scopus Author IDs, in the case the author you are interested in has more than one. All properties and the control group will be based on the publications associated to all Scopus Author IDs and published before the year you provide. You can also set as an optional parameter a list of Scopus EIDs corresponding to a list of publications. If you do so, all properties of the scientists and the control group will be based on the publications in this list only, published before they year you provide: 

.. code-block:: python
   
    >>> eids = ['2-s2.0-84959420483', '2-s2.0-84949113230',
                '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(55208373700, 2017, eids=eids)

A number of optional parameters will be used throughout the query process in order to define "about" similarity.  There are margins for the first year of publication, the number of co-authors and the number of publications:

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2017, first_year_margin=2,
                           coauth_margin=0.2, pub_margin=0.2,
                           cits_margin=0.2)

This will find matches who started publishing the year of the scientist's first publication plus or minus 2 years, who in the year of treatment have the same number of coauthors plus or minus 20% of that number (at least 1), and who in the year of treatment have the same number of publications plus or minus 20% of that number (at least 1).  If the last two parameters receive integers rather than floats, they will be interpreted as absolute margin.

Upon initation, `pybliometrics` performs queries on the Scopus database under the hood.  The information is valid in the year of treatment and used to find similarities:

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


Defining search sources
-----------------------
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
    Found 65 sources matching main field 1405 and source type(s) journal


Defining the search group
-------------------------

The next step is to define a first search group that adhere to conditions 1 to 4 above and do not violate condition 5 (in the sense that we remove authors with too many publications).

.. code-block:: python

    >>> stefano.define_search_group(verbose=True)
    Defining 'search_group' using up to 65 sources...
    ... parsing Scopus information for 2017...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2009...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2010...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2011...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2012...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2013...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2014...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Found 846 authors for search_group


You can inspect the search group using `stefano.search_group`, which you can also override, pre-define or edit.

An alternative search process will try to minimize the number of queries.  The downside is that the resulting query cannot be reused for other searches (of other scientists).  Activate this by setting `stacked=True`:

.. code-block:: python

    >>> stefano.define_search_group(verbose=True, stacked=True)
    Defining 'search_group' using up to 65 sources...
    ... parsing Scopus information for 2017...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2009...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2010...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2011...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2012...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2013...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    ... parsing Scopus information for 2014...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Found 846 authors for search_group


Finding matches
---------------

The final step is to search within this search group for authors that fulfill criteria 5 through 6.  Matches are accessible through property `.matches`:

.. code-block:: python

    >>> stefano.find_matches(verbose=True)
    Searching through characteristics of 846 authors...
    Pre-filtering...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Left with 503 authors with sufficient number of publications and same main field
    Obtaining information for 503 authors without sufficient information in database...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Left with 97 authors based on publication information before 2009
    Counting publications of 97 authors before 2018...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Left with 35 researchers
    Counting citations of 35 authors...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Filtering based on count of citations...
    Left with 5 authors
    Filtering based on coauthor count...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Found 3 author(s) matching all criteria
    Find matches...
    Searching through characteristics of 846 authors...
    Left with 503 authors with sufficient number of publications and same main field
    Left with 35 researchers
    Filtering based on count of citations...
    Left with 5 authors
    Filtering based on coauthor count...
    Found 3 author(s) matching all criteria
    >>> print(stefano.matches)
    ['55022752500', '55810688700', '55824607400']


Adding information to matches
-----------------------------

The researcher might need additional information to both assess match quality and select matches.  Using `.inform_matches()` one can source certain specified information.  It returns list of `namedtuples <https://docs.python.org/2/library/collections.html#collections.namedtuple>`_:

.. code-block:: python

    >>> stefano.inform_matches(verbose=True)
    Providing additional information...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Match 55071051800: 2 abstract(s) and 0 reference list(s) out of 8 documents missing
    Match 55317901900: 0 abstract(s) and 0 reference list(s) out of 7 documents missing
    Match 55804519400: 0 abstract(s) and 0 reference list(s) out of 8 documents missing
    Original 55208373700: 0 abstract(s) and 1 reference list(s) out of 7 documents missing
    >>> print(stefano.matches[0])
    Match(ID='55022752500', name='Van der Borgh, Michel', first_name='Michel',
    surname='Van der Borgh', first_year=2012, num_coauthors=6, num_publications=5,
    num_citations=33, num_coauthors_period=6, num_publications_period=5, num_citations_period=33,
    subjects=['BUSI', 'COMP', 'SOCI'], country='Netherlands', affiliation_id='60032882',
    affiliation='Eindhoven University of Technology, Department of Industrial Engineering &
    Innovation Sciences', language='eng', reference_sim=0.0, abstract_sim=0.1217)


By default, `sosia` provides the following information:

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
    >>> df = pd.DataFrame(stefano.matches)
    >>> df = df.set_index('ID')
    >>> df
                                  name  first_name        surname  first_year  \
    ID                                                                          
    55022752500  Van der Borgh, Michel      Michel  Van der Borgh        2012   
    55810688700     Zapkau, Florian B.  Florian B.         Zapkau        2014   
    55824607400   Pellegrino, Gabriele    Gabriele     Pellegrino        2011   

                 num_coauthors  num_publications  num_citations  \
    ID                                                            
    55022752500              6                 5             33   
    55810688700              8                 6             32   
    55824607400              5                 7             34   

                 num_coauthors_period  num_publications_period  \
    ID                                                           
    55022752500                     6                        5   
    55810688700                     8                        6   
    55824607400                     5                        7   

                 num_citations_period            subjects             country  \
    ID                                                                          
    55022752500                    33  [BUSI, COMP, SOCI]         Netherlands   
    55810688700                    32        [BUSI, ECON]             Germany   
    55824607400                    34  [BUSI, ECON, DECI]  Spain; Switzerland   

                               affiliation_id  \
    ID                                          
    55022752500                      60032882   
    55810688700                      60025310   
    55824607400  60001576; 60028186; 60121786   

                                                       affiliation language  \
    ID                                                                        
    55022752500  Eindhoven University of Technology, Department...      eng   
    55810688700                           University of Düsseldorf      eng   
    55824607400  Barcelona Institute of Economics, University o...      eng   

                 reference_sim  abstract_sim  
    ID                                        
    55022752500         0.0000        0.1217  
    55810688700         0.0000        0.1179  
    55824607400         0.0084        0.1074  

