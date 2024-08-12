--------------------------
Refinig the search process
--------------------------

Incomplete Scopus profiles
--------------------------

Scopus is generally very comprehensive and reliable, and Scopus Author IDs are well-curated and fairly accurate on average. However, some issues remain that you should be aware of, and sosia can help address them. These issues primarily relate to the disambiguation of names. Occasionally, there may be multiple profiles for a single researcher, or a profile may include documents that actually belong to another researcher.

First, you should always verify the correctness of the profile for which you want to find matches. In case multiple profiles belong to the same researcher, you can provide a list of Scopus Author IDs. To address profiles with too many documents, you can specify the list of Scopus EIDs (the Elsevier ID for a document) to use exclusively for determining the characteristics (an ID is still required in this case):

.. code-block:: python
   
    >>> eids = ['2-s2.0-84959420483', '2-s2.0-84949113230',
                '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(55208373700, 2017, eids=eids)


While above options deal with problematic focal scientists, the same issues may apply to potential matches. That is, there might be good matches in reality but they are not found because the profiles are incomplete. `sosia` offers two ways to deal with this. First, use the parameter "period" to base the search on a shorter period. For example, setting the value to 3 will match characteristics from up to 3 years before the comparison year (with the same margins applied). This increases the likelihood of finding a valid Author ID for the "hypothetical author" within that period. Second, set the "first_year_search" parameter equal to "name".

.. code-block:: python

    >>> scientist_name = sosia.Original(55208373700, 2017, cits_margin=1,
            pub_margin=1, coauth_margin=1, period=3, first_year_search="name")
    >>> scientist_name.define_search_group()

This approach allows you to disregard whether the same Author ID remains valid throughout the entire period, down to the target scientist's first year of publication. `sosia` will still filter out Author IDs with a first year of publication that is significantly later, but it will retain those whose first year of publication falls within the provided year margin. In other words, the first year of publication for these Author IDs may be later than the target scientist's upper margin for the first publication year. It is then up to the user to complete the profiles of the identified authors and to reevaluate in a second stage whether they are indeed good matches.

Restricting to affiliations
---------------------------

Additional search options are available to the user.  First, the user can restrict the search of potential matches to authors affiliated to given institutions.  Provide a list of Scopus Affiliation IDs with parameter `affiliations`:

.. code-block:: python

    >>> affiliations = [60002612, 60032111, 60000765]
    >>> scientist_aff = sosia.Original(55208373700, 2017, affiliations=affiliations)

