"""Module to configure the logging for the package."""
import logging
from pathlib import Path

_cache_folder = Path.home() / '.cache' / 'sosia/'
_cache_folder.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('sosia')

file_handler = logging.FileHandler(_cache_folder / 'sosia.log', mode='a', encoding='utf-8')

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False
