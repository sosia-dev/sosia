--------------
Initial set-up
--------------

`sosia` infers the scientist's (main )field of research from the field-associations of the sources she publishes in.  Two lists with source information are necessary.  A list linking source titles to fields, and another one that links source titles to source IDs.  Both are stored in `~/.sosia/` (that is, in your home drive - on Unix systems this will be a hidden folder).  Create the lists like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.create_fields_sources_list()


To speed up the process, sosia makes use of a SQLite Database.  Specify the path in `~/.sosia/config.ini` (or keep the default) and initiate the database like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.make_database()
