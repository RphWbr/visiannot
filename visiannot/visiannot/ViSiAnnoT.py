# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.ViSiAnnoT`
"""


from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
from threading import Thread
from cv2 import imwrite
import os
from time import time, sleep
from shutil import rmtree
from datetime import datetime, timedelta
from math import ceil
from pytz import timezone
from collections import OrderedDict
from ..tools import ToolsPyQt
from ..tools import ToolsPyqtgraph
from ..tools import ToolsDateTime
from ..tools import ToolsData
from ..tools import ToolsImage
from ..tools import ToolsAudio
from .components.Signal import Signal
from .components.MenuBar import MenuBar


class ViSiAnnoT():
    def __init__(
        self,
        video_dict,
        signal_dict,
        annotevent_dict={},
        annotimage_list=[],
        threshold_dict={},
        interval_dict={},
        y_range_dict={},
        poswid_dict={},
        layout_mode=1,
        trunc_duration=(0, 0),
        flag_long_rec=False,
        from_cursor_list=[],
        zoom_factor=2,
        nb_ticks=10,
        annot_dir_base="Annotations",
        down_freq=500,
        flag_pause_status=False,
        max_points=5000,
        time_zone="Europe/Paris",
        flag_infinite_loop=True,
        bg_color=(244, 244, 244),
        bg_color_plot=(255, 255, 255),
        font_name="Times",
        font_size=12,
        font_size_title=16,
        font_color=(0, 0, 0),
        ticks_color=(93, 91, 89),
        ticks_size=12,
        ticks_offset=5,
        nb_table_annot=5,
        height_widget_signal=150
    ):
        """
        Class defining the visualization and annotation GUI for a set of
        synchronized video(s) and signal(s).

        The constructor takes as arguments dictionaries with the path to the
        video files and signal files. It calls the method
        :meth:`.setAllData` in order to load data and store them in
        attributes.

        For a given video file, data are loaded in an instance of
        cv2.VideoCapture. The set of video data is stored in
        :attr:`.video_data_dict`. The set of widgets for plotting
        video is stored in :attr:`.wid_vid_dict`. The set of current
        video frames is stored in :attr:`.im_dict`. For plotting, the
        video frames are converted to instances of pyqtgraph.ImageItem which
        are stored in :attr:`.img_vid_dict`.

        For a given signal file, data are loaded in an instance of
        :class:`.Signal`. The supported formats are txt, mat, h5 and wav. The
        set of :class:`.Signal` instances is stored in
        :attr:`.sig_list_list`. The set of widgets for plotting
        signals is stored in :attr:`.wid_data_list`. A temporal
        cursor (instance of pyqtgraph.InfiniteLine) is plotted on each signal
        widget and is synchronized with the video playback. The set of temporal
        cursors is stored in :attr:`.current_cursor_list`.

        The reference frequency :attr:`.ViSiAnnoT.fps` is defined as the video
        frequency. If there is no video to display, :attr:`.ViSiAnnoT.fps` is
        defined as the frequency of the first signal to plot. The playback
        speed (both video and signal temporal cursor) is at the reference
        frequency.

        The video display is initialized by the method
        :meth:`.initVideoPlot`. The signal display is initialized by
        the method :meth:`.initSignalPlot`.

        The temporal range is defined by :attr:`.first_frame` and
        :attr:`.last_frame` (sampled at :attr:`.ViSiAnnoT.fps`).
        The signal widgets display the signal between those bounds. So when
        zooming in/out, the temporal range is modified and then the display is
        updated with the method :meth:`.updateSignalPlot`.

        The playback is managed with two separate threads:

        - Reading next video frame - an instance of threading.Thread with the
          method :meth:`.updateVideoFrame` as target,
        - Updating plot - an instance of QtCore.QTimer connected to the method
          :meth:`.updatePlot`.

        The current position in the video file (i.e. the current position of
        the temporal cursor) is :attr:`.frame_id` (sampled at
        :attr:`.ViSiAnnoT.fps`).

        :param video_dict: video configuration, each item corresponds to one
            camera. Key is the camera ID (string). Value is a configuration
            list with 4 elements:

            - (*str*) Path to the video file,
            - (*str*) Delimiter to get beginning datetime in the video file
              name,
            - (*int*) Position of the beginning datetime in the video file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the video file name
              (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``).
        :type video_dict: dict
        :param signal_dict: signal configuration, each item corresponds to one
            signal widget. Key is the widget ID (Y axis label, string). Value
            is a nested list of signal configurations. Each element of the
            nested list corresponds to one signal plot and is a configuration
            list of 7 elements:

            - (*str*) Path to the signal file, data must be stored in a 1D
              array if regularly sampled, otherwise in a 2D array (where first
              column is the timestamp in milliseconds and the second column the
              signal value)
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int* or *float* or *str*) Signal frequency, set it to ``0`` if
              signal non regularly sampled, set it to ``-1`` if same frequency
              as :attr:`.ViSiAnnoT.fps`, it may be a string with the path to
              the frequency attribute in a .h5 file,
            - (*str*) Delimiter to get beginning datetime in the signal file
              name,
            - (*int*) Position of the beginning datetime in the signal file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the signal file name
              (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
            - (*dict*) Plot style, see
              https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html
              for details, set it to ``None`` for default.

            Here is an example::

                {
                "sig_1": [
                    [
                        "folder1/file1.txt", "", 50, '_', 1,
                        "%Y-%m-%dT%H-%M-%S", None
                    ]
                ],
                "sig_2": [
                    [
                        "folder1/file2.h5", "key2", 0, '_', 0, "posix",
                        {'pen': {'color': 'm', 'width': 1}
                    ],
                    ["folder3/file3.mat", "key3", -1, '_', 0, "posix", None]
                ]
                }

            In case of audio signal to plot, the configuration list is slightly
            different. The second element (key to access data) is a string to
            specify which channel to plot. It must contain ``"left"`` or
            ``"right"``, whatever the letter capitalization is. Otherwise, by
            default the left channel is plotted. Moreover, the frequency is
            directly retrieved from the wav file, so the third element of the
            configuration list (signal frequency) is ignored.

            Here is an example for audio::

                {
                "Audio L": [
                    [
                        "path/to/audio.wav", "Left channel", 0, '_', 1,
                        "%Y-%m-%dT%H-%M-%S", None
                    ]
                ],
                "Audio R": [
                    [
                        "path/to/audio.wav", "Right channel", 0, '_', 1,
                        "%Y-%m-%dT%H-%M-%S", None
                    ]
                ]
                }
        :type signal_dict: dict
        :param annotevent_dict: events annotation configuration.
            Key is the label (string). Value is the associated color (RGBA).
        :type annotevent_dict: dict
        :param annotimage_list: labels for image extraction
        :type annotimage_list: list
        :param threshold_dict: threshold configuration. Each item corresponds
            to a signal widget on which to plot threshold(s). The key must be
            the same as in ``signal_dict``. Value is a list of configuration
            lists. This is a nested list because there can be several
            thresholds plotted in the same widget. A configuration list has 2
            elements:

            - (*int* or *float*) Threshold value on Y axis,
            - (*tuple* or *list* or *str*) Plot color in (RGB) format or HEX
              color string.
        :type threshold_dict: dict
        :param interval_dict: interval configuration. Each item corresponds to
            a signal widget on which to plot intervals. The key must be the
            same as in ``signal_dict``. Value is a nested list of interval
            configurations. Each element of the nested list corresponds to one
            type of interval to be plotted on the same signal widget and is a
            configuration list of 7 elements:

            - (*str*) Path to the interval file, data can be stored as a 2D
              array (where each line has 2 elements: start and stop frames) or
              a 1D array (time series of 0 and 1),
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int*) Signal frequency, set it to ``-1`` if same frequency as
              :attr:`.ViSiAnnoT.fps`, it may be a string with the path to the
              frequency attribute in a .h5 file,
            - (*str*) Delimiter to get beginning datetime in the interval file
              name,
            - (*int*) Position of the beginning datetime in the interval file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the interval file
              name (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
            - (*tuple* or *list*) Plot color (RGBA).
        :type interval_dict: dict
        :param y_range_dict: visible Y range for signal widgets, each item
            corresponds to a signal widget. The key must be the same as in
            ``signal_dict``. Value is a list/tuple of length 2 with the min and
            max values to display on the Y axis. The signal widgets that are
            not specified in this dictionary have auto-range enabled for Y
            axis.
        :type y_range_dict: dict
        :param poswid_dict: custom position of the widgets in the window to use
            the positions defined by the layout mode (see input
            ``layout_mode``). Value is a tuple of length 2 ``(row, col)``
            or 4 ``(row, col, rowspan, colspan)``. Key identifies the widget:

            - ``"logo"``
            - ``"select_trunc"``
            - ``"select_manual"``
            - ``"select_from_cursor"``
            - ``"annot_event"``
            - ``"annot_image"``
            - ``"visi"``
            - ``"zoomin"``
            - ``"zoomout"``
            - ``"progress"``
        :type poswid_dict: dict
        :param layout_mode: layout mode of the window for positioning the
            widgets, one of the following:

            - ``1`` (focus on video, works better with a big screen),
            - ``2`` (focus on signal, suitable for a laptop screen),
            - ``3`` (compact display with some features disabled).
        :type layout_mode: int
        :param trunc_duration: (tool for fast navigation) duration
            ``(min, sec)`` to be used for splitting video/file in the combo box
            of temporal range selection. For example, for a video of 30
            minutes, ``trunc_duration=(10, 0)`` will provide 3 temporal ranges
            in the combo box: from 0 to 10 minutes, from 10 to 20 minutes and
            from 20 to 30 minutes.
        :type trunc_duration: list
        :param flag_long_rec: specify if :class:`.ViSiAnnoT` is launched in the
            context of :class:`.ViSiAnnoTLongRec` (long recording)
        :type flag_long_rec: bool
        :param from_cursor_list: (tool for fast navigation) list of durations
            that are available in the combo box to select a temporal range
            duration in order to display a new temporal range that will begin
            at the current position of the temporal cursor. Each element is a
            tuple of length 2 ``(min, sec)``. An example:
            ``[[0,30],[1,0],[2,0],[3,0],[4,0],[5,0]]``.
        :type from_cursor_list: list
        :param zoom_factor: zoom factor
        :type zoom_factor: int
        :param nb_ticks: number of temporal ticks on the X axis of the signals
            widgets
        :type nb_ticks: int
        :param annot_dir_base: base directory where to save annotations, a
            sub-directory is automatically created for the recording
        :type annot_dir_base: str
        :param down_freq: maximum signal frequency to plot, if a signal has a
            frequency strictly higher than ``down_freq``, then the signal is
            downsampled to ``down_freq``
        :type down_freq: int
        :param flag_pause_status: specify if the video is paused when launching
            :class:`.ViSiAnnoT`
        :type flag_pause_status: bool
        :param max_points: maximum number of points to plot for the signals
        :type max_points: int
        :param time_zone: time zone (compliant package pytz)
        :type time_zone: str
        :param flag_infinite_loop: specify if an infinite loop is set after
            creating the window. Set it to ``False`` if several
            :class:`.ViSiAnnoT` windows must be displayed simultaneousely, do
            not forget to store each instance of :class:`.ViSiAnnoT` in a
            variable and to set manually the infinite loop with
            :func:`graphicsoverlayer.ToolsPyQt.infiniteLoopDisplay`
        :type flag_infinite_loop: bool
        :param bg_color: backgroud color of the GUI, RGB or HEX string
        :type bg_color: tuple or str
        :param bg_color_plot: background color of the signal plots, RGB or HEX
            string
        :type bg_color_plot: tuple or str
        :param font_name: font used for the text in the GUI (must be available
            in PyQt5)
        :type font_name: str
        :param font_size: font size of the text in the GUI
        :type font_size: int
        :param font_size_title: font size of the titles in the GUI (progress
            bar and video widgets)
        :type font_size_title: int
        :param font_color: font color of the text in the GUI, RGB
        :type font_color: tuple
        :param ticks_color: color of the ticks in the signal plots, RGB or HEX
            string
        :type ticks_color: tuple or str
        :param ticks_size: size of the ticks values in the signal plots
        :type ticks_size: int
        :param ticks_offset: offset between the ticks and associated values in
            the signal plots
        :type ticks_offset: int
        :param nb_table_annot: maximum number of labels in a row in the
            widgets for event annotation and image annotation
        :type nb_table_annot: int
        :param height_widget_signal: minimum height in pixel of the signal
            widgets
        :type height_widget_signal: int
        """

        # check input dictionaries are empty
        if not any(video_dict) and not any(signal_dict):
            raise Exception("Input dictionaries are empty")

        # ******************************************************************* #
        # *********************** miscellaneous ***************************** #
        # ******************************************************************* #
        #: (*int*) Number of temporal ticks on the X axis of the
        #: signals plots
        self.nb_ticks = nb_ticks

        #: (*str*) Time zone (as in package pytz)
        self.time_zone = time_zone

        #: (*int*) Maximum signal frequency to plot
        self.down_freq = down_freq

        #: (*int*) Maximum number of points to plot for the signals
        self.max_points = max_points

        #: (*list*) Default plot styles for signals on a single widget
        #: (length 10)
        self.plot_style_list = [
            {'pen': {'color': 'b', 'width': 1}},
            {'pen': {'color': 'r', 'width': 1}},
            {'pen': {'color': 'g', 'width': 1}},
            {'pen': {'color': 'm', 'width': 1}},
            {'pen': {'color': 'c', 'width': 1}},
            {'pen': {'color': 'y', 'width': 1}},
            {'pen': {'color': 'k', 'width': 1}},
            {'pen': {'color': '#FFCCFF', 'width': 1}},
            {'pen': {'color': '#00CCCC', 'width': 1}},
            {'pen': {'color': '#4C9900', 'width': 1}}
        ]

        #: (*list*) Data types (string) for signal widget
        #:
        #: It is the list of keys of ``signal_dict``
        #: (positional argument of the constructor of :class:`.ViSiAnnoT`),
        #:
        #: It is used for the Y axis label of the signal widgets
        self.sig_labels = list(signal_dict.keys())



        # ******************************************************************* #
        # ************************ long recordings ************************** #
        # ******************************************************************* #
        #: (*bool*) Specify if :class:`.ViSiAnnoT` is launched in the context
        #: of :class:`.ViSiAnnoTLongRec`
        self.flag_long_rec = flag_long_rec

        #: (*int*) ID of the current video/signal file in case of long
        #: recordings
        #:
        #: If :attr:`.ViSiAnnoT.flag_long_rec` is ``False``, then
        #: :attr:`.ViSiAnnoT.rec_id` is always equal to 0.
        self.rec_id = 0

        #: (*int*) Number of files in case of long recordings
        #:
        #: If ``self.flag_long_rec`` is false, then ``self.rec_nb`` is set to
        #: 1.
        self.rec_nb = 1


        # ******************************************************************* #
        # *************************** data ********************************** #
        # ******************************************************************* #

        # initialize attributes that are set in the method setAllData

        #: (*dict*) Key is the camera ID, value is an instance of
        #: cv2.VideoCapture containing the video data
        #:
        #: Same keys as ``video_dict``, positional argument of the constructor
        #: of :class:`.ViSiAnnoT`.
        self.video_data_dict = OrderedDict()

        # only for documentation
        #: (*list*) Each element corresponds to a signal widget and is a list
        #: of instances of :class:`.Signal` to plot on the corresponding widget
        self.sig_list_list = None

        #: (*dict*) Intervals to plot on signals, each item corresponds to one
        #: signal widget
        #:
        #: Key is the data type of the signal widget on which to plot (same as
        #: in positional argument ``signal_dict`` of the constructor of
        #: :class:`.ViSiAnnoT`)
        #:
        #: Value is a list of lists, so that several intervals files can be
        #: plotted on the same signal widget. Each sub-list has 3 elements:
        #:
        #:  - (*numpy array*) Intervals data, shape :math:`(n_{detection}, 2)`
        #:  - (*float*) Frequency (``0`` if timestamps, ``-1`` if same as
        #:    signal)
        #:  - (*tuple*) Plot color (RGBA)
        self.interval_dict = {}

        # for documentation only
        #: (*int*) Frequency of the video (or the first signal if there is no
        #: video), it is the reference frequency
        self.fps = None

        # for documentation only
        #: (*int*) Number of frames in the video (or the first signal if there
        #: is no video)
        self.nframes = None

        # for documentation only
        #: (*datetime.datetime*) Beginning datetime of the video (or the first
        #: signal if there is no video)
        self.beginning_datetime = None

        # set data
        self.setAllData(video_dict, signal_dict, interval_dict)

        #: (*dict*) Thresholds to plot on signals widgets
        #:
        #: For a given signal, key must be the corresponding element in
        #: :attr:`.ViSiAnnoT.sig_labels`
        #:
        #: Value is a list of length 2:
        #:
        #: - integer/float with the value of the threshold (on Y axis)
        #: - tuple with the color to plot (RGB), it can also be a
        #:   string with HEX color
        self.threshold_dict = threshold_dict


        # ******************************************************************* #
        # ******************** decorative images **************************** #
        # ******************************************************************* #
        dir_path = ToolsData.getWorkingDirectory(__file__)

        im_deco_dict = {}
        for im_name in ["zoomin", "zoomout", "visibility"]:
            im_path = "%s/Images/%s.jpg" % (dir_path, im_name)
            im_deco_dict[im_name] = ToolsImage.readImage(im_path)


        # ******************************************************************* #
        # ***************** annotation files management ********************* #
        # ******************************************************************* #

        # check if not long recording
        if not self.flag_long_rec:
            # check if any video
            if any(video_dict):
                #: (*str*) Base name of the annotation files
                #:
                #: Label and annotation type is added when loading/saving
                #: annotation files)
                self.annot_file_base = os.path.splitext(
                    os.path.basename(list(video_dict.values())[0][0])
                )[0]

            else:
                # get base name of annotation files
                self.annot_file_base = os.path.splitext(
                    os.path.basename(list(signal_dict.values())[0][0][0])
                )[0]

        #: (*str*) Directory where the annotations are saved
        #:
        #: A sub-directory is automatically created: %s_annotations, where %s
        #: is the name of the first video file (or signal file if no video).
        self.annot_dir = "%s/%s_annotations" % (
            annot_dir_base, self.annot_file_base
        )


        # ******************************************************************* #
        # ********************** event annotation *************************** #
        # ******************************************************************* #

        #: (*str*) Label automatically created for getting duration of video
        #: files (or first signal if no video)
        #:
        #: It cannot be used for manual annotation, so it is ignored if
        #: specified by the user in the keyword argument ``annotevent_dict`` of
        #: :class:`.ViSiAnnoT` constructor.
        self.annotevent_protected_label = "DURATION"

        # check if protected label in list of labels
        if self.annotevent_protected_label in annotevent_dict.keys():
            del annotevent_dict[self.annotevent_protected_label]
            print(
                "Label %s for events annotation is protected and cannot be\
                used for manual annotation, so it is ignored" %
                self.annotevent_protected_label
            )

        #: (*list*) Labels of the event annotation (string)
        self.annotevent_label_list = list(annotevent_dict.keys())

        #: (*list*) Colors of the event annotation labels
        #:
        #: each element is a list of length 4 with the RGBA color, or length 3
        #: with the RGB color (in this case transparency A is set to 100)
        self.annotevent_color_list = list(annotevent_dict.values())

        # add transparency for color if needed
        for annot_color in self.annotevent_color_list:
            if isinstance(annot_color, list) and len(annot_color) == 3:
                annot_color.append(80)

        #: (*numpy array*) Array with unsaved annotated events
        #:
        #: Shape :math:`(n_{annot}, 2, 2)`, where :math:`n_{annot}` is the
        #: length of :attr:`.ViSiAnnoT.annotevent_label_list`.
        #: For a given label with index ``n`` in
        #: :attr:`.ViSiAnnoT.annotevent_label_list`, the sub-array
        #: ``self.annotevent_array[n]`` is organized as follows:
        #:
        #: =====================  =================================================
        #: start datetime string  start frame index in the format "rec-id_frame-id"
        #: end datetime string    end frame index in the format "rec-id_frame-id"
        #: =====================  =================================================
        self.annotevent_array = np.zeros(
            (len(self.annotevent_label_list), 2, 2), dtype=object
        )

        #: (*dict*) Event annotations descriptions to be displayed
        #:
        #: Key is the index of a label in
        #: :attr:`.ViSiAnnoT.annotevent_label_list`. Value is a dictionary:
        #:
        #:      - Key is an integer with the annotation ID (index in the
        #:        annotation file)
        #:      - Value is a list of instances of pyqtgraph.TextItem with the
        #:        description, same length and order as
        #:        :attr:`.ViSiAnnoT.wid_data_list`, so that one element
        #:        corresponds to one signal widget
        self.annotevent_description_dict = {}

        #: (*list*) Way of storing event annotations
        #:
        #: Two elements:
        #:
        #: - ``"datetime"``: datetime string in the format
        #:   %Y-%M-%DT%h-%m-%s.%ms
        #: - ``"frame"``: rec-id_frame-id
        self.annotevent_type_list = ["datetime", "frame"]

        if len(self.annotevent_label_list) > 0:
            #: (*list*) Files names of event annotation
            #:
            #: Same length as :attr:`.ViSiAnnoT.annotevent_type_list`, there is
            #: one file for each annotation type.
            self.annotevent_path_list = self.annotEventGetPathList(
                self.annotevent_label_list[0]
            )

            # create directory if necessary
            if not os.path.isdir(self.annot_dir):
                os.makedirs(self.annot_dir)

            # create annotation file with duration of video files
            # (or first signal if no video)
            output_path_0 = "%s/%s_%s-datetime.txt" % \
                (self.annot_dir, self.annot_file_base,
                    self.annotevent_protected_label)
            output_path_1 = "%s/%s_%s-frame.txt" % \
                (self.annot_dir, self.annot_file_base,
                    self.annotevent_protected_label)

            if not os.path.isfile(output_path_0):
                if self.flag_long_rec:
                    with open(output_path_0, 'w') as f:
                        for beg_datetime, duration in zip(
                            self.rec_beginning_datetime_list,
                            self.rec_duration_list
                        ):
                            end_datetime = beg_datetime + timedelta(
                                seconds=duration
                            )

                            beg_string = ToolsDateTime.convertDatetimeToString(
                                beg_datetime
                            )

                            end_string = ToolsDateTime.convertDatetimeToString(
                                end_datetime
                            )

                            f.write("%s - %s\n" % (beg_string, end_string))

                    with open(output_path_1, 'w') as f:
                        for ite_file, duration in enumerate(
                            self.rec_duration_list
                        ):
                            f.write("%d_0 - %d_%d\n" % (
                                ite_file, ite_file, int(duration * self.fps)
                            ))

                else:
                    with open(output_path_0, 'w') as f:
                        end_datetime = self.beginning_datetime + timedelta(
                            seconds=self.nframes / self.fps
                        )

                        beg_string = ToolsDateTime.convertDatetimeToString(
                            self.beginning_datetime
                        )

                        end_string = ToolsDateTime.convertDatetimeToString(
                            end_datetime
                        )

                        f.write("%s - %s\n" % (beg_string, end_string))

                    with open(output_path_1, 'w') as f:
                        f.write("0_0 - 0_%d\n" % self.nframes)

        else:
            self.annotevent_path_list = []

        #: (*int*) Index of the currently selected label, with respect to the
        #: list :attr:`.ViSiAnnoT.annotevent_type_list`
        self.annotevent_current_label_id = 0


        # ******************************************************************* #
        # ********************** image annotation *************************** #
        # ******************************************************************* #

        # check type (if loaded from a configuration, then dictionary instead
        # of list)
        if isinstance(annotimage_list, dict):
            # convert to list
            annotimage_list = [k for k in annotimage_list.values()]

        #: (*list*) Image annotation labels (strings)
        self.annotimage_label_list = annotimage_list

        if len(self.annotimage_label_list) > 0:
            # create directories if necessary
            if not os.path.isdir(self.annot_dir):
                os.makedirs(self.annot_dir)

            for label in self.annotimage_label_list:
                label_dir = "%s/%s" % (self.annot_dir, label)
                if not os.path.isdir(label_dir):
                    os.mkdir(label_dir)


        # ******************************************************************* #
        # ***************************** zoom ******************************** #
        # ******************************************************************* #
        #: (*int*) Zoom factor
        self.zoom_factor = zoom_factor

        #: (*int*) Start position (frame number) for custom manual zoom (set to
        #: -1 if not defined)
        self.zoom_pos_1 = -1

        #: (*int*) End position (frame number) for custom manual zoom (set to
        #: -1 if not defined)
        self.zoom_pos_2 = -1

        #: (*list*) Instances of pyqtgraph.LinearRegionItem with all the grey
        #: regions for custom manual zoom
        self.region_zoom_list = []

        #: (*list*) Instances of pyqtgraph.TextItem with the duration of the
        #: custom manual zoom
        #:
        #: Same length and order as :attr:`.ViSiAnnoT.wid_data_list`, so that
        #: one element corresponds to one signal widget
        self.region_zoom_text_item_list = []


        # ******************************************************************* #
        # ****************************** time ******************************* #
        # ******************************************************************* #

        #: (*int*) Number of frames correpsonding to
        #: :attr:`.ViSiAnnoT.trunc_duration`
        self.nframes_trunc = ToolsDateTime.convertTimeToFrame(
            self.fps, minute=trunc_duration[0], sec=trunc_duration[1]
        )

        # check if trunc duration is above the total number of frames or
        # default => set it to 0
        if self.nframes_trunc > self.nframes or self.nframes_trunc == 0:
            self.nframes_trunc = self.nframes
            trunc_duration = (0, 0)

        #: (*list*) Duration of file split (tool for fast navigation), 2
        #: elements (int): ``(minute, second)``
        self.trunc_duration = trunc_duration

        #: (*int*) Number of splits in the file (tool for fast navigation)
        self.nb_trunc = round(self.nframes / self.nframes_trunc)

        #: (*list*) Temporal range durations intervals starting at the current
        #: position of the temporal cursor (tool for fast navigation)
        #:
        #: Each element is a list of integers with 2 elements:
        #: ``(minute, second)``.
        self.from_cursor_list = from_cursor_list

        #: (*bool*) Specify if the video is paused
        self.flag_pause_status = flag_pause_status

        #: (*int*) Index of the current frame
        self.frame_id = 0

        #: (*int*) First frame that is displayed in the signal plots
        self.first_frame = 0

        #: (*int*) Last frame that is displayed in the signal plots
        #:
        #: Actually, the last frame that is displayed is
        #: ``:attr:`.ViSiAnnoT.last_frame` - 1``, because of zero-indexation.
        self.last_frame = self.nframes_trunc

        #: (*bool*) Specify if the window is running
        self.flag_processing = True


        # ******************************************************************* #
        # *********************** layout definition ************************* #
        # ******************************************************************* #

        # define window organization if none provided
        if not any(poswid_dict):
            nb_video = len(video_dict)

            # check layout mode
            if layout_mode == 1:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 5, 1)
                poswid_dict['select_trunc'] = (0, nb_video, 1, 2)
                poswid_dict['select_manual'] = (1, nb_video, 1, 3)
                poswid_dict['select_from_cursor'] = (0, nb_video + 2)
                poswid_dict['annot_event'] = (2, nb_video, 1, 3)
                poswid_dict['annot_image'] = (3, nb_video, 1, 3)
                poswid_dict['visi'] = (4, nb_video)
                poswid_dict['zoomin'] = (4, nb_video + 1)
                poswid_dict['zoomout'] = (4, nb_video + 2)
                poswid_dict['progress'] = (5, 0, 1, nb_video + 3)


            elif layout_mode == 2:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 4, 1)
                poswid_dict['select_trunc'] = (1, nb_video, 1, 2)
                poswid_dict['select_manual'] = (2, nb_video, 1, 3)
                poswid_dict['select_from_cursor'] = (1, nb_video + 2)
                poswid_dict['annot_event'] = (0, nb_video + 3, 4, 1)
                poswid_dict['annot_image'] = (0, nb_video, 1, 3)
                poswid_dict['visi'] = (3, nb_video)
                poswid_dict['zoomin'] = (3, nb_video + 1)
                poswid_dict['zoomout'] = (3, nb_video + 2)
                poswid_dict['progress'] = (4, 0, 1, nb_video + 4)


            elif layout_mode == 3:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 2, 1)
                poswid_dict['annot_event'] = (0, nb_video, 2, 1)
                poswid_dict['annot_image'] = (0, nb_video + 1, 1, 3)
                poswid_dict['visi'] = (1, nb_video + 1)
                poswid_dict['zoomin'] = (1, nb_video + 2)
                poswid_dict['zoomout'] = (1, nb_video + 3)
                poswid_dict['progress'] = (2, 0, 1, nb_video + 4)


            else:
                raise Exception("No layout configuration given - got mode %d, must be 1, 2 or 3" % layout_mode)


        # ******************************************************************* #
        # ********************* display initialization ********************** #
        # ******************************************************************* #

        # ************** create GUI application and set font **************** #
        #: (*QtWidgets.QApplication*) GUI initializer
        self.app = ToolsPyqtgraph.initializeDisplayAndBgColor(
            color=bg_color_plot
        )

        # set style sheet
        ToolsPyQt.setStyleSheet(
            self.app, font_name, font_size, font_color,
            ["QGroupBox", "QComboBox", "QPushButton", "QRadioButton", "QLabel",
             "QCheckBox", "QDateTimeEdit", "QTimeEdit"]
        )

        # get default font for titles in pyqtgraph
        font_default_title = {
            "color": font_color, "size": "%dpt" % font_size_title
        }

        font_default_axis_label = {
            "color": font_color, "font-size": "%dpt" % font_size_title
        }


        # ****************** create window and layout *********************** #
        #: (*QtWidgets.QWidget*) Window container
        self.win = None

        #: (*QtWidgets.QGridLayout*) layout filling the window
        self.lay = None

        # create window
        self.win, self.lay = ToolsPyQt.createWindow(
            title="ViSiAnnoT", bg_color=bg_color
        )

        # listen to the callback method (keyboard interaction)
        self.win.keyPressEvent = self.keyPress
        self.win.keyReleaseEvent = self.keyRelease


        # ************************** menu *********************************** #
        #: (:class:`.MenuBar`) Menu bar item, instance of a sub-class of
        #: **QtWidgets.QMenuBar**, by default it is hidden, see
        #: :meth:`.keyRelease` for the keyword shortcut for displaying it
        self.menu_bar = MenuBar(self.win, self.lay)


        # ********************** progress bar ******************************* #
        if "progress" in poswid_dict.keys():
            #: (:class:`graphicsoverlayer.ToolsPyqtgraph.ProgressWidget`)
            #: Widget containing the progress bar
            self.wid_progress = None

            self.createWidgetProgress(
                poswid_dict['progress'], title="",
                title_style=font_default_title, ticks_color=ticks_color,
                ticks_size=ticks_size, ticks_offset=ticks_offset
            )

            # listen to the callbakc method
            self.wid_progress.getProgressPlot().sigPlotChanged.connect(
                self.mouseDraggedProgress
            )

        else:
            raise Exception("No widget position given for the progress bar => add key 'progress' to positional argument poswid_dict")


        # ************************ video widgets **************************** #
        #: (*dict*) Video widgets
        #:
        #: Key is the camera ID (string). Value is the widget
        #: (pyqtgraph.PlotWidget) where the corresponding video is displayed.
        #:
        #: Same keys as the position argument
        #: ``video_dict`` of the constructor of :class:`.ViSiAnnoT`
        self.wid_vid_dict = {}

        #: (*dict*) Image items of the current frame
        #:
        #: Key is the camera ID (string). Value is the image item
        #: (pyqtgraph.ImageItem) displayed for the corresponding video
        #:
        #: Same keys as the position argument
        #: ``video_dict`` of the constructor of :class:`.ViSiAnnoT`
        self.img_vid_dict = {}

        #: (*dict*) Image arrays of the current frame
        #:
        #: Key is the camera ID (string). Value is a numpy array of shape
        #: :math:`(width, height, 3)` containing the RGB image of the current
        #: frame for the corresponding video.
        #:
        #: Same keys as the position argument
        #: ``video_dict`` of the constructor of :class:`.ViSiAnnoT`
        self.im_dict = {}

        #: (*dict*) Files names of the video
        #:
        #: Key is the camera ID (string). Value is the corresponding video
        #: file name (strin).
        #:
        #: Same keys as the position argument
        #: ``video_dict`` of the constructor of :class:`.ViSiAnnoT`
        self.vid_file_name_dict = {}

        # create video widgets and initialize video plots
        # (it sets the attributes self.wid_vid_dict, self.img_vid_dict,
        # self.im_dict and self.vid_file_name_dict)
        self.initVideoPlot(
            video_dict, poswid_dict, font_title=font_default_title
        )


        # *********************** signal widgets **************************** #
        #: (*list*) Widgets for signal plot, each element is an instance of
        #: :class:`.SignalWidget`
        #:
        #: Same length as :attr:`.sig_labels`.
        self.wid_data_list = []

        #: (*list*) Plot items of the signals
        #:
        #: Each element corresponds to a signal widget in
        #: :attr:`.wid_data_list` (same indexing) and is a list of
        #: plot items (pyqtgraph.PlotDataItem)
        self.data_plot_list_list = []

        #: (*list*) Temporal cursor item for each signal
        #:
        #: Each element is an instance of pyqtgraph.InfiniteLine.
        self.current_cursor_list = []

        #: (*dict*) Lists of region items for temporal intervals
        #:
        #: Key is the ID of the widget on which temporal intervals are plotted
        #: (must be in :attr:`.sig_labels`). Value is a list of
        #: instances of pyqtgraph.LinearRegionItem displayed on the
        #: corresponding widget.
        self.region_interval_dict = {}

        # create signal widgets and initialize signal plots
        # (it sets the attributes self.wid_data_list,
        # self.data_plot_list_list, self.current_cursor_list and
        # self.region_interval_dict)
        self.initSignalPlot(
            poswid_dict['progress'],
            font_axis_label=font_default_axis_label,
            ticks_color=ticks_color,
            ticks_size=ticks_size,
            ticks_offset=2,
            y_range_dict=y_range_dict,
            height_widget_signal=height_widget_signal
        )

        # listen to the callback methods
        for wid, current_cursor in zip(
            self.wid_data_list, self.current_cursor_list
        ):
            # mouse click on the plot => move temporal cursor
            wid.scene().sigMouseClicked.connect(self.signalMouseClicked)

            # temporal cursor dragging
            current_cursor.sigDragged.connect(self.currentCursorDragged)


        # *********************** trunc widget ****************************** #
        if self.trunc_duration[0] != 0 or self.trunc_duration[1] != 0:
            if "select_trunc" in poswid_dict.keys():
                #: (:class:`graphicsoverlayer.ToolsPyQt.ComboBox`) Combo box
                #: for selecting a truncated temporal range (tool for fast
                #: navigation)
                _, _, self.combo_trunc = ToolsPyQt.addComboBox(
                    self.lay, poswid_dict['select_trunc'],
                    [""] + self.getTruncIntervals(),
                    box_title="%dmin %ds temporal range" %
                    tuple(self.trunc_duration)
                )

                self.combo_trunc.setCurrentIndex(1)

                # listen to the callback method
                self.combo_trunc.currentIndexChanged.connect(
                    self.callComboTrunc
                )


        # ************ widget for custom temporal re-scaling **************** #
        if "select_manual" in poswid_dict.keys():
            #: (*QtWidgets.QDateTimeEdit*) Editor of starting datetime of
            #: custom temporal interval
            self.edit_start = QtWidgets.QDateTimeEdit(QtCore.QDateTime(
                QtCore.QDate(
                    self.beginning_datetime.year,
                    self.beginning_datetime.month,
                    self.beginning_datetime.day
                ),
                QtCore.QTime(
                    self.beginning_datetime.hour,
                    self.beginning_datetime.minute,
                    self.beginning_datetime.second
                )
            ))

            # only for documentation
            #: (*QtWidgets.QPushButton*) Push button for defining the starting
            #: datetime of custom temporal interval as the current frame
            self.current_push = None

            #: (*QtWidgets.QTimeEdit*) Editor of the duration of custom
            #: temporal interval
            self.edit_duration = QtWidgets.QTimeEdit()

            # only for documentation
            #: (*QtWidgets.QPushButton*) Push button for validating custom
            #: temporal interval
            self.time_edit_push = None

            # create widget
            self.createWidgetTimeEdit(poswid_dict['select_manual'])

            # listen to the callback methods
            self.current_push.clicked.connect(self.timeEditCurrent)
            self.time_edit_push.clicked.connect(self.timeEditOk)


        # *************** widget for temporal re-scaling ******************** #
        if len(self.wid_data_list) > 0 and \
            "select_from_cursor" in poswid_dict.keys() and \
                len(self.from_cursor_list) > 0:
            #: (:class:`graphicsoverlayer.ToolsPyQt.ComboBox`) Combo box for
            #: selecting a temporal range starting from the current frame (tool
            #: for fast navigation)
            _, _, self.combo_from_cursor = ToolsPyQt.addComboBox(
                self.lay, poswid_dict['select_from_cursor'],
                [""] + ['{:>02}:{:>02}'.format(from_cursor[0], from_cursor[1])
                        for from_cursor in self.from_cursor_list],
                box_title="Temporal range duration"
            )

            # listen to the callback method
            self.combo_from_cursor.currentIndexChanged.connect(
                self.callComboFromCursor
            )


        # *********************** zoom widgets ****************************** #
        if len(self.wid_data_list) > 0 and "visi" in poswid_dict.keys():
            #: (*pyqtgraph.PlotWidget*) Widget with the visibility image
            #:
            #: Clicking on it sets the temporal range to the fullest
            self.wid_visi = ToolsPyqtgraph.createWidgetLogo(
                self.lay, poswid_dict['visi'], im_deco_dict["visibility"],
                box_size=50
            )

            # listen to the callback method
            self.wid_visi.scene().sigMouseClicked.connect(self.visiAll)


        if len(self.wid_data_list) > 0 and "zoomin" in poswid_dict.keys():
            #: (*pyqtgraph.PlotWidget*) Widget containing the zoomin image
            self.wid_zoomin = ToolsPyqtgraph.createWidgetLogo(
                self.lay, poswid_dict['zoomin'], im_deco_dict["zoomin"],
                box_size=50
            )

            # listen to the callback method
            self.wid_zoomin.scene().sigMouseClicked.connect(self.zoomIn)


        if len(self.wid_data_list) > 0 and "zoomout" in poswid_dict.keys():
            #: (*pyqtgraph.PlotWidget*) Widget containing the zoomout image
            self.wid_zoomout = ToolsPyqtgraph.createWidgetLogo(
                self.lay, poswid_dict['zoomout'], im_deco_dict["zoomout"],
                box_size=50
            )

            # listen to the callback method
            self.wid_zoomout.scene().sigMouseClicked.connect(self.zoomOut)


        # ******************* event annotation widget *********************** #
        if len(self.annotevent_label_list) > 0:
            if "annot_event" in poswid_dict.keys():
                # for documentation only
                #: (*QtWidgets.QButtonGroup*) Set of the radio buttons with
                #: labels of events annotation
                self.annotevent_button_group_radio_label = None

                # for documentation only
                #: (*QtWidgets.QButtonGroup*) Set of the radio buttons with
                #: display options of events annotation
                self.annotevent_button_group_radio_disp = None

                # for documentation only
                #: (*QtWidgets.QButtonGroup*) Set of the check boxes for
                #: custom display of events annotation
                self.annotevent_button_group_check_custom = None

                #: (*QtWidgets.QButtonGroup*) Set of push buttons for
                #: events annotation (Sart, Stop, Add, Delete last, Display)
                self.annotevent_button_group_push = QtWidgets.QButtonGroup()

                #: (*list*) Instances of QtWidgets.QLabel containing the text
                #: next to the push buttons grouped in
                #: :attr:`.ViSiAnnoT.annotevent_button_group_push`
                self.annotevent_button_label_list = []

                # create widget for events annotation
                self.createWidgetAnnotEvent(
                    poswid_dict['annot_event'], nb_table=nb_table_annot
                )

                #: (*dict*) Lists of region items (pyqtgraph.LinearRegionItem)
                #: for the display of event annotations
                #:
                #: Key is a label index. Value is a list of lists, each sublist
                #: corresponds to one annotation and contains
                #: :math:`n_{wid} + 1` region items, where :math:`n_{wid}` is
                #: the length of :attr:`.ViSiAnnoT.wid_data_list` (number of
                #: signal widgets), the additional region item is for the
                #: progress bar (:attr:`.ViSiAnnoT.wid_progress`).
                #:
                #: For example, for 3 signal widgets and for a given label with
                #: 2 annotations, the value of the dictionary would be::
                #:
                #:      [
                #:          [
                #:              annot1_widProgress, annot1_wid1, annot1_wid2,
                #:              annot1_wid3
                #:          ],
                #:          [
                #:              annot2_widProgress, annot2_wid1, annot2_wid2,
                #:              annot2_wid3
                #:          ]
                #:      ]
                self.region_annotation_dict = {}

                # plot annotations
                self.plotAnnotEventRegions()

                # listen to the callback methods
                self.annotevent_button_group_push.buttonClicked[int].connect(
                    self.annotEventCallPushButton
                )

                self.annotevent_button_group_radio_label.buttonClicked.connect(
                    self.annotEventCallRadio
                )

                self.annotevent_button_group_radio_disp.buttonClicked.connect(
                    self.plotAnnotEventRegions
                )

                self.annotevent_button_group_check_custom.buttonClicked.connect(
                    self.plotAnnotEventRegions
                )

            else:
                raise Exception("No widget position given for the event annotation => add key 'annot_event' to positinal argument poswid_dict")


        # ******************* image annotation widget *********************** #
        if len(self.annotimage_label_list) > 0:
            if "annot_image" in poswid_dict.keys():
                # for documentation only
                #: (*QtWidgets.QButtonGroup*) Set of radio buttons with
                #: labels of image extraction
                self.annotimage_radio_button_group = None

                # for documentation only
                #: (:class:`graphicsoverlayer.ToolsPyQt.PushButton`) Push
                #: button for saving image extraction
                self.annotimage_push_button = None

                # check if horizontal or vertical radio buttons
                if layout_mode == 3:
                    flag_horizontal = False

                else:
                    flag_horizontal = True

                # create widget
                self.createWidgetAnnotImage(
                    poswid_dict['annot_image'],
                    flag_horizontal=flag_horizontal,
                    nb_table=nb_table_annot
                )

                # listen to the callback method
                self.annotimage_push_button.clicked.connect(
                    self.annotImageCallPushButton
                )

            else:
                raise Exception("No widget position given for the image annotation => add key 'annot_image' to positinal argument poswid_dict")


        # ******************************************************************* #
        # ************** thread for getting videos images ******************* #
        # ******************************************************************* #

        if any(self.video_data_dict):
            #: (*threading.Thread*) Thread for getting video frames, connected
            #: to the method :meth:`.ViSiAnnoT.updateVideoFrame`
            self.update_frame_thread = Thread(target=self.updateVideoFrame)
            self.update_frame_thread.start()


        # ******************************************************************* #
        # ************************ plot timer ******************************* #
        # ******************************************************************* #

        #: (*QtCore.QTimer*) Thread for updating the current frame position,
        #: connected to the method :meth:`.ViSiAnnoT.updatePlot`
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)
        self.timer.start()


        # ******************************************************************* #
        # *********************** infinite loop ***************************** #
        # ******************************************************************* #

        # this does not apply in case of long recording, because there are
        # other stuff to do after calling this constructor
        if not self.flag_long_rec and flag_infinite_loop:
            ToolsPyQt.infiniteLoopDisplay(self.app)

            # close streams, delete temporary folders
            self.stopProcessing()


    # *********************************************************************** #
    # ************************ ViSiAnnoT methods **************************** #
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Miscellaneous methods
    # *********************************************************************** #


    def getTruncIntervals(self):
        """
        Gets the string associated to the truncated temporal intervals defined
        by :attr:`.ViSiAnnoT.trunc_duration` for fast navigation

        :returns: list of strings
        :rtype: list
        """

        trunc_list = []
        for ite_trunc in range(self.nb_trunc):
            string_1 = ToolsDateTime.convertFrameToAbsoluteTimeString(
                ite_trunc * self.nframes_trunc, self.fps,
                self.beginning_datetime
            )

            if (ite_trunc + 1) == self.nb_trunc:
                string_2 = ToolsDateTime.convertFrameToAbsoluteTimeString(
                    self.nframes, self.fps, self.beginning_datetime
                )

            else:
                string_2 = ToolsDateTime.convertFrameToAbsoluteTimeString(
                    (ite_trunc + 1) * self.nframes_trunc, self.fps,
                    self.beginning_datetime
                )

            label = "%s - %s" % (string_1, string_2)
            trunc_list.append(label)

        return trunc_list


    def setTemporalTicks(self, widget, temporal_info):
        """
        Sets the ticks of the X axis of the widget and the X axis range
        according to a temporal range

        It creates temporal labels for ticks in the format HH:MM:SS.SSS.
        The number of ticks is specified by :attr:`.ViSiAnnoT.nb_ticks`.

        :param widget: widget where to set X axis ticks and X axis range,
            it may be any sub-class of pyqtgraph.PlotWidget, such as
            :class:`graphicsoverlayer.ToolsPyqtgraph.SignalWidget` or
            :class:`graphicsoverlayer.ToolsPyqtgraph.ProgressWidget`
        :type widget: pyqtgraph.PlotWidget
        :param temporal_info: temporal range, there are two ways to specify it:

            - ``(first_frame_ms, last_frame_ms)``, the temporal range is
              expressed in milliseconds,
            - ``(first_frame, last_frame, freq)``, the temporal range is
              expressed in number of frames sampled at the frequency ``freq``
        :type temporal_info: list
        """

        start = temporal_info[0]
        stop = temporal_info[1]
        temporal_range = [start + i * (stop - start) / (self.nb_ticks - 1)
                          for i in range(self.nb_ticks - 1)] + [stop]

        # X axis range
        widget.setXRange(start, stop)

        if len(temporal_info) == 3:
            freq = temporal_info[2]

            # define temporal labels
            temporal_labels = [
                ToolsDateTime.convertFrameToAbsoluteTimeString(
                    frame_id, freq, self.beginning_datetime
                ) for frame_id in temporal_range
            ]

        else:
            # define temporal labels
            temporal_labels = [
                ToolsDateTime.convertMsecToAbsoluteTimeString(
                    msec, self.beginning_datetime
                ) for msec in temporal_range
            ]

        # set ticks
        ticks = [[(frame, label) for frame, label in
                  zip(temporal_range, temporal_labels)], []]
        axis = widget.getAxis('bottom')
        axis.setTicks(ticks)


    def getFrameIdInMs(self, frame_id):
        """
        Converts a frame number to milliseconds

        :param frame_id: frame number sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`
        :type frame_id: int

        :returns: frame number in milliseconds
        :rtype: float
        """

        return 1000 * frame_id / self.fps


    def convertMsToFrameRef(self, frame_ms):
        """
        Converts milliseconds to frame number sampled at the reference
        frequency :attr:`.ViSiAnnoT.fps`

        :param frame_ms: frame number in milliseconds
        :type frame_ms: float

        :returns: frame number sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`
        :rtype: int
        """

        return int(frame_ms * self.fps / 1000)


    def getCurrentRangeInMs(self):
        """
        Converts the current temporal range defined by
        :attr:`.ViSiAnnoT.first_frame` and :attr:`.ViSiAnnoT.last_frame` to
        milliseconds

        :returns:
            - **first_frame_ms** (*int*) -- first frame of the current temporal
              range in milliseconds
            - **last_frame_ms** (*int*) -- last frame of the current temporal
              range in milliseconds
        """

        return self.getFrameIdInMs(self.first_frame), \
            self.getFrameIdInMs(self.last_frame)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for displaying video / plotting signals and progress bar
    # *********************************************************************** #


    def initVideoPlot(self, video_dict, poswid_dict,
                      font_title={"color": "#000", "size": "12pt"}):
        """
        Creates the video widgets and initializes the video plots

        It sets the following attributes:

        - :attr:`.ViSiAnnoT.wid_vid_dict`
        - :attr:`.ViSiAnnoT.img_vid_dict`
        - :attr:`.ViSiAnnoT.im_dict`
        - :attr:`.ViSiAnnoT.vid_file_name_dict`

        Make sure the attribute :attr:`.ViSiAnnoT.lay` is created before
        calling this method.

        :param video_dict: video configuration, see positional argument
            ``video_dict`` of :class:`.ViSiAnnoT` constructor
        :type video_dict: dict
        :param poswid_dict: position of the widgets in the window, see
            positional argument ``poswid_dict`` of :class:`.ViSiAnnoT`
            constructor
        :type poswid_dict: dict
        :param font_title: font of the widget title
        :type font_title: dict
        """

        for video_id, (video_path, _, _, _) in video_dict.items():
            # check if widget position exists
            if video_id in poswid_dict.keys():
                # get file name
                file_name = os.path.splitext(os.path.basename(video_path))[0]
                self.vid_file_name_dict[video_id] = file_name

                # create widget
                self.wid_vid_dict[video_id], self.img_vid_dict[video_id] = \
                    ToolsPyqtgraph.createWidgetImage(
                        self.lay, poswid_dict[video_id],
                        title=file_name, title_style=font_title
                )

                # initialize image arrays
                self.im_dict[video_id] = self.getVideoData(
                    self.video_data_dict[video_id]
                )

                # display first frame
                self.img_vid_dict[video_id].setImage(self.im_dict[video_id])

            else:
                raise Exception("No widget position given for video %s => add key %s to positinal argument poswid_dict" % (video_id, video_id))


    def initSignalPlot(
        self, progbar_wid_pos,
        font_axis_label={"color": "#000", "font-size": "12pt"},
        ticks_color=(93, 91, 89), ticks_size=10, ticks_offset=2,
        current_cursor_style={'color': "F00", 'width': 1},
        current_cursor_dragged_style={'color': "F0F", 'width': 2},
        y_range_dict={}, height_widget_signal=150
    ):
        """
        Creates the signal widgets and initializes the signal plots

        The widgets are automatically positioned below the progress bar.

        It sets the following attributes:

        - :attr:`.ViSiAnnoT.wid_data_list`
        - :attr:`.ViSiAnnoT.data_plot_list_list`
        - :attr:`.ViSiAnnoT.current_cursor_list`
        - :attr:`.ViSiAnnoT.region_interval_dict`

        Make sure the attributes :attr:`.ViSiAnnoT.lay`,
        :attr:`.ViSiAnnoT.sig_list_list`, :attr:`.ViSiAnnoT.sig_labels`,
        :attr:`.ViSiAnnoT.threshold_dict` and :attr:`.ViSiAnnoT.interval_dict`
        are defined before calling this method.

        :param progbar_wid_pos: position of the progress bar widget, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type progbar_wid_pos: tuple of list
        :param font_axis_label: font of the Y axis label
        :type font_axis_label: dict
        :param ticks_color: ticks color (RGB)
        :type ticks_color: tuple or list
        :param ticks_size: size of the ticks text
        :type ticks_size: int
        :param ticks_offset: offset between the ticks and the text
        :type ticks_offset: int
        :param current_cursor_style: plot style of the temporal cursor
        :type current_cursor_style: dict
        :param current_cursor_dragged_style: plot style of the temporal cursor
            when dragged
        :type current_cursor_dragged_style: dict
        :param y_range_dict: visible Y range for signal widgets, see positional
            argument ``y_range_dict`` of :class:`.ViSiAnnoT` constructor
        :type y_range_dict: dict
        :param height_widget_signal: minimum height in pixels of the signal
            widgets
        :type height_widget_signal: int
        """

        # get current range in milliseconds
        first_frame_ms, last_frame_ms = self.getCurrentRangeInMs()

        # convert progress bar widget position to a list
        pos_sig = list(progbar_wid_pos)

        # loop on signals
        for ite_sig, (type_data, sig_list) in enumerate(
            zip(self.sig_labels, self.sig_list_list)
        ):
            # get position of the widget relatively to the progress bar
            pos_sig[0] += 1

            # create scroll area
            if ite_sig == 0:
                scroll_lay, _ = ToolsPyQt.addScrollArea(
                    self.lay, pos_sig, flag_ignore_wheel_event=True
                )

            # get Y range
            if type_data in y_range_dict.keys():
                y_range = y_range_dict[type_data]

            else:
                y_range = []

            # create widget
            wid = ToolsPyqtgraph.createWidgetSignal(
                self.lay, pos_sig, y_range=y_range,
                left_label=type_data, left_label_style=font_axis_label,
                ticks_color=ticks_color, ticks_size=ticks_size,
                ticks_offset=ticks_offset
            )

            # add widget to scroll area
            wid.setMinimumHeight(height_widget_signal)
            scroll_lay.addWidget(wid)

            # append widget to list of widgets
            self.wid_data_list.append(wid)

            # reconnect to keypress event callback, so that keypress events of
            # scroll are ignored
            wid.keyPressEvent = self.keyPress

            # create legend item
            if len(sig_list) > 1:
                legend = pg.LegendItem(offset=(0, 10))
                legend.setParentItem(wid.graphicsItem())

            # loop on sub-signals for the widget
            data_plot_list_tmp = []
            for sig in sig_list:
                # define temporal range for the signal
                data_in_current_range = sig.getDataInRange(
                    first_frame_ms, last_frame_ms
                )

                # plot signal in the widget
                plot = ToolsPyqtgraph.addPlotTo2DWidget(
                    wid, data_in_current_range,
                    flag_nan_void=True, plot_style=sig.getPlotStyle()
                )

                data_plot_list_tmp.append(plot)

                # add legend
                if len(sig_list) > 1 and sig.getLegendText() != "":
                    legend.addItem(plot, sig.getLegendText())

            # append list of plot list
            self.data_plot_list_list.append(data_plot_list_tmp)

            # create the infinite line for the current cursor
            current_cursor = pg.InfiniteLine(
                angle=90, movable=True, bounds=[0, last_frame_ms],
                pen=current_cursor_style, hoverPen=current_cursor_dragged_style
            )

            wid.addItem(current_cursor)
            current_cursor.setPos(0)
            self.current_cursor_list.append(current_cursor)

            # set temporal ticks and X axis range
            self.setTemporalTicks(wid, (first_frame_ms, last_frame_ms))

            # check if there are intervals to plot
            if type_data in self.interval_dict.keys():
                # loop on interval data
                self.region_interval_dict[type_data] = []
                for intervals, freq, color in self.interval_dict[type_data]:
                    # plot intervals
                    self.region_interval_dict[type_data] += \
                        ViSiAnnoT.plotIntervals(intervals, wid, freq, color)

            # check if there are thresholds to plot
            if type_data in self.threshold_dict.keys():
                for value, color in self.threshold_dict[type_data]:
                    infinite_line = pg.InfiniteLine(
                        pos=value, angle=0, pen={'color': color, 'width': 1}
                    )

                    wid.addItem(infinite_line)


    def getVideoData(self, data_video):
        """
        Gets video frame at the current frame :attr:`.frame_id`

        :param data_video: video data to read
        :type data_video: cv2.VideoCapture

        :returns: RGB image of the current frame, shape
            :math:`(width, height, 3)`
        :rtype: numpy array
        """

        # check data video
        if data_video is not None:
            # set the video stream at the current frame
            data_video.set(1, self.frame_id)

            # read image
            ret, im = data_video.read()

        else:
            ret = False

        # check if reading is successful
        if ret:
            # cv2 returns BGR => converted to RGB
            # cv2 returns image with shape (height,width,3) => transposed to
            # (width, height, 3) for display
            return ToolsImage.transformImage(im)

        else:
            # if no image read, returns black image
            return np.zeros((100, 100, 3))


    def updateVideoFrame(self):
        """
        Reads the video stream (launched in a thread)

        Called by the thread :attr:`.update_frame_thread`.

        It updates the attribute :attr:`.im_dict` with the image at
        the current frame.
        """

        # check if the process still goes on
        while self.flag_processing:
            if not self.flag_pause_status:
                # update images at the current frame
                for video_id, data_video in self.video_data_dict.items():
                    self.im_dict[video_id] = self.getVideoData(data_video)
            else:
                sleep(0.001)


    def stopProcessing(self):
        """
        Closes streams (elements of :attr:`.video_data_dict`) and
        deletes temporary signal folder

        It sets the value of :attr:`.flag_processing` to ``False`` so
        that the thread :attr:`.update_frame_thread` is stopped.
        """

        self.timer.stop()
        self.app.quit()
        self.flag_processing = False

        # check if annotation directory exists
        if os.path.isdir(self.annot_dir):
            # get list of files/folders in the annotation directory
            print("delete empty annotation folders/files if necessary")
            annot_path_list = os.listdir(self.annot_dir)

            # get file name of event annotation of protected label
            protected_name_0 = "%s_%s-datetime.txt" % (
                self.annot_file_base, self.annotevent_protected_label
            )
            protected_name_1 = "%s_%s-frame.txt" % (
                self.annot_file_base, self.annotevent_protected_label
            )

            # loop on annotation files/folders
            for annot_file_name in annot_path_list:
                # get path of file/folder
                annot_path = "%s/%s" % (self.annot_dir, annot_file_name)

                # split extension
                name, ext = os.path.splitext(annot_file_name)

                # check if directory of image annotation
                if os.path.isdir(annot_path) and \
                        annot_file_name in self.annotimage_label_list:
                    if os.listdir(annot_path) == []:
                        rmtree(annot_path)

                # check if file of event annotation
                elif ext == ".txt" and ("datetime" in name or "frame" in name):
                    # check if empty file
                    if os.path.getsize(annot_path) == 0:
                        # remove empty file
                        os.remove(annot_path)

            # update the list of files/folders in the annotation directory
            annot_path_list = os.listdir(self.annot_dir)

            # check if empty annotation directory (or only filled with
            # event annotation of protected label)
            if len(annot_path_list) == 0 or len(annot_path_list) == 2 and \
                annot_path_list[0] == protected_name_0 and \
                    annot_path_list[1] == protected_name_1:
                rmtree(self.annot_dir)

            # check if parent annotation directory is empty
            parent_dir = os.path.split(self.annot_dir)[0]
            if os.listdir(parent_dir) == []:
                rmtree(parent_dir)

        # close videos
        print("close videos (if any)")
        for data_video in self.video_data_dict.values():
            if data_video is not None:
                data_video.release()

        # delete temporary files
        if self.flag_long_rec:
            print("delete temporary signal files")
            rmtree(self.tmp_name, ignore_errors=True)


    def updatePlot(self):
        """
        Updates (during playback) the displayed video frame and the plots of
        the temporal cursor at the current frame :attr:`.frame_id`

        It is called by the thread :attr:`.timer`.

        The displayed video frame and the plots are updated by calling the
        method :meth:`.plotFrameIdPosition`.

        It is only effective if :attr:`.flag_pause_status` is
        ``False``.

        It increments the value of :attr:`.frame_id`.
        """

        # in order to get processing time for updating plot
        time_start = time()

        # update plot only if pause status is False
        if not self.flag_pause_status:
            # plot temporal cursor at the value of self.frame_id
            self.plotFrameIdPosition()

            # increment current frame
            self.frame_id += 1

            # plot in a loop
            self.app.processEvents()

        # sleep
        sleep(max(0, 1 / self.fps - (time() - time_start)))


    def updateFrameId(self, frame_id):
        """
        Sets the value of current frame :attr:`.frame_id` and updates
        the displayed video frame and the plots of the temporal cursor at new
        current frame

        The displayed video frame and the plots are updated by calling the
        method :meth:`.plotFrameIdPosition`.

        :param frame_id: new current frame index
        :type frame_id: int
        """

        # update frame ID
        self.frame_id = frame_id

        # get image if pause status is true
        if self.flag_pause_status:
            for video_id, data_video in self.video_data_dict.items():
                self.im_dict[video_id] = self.getVideoData(data_video)

        # plot frame id position
        self.plotFrameIdPosition()


    def updateProgressBarTitle(self):
        """
        Updates the title of the progress bar :attr:`.wid_progress`
        with the values of the current temporal range defined by
        :attr:`.first_frame` and :attr:`.last_frame`
        """

        current_range_string = ToolsDateTime.convertFrameToString(
            self.last_frame - self.first_frame, self.fps
        )

        frame_id_string = ToolsDateTime.convertFrameToAbsoluteDatetimeString(
            self.frame_id, self.fps, self.beginning_datetime
        )

        self.wid_progress.setTitle(
            '%s (frame %d) - temporal range duration: %s'
            % (frame_id_string, self.frame_id, current_range_string)
        )


    def plotFrameIdPosition(self):
        """
        Updates the displayed video frame and the plots of the temporal cursor
        at the current frame position :attr:`.frame_id`

        If :attr:`.frame_id` is out of the temporal range (defined by
        :attr:`.first_frame` and :attr:`.last_frame`), then
        the temporal range is updated. For example, in the context of long
        recording, this might happen when navigating from one file to another.
        If the temporal range is updated, then the method
        :meth:`.updateSignalPlot` is called in order to update the
        signal plots with the new temporal range.

        The attribute :attr:`.img_vid_dict` is set with the values in
        :attr:`.im_dict` in order to update the displayed video
        frame.

        If the navigation point of the progress bar is not dragged, then the
        attribute :attr:`.wid_progress` is modified in order to
        update the position of the navigation point.

        The attribute :attr:`.current_cursor_list` is set in order to
        update the position of the temporal cursor in the signal widgets.
        """

        # check if frame_id overtakes the current range
        if self.frame_id >= self.last_frame:
            # check if frame id overtakes the video
            if self.frame_id >= self.nframes:
                if not self.flag_long_rec:
                    # single recording
                    self.frame_id = self.nframes - 1

                else:
                    # long recordings => change file
                    ok = self.nextRecording()
                    if not ok:
                        self.frame_id = self.nframes - 1

            else:
                # define new range (with same temporal width as previously)
                temporal_width = self.last_frame - self.first_frame
                if temporal_width + self.last_frame >= self.nframes:
                    self.first_frame = self.nframes - temporal_width
                    self.last_frame = self.nframes

                elif temporal_width + self.last_frame < self.frame_id:
                    self.first_frame = self.frame_id
                    self.last_frame = self.first_frame + temporal_width

                else:
                    self.first_frame = self.last_frame
                    self.last_frame = self.first_frame + temporal_width

                # update signals plot
                self.updateSignalPlot()

        # check if frame_id undertakes the current range
        elif self.frame_id < self.first_frame:
            # check if frame undertakes the video
            if self.frame_id < 0 and self.flag_long_rec:
                # long recordings => change file
                self.previousRecording()

            else:
                # define new range (with same temporal width as previously)
                temporal_width = self.last_frame - self.first_frame
                if self.first_frame - temporal_width < 0:
                    self.first_frame = 0
                    self.last_frame = temporal_width

                elif self.first_frame - temporal_width > self.frame_id:
                    self.last_frame = self.frame_id
                    self.first_frame = self.last_frame - temporal_width

                else:
                    self.last_frame = self.first_frame
                    self.first_frame = self.last_frame - temporal_width

                # update signals plots
                self.updateSignalPlot()

        # update progress bar (if the progress bar is dragged, then there is no
        # need to update it)
        if not self.wid_progress.getDragged():
            self.wid_progress.getProgressPlot().setData([self.frame_id], [0])

        # update temporal cursor
        for current_cursor in self.current_cursor_list:
            current_cursor.setPos(self.getFrameIdInMs(self.frame_id))

        # print current frame id and current temporal width
        self.updateProgressBarTitle()

        # update video image
        for video_id, img_vid in self.img_vid_dict.items():
            img_vid.setImage(self.im_dict[video_id])


    def updateSignalPlot(self, flag_reset_combo_trunc=True,
                         flag_reset_combo_from_cursor=True):
        """
        Updates the signal plots so that it spans the current temporal range
        defined by :attr:`.first_frame` and
        :attr:`.last_frame`

        :param flag_reset_combo_trunc: specify if the combo box
            :attr:`.combo_trunc` must be reset
        :type flag_reset_combo_trunc: bool
        :param flag_reset_combo_from_cursor: specify if the combo box
            :attr:`.combo_from_cursor` must be reset
        :type flag_reset_combo_from_cursor: bool
        """

        # reset combo boxes
        if flag_reset_combo_trunc:
            try:
                self.combo_trunc.setCurrentIndex(0)
            except Exception:
                pass

        if flag_reset_combo_from_cursor:
            try:
                self.combo_from_cursor.setCurrentIndex(0)
            except Exception:
                pass

        # get current range in milliseconds
        first_frame_ms, last_frame_ms = self.getCurrentRangeInMs()

        # print current frame id and current temporal width
        self.updateProgressBarTitle()

        # update progress bar limits
        self.wid_progress.getFirstLine().setValue(self.first_frame)
        self.wid_progress.getLastLine().setValue(self.last_frame - 1)

        # update plots
        for wid, sig_list, data_plot_list, current_plot, type_data in \
            zip(self.wid_data_list, self.sig_list_list,
                self.data_plot_list_list, self.current_cursor_list,
                self.sig_labels):
            for sig, data_plot in zip(sig_list, data_plot_list):
                # get data in the current temporal range
                data_in_current_range = sig.getDataInRange(
                    first_frame_ms, last_frame_ms
                )

                # check if empty signal in the temporal range
                if data_in_current_range.shape[0] == 0:
                    data_plot.clear()

                else:
                    # delete NaNs
                    data_in_current_range = ToolsPyqtgraph.deleteNaNForPlot(
                        data_in_current_range
                    )

                    # signal plot
                    data_plot.setData(data_in_current_range)

            # X axis ticks and range
            self.setTemporalTicks(wid, (first_frame_ms, last_frame_ms))

            # update temporal cursor bounds (for dragging)
            current_plot.setBounds([first_frame_ms, last_frame_ms])

            # check if there are intervals to plot
            if type_data in self.interval_dict.keys():
                # clear existing regions
                for region in self.region_interval_dict[type_data]:
                    wid.removeItem(region)

                # plot detection
                self.region_interval_dict[type_data] = []
                for interval, freq, color in self.interval_dict[type_data]:
                    self.region_interval_dict[type_data] += \
                        ViSiAnnoT.plotIntervals(interval, wid, freq, color)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for plotting region items (pyqtgraph.LinearRegionItem)
    # *********************************************************************** #


    @staticmethod
    def removeItemInWidgets(wid_list, item_list):
        """
        Removes an item from a list of widgets

        :param wid_list: widgets where to remove an item, each element must
            have a method ``removeItem`` (for example an instance of
            pyqtgraph.PlotWidget)
        :type wid_list: list
        :param item_list: items to remove from widgets, same length as
            ``wid_list``, each element corresponds to one element of
            ``wid_list``
        :type item_list: list
        """

        for wid, item in zip(wid_list, item_list):
            wid.removeItem(item)


    def addItemToSignals(self, item_list):
        """
        Displays items in the signal widgets

        :param item_list: items to display in the signal widgets, same length
            as :attr:`.wid_data_list`, each element corresponds to
            one signal widget
        :type item_list: list
        """

        for wid, item in zip(self.wid_data_list, item_list):
            wid.addItem(item)


    def removeRegionInWidgets(self, region_list):
        """
        Removes a region item from the progress bar widget and the signal
        widgets

        :param region_list: instances of pyqtgraph.LinearRegionItem, all
            elements correspond to the same region displayed in the different
            widgets, first element is the region item displayed in the progress
            bar widget (:attr:`.wid_progress`) and the remaining
            elements are the region items displayed in the signal widgets
            (same order as :attr:`.wid_data_list`)
        :type region_list: list
        """

        ViSiAnnoT.removeItemInWidgets(
            [self.wid_progress] + self.wid_data_list, region_list
        )


    def addRegionToWidgets(self, bound_1, bound_2, color=(150, 150, 150, 50)):
        """
        Creates and displays a region item (pyqtgraph.LinearRegionItem) for the
        progress bar (:attr:`.wid_progress`) and the signal widgets
        (:attr:`.wid_data_list`)

        :param bound_1: start frame of the region item (sampled at the
            reference frequency :attr:`.ViSiAnnoT.fps`)
        :type bound_1: int
        :param bound_2: end frame of the region item (sampled at the
            reference frequency :attr:`.ViSiAnnoT.fps`)
        :type bound_2: int
        :param color: plot color (RGBA)
        :type color: tuple or list

        :returns: instances of pyqtgraph.LinearRegionItem (corresponding to the
            same region), first element displayed in the progress bar widget,
            remaining elements displayed in the widget signals
        :rtype: list
        """

        region_list = []

        # display region in progress bar
        region = ViSiAnnoT.addRegionToWidget(
            bound_1, bound_2, self.wid_progress, color
        )

        region_list.append(region)

        # display region in each signal plot
        for wid in self.wid_data_list:
            # convert bounds in milliseconds
            bound_1_ms = self.getFrameIdInMs(bound_1)
            bound_2_ms = self.getFrameIdInMs(bound_2)

            # plot regions in signal widgets
            region = ViSiAnnoT.addRegionToWidget(
                bound_1_ms, bound_2_ms, wid, color
            )

            region_list.append(region)

        return region_list


    @staticmethod
    def plotIntervals(data_interval, wid, freq, color):
        """
        Plots intervals data as a region

        :param data_interval: intervals to be displayed, shape
            :math:`(n_{intervals}, 2)`, each line is an interval with start
            frame and end frame (sampled at ``freq``, relatively to
            :attr:`.ViSAnnoT.beginning_datetime` if used inside
            :class:`.ViSiAnnoT`) ; the intervals might be expressed in
            milliseconds, then ``freq`` must be set to ``0``

            WARNING: test this feature in asynchronous long recording (because
            of relative to :attr:`.ViSAnnoT.beginning_datetime`)
        :type data_interval: numpy array
        :param wid: widget where to plot intervals, might be any widget class
            with a method ``addItem``
        :type wid: pyqtgraph.PlotWidget
        :param freq: sampling frequency of intervals frames, set it to ``0`` if
            intervals expressed in milliseconds
        :type freq: float
        :param color: plot color (RGBA)
        :type color: tuple or list

        :returns: instances of pyqtgraph.LinearRegionItem
        :rtype: list
        """

        region_list = []
        for interval in data_interval:
            det_0 = interval[0]
            det_1 = interval[1]

            # convert interval frames to milliseconds
            if freq > 0:
                det_0 = 1000.0 * det_0 / freq
                det_1 = 1000.0 * det_1 / freq

            # plot region
            region = ViSiAnnoT.addRegionToWidget(det_0, det_1, wid, color)
            region_list.append(region)

        return region_list


    def createTextItem(
        self, text, pos_ms, pos_y_list, text_color=(0, 0, 0),
        border_color=(255, 255, 255), border_width=3
    ):
        """
        Adds a text item to the signal widgets
        (:attr:`.wid_data_list`)

        See
        https://pyqtgraph.readthedocs.io/en/latest/functions.html#pyqtgraph.mkColor
        for supported color formats.

        :param text: text to display in the signal widgets (it is the same in
            each widget)
        :type text: str
        :param pos_ms: temporal position (X axis) of the text item in
            milliseconds
        :type pos_ms: float
        :param pos_y_list: position on the Y axis of the text item in each
            signal widget, same length as :attr:`.wid_data_list`
        :type pos_y_list: float
        :param text_color: color of the text
        :type text_color: tuple or list or str
        :param border_color: color of the text item border
        :type border_color: tuple or list or str
        :param border_width: width of the text item border in pixels
        :type border_width: int

        :returns: instances of pyqtgraph.TextItem, each element corresponds to
            a signal widget, same length and order as
            :attr:`wid_data_list`
        :rtype: list
        """

        # initialize list of text items
        text_item_list = []

        # loop on signal widgets
        for wid, pos_y in zip(self.wid_data_list, pos_y_list):
            # create text item
            text_item = pg.TextItem(text, fill='w', color=text_color,
                                    border={"color": border_color,
                                            "width": border_width})

            # set text item position
            text_item.setPos(pos_ms, pos_y)

            # add text item to signal widget
            wid.addItem(text_item)

            # append list of text items
            text_item_list.append(text_item)

        return text_item_list


    @staticmethod
    def addRegionToWidget(bound_1, bound_2, wid, color):
        """
        Creates a region item (pyqtgraph.LinearRegionItem) and displays it in a
        widget

        :param bound_1: start value of the region item (expressed as a
            coordinate in the X axis of the widget)
        :type bound_1: int
        :param bound_2: end value of the region item (expressed as a
            coordinate in the X axis of the widget)
        :type bound_2: int
        :param wid: widget where to display the region item, might be any
            widget class with a method ``addItem``
        :type wid: pyqtgraph.PlotWidget
        :param color: plot color (RGBA)
        :type color: tuple or list

        :returns: region item displayed in the widget
        :rtype: pyqtgraph.LinearRegionItem
        """

        # pen disabled for linux compatibility
        try:
            region = pg.LinearRegionItem(movable=False, brush=color,
                                         pen={'color': color, 'width': 1})

        except Exception:
            region = pg.LinearRegionItem(movable=False, brush=color)

        # set region boundaries
        region.setRegion([bound_1, bound_2])

        # add region to widget
        wid.addItem(region)

        return region


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for mouse interaction with plots (mostly callback methods)
    # *********************************************************************** #


    def mouseDraggedProgress(self):
        """
        Callback method for mouse dragging of the navigation point in the
        progress bar widget :attr:`.wid_progress`

        It updates the current frame :attr:`.frame_id` at the
        current position defined by the mouse in the progress bar widget.

        Connected to the signal ``sigPlotChanged`` of the scatter plot item of
        :attr:`.wid_progress` (accessed with the method
        :meth:`graphicsoverlayer.ToolsPyqtgraph.ProgressWidget.getProgressPlot`).
        """

        # check if dragging
        if self.wid_progress.getDragged():
            # get the temporal position
            temporal_position = int(
                self.wid_progress.getProgressPlot().getData()[0][0]
            )

            # update current frame
            self.updateFrameId(temporal_position)

            # define new range
            current_range = self.last_frame - self.first_frame

            if self.frame_id + current_range >= self.nframes:
                self.first_frame = self.nframes - current_range
                self.last_frame = self.nframes

            else:
                self.first_frame = self.frame_id
                self.last_frame = self.first_frame + current_range

            # update plots signals
            self.updateSignalPlot()


    def currentCursorDragged(self, cursor):
        """
        Callback method for mouse dragging of the temporal cursor in a signal
        widget

        It updates the current frame :attr:`.frame_id` at the current
        position of the temporal cursor.

        Connected to the signal ``sigDragged`` of the elements of
        :attr:`.current_cursor_list`.

        :param cursor: temporal cursor that is dragged
        :type cursor: pyqtgraph.InfiniteLine
        """

        # update frame id (convert frame id from signal to ref)
        self.updateFrameId(self.convertMsToFrameRef(int(cursor.value())))


    def currentCursorClicked(self, position):
        """
        Sets the current frame :attr:`.frame_id` at the specified
        position

        If the specified position is out of bounds of the current temporal
        range defined by :attr:`.first_frame` and :attr:`.last_frame`,
        then the current frame is not set.

        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`)
        :type position: int
        """

        # check if temporal_position is in the current range
        if position >= self.first_frame and position < self.last_frame:
            # update current frame
            self.updateFrameId(position)


    def signalMouseClicked(self, ev):
        """
        Callback method for managing mouse click on the signal widgets
        (:attr:`.wid_data_list`)

        Connected to the signal ``sigMouseClicked`` of the elements of
        :attr:`.wid_data_list`.

        On one hand, it allows to define manually a temporal interval on which
        to zoom by calling the method :meth:`.zoomOrAnnotClicked`.

        On the other hand, it allows to define a new annotation and to add it
        the annotation file by calling the method
        :meth:`zoomOrAnnotClicked`. Also, it allows to delete
        manually a specific annotation by calling the method
        :meth:`.annotEventDeleteClicked`.

        It also updates the position of the temporal cursor by calling the
        method :meth:`.currentCursorClicked`.

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        keyboard_modifiers = ev.modifiers()

        # map the mouse position to the plot coordinates
        pos_frame, pos_ms = self.getMouseTemporalPosition(ev)

        # check if mouse clicked on a signal widget
        if pos_frame >= 0:
            # check if left button clicked
            if ev.button() == QtCore.Qt.LeftButton:
                # crtl+shift key => delete annotation
                if keyboard_modifiers == \
                        (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                    # only when display mode is on
                    if self.annotevent_button_label_list[3].text() == "On":
                        self.annotEventDeleteClicked(pos_frame)

                # alt key => display description
                elif keyboard_modifiers == QtCore.Qt.AltModifier:
                    self.annotEventDescription(ev, pos_frame, pos_ms)

                # no key modifier (only left button clicked)
                else:
                    self.currentCursorClicked(pos_frame)

            elif ev.button() == QtCore.Qt.RightButton:
                self.zoomOrAnnotClicked(ev, pos_frame, pos_ms)


    def getMouseYPosition(self, ev):
        """
        Gets position of the mouse on the Y axis of all the signal widgets

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent

        :returns: same length as :attr:`.wid_data_list`, each element
            is the position of the mouse on the Y axis in the corresponding
            signal widget, it returns ``[]`` if the mouse clicked on a label
            item (most likely the widget title)
        :rtype: list
        """

        # check what is being clicked
        for item in self.wid_data_list[0].scene().items(ev.scenePos()):
            # if widget title is checked, nothing is returned
            if type(item) is pg.graphicsItems.LabelItem.LabelItem:
                return []

        # map the mouse position to the plot coordinates
        position_y_list = []
        for wid in self.wid_data_list:
            position_y = wid.getViewBox().mapToView(ev.pos()).y()
            position_y_list.append(position_y)

        return position_y_list


    def getMouseTemporalPosition(self, ev):
        """
        Gets the position of the mouse on the X axis

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent

        :returns:
            - **position_frame** (*int*) -- position of the mouse on the X axis
              in frame number (sampled at the reference frequency
              :attr:`ViSiAnnoT.fps`), ``-1`` if the mouse clicked on a label
              item (most likely the widget title)
            - **position_ms** (*float*) -- position of the mouse on the X axis
              in milliseconds, ``-1`` if the mouse clicked on a label item
              (most likely the widget title)
        """

        # check what is being clicked
        for item in self.wid_data_list[0].scene().items(ev.scenePos()):
            # if widget title is checked, nothing is returned
            if type(item) is pg.graphicsItems.LabelItem.LabelItem:
                return -1, -1

        # map the mouse position to the plot coordinates
        position_ms = self.wid_data_list[0].getViewBox().mapToView(ev.pos()).x()

        # convert from signal to ref
        position_frame = self.convertMsToFrameRef(position_ms)

        return position_frame, position_ms


    def zoomOrAnnotClicked(self, ev, pos_frame, pos_ms):
        """
        Manages mouse click for zoom or annotation

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        :param pos_frame: mouse position on the X axis in frame number (sampled
            at the reference frequency :attr:`ViSiAnnoT.fps`)
        :type pos_frame: int
        :param pos_ms: mouse position on the X axis in milliseconds
        :type pos_ms: int
        """

        keyboard_modifiers = ev.modifiers()

        # define position 1
        if self.zoom_pos_1 == -1:
            # zoom
            self.zoom_pos_1 = max(0, min(pos_frame, self.nframes - 1))

            # ctrl key => add annotation
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.annotEventSetTime(self.zoom_pos_1, 0)

        # define position 2
        elif self.zoom_pos_2 == -1:
            # zoom
            self.zoom_pos_2 = max(0, min(pos_frame, self.nframes - 1))

            # ctrl key => add annotation
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.annotEventSetTime(self.zoom_pos_2, 1)

            # swap pos_1 and pos_2 if necessary
            if self.zoom_pos_1 > self.zoom_pos_2:
                self.zoom_pos_1, self.zoom_pos_2 = \
                    self.zoom_pos_2, self.zoom_pos_1

            # plot zoom region
            self.region_zoom_list = self.addRegionToWidgets(
                self.zoom_pos_1, self.zoom_pos_2
            )

            # compute zoom region duration
            duration = (self.zoom_pos_2 - self.zoom_pos_1) / self.fps

            # get list of Y position of the mouse in each signal widget
            pos_y_list = self.getMouseYPosition(ev)

            # display zoom region duration
            self.region_zoom_text_item_list = self.createTextItem(
                "%.3f s" % duration, pos_ms, pos_y_list,
                border_color=(150, 150, 150)
            )

        # both positions defined
        elif self.zoom_pos_1 != -1 and self.zoom_pos_2 != -1:
            # check if click is inside the zoom in area
            if pos_frame >= self.zoom_pos_1 and pos_frame <= self.zoom_pos_2:
                # ctrl key => add annotation
                if keyboard_modifiers == QtCore.Qt.ControlModifier:
                    self.annotEventAdd()

                # no ctrl key => zoom
                else:
                    # define new range
                    self.first_frame = self.zoom_pos_1
                    self.last_frame = self.zoom_pos_2

                    # update current frame if necessary
                    if self.frame_id < self.first_frame \
                            or self.frame_id >= self.last_frame:
                        self.updateFrameId(self.first_frame)

                    # update signals plots
                    self.updateSignalPlot()

            # in case the click is outside the zoom in area
            else:
                if self.annotevent_array.size > 0:
                    # reset annotation times
                    self.annotEventResetTime()

            # remove zoom regions
            self.removeRegionInWidgets(self.region_zoom_list)
            self.region_zoom_list = []

            # remove zoom regions description
            ViSiAnnoT.removeItemInWidgets(
                self.wid_data_list, self.region_zoom_text_item_list
            )

            self.region_zoom_text_item_list = []

            # reset zoom positions
            self.zoom_pos_1 = -1
            self.zoom_pos_2 = -1


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Callback methods for zooming in/out
    # *********************************************************************** #


    def visiAll(self):
        """
        Callback method for resetting the temporal range (defined by
        :attr:`.first_frame` and :attr:`.last_frame`) to
        the fullest

        Connected to the signal ``sigMouseClicked`` of the scene attribute of
        :attr:`.wid_visi`.

        It sets :attr:`.first_frame` to ``0`` and
        :attr:`.last_frame` to :attr:`.nframes`. Then it
        calls the method :meth:`.updateSignalPlot`.
        """

        # update range: all video
        self.first_frame = 0
        self.last_frame = self.nframes

        # update signal plots
        self.updateSignalPlot()


    def zoomIn(self):
        """
        Callback method for zooming in

        Connected to the signal ``sigMouseClicked`` of the scene attribute of
        :attr:`.wid_zoomin`.
        """

        # get current X axis range
        axis = self.wid_data_list[0].getAxis('bottom')
        axis_range_min, axis_range_max = axis.range[0], axis.range[1]

        # convert from signal to ref
        axis_range_min = self.convertMsToFrameRef(axis_range_min)
        axis_range_max = self.convertMsToFrameRef(axis_range_max)

        # check if current range is large enough for zoom in
        if axis_range_max - axis_range_min > 5:
            # compute the range on the left/right side of the temporal cursor
            left = self.frame_id - axis_range_min
            right = axis_range_max - self.frame_id

            # compute the first frame and the last frame after zooming
            self.first_frame = max(
                int(self.frame_id - left / self.zoom_factor), self.first_frame
            )

            self.last_frame = min(
                int(self.frame_id + right / self.zoom_factor), self.last_frame
            )

            # update signals plots
            self.updateSignalPlot()


    def zoomOut(self):
        """
        Callback method for zooming out

        Connected to the signal ``sigMouseClicked`` of the scene attribute of
        :attr:`.wid_zoomout`.
        """

        # get current X axis range
        axis = self.wid_data_list[0].getAxis('bottom')
        axis_range_min, axis_range_max = axis.range[0], axis.range[1]

        # convert from signal to ref
        axis_range_min = self.convertMsToFrameRef(axis_range_min)
        axis_range_max = self.convertMsToFrameRef(axis_range_max)

        # compute the range on the left/right side of the temporal cursor
        left = self.frame_id - axis_range_min
        right = axis_range_max - self.frame_id

        # compute the first frame and the last frame after zooming
        self.first_frame = max(int(self.frame_id - left * self.zoom_factor), 0)

        self.last_frame = min(
            int(self.frame_id + right * self.zoom_factor), self.nframes
        )

        # update signals plots
        self.updateSignalPlot()


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for managing image annotations
    # *********************************************************************** #


    def annotImageCallPushButton(self):
        """
        Callback method for saving an annotated image

        Connected to the signal ``clicked`` of
        :attr:`.annotimage_push_button`.
        """

        # get current label
        current_label = self.annotimage_radio_button_group.checkedButton().text()

        # get output directory
        output_dir = "%s/%s" % (self.annot_dir, current_label)

        # loop on cameras
        for video_id, file_name in self.vid_file_name_dict.items():
            # read image
            im = ToolsImage.transformImage(self.im_dict[video_id])

            # save image
            im_path = "%s/%s_%s.png" % (output_dir, file_name, self.frame_id)
            imwrite(im_path, im)
            print("image saved: %s" % im_path)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for managing event annotations
    # *********************************************************************** #


    def annotEventCallRadio(self, ev):
        """
        Callback method for changing event annotation label with the radio
        buttons

        Connected to the signal ``buttonClicked`` of
        :attr:`.annotevent_button_group_radio_label`.

        It calls the method :meth:`.annotEventChangeLabel` with
        ``ev.text()`` as input.

        :param ev: radio button that has been clicked
        :type ev: QtWidgets.QRadioButton
        """

        # get the new annotation file name
        self.annotEventChangeLabel(ev.text())


    def annotEventChangeLabel(self, new_label):
        """
        Changes event annotation label (loads new annotation file)

        It sets the value of the following attributes:

        - :attr:`.current_label_id` with the index of the new
          annotation label in :attr:`.annotevent_label_list`
        - :attr:`.annotevent_path_list` with the new list of
          annotation file paths (by calling
          :meth:`.annotEventGetPathList`)

        It also manages the display of the annotations.

        :param new_label: new annotation label
        :type new_label: str
        """

        # update current label
        self.annotevent_current_label_id = \
            self.annotevent_label_list.index(new_label)

        # get the new annotation file name
        self.annotevent_path_list = self.annotEventGetPathList(new_label)

        # get number of annotation already stored
        if os.path.isfile(self.annotevent_path_list[0]):
            lines = ToolsData.getTxtLines(self.annotevent_path_list[0])
            nb_annot = len(lines)

        else:
            nb_annot = 0

        # update label with the number of annotations
        self.annotevent_button_label_list[2].setText("Nb: %d" % nb_annot)

        # update label with the start and end time
        non_zero_array = np.count_nonzero(
            self.annotevent_array[self.annotevent_current_label_id], axis=1
        )

        if non_zero_array[0] < 2:
            self.annotevent_button_label_list[0].setText(
                "YYYY-MM-DD hh:mm:ss.sss"
            )
        else:
            self.annotevent_button_label_list[0].setText(
                self.annotevent_array[self.annotevent_current_label_id, 0, 0]
            )

        if non_zero_array[1] < 2:
            self.annotevent_button_label_list[1].setText(
                "YYYY-MM-DD hh:mm:ss.sss"
            )
        else:
            self.annotevent_button_label_list[1].setText(
                self.annotevent_array[self.annotevent_current_label_id, 1, 0]
            )

        # plot annotations
        self.plotAnnotEventRegions()


    def annotEventGetPathList(self, label):
        """
        Gets the path of the annotation files corresponding to the input label

        :param label: event annotation label
        :type label: str

        :returns: paths of the annotation files, each element corresponds to an
            annotation type (see :attr:`.annotevent_type_list`)
        :rtype: list
        """

        annotevent_path_list = []
        for annot_type in self.annotevent_type_list:
            annotevent_path_list.append(
                '%s/%s_%s-%s.txt' % (
                    self.annot_dir, self.annot_file_base, label, annot_type
                )
            )

        return annotevent_path_list


    def annotEventSetTime(self, frame_id, annot_position):
        """
        Sets an annotation value for the current label, either start or end
        timestamp of the event annotation

        It sets the values of
        ``ViSiAnnoT.annotevent_array[ViSiAnnoT.current_label_id, annot_position]``.

        :param frame_id: frame number of the annotation timestamp (sampled at
            the reference frequency :attr:`.ViSiAnnoT.fps`)
        :type frame_id: int
        :param annot_position: specify if start timestamp (``0``) or end
            timestamp (``1``)
        :type annot_position: int
        """

        if (annot_position == 0 or annot_position == 1) and \
                len(self.annotevent_label_list) > 0:
            # set the beginning time of the annotated interval to
            # the current frame
            self.annotevent_array[self.annotevent_current_label_id, annot_position, 0] = \
                ToolsDateTime.convertFrameToAbsoluteDatetimeString(
                    frame_id, self.fps, self.beginning_datetime
            )

            self.annotevent_array[self.annotevent_current_label_id, annot_position, 1] = \
                '%d_%d' % (self.rec_id, frame_id)

            # display the beginning time of the annotated interval
            self.annotevent_button_label_list[annot_position].setText(
                self.annotevent_array[self.annotevent_current_label_id, annot_position, 0]
            )


    def annotEventResetTime(self):
        """
        Resets the annotations value for the current label

        It sets ``ViSiAnnoT.annotevent_array[ViSiAnnoT.annotevent_current_label_id]``
        to zeros.
        """

        # reset the beginning and ending times of the annotated interval
        self.annotevent_array[self.annotevent_current_label_id] = \
            np.zeros((2, 2))

        # reset the displayed beginning and ending times of the annotated interval
        self.annotevent_button_label_list[0].setText("YYYY-MM-DD hh:mm:ss.sss")
        self.annotevent_button_label_list[1].setText("YYYY-MM-DD hh:mm:ss.sss")


    def annotEventAdd(self):
        """
        Adds an event annotation to the current label

        It writes in the annotation files
        (:attr:`.annotevent_path_list`).

        If the annotation start timestamp or end timestamp is not defined, then
        nothing happens.
        """

        # check if beginning time or ending of the annotated interval is empty
        if np.count_nonzero(self.annotevent_array[self.annotevent_current_label_id]) < 4:
            print("Empty annotation !!! Cannot write file.")

        # otherwise all good
        else:
            # convert annotation to datetime
            annot_datetime_0 = ToolsDateTime.convertStringToDatetime(
                self.annotevent_array[self.annotevent_current_label_id, 0, 0],
                "format_T", time_zone=self.time_zone
            )

            annot_datetime_1 = ToolsDateTime.convertStringToDatetime(
                self.annotevent_array[self.annotevent_current_label_id, 1, 0],
                "format_T", time_zone=self.time_zone
            )

            # check if annotation must be reversed
            if (annot_datetime_1 - annot_datetime_0).total_seconds() < 0:
                self.annotevent_array[self.annotevent_current_label_id, [0, 1]] = \
                    self.annotevent_array[self.annotevent_current_label_id, [1, 0]]

            # append the annotated interval to the annotation file
            for ite_annot_type, annot_path in enumerate(
                self.annotevent_path_list
            ):
                with open(annot_path, 'a') as file:
                    file.write(
                        "%s - %s\n" % (
                            self.annotevent_array[self.annotevent_current_label_id, 0, ite_annot_type],
                            self.annotevent_array[self.annotevent_current_label_id, 1, ite_annot_type]
                        )
                    )

            # update the number of annotations
            nb_annot = int(self.annotevent_button_label_list[2].text().split(': ')[1]) + 1
            self.annotevent_button_label_list[2].setText("Nb: %d" % nb_annot)

            # if display mode is on, display the appended interval
            if self.annotevent_button_label_list[3].text() == "On" and \
                self.annotevent_current_label_id in \
                    self.region_annotation_dict.keys():
                region_list = self.annotEventAddRegion(
                    self.annotevent_array[self.annotevent_current_label_id, 0, 0],
                    self.annotevent_array[self.annotevent_current_label_id, 1, 0],
                    color=self.annotevent_color_list[self.annotevent_current_label_id]
                )

                self.region_annotation_dict[self.annotevent_current_label_id].append(region_list)

            # reset the beginning and ending times of the annotated interval
            self.annotEventResetTime()


    def annotEventIdFromPosition(self, position):
        """
        Looks for the index of the annotation at the given position (for the
        current label)

        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`)
        :type position: int

        :returns: index of the annotation (i.e. line number in the annotation
            file), returns ``-1`` if no annotation at ``position``
        :rtype: int
        """

        # initialize output
        annot_id = -1

        # check if annotation file exists
        if os.path.isfile(self.annotevent_path_list[0]):
            # convert mouse position to datetime
            position_date_time = ToolsDateTime.convertFrameToAbsoluteDatetime(
                position, self.fps, self.beginning_datetime
            )

            # get annotations for current label
            lines = ToolsData.getTxtLines(self.annotevent_path_list[0])

            # loop on annotations
            for ite_annot, line in enumerate(lines):
                # get annotation
                line = line.replace("\n", "")

                start_date_time = ToolsDateTime.convertStringToDatetime(
                    line.split(" - ")[0], "format_T", time_zone=self.time_zone
                )

                end_date_time = ToolsDateTime.convertStringToDatetime(
                    line.split(" - ")[1], "format_T", time_zone=self.time_zone
                )

                # check if mouse position is in the annotation interval
                if (position_date_time - start_date_time).total_seconds() >= 0 and \
                        (end_date_time - position_date_time).total_seconds() >= 0:
                    annot_id = ite_annot
                    break

        return annot_id


    def annotEventDescription(self, ev, pos_frame, pos_ms):
        """
        Creates and displays text items in signal widgets with the description
        of the event annotation that has been clicked on

        :param ev: radio button that has been clicked
        :type ev: QtWidgets.QRadioButton
        :param pos_frame: frame number (sampled at the reference frequency
            :attr:`ViSiAnnoT.fps`) corresponding to the mouse position on the X
            axis of the signal widget
        :type pos_frame: int
        :param pos_ms: mouse position on the X axis of the signal widget in
            milliseconds
        :type pos_ms: float
        """

        # get annotation ID that has been clicked
        annot_id = self.annotEventIdFromPosition(pos_frame)

        # check if mouse clicked on an annotation
        if annot_id >= 0:
            # get dictionary with description text items for the current label
            if self.annotevent_current_label_id in \
                    self.annotevent_description_dict.keys():
                description_dict = self.annotevent_description_dict[
                    self.annotevent_current_label_id
                ]

            # create dictionary with description items for the current label
            else:
                description_dict = {}

                self.annotevent_description_dict[
                    self.annotevent_current_label_id
                ] = description_dict

            # check if description already displayed
            if annot_id in description_dict.keys():
                # remove display
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_data_list, description_dict[annot_id]
                )

                # delete list of description text items from dictionary
                del description_dict[annot_id]

            else:
                # get list of Y position of the mouse in each signal widget
                pos_y_list = self.getMouseYPosition(ev)

                # get date-time string annotation
                annot = ToolsData.getTxtLines(
                    self.annotevent_path_list[0]
                )[annot_id]

                # get date-time start/stop of the annotation
                start, stop = annot.replace("\n", "").split(" - ")

                # convert date-time string to datetime
                start = ToolsDateTime.convertStringToDatetime(
                    start, "format_T", time_zone=self.time_zone
                )

                stop = ToolsDateTime.convertStringToDatetime(
                    stop, "format_T", time_zone=self.time_zone
                )

                # compute annotation duration
                duration = (stop - start).total_seconds()

                # get annotation description
                description = "%s - %.3f s" % (
                    self.annotevent_label_list[self.annotevent_current_label_id],
                    duration
                )

                # get description color
                color = self.annotevent_color_list[self.annotevent_current_label_id]

                # create list of description text items for the annotation
                self.annotevent_description_dict[self.annotevent_current_label_id][annot_id] = \
                    self.createTextItem(
                        description, pos_ms, pos_y_list, border_color=color
                )


    def annotEventDeleteClicked(self, position):
        """
        Deletes an annotion that is clicked with mouse

        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`) corresponding to the mouse position on the
            X axis of the signal widgets
        :type position: int
        """

        # get annotated event ID
        annot_id = self.annotEventIdFromPosition(position)

        # check if an annotated event must be deleted
        if annot_id >= 0:
            # delete annotation
            self.annotEventDelete(annot_id)


    @staticmethod
    def deleteLineInFile(path, line_id):
        """
        Class method for deleting a line in a txt file

        :param path: path to the text file
        :type path: str
        :param line_id: number of the line to delete (zero-indexed)
        :type line_id: int
        """

        # read annotation file lines
        lines = ToolsData.getTxtLines(path)

        # remove specified line
        del lines[line_id]

        # rewrite annotation file
        with open(path, 'w') as file:
            file.writelines(lines)


    def annotEventDelete(self, annot_id):
        """
        Deletes a specific annotation for the current label

        :param annot_id: index of the annotation to delete
        :type annot_id: int
        """

        # delete annotation in the txt file
        for annot_path in self.annotevent_path_list:
            ViSiAnnoT.deleteLineInFile(annot_path, annot_id)

        # update number of annotations
        nb_annot = int(self.annotevent_button_label_list[2].text().split(': ')[1])
        nb_annot = max(0, nb_annot - 1)
        self.annotevent_button_label_list[2].setText("Nb: %d" % nb_annot)

        # delete annotation description if necessary
        if self.annotevent_current_label_id in \
                self.annotevent_description_dict.keys():
            description_dict = self.annotevent_description_dict[
                self.annotevent_current_label_id
            ]

            if annot_id in description_dict.keys():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_data_list, description_dict[annot_id]
                )

                del description_dict[annot_id]

            elif annot_id == -1 and nb_annot in description_dict.keys():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_data_list, description_dict[nb_annot]
                )

                del description_dict[nb_annot]

        # if display mode is on, remove the deleted annotation
        if self.annotevent_button_label_list[3].text() == "On":
            self.removeRegionInWidgets(
                self.region_annotation_dict[self.annotevent_current_label_id][annot_id]
            )

            del self.region_annotation_dict[self.annotevent_current_label_id][annot_id]


    def annotEventShow(self):
        """
        Mananges the display of events annotation (on/off)
        """

        # if display mode is off, put it on
        if self.annotevent_button_label_list[3].text() == "Off":
            # notify that display mode is now on
            self.annotevent_button_label_list[3].setText("On")

            # display regions from the annotation file
            self.plotAnnotEventRegions()

        # display mode is on, put it off
        else:
            self.clearAnnotEventRegions()

            # notify that display mode is now off
            self.annotevent_button_label_list[3].setText("Off")


    def annotEventCallPushButton(self, button_id):
        """
        Callback method managing events annotation with push buttons

        Connected to the signal ``buttonClicked[int]`` of the attribute
        attr:`.annotevent_button_group_push`.

        There are 5 buttons and they have an effect on the current label:

        - ``button_id == 0``: set annotation beginning datetime at the current
          frame :attr:`.frame_id`
        - ``button_id == 1``: set annotation ending datetime with the current
          frame :attr;`.frame_id`
        - ``button_id == 2``: add annotation defined by the current beginning
          and ending datetimes
        - ``button_id == 3``: delete last annotation
        - ``button_id == 4``: on/off display

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        # set beginning time of the annotated interval
        if button_id == 0:
            self.annotEventSetTime(self.frame_id, 0)

        # set ending time of the annotated interval
        elif button_id == 1:
            self.annotEventSetTime(self.frame_id, 1)

        # add the annotated interval to the annotation file
        elif button_id == 2:
            self.annotEventAdd()

        # delete last annotation
        elif button_id == 3:
            # check if annotation file exists and annotation file is not empty
            if os.path.isfile(self.annotevent_path_list[0]) and \
                    int(self.annotevent_button_label_list[2].text().split(': ')[1]) > 0:
                self.annotEventDelete(-1)

            else:
                print("Cannot delete annotation since annotation file does not exist or is empty.")

        # display the annotated intervals
        elif button_id == 4:
            self.annotEventShow()


    def plotAnnotEventRegions(self):
        """
        Plots events annotations, either only for the current label, or for all
        lables (depending on the check box "Display all labels")

        Make sure that the attribute :attr:`.region_annotation_dict`
        is already created.

        It checks if the display mode is on before plotting.

        Connected to the signal ``buttonClicked`` of
        :attr:`.annotevent_button_group_radio_disp` and
        :attr:`.annotevent_button_group_check_custom`.
        """

        # check if display mode is on
        if self.annotevent_button_label_list[3].text() == "On":
            # get display mode
            button_id = self.annotevent_button_group_radio_disp.checkedId()

            # display current label
            if button_id == 0:
                plot_dict = {
                    self.annotevent_current_label_id:
                    self.annotevent_color_list[self.annotevent_current_label_id]
                }

            # display all labels
            elif button_id == 1:
                plot_dict = {}
                for label_id, color in enumerate(self.annotevent_color_list):
                    plot_dict[label_id] = color

            # display custom
            elif button_id == 2:
                plot_dict = {}
                for label_id, color in enumerate(self.annotevent_color_list):
                    if self.annotevent_button_group_check_custom.button(label_id).isChecked():
                        plot_dict[label_id] = color

            # loop on labels already plotted
            label_id_list = list(self.region_annotation_dict.keys())
            for label_id in label_id_list:
                # if label not to be plotted anymore
                if label_id not in plot_dict.keys():
                    # clear display
                    self.clearAnnotEventRegionsSingleLabel(label_id)

            # loop on labels to plot
            for label_id, color in plot_dict.items():
                # check if label not already displayed
                if label_id not in self.region_annotation_dict.keys():
                    # get annotation path
                    label = self.annotevent_label_list[label_id]
                    annot_path = self.annotEventGetPathList(label)[0]

                    # initialize list of region items for the label
                    region_annotation_list = []

                    # check if annotation file exists
                    if os.path.isfile(annot_path):
                        # read annotation file
                        lines = ToolsData.getTxtLines(annot_path)

                        # loop on annotations
                        for annot_line in lines:
                            # display region
                            annot_line_content = annot_line.split(' - ')

                            region_list = self.annotEventAddRegion(
                                annot_line_content[0],
                                annot_line_content[1].replace("\n", ""),
                                color=color
                            )

                            # append list of region items for the label
                            region_annotation_list.append(region_list)

                    # update dictionary of region items
                    self.region_annotation_dict[label_id] = \
                        region_annotation_list

                    # display annotations description
                    if label_id in self.annotevent_description_dict.keys():
                        for description_list in \
                                self.annotevent_description_dict[label_id].values():
                            self.addItemToSignals(description_list)


    def clearAnnotEventRegions(self):
        """
        Clears the display of events annotation for all labels (but does not
        delete the annotations)
        """

        # loop on labels
        for label_id in range(len(self.annotevent_label_list)):
            self.clearAnnotEventRegionsSingleLabel(label_id)


    def clearAnnotEventRegionsSingleLabel(self, label_id):
        """
        Clears the display of events annotation for a specific label

        :param label_id: index of the label in the list
            :attr:`.ViSiAnnoT.annotevent_label_list`
        :type label_id: int
        """

        # clear annotations display
        if label_id in self.region_annotation_dict.keys():
            for region_list in self.region_annotation_dict[label_id]:
                self.removeRegionInWidgets(region_list)
            del self.region_annotation_dict[label_id]

        # clear descriptions display
        if label_id in self.annotevent_description_dict:
            for description_list in \
                    self.annotevent_description_dict[label_id].values():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_data_list, description_list
                )


    def clearAllAnnotEventDescriptions(self):
        """
        Clears the display of all the descriptions of events annotation
        """

        for description_dict in self.annotevent_description_dict.values():
            for description_list in description_dict.values():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_data_list, description_list
                )

        self.annotevent_description_dict = {}


    def annotEventAddRegion(self, bound_1, bound_2, **kwargs):
        """
        Displays a region in the progress bar and the signal widgets

        It converts the bounds to frame numbers and then calls the
        method :meth:`.ViSiAnnoT.addRegionToWidgets`.

        :param bound_1: start datetime of the region
        :type bound_1: str
        :param bound_2: end datetime of the region
        :type bound_2: str
        :param kwargs: keyword arguments of
            :meth:`.ViSiAnnoT.addRegionToWidgets`
        """

        # convert bounds to frame numbers
        frame_1 = ToolsDateTime.convertAbsoluteDatetimeStringToFrame(
            bound_1, self.fps, self.beginning_datetime,
            time_zone=self.time_zone
        )

        frame_2 = ToolsDateTime.convertAbsoluteDatetimeStringToFrame(
            bound_2, self.fps, self.beginning_datetime,
            time_zone=self.time_zone
        )

        # check date-time (useful for longRec)
        if frame_1 >= 0 and frame_1 < self.nframes \
            or frame_2 >= 0 and frame_2 < self.nframes \
                or frame_1 < 0 and frame_2 >= self.nframes:
            # display region in each signal plot
            region_list = self.addRegionToWidgets(frame_1, frame_2, **kwargs)

            return region_list

        else:
            return []


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Callback methods for fast navigation
    # *********************************************************************** #


    def callComboTrunc(self, ite_trunc):
        """
        Callback method for selecting a part of the video/signal defined by
        :attr:`.trunc_duration` via the combo box
        :attr:`.combo_trunc`

        Connected to the signal ``currentIndexChanged`` of
        :attr:`.combo_trunc`.

        It sets the temporal range (:attr:`.first_frame` and
        :attr:`.last_frame`) with the selected value in the combo
        box. The current frame :attr:`.frame_id` is set to the new
        :attr:`.first_frame`. Then it calls the method
        :meth:`.updateSignalPlot`.

        :param ite_trunc: index of the selected value in the combo box
            :attr:`.combo_trunc`
        :type ite_trunc: int
        """

        # check if the value selected in the combo box is not the first one
        # (empty one)
        if ite_trunc > 0:
            # define new range
            ite_trunc -= 1
            self.first_frame = ite_trunc * self.nframes_trunc
            self.last_frame = min((ite_trunc + 1) * self.nframes_trunc,
                                  self.nframes)

            # update plots signals
            self.updateSignalPlot(flag_reset_combo_trunc=False)

            # update frame id
            self.updateFrameId(ite_trunc * self.nframes_trunc)


    def callComboFromCursor(self, ite_combo):
        """
        Callback method for selecting a pre-defined temporal range that begins
        at the current temporal cursor position

        Connected to the signal ``currentIndexChanged`` of the attribute
        :attr:`.combo_from_cursor`.

        It sets :attr:`.first_frame` to :attr:`.frame_id`
        and :attr:`.last_frame` so that the temporal range spans the
        selected value of the combo box :attr:`.combo_from_cursor`.
        Then it calls the method :meth:`.updateSignalPlot`.

        :param ite_combo: index of the selected value in the combo box
            :attr:`.combo_from_cursor`
        :type ite_combo: int
        """

        # check if the value selected in the combo box is not empty
        if ite_combo > 0:
            # get the value of the combo box and convert it to frame number
            ite_combo -= 1
            frame_interval = ToolsDateTime.convertTimeToFrame(
                self.fps, minute=self.from_cursor_list[ite_combo][0],
                sec=self.from_cursor_list[ite_combo][1]
            )

            # define new range
            self.first_frame = self.frame_id
            self.last_frame = min(self.frame_id + frame_interval, self.nframes)

            # update plots signals
            self.updateSignalPlot(flag_reset_combo_from_cursor=False)


    def timeEditCurrent(self):
        """
        Callback method to set :attr:`.ViSiAnnoT.edit_start` to the current
        frame :attr:`.ViSiAnnoT.frame_id`

        Connected to the signal ``clicked`` of :attr:`.ViSiAnnoT.current_push`.
        """

        current_datetime = ToolsDateTime.convertFrameToAbsoluteDatetime(
            self.frame_id, self.fps, self.beginning_datetime
        )

        self.edit_start.setDate(
            QtCore.QDate(current_datetime.year,
                         current_datetime.month,
                         current_datetime.day)
        )

        self.edit_start.setTime(
            QtCore.QTime(current_datetime.hour,
                         current_datetime.minute,
                         current_datetime.second)
        )


    def timeEditOk(self):
        """
        Callback method to set the temporal range
        (:attr:`.first_frame` and :attr:`.last_frame`) to
        the custom temporal range (manually defined with
        :attr:`.edit_duration` and :attr:`.edit_start`)

        If :attr:`.edit_duration` is 0, then the current temporal
        range duration is kept.

        Connected to the signal ``clicked`` of
        :attr:`.time_edit_push`.
        """

        # get duration time edit
        duration_qtime = self.edit_duration.time()
        duration_hour = duration_qtime.hour()
        duration_minute = duration_qtime.minute()
        duration_sec = duration_qtime.second()

        # check duration
        if duration_hour == 0 and duration_minute == 0 and duration_sec == 0:
            duration_hour, duration_minute, duration_sec, _ = \
                ToolsDateTime.convertFrameToTime(
                    self.last_frame - self.first_frame, self.fps
                )

        # get start date-time
        start_qdate = self.edit_start.date()
        start_qtime = self.edit_start.time()
        start_date_time = datetime(
            start_qdate.year(), start_qdate.month(), start_qdate.day(),
            start_qtime.hour(), start_qtime.minute(), start_qtime.second()
        )
        pst = timezone(self.time_zone)
        start_date_time = pst.localize(start_date_time)

        # get start frame
        start_frame = ToolsDateTime.convertAbsoluteDatetimeToFrame(
            start_date_time, self.fps, self.beginning_datetime
        )

        # check temporal coherence
        coherence = True
        if start_frame < 0 or start_frame >= self.nframes:
            # check long recordings
            if self.flag_long_rec:
                # get recording id
                start_rec_diff_array = np.array(
                    [(beg_rec - start_date_time).total_seconds()
                        for beg_rec in self.rec_beginning_datetime_list]
                )

                new_rec_id = np.where(start_rec_diff_array >= 0)[0]

                if new_rec_id.shape[0] == 0:
                    coherence = False
                    print("wrong input: start time is above the ending of the recordings")

                elif new_rec_id.shape[0] == start_rec_diff_array.shape[0]:
                    coherence = False
                    print("wrong input: start time is below the beginning of the recording")

                else:
                    # change recording
                    new_rec_id = new_rec_id[0] - 1
                    coherence = self.prepareNewRecording(new_rec_id)

            else:
                print("wrong input: start time is below the beginning of the recordings or above the ending of the recording")
                coherence = False

        # go for it
        if coherence:
            # define new range
            start_frame = ToolsDateTime.convertAbsoluteDatetimeToFrame(
                start_date_time, self.fps, self.beginning_datetime
            )

            if len(self.wid_data_list) > 0:
                self.first_frame = start_frame

                self.last_frame = min(
                    self.nframes,
                    self.first_frame + ToolsDateTime.convertTimeToFrame(
                        self.fps, duration_hour, duration_minute, duration_sec
                    )
                )

            # udpdate current frame
            self.updateFrameId(start_frame)

            # update signals plots
            self.updateSignalPlot()

            # update annotation regions plot
            if len(self.annotevent_label_list) > 0:
                self.clearAnnotEventRegions()
                self.plotAnnotEventRegions()


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Callback method for key press interaction
    # *********************************************************************** #


    def keyPress(self, ev):
        """
        Callback method for key press interaction

        - **Space**: play/pause video playback
        - **Left**: rewind 1 second (1 minute if **ctrl** key pressed as well)
        - **Right**: forward 1 second (1 minute if **ctrl** key pressed as
          well)
        - **Down**: rewind 10 seconds (10 minutes if **ctrl** key pressed as
          well)
        - **Up**: forward 10 seconds (10 minutes if **ctrl** key pressed as
          well)
        - **l**: rewind 1 frame
        - **m**: forward 1 frame
        - **Home**: set the current frame :attr:`.ViSiAnnoT.frame_id` to 0
        - **End**: set the current frame :attr:`.ViSiAnnoT.frame_id` to
          ``ViSiAnnoT.nframes-1``
        - **i**: zoom in (:meth:`.ViSiAnnoT.zoomIn` is called)
        - **o**: zoom out (:meth:`.ViSiAnnoT.zoomOut` is called)
        - **n**: set the temporal range to the fullest
        - **a**: define start datetime of events annotation
        - **z**: define end datetime of events annotation
        - **e**: add events annotation
        - **s**: display events annotations
        - **Page down**: load previous file in case of long recordings
          (:attr:`.ViSiAnnoT.flag_long_rec` is ``True``)
        - **Page up**: load next file in case of long recordings
          (:attr:`.ViSiAnnoT.flag_long_rec` is ``True``)
        - **d** + **ctrl** + **shift**: clear the display of all events
          annotation descriptions

        :param ev: emmited when a key is pressed
        :type ev: QtGui.QKeyEvent
        """

        keyboard_modifiers = ev.modifiers()

        # get pressed key
        key = ev.key()

        if key == QtCore.Qt.Key_Space:
            self.flag_pause_status = not self.flag_pause_status

        elif key == QtCore.Qt.Key_Left:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.updateFrameId(self.frame_id - 60 * self.fps)

            else:
                self.updateFrameId(self.frame_id - self.fps)

            if self.rec_id == 0:
                self.updateFrameId(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_Right:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.updateFrameId(self.frame_id + 60 * self.fps)

            else:
                self.updateFrameId(self.frame_id + self.fps)

            if self.rec_id == self.rec_nb - 1:
                self.updateFrameId(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_Down:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.updateFrameId(self.frame_id - 600 * self.fps)

            else:
                self.updateFrameId(self.frame_id - 10 * self.fps)

            if self.rec_id == 0:
                self.updateFrameId(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_Up:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.updateFrameId(self.frame_id + 600 * self.fps)

            else:
                self.updateFrameId(self.frame_id + 10 * self.fps)

            if self.rec_id == self.rec_nb - 1:
                self.updateFrameId(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_L:
            self.updateFrameId(self.frame_id - 1)
            if self.rec_id == 0:
                self.updateFrameId(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_M:
            self.updateFrameId(self.frame_id + 1)
            if self.rec_id == self.rec_nb - 1:
                self.updateFrameId(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_I and len(self.wid_data_list) > 0:
            self.zoomIn()

        elif key == QtCore.Qt.Key_O and len(self.wid_data_list) > 0:
            self.zoomOut()

        elif key == QtCore.Qt.Key_N and len(self.wid_data_list) > 0:
            self.visiAll()

        elif key == QtCore.Qt.Key_A and len(self.annotevent_label_list) > 0:
            self.annotEventSetTime(self.frame_id, 0)

        elif key == QtCore.Qt.Key_Z and len(self.annotevent_label_list) > 0:
            self.annotEventSetTime(self.frame_id, 1)

        elif key == QtCore.Qt.Key_E and len(self.annotevent_label_list) > 0:
            self.annotEventAdd()

        elif key == QtCore.Qt.Key_S and len(self.annotevent_label_list) > 0:
            self.annotEventShow()

        elif key == QtCore.Qt.Key_PageDown and self.flag_long_rec:
            self.changeFileInLongRec(self.rec_id - 1, 0)

        elif key == QtCore.Qt.Key_PageUp and self.flag_long_rec:
            self.changeFileInLongRec(self.rec_id + 1, 0)

        elif key == QtCore.Qt.Key_Home:
            self.updateFrameId(0)

        elif key == QtCore.Qt.Key_End:
            self.updateFrameId(self.nframes - 1)

        elif key == QtCore.Qt.Key_D and keyboard_modifiers == \
                (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            self.clearAllAnnotEventDescriptions()


    def keyRelease(self, ev):
        """
        Callback method for key release interaction

        - **Alt**: show/hide menu bar

        :param ev: emmited when a key is released
        :type ev: QtGui.QKeyEvent
        """

        # get released key
        key = ev.key()

        if key == QtCore.Qt.Key_Alt:
            if self.menu_bar.isVisible():
                self.menu_bar.hide()

            else:
                self.menu_bar.show()


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for creating widgets
    # *********************************************************************** #


    def createWidgetTimeEdit(self, widget_position):
        """
        Creates a widget for defining a custom temporal interval and adds it to
        the layout :attr:`.ViSiAnnoT.lay`

        A group box is added to the layout and the combo box is added to the
        group box.

        It sets the following attributes:

        - :attr:`.edit_start`
        - :attr:`.current_push`
        - :attr:`.edit_duration`
        - :attr:`.time_edit_push`

        :param widget_position: position of the widget in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type widget_position: list or tuple
        """

        # create group box
        grid, _ = ToolsPyQt.addGroupBox(self.lay,
                                        widget_position,
                                        "Custom temporal range")

        # add qlabel
        q_label = QtWidgets.QLabel("Start date-time")
        q_label.setAlignment(QtCore.Qt.AlignRight)
        grid.addWidget(q_label, 0, 0)

        self.edit_start.setDisplayFormat("yyyy-MM-dd - hh:mm:ss")
        grid.addWidget(self.edit_start, 0, 1)

        # add push button
        self.current_push = ToolsPyQt.addPushButton(grid, (0, 2), "Current")

        # add qlabel
        q_label = QtWidgets.QLabel("Temporal range duration")
        q_label.setAlignment(QtCore.Qt.AlignRight)
        grid.addWidget(q_label, 1, 0)

        # add time edit
        self.edit_duration.setDisplayFormat("hh:mm:ss")
        grid.addWidget(self.edit_duration, 1, 1)

        # add push button
        self.time_edit_push = ToolsPyQt.addPushButton(grid, (1, 2), "Ok")


    def createWidgetProgress(
        self, widget_position, title=None,
        title_style={'color': '#000', 'size': '9pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0
    ):
        """
        Creates a widget with the progress bar and adds it to the layout
        :attr:`.ViSiAnnoT.lay`

        It sets the attribute :attr:`.wid_progress`.

        :param widget_position: position of the widget in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type widget_position: list or tuple
        :param title: widget title
        :type title: str
        :param title_style: widget title style
        :type title_style: dict
        :param ticks_color: color of the ticks text, may be HEX string or
            (RGB)
        :type ticks_color: str or tuple or list
        :param ticks_size: font size of the ticks text in pt
        :type ticks_size: float
        :param ticks_offset: ticks text offset
        :type ticks_offset: int
        """

        # create widget containing the progress bar
        self.wid_progress = ToolsPyqtgraph.ProgressWidget(
            self.nframes, title=title, title_style=title_style,
            ticks_color=ticks_color, ticks_size=ticks_size,
            ticks_offset=ticks_offset
        )

        # add the widget to the layout
        ToolsPyQt.addWidgetToLayout(
            self.lay, self.wid_progress, widget_position
        )

        # set widget height
        self.wid_progress.setMaximumHeight(80)

        # set temporal ticks and X axis range
        self.setTemporalTicks(self.wid_progress, (0, self.nframes, self.fps))

        # set boundaries
        self.wid_progress.getFirstLine().setValue(self.first_frame)
        self.wid_progress.getLastLine().setValue(self.last_frame - 1)

        # print current frame id and current temporal width
        self.updateProgressBarTitle()


    def createWidgetAnnotEvent(self, widget_position, nb_table=5):
        """
        Creates a widget with the events annotation tool and adds it to the
        layout :attr:`.ViSiAnnoT.lay`

        Make sure the attribute :attr:`.annotevent_label_list` is
        defined before calling this method.

        It sets the following attributes:

        - :attr:`.annotevent_button_group_radio_label`
        - :attr:`.annotevent_button_group_push` (must be initialized)
        - :attr:`.annotevent_button_label_list` (must be initialized)
        - :attr:`.annotevent_button_group_radio_disp`
        - :attr:`.annotevent_button_group_check_custom`

        :param widget_position: position of the widget in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type widget_position: list or tuple
        """

        # create group box
        grid, _ = ToolsPyQt.addGroupBox(self.lay, widget_position,
                                        title="Events annotation")

        # create widget with radio buttons (annotation labels)
        _, _, self.annotevent_button_group_radio_label = \
            ToolsPyQt.addWidgetButtonGroup(
                grid, (0, 0, 1, 2), self.annotevent_label_list,
                color_list=self.annotevent_color_list,
                box_title="Current label selection",
                nb_table=nb_table
            )

        # get number of annotations already stored (default first label)
        if os.path.isfile(self.annotevent_path_list[0]):
            lines = ToolsData.getTxtLines(self.annotevent_path_list[0])
            nb_annot = len(lines)
        else:
            nb_annot = 0

        # create push buttons with a label next to it
        button_text_list = ["Start", "Stop", "Add", "Delete last", "Display"]
        button_label_list = [
            "YYYY-MM-DD hh:mm:ss.sss",
            "YYYY-MM-DD hh:mm:ss.sss",
            "Nb: %d" % nb_annot,
            "",
            "On"
        ]

        for ite_button, (text, label) in enumerate(zip(
            button_text_list, button_label_list
        )):
            # add push button
            push_button = ToolsPyQt.addPushButton(
                grid, (1 + ite_button, 0), text,
                flag_enable_key_interaction=False
            )

            # add push button to group for push buttons
            self.annotevent_button_group_push.addButton(
                push_button, ite_button
            )

            # add label next to the push button
            if label != '':
                q_label = QtWidgets.QLabel(label)
                q_label.setAlignment(QtCore.Qt.AlignVCenter)
                grid.addWidget(q_label, 1 + ite_button, 1)
                self.annotevent_button_label_list.append(q_label)

        # create widget with radio buttons (display options)
        _, _, self.annotevent_button_group_radio_disp = \
            ToolsPyQt.addWidgetButtonGroup(
                grid, (2 + ite_button, 0, 1, 2),
                ["Current label", "All labels", "Custom (below)"],
                box_title="Display mode"
            )

        # create check boxes with labels
        _, _, self.annotevent_button_group_check_custom = \
            ToolsPyQt.addWidgetButtonGroup(
                grid, (3 + ite_button, 0, 1, 2), self.annotevent_label_list,
                color_list=self.annotevent_color_list,
                box_title="Custom display",
                button_type="check_box",
                nb_table=nb_table
            )


    def createWidgetAnnotImage(
        self, widget_position, flag_horizontal=True, nb_table=5
    ):
        """
        Creates a widget with the image annotation tool and adds to the layout
        :attr:`.ViSiAnnoT.lay`

        Make sure the attribute :attr:`.annotimage_label_list` is
        defined before calling this method.

        It sets the following attributes:

        - :attr:`.annotimage_radio_button_group`
        - :attr:`.annotimage_push_button`

        :param widget_position: position of the widget in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type widget_position: list or tuple
        :param flag_horizontal: specify if radio buttons are horizontal
        :type flag_horizontal: bool
        """

        # create widget with radio buttons (annotation labels)
        grid, _, self.annotimage_radio_button_group = \
            ToolsPyQt.addWidgetButtonGroup(
                self.lay, widget_position, self.annotimage_label_list,
                button_type="radio",
                box_title="Image extraction",
                flag_horizontal=flag_horizontal,
                nb_table=nb_table
            )

        # get push button position
        if flag_horizontal:
            pos_push_button = (
                ceil(len(self.annotimage_label_list) / nb_table), 0
            )

        else:
            pos_push_button = (
                min(len(self.annotimage_label_list), nb_table), 0
            )

        # add push button
        self.annotimage_push_button = ToolsPyQt.addPushButton(
            grid, pos_push_button, "Save", flag_enable_key_interaction=False
        )


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for setting video and signal data
    # *********************************************************************** #


    def setAllData(self, video_dict, signal_dict, interval_dict):
        """
        Sets video and signal data (to be called before plotting)

        Make sure the following attributes are defined before calling this
        method:

        - :attr:`.plot_style_list`
        - :attr:`.flag_long_rec`

        Make sure the follwing attributes are initialized before calling this
        method (it can be empty):

        - :attr:`.video_data_dict`
        - :attr:`.sig_list_list`
        - :attr:`.interval_dict`

        Otherwise the video thread throws a RunTime error.
        These attributes are then set thanks to the positional arguments
        ``video_dict`` and ``signal_dict``.

        This method sets the following attributes:

        - :attr:`.nframes`
        - :attr:`.ViSiAnnoT.fps`
        - :attr:`.beginning_datetime`
        - :attr:`.sig_list_list`
        - :attr:`.interval_dict`
        - :attr:`.data_wave`

        If there is no video, the attributes :attr:`.nframes`,
        :attr:`.ViSiAnnoT.fps` and :attr:`.beginning_datetime` are
        set with the first signal in ``signal_dict``.

        It raises an exception if 2 videos do not have the same FPS or have a
        temporal shift of more than 1 second.

        :param video_dict: same as first positional argument of
            :class:`.ViSiAnnoT` constructor
        :type video_dict: dict
        :param signal_dict: same as second positional argument of
            :class:`.ViSiAnnoT` constructor
        :type signal_dict: dict
        :param interval_dict: same as keyword argument of :class:`.ViSiAnnoT`
            constructor
        :type interval_dict: dict
        """

        # ******************************************************************* #
        # **************************** Video ******************************** #
        # ******************************************************************* #

        # initialize temporary lists (used in case of several cameras to check
        # synchronization)
        nframes_list = []
        fps_list = []
        beginning_datetime_list = []

        # reset attributes
        self.sig_list_list = []
        self.interval_dict = {}

        # loop on video
        for ite, (video_id, (path_video, delimiter, pos, fmt)) in \
                enumerate(video_dict.items()):
            # get data
            if path_video != '':
                self.video_data_dict[video_id], nframes, fps = \
                    ToolsImage.getDataVideo(path_video)

                beginning_datetime = ToolsDateTime.getDatetimeFromPath(
                    path_video, delimiter, pos, fmt, time_zone=self.time_zone
                )

            else:
                self.video_data_dict[video_id] = None
                nframes = 0
                fps = 0
                beginning_datetime = None

            # update lists
            nframes_list.append(nframes)
            fps_list.append(fps)
            beginning_datetime_list.append(beginning_datetime)

            # check FPS
            if fps <= 0 and path_video != '':
                print("WARNING: video with null FPS at %s" % path_video)
                print()

        # check if there is any video
        if any(self.video_data_dict):
            # make sure that FPS is not null
            flag_ok = False
            for ite_vid, fps in enumerate(fps_list):
                if fps > 0:
                    flag_ok = True
                    break

            if flag_ok:
                self.fps = fps_list[ite_vid]
            else:
                self.fps = 1

            # get number of frames of the video
            self.nframes = nframes_list[ite_vid]

            # get beginning datetime of the video
            self.beginning_datetime = beginning_datetime_list[ite_vid]

        # check if more than 2 videos
        if len(nframes_list) >= 2:
            # update number of frames
            self.nframes = max(nframes_list)

            # check coherence
            for fps in fps_list[1:]:
                if self.fps != fps:
                    if '' not in video_dict.values():
                        raise Exception('The 2 videos do not have the same FPS. %s - %s' % (list(video_dict.values())[0], path_video))


        # ******************************************************************* #
        # ************************** No video ******************************* #
        # ******************************************************************* #

        # check if there is no video
        # in this case the attributes fps, nframes and beginning_datetime are
        # not defined yet => these attributes are defined with the first signal
        if not any(video_dict):
            # get information about signal
            path, key_data, self.fps, delimiter, pos, fmt, _ = \
                list(signal_dict.values())[0][0]

            # get beginning date-time
            self.beginning_datetime = ToolsDateTime.getDatetimeFromPath(
                path, delimiter, pos, fmt, time_zone=self.time_zone
            )

            # get data path (in case not synchronized)
            if self.flag_long_rec and not self.flag_synchro:
                # get first synchronization file content
                lines = ToolsData.getTxtLines(path)

                # get first signal file
                path = lines[1].replace("\n", "")

            # check if audio
            if os.path.splitext(path)[1] == ".wav":
                # get fps of audio
                _, self.fps = ToolsAudio.getAudioWaveFrequency(path)

            # get data
            data = ToolsData.getDataGeneric(path, key_data)

            # check if there is data indeed
            if data.shape[0] == 0:
                raise Exception(
                    "There is no data in the first signal file %s" % path
                )

            # get number of frames
            self.nframes = data.shape[0]


        # ******************************************************************* #
        # *************************** Signal ******************************** #
        # ******************************************************************* #

        # loop on signals
        for ite_type, (type_data, data_info_list) in \
                enumerate(signal_dict.items()):
            # initialize temporary list
            sig_list_tmp = []

            # loop on sub-signals
            for ite_data, (path_data, key_data, freq_data, _, _, _, plot_style) \
                    in enumerate(data_info_list):
                # ******************** load intervals *********************** #
                if type_data in interval_dict.keys():
                    # initialize dictionary value
                    self.interval_dict[type_data] = []

                    # loop on intervals paths
                    for path_interval, key_interval, freq_interval, _, _, _, \
                            color_interval in interval_dict[type_data]:
                        # get frequency if necessary
                        if isinstance(freq_interval, str):
                            freq_interval = ToolsData.getAttributeGeneric(
                                path_interval, freq_interval
                            )

                        elif freq_interval == -1:
                            freq_interval = self.fps

                        # check if file exists
                        if os.path.isfile(path_interval):
                            # asynchronous signal
                            if self.flag_long_rec and not self.flag_synchro:
                                # load intervals data
                                interval = self.getDataSigTmp(
                                    path_interval, type_data, key_interval,
                                    freq_interval, self.tmp_delimiter
                                )

                                # if time series, convert to intervals
                                if interval.ndim == 1:
                                    interval = \
                                        ToolsData.convertTimeSeriesToIntervals(
                                            interval, 1
                                        )

                            # synchro OK
                            else:
                                # load intervals data
                                interval = ToolsData.getDataInterval(
                                    path_interval, key_interval
                                )

                            # update dictionary value
                            self.interval_dict[type_data].append(
                                [interval, freq_interval, color_interval]
                            )


                # ******************** get frequency ************************ #
                # get frequency if necessary
                if os.path.splitext(path_data)[1] == ".wav":
                    _, freq_data = ToolsAudio.getAudioWaveFrequency(path_data)

                elif isinstance(freq_data, str):
                    freq_data = ToolsData.getAttributeGeneric(
                        path_data, freq_data
                    )

                elif freq_data == -1:
                    freq_data = self.fps


                # ********************** load data ************************** #
                # asynchronous signal
                if self.flag_long_rec and not self.flag_synchro:
                    # get data
                    data = self.getDataSigTmp(
                        path_data, type_data, key_data, freq_data,
                        self.tmp_delimiter
                    )

                # synchronous signals
                else:
                    # keyword arguments for ToolsData.getDataGeneric
                    kwargs = {}

                    if os.path.splitext(path_data)[1] == ".wav":
                        kwargs["channel_id"] = \
                            ToolsAudio.convertKeyToChannelId(key_data)

                    # load data
                    data = ToolsData.getDataGeneric(
                        path_data, key_data, **kwargs
                    )


                # ********* convert data into an instance of Signal ********* #
                # signal plot style
                if plot_style is None or plot_style == "":
                    if ite_data < len(self.plot_style_list):
                        plot_style = self.plot_style_list[ite_data]
                    else:
                        raise Exception("No plot style provided for signal %s - %s (sub-id %d) and cannot use the default style." % (type_data, key_data, ite_data))

                # create an instance of Signal
                signal = Signal(
                    data, freq_data, max_points=self.max_points,
                    plot_style=plot_style, legend_text=key_data
                )

                # downsample if necessary
                if freq_data > self.down_freq:
                    signal.downsampleSignal(self.down_freq)

                # append temporary signal list
                sig_list_tmp.append(signal)

            # append list of signals
            self.sig_list_list.append(sig_list_tmp)


    @staticmethod
    def getFileSigTmp(line, delimiter):
        """
        Gets the file name and the start second in a line of a temporary
        synchronization file (in case signal is not synchronized with video)

        :param line: line containing the signal file name and start second
        :type line: str
        :param delimiter: delimiter used to split the line between file name
            and start second
        :type delimiter: str

        :returns:
            - **path** (*str*) -- path to the signal file
            - **start_sec** (*int*) -- start second
        """

        # get data file name and starting second
        if delimiter in line:
            line_split = line.split(delimiter)
            path = line_split[0]
            start_sec = int(line_split[1].replace("\n", ""))
        else:
            path = line.replace("\n", "")
            start_sec = 0

        return path, start_sec


    def getDataSigTmp(self, path, type_data, key_data, freq_data, delimiter):
        """
        Gets signal data after synchronization with video

        :param path: path to the temporary signal file
        :type path: str
        :param type_data: data type (key of the dictionary ``signal_dict``,
            second positional argument of :class:`.ViSiAnnoT` constructor)
        :type type_data: str
        :param key_data: key to access the data (in case of .h5 or .mat file)
        :type key_data: str
        :param freq_data: signal frequency
        :type freq_data: float
        :param delimiter: delimiter used to split the lines of the temporary
            signal files
        :type delimiter: str

        :returns: signal data synchronized with video
        :rtype: numpy array
        """

        # read temporary file
        lines = ToolsData.getTxtLines(path)

        # define empty data
        if len(lines) == 0:
            data = np.array([])

        else:
            # initialize data list
            data_list = []
            start_sec_prev = -1

            # loop on temporary file lines
            for ite_line, line in enumerate(lines):
                # get data file name and starting second
                file_name, start_sec = ViSiAnnoT.getFileSigTmp(line, delimiter)

                # no data at the beginning
                if file_name == "None":
                    data_list.append(np.zeros((int(start_sec * freq_data),)))
                    start_sec_prev = start_sec
                else:
                    # keyword arguments for ToolsData.getDataGeneric
                    kwargs = {}

                    if file_name.split('.')[-1] == "wav":
                        kwargs["channel_id"] = \
                            ToolsAudio.convertKeyToChannelId(key_data)

                    # get data
                    next_data = ToolsData.getDataGeneric(
                        file_name, key_data, **kwargs
                    )

                    # truncate data at the beginning if necessary
                    if ite_line == 0:
                        # 1D data (constant frequency)
                        if len(next_data.shape) == 1:
                            start_frame = int(start_sec * freq_data)
                            next_data = next_data[start_frame:]

                        # 2D data => ms timestamp on first axis
                        else:
                            inds = np.where(next_data[:, 0] >= start_sec * 1000)[0]
                            next_data = next_data[inds]
                            next_data[:, 0] = next_data[:, 0] - start_sec * 1000


                    # truncate data at the end if necessary
                    if ite_line == len(lines) - 1:
                        # 1D data
                        if len(next_data.shape) == 1:
                            # get length of data so far
                            data_length = 0
                            for data_tmp in data_list:
                                data_length += data_tmp.shape[0]

                            # get the end frame
                            end_frame = int(round(freq_data * self.nframes / self.fps - data_length))
                            next_data = next_data[:end_frame]

                        # 2D data => ms timestamp on first axis
                        else:
                            if start_sec_prev != -1:
                                inds = np.where(next_data[:, 0] <= (self.nframes / self.fps - start_sec_prev) * 1000)[0]
                                next_data = next_data[inds]
                                next_data[:, 0] = next_data[:, 0] + start_sec_prev * 1000
                            else:
                                inds = np.where(next_data[:, 0] <= 1000 * self.nframes / self.fps)[0]
                                next_data = next_data[inds]

                    start_sec_prev = -1

                    # concatenate data
                    data_list.append(next_data)

            # check if 2D and zero fill at the beginning
            if len(data_list) > 1:
                if len(data_list[0].shape) == 1 and len(data_list[1].shape) == 2:
                    zero_length = data_list[0].shape[0]
                    if freq_data == 0:
                        data_list[0] = np.empty((0, 2))

                    else:
                        data_list[0] = np.vstack((
                            np.arange(0, zero_length, int(1000 / freq_data)),
                            np.zeros((zero_length,))
                        )).T

            # get data as a numpy array
            data = np.concatenate(tuple(data_list))

        return data


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
