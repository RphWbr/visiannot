# -*- coding: utf-8 -*-

"""
in order to automatically generate APIreference index files,
this script must be launched before generating documentation
"""

text_top = "The package **visiannot** is made up of three sub-packages:\n"

text_bottom = """
The sub-package **configuration** contains modules where are defined the
classes for the creation of the configuration GUI.

The sub-package **tools** contains modules with functions that may be used
outside of **ViSiAnnoT**. In particular, the modules **ToolsPyQt** and
**ToolsPyqtgraph** are an overlayer of **PyQt5** and **pyqtgraph**
respectively. They may be used in order to ease the creation of a GUI and
scientific graphics respectively. See chapters :ref:`toolspyqt` and
:ref:`toolspyqtgraph`.

The sub-package **visiannot** contains modules where are defined the classes
for the creation of the ViSiAnnoT GUI.

The summary of the modules can be found at the top of their respective page.
"""

from autoDocAPI import generateIndexFiles
generateIndexFiles(
    "visiannot", "../..", text_top=text_top, text_bottom=text_bottom
)
