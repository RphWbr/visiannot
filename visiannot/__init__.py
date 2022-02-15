"""
ViSiAnnoT: VIdeo and SIgnal Annotation Tool
===========================================

Package for visualization and annotation of video and signal data

Initially developed as part of the european project Digi-NewB at the LTSI lab,
Université Rennes 1.
"""

__version__ = "0.2.7"
__authors__ = "Raphaël Weber"


from os.path import dirname
from pkgutil import iter_modules

pkg_dir = dirname(__file__)
__path__ = [pkg_dir]

__all__ = []
for _, module_name, _ in iter_modules(__path__):
	__all__.append(module_name)
