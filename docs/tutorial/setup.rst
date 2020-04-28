--------------
Initial set-up
--------------

`sosia` infers the scientist's (main )field of research from the field-associations of the sources she publishes in.  To this end, two lists with source information are necessary.  A list linking source titles to fields, and a list linking source titles to source IDs.  Both will be stored in `~/.sosia/` (that is, in your home drive - on Unix systems this will be a hidden folder).  Create the lists like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.create_fields_sources_list()


To speed up the process, sosia makes use of a SQLite Database.  Specify the path in `~/.sosia/config.ini` (or keep the default) and initiate the database like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.make_database()
