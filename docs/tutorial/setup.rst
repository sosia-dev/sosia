--------------
Initial set-up
--------------

`sosia` infers the scientist's (main )field of research from the field-associations of the sources she publishes in.  Two lists with source information are necessary.  A list linking source titles to fields, and another one that lists for each source ID the source type and its name.  Both are stored in `~/.cache/sosia/` (that is, in your home drive - on Unix systems this will be a hidden folder).  Create the lists like so:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.get_field_source_information(verbose=True)
    Stored information for 91,271 sources as well as 204,906 field-source
    assigments in /home/merose/.cache/sosia/


To speed up the process, sosia makes use of a SQLite Database.  Specify the path and pass it on in:

.. code-block:: python
   
    >>> from pathlib import Path
    >>> DB_NAME = Path("./sosia/project.sqlite")
    >>> sosia.make_database(DB_NAME)


The database can be anywhere; for small projects we advise to have it in the project folder, for large projects we recomment other places such as `~/.cache/sosia/<project_name>.sqlite`.  If you do not specify a path, `sosia` will default to `~/.cache/sosia/main.sqlite`.
