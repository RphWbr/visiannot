.. _customization:

=============
Customization
=============

It is possible to call a function to automatically update the configuration before launching the GUIs::

    $ python3 -m visiannot -c path/to/config.ini -n -u visiannot.configuration.configUpdateExamples.updateDataAndAnnotationDirectory

The option ``-c`` specifies the path to the configuration file to load. The option ``-n`` disables configuration GUI. With the option ``-u``, we give the path to a function in **visiannot** package that updates the loaded configuration dictionary. The update function may be in a module that is not in a package (``moduleName.functionName``). It must have one positional argument (path to the configuration file) and must return the updated configuration dictionary.

Let's give an example to illustrate the effect of the configuration update function. We have a dataset organized as follows::

    |__ DATA
        |__ Subject01
            |__ Subject01_2021-01-01T00-00-00
                |__ Subject01_vid_2021-01-01T00-00-00.mp4
                |__ Subject01_vid_2021-01-01T00-30-00.mp4
                |__ Subject01_sig_2021-01-01T00-00-30.h5
                |__ Subject01_sig_2021-01-01T00-30-30.h5
            |__ Subject01_2021-02-01T00-00-00
                |__ Subject01_vid_2021-02-01T00-00-00.mp4
                |__ Subject01_vid_2021-02-01T00-30-00.mp4
                |__ Subject01_sig_2021-02-01T00-00-30.h5
                |__ Subject01_sig_2021-02-01T00-30-30.h5
        |__ Subject02
            |__ Subject02_2021-01-03T01-00-00
                |__ Subject02_vid_2021-01-03T01-00-00.mp4
                |__ Subject02_vid_2021-01-03T01-30-00.mp4
                |__ Subject02_sig_2021-01-03T01-00-30.h5
                |__ Subject02_sig_2021-01-03T01-30-30.h5
            |__ Subject02_2021-02-03T01-00-00
                |__ Subject02_vid_2021-02-03T01-00-00.mp4
                |__ Subject02_vid_2021-02-03T01-30-00.mp4
                |__ Subject02_sig_2021-02-03T01-00-30.h5
                |__ Subject02_sig_2021-02-03T01-30-30.h5

There is a folder for each subject, with a sub-folder for each recording. A recording is made up of two video files and two signal files that are not synchronized.

We want the annotations to be stored as follows (two labels, "Label1" and "Label2")::

    |__ Annnotations
        |__ Subject01
            |__ Subject01_2021-01-01T00-00-00
                |__ Subject01_2021-01-01T00-00-00_Label1-datetime.txt
                |__ Subject01_2021-01-01T00-00-00_Label1-frame.txt
                |__ Subject01_2021-01-01T00-00-00_Label2-datetime.txt
                |__ Subject01_2021-01-01T00-00-00_Label2-frame.txt
        |__ Subject02
            |__ Subject02_2021-01-03T01-00-00
                |__ Subject02_2021-01-03T01-00-00_Label1-datetime.txt
                |__ Subject02_2021-01-03T01-00-00_Label1-frame.txt
                |__ Subject02_2021-01-03T01-00-00_Label2-datetime.txt
                |__ Subject02_2021-01-03T01-00-00_Label2-frame.txt

When we change subject and/or recording, we need to update the following fields in the configuration file (see :ref:`configuration`):

* First field of each video configuration (directory where to find video files),
* First field of each signal configuration (directory where to find signal files),
* Field ``annot_dir`` in the section ``General``.

Thanks to the option ``-u``, it is possible to automate this process of configuration update. When running the command above, the function :func:`.updateDataAndAnnotationDirectory` is called before launching the GUIs. It runs the following steps:

* Load the configuration file as a dictionary,
* Open a dialog window for selecting a recording folder (e.g. "*DATA/Subject02/Subject02_2021-01-03T01-00-00*"),
* Update first field of each video configuration in the configuration dictionary with the selected directory,
* Update first field of each signal configuration in the configuration dictionary with the selected directory,
* Get the annotation directory defined as ``annotDirBase/patID/recName``, where ``annotDirBase`` is the initial value of the annotation directory in the configuration file, ``recName`` is the basename of the selected directory (e.g. "Subject02_2021-01-03T01-00-00") and ``patID`` is the patient ID (e.g. "Subject02"),
* Update the field ``annot_dir`` in the section ``General`` of the configuration dictionary with the new annotation directory.

In order to have the dialog window to open at particular location at launch, it is possible to add the key ``data_dir_base`` in the section ``General`` of the configuration file.

**NB**: only the configuration dictionary is updated in the function, the configuration file remains unchanged, implying that it is not needed to reset the value of ``annot_dir`` in the configuration file after each launch.
