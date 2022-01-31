# -*- coding: utf-8 -*-

from os.path import dirname
from pkgutil import iter_modules

# import classes/functions to ease import outside of the package
from .Configuration import Configuration, check_configuration
from .ConfigurationWindow import ConfigurationWindow


pkg_dir = dirname(__file__)
__path__ = [pkg_dir]

__all__ = []
for _, module_name, flag_pkg in iter_modules(__path__):
    __all__.append(module_name)
