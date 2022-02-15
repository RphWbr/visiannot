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


from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np
from threading import Thread
import os
from time import sleep
from shutil import rmtree
from ..tools import pyqt_overlayer
from ..tools import pyqtgraph_overlayer
from ..tools import datetime_converter
from ..tools import data_loader
from ..tools.video_loader import get_data_video
from ..tools.audio_loader import get_audio_wave_info, convert_key_to_channel_id
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
from .components.AnnotEventWidget import AnnotEventWidget
from .components.AnnotImageWidget import AnnotImageWidget
from ..configuration import check_configuration


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
        flag_annot_overlap=False,
        annot_dir="Annotations",
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
        current_fmt="%Y-%m-%dT%H:%M:%S.%s",
        range_fmt="%H:%M:%S.%s",
        ticks_fmt="%H:%M:%S.%s",
        ticks_color=(93, 91, 89),
        ticks_size=12,
        ticks_offset=5,
        y_ticks_width=30,
        nb_table_annot=5,
        height_widget_signal=150
    ):
        """
        Class defining the visualization and annotation GUI for a set of
        synchronized video(s) and signal(s).

        The constructor takes as arguments dictionaries with the path to the
        video files and signal files. It calls the method
        :meth:`.set_all_data` in order to load data and store them in
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
        updated with the method :meth:`.update_signal_plot`.

        The playback is managed with two separate threads:

        - Reading next video frame - an instance of threading.Thread with the
          method :meth:`.update_video_frame` as target,
        - Updating plot - an instance of QtCore.QTimer connected to the method
          :meth:`.update_plot`.

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
            - (*str*) Delimiter to get beginning datetime in the signal file
              name,
            - (*int*) Position of the beginning datetime in the signal file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the signal file name
              (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int* or *float* or *str*) Signal frequency, set it to ``0`` if
              signal non regularly sampled, set it to ``-1`` if same frequency
              as :attr:`.ViSiAnnoT.fps`, it may be a string with the path to
              the frequency attribute in a .h5 file - in case of 2D data with
              several value columns, then the column index must be specified,
              e.g. ``"key - 1"`` or ``"key - colName"`` if there is an
              attribute at ``key`` named ``columns`` with columns name being
              comma-separated (first column is always the timestamps),
            - (*dict*) Plot style, see
              https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html
              for details, set it to ``None`` for default.

            See :ref:`signal` for details and examples.
        :type signal_dict: dict
        :param annotevent_dict: events annotation configuration,
            key is the label (string), value is the associated color (RGBA)
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
            - (*tuple* or *list*) Plot color (RGB).
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
            - (*str*) Delimiter to get beginning datetime in the interval file
              name,
            - (*int*) Position of the beginning datetime in the interval file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the interval file
              name (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int*) Signal frequency, set it to ``-1`` if same frequency as
              :attr:`.ViSiAnnoT.fps`, it may be a string with the path to the
              frequency attribute in a .h5 file,
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
        :param flag_annot_overlap: specify if overlap of events annotations is
            enabled
        :type flag_annot_overlap: bool
        :param annot_dir: directory where to save annotations, automatically
            created if it does not exist
        :type annot_dir: str
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
            :func:`.infinite_loop_gui`
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
        :param current_fmt: datetime string format of the current temporal
            position in progress bar, see keyword argument ``fmt`` of
            :func:`.convert_datetime_to_string`
        :type current_fmt: str
        :param range_fmt: datetime string format of the temporal range
            duration in progress bar, see keyword argument ``fmt`` of
            :func:`.convert_datetime_to_string`
        :type range_fmt: str
        :param ticks_fmt: datetime string format of X axis ticks text, see
            keyword argument ``fmt`` of :func:`.convert_datetime_to_string`
        :type ticks_fmt: str
        :param ticks_color: color of the ticks in the signal plots, RGB or HEX
            string
        :type ticks_color: tuple or str
        :param ticks_size: size of the ticks values in the signal plots
        :type ticks_size: int
        :param ticks_offset: offset between the ticks and associated values in
            the signal plots
        :type ticks_offset: int
        :param y_ticks_width: horizontal space in pixels for the text of Y axis
            ticks in signal widgets
        :type y_ticks_width: int
        :param nb_table_annot: maximum number of labels in a row in the
            widgets for events annotation and image annotation
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

        #: (*str*) Datetime string format of the text of X axis ticks
        self.ticks_fmt = ticks_fmt

        #: (*int*) Number of temporal ticks on the X axis of the
        #: signals plots
        self.nb_ticks = nb_ticks

        #: (*str*) Time zone (as in package pytz)
        self.time_zone = time_zone

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

        #: (*str*) Directory where the events annotations and extracted images
        #: are saved
        self.annot_dir = annot_dir


        # ******************************************************************* #
        # ************************ long recordings ************************** #
        # ******************************************************************* #

        #: (*bool*) Specify if :class:`.ViSiAnnoT` is launched in the context
        #: of :class:`.ViSiAnnoTLongRec`
        self.flag_long_rec = flag_long_rec

        #: (*int*) ID of the current video/signal file in case of long
        #: recordings
        #:
        #: If :attr:`.flag_long_rec` is ``False``, then :attr:`.ite_file` is
        #: always equal to 0.
        self.ite_file = 0

        #: (*int*) Number of files for reference modality in case of long
        #: recording
        #:
        #: If :attr:`.flag_long_rec` is ``False``, then :attr:`.nb_files` is
        #: set to 1.
        self.nb_files = 1


        # ******************************************************************* #
        # *************************** data ********************************** #
        # ******************************************************************* #

        # initialize attributes that are set in the method set_all_data

        #: (*dict*) Video data, each item corresponds to one camera
        #:
        #: Key is the camera ID (same keys as ``video_dict``, positional
        #: argument of the constructor of :class:`.ViSiAnnoT`).
        #:
        #: Value is an instance of **cv2.VideoCapture** containing the video
        #: data
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

        # check if not long recording => create attribute of reference
        # frequency (otherwise already set in ViSiAnnoTLongRec)
        if not self.flag_long_rec:
            #: (*int*) Frequency of the video (or the first signal if there is
            #: no video), it is the reference frequency
            self.fps = None

        #: (*int*) Number of frames in the video (or the first signal if there
        #: is no video)
        self.nframes = None

        #: (*datetime.datetime*) Beginning datetime of the video (or the first
        #: signal if there is no video)
        self.beginning_datetime = None

        # set data
        self.set_all_data(video_dict, signal_dict, interval_dict)

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
        # ***************************** zoom ******************************** #
        # ******************************************************************* #

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
        #: Same length and order as :attr:`.ViSiAnnoT.wid_sig_list`, so that
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
                raise Exception(
                    "No layout configuration given - got mode %d, "
                    "must be 1, 2 or 3" % layout_mode
                )


        # ******************************************************************* #
        # ********************* display initialization ********************** #
        # ******************************************************************* #

        # ************** create GUI application and set font **************** #
        #: (*QtWidgets.QApplication*) GUI initializer
        self.app = pyqtgraph_overlayer.initialize_gui_and_bg_color(
            color=bg_color_plot
        )

        # set style sheet
        pyqt_overlayer.set_style_sheet(
            self.app, font_name, font_size, font_color, [
                "QGroupBox", "QComboBox", "QPushButton", "QRadioButton",
                "QLabel", "QCheckBox", "QDateTimeEdit", "QTimeEdit"
            ]
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
        self.win, self.lay = pyqt_overlayer.create_window(
            title="ViSiAnnoT", bg_color=bg_color
        )

        # listen to the callback method (keyboard interaction)
        self.win.keyPressEvent = self.key_press
        self.win.keyReleaseEvent = self.key_release


        # ************************** menu *********************************** #
        #: (:class:`.MenuBar`) Menu bar item, instance of a sub-class of
        #: **QtWidgets.QMenuBar**, by default it is hidden, see
        #: :meth:`.key_release` for the keyword shortcut for displaying it
        self.menu_bar = MenuBar(self.win, self.lay)


        # *************** widget for truncated temporal range *************** #
        if len(self.sig_dict) > 0 and "select_trunc" in poswid_dict.keys():
            # check trunc duration
            if trunc_duration[0] == 0 and trunc_duration[1] == 0:
                print(
                    "Duration of truncated temporal range is 0 => widget not "
                    "created"
                )

                self.wid_trunc = None

            else:
                #: (:class:`.TruncTemporalRangeWidget`) Widget for selecting a
                #: truncated temporal range
                self.wid_trunc = TruncTemporalRangeWidget(
                    self, poswid_dict['select_trunc'], trunc_duration
                )

        else:
            self.wid_trunc = None


        # **************** widget for custom temporal range ***************** #
        if len(self.sig_dict) > 0 and "select_manual" in poswid_dict.keys():
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
                ticks_offset=ticks_offset, nb_ticks=self.nb_ticks,
                current_fmt=current_fmt, range_fmt=range_fmt,
                ticks_fmt=self.ticks_fmt
            )

        else:
            raise Exception(
                "No widget position given for the progress bar => "
                "add key 'progress' to positional argument poswid_dict"
            )


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
        #: :class:`.SignalWidget` (same order as :attr:`.sig_dict`)
        self.wid_sig_list = []

        if len(self.sig_dict) > 0:
            # create signal widgets and initialize signal plots
            self.init_signal_plot(
                poswid_dict['progress'], y_range_dict=y_range_dict,
                left_label_style=font_default_axis_label,
                ticks_color=ticks_color, ticks_size=ticks_size, ticks_offset=2,
                y_ticks_width=y_ticks_width, wid_height=height_widget_signal
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
            self.wid_zoomout = None


        # ******************* events annotation widget ********************** #
        if len(annotevent_dict) > 0:
            if "annot_event" in poswid_dict.keys():
                #: (:class:`.AnnotEventWidget`) Widget for events annotation
                self.wid_annotevent = AnnotEventWidget(
                    self, poswid_dict["annot_event"], annotevent_dict,
                    annot_dir, flag_annot_overlap=flag_annot_overlap,
                    nb_table=nb_table_annot
                )

            else:
                raise Exception(
                    "No widget position given for the events annotation => "
                    "add key 'annot_event' to positinal argument poswid_dict"
                )

        else:
            self.wid_annotevent = None


        # ******************* image annotation widget *********************** #
        if len(annotimage_list) > 0:
            if "annot_image" in poswid_dict.keys():
                # check layout mode
                if layout_mode == 3:
                    flag_horizontal = False

                else:
                    flag_horizontal = True

                #: (:class:`.AnnotImageWidget`) Widget for image extraction
                self.wid_annotimage = AnnotImageWidget(
                    self, poswid_dict["annot_image"], annotimage_list,
                    annot_dir, nb_table=nb_table_annot,
                    flag_horizontal=flag_horizontal
                )

            else:
                raise Exception(
                    "No widget position given for the image annotation => "
                    "add key 'annot_image' to positinal argument poswid_dict"
                )

        else:
            self.wid_annotimage = None


        # ******************************************************************* #
        # ************** thread for getting videos images ******************* #
        # ******************************************************************* #

        if any(self.video_data_dict):
            #: (*threading.Thread*) Thread for getting video frames, connected
            #: to the method :meth:`.ViSiAnnoT.update_video_frame`
            self.update_frame_thread = Thread(target=self.update_video_frame)
            self.update_frame_thread.start()


        # ******************************************************************* #
        # ************************ plot timer ******************************* #
        # ******************************************************************* #

        #: (*QtCore.QTimer*) Thread for updating the current frame position,
        #: connected to the method :meth:`.ViSiAnnoT.update_plot`
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(1000 / self.fps))


        # ******************************************************************* #
        # *********************** infinite loop ***************************** #
        # ******************************************************************* #

        # this does not apply in case of long recording, because there are
        # other stuff to do after calling this constructor
        if not self.flag_long_rec and flag_infinite_loop:
            pyqt_overlayer.infinite_loop_gui(self.app)

            # close streams, delete temporary folders
            self.stop_processing()


    # *********************************************************************** #
    # Group: Methods for conversion between milliseconds and frame number
    # *********************************************************************** #


    def get_frame_id_in_ms(self, frame_id):
        """
        Converts a frame number to milliseconds

        :param frame_id: frame number sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`
        :type frame_id: int

        :returns: frame number in milliseconds
        :rtype: float
        """

        return 1000 * frame_id / self.fps


    def convert_ms_to_frame_ref(self, frame_ms):
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


    def get_current_range_in_ms(self):
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

        return self.get_frame_id_in_ms(self.first_frame), \
            self.get_frame_id_in_ms(self.last_frame)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for displaying video, signals and progress bar
    # *********************************************************************** #


    def init_signal_plot(
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
        first_frame_ms, last_frame_ms = self.get_current_range_in_ms()

        # convert progress bar widget position to a list
        pos_sig = list(progbar_wid_pos)

        # signal widget position is defined relatively to progress bar
        # widget position
        pos_sig[0] += 1

        # create scroll area
        scroll_lay, _ = pyqt_overlayer.add_scroll_area(
            self.lay, pos_sig, flag_ignore_wheel_event=True
        )

        # loop on signals
        for ite_sig, (signal_id, sig_list) in \
                enumerate(self.sig_dict.items()):
            # get Y range
            if signal_id in y_range_dict.keys():
                y_range = y_range_dict[signal_id]

                # check number of elements in yrange configuration
                check_configuration(signal_id, y_range, "YRange")

            else:
                y_range = []

            # get list of intervals to plot in the signal widget
            if signal_id in self.interval_dict.keys():
                interval_list = self.interval_dict[signal_id]

            else:
                interval_list = []

            # get list of thresholds to plot in the signal widget
            if signal_id in self.threshold_dict.keys():
                threshold_list = self.threshold_dict[signal_id]

                # check number of elements in threshold configuration
                check_configuration(signal_id, threshold_list, "Threshold")

            else:
                threshold_list = []

            # create widget
            wid = SignalWidget(
                self, pos_sig, y_range=y_range, left_label=signal_id, **kwargs
            )

            # create plot items in the signal widget
            wid.createPlotItems(
                first_frame_ms, last_frame_ms, sig_list, interval_list,
                threshold_list
            )

            # set temporal ticks and X axis range
            pyqtgraph_overlayer.set_temporal_ticks(
                wid, self.nb_ticks, (first_frame_ms, last_frame_ms),
                self.beginning_datetime, fmt=self.ticks_fmt
            )

            # add widget to scroll area
            scroll_lay.addWidget(wid)

            # append widget to list of widgets
            self.wid_sig_list.append(wid)

            # reconnect to key_press event callback, so that keyPress events of
            # scroll are ignored
            wid.keyPressEvent = self.key_press

            # get position of next signal widget
            pos_sig[0] += 1


    def update_video_frame(self):
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


    def stop_processing(self):
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
            print("delete empty annotation folders/files if necessary")

            # get list of files/folders in the annotation directory
            annot_path_list = os.listdir(self.annot_dir)

            # loop on annotation files/folders
            for annot_file_name in annot_path_list:
                # get path of file/folder
                annot_path = "%s/%s" % (self.annot_dir, annot_file_name)

                # split extension
                name, ext = os.path.splitext(annot_file_name)

                # check if directory of image annotation
                if os.path.isdir(annot_path) and \
                        self.wid_annotimage is not None:
                    if annot_file_name in self.wid_annotimage.label_list:
                        if os.listdir(annot_path) == []:
                            rmtree(annot_path)

                # check if file of events annotation
                elif ext == ".txt":
                    # check if empty file
                    if os.path.getsize(annot_path) == 0:
                        # remove empty file
                        os.remove(annot_path)

            # check if events annotation
            if self.wid_annotevent is not None:
                # update the list of files/folders in the annotation directory
                annot_path_list = os.listdir(self.annot_dir)

                # get file name of events annotation of protected label
                protected_name = "%s_%s-datetime.txt" % (
                    self.wid_annotevent.file_name_base,
                    self.wid_annotevent.protected_label
                )

                # check if empty annotation directory (or only filled with
                # events annotation of protected label)
                if len(annot_path_list) == 0 or len(annot_path_list) == 1 and \
                        annot_path_list[0] == protected_name:
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


    def update_plot(self):
        """
        Updates (during playback) the displayed video frame and the plots of
        the temporal cursor at the current frame :attr:`.frame_id`

        It is called by the thread :attr:`.timer`.

        The displayed video frame and the plots are updated by calling the
        method :meth:`.plot_frame_id_position`.

        It is only effective if :attr:`.flag_pause_status` is
        ``False``.

        It increments the value of :attr:`.frame_id`.
        """

        # update plot only if pause status is False
        if not self.flag_pause_status:
            # plot temporal cursor at the value of self.frame_id
            self.plot_frame_id_position()

            # increment current frame
            self.frame_id += 1

            # plot in a loop
            # self.app.processEvents() # not sure about the usefullness of this


    def update_frame_id(self, frame_id):
        """
        Sets the value of current frame :attr:`.frame_id` and updates
        the displayed video frame and the plots of the temporal cursor at new
        current frame

        The displayed video frame and the plots are updated by calling the
        method :meth:`.plot_frame_id_position`.

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
        self.plot_frame_id_position()


    def plot_frame_id_position(self):
        """
        Updates the displayed video frame and the plots of the temporal cursor
        at the current frame position :attr:`.frame_id`

        If :attr:`.frame_id` is out of the temporal range (defined by
        :attr:`.first_frame` and :attr:`.last_frame`), then
        the temporal range is updated. For example, in the context of long
        recording, this might happen when navigating from one file to another.
        If the temporal range is updated, then the method
        :meth:`.update_signal_plot` is called in order to update the
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
                    ok = self.next_file()
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
                self.update_signal_plot()

        # check if frame_id undertakes the current range
        elif self.frame_id < self.first_frame:
            # check if frame undertakes the video
            if self.frame_id < 0 and self.flag_long_rec:
                # long recordings => change file
                self.previous_file()

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
                self.update_signal_plot()

        # update temporal cursor
        for wid in self.wid_sig_list:
            wid.cursor.setPos(self.get_frame_id_in_ms(self.frame_id))

        # update progress bar (if the progress bar is dragged, then there is no
        # need to update it)
        if not self.wid_progress.flag_dragged:
            self.wid_progress.setProgressPlot(self.frame_id)

        # set title of progress bar
        self.wid_progress.updateTitle(self.fps, self.beginning_datetime)

        # update video image
        for video_id, wid_vid in self.wid_vid_dict.items():
            wid_vid.displayImage()


    def update_signal_plot(
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
        first_frame_ms, last_frame_ms = self.get_current_range_in_ms()

        # update plots
        for wid, (signal_id, sig_list) in zip(
            self.wid_sig_list, self.sig_dict.items()
        ):
            # check if there are intervals to plot
            if signal_id in self.interval_dict.keys():
                interval_list = self.interval_dict[signal_id]

            else:
                interval_list = []

            # update plot items
            wid.updatePlotItems(
                first_frame_ms, last_frame_ms, sig_list, interval_list
            )

            # X axis ticks
            pyqtgraph_overlayer.set_temporal_ticks(
                wid, self.nb_ticks, (first_frame_ms, last_frame_ms),
                self.beginning_datetime, fmt=self.ticks_fmt
            )


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for plotting region items (pyqtgraph.LinearRegionItem)
    # *********************************************************************** #


    def add_item_to_signals(self, item_list):
        """
        Displays items in the signal widgets

        :param item_list: items to display in the signal widgets, same length
            as :attr:`.wid_sig_list`, each element corresponds to
            one signal widget
        :type item_list: list
        """

        for wid, item in zip(self.wid_sig_list, item_list):
            wid.addItem(item)


    def remove_region_in_widgets(self, region_list):
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

        pyqtgraph_overlayer.remove_item_in_widgets(
            [self.wid_progress] + self.wid_sig_list, region_list
        )


    def add_region_to_widgets(
        self, bound_1, bound_2, color=(150, 150, 150, 50)
    ):
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
        region = pyqtgraph_overlayer.add_region_to_widget(
            bound_1, bound_2, self.wid_progress, color
        )

        region_list.append(region)

        # display region in each signal plot
        for wid in self.wid_sig_list:
            # convert bounds in milliseconds
            bound_1_ms = self.get_frame_id_in_ms(bound_1)
            bound_2_ms = self.get_frame_id_in_ms(bound_2)

            # plot regions in signal widgets
            region = pyqtgraph_overlayer.add_region_to_widget(
                bound_1_ms, bound_2_ms, wid, color
            )

            region_list.append(region)

        return region_list


    def create_text_item(
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
            a signal widget, same length and order as :attr:`wid_sig_list`
        :rtype: list
        """

        # initialize list of text items
        text_item_list = []

        # loop on signal widgets
        for wid, pos_y in zip(self.wid_sig_list, pos_y_list):
            # create text item
            text_item = pg.TextItem(
                text, fill='w', color=text_color,
                border={"color": border_color, "width": border_width}
            )

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
    # Group: Methods for mouse interaction with plots
    # *********************************************************************** #


    def get_mouse_y_position(self, ev):
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


    def zoom_or_annot_clicked(self, ev, pos_frame, pos_ms):
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
            if keyboard_modifiers == QtCore.Qt.ControlModifier and \
                    self.wid_annotevent is not None:
                self.wid_annotevent.set_timestamp(self, self.zoom_pos_1, 0)

        # define position 2
        elif self.zoom_pos_2 == -1:
            # zoom
            self.zoom_pos_2 = max(0, min(pos_frame, self.nframes - 1))

            # ctrl key => add annotation
            if keyboard_modifiers == QtCore.Qt.ControlModifier and \
                    self.wid_annotevent is not None:
                self.wid_annotevent.set_timestamp(self, self.zoom_pos_2, 1)

            # swap pos_1 and pos_2 if necessary
            if self.zoom_pos_1 > self.zoom_pos_2:
                self.zoom_pos_1, self.zoom_pos_2 = \
                    self.zoom_pos_2, self.zoom_pos_1

            # plot zoom region
            self.region_zoom_list = self.add_region_to_widgets(
                self.zoom_pos_1, self.zoom_pos_2
            )

            # compute zoom region duration
            duration = (self.zoom_pos_2 - self.zoom_pos_1) / self.fps

            # get list of Y position of the mouse in each signal widget
            pos_y_list = self.get_mouse_y_position(ev)

            # display zoom region duration
            self.region_zoom_text_item_list = self.create_text_item(
                "%.3f s" % duration, pos_ms, pos_y_list,
                border_color=(150, 150, 150)
            )

        # both positions defined
        elif self.zoom_pos_1 != -1 and self.zoom_pos_2 != -1:
            # check if click is inside the zoom in area
            if pos_frame >= self.zoom_pos_1 and pos_frame <= self.zoom_pos_2:
                # ctrl key => add annotation
                if keyboard_modifiers == QtCore.Qt.ControlModifier and \
                        self.wid_annotevent is not None:
                    self.wid_annotevent.add(self)

                # no ctrl key => zoom
                else:
                    # define new range
                    self.first_frame = self.zoom_pos_1
                    self.last_frame = self.zoom_pos_2

                    # update current frame if necessary
                    if self.frame_id < self.first_frame \
                            or self.frame_id >= self.last_frame:
                        self.update_frame_id(self.first_frame)

                    # update signals plots
                    self.update_signal_plot()

            # in case the click is outside the zoom in area
            else:
                if self.wid_annotevent is not None:
                    if self.wid_annotevent.annot_array.size > 0:
                        # reset annotation times
                        self.wid_annotevent.reset_timestamp()

            # remove zoom regions
            self.remove_region_in_widgets(self.region_zoom_list)
            self.region_zoom_list = []

            # remove zoom regions description
            pyqtgraph_overlayer.remove_item_in_widgets(
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
    # Group: Callback method for key press interaction
    # *********************************************************************** #


    def key_press(self, ev):
        """
        Callback method for key press interaction, see :ref:`keyboard`

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
                self.update_frame_id(self.frame_id - 60 * self.fps)

            else:
                self.update_frame_id(self.frame_id - self.fps)

            if self.ite_file == 0:
                self.update_frame_id(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_Right:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.update_frame_id(self.frame_id + 60 * self.fps)

            else:
                self.update_frame_id(self.frame_id + self.fps)

            if self.ite_file == self.nb_files - 1:
                self.update_frame_id(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_Down:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.update_frame_id(self.frame_id - 600 * self.fps)

            else:
                self.update_frame_id(self.frame_id - 10 * self.fps)

            if self.ite_file == 0:
                self.update_frame_id(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_Up:
            if keyboard_modifiers == QtCore.Qt.ControlModifier:
                self.update_frame_id(self.frame_id + 600 * self.fps)

            else:
                self.update_frame_id(self.frame_id + 10 * self.fps)

            if self.ite_file == self.nb_files - 1:
                self.update_frame_id(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_L:
            self.update_frame_id(self.frame_id - 1)
            if self.ite_file == 0:
                self.update_frame_id(max(0, self.frame_id))

        elif key == QtCore.Qt.Key_M:
            self.update_frame_id(self.frame_id + 1)
            if self.ite_file == self.nb_files - 1:
                self.update_frame_id(min(self.nframes, self.frame_id))

        elif key == QtCore.Qt.Key_I and len(self.wid_sig_list) > 0 and \
                self.wid_zoomin is not None:
            self.wid_zoomin.callback(self)

        elif key == QtCore.Qt.Key_O and len(self.wid_sig_list) > 0 and \
                self.wid_zoomout is not None:
            self.wid_zoomout.callback(self)

        elif key == QtCore.Qt.Key_N and len(self.wid_sig_list) > 0 and \
                self.wid_visi is not None:
            self.wid_visi.callback(self)

        elif key == QtCore.Qt.Key_A and self.wid_annotevent is not None:
            if len(self.wid_annotevent.label_list) > 0:
                self.wid_annotevent.set_timestamp(self, self.frame_id, 0)

        elif key == QtCore.Qt.Key_Z and self.wid_annotevent is not None:
            if len(self.wid_annotevent.label_list) > 0:
                self.wid_annotevent.set_timestamp(self, self.frame_id, 1)

        elif key == QtCore.Qt.Key_E and self.wid_annotevent is not None:
            if len(self.wid_annotevent.label_list) > 0:
                self.wid_annotevent.add(self)

        elif key == QtCore.Qt.Key_S and self.wid_annotevent is not None:
            if len(self.wid_annotevent.label_list) > 0:
                self.wid_annotevent.display(self)

        elif key == QtCore.Qt.Key_PageDown and self.flag_long_rec:
            self.change_file_in_long_rec(self.ite_file - 1, 0)

        elif key == QtCore.Qt.Key_PageUp and self.flag_long_rec:
            self.change_file_in_long_rec(self.ite_file + 1, 0)

        elif key == QtCore.Qt.Key_Home:
            self.update_frame_id(0)

        elif key == QtCore.Qt.Key_End:
            self.update_frame_id(self.nframes - 1)

        elif key == QtCore.Qt.Key_D and keyboard_modifiers == \
                (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            if self.wid_annotevent is not None:
                self.wid_annotevent.clear_descriptions(self)


    def key_release(self, ev):
        """
        Callback method for key release interaction, see :ref:`keyboard`

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
    # Group: Methods for setting video and signal data
    # *********************************************************************** #


    def set_all_data(self, video_dict, signal_dict, interval_dict):
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

        Otherwise the video thread throws a RunTime error. These attributes are
        then set thanks to the positional arguments ``video_dict`` and
        ``signal_dict``.

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
        for ite, (video_id, video_config) in enumerate(video_dict.items()):
            # check number of elements in configuration
            check_configuration(
                video_id, video_config, "Video", flag_long_rec=False
            )

            # get video configuration
            path_video, delimiter, pos, fmt = video_config

            # get video data
            self.video_data_dict[video_id], nframes, fps = get_data_video(
                path_video
            )

            # check if no video data
            if self.video_data_dict is None:
                beginning_datetime = None

            else:
                # get beginning datetime of video file
                beginning_datetime = datetime_converter.get_datetime_from_path(
                    path_video, delimiter, pos, fmt, time_zone=self.time_zone
                )

            # update lists
            nframes_list.append(nframes)
            fps_list.append(fps)
            beginning_datetime_list.append(beginning_datetime)

            # check FPS
            if fps <= 0 and path_video != '':
                raise Warning("Video with null FPS at %s" % path_video)

        # check if there is any video
        if any(self.video_data_dict):
            # make sure that FPS is not null
            flag_ok = False
            for ite_vid, fps in enumerate(fps_list):
                if fps > 0:
                    flag_ok = True
                    break

            # check if fps attribute to be set
            if self.fps is None:
                if flag_ok:
                    self.fps = fps_list[ite_vid]

                else:
                    self.fps = 1

            # get number of frames of the video
            self.nframes = nframes_list[ite_vid]

            # get beginning datetime of the video
            self.beginning_datetime = beginning_datetime_list[ite_vid]

        # check if more than 1 video
        if len(nframes_list) > 1:
            # update number of frames
            self.nframes = max(nframes_list)

            # check coherence
            for fps in fps_list[1:]:
                if self.fps != fps and fps >= 0:
                    if '' not in video_dict.values():
                        raise Exception(
                            "The 2 videos do not have the same FPS: "
                            "%s - %s" % (
                                list(video_dict.values())[0][0], path_video
                            )
                        )


        # ******************************************************************* #
        # ************************** No video ******************************* #
        # ******************************************************************* #

        # check if there is no video
        # in this case the attributes fps, nframes and beginning_datetime are
        # not defined yet => these attributes are defined with the first signal
        if not any(video_dict):
            # get first signal configuration
            signal_id = list(signal_dict.keys())[0]
            signal_config = list(signal_dict.values())[0][0]

            # check number of elements in first signal configuration
            check_configuration(
                signal_id, signal_config, "Signal", flag_long_rec=False
            )

            # get first signal configuration
            path, delimiter, pos, fmt, key_data, freq, _ = signal_config

            # check if attribute fps to be set
            if self.fps is None:
                # get frequency and store it as reference frequency
                self.fps = self.get_data_frequency(path, freq)

            # get beginning date-time
            self.beginning_datetime = \
                datetime_converter.get_datetime_from_path(
                    path, delimiter, pos, fmt, time_zone=self.time_zone
                )

            # get data path (in case not synchronized)
            if self.flag_long_rec and not self.flag_synchro:
                # get first synchronization file content
                lines = data_loader.get_txt_lines(path)

                # get first signal file
                path = lines[1].replace("\n", "")

            # get number of frames
            self.nframes = data_loader.get_nb_samples_generic(path, key_data)

            # check if there is data indeed
            if self.nframes == 0:
                raise Exception(
                    "There is no data in the first signal file %s" % path
                )


        # ******************************************************************* #
        # *************************** Signal ******************************** #
        # ******************************************************************* #

        # loop on signals
        for signal_id, signal_config_list in signal_dict.items():
            # initialize temporary list
            sig_list_tmp = []

            # loop on sub-signals
            for ite_data, signal_config in enumerate(signal_config_list):
                # check number of elements in signal configuration
                check_configuration(
                    signal_id, signal_config, "Signal", flag_long_rec=False
                )

                # get configuration
                path_data, _, _, _, key_data, freq_data, plot_style = \
                    signal_config

                # ******************** load intervals *********************** #
                if signal_id in interval_dict.keys():
                    # initialize dictionary value
                    self.interval_dict[signal_id] = []

                    # loop on intervals paths
                    for interval_config in interval_dict[signal_id]:
                        # check number of elements in interval configuration
                        check_configuration(
                            signal_id, interval_config, "Interval",
                            flag_long_rec=False
                        )

                        # get configuration
                        path_interval, _, _, _, key_interval, freq_interval, \
                            color_interval = interval_config

                        # get frequency
                        freq_interval = self.get_data_frequency(
                            path_interval, freq_interval
                        )

                        # asynchronous signal
                        if self.flag_long_rec and not self.flag_synchro:
                            # load intervals data
                            interval, _ = self.get_data_sig_tmp(
                                path_interval, signal_id, key_interval,
                                freq_interval, self.tmp_delimiter,
                                flag_interval=True
                            )

                            # check if empty
                            if interval is None:
                                interval = np.empty((0,))

                        # synchro OK
                        else:
                            # check if fake hole file
                            if path_interval == '':
                                interval = np.empty((0,))

                            else:
                                # load intervals data
                                interval = data_loader.get_data_interval(
                                    path_interval, key_interval
                                )

                        # update dictionary value
                        self.interval_dict[signal_id].append(
                            [interval, freq_interval, color_interval]
                        )

                # ********************** load data ************************** #
                # asynchronous signal
                if self.flag_long_rec and not self.flag_synchro:
                    # get data and frequency
                    data, freq_data = self.get_data_sig_tmp(
                        path_data, signal_id, key_data, freq_data,
                        self.tmp_delimiter
                    )

                # synchronous signals
                else:
                    # check if fake hole file
                    if path_data == '':
                        freq_data = 1
                        data = None

                    else:
                        # get frequency
                        freq_data = self.get_data_frequency(
                            path_data, freq_data
                        )

                        # keyword arguments for data_loader.get_data_generic
                        kwargs = {}
                        if os.path.splitext(path_data)[1] == ".wav":
                            kwargs["channel_id"] = convert_key_to_channel_id(
                                key_data
                            )

                        # load data
                        data = data_loader.get_data_generic(
                            path_data, key_data, **kwargs
                        )


                # ********* convert data into an instance of Signal ********* #
                # signal plot style
                if plot_style is None or plot_style == "":
                    if ite_data < len(self.plot_style_list):
                        plot_style = self.plot_style_list[ite_data]
                    else:
                        raise Exception(
                            "No plot style provided for signal %s - %s "
                            "(sub-id %d) and cannot use the default style" % (
                                signal_id, key_data, ite_data
                            )
                        )

                # create an instance of Signal
                signal = Signal(
                    data, freq_data, max_points=self.max_points,
                    plot_style=plot_style, legend_text=key_data
                )

                # append temporary signal list
                sig_list_tmp.append(signal)

            # append list of signals
            self.sig_dict[signal_id] = sig_list_tmp


    def get_data_frequency(self, path, freq):
        # get frequency if necessary
        if os.path.splitext(path)[1] == ".wav":
            _, freq, _ = get_audio_wave_info(path)

        elif isinstance(freq, str):
            freq = data_loader.get_attribute_generic(path, freq)

        elif freq == -1:
            freq = self.fps

        return freq


    @staticmethod
    def get_file_sig_tmp(line, delimiter):
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


    def get_data_sig_tmp(
        self, path, signal_id, key_data, freq_data, delimiter,
        flag_interval=False
    ):
        """
        Gets signal data after synchronization with video

        :param path: path to the temporary synchronization file
        :type path: str
        :param signal_id: signal type (key in the dictionary ``signal_dict``,
            second positional argument of :class:`.ViSiAnnoT` constructor)
        :type signal_id: str
        :param key_data: key to access the data (in case of .h5 or .mat file)
        :type key_data: str
        :param freq_data: signal frequency as found in the configuration file,
            in case this is a string, then the frequency is retrieved in the
            data file
        :type freq_data: float or str
        :param delimiter: delimiter used to split the lines of the temporary
            signal files
        :type delimiter: str
        :param flag_interval: specify if data to load is intervals
        :type flag_interval: bool

        :returns: signal data synchronized with video
        :rtype: numpy array
        """

        # read temporary file
        lines = data_loader.get_txt_lines(path)

        # define empty data
        if len(lines) == 0:
            data = None
            freq_data = None

        else:
            # initialize data list
            data_list = []
            duration_progress = 0

            # look for data file path in order to get frequency if stored in
            # file attribute
            if isinstance(freq_data, str):
                freq_data_tmp = None
                for line in lines:
                    data_path, _ = ViSiAnnoT.get_file_sig_tmp(line, delimiter)
                    if data_path != "None":
                        freq_data_tmp = self.get_data_frequency(
                            data_path, freq_data
                        )
                        break

                if freq_data_tmp is not None:
                    freq_data = freq_data_tmp

            # data frequency is the same as reference frequency
            elif freq_data == -1:
                freq_data = self.fps

            # loop on temporary file lines
            for ite_line, line in enumerate(lines):
                # get data path and starting second
                data_path, start_sec = ViSiAnnoT.get_file_sig_tmp(
                    line, delimiter
                )

                # no data at the beginning
                if data_path == "None":
                    # check if 2D data (signal not regularly sampled)
                    if freq_data == 0:
                        next_data = np.empty((0, 2))

                    else:
                        next_data = np.nan * np.ones(
                            (int(start_sec * freq_data),)
                        )
                    
                    duration_progress += start_sec

                else:
                    # check if 2D data (signal not regularly sampled)
                    if freq_data == 0:
                        # get first column (samples timestamps)
                        next_data_ts = data_loader.get_data_generic(
                            data_path, key=key_data, slicing=("col", 0)
                        )

                    # initialize slicing indexes
                    start_ind = 0
                    end_ind = None

                    # truncate data at the beginning if necessary
                    if ite_line == 0:
                        # 1D data (regularly sampled)
                        if freq_data > 0:
                            # get slicing index
                            start_ind = int(start_sec * freq_data)

                        # 2D data (not regularly sampled)
                        else:
                            # get indexes of samples after starting second
                            inds = np.where(
                                next_data_ts >= start_sec * 1000
                            )[0]

                            # get slicing index
                            start_ind = inds[0]

                            # update temporal offset
                            duration_progress = - start_sec

                    # truncate data at the end if necessary
                    if ite_line == len(lines) - 1:
                        # get duration of reference data file in seconds
                        ref_duration = self.nframes / self.fps

                        # 1D data
                        if freq_data > 0:
                            # get length of data so far
                            data_length = 0
                            for data_tmp in data_list:
                                data_length += data_tmp.shape[0]

                            # get remaining data length required to fill
                            # the reference data file
                            remaining_length = int(round(
                                freq_data * ref_duration - data_length
                            ))

                            # get slicing index
                            end_ind = start_ind + remaining_length

                        # 2D data (not regularly sampled)
                        else:
                            temporal_limit = (
                                ref_duration - duration_progress
                            ) * 1000

                            # get indexes of samples before temporal limit
                            inds = np.where(
                                next_data_ts <= temporal_limit
                            )[0]

                            # get slicing indexes
                            end_ind = inds[-1] + 1

                    # keyword arguments for loading data
                    kwargs = {"key": key_data}

                    # channel specification when loading audio
                    if data_path.split('.')[-1] == "wav":
                        kwargs["channel_id"] = convert_key_to_channel_id(
                            key_data
                        )

                    # slicing keyword argument for data loading
                    if start_ind == 0 and end_ind is None:
                        kwargs["slicing"] = ()

                    elif end_ind is None:
                        kwargs["slicing"] = (start_ind,)

                    else:
                        kwargs["slicing"] = (start_ind, end_ind)

                    # check if interval data
                    if flag_interval:
                        # load data with slicing
                        next_data = \
                            data_loader.get_data_interval_as_time_series(
                                data_path, **kwargs
                            )

                    else:
                        # load data with slicing
                        next_data = data_loader.get_data_generic(
                            data_path, **kwargs
                        )

                    # get duration of truncated data
                    if freq_data > 0:
                        duration = next_data.shape[0] / freq_data

                    else:
                        duration = (next_data[-1, 0] - next_data[0, 0]) / 1000

                        # temporal offset
                        next_data[:, 0] += duration_progress * 1000

                    duration_progress += duration

                # concatenate data
                data_list.append(next_data)

            # get data as a numpy array
            data = np.concatenate(tuple(data_list))

            # convert intervals data from time series to intervals
            if flag_interval:
                data = data_loader.convert_time_series_to_intervals(data, 1)

        return data, freq_data


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
