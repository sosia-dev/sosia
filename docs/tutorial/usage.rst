------------------------
Using sosia step-by-step
------------------------

Characteristics of the scientist
--------------------------------

The primary class to interact with is :ref:`Original() <class_original>`. This class represents the scientist for whom you want to find matches. To initiate it, provide the Scopus Author ID, the year of comparison, as well as the path to the local database:

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2017, db_path=DB_NAME)

Upon initiation, pybliometrics performs queries on the Scopus database in the background.

All properties and the control group are derived from the publications associated with the profile, specifically those published before the comparison year. They represent the state of the profile in this year.

sosia considers only research-type articles as defined by Scopus; these are articles (ar), books (bk), book chapter (ch), conference proceeding (cp), conference review (cr), notes (no), reviews (re), and short articles (sh). With the exception of notes, books and book chapters, these types are the ones Scopus uses for journal metrics. Notably, sosia excludes letters, editorials, errata and retracted papers.

.. code-block:: python

    >>> stefano.affiliation_country
    'Switzerland'
    >>> stefano.coauthors
    [24464562500, 24781156100, 36617057700, 54929867200, 54930777900,
     55875219200, 57217825601]
    >>> stefano.fields
    [2300, 3300, 2002, 1405, 1408, 1803, 1400, 1405]
    >>> stefano.first_year
    2012
    >>> stefano.sources
    [(15143, 'Regional Studies'), (18769, 'Applied Economics Letters'),
     (22900, 'Research Policy'), (23013, 'Industry and Innovation'), (21100858668, None)]
    >>> stefano.main_field
    (1405, 'BUSI')

Additionally, `stefano.publications` is a list of namedtuples storing information about the indexed publications.

You can override each property manually, for instance when you are certain that a Scopus profile contains errors you may want to set another country or main field.

.. code-block:: python

    >>> stefano.affiliation_country = 'Germany'
    >>> stefano.affiliation_country
    'Germany'
    >>> stefano.main_field = (1406, 'ECON')
    >>> stefano.main_field
    (1406, 'ECON')


Similarity parameters
---------------------

`sosia` aims to identify researchers who are similar to the Original in the comparison year. Currently, `sosia` defines similarity based on four criteria: the start of the academic career, the number of co-authors, the number of publications, and the total citation count. Another researcher (i.e., Scopus profile) is considered similar if their characteristics fall within a defined margin around those of the Original. If all characteristics are similar and the other researcher is not a co-author, they are considered a match.

By default (i.e., if not specified), the margin for the first year of publication is set to 2 years, while the margins for the number of co-authors, publications, and citations are set to 20%. These margins apply in both directions. You can override these parameters. sosia interprets integer values as absolute deviations and float values as percentages for relative deviations.

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2017, first_year_margin=2,
    >>>                    coauth_margin=0.2, pub_margin=0.2,
    >>>                    cits_margin=0.2, db_path=DB_NAME)

With this configuration, sosia will identify matches who began publishing within ±2 years of the scientist's first publication. In the comparison year, the matches will have a similar number of co-authors, within a range of ±20% of the original number (with a minimum of 1), and a similar number of publications, also within a range of ±20% (with a minimum of 1).

Defining search sources
-----------------------
The first step in this process is to define a list of sources that are similar in type and area to those the scientist published in up to the comparison year. A source is considered similar if it (i) is associated with the scientist's main field, (ii) matches the type(s) of sources the scientist has used, and (iii) is not linked to fields unrelated to the scientist's expertise. Here, the type of source refers to categories such as journals, conference proceedings, books, etc. You define the list of search sources using a method within the class and access the results via a property.

.. code-block:: python

    >>> stefano.define_search_sources()
    >>> print(stefano.search_sources)
    [(15143, 'Regional Studies'), (16680, 'Engineering Science and Education Journal'),
    (17047, 'Chronicle of Higher Education'), (18769, 'Applied Economics Letters'),
    # 58 more sources omitted
    (21101212779, 'Technological Sustainability')]

Property `search_sources` is a list of tuples storing source ID and source title. As before, you can override (or predefine) your own set of search_sources.  This can be a list of tuples as well or a list of source IDs only.  For example, you can set the search sources equal to the sources the scientist publishes in: `stefano.search_sources = stefano.sources`. Then only authors publishing in these sources will be considered for a match.

Using `verbose=True` you receive additional information on this operation:

.. code-block:: python

    >>> stefano.define_search_sources(verbose=True)
    Found 61 sources matching main field 1405 and source type(s) jr


Defining the search group
-------------------------

`sosia` uses these sources to create an initial search group of authors. This group publishes in the same kind of sources associated to the same main field last year the Original was active in (in this case: 2017) as well as around the year of the first publiscation (in this case: between 2010 and 2014). `sosia` also removes authors that published before (in this case: 2009).

.. code-block:: python

    >>> stefano.define_search_group(verbose=True)
    Defining 'search_group' using up to 65 sources...
	... parsing Scopus information for 2017...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 176.76it/s]
	... parsing Scopus information for 2010...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 168.01it/s]
	... parsing Scopus information for 2011...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 161.92it/s]
	... parsing Scopus information for 2012...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 137.80it/s]
	... parsing Scopus information for 2013...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 133.42it/s]
	... parsing Scopus information for 2014...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 144.00it/s]
	... parsing Scopus information for 2009...
	100%|█████████████████████████████████████████████████████████████████████████████████| 61/61 [00:00<00:00, 161.04it/s]
	Found 783 candidates


You can inspect the search group using `stefano.search_group`, which you can also override or pre-define.

An alternative search process that minimizes the number of queries can be activated by setting stacked=True. The downside of this method is that the resulting queries cannot be reused for other searches involving different scientists.

.. code-block:: python

    >>> stefano.define_search_group(verbose=True, stacked=True)
    Defining 'search_group' using up to 65 sources...
    ... parsing Scopus information for 2017...
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
    ... parsing Scopus information for 2009...
    Progress: |██████████████████████████████████████████████████| 100.00% complete
    Found 783 candidates


Finding matches
---------------

The final step is to search within this search group for authors who are mainly active in the same field, started around the same time, have a similar number of publications, have a similar number of coauthors, and have been cited about equally often.  The matches can be accessed through the .matches property.

.. code-block:: python

    >>> stefano.find_matches(verbose=True)
    Filtering 783 candidates...
    Downloading information for 783 candidates...
    100%|████████████████████████████████████████████████████████████████████████████████████| 9/9 [04:51<00:00, 32.39s/it]
    ... left with 479 candidates in main field (BUSI)
    ... left with 472 candidates with sufficient total publications (5)
    Querying Scopus for information for 472 authors...
    100%|████████████████████████████████████████████████████████████████████████████████| 472/472 [00:08<00:00, 55.19it/s]
    ... left with 79 candidates with similar year of first publication (2010 to 2014)
    ... left with 27 candidates with similar number of publications (5 to 9)
    ... left with 15 candidates with similar number of coauthors (5 to 9)
    Counting citations of 15 candidates...
    100%|██████████████████████████████████████████████████████████████████████████████████| 15/15 [00:16<00:00,  1.12s/it]
    ... left with 3 candidates with similar number of citations (24 to 38)
    Found 3 matches
    >>> print(stefano.matches)
    [55022752500, 55810688700, 55824607400]


Adding information to matches
-----------------------------

You may need additional information to both assess match quality and select matches. The .inform_matches() method adds specified details to each match. After this, the stefano.matches attribute becomes a list of `namedtuples <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_:

.. code-block:: python

    >>> stefano.inform_matches(verbose=True)
    Providing information for 3 matches...
    100%|████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:09<00:00,  2.33s/it]
    Match 55022752500: No reference list of 5 documents missing
    Match 55810688700: No reference list of 6 documents missing
    Match 55824607400: No reference list of 7 documents missing
    Original 55208373700: 1 reference list out of 7 documents missing

By default, `sosia` provides the following information:

* `first_year`: The year of the first recorded publication
* `num_coauthors`: The number of coauthors (Scopus Author profiles) up to the comparison year
* `num_publications`: The number of indexed publications up to the comparison year
* `num_citations`: The number of citations up to the comparison year
* `subjects`: List of research subjects in which the matched author has published up to the comparison year
* `affiliation_country`: The current country of the affiliation belonging to "affiliation_id"
* `affiliation_id`: The most frequent Scopus Affiliation ID of all affiliations listed on publications most recent to the comparison year
* `affiliation_name`: The current name of the affiliation belonging to "affiliation_id"
* `affiliation_type`: The current type of the affiliation belonging to "affiliation_id"
* `language`: The language(s) of the published documents of an author up until the comparison year
* `num_cited_refs`: The number of jointly cited references as per publications up until the comparison year (reference lists may be missing on Scopus, which is what the text in the output is telling you)

Alternatively, you can provide a list of the desired keywords to obtain information only on those specific keywords. This approach is useful because certain information takes longer to gather.

.. code-block:: python

    >>> print(stefano.matches[0])
    Match(ID=55022752500, name='Van der Borgh, Michel', first_name='Michel',
          surname='Van der Borgh', first_year=2012, num_coauthors=6, num_publications=5,
          num_citations=36, subjects=['BUSI', 'SOCI', 'COMP'], affiliation_country='Netherlands',
          affiliation_id='60032882', affiliation_name='Technische Universiteit Eindhoven',
          affiliation_type='univ', language='eng', num_cited_refs=0)

It is easy to work with namedtuples.  For example, using `pandas <https://pandas.pydata.org/>`_ you easily turn the list into a pandas DataFrame:

.. code-block:: python

    >>> import pandas as pd
    >>> pd.set_option('display.max_columns', None)  # this is just for full display
    >>> df = pd.DataFrame(stefano.matches)
    >>> df = df.set_index('ID')
    >>> print(df)
                                  name  first_name        surname  first_year  \
    ID                                                                          
    55022752500  Van der Borgh, Michel      Michel  Van der Borgh        2012   
    55810688700     Zapkau, Florian B.  Florian B.         Zapkau        2014   
    55824607400   Pellegrino, Gabriele    Gabriele     Pellegrino        2011   

                 num_coauthors  num_publications  num_citations  \
    ID                                                            
    55022752500              6                 5             36   
    55810688700              8                 6             33   
    55824607400              5                 7             34   

                           subjects affiliation_country affiliation_id  \
    ID                                                                   
    55022752500  [BUSI, ECON, COMP]         Netherlands       60032882   
    55810688700  [BUSI, ECON, MEDI]             Germany       60025310   
    55824607400  [BUSI, ECON, DECI]         Switzerland       60028186   

                                         affiliation_name affiliation_type  \
    ID                                                                       
    55022752500         Technische Universiteit Eindhoven             univ   
    55810688700     Heinrich-Heine-Universität Düsseldorf             univ   
    55824607400  Ecole Polytechnique Fédérale de Lausanne             univ   

                language  num_cited_refs  
    ID                                    
    55022752500      eng               0  
    55810688700      eng               0  
    55824607400      eng               5  

