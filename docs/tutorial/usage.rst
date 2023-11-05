------------------------
Using sosia step-by-step
------------------------

Characteristics of the scientist
--------------------------------

The only class to interact with is :doc:`Original() <../reference/sosia.Original>`.  It represents the scientist for whom you'd like to find matches.  You initiate it with the Scopus Author ID and the year of treatment.

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2017, sql_fname=DB_NAME)

All properties and the control group are based on the publications associated with the profile and published before the treatment year.

Upon initiation, `pybliometrics` performs queries on the Scopus database under the hood.  The information is valid in the year of treatment and used to find similarities:

.. code-block:: python

    >>> stefano.affiliation_country
    'Switzerland'
    >>> stefano.coauthors
    {57217825601, 54930777900, 36617057700, 54929867200, 55875219200,
     24464562500, 24781156100}
    >>> stefano.fields
    [2300, 3300, 2002, 1405, 1400, 1405, 1408, 1803, 2200, 2002, 1405, 1400,
     3300, 2300, 1405, 1803, 1408]
    >>> stefano.first_year
    2012
    >>> stefano.sources
    [(15143, 'Regional Studies'), (18769, 'Applied Economics Letters'),
     (22900, 'Research Policy'), (23013, 'Industry and Innovation'), (21100858668, None)]
    >>> stefano.main_field
    (1405, 'BUSI')

Additionally, `stefano.publications` is a list of namedtuples storing information about the indexed publications.  Each property can be manually overriden:

.. code-block:: python

    >>> stefano.affiliation_country = 'Germany'
    >>> stefano.affiliation_country
    'Germany'
    >>> stefano.main_field = (1406, 'ECON')
    >>> stefano.main_field
    (1406, 'ECON')


Similarity parameters
---------------------

`sosia` tries to find researchers that are similar to the Original in the year of treatment.  Currently, `sosia` defines similar along four margins: the start of the academic career, the number of co-authors and publications, and the total citation count.  Another researcher (read: Scopus profile) is similar if her characteristics fall within the margin around the Original's characteristics.  If all characteristics are similar, and the other researcher is not a co-author, she is deemed a match.

By default (i.e., if not specified), the margins for the first year of publication is 2, for the number of co-authors, the number of publications, and for the number of citations it is 20%.  Margins apply in either direction.  You can override these parameters.  `sosia` interprets integer values as absolute deviation, and float values as a percentage for relative deviation:

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2017, first_year_margin=2,
                           coauth_margin=0.2, pub_margin=0.2,
                           cits_margin=0.2, sql_fname=DB_NAME)

This configuration will find matches who started publishing the year of the scientist's first publication plus or minus 2 years, who in the year of treatment have the same number of coauthors plus or minus 20% of that number (with a minimum of 1), and who in the year of treatment have the same number of publications plus or minus 20% of that number (with a minimum of 1).


Defining search sources
-----------------------
The first step is to define a list of sources similar (in type and area) to the sources the scientist published until the year of treatment. `sosia` uses these sources to define an initial search group. A source is similar if (i) it is associated with the scientist's main field, (ii) is of the same type(s) as the scientist's sources, and (iii) is not associated with fields alien to the scientist. Here the type of source refers to journal, conference proceeding, book, etc. You define the list of search sources with a method to the class and access the results using a property:

.. code-block:: python

    >>> stefano.define_search_sources()
    >>> stefano.search_sources
    [(15143, 'Regional Studies'), (16680, 'Engineering Science and Education
     Journal'), (17047, 'Chronicle of Higher Education')
    # 56 more sources omitted
    (21100898637, 'Research Policy: X')]

Property `search_sources` is a list of tuples storing source ID and source title.

As before, you can override (or predefine) your own set of search_sources.  This can be a list of tuples as well or a list of source IDs only.  For example, you can set the search sources equal to the source the scientist publishes in: `stefano.search_sources = stefano.sources`.

Using `verbose=True` you receive additional information on this operation:

.. code-block:: python

    >>> stefano.define_search_sources(verbose=True)
    Found 61 sources matching main field 1405 and source type(s) jr


Defining the search group
-------------------------

The next step is to define a first search group that adhere to conditions 1 to 4 above and do not violate condition 5 (in the sense that we remove authors with too many publications).

.. code-block:: python

    >>> stefano.define_search_group(verbose=True)
    Defining 'search_group' using up to 61 sources...
    .. parsing Scopus information for 2017...
    100%|█████████████████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 232.94it/s]
    ... parsing Scopus information for 2010...
    100%|█████████████████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 253.99it/s]
    ... parsing Scopus information for 2011...
    100%|█████████████████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 270.35it/s]
    ... parsing Scopus information for 2012...
    100%|█████████████████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 253.48it/s]
    ... parsing Scopus information for 2013...
    100%|█████████████████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 200.54it/s]
    Found 863 authors for search_group


You can inspect the search group using `stefano.search_group`, which you can also override, pre-define or edit.

An alternative search process, which tries to minimize the number of queries, can be activated with `stacked=True`. The downside of this method is that the resulting query, which pybliometrics caches under the hood, cannot be reused for other searches (of other scientists).

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
    Found 787 authors for search_group


Finding matches
---------------

The final step is to search within this search group for authors that fulfill criteria 5 through 6.  Matches are accessible through property `.matches`:

.. code-block:: python

    >>> stefano.find_matches(verbose=True)
    Searching through characteristics of 787 authors...
    Pre-filtering...
    100%|████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [03:17<00:00, 49.41s/it]
    Left with 473 authors with sufficient number of publications and same main field
    Obtaining information for 447 authors without sufficient information in database...
    Left with 59 authors based on publication information before 2009
    Counting publications of 59 authors before 2018...
    Left with 34 researchers
    Counting citations of 22 authors...
    Filtering based on count of citations...
    Left with 7 authors
    Filtering based on coauthor count...
    100%|████████████████████████████████████████████████████████████████████████████████████████████████| 6/6 [00:05<00:00,  1.00it/s]
    Left with 4 authors
    Found 4 author(s) matching all criteria
    >>> print(stefano.matches)
    [55022752500, 55567912500, 55810688700, 55824607400]


Adding information to matches
-----------------------------

You might need additional information to both assess match quality and select matches.  Method `.inform_matches()` adds certain specified information to each match.  Attribute `stefano.matches` then becomes a list of `namedtuples <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_:

.. code-block:: python

    >>> stefano.inform_matches(verbose=True)
    Providing information for 4 matches...
    Match 55022752500: 0 reference list(s) out of 5 documents missing
    Match 55567912500: 0 reference list(s) out of 6 documents missing
    Match 55810688700: 0 reference list(s) out of 6 documents missing
    Match 55824607400: 0 reference list(s) out of 7 documents missing
    Original 55208373700: 1 reference list(s) out of 7 documents missing
    >>> print(stefano.matches[0])
    Match(ID=55022752500, name='Van der Borgh, Michel', first_name='Michel',
          surname='Van der Borgh', first_year=2012, num_coauthors=6,
          num_publications=5, num_citations=36, num_coauthors_period=None,
          num_publications_period=None, num_citations_period=None,
          subjects=['BUSI', 'ECON', 'COMP'], affiliation_country='Netherlands',
          affiliation_id='60032882', affiliation_name='Technische Universiteit
          Eindhoven', affiliation_type='univ', language='eng', num_cited_refs=0)

By default, `sosia` provides the following information:

* `first_year`: The year of the first recorded publication
* `num_coauthors`: The number of coauthors (Scopus Author profiles) up to the year of treatment
* `num_publications`: The number of indexed publications up to the year of treatment
* `num_citations`: The number of citations up to the year of treatment
* `num_coauthors_period`: The number of coauthors (Scopus Author profiles) within the desired `period` (if not provided, equal to num_coauthors)
* `num_publications_period`: The number of indexed publications within the desired `period` (if not provided, equal to num_publications)
* `num_citations_period`: The number of citations within the `period` desired  (if not provided, equal to num_citations)
* `subjects`: List of research subjects in which the matched author has published up to the year of treatment
* `affiliation_country`: The current country of the affiliation belonging to "affiliation_id"
* `affiliation_id`: The most frequent Scopus Affiliation ID of all affiliations listed on publications most recent to the year of treatment
* `affiliation_name`: The current name of the affiliation belonging to "affiliation_id"
* `affiliation_type`: The current type of the affiliation belonging to "affiliation_id"
* `language`: The language(s) of the published documents of an author up until the year of treatment
* `num_cited_refs`: The number of jointly cited references as per publications up until the year of treatment (reference lists may be missing)

Alternatively, you can provide a list of above keywords to only obtain information on these keywords.  This is helpful as some information takes time to gather.

It is easy to work with namedtuples.  For example, using `pandas <https://pandas.pydata.org/>`_ you easily turn the list into a pandas DataFrame:

.. code-block:: python

    >>> import pandas as pd
    >>> pd.set_option('display.max_columns', None)  # this is just for full display
    >>> df = pd.DataFrame(stefano.matches)
    >>> df = df.set_index('ID')
    >>> df
                                  name  first_name        surname  first_year  \
    ID                                                                          
    55022752500  Van der Borgh, Michel      Michel  Van der Borgh        2012   
    55567912500          Eling, Katrin      Katrin          Eling        2013   
    55810688700     Zapkau, Florian B.  Florian B.         Zapkau        2014   
    55824607400   Pellegrino, Gabriele    Gabriele     Pellegrino        2011   

                 num_coauthors  num_publications  num_citations  \
    ID                                                            
    55022752500              6                 5             36   
    55567912500              5                 6             37   
    55810688700              8                 6             33   
    55824607400              5                 7             34   

                num_coauthors_period num_publications_period num_citations_period  \
    ID                                                                              
    55022752500                 None                    None                 None   
    55567912500                 None                    None                 None   
    55810688700                 None                    None                 None   
    55824607400                 None                    None                 None   

                           subjects affiliation_country affiliation_id  \
    ID                                                                   
    55022752500  [BUSI, ECON, COMP]         Netherlands       60032882   
    55567912500  [BUSI, COMP, ENGI]         Netherlands       60032882   
    55810688700  [BUSI, ECON, MEDI]             Germany       60025310   
    55824607400  [BUSI, ECON, DECI]         Switzerland       60028186   

                                         affiliation_name affiliation_type  \
    ID                                                                       
    55022752500         Technische Universiteit Eindhoven             univ   
    55567912500         Technische Universiteit Eindhoven             univ   
    55810688700     Heinrich-Heine-Universität Düsseldorf             univ   
    55824607400  Ecole Polytechnique Fédérale de Lausanne             univ   

                language  num_cited_refs  
    ID                                    
    55022752500      eng               0  
    55567912500      eng               0  
    55810688700      eng               0  
    55824607400      eng               5  

