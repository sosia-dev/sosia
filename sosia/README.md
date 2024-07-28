The simplest way to invoke the tests is to use the external [pytest package](https://docs.pytest.org/en/latest/) (`pip install pytest`). Then run

    pytest --verbose

or alternatively

	python -m pytest --verbose

in the command line from within the root directory.

During the tests, files from the Scopus database are downloaded and cached in the usual way.  Hence, tests make use of your API Key and require a valid connection.
