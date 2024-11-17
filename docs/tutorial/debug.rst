---------
Debugging
---------

Queries may occasionally fail for various reasons. The internet is an unpredictable medium, and not all transmitted data arrives perfectly. To facilitate troubleshooting, `sosia` logs every query made against the Scpous APIs with the help of the `logging <https://docs.python.org/3/library/logging.html>`_ library. By default, the log file is stored a `~/.cache/sosia/sosia.log`. However, you can specify a custom path by using the `Original(log_path="...")` parameter.

The log file records entries in the following format:

.. code-block:: yaml
   
    24-11-16 21:47:20 - DEBUG: 
        - Scopus API: Scopus Search
        - View: COMPLETE
        - Query: AU-ID(55208373700)
        
    24-11-16 21:47:21 - DEBUG: 
        - Scopus API: Scopus Search
        - View: COMPLETE
        - Query: REF(55208373700) AND PUBYEAR BEF 2019 AND NOT AU-ID(55208373700)


For instance, you may want to refresh the query manually using `pybliometrics`.

Each new call of `Original()` will overwrite the existing log file. If preserving previous logs is necessary, consider backing up the log file before re-initializing.
