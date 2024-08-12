--------------
Initial set-up
--------------

Source information
------------------

sosia infers the scientist's main field of research from the field associations of the sources in which they publish. Two lists containing source information are required: one list linking source titles to fields, and another listing, for each source ID, the source type and its name. Both lists are stored in ~/.cache/sosia/ (a hidden folder in your home directory on Unix systems). You can create these lists as follows:

.. code-block:: python
   
    >>> import sosia
    >>> sosia.get_field_source_information(verbose=True)
    Stored information for 97,292 sources as well as 234,384 field-source
    assignments in /home/merose/.cache/sosia/

We provide two files via a companion repository on GitHub, [sosia-dev/sosia-data](https://github.com/sosia-dev/sosia-data). This data is updated in the spring and fall when Scopus revises its list of included source definitions. Since source types and associated fields may change, the results may also change after updates. We recommend keeping the source definitions constant or, at the very least, carefully checking for changes in the results after updates.

Local SQLite Database
---------------------

To speed up the process, `sosia` utilizes an SQLite database. The database gets filled automatically, and values in the database take precedence. `sosia` does not automatically update values in the database. To do so, simply use the `refresh` parameter described below.

Create the database like so:

.. code-block:: python

    >>> sosia.make_database()

If you do not specify a path, `sosia` will default to `~/.cache/sosia/main.sqlite`, where ~ refers to your user directory.

The database can be located anywhere; for small projects, we recommend placing it in the project folder, while for larger projects, it's better to store it in a location such as ~/.cache/sosia/<project_name>.sqlite. 

.. code-block:: python
   
    >>> from pathlib import Path
    >>> DB_NAME = Path("./sosia/project.sqlite")
	>>> sosia.make_database(DB_NAME)
