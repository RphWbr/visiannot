================================
Creating a standalone executable
================================

Prerequisites
=============

There exists several tools for freezing a Python application into a standalone executable. Here we describe how to create a standalone executable of a ViSiAnnoT script with **PyInstaller**.

First, the package `PyInstaller <https://www.pyinstaller.org>`_ must be installed.

PyInstaller uses hooks in order to put the needed packages into the standalone executable. The problem is that it may also add hooks that are not needed, leading to a very big file. For this reason, it is advised to work with virtual environment when generating a standalone executable. One possibility is to follow these steps:

* Install a basic `Python <https://www.python.org/downloads/>`_ with only the core packages,
* Create a virtual environment dedicated to **ViSiAnnoT** and switch to this virtual environment,
* Install **ViSiAnnoT** package and all depedencies,
* Check if the script runs with no error,
* Generate the standalone executable.


Generation
==========

* (optional) Create a directory "visiannot_exe"
* Create the file ``visiannot.spec``::

    # -*- mode: python -*-

    block_cipher = None

    pkg_dir = '/dir/to/parent/visiannot/package'

    # list of files to include into the standalone executable
    data_list = [
        ('%s/Images/*.jpg' % pkg_dir, 'Images'),
        ('%s/components/Images/*.jpg' % pkg_dir, 'Images'),
    ]

    a = Analysis(['/path/to/main_visiannot.py'],
                 binaries=[],
                 datas=data_list,
                 hiddenimports=[],
                 hookspath=[],
                 runtime_hooks=[],
                 excludes=[],
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 noarchive=False)
    pyz = PYZ(a.pure, a.zipped_data,
                 cipher=block_cipher)
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name='ViSiAnnoT_Sensitact',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              runtime_tmpdir=None,
              console=True)

* The following variables must be set:
    
    * ``pkg_dir`` is the path to the directory containing **ViSiAnnoT** package
    * ``'/path/to/main_visiannot.py'`` is the path to the application script to freeze into a standalone executable
* Open a console and place yourself where is located ``visiannot.spec``
* (optional) Activate python virtual environment
* Run the following command: ``python3 -m PyInstaller visiannot.spec``, it may be necessary to replace ``python3`` by ``python`` depending on the alias defined on your computer
* A directory named ``dist`` is automatically created and contains the executable standalone
