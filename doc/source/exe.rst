.. _exe:

================================
Creating a standalone executable
================================

Prerequisites
=============

There exists several tools for freezing a Python application into a standalone executable. Here we describe how to create a standalone executable of a ViSiAnnoT script with **PyInstaller**.

**PyInstaller** uses hooks in order to put the needed packages into the standalone executable. The problem is that it may also add hooks that are not needed, leading to a very big file. For this reason, it is advised to work with virtual environment when generating a standalone executable. One possibility is to follow these steps:

* Install a basic `Python <https://www.python.org/downloads/>`_ with only the core packages,
* Create a virtual environment dedicated to **ViSiAnnoT** and switch to this virtual environment,
* Install **ViSiAnnoT** package and all depedencies,
* Install `PyInstaller <https://www.pyinstaller.org>`_,
* Check if **ViSiAnnoT** runs wihtout error: ``python3 -m visiannot`` (see :ref:`run`),
* Generate the standalone executable.


Generation
==========

In a console:

* Two options for the first step

    * If you have cloned the repository, go to the directory "*exe_generation*"
    * Otherwise

        * Download the specification file `visiannot.spec <https://github.com/RphWbr/visiannot/blob/main/exe_generation/visiannot.spec>`_ and copy it to the directory where you want to generate the standalone executable
        * In ``visiannot.spec``, set the variable ``pkg_dir`` to the path to the directory containing the package **visiannot**
* (optional) Activate python virtual environment
* Run the following command: ``python3 -m PyInstaller visiannot.spec``
* A directory named ``dist`` is automatically created and contains the standalone executable


Specify options
===============

As seen in :ref:`run`, it is possible to specify different options when launching **ViSiAnnoT**. Once the standalone executable is generated, you may create a shortcut with a specific target for the options.
