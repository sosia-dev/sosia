--------------------------
Refinig the search process
--------------------------

Incomplete Scopus profiles
--------------------------

Scopus is generally very comprehensive and reliable, and Scopus Author IDs are well-curated and fairly accurate on average. However, some issues remain that you should be aware of, and sosia can help address them. These issues primarily relate to the disambiguation of names. Occasionally, there may be multiple profiles for a single researcher, or a profile may include documents that actually belong to another researcher.

First, you should always verify the correctness of the profile for which you want to find matches. In case multiple profiles belong to the same researcher, you can provide a list of Scopus Author IDs. To address profiles with too many documents, you can specify the list of Scopus EIDs (the Elsevier ID for a document) to use exclusively for determining the characteristics (an ID is still required in this case):

.. code-block:: python
   
    >>> eids = ['2-s2.0-84959420483', '2-s2.0-84949113230',
    >>>         '2-s2.0-84961390052', '2-s2.0-84866317084']
    >>> scientist1_eids = sosia.Original(55208373700, 2017, eids=eids)

Restricting to affiliations
---------------------------

You can also restrict the search of potential matches to authors affiliated to given institutions.  Provide a list of Scopus Affiliation IDs with parameter `affiliations`, and `sosia` will find matches only among authors affiliated to these institutions:

.. code-block:: python

    >>> affiliations = [60002612, 60032111, 60000765]
    >>> scientist_aff = sosia.Original(55208373700, 2017, affiliations=affiliations)

