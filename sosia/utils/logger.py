"""Module to configure the logging for the package."""
import logging
from pathlib import Path

logger = None

_cache_folder = Path.home() / '.cache' / 'sosia/'
_cache_folder.mkdir(parents=True, exist_ok=True)
_log_file = _cache_folder / 'LOG_FILE.log'

def create_logger(name: str = 'sosia',
                  log_file: str | Path = _log_file) -> None:
    """Create a logger for the package."""
    global logger

    logger = logging.getLogger(name)

    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s: %(message)s',
        datefmt='%y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

def get_logger() -> logging.Logger:
    """Return the logger for the package."""
    if logger is None:
        create_logger()
    return logger

def log_scopus(scopus_obj) -> None:
    """Log the results of a Scopus query."""

    scopus_class = scopus_obj.__class__.__name__
    view = scopus_obj._view
    query = scopus_obj._query[:255]

    if scopus_class == 'AuthorSearch':
        results = scopus_obj.get_results_size()
    elif scopus_class == 'ScopusSearch':
        if scopus_obj.results is None:
            results = 0
        else:
            results = len(scopus_obj.results)
    else:
        raise ValueError(f"Unknown Scopus class: {scopus_class}")

    logger = get_logger()

    logger.debug(
        "\n\t- Class: %s\n\t- View: %s\n\t- Query: %s\n\t- Nr Results: %d",
        scopus_class, view, query, results
    )
