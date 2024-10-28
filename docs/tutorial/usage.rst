------------------------
Using sosia step-by-step
------------------------

Characteristics of the scientist
--------------------------------

The primary class to interact with is :ref:`Original() <class_original>`. This class represents the scientist for whom you want to find matches. To initiate it, provide the Scopus Author ID, the year of comparison, as well as the path to the local database:

.. code-block:: python
   
    >>> from sosia import Original
    >>> stefano = Original(55208373700, 2018, db_path=DB_NAME)

Upon initiation, pybliometrics performs queries on the Scopus database in the background.

All properties and the control group are derived from the publications associated with the profile, specifically those published before the comparison year. They represent the state of the profile in this year.

sosia considers only research-type articles as defined by Scopus; these are articles (ar), books (bk), book chapter (ch), conference proceeding (cp), conference review (cr), notes (no), reviews (re), and short articles (sh). With the exception of notes, books and book chapters, these types are the ones Scopus uses for journal metrics. Notably, sosia excludes letters, editorials, errata and retracted papers.

.. code-block:: python

    >>> stefano.affiliation_country
    'Switzerland'
    >>> stefano.coauthors
    [24464562500, 24781156100, 36617057700, 54929867200, 54930777900,
     55875219200, 57131011400, 57217825601]
    >>> stefano.fields
    [2300, 3300, 2002, 1405, 1408, 1803, 1400, 1405, 1404, 1405, 1410]
    >>> stefano.first_year
    2012
    >>> stefano.sources
    [(15143, 'Regional Studies'), (18769, 'Applied Economics Letters'), (22900, 'Research Policy'),
     (23013, 'Industry and Innovation'), (21100858668, None),
     (21100880192, '78th Annual Meeting of the Academy of Management, AOM 2018')]
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

`sosia` aims to identify researchers who are similar to the Original in the comparison year. `sosia` can define similarity based on six criteria: the same main field (ASJC2), the start of the academic career, the number of co-authors, the number of publications, the total citation count, being affiliated to a specific (set of) affiliations. Another researcher (i.e., Scopus profile) is considered similar if their characteristics fall within a defined margin around those of the Original. However, keep in mind that `sosia` discards coauthors of the Original.

By default none of the six criteria is active; i.e., you can switch them on and off like they were modules. We recommend to use the first five criteria with rather low values (e.g., , the margin for the first year of publication equal to 1 year, and the margins for the number of co-authors, publications, and citations equal to something between 10% and 20%). Margins apply in both directions. `sosia` interprets integer values as absolute deviations and float values as percentages for relative deviations. To match on the characteristic precisely, use the value 0.

.. code-block:: python
   
    >>> stefano = Original(55208373700, 2018, db_path=DB_NAME,
    >>>                    same_field=True, first_year_margin=1,
    >>>                    coauth_margin=0.2, pub_margin=0.2,
    >>>                    cits_margin=0.15)

With this configuration, sosia will identify matches who began publishing within ±1 years of the scientist's first publication. In the comparison year, the matches will have a similar number of co-authors, within a range of ±20% of the original number (with a minimum of 1), and a similar number of publications, also within a range of ±15% (with a minimum of 1).

Defining search sources
-----------------------
The first step in this process is to define a list of sources that are similar in type and area to those the scientist published in up to the comparison year. A source is considered similar if it (i) is associated with the scientist's main field and (ii) matches the type(s) of sources the scientist has used. Here, the type of source refers to categories such as journals, conference proceedings, books, etc. Using parameter "mode", users can (iii) choose between a wide and a narrow defintion of sources. In the narrow defintion, the default, a source may not be linked to fields that are alien to the Original; in the wide defintion, those sources are included.

.. code-block:: python

    >>> stefano.define_search_sources()
    >>> print(stefano.search_sources)
    [(15143, 'Regional Studies'), (16680, 'Engineering Science and Education Journal'),
     (17047, 'Chronicle of Higher Education'), (18769, 'Applied Economics Letters'),
    # 200 more sources omitted
     (21101212779, 'Technological Sustainability')]

Property `search_sources` is a list of tuples storing source ID and source title. You can override (or predefine) your own set of `search_sources`.  This can be a list of tuples as well or a list of source IDs only.  For example, you can set the search sources equal to the sources the scientist publishes in: `stefano.search_sources = stefano.sources`. Then only authors publishing in these sources will be considered for a match.

Using `verbose=True` you receive additional information on this operation:

.. code-block:: python

    >>> stefano.define_search_sources(verbose=True, mode="narrow")
    Found 206 sources of types jr, cp matching main field 1405 narrowly


Defining the search group
-------------------------

`sosia` uses these sources to create an initial search group of authors. `sosia` takes all the years between the Original's first year and the comparison year (including these two) and splits them into chunks. The number of years of each chunk is determined by the user, and it must not be smaller than the first year margin. The first chunk may be larger as the left margin of the first year is included. The last chunk will be merged into the next-to-last margin if it is smaller than half the target size. Suitable candidates then have to publish in all these chunks. Technically, the search group is hence the intersection of authors publishing in these chunks. In the example, `sosia` will look at all publications in the search sources between 2011 (the first year 2012 minus the first_year_margin) and 2017 (the year before the comparison year). With a chunk_size equal to 2, the following chunks emerge: {2011, 2012, 2013}, {2014, 2015}, {2016, 2017}.

.. code-block:: python

    >>> stefano.define_search_group(verbose=True, chunk_size=2)
    Defining 'search_group' using up to 206 sources...
    ... parsing Scopus information for 2010...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [03:27<00:00,  1.01s/it]
    ... parsing Scopus information for 2011...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [05:10<00:00,  1.51s/it]
    ... parsing Scopus information for 2012...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [04:38<00:00,  1.35s/it]
    ... parsing Scopus information for 2013...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [04:23<00:00,  1.28s/it]
    ... parsing Scopus information for 2014...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [04:01<00:00,  1.17s/it]
    ... parsing Scopus information for 2015...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [03:26<00:00,  1.00s/it]
    ... parsing Scopus information for 2016...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [03:57<00:00,  1.15s/it]
    ... parsing Scopus information for 2017...
    100%|████████████████████████████████████████████████████████████████████████████████| 206/206 [03:32<00:00,  1.03s/it]
    Found 772 candidates


You can inspect the search group using `stefano.search_group`, which you can also override or pre-define.

An alternative search process that minimizes the number of queries can be activated by setting stacked=True. The downside of this method is that the resulting queries cannot be reused for anything else (for instance, you may maintain a separate Scopus database fuelled by `pybliometrics`). Use `stacked=True` to invoke this option.


Finding matches
---------------

The final step is to filter the candidates from the search group. Depending on the search paratmers, `sosia` searches for authors who are mainly active in the same field, started around the same time, have a similar number of publications, have a similar number of coauthors, and have been cited about equally often.

.. code-block:: python

    >>> stefano.find_matches(verbose=True)
    Filtering 772 candidates...
    Downloading information for 772 candidates...
    100%|████████████████████████████████████████████████████████████████████████████████████| 8/8 [02:07<00:00,  9.58s/it]
    ... left with 560 candidates in main field (BUSI)
    ... left with 557 candidates with sufficient total publications (6)
    Querying Scopus for information for 557 authors...
    100%|████████████████████████████████████████████████████████████████████████████████| 557/557 [35:46<00:00,  3.85s/it]
    ... left with 57 candidates with similar year of first publication (2011 to 2013)
    ... left with 22 candidates with similar number of publications (6 to 10)
    ... left with 8 candidates with similar number of coauthors (6 to 10)
    ... left with 2 candidates with similar number of citations (42 to 58)
    Found 2 matches
    
The matches are a list available through the .matches property.

.. code-block:: python

    >>> print(stefano.matches)
    [37080157400, 55567912500]


Adding information to matches
-----------------------------

You may need additional information to both assess match quality and select matches. The .inform_matches() method adds specified details to each match. After this, the stefano.matches attribute becomes a list of `namedtuples <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_:

.. code-block:: python

    >>> stefano.inform_matches(verbose=True)
    Providing information for 2 matches...
    100%|████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:20<00:00, 10.21s/it]
    Match 37080157400: 2 reference list out of 6 documents missing
    Match 55567912500: No reference list of 8 documents missing
    Original 55208373700: 1 reference list out of 8 documents missing

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

Alternatively, you can provide a list of the desired keywords to obtain information only on those specific keywords. This approach is useful because certain information takes longer to gather (for instance, language and num_cited_refs).

.. code-block:: python

    >>> print(stefano.matches[0])
    Match(ID=37080157400, name='Buchanan, Sean', first_name='Sean', surname='Buchanan',
          first_year=2011, num_coauthors=5, num_publications=6, num_citations=45,
          subjects=['BUSI', 'ECON', 'SOCI'], affiliation_country='Canada',
          affiliation_id='60009697', affiliation_name='University of Manitoba',
          affiliation_type='univ', language='eng', num_cited_refs=1)

It is easy to work with namedtuples.  For example, using `pandas <https://pandas.pydata.org/>`_ you easily turn the list into a pandas DataFrame:

.. code-block:: python

    >>> import pandas as pd
    >>> pd.set_option('display.max_columns', None)  # this is just for full display
    >>> df = pd.DataFrame(stefano.matches)
    >>> df = df.set_index('ID')
    >>> print(df)
                           name first_name   surname  first_year  num_coauthors  \
    ID
    37080157400  Buchanan, Sean       Sean  Buchanan        2011              5
    55567912500   Eling, Katrin     Katrin     Eling        2013              9

                 num_publications  num_citations            subjects  \
    ID
    37080157400                 6             45  [BUSI, ECON, SOCI]
    55567912500                 8             56  [BUSI, COMP, ENGI]

                affiliation_country affiliation_id  \
    ID
    37080157400              Canada       60009697
    55567912500         Netherlands       60032882

                                  affiliation_name affiliation_type language  \
    ID
    37080157400             University of Manitoba             univ      eng
    55567912500  Technische Universiteit Eindhoven             univ      eng

                 num_cited_refs
    ID
    37080157400               1
    55567912500               0
