---------
Debugging
---------

Queries may occasionally fail for various reasons. The internet is an unpredictable medium, and not all transmitted data arrives perfectly. To facilitate troubleshooting, `sosia` logs every query made against the Scpous APIs with the help of the `logging <https://docs.python.org/3/library/logging.html>`_ library. By default, the log file is stored a `~/.cache/sosia/sosia.log`. However, you can specify a custom path by using the `Original(log_path="...")` parameter.

The log file records entries in the following format:

.. code-block:: yaml
   
    24-11-22 10:09:49 - DEBUG: 
        - Scopus API: Scopus Search with COMPLETE view 
        - Query: AU-ID(55567912500)
        - Results: 13
    24-11-22 10:09:51 - DEBUG: 
        - Scopus API: Scopus Search with COMPLETE view 
        - Query: REF(55567912500) AND PUBYEAR BEF 2019 AND NOT AU-ID(55567912500)
        - Results: <class 'SomeErrorClass'>


For instance, you may want to refresh the query manually using `pybliometrics`.

Each new call of `Original()` will overwrite the existing log file. If preserving previous logs is necessary, consider backing up the log file before re-initializing.
