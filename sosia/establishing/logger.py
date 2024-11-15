"""Module to configure the logging for the package."""

import logging
from typing import Union
from pathlib import Path
from re import sub

logger = None


def create_logger(log_file: Union[str, Path] = None) -> None:
    """Configure a logger."""
    global logger

    logger = logging.getLogger("sosia")

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s: %(message)s',
        datefmt='%y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


def log_scopus(scopus_obj) -> None:
    """Log the results of a Scopus query."""
    scopus_class = scopus_obj.__class__.__name__
    scopus_name = sub(r'(?<!^)([A-Z])', r' \1', scopus_class)
    view = scopus_obj._view
    query = scopus_obj._query

    if logger is None:
        create_logger()

    logger.debug(
        "\n\t- Scopus API: %s\n\t- View: %s\n\t- Query: %s\n\t",
        scopus_name, view, query
    )
