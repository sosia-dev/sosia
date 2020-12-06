from configparser import ConfigParser, DuplicateSectionError
from os import makedirs
from os.path import split

from sosia.establishing.constants import CONFIG_FILE
from sosia.utils.defaults import CONFIG_DEFAULTS

config = ConfigParser()
config.optionxform = str
try:
    config.read_file(open(CONFIG_FILE))
except FileNotFoundError:
    # Create config
    for sec_key, d in CONFIG_DEFAULTS.items():
        try:
            config.add_section(sec_key)
        except DuplicateSectionError:
            pass
        for key, val in d.items():
            config.set(sec_key, key, val)
    try:
        try:
            path, fname = split(CONFIG_FILE)
            makedirs(path)
        except FileExistsError:
            pass
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    except FileNotFoundError:  # Fix for sphinx build
        pass
