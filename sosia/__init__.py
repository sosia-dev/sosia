# -*- coding: utf-8 -*-
from pbr.version import VersionInfo

_v = VersionInfo("sosia").semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()

__citation__ = 'Rose, Michael E. and Stefano H. Baruffaldi: "Finding '\
    'Doppelgängers in Scopus: How to Build Scientists Control Groups Using '\
    'Sosia", Max Planck Institute for Innovation & Competition Research '\
    'Paper No. 20-20.'

from sosia.classes import Original
from sosia.establishing import *
