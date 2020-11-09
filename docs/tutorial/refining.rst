--------------------------
Refinig the search process
--------------------------

Additional search options are available to the user. First, the user can restrict the search of potential matches to authors affiliated to given institutions. This is achieved by providing a list of Scopus Affiliation IDs as value of the optional parameter `affiliations` in the class `Original()`. For instance:

.. code-block:: python

    >>> affiliations = [60002612, 60032111, 60000765]
    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1,
            pub_margin=1, coauth_margin=1, period=3, affiliations=affiliations)


A second option allows to change the window of time within which the similarity between scientist and potential matches is considered. With default settings, `sosia` searches for matches that are similar to the scientist provided, based on indicators constructed over the entire period between the first year of publication of the scientist until the year provided as year of treatment. It is possible to change this behavior in order to focus on a shorter period of time before the year of treatment. This is done by initiating the class :doc:`Original <../reference/sosia.Original>` and setting the option `period` equal to the desired number of years,

.. code-block:: python

    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1,
            pub_margin=1, coauth_margin=1, period=3)


and then proceeding normally with the other steps. `sosia` will return authors starting publishing within 1 year before or after the first year of publication, with maximum 1 publication more or less, 1 citation more or less and 1 coauthor more or less the scientists, between 2017 and 2015 included. More precisely, for citations and coauthors, `sosia` counts: only citations (excluding self-citations) up to 2017 to papers published within the period; the number of unique coauthors in publications within the period. It is left to the user to further restrict the sample of matches based on similarity over the full period (the necessary variables can be obtained as output).

Finally, for demanding users, there exists an option to attenuate the issue of disambiguation of names in Scopus. Scopus Author IDs are curated and fairly correct, on average. However, in some cases they are incorrect. In most of these cases, more than one Author ID is associated to one same author. In `sosia` it is left to the user to verify whether the Author IDs obtained in the list of matches are precise. At the same time, with default settings, there may be a "hypothetical author" that is in theory a good match, but that is not found because she does not have a unique Author ID. This is the type of error that can be attenuated. First, use the option `period` to base the search on a shorter period. This increases the likelihood of finding one Author ID of the "hypothetical author" which is valid within the period. Second, set the option `first_year_search` equal to `"name"`.

.. code-block:: python

    >>> scientist_period = sosia.Original(55208373700, 2017, cits_margin=1,
            pub_margin=1, coauth_margin=1, period=3, first_year_search="name")
    >>> scientist_period.define_search_group()

This allows to ignore whether or not the same Author ID is valid for the full period down to the first year of publication of the target scientist. `sosia` will still filter out Author IDs whose first year of publication is too old, but it will maintain as potential matches Author IDs whose first year of publication is after the year margin provided (this is, the first year of publication of the Author IDs can be later than the upper margin of first year of publication of the target scientist). By now, it is left to the user to complete the profiles of the authors obtained and to reevaluate in a second stage whether they are indeed good matches.
