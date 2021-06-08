============
Installation
============

Pip
===

The easiest way is to install **ViSiAnnoT** with ``pip``::

    $ pip install visiannot

You may need to call ``pip3`` instead.


From source
===========

You may install **ViSiAnnoT** from source::

    $ git clone https://github.com/RphWbr/visiannot
    $ cd visiannot
    $ pip install .


Depedencies
===========

**ViSiAnnoT** requires Python 3.6+.

It is cross-platform and has been tested on Windows 7/10, Ubuntu 16/18/20 and MacOS Mojave/Catalina.

The following packages are required and are automatically installed with ``pip``: 

* `configobj <https://pypi.org/project/configobj/>`_ (saving and loading configuration files)
* `opencv-python <https://opencv.org/>`_
* `h5py <https://pypi.org/project/h5py/>`_
* `numpy <https://numpy.org/>`_
* `PyQt5 <https://pypi.org/project/PyQt5/>`_ (GUI creation)
* `pyqtgraph <http://pyqtgraph.org/>`_ (video and signal plots)
* `pytz <https://pypi.org/project/pytz/>`_ (used for date-time comparison)
* `scipy <https://www.scipy.org/>`_


Run ViSiAnnoT
=============

Once it is installed, you can launch **ViSiAnnoT** with the following command line::

    $ python3 -m visiannot

First, the configuration GUI will open, see chapter :ref:`configuration`. Then the ViSiAnnoT GUI will open, see chapter :ref:`userguide-visiannot`.
