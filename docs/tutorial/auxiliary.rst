---------------------
Auxiliary information
---------------------

Source information
------------------

`sosia` infers the scientist's main field of research from the field associations of the sources in which they publish. Two lists containing source information are required: one list linking source titles to fields, and another listing, for each source ID, the source type and its name. Both files are stored in ~/.cache/sosia/ (a folder in your home directory, on Unix systems the folder is hidden).

If the files do not exist, `sosia` downloads them automatically. To update them, you can downloada them as follows:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.get_field_source_information(verbose=True)
    Stored information for 99,210 sources as well as 241,648 field-source
    assignments in '/home/merose/.cache/sosia/'

We provide two files via a companion repository on GitHub, [sosia-dev/sosia-data](https://github.com/sosia-dev/sosia-data). This data is updated in spring and fall, when Scopus revises its list of included source definitions. Since source types and associated fields may change, your results may also change after updates. We recommend keeping the source definitions constant within a project. At the very least, expect changes in your results after updates.

Local SQLite Database
---------------------

To speed up the process, `sosia` utilizes an SQLite database. Create the database like so:

.. code-block:: python
   
    >>> from pathlib import Path
    >>> DB_NAME = Path("./sosia/project.sqlite")
    >>> sosia.make_database(DB_NAME, verbose=True)
    Local database './sosia/project.sqlite' created successfully

If you do not specify a path, `sosia` will default to `~/.cache/sosia/main.sqlite` (a folder in your home directory, on Unix systems the folder is hidden). The database can be located anywhere; for multiple small and distinct projects, we recommend utilizing separate databases in the project folder.

The database gets filled automatically, and values in the database take precedence. `sosia` does not automatically update values in the database. To do so, simply use the `refresh` parameters in the corresponding functions.
