ViSiAnnoT
=========

**ViSiAnnoT** (Video Signal Annotation Tool) is a package that provides a graphical user interface for the visualization and annotation of video and signal data.

The main features are:

- Simultaneous visualization of several videos
- Simultaneous visualization of several signals

  - Regularly sampled or not
  - Zoom on signals
  - Plot thresholds on signals
  - Plot temporal intervals on signals
- Combined visualization of videos and signals
- Management of long recordings (split in several files)

  - Automatic synchronization between the different modalities
  - Tools for fast navigation
- Multi-label annotation of temporal events
- Multi-label image extraction
- Configuration via a graphical user interface

![](https://github.com/RphWbr/visiannot/raw/main/doc/source/images/layout_mode_2.png)


Documentation
-------------

Documentation is hosted on [ReadTheDocs](https://visiannot.readthedocs.io/en/latest/index.html).



Installation
------------

**Pip**

The easiest way is to install **ViSiAnnoT** with ``pip``:

    $ pip install visiannot

You may need to call ``pip3`` instead.


**From source**

You may install **ViSiAnnoT** from source:

    $ git clone https://github.com/RphWbr/visiannot
    $ cd visiannot
    $ pip install .


**Depedencies**

**ViSiAnnoT** requires Python 3.6+.

It is cross-platform and has been tested on Windows 7/10, Ubuntu 16/18/20 and MacOS Mojave/Catalina.

The following packages are required and are automatically installed with ``pip``: 

* [configobj](https://pypi.org/project/configobj/) (saving and loading configuration files)
* [opencv-python](https://opencv.org/)
* [h5py](https://pypi.org/project/h5py/)
* [numpy](https://numpy.org/)
* [PyQt5](https://pypi.org/project/PyQt5/) (GUI creation)
* [pyqtgraph](http://pyqtgraph.org/) (video and signal plots)
* [pytz](https://pypi.org/project/pytz/) (used for date-time comparison)
* [scipy](https://www.scipy.org/)
* [tinytag](https://pypi.org/project/tinytag/)


Run ViSiAnnoT
-------------

Once it is installed, you can launch **ViSiAnnoT** with the following command line::

    $ python3 -m visiannot

First, the configuration GUI will open, see [dedicated user guide](https://visiannot.readthedocs.io/en/latest/userguide-configuration.html#configuration-with-the-graphical-user-interface). Then the ViSiAnnoT GUI will open, see [dedicated user guide](https://visiannot.readthedocs.io/en/latest/userguide-visiannot.html).

In order to familiarize with **ViSiAnnoT**, an example of dataset is provided on [GitHub](https://github.com/RphWbr/visiannot-example). You may download or clone this repository on your computer.


Support
-------

This package is developed at the LTSI Lab, INSERM-1099, located at Université Rennes 1, France.

For any enquiry, please send an email to raphael.weber@univ-rennes1.fr.

If you encounter a bug, feel free to raise an issue on [GitHub](https://github.com/RphWbr/visiannot/issues).


Used by
-------

**ViSiAnnoT** has been used in several clinical studies during the time of initial developments, with a particular focus in pediatrics. In particular, it has been used in a study on quiet sleep organization that has been published in the following article, where is introduced **ViSiAnnoT**: [Quiet Sleep Organization of Very Preterm Infants Is Correlated With Postnatal Maturation](https://www.frontiersin.org/articles/10.3389/fped.2020.559658/full).
