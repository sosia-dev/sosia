"""This module is the entry point for the `sosia` package."""

import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    from importlib_metadata import version

__version__ = version("sosia")

__citation__ = 'Rose, Michael E. and Stefano H. Baruffaldi: "Finding '\
    'Doppelgängers in Scopus: How to Build Scientists Control Groups Using '\
    'Sosia", Max Planck Institute for Innovation & Competition Research '\
    'Paper No. 20-20.'

from sosia.classes import Original
from sosia.establishing import *
