from pbr.version import VersionInfo

_v = VersionInfo("sosia").semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()

from sosia.sosia import Original
from sosia.utils import *
