# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
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
from datetime import timedelta
from math import ceil
from ..tools import ToolsPyQt
from ..tools import ToolsPyqtgraph
from ..tools import ToolsDateTime
from ..tools import ToolsData
from ..tools import ToolsImage
from ..tools import ToolsAudio
from .components.Signal import Signal
from .components.SignalWidget import SignalWidget
from .components.MenuBar import MenuBar
from .components.ProgressWidget import ProgressWidget
from .components.VideoWidget import VideoWidget
from .components.CustomTemporalRangeWidget import CustomTemporalRangeWidget
from .components.TruncTemporalRangeWidget import TruncTemporalRangeWidget
from .components.FromCursorTemporalRangeWidget import \
    FromCursorTemporalRangeWidget
from .components.LogoWidgets import ZoomInWidget, ZoomOutWidget, FullVisiWidget


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
        annot_dir="Annotations",
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
        **cv2.VideoCapture**. The set of video data is stored in
        :attr:`.video_data_dict`. The widgets for plotting video are stored in
        :attr:`.wid_vid_dict`.

        For a given signal file, data are loaded in an instance of
        :class:`.Signal`. The supported formats are txt, mat, h5 and wav. The
        set of :class:`.Signal` instances is stored in
        :attr:`.sig_dict`. The widgets for plotting signals are stored in
        :attr:`.wid_sig_list`.

        The reference frequency :attr:`.ViSiAnnoT.fps` is defined as the video
        frequency. If there is no video to display, :attr:`.ViSiAnnoT.fps` is
        defined as the frequency of the first signal to plot. The playback
        speed (both video and signal temporal cursor) is at the reference
        frequency.

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
        :param annot_dir: directory where to save annotations, automatically
            created if it does not exist
        :type annot_dir: str
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
            :func:`.infiniteLoopDisplay`
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

        #: (*dict*) Video data, each item corresponds to one camera
        #:
        #: Key is the camera ID (same keys as ``video_dict``, positional
        #: argument of the constructor of :class:`.ViSiAnnoT`).
        #:
        #: Value is an instance of **cv2.VideoCapture** containing the video
        #: data.
        self.video_data_dict = {}

        #: (*dict*) Signal data, each item corresponds to a signal widget
        #:
        #: Key is the data type (same keys as ``signal_dict``, positional
        #: argument of the constructor), used as label of the Y axis of the
        #: corresponding widget.
        #:
        #: Value is a list of instances of :class:`.Signal` to plot on the
        #: corresponding widget
        self.sig_dict = None

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
        #:  - (*numpy array*) Intervals data, shape :math:`(n_{intervals}, 2)`
        #:  - (*float*) Frequency (``0`` if timestamps, ``-1`` if same as
        #:    signal)
        #:  - (*tuple*) Plot color (RGBA)
        self.interval_dict = {}

        #: (*int*) Frequency of the video (or the first signal if there is no
        #: video), it is the reference frequency
        self.fps = None

        #: (*int*) Number of frames in the video (or the first signal if there
        #: is no video)
        self.nframes = None

        #: (*datetime.datetime*) Beginning datetime of the video (or the first
        #: signal if there is no video)
        self.beginning_datetime = None

        # set data
        self.setAllData(video_dict, signal_dict, interval_dict)

        #: (*dict*) Thresholds to plot on signals widgets, each item
        #: corresponds to one signal widget
        #:
        #: Key is the data type of the signal widget on which to plot (same as
        #: in positional argument ``signal_dict`` of the constructor of
        #: :class:`.ViSiAnnoT`)
        #:
        #: Value is a list of length 2:
        #:
        #: - (*float*) Value of the threshold on Y axis
        #: - (*tuple*) Color to plot (RGB), it can also be a string with HEX
        #:   color
        self.threshold_dict = threshold_dict


        # ******************************************************************* #
        # ***************** annotation files management ********************* #
        # ******************************************************************* #

        #: (*str*) Directory where the annotations are saved
        #:
        #: Specified by the keyword argument ``annot_dir``
        self.annot_dir = annot_dir

        #: (*str*) Base name of the annotation files
        #:
        #: It is defined as the basename of the annotation directory
        #: :attr:`.annot_dir`. When loading/saving annotation files, the label
        #: is appended to the file name.
        self.annot_file_base = os.path.basename(self.annot_dir)


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
            self.createAnnotEventDuration()

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

        #: (*bool*) Specify if the video is paused
        self.flag_pause_status = flag_pause_status

        #: (*int*) Index of the current frame
        self.frame_id = 0

        #: (*int*) First frame that is displayed in the signal plots
        self.first_frame = 0

        #: (*int*) Last frame that is displayed in the signal plots
        #:
        #: Actually, the last frame that is displayed is
        #: ``last_frame` - 1``, because of zero-indexation.
        self.last_frame = self.nframes

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


        # *************** widget for truncated temporal range *************** #
        if "select_trunc" in poswid_dict.keys():
            #: (:class:`.TruncTemporalRangeWidget`) Widget for selecting a
            #: truncated temporal range
            self.wid_trunc = TruncTemporalRangeWidget(
                self, poswid_dict['select_trunc'], trunc_duration
            )

        else:
            self.wid_trunc = None


        # **************** widget for custom temporal range ***************** #
        if "select_manual" in poswid_dict.keys():
            #: (:class:`.CustomTemporalRangeWidget`) Widget for defining a
            #: custom temporal range
            self.wid_time_edit = CustomTemporalRangeWidget(
                self, poswid_dict["select_manual"]
            )

        else:
            self.wid_time_edit = None


        # *************** widget for temporal re-scaling ******************** #
        if len(self.sig_dict) > 0 and \
            "select_from_cursor" in poswid_dict.keys() and \
                len(from_cursor_list) > 0:
            #: (:class:`.FromCursorTemporalRangeWidget`) Widget for selecting
            #: a duration of temporal range to be started at the current frame
            self.wid_from_cursor = FromCursorTemporalRangeWidget(
                self, poswid_dict["select_from_cursor"], from_cursor_list
            )

        else:
            self.wid_from_cursor = None


        # ********************** progress bar ******************************* #
        if "progress" in poswid_dict.keys():
            #: (:class:`.ProgressWidget`) Widget containing the progress bar
            self.wid_progress = ProgressWidget(
                self, poswid_dict['progress'], title_style=font_default_title,
                ticks_color=ticks_color, ticks_size=ticks_size,
                ticks_offset=ticks_offset, nb_ticks=self.nb_ticks
            )

        else:
            raise Exception("No widget position given for the progress bar => add key 'progress' to positional argument poswid_dict")


        # ************************ video widgets **************************** #
        #: (*dict*) Video widgets, each item corresponds to one camera
        #:
        #: Key is the camera ID (same keys as the positional argument
        #: ``video_dict`` of the constructor of :class:`.ViSiAnnoT`).
        #:
        #: Value is an instance of :class:`.VideoWidget` where the
        #: corresponding video is displayed.
        self.wid_vid_dict = {}

        # loop on cameras
        for video_id, (video_path, _, _, _) in video_dict.items():
            # check if widget position exists
            if video_id in poswid_dict.keys():
                # create widget
                self.wid_vid_dict[video_id] = VideoWidget(
                    self.lay, poswid_dict[video_id], video_path,
                    **font_default_title
                )

                # initialize image
                self.wid_vid_dict[video_id].setAndDisplayImage(
                    self.video_data_dict[video_id], self.frame_id
                )


        # *********************** signal widgets **************************** #
        #: (*list*) Signal widgets, each element is an instance of
        #: :class:`.Signal` (same order as :attr:`.sig_dict`
        self.wid_sig_list = []

        # create signal widgets and initialize signal plots
        # it sets the attribute wid_sig_list
        self.initSignalPlot(
            poswid_dict['progress'], y_range_dict=y_range_dict,
            left_label_style=font_default_axis_label, ticks_color=ticks_color,
            ticks_size=ticks_size, ticks_offset=2,
            wid_height=height_widget_signal
        )


        # *********************** zoom widgets ****************************** #
        if len(self.sig_dict) > 0 and "visi" in poswid_dict.keys():
            #: (:class:`.FullVisiWidget`) Widget for zooming out to the full
            #: temporal range
            self.wid_visi = FullVisiWidget(
                self, poswid_dict["visi"], "visibility"
            )

        else:
            self.wid_visi = None

        if len(self.sig_dict) > 0 and "zoomin" in poswid_dict.keys():
            #: (:class:`.ZoomInWidget`) Widget for zooming in
            self.wid_zoomin = ZoomInWidget(
                self, poswid_dict["zoomin"], "zoomin", zoom_factor=zoom_factor
            )

        else:
            self.wid_zoomin = None

        if len(self.sig_dict) > 0 and "zoomout" in poswid_dict.keys():
            #: (:class:`.ZoomOutWidget`) Widget for zooming out
            self.wid_zoomout = ZoomOutWidget(
                self, poswid_dict["zoomout"], "zoomout",
                zoom_factor=zoom_factor
            )

        else:
            self.zoomout = None


        # ******************* event annotation widget *********************** #
        if len(self.annotevent_label_list) > 0:
            if "annot_event" in poswid_dict.keys():
                #: (*QtWidgets.QButtonGroup*) Set of the radio buttons with
                #: labels of events annotation
                self.annotevent_button_group_radio_label = None

                #: (*QtWidgets.QButtonGroup*) Set of the radio buttons with
                #: display options of events annotation
                self.annotevent_button_group_radio_disp = None

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
                #: (*QtWidgets.QButtonGroup*) Set of radio buttons with
                #: labels of image extraction
                self.annotimage_radio_button_group = None

                #: (:class:`.ToolsPyQt.PushButton`) Push
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


    def initSignalPlot(
        self, progbar_wid_pos, y_range_dict={}, **kwargs
    ):
        """
        Creates the signal widgets and initializes the signal plots

        The widgets are automatically positioned below the progress bar.

        It sets the attribute :attr:`.ViSiAnnoT.wid_sig_list`.

        Make sure the attributes :attr:`.ViSiAnnoT.lay`,
        :attr:`.ViSiAnnoT.sig_dict`, :attr:`.ViSiAnnoT.threshold_dict` and
        :attr:`.ViSiAnnoT.interval_dict` are defined before calling this
        method.

        :param progbar_wid_pos: position of the progress bar widget, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type progbar_wid_pos: tuple of list
        :param y_range_dict: visible Y range for signal widgets, see positional
            argument ``y_range_dict`` of :class:`.ViSiAnnoT` constructor
        :type y_range_dict: dict
        :param kwargs: keyword arguments of the constructor of
            :class:`.SignalWidget`, except ``y_range`` and ``left_label``
        """

        # get current range in milliseconds
        first_frame_ms, last_frame_ms = self.getCurrentRangeInMs()

        # convert progress bar widget position to a list
        pos_sig = list(progbar_wid_pos)

        # signal widget position is defined relatively to progress bar
        # widget position
        pos_sig[0] += 1

        # create scroll area
        scroll_lay, _ = ToolsPyQt.addScrollArea(
            self.lay, pos_sig, flag_ignore_wheel_event=True
        )

        # loop on signals
        for ite_sig, (type_data, sig_list) in \
                enumerate(self.sig_dict.items()):
            # get Y range
            if type_data in y_range_dict.keys():
                y_range = y_range_dict[type_data]

            else:
                y_range = []

            # get list of intervals to plot in the signal widget
            if type_data in self.interval_dict.keys():
                interval_list = self.interval_dict[type_data]

            else:
                interval_list = []

            # get list of thresholds to plot in the signal widget
            if type_data in self.threshold_dict.keys():
                threshold_list = self.threshold_dict[type_data]

            else:
                threshold_list = []

            # create widget
            wid = SignalWidget(
                self, pos_sig, y_range=y_range, left_label=type_data, **kwargs
            )

            # create plot items in the signal widget
            wid.createPlotItems(
                first_frame_ms, last_frame_ms, sig_list, interval_list,
                threshold_list
            )

            # set temporal ticks and X axis range
            ToolsPyqtgraph.setTemporalTicks(
                wid, self.nb_ticks, (first_frame_ms, last_frame_ms),
                self.beginning_datetime
            )

            # add widget to scroll area
            scroll_lay.addWidget(wid)

            # append widget to list of widgets
            self.wid_sig_list.append(wid)

            # reconnect to keypress event callback, so that keypress events of
            # scroll are ignored
            wid.keyPressEvent = self.keyPress

            # get position of next signal widget
            pos_sig[0] += 1


    def updateVideoFrame(self):
        """
        Reads the video stream (launched in a thread)

        Called by the thread :attr:`.update_frame_thread`.

        It updates the attribute :attr:`.wid_vid_dict` with the image at
        the current frame for each camera.
        """

        # check if the process still goes on
        while self.flag_processing:
            if not self.flag_pause_status:
                # get image at the current frame for each camera
                for video_id, data_video in self.video_data_dict.items():
                    self.wid_vid_dict[video_id].setImage(
                        data_video, self.frame_id
                    )

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
            annot_path_list = sorted(os.listdir(self.annot_dir))

            # check if empty annotation directory (or only filled with
            # event annotation of protected label)
            if len(annot_path_list) == 0 or len(annot_path_list) == 2 and \
                annot_path_list[0] == protected_name_0 and \
                    annot_path_list[1] == protected_name_1:
                rmtree(self.annot_dir)

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

        # get image for each camera if pause status is true
        if self.flag_pause_status:
            for video_id, data_video in self.video_data_dict.items():
                self.wid_vid_dict[video_id].setImage(
                    data_video, self.frame_id
                )

        # plot frame id position
        self.plotFrameIdPosition()


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

        # check if frame id overtakes the current range
        if self.frame_id >= self.last_frame:
            # check if frame id overtakes the reference file
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
                # get width of the current temporal range
                temporal_width = self.last_frame - self.first_frame

                # frame id is in the last temporal range window
                if self.frame_id + temporal_width > self.nframes:
                    self.first_frame = self.nframes - temporal_width
                    self.last_frame = self.nframes

                # frame id is in the next temporal range window
                elif self.frame_id < self.last_frame + temporal_width:
                    self.first_frame = self.last_frame
                    self.last_frame = self.first_frame + temporal_width

                else:
                    self.first_frame = self.frame_id
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
                # get width of the current temporal range
                temporal_width = self.last_frame - self.first_frame

                # frame id is the first temporal range window
                if self.frame_id - temporal_width < 0:
                    self.first_frame = 0
                    self.last_frame = temporal_width

                # frame id is in the previous temporal range window
                elif self.frame_id > self.first_frame - temporal_width:
                    self.last_frame = self.first_frame
                    self.first_frame = self.last_frame - temporal_width

                else:
                    self.last_frame = self.frame_id
                    self.first_frame = self.last_frame - temporal_width

                # update signals plots
                self.updateSignalPlot()

        # update temporal cursor
        for wid in self.wid_sig_list:
            wid.cursor.setPos(self.getFrameIdInMs(self.frame_id))

        # update progress bar (if the progress bar is dragged, then there is no
        # need to update it)
        if not self.wid_progress.flag_dragged:
            self.wid_progress.setProgressPlot(self.frame_id)

        # set title of progress bar
        self.wid_progress.updateTitle(self.fps, self.beginning_datetime)

        # update video image
        for video_id, wid_vid in self.wid_vid_dict.items():
            wid_vid.displayImage()


    def updateSignalPlot(
        self, flag_reset_combo_trunc=True, flag_reset_combo_from_cursor=True
    ):
        """
        Updates the signal plots and the progress bar so that they span the
        current temporal range defined by :attr:`.first_frame` and
        :attr:`.last_frame`

        :param flag_reset_combo_trunc: specify if the combo box of
            :attr:`.wid_trunc` must be reset
        :type flag_reset_combo_trunc: bool
        :param flag_reset_combo_from_cursor: specify if the combo box of
            :attr:`.wid_from_cursor` must be reset
        :type flag_reset_combo_from_cursor: bool
        """

        # reset combo boxes
        if flag_reset_combo_trunc and self.wid_trunc is not None:
            if self.wid_trunc.combo_box is not None:
                self.wid_trunc.combo_box.setCurrentIndex(0)

        if flag_reset_combo_from_cursor and self.wid_from_cursor is not None:
            self.wid_from_cursor.combo_box.setCurrentIndex(0)

        # set boundaries of progress bar with current temporal range
        self.wid_progress.setBoundaries(self.first_frame, self.last_frame)

        # update title of progress bar
        self.wid_progress.updateTitle(self.fps, self.beginning_datetime)

        # get current range in milliseconds
        first_frame_ms, last_frame_ms = self.getCurrentRangeInMs()

        # update plots
        for wid, (type_data, sig_list) in zip(
            self.wid_sig_list, self.sig_dict.items()
        ):
            # check if there are intervals to plot
            if type_data in self.interval_dict.keys():
                interval_list = self.interval_dict[type_data]

            else:
                interval_list = []

            # update plot items
            wid.updatePlotItems(
                first_frame_ms, last_frame_ms, sig_list, interval_list
            )

            # X axis ticks
            ToolsPyqtgraph.setTemporalTicks(
                wid, self.nb_ticks, (first_frame_ms, last_frame_ms),
                self.beginning_datetime
            )


    # *********************************************************************** #
    # End group
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for plotting region items (pyqtgraph.LinearRegionItem)
    # *********************************************************************** #


    def addItemToSignals(self, item_list):
        """
        Displays items in the signal widgets

        :param item_list: items to display in the signal widgets, same length
            as :attr:`.wid_sig_list`, each element corresponds to
            one signal widget
        :type item_list: list
        """

        for wid, item in zip(self.wid_sig_list, item_list):
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
            (same order as :attr:`.wid_sig_list`)
        :type region_list: list
        """

        ToolsPyqtgraph.removeItemInWidgets(
            [self.wid_progress] + self.wid_sig_list, region_list
        )


    def addRegionToWidgets(self, bound_1, bound_2, color=(150, 150, 150, 50)):
        """
        Creates and displays a region item (pyqtgraph.LinearRegionItem) for the
        progress bar (:attr:`.wid_progress`) and the signal widgets
        (:attr:`.wid_sig_list`)

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
        region = ToolsPyqtgraph.addRegionToWidget(
            bound_1, bound_2, self.wid_progress, color
        )

        region_list.append(region)

        # display region in each signal plot
        for wid in self.wid_sig_list:
            # convert bounds in milliseconds
            bound_1_ms = self.getFrameIdInMs(bound_1)
            bound_2_ms = self.getFrameIdInMs(bound_2)

            # plot regions in signal widgets
            region = ToolsPyqtgraph.addRegionToWidget(
                bound_1_ms, bound_2_ms, wid, color
            )

            region_list.append(region)

        return region_list


    def createTextItem(
        self, text, pos_ms, pos_y_list, text_color=(0, 0, 0),
        border_color=(255, 255, 255), border_width=3
    ):
        """
        Adds a text item to the signal widgets
        (:attr:`.wid_sig_list`)

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
            signal widget, same length as :attr:`.wid_sig_list`
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
        for wid, pos_y in zip(self.wid_sig_list, pos_y_list):
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


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for mouse interaction with plots (mostly callback methods)
    # *********************************************************************** #


    def getMouseYPosition(self, ev):
        """
        Gets position of the mouse on the Y axis of all the signal widgets

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent

        :returns: same length as :attr:`.wid_sig_list`, each element
            is the position of the mouse on the Y axis in the corresponding
            signal widget, it returns ``[]`` if the mouse clicked on a label
            item (most likely the widget title)
        :rtype: list
        """

        # check what is being clicked
        for item in self.wid_sig_list[0].scene().items(ev.scenePos()):
            # if widget title is checked, nothing is returned
            if type(item) is pg.graphicsItems.LabelItem.LabelItem:
                return []

        # map the mouse position to the plot coordinates
        position_y_list = []
        for wid in self.wid_sig_list:
            position_y = wid.getViewBox().mapToView(ev.pos()).y()
            position_y_list.append(position_y)

        return position_y_list


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
            ToolsPyqtgraph.removeItemInWidgets(
                self.wid_sig_list, self.region_zoom_text_item_list
            )

            self.region_zoom_text_item_list = []

            # reset zoom positions
            self.zoom_pos_1 = -1
            self.zoom_pos_2 = -1


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


    def createAnnotEventDuration(self):
        """
        Creates annotation events files for the duration of each file of the
        reference modality (only one file if not a long recording)
        """

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
                    self.wid_sig_list, description_dict[annot_id]
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
                    self.wid_sig_list, description_dict[annot_id]
                )

                del description_dict[annot_id]

            elif annot_id == -1 and nb_annot in description_dict.keys():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_sig_list, description_dict[nb_annot]
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
                    self.wid_sig_list, description_list
                )


    def clearAllAnnotEventDescriptions(self):
        """
        Clears the display of all the descriptions of events annotation
        """

        for description_dict in self.annotevent_description_dict.values():
            for description_list in description_dict.values():
                ViSiAnnoT.removeItemInWidgets(
                    self.wid_sig_list, description_list
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

        elif key == QtCore.Qt.Key_I and len(self.wid_sig_list) > 0:
            self.wid_zoomin.callback(self)

        elif key == QtCore.Qt.Key_O and len(self.wid_sig_list) > 0:
            self.wid_zoomout.callback(self)

        elif key == QtCore.Qt.Key_N and len(self.wid_sig_list) > 0:
            self.wid_visi.callback(self)

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
        - :attr:`.sig_dict`
        - :attr:`.interval_dict`

        Otherwise the video thread throws a RunTime error.
        These attributes are then set thanks to the positional arguments
        ``video_dict`` and ``signal_dict``.

        This method sets the following attributes:

        - :attr:`.nframes`
        - :attr:`.ViSiAnnoT.fps`
        - :attr:`.beginning_datetime`
        - :attr:`.sig_dict`
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
        self.sig_dict = {}
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
                fps = -1
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
                if self.fps != fps and fps >= 0:
                    if '' not in video_dict.values():
                        raise Exception('The 2 videos do not have the same FPS. %s - %s' % (list(video_dict.values())[0][0], path_video))


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
            self.sig_dict[type_data] = sig_list_tmp


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
                            inds = np.where(
                                next_data[:, 0] >= start_sec * 1000
                            )[0]

                            next_data = next_data[inds]

                            next_data[:, 0] = \
                                next_data[:, 0] - start_sec * 1000


                    # truncate data at the end if necessary
                    if ite_line == len(lines) - 1:
                        # 1D data
                        if len(next_data.shape) == 1:
                            # get length of data so far
                            data_length = 0
                            for data_tmp in data_list:
                                data_length += data_tmp.shape[0]

                            # get the end frame
                            end_frame = int(round(
                                freq_data * self.nframes / self.fps - data_length
                            ))

                            next_data = next_data[:end_frame]

                        # 2D data => ms timestamp on first axis
                        else:
                            if start_sec_prev != -1:
                                inds = np.where(
                                    next_data[:, 0] <= (
                                        self.nframes / self.fps - start_sec_prev
                                    ) * 1000
                                )[0]

                                next_data = next_data[inds]

                                next_data[:, 0] = \
                                    next_data[:, 0] + start_sec_prev * 1000

                            else:
                                inds = np.where(
                                    next_data[:, 0] <= 1000 * self.nframes / self.fps
                                )[0]

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
