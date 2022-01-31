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


Dependencies
============

**ViSiAnnoT** requires Python 3.6+.

It is cross-platform and has been tested on Windows 7/10, Ubuntu 16/18/20 and MacOS Mojave/Catalina.

The following packages are required and are automatically installed with ``pip``: 

* `configobj <https://pypi.org/project/configobj/>`_ (saving and loading configuration files)
* `opencv-python <https://opencv.org/>`_ (loading video files)
* `h5py <https://pypi.org/project/h5py/>`_ (loading .h5 files)
* `numpy <https://numpy.org/>`_
* `PyQt5 <https://pypi.org/project/PyQt5/>`_ (GUI creation)
* `pyqtgraph <http://pyqtgraph.org/>`_ (video and signal plots)
* `pytz <https://pypi.org/project/pytz/>`_ (date-time comparison with time zone)
* `scipy <https://www.scipy.org/>`_ (loading .mat files)


.. _run:

Run ViSiAnnoT
=============

Once it is installed, you can launch **ViSiAnnoT** with the following command line::

    $ python3 -m visiannot

First, the configuration GUI will open, see chapter :ref:`configuration`. Then the ViSiAnnoT GUI will open, see chapter :ref:`userguide-visiannot`.

In order to familiarize with **ViSiAnnoT**, an example of dataset is provided on `GitHub <https://github.com/RphWbr/visiannot-example>`_. You may download or clone this repository on your computer.

There are several optional arguments, run ``python3 -m visiannot -h`` to get help. Below we give some examples on how to use them.

Specify a configuration file to load::

    $ python3 -m visiannot -c path/to/config.ini

Disable configuration GUI (only ViSiAnnoT GUI is launched)::

    $ python3 -m visiannot -c path/to/config.ini -n

Disable ViSiAnnoT GUI (only configuration GUI is launched)::

    $ python3 -m visiannot -m

Call a function in order to automatically update the configuration before launching the GUIs (see :ref:`customization` for details)::

    $ python3 -m visiannot -c path/to/config.ini -u visiannot.configuration.update.update_data_and_annotations_directory
