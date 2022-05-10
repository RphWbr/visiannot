.. _configuration:

=========================
User guide: configuration
=========================

Previous section introduced the features of **ViSiAnnoT** and it goes to show that the software is highly configurable. The configuration might not be easy for people not familiar with computer sciences. So we provide a graphical tool for creating, loading and saving configurations, that we describe in this section.

The configuration of **ViSiAnnoT** can be be split in seven parts: video, signal, threshold, interval, events annotation, image extraction, general. There are three ways to achieve the configuration:

* Editing a Python script (both for :class:`.ViSiAnnoT` and :class:`.ViSiAnnoTLongRec`),
* Editing a configuration file complying with the formatting of **Configobj** package (only for :class:`.ViSiAnnoTLongRec`),
* Using the configuration tool that we provide, consisting in a graphical user interface (only for :class:`.ViSiAnnoTLongRec`).

Several examples on how to configure :class:`.ViSiAnnoT` and :class:`.ViSiAnnoTLongRec` in a script are given in the chapter :ref:`userguide-visiannot`.


Editing a configuration file
============================

Configuration files are managed with the **Configobj** package. See `this link <https://configobj.readthedocs.io/en/latest/configobj.html#the-config-file-format>`_ for details about text formatting inside the configuration file. Below we give examples that show how to configure :class:`.ViSiAnnoTLongRec`.


Video
-----

See section :ref:`video` for details about video configuration. In a Python script, it is stored in a dictionary as in the following example::

    video_dict = {}
    video_dict["BW1"] = ["dir/to/video", "*BW1*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"]
    video_dict["BW2"] = ["dir/to/video", "*BW2*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"]

In the configuration file, we create a section named "Video", composed of as much sub-sections as cameras. The name of the subsections is equivalent to the dictionary keys. Here is the equivalent video configuration::

    [Video]
    BW1 = ["dir/to/video", "*BW1*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"]
    BW2 = ["dir/to/video", "*BW2*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"]

The brackets may be omitted::

    [Video]
    BW1 = "dir/to/video", "*BW1*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"
    BW2 = "dir/to/video", "*BW2*.mp4", '_', 1, "%Y-%m-%dT%H-%M-%S"

The drawback of the compact writing is that it loses clarity for long lists as it is not allowed to span several lines for a single key (e.g. BW1).


Signal
------

See section :ref:`signal` for details about signal configuration. In a Python script, it is stored in a dictionary as in the following example::

    signal_dict = {}

    signal_dict["ECG"] = [
        ['dir/to/sig', "physio_*.h5", '_', 1, "%Y-%m-%dT%H-%M-%S", "ecg", 500, None],
        ['dir/to/sig', "physio_*.h5", '_', 1, "%Y-%m-%dT%H-%M-%S", "beat - TQRS", 0, {'pen': None, 'symbol': '+', 'symbolPen': 'r', 'symbolSize': 10}]
    ]

    signal_dict["Respiration"] = [
        ['dir/to/sig', "physio_*.h5", '_', 1, "%Y-%m-%dT%H-%M-%S", "resp", "resp/freq", {'pen': {'color': 'm', 'width': 1}}]
    ]

There are two signal widgets ("ECG" and "Repsiration"), with two signals in the first one and one signal in the second one. In the configuration file, we create a section named "Signal", composed of as much sub-sections as signal widgets. Each sub-section is composed of as much sub-sub-sections as signals in the corresponding signal widget. Here is the equivalent signal configuration::

    [Signal]
    ECG = [['dir/to/sig', 'physio_*.h5', '_', 1, '%Y-%m-%dT%H-%M-%S', 'ecg', '500', None], ['dir/to/sig', 'physio_*.h5', '_', 1, '%Y-%m-%dT%H-%M-%S', 'tqrs', 0, {'pen': None, 'symbol': '+', 'symbolPen': 'r', 'symbolSize': 10}]]
    Respiration = [['dir/to/sig', 'physio_*.h5', '_', 1, '%Y-%m-%dT%H-%M-%S', 'resp', 'resp/freq', {'pen': {'color': 'm', 'width': 1}}]]


YRange
------
See section :ref:`yrange` for details about YRange configuration. In a Python script, it is stored in a dictionary as in the following example::

    y_range_dict = {}
    y_range_dict["ECG"] = (500, 1000)

In the configuration file, we create a section named "YRange", composed of as much keys as signal widgets where to set the Y axis range. Here is the equivalent YRange configuration::

    [YRange]
    ECG = (500, 1000)


Threshold
---------
See section :ref:`threshold` for details about threshold configuration. In a Python script, it is stored in a dictionary as in the following example::

    threshold_dict = {}
    threshold_dict["RR"] = [
        [600, (220, 0, 0)],
        [750, (178, 34, 34)]
    ]

In the configuration file, we create a section named "Threshold", composed of as much sub-sections as threshold values. Here is the equivalent threshold configuration::

    [Threshold]
    [[RR]]
    key_0 = [600, [220, 0, 0]]
    key_1 = [750, [178, 34, 34]]


Interval
--------

See section :ref:`intervals` for details about interval configuration. In a Python script, it is stored in a dictionary as in the following example::

    interval_dict = {}
    interval_dict["ECG"] = [
        ["dir/to/interval", "I0_*.txt", '_', 0, '%Y%m%dT%H%M%S', "", 500, (0, 255, 0, 50)],
        ["dir/to/interval", "I1_*.txt", '_', 0, '%Y%m%dT%H%M%S', "", 500, (255, 200, 0, 50)]
    ]

Intervals must be plotted only the signal widget "ECG" with two interval types. In the configuration file, we create a section named "Interval", composed of as much sub-sections as signal widgets on which to plot intervals. Each sub-section is composed of as much sub-sub-sections as interval types to plot on the corresponding signal widget. Here is the equivalent interval configuration::

    [Interval]
    ECG = [["dir/to/interval", "I0_*.txt", '_', 0, '%Y%m%dT%H%M%S', "", 500, [0, 255, 0, 50]], ["dir/to/interval", "I1_*.txt", '_', 0, '%Y%m%dT%H%M%S', "", 500, [255, 200, 0, 50]]]


Events annotation
-----------------

See section :ref:`eventsannot` for details about events annotation configuration. In a Python script, it is stored in a dictionary as in the following example::

    annotevent_dict = {}
    annotevent_dict["Label-1"] = [200, 105, 0, 50]
    annotevent_dict["Label-2"] = [105, 205, 0, 50]

In the configuration file, we create a section named "AnnotEvent", composed of as much sub-sections as labels. Here is the equivalent events annotation configuration::

    [AnnotEvent]
    Label-1 = [200, 105, 0, 50]
    Label-2 = [105, 205, 0, 50]


Image extraction
----------------

See section :ref:`image-extraction` for details about image extraction configuration. In a Python script, it is stored in a list as in the following example::

    annotimage_list = ["Label-A", "Label-B", "Label-C"]

In the configuration file, we create a section named "AnnotImage"::

    [AnnotImage]
    k0 = "Label-A"
    k1 = "Label-B"
    k2 = "Label-C"

We must keep the dictionary structure because of the structure of the class :class:`.Configuration`. Nevertheless, it is converted to a list inside :class:`.ViSiAnnoT`.


General
-------

In a Python script, the general configuration is specified with the keyword arguments of :class:`.ViSiAnnoTLongRec` and :class:`.ViSiAnnoT`. In the configuration file, we create a section named "General" as in the following example::

    [General]
    temporal_range = (0, 30)
    flag_pause_status = True
    layout_mode = 1
    zoom_factor = 2
    max_points = 5000
    nb_ticks = 10
    time_zone = 'Europe/Paris'
    annot_dir = 'Annotations'
    from_cursor_list = [[0, 20], [0, 40], [1, 0]]
    ticks_size = 12
    ticks_color = [93, 91, 89]
    ticks_offset = 5
    font_name = 'Times'
    font_size = 12
    font_size_title = 16
    font_color = [0, 0, 0]
    nb_table_annot = 3
    bg_color = [244, 244, 244]
    bg_color_plot = [255, 255, 255]
    height_widget_signal = 150
    flag_annot_overlap = False
    current_fmt = '%Y-%m-%dT%H:%M:%S.%s'
    range_fmt = '%H:%M:%S.%s'
    ticks_fmt = '%H:%M:%S.%s'
    y_ticks_width = 30


If a key is not specified in the configuration file, then the keyword argument takes the default value of :class:`.ViSiAnnoT` constructor.

.. _config-gui:

Configuration with the graphical user interface
===============================================

This configuration tool only manages long recordings (see section :ref:`sec-longrec`) and is composed of six parts: video, signal, events annotation, image extraction, general and configuration file management. On the one hand, the user sets up manually the configuration by filling in the fields in the window. On the other hand, the tool can automatically convert the values filled in the window to a configuration file complying with the **Configobj** package. It also handles the inverse operation, so that the user can save and load custom configurations.


Video
-----
The video configuration is contained in the first group box named "Video".

The user must click on the push button "Add" in order to create a new video configuration, corresponding to a new camera. Once a video configuration is added, there are 5 fields to fill in: 

* Directory where to find the video files,
* Pattern to find the video files,
* Delimiter to get the beginning datetime in the video file name,
* Position of the beginning datetime in the video file name, according to the delimiter,
* Format of the beginning datetime in the video file name (``"posix"`` or format compliant with ``datetime``, see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).

:numref:`fig-config-video` shows an example of video configuration with three cameras that would give a display similar to :numref:`fig-example-video`.

.. _fig-config-video:

.. figure:: images/configuration_video.png

  Example of video configuration

The "Help" push buttons displays a window with a description of each field.


Signal
------
The signal configuration is contained in the second group box named "Signal".

The user must click on the push button "Add" in order to create a new signal configuration. Then, in order to have multiple signals on the same plot, he must click on the push button "Add sub" located next to the signal configuration. Once a signal configuration is added, there are 9 fields to fill in:  

* Signal widget ID (used as the Y axis label on the plot)
* Directory where to find the signal files,
* Pattern to find the signal files,
* Delimiter to get the beginning datetime in the signal file name,
* Position of the beginning datetime in the signal file name, according to the delimiter,
* Format of the beginning datetime in the signal file name (``"posix"`` or format compliant with ``datetime``, see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes),
* Key to access the data in the file (in case of .h5 or .mat, set it to ``''`` otherwise), also used a legend - in case of 2D data with several value columns, then the column index must be specified, e.g. ``"key - 1"`` or ``"key - colName"`` if there is an attribute at ``key`` named ``columns`` with columns name being comma-separated (first column is always the timestamps),
* Signal frequency (may also be a string with path to the frequency attribute in case of h5 file), set it to ``0`` in case of non-regularly sampled signal,
* Dictionary with plot style.

:numref:`fig-config-signal` shows an example of signal configuration with two plots and three signals. The first widget (resp. second one) contains two signals plots (resp. one signal plot) and would give a display similar to :numref:`fig-example-signal` and :numref:`fig-example-signal-zoom`.

.. _fig-config-signal:

.. figure:: images/configuration_signal.png

  Example of signal configuration


:numref:`fig-config-audio` shows an example of audio signal configuration with a plot for each channel. The first plot (resp. second one) contains the left channel (resp. right channel).

.. _fig-config-audio:

.. figure:: images/configuration_audio.png

  Example of audio signal configuration


YRange
------
The user can manage the YRange configuration by clicking on the push button "YRange" located above the signal configuration. This opens a new window illustrated in figure :numref:`fig-config-yrange`. The push button "Add" allows to add a YRange configuration that is automatically linked to an existing signal widget.

.. _fig-config-yrange:

.. figure:: images/configuration_yrange.png

  Example of YRange configuration


Threshold
---------
The user can manage the threshold configuration by clicking on the push button "Threshold" located above the signal configuration. This opens a new window illustrated in figure :numref:`fig-config-threshold`. The push button "Add" allows to add a threshold configuration that is automatically linked to an existing signal configuration thanks to the signal widget ID. Several thresholds can be added to one signal widget with the push button "Add sub".

.. _fig-config-threshold:

.. figure:: images/configuration_threshold.png

  Example of threshold configuration

Once a threshold configuration is added, there are 2 fields to fill in:

* Value of the threshold,
* Color of the threshold line (RGBA).

If we combine this threshold configuration with the second signal configuration of :numref:`fig-config-signal`, this would give a display similar to :numref:`fig-example-threshold`.


Interval
--------
Similarly to the threshold configuration, the user can manage the interval configuration by clicking on the push button "Interval" located above the signal configurations. This opens a new window, illustrated in figure :numref:`fig-config-intervals`.

Once an interval configuration is added, there are 8 fields to fill in:

* Directory where to find the intervals files,
* Pattern to find the intervals files,
* Delimiter to get the beginning datetime in the signal file name,
* Position of the beginning datetime in the signal file name, according to the delimiter,
* Format of the beginning datetime in the signal file name (``"posix"`` or format compliant with ``datetime``, see https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes),
* Key to access the data in the file (in case of .h5 or .mat, set it to ``''`` otherwise),
* Frequency (in case of a time series, may also be a string with path to the frequency attribute in case of h5 file),
* Color of the interval (RGBA).

.. _fig-config-intervals:

.. figure:: images/configuration_interval.png

  Example of intervals configuration

If we combine this interval configuration with the first signal configuration in :numref:`fig-config-signal`, this would give a display similar to figure :numref:`fig-example-intervals`.


Events annotation
-----------------
The events annotation configuration is contained in the third group box named "AnnotEvent". Figure :numref:`fig-annotevent` shows an example.

.. _fig-annotevent:

.. figure:: images/configuration_annotevent.png

  Screenshot of the events annotation configuration

The user must click on the push button "Add" in order to create a new annotation configuration, corresponding to a new label. Once an annotation configuration is added, there are two fields to fill in: 

* Annotation label
* Color for plotting


Image extraction
----------------
The image extraction configuration is contained in the fourth group box named "AnnotImage". Figure :numref:`fig-annotimage` shows an example.

.. _fig-annotimage:

.. figure:: images/configuration_annotimage.png

  Screenshot of the image annotation configuration


The user must click on the push button "Add" in order to create a new annotation configuration, corresponding to a new label. Once an annotation configuration is added, there is one field to fill in: annotation label.


General
-------
The general configuration is contained in the fifth group box named "General". Figure :numref:`fig-general` shows an example with default values. 

.. _fig-general:

.. figure:: images/configuration_general.png

  Screenshot of the general configuration

The "Temporal range" spin boxes specify the duration of "files" in the long recording.

The "Video paused to launch" check box specifies if the video must be in pause mode when launching the software.

The "Events annotations overlap" check box specifies if the overlap of events annotations is enabled.

The "Layout mode" spin box specifies the layout mode (see :numref:`fig-example-combined`).

The "Time zone" line edit specifies the time zone that is used for date-time comparison.

The "Max nb of points to display" spin box specifies the maximum number of signal samples that are plotted. For a given temporal range, if the number of signal samples contained in this range is above the maximum number, then we simply skip samples so that we reach the maximum number.

The "Minimum height in pixels of the signal widgets" spin box specifies the vertical size of the signal widgets in the scroll area in case it exceeds the size of the window.

The "Zoom factor" spin box specifies the zoom factor when zooming in/out around the temporal cursor.

The "Temporal ticks nb" spin box specifies the number of ticks on the X axis of the signal plots.

The "Ticks color" spin boxes specify the color of the ticks.

The "Ticks size" spin box specifies the font size of the ticks text.

The "Ticks offset" spin box specifies the space in pixels between the ticks and the associated text.

The "Font name" line edit specifies the font of the text in ViSiAnnoT.

The "Font size" spin box specifies the font size.

The "Font size" spin box specifies the font size for the title of the video widgets and the progression bar widget.

The "Font color" spin boxes specify the font color.

The "Maximum number of labels in a row" spin box specifies the maximum number of labels to put in a row in the widgets of events annotation and image annotation.

The "Background color" spin boxes specify the background color of ViSiAnnoT window.

The "Background color (signal plot)" spin boxes specify the background color of ViSiAnnoT plots.

The "Annotations directory" line edit specifies the directory where to save the annotations (both events and image extraction). **Make sure to change this directory when switching to another recording**.

The "from cursor durations" spin boxes table specifies the list of temporal range durations for defining a new temporal range beginning at the current temporal cursor (see section :ref:`sec-fast-nav`).

.. _customization:

Customization
=============

It is possible to call a function to automatically update the configuration before launching the GUIs::

    $ python3 -m visiannot -c path/to/config.ini -n -u visiannot.configuration.update.update_data_and_annotations_directory

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
                |__ Subject01_2021-01-01T00-00-00_Label1.txt
                |__ Subject01_2021-01-01T00-00-00_Label2.txt
        |__ Subject02
            |__ Subject02_2021-01-03T01-00-00
                |__ Subject02_2021-01-03T01-00-00_Label1.txt
                |__ Subject02_2021-01-03T01-00-00_Label2.txt

When we change subject and/or recording, we need to update the following fields in the configuration file (see :ref:`configuration`):

* First field of each video configuration (directory where to find video files),
* First field of each signal configuration (directory where to find signal files),
* Field ``annot_dir`` in the section ``General``.

Thanks to the option ``-u``, it is possible to automate this process of configuration update. When running the command above, the function :func:`.update_data_and_annotations_directory` is called before launching the GUIs. It runs the following steps:

* Load the configuration file as a dictionary,
* Open a dialog window for selecting a recording folder (e.g. "*DATA/Subject02/Subject02_2021-01-03T01-00-00*"),
* Update first field of each video configuration in the configuration dictionary with the selected directory,
* Update first field of each signal configuration in the configuration dictionary with the selected directory,
* Get the annotation directory defined as ``annotDirBase/patID/recName``, where ``annotDirBase`` is the initial value of the annotation directory in the configuration file, ``recName`` is the basename of the selected directory (e.g. "Subject02_2021-01-03T01-00-00") and ``patID`` is the patient ID (e.g. "Subject02"),
* Update the field ``annot_dir`` in the section ``General`` of the configuration dictionary with the new annotation directory.

In order to have the dialog window to open at particular location at launch, it is possible to add the key ``data_dir_base`` in the section ``General`` of the configuration file.

**NB**: only the configuration dictionary is updated in the function, the configuration file remains unchanged, implying that it is not needed to reset the value of ``annot_dir`` in the configuration file after each launch.
