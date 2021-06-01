# -*- coding: utf-8 -*-

from os.path import dirname
from .Configuration import Configuration
from .ConfigurationWindow import ConfigurationWindow


pkg_dir = dirname(__file__)
__path__ = [pkg_dir]

__all__ = [
    "Configuration",
    "ConfigurationWindow"
]
