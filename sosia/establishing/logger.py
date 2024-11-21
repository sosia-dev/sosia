"""Module to configure the logging for the package."""

import logging
from typing import Union
from pathlib import Path

from pybliometrics.scopus import AuthorSearch, ScopusSearch

logger = None


def create_logger(log_file: Union[str, Path]) -> None:
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


class ScopusLogger:
    """Context manager to log scopus"""
    def __init__(self, scopus_class_name, params):
        self.scopus_obj: Union[AuthorSearch, ScopusSearch]
        self.scopus_class_name = scopus_class_name
        self.query = params.get('query')
        self.view = params.get('view', 'Default')

        if logger is None:
            create_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not exc_type:
            results = self.scopus_obj.get_results_size()
            self.view = self.scopus_obj._view
        logger.debug(
            '\n\t- Scopus API: %s with %s view \n\t- Query: %s\n\t- Results: %s',
            self.scopus_class_name, self.view, self.query[:255], exc_type or results
        )
