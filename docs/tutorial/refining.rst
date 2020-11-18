--------------------------
Refinig the search process
--------------------------

Incomplete Scopus profiles
--------------------------

Scopus is very comprehensive and reliable in general, and Scopus Author IDs are curated and fairly correct, on average.  But few problems remain that you should be aware of and that `sosia` can deal with.  This relates mostly to the issue of disambiguation of names.  Sometimes there are multiple profiles for one researcher, or one profile contains documentats that in reality belong to another researcher.

First of, you should always check the uniqueness of a profile for which you want to find matches.    To correct for incomplete or multiple profiles, you can provide a list of Scopus Author IDs in case there are multiple Scopus profiles for a researcher.  To deal with profiles with too many documents, you can specify a list of Scopus EIDs (the Elsevier ID for a document) to use exclusively in order to determine the characteristics (in this case, an ID is still required):

.. code-block:: python
   
    >>> eids = ['2-s2.0-84959420483', '2-s2.0-84949113230',
                '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(55208373700, 2017, eids=eids)


Finally, to deal with problematic profiles of potential matches `sosia` provides one possibility.  Consider a "hypothetical author" that is in theory a good match, but that is not found because she does not have a unique Author ID.  This is the type of error that can be attenuated.  First, use the option `period` to base the search additionally on a shorter period.  A value of say 3 will match characteristics 3 years before the treatment year as well (same margins apply).  This increases the likelihood of finding one Author ID of the "hypothetical author" which is valid within the period.  Second, set the option `first_year_search` equal to `"name"`.

.. code-block:: python

    >>> scientist_name = sosia.Original(55208373700, 2017, cits_margin=1,
            pub_margin=1, coauth_margin=1, period=3, first_year_search="name")
    >>> scientist_name.define_search_group()

This allows to ignore whether or not the same Author ID is valid for the full period down to the first year of publication of the target scientist.  `sosia` will still filter out Author IDs whose first year of publication is too large, but it will keep Author IDs whose first year of publication is past the year margin provided.  That is, the first year of publication of the Author IDs can be later than the upper margin of first year of publication of the target scientist).  By now, it is left to the user to complete the profiles of the authors obtained and to reevaluate in a second stage whether they are indeed good matches.


Altering the search process
---------------------------

Additional search options are available to the user.  First, the user can restrict the search of potential matches to authors affiliated to given institutions.  Provide a list of Scopus Affiliation IDs with parameter `affiliations`:

.. code-block:: python

    >>> affiliations = [60002612, 60032111, 60000765]
    >>> scientist_aff = sosia.Original(55208373700, 2017, affiliations=affiliations)

