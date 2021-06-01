============
Installation
============

Clone repository
================

TODO


Pip install
===========

TODO


Depedencies
===========

**ViSiAnnoT** was initially developped using Python 3.5.4 on Windows 7, then using Python 3.8.5 on Ubuntu 20. It is cross-platform and has been tested on Windows 7/10, Ubuntu 16/18/20 and MacOS Mojave/Catalina.

It mainly relies on `PyQt5 <https://pypi.org/project/PyQt5/>`_ for the GUI, on `PyQtGraph <http://pyqtgraph.org/>`_ for video and signal plots and on `OpenCV <https://opencv.org/>`_ for loading video data. Saving and loading configuration files is achieved with `Configobj <https://pypi.org/project/configobj/>`_. `Pytz <https://pypi.org/project/pytz/>`_ is used for date-time comparison. `H5py <https://pypi.org/project/h5py/>`_ is used for reading hdf5 files.

The other packages are rather common in most Python distributions.

Here is an exhaustive list of required packages: 

* ast
* collections
* configobj
* cv2
* datetime
* glob
* h5py
* numpy
* os
* PyQt5
* pyqtgraph
* pytz
* scipy
* shutil
* sys
* threading
* time
* wave
