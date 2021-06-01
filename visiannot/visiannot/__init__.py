# -*- coding: utf-8 -*-

from os.path import dirname
from pkgutil import iter_modules

# import classes to ease import outside of the package
from .ViSiAnnoT import ViSiAnnoT
from .ViSiAnnoTLongRec import ViSiAnnoTLongRec
from .ViSiAnnoTLongRecFromConfigFile import ViSiAnnoTLongRecFromConfigFile
from .ViSiAnnoTLongRecFromConfigGUI import ViSiAnnoTLongRecFromConfigGUI

pkg_dir = dirname(__file__)
__path__ = [pkg_dir]

__all__ = []
for _, module_name, flag_pkg in iter_modules(__path__):
    __all__.append(module_name)
