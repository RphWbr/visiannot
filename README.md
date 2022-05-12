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


License
-------
Copyright Université Rennes 1 / INSERM (2018)

Contributor: Raphaël Weber

raphael.weber@univ-rennes1.fr

This software is a computer program whose purpose is to to provide a graphical user interface for the visualization and annotation of video and signal data.

This software is governed by the CeCILL license under French law and abiding by the rules of distribution of free software. You can  use, modify and/or redistribute the software under the terms of the CeCILL license as circulated by CEA, CNRS and INRIA at the following URL "http://www.cecill.info". 

As a counterpart to the access to the source code and rights to copy, modify and redistribute granted by the license, users are provided only with a limited warranty  and the software's author, the holder of the economic rights, and the successive licensors have only limited liability. 

In this respect, the user's attention is drawn to the risks associated with loading, using, modifying and/or developing or reproducing the software by the user in light of its specific status of free software, that may mean that it is complicated to manipulate, and that also therefore means that it is reserved for developers and  experienced professionals having in-depth computer knowledge. Users are therefore encouraged to load and test the software's suitability as regards their requirements in conditions enabling the security of their systems and/or data to be ensured and, more generally, to use and operate it in the same conditions as regards security.

The fact that you are presently reading this means that you have had knowledge of the CeCILL license and that you accept its terms.


Using ViSiAnnoT in a scientific publication
-------------------------------------------
If you use **ViSiAnnoT** in a scientific publication, we would appreciate citations to the following paper:

CAILLEAU, Léa, WEBER, Raphael, CABON, Sandie, *et al*. [Quiet Sleep Organization of Very Preterm Infants Is Correlated With Postnatal Maturation](https://www.frontiersin.org/articles/10.3389/fped.2020.559658/full). *Frontiers in Pediatrics*, 2020, vol. 8, p. 613.


Bibtex entry::

    @article{cailleau2020quiet,
    title={Quiet sleep organization of very preterm infants is correlated with postnatal maturation},
    author={Cailleau, L{\'e}a and Weber, Raphael and Cabon, Sandie and Flamant, Cyril and Rou{\'e}, Jean-Michel and Favrais, G{\'e}raldine and Gascoin, G{\'e}raldine and Thollot, Aurore and Por{\'e}e, Fabienne and Pladys, Patrick},
    journal={Frontiers in Pediatrics},
    volume={8},
    pages={613},
    year={2020},
    publisher={Frontiers}
    }


Acknowledgment
--------------
The initial development of **ViSiAnnoT** was made possible by a funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 689260 ([Digi-NewB project](http://www.digi-newb.eu/)).
