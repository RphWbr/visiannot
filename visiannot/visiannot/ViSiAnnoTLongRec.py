# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber, Edouard Boustouler
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.ViSiAnnoTLongRec`
"""


import numpy as np
import os
from glob import glob
from datetime import timedelta
from ..tools import pyqt_overlayer
from ..tools import datetime_converter
from ..tools import data_loader
from ..tools.video_loader import get_duration_video, get_data_video
from .ViSiAnnoT import ViSiAnnoT
from ..configuration import check_configuration
from .components.LogoWidgets import PreviousWidget, NextWidget
from .components.FileSelectionWidget import FileSelectionWidget
from concurrent.futures import ProcessPoolExecutor


class ViSiAnnoTLongRec(ViSiAnnoT):
    def __init__(
        self, video_dict, signal_dict, interval_dict={},
        temporal_range=(0, 30), layout_mode=1, poswid_dict={}, **kwargs
    ):
        """
        Subclass of :class:`.ViSiAnnoT` for managing a long recording with
        several files

        First, it searches the list of paths to the video/signal files. It
        creates temporary files with info for synchronization. TODOTODO

        :param video_dict: video configuration, each item corresponds to one
            camera. Key is the camera ID (string). Value is a configuration
            list of length 5:

            - (*str*) Directory where to find the video files,
            - (*str*) Pattern to find video files (e.g. ``"*.mp4"``),
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
            list of 8 elements:

            - (*str*) Directory where to find the signal files, see positional
              argument ``signal_dict`` of :class:`.ViSiAnnoT` constructor for
              detail about data storing format,
            - (*str*) Pattern to find signal files,
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

            See :ref:`sec-longrec` for details.
        :type signal_dict: dict
        :param interval_dict: interval configuration. Each item
            corresponds to a signal widget on which to plot intervals. The key
            must be the same as in ``signal_dict``. Value is a nested list of
            interval configurations. Each element of the nested list
            corresponds to a type of interval to be plotted in the same
            signal widget and is a configuration list of 8 elements:

            - (*str*) Directory where to find interval files, see positional
              argument ``interval_dict`` of :class:`.ViSiAnnoT` constructor for
              detail about data storing format,
            - (*str*) Pattern to find interval files,
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
        :param temporal_range: temporal range duration used to split the long
            recording into several files, 2 elements: *(minutes, seconds)*
        :type temporal_range: tuple
        :param layout_mode: organization of widgets positioning in the window
            layout (ignored if custom layout organization provided with keyword
            argument ``poswid_dict``), one of the following:

            - ``1`` (focus on video, works better with a big screen),
            - ``2`` (focus on signal, suitable for a laptop screen),
            - ``3`` (compact display with some features disabled),
            - ``4`` (adapted to portrait screen orientation).
        :type layout_mode: int
        :param poswid_dict: custom organization of widgets positioning in the
            window layout. Value is a tuple of length 2 ``(row, col)``
            or 4 ``(row, col, rowspan, colspan)``. Key identifies the widget:

            - ``"video"``
            - ``"select_manual"``
            - ``"select_from_cursor"``
            - ``"annot_event"``
            - ``"annot_image"``
            - ``"visi"``
            - ``"zoomin"``
            - ``"zoomout"``
            - ``"previous"``
            - ``"next"``
            - ``"file_selection"``
            - ``"progress"``

            The signal widgets are automatically positioned below the progress
            bar.
        :type poswid_dict: dict
        :param kwargs: keyword arguments of :class:`.ViSiAnnoT` constructor
        """

        # check input dictionaries are empty
        if not any(video_dict) and not any(signal_dict):
            raise Exception("Input dictionaries are empty")

        #: (*int*) Temporal range duration in seconds used to split long
        #: recording into several files
        self.temporal_range_duration_split = \
            temporal_range[0] * 60 + temporal_range[1]

        # get time zone
        if "time_zone" in kwargs.keys():
            time_zone = kwargs["time_zone"]
        else:
            time_zone = "Europe/Paris"


        # ******************************************************************* #
        # ********************* video configuration ************************* #
        # ******************************************************************* #

        #: (*dict*) Key is a camera ID. Value is the corresponding
        #: configuration list without video path
        self.video_config_dict = {}
        for cam_id, config in video_dict.items():
            self.video_config_dict[cam_id] = config[2:]

        #: (*dict*) Key is a camera ID. Value is a list of length 2: list of 
        #: video paths and list of beginning datetimes
        #:
        #: After having called the method :meth:`.process_synchronization_all`,
        #: the video paths become the path to temporary synchronization files.
        self.video_list_dict = {}

        # get list of video paths and beginning datetimes for each camera
        self.set_video_list_dict(video_dict, time_zone=time_zone)

        # ******************************************************************* #
        # ********************* reference frequency ************************* #
        # ******************************************************************* #

        # check if any video
        if any(video_dict):
            # get fps
            ite_vid = 0
            path_list = list(self.video_list_dict.values())[0][0]
            self.fps = 0
            while self.fps <= 0:
                _, _, self.fps = get_data_video(path_list[ite_vid])
                ite_vid += 1

        # no video
        else:
            # get first signal configuration
            signal_id = list(signal_dict.keys())[0]
            signal_config = list(signal_dict.values())[0][0]

            # check number of elements in first signal configuration
            check_configuration(signal_id, signal_config, "Signal")

            # get info for first signal
            data_dir, pattern, _, _, _, _, freq, _ = signal_config

            # get list of signal files paths
            data_list_tmp = glob('%s/%s' % (data_dir, pattern))

            # check if any file
            if len(data_list_tmp) == 0:
                raise Exception(
                    "Empty directory for first signal: %s - %s" %
                    (pattern, data_dir)
                )

            # store frequency as the reference frequency
            self.fps = self.get_data_frequency(data_list_tmp[0], freq)


        # ******************************************************************* #
        # ********************** signal configuration *********************** #
        # ******************************************************************* #

        #: (*dict*) Key is a data type, corresponding to a signal widget. Value
        #: is the corresponding configuration list without data path
        self.signal_config_dict = {}
        for signal_id, config_list in signal_dict.items():
            self.signal_config_dict[signal_id] = []
            for config in config_list:
                self.signal_config_dict[signal_id].append(config[2:])

        #: (*dict*) Key is a data type, corresponding to a signal widget. Value
        #: is a list (along the signals in the widget) of lists of length 2:
        #: list of signal paths and list of beginning datetimes
        #:
        #: After having called the method :meth:`.process_synchronization_all`,
        #: the video paths become the path to temporary synchronization files.
        self.signal_list_dict = {}

        #: (*dict*) Key is a data type, corresponding to a signal widget on
        #: which to plot intervals. Value is the corresponding configuration
        #: list without data path
        self.interval_config_dict = {}
        for interval_id, config_list in interval_dict.items():
            self.interval_config_dict[interval_id] = []
            for config in config_list:
                self.interval_config_dict[interval_id].append(config[2:])

        #: (*dict*) Key is a data type, corresponding to a signal widget on
        #: which to plot intervals. Value is a list (along the intervals types
        #: in the widget) of lists of length 2: list of interval paths and
        #: list of beginning datetimes
        #:
        #: After having called the method :meth:`.process_synchronization_all`,
        #: the video paths become the path to temporary synchronization files.
        self.interval_list_dict = {}

        # get list of data paths and beginning datetimes for each signal and
        # interval
        self.set_signal_interval_list(
            signal_dict, interval_dict, time_zone=time_zone
        )


        # ******************************************************************* #
        # *********************** synchronization *************************** #
        # ******************************************************************* #

        # get temporal bounds of the long recording
        beginning_datetime_long, ending_datetime_long = \
            self.get_recording_temporal_bounds(signal_dict)

        #: (*list*) Beginning datetimes of the files splitting in the long
        #: recording
        #:
        #: The temporal bounds of the long recording (beginning, ending) are
        #: retrieved with :meth:`.get_recording_temporal_bounds`. The list of
        #: beginning datetimes of the files splitting starts at the beginning
        #: of the long recording and is incremented by
        #: :attr:`.temporal_range_duration`.
        self.ref_beg_datetime_list = []
        ref_datetime = beginning_datetime_long
        while ref_datetime < ending_datetime_long:
            self.ref_beg_datetime_list.append(ref_datetime)
            ref_datetime = ref_datetime + \
                timedelta(seconds=self.temporal_range_duration_split)

        #: (*float*) Temporal range duration of the last file in the long
        #: recording (it might be lower than :attr:`.temporal_range_duration`)
        self.temporal_range_duration_last = (
            ending_datetime_long - self.ref_beg_datetime_list[-1]
        ).total_seconds()

        #: (*float*) Temporal range duration of the current file in the long
        #: recording (equal to :attr:`.temporal_range_duration_last` if last
        #: file, otherwise equal to :attr:`.temporal_range_duration_split`)
        self.temporal_range_duration = None

        #: (*int*) Index of the current file in the long recording
        #:
        #: If :attr:`.flag_long_rec` is ``False``, then :attr:`.ite_file` is
        #: always equal to 0.
        self.ite_file = 0

        #: (*int*) Number of files for splitting the long recording
        #:
        #: If :attr:`.flag_long_rec` is ``False``, then :attr:`.nb_files` is
        #: set to 1.
        self.nb_files = len(self.ref_beg_datetime_list)

        #: (*str*) Directory where to save temporary files for synchronization
        self.synchro_dir = "sig-tmp"

        #: (*str*) Delimiter for parsing temporary files for synchronization
        self.synchro_delimiter = " *=* "

        #: (*list*) Configuration for getting timestamp of temporary
        #: synchronization files (delimiter, index, format)
        self.synchro_timestamp_config = ['_', -1, "%Y-%m-%dT%H-%M-%S"]

        # create temporary directory for temporary synchronization files
        if not os.path.isdir(self.synchro_dir):
            os.mkdir(self.synchro_dir)

        # delete content from temporary directory
        else:
            from shutil import rmtree
            rmtree(self.synchro_dir, ignore_errors=True)
            os.mkdir(self.synchro_dir)

        # synchronize videos, signals and intervals by creating temporary
        # synchronization files
        self.process_synchronization_all()


        # ******************************************************************* #
        # *********************** layout definition ************************* #
        # ******************************************************************* #

        # define window organization if none provided
        if not any(poswid_dict):
            poswid_dict = {}

            # check layout mode
            if layout_mode == 1:
                poswid_dict["video"] = (0, 0, 5, 1)
                poswid_dict['select_from_cursor'] = (0, 1, 1, 6)
                poswid_dict['select_manual'] = (1, 1, 1, 6)
                poswid_dict['annot_event'] = (2, 1, 1, 6)
                poswid_dict['annot_image'] = (3, 1, 1, 6)
                poswid_dict['visi'] = (4, 1)
                poswid_dict['zoomin'] = (4, 2)
                poswid_dict['zoomout'] = (4, 3)
                poswid_dict['previous'] = (4, 4)
                poswid_dict['next'] = (4, 5)
                poswid_dict['file_selection'] = (4, 6)
                poswid_dict['progress'] = (5, 0, 1, 7)

            elif layout_mode == 2:
                poswid_dict["video"] = (0, 0, 4, 1)
                poswid_dict['select_from_cursor'] = (1, 1, 1, 6)
                poswid_dict['select_manual'] = (2, 1, 1, 6)
                poswid_dict['annot_event'] = (0, 7, 4, 1)
                poswid_dict['annot_image'] = (0, 1, 1, 6)
                poswid_dict['visi'] = (3, 1)
                poswid_dict['zoomin'] = (3, 2)
                poswid_dict['zoomout'] = (3, 3)
                poswid_dict['previous'] = (3, 4)
                poswid_dict['next'] = (3, 5)
                poswid_dict['file_selection'] = (3, 6)
                poswid_dict['progress'] = (4, 0, 1, 8)

            elif layout_mode == 3:
                poswid_dict["video"] = (0, 0, 3, 1)
                poswid_dict['annot_event'] = (0, 1, 3, 1)
                poswid_dict['annot_image'] = (0, 2, 1, 3)
                poswid_dict['visi'] = (1, 2)
                poswid_dict['zoomin'] = (1, 3)
                poswid_dict['zoomout'] = (1, 4)
                poswid_dict['previous'] = (2, 2)
                poswid_dict['next'] = (2, 3)
                poswid_dict['file_selection'] = (2, 4)
                poswid_dict['progress'] = (3, 0, 1, 5)

            elif layout_mode == 4:
                poswid_dict['select_from_cursor'] = (0, 0, 1, 6)
                poswid_dict['select_manual'] = (1, 0, 1, 6)
                poswid_dict['annot_image'] = (2, 0, 1, 6)
                poswid_dict['visi'] = (3, 0)
                poswid_dict['zoomin'] = (3, 1)
                poswid_dict['zoomout'] = (3, 2)
                poswid_dict['previous'] = (3, 3)
                poswid_dict['next'] = (3, 4)
                poswid_dict['file_selection'] = (3, 5)
                poswid_dict['annot_event'] = (0, 6, 4, 1)
                poswid_dict["video"] = (4, 0, 1, 7)
                poswid_dict['progress'] = (5, 0, 1, 7)

            else:
                raise Exception(
                    "No layout configuration given - got mode %d, "
                    "must be 1, 2, 3 or 4" % layout_mode
                )


        # ******************************************************************* #
        # *********************** launch ViSiAnnoT ************************** #
        # ******************************************************************* #

        # get configuration dictionaries for first file
        video_dict_current, signal_dict_current, interval_dict_current = \
            self.get_current_file_configuration()

        # lauch ViSiAnnoT
        ViSiAnnoT.__init__(
            self, video_dict_current, signal_dict_current,
            interval_dict=interval_dict_current, poswid_dict=poswid_dict,
            flag_long_rec=True, layout_mode=layout_mode, **kwargs
        )


        # ******************* previous/next recording *********************** #
        if "previous" in poswid_dict.keys():
            #: (:class:`.PreviousWidget`) Widget for selecting previous file
            self.wid_previous = PreviousWidget(
                self, poswid_dict["previous"], "previous"
            )

        else:
            self.wid_previous = None

        if "next" in poswid_dict.keys():
            #: (:class:`.NextWidget`) Widget for selecting next file
            self.wid_next = NextWidget(self, poswid_dict["next"], "next")

        else:
            self.wid_next = None

        if "file_selection" in poswid_dict.keys():
            #: (:class:`.file_selectionWidget`) Widget for selecting a in a
            #: combo box
            self.file_selection_widget = FileSelectionWidget(
                self, poswid_dict["file_selection"]
            )

        else:
            self.file_selection_widget = None


        # *********************** infinite loop ***************************** #
        pyqt_overlayer.infinite_loop_gui(self.app)

        # close streams, delete temporary folders
        self.stop_processing()


    # *********************************************************************** #
    # Group: Methods for finding data files of the long recording
    # *********************************************************************** #


    @staticmethod
    def get_path_list(
        config_id, config, config_type, flag_raise_exception=False,
        **kwargs
    ):
        """
        Gets list of paths and list of beginning datetimes along the recording
        for a specific modality

        :param config_id: configuration key of the modality in the
            configuration dictionary
        :type config_id: str
        :param config: configuration list
        :type config: list
        :param config_type: one of the following: "Video", "Signal" or
            "Interval"
        :type config_type: str
        :param flag_raise_exception: specify if an exception must be raised i
            case no file is found
        :type flag_raise_exception: bool
        :param kwargs: keyword arguments of :func:`.get_datetime_from_path`

        :returns: 2 elements:

            - (*list*) paths to the data files along the recording
            - (*list*) beginning datetimes of the data files along the
              recording
        :rtype: list
        """

        # check number of elements in configuration
        check_configuration(config_id, config, config_type)

        # get configuration
        data_dir, pattern, delimiter, pos, fmt = config[:5]

        # get list of data paths
        path_list = sorted(glob("%s/%s" % (data_dir, pattern)))

        # check if any data file
        if flag_raise_exception and path_list == []:
            raise Exception(
                "Empty directory for %s %s: %s - %s" %
                (config_type, config_id, pattern, data_dir)
            )

        # initialize list of beginning datetime of data files
        datetime_list = []

        # loop on data files paths
        for path in path_list:
            # get beginning datetime of the video file
            beginning_datetime = datetime_converter.get_datetime_from_path(
                path, delimiter, pos, fmt, **kwargs
            )

            # append list
            datetime_list.append(beginning_datetime)

        # sort data paths by chronological order
        sort_indexes = np.argsort(datetime_list)
        path_list = [path_list[i] for i in sort_indexes]
        datetime_list = [datetime_list[i] for i in sort_indexes]

        return [path_list, datetime_list]


    def set_video_list_dict(self, video_dict, **kwargs):
        """
        Finds the list of video files (path and beginning datetime) in the
        long recording

        It sets the attribute :attr:`.video_list_dict`.

        :param video_dict: see first positional argument of
            :class:`.ViSiAnnoTLongRec`
        :type video_dict: dict
        :param kwargs: keyword arguments of :meth:`.get_path_list`
        """

        # initialize dictionaries
        self.video_list_dict = {}

        # loop on cameras
        for ite_id, (video_id, video_config) in enumerate(video_dict.items()):
            # get list of video paths and beginning datetimes
            self.video_list_dict[video_id] = self.get_path_list(
                video_id, video_config, "Video", flag_raise_exception=True,
                **kwargs
            )


    def set_signal_interval_list(self, signal_dict, interval_dict, **kwargs):
        """
        Finds the list of data files (path and beginning datetime) in the
        long recording for signals and intervals

        It sets the attributes :attr:`.signal_list_dict` and
        :attr:`.interval_list_dict`.

        :param signal_dict: see second positional argument of
            :class:`.ViSiAnnoTLongRec`
        :type signal_dict: dict
        :param interval_dict: see keyword argument of
            :class:`.ViSiAnnoTLongRec`
        :type interval_dict: dict
        :param kwargs: keyword arguments of :meth:`.get_path_list`
        """

        # initialize dictionaries
        self.signal_list_dict = {}
        self.interval_list_dict = {}

        # loop on data types
        for signal_id, data_info_list in signal_dict.items():
            # check if there are intervals
            if signal_id in interval_dict.keys():
                # loop on interval configurations for current signal
                interval_list_tmp = []
                for data_info in interval_dict[signal_id]:
                    # get list of interval files
                    interval_list_tmp.append(
                        self.get_path_list(
                            signal_id, data_info, "Interval", **kwargs
                        )
                    )

                self.interval_list_dict[signal_id] = interval_list_tmp

            # loop on signal configurations for current signal
            signal_list_tmp = []
            for data_info in data_info_list:
                signal_list_tmp.append(
                    self.get_path_list(
                        signal_id, data_info, "Signal", **kwargs
                    )
                )

            self.signal_list_dict[signal_id] = signal_list_tmp


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for signal synchronization
    # *********************************************************************** #


    def get_recording_temporal_bounds(self, signal_dict):
        """
        Gets temporal bounds (beginning, ending) of the long recording

        :param signal_dict: see second positional argument of the constructor
            of :class:`.ViSiAnnoTLongRec`
        :type signal_dict: dict

        :returns:
            - **beginning_datetime** (*datetime.datetime*) -- beginning
              datetime of the long recording
            - **ending_datetime** (*datetime.datetime*) -- ending datetime of
              the long recording
        """

        # initialize list of beginning datetime for all modalities
        beg_datetime_list = []

        # initialize list of ending datetime for all modalities
        end_datetime_list = []

        # loop on cameras
        for video_list in self.video_list_dict.values():
            # get beginning datetime of the first video
            beg_datetime_list.append(video_list[1][0])

            # get ending datetime of the last video
            duration = get_duration_video(video_list[0][-1])
            end_datetime = video_list[1][-1] + timedelta(seconds=duration)
            end_datetime_list.append(end_datetime)

        # loop on signals
        for sig_id, signal_list_list in self.signal_list_dict.items():
            for ite_sig, signal_list in enumerate(signal_list_list):
                # get beginning datetime of the signal
                beg_datetime_list.append(signal_list[1][0])

                # get info in order to compute duration of last signal file
                _, _, _, _, _, key, freq, _ = signal_dict[sig_id][ite_sig]

                # get frequency
                freq = self.get_data_frequency(signal_list[0][-1], freq)

                # get duration
                duration = data_loader.get_data_duration(
                    signal_list[0][-1], freq, key=key
                )

                # get ending datetime of the last signal file
                end_datetime = signal_list[1][-1] + timedelta(seconds=duration)
                end_datetime_list.append(end_datetime)

        return min(beg_datetime_list), max(end_datetime_list)


    def process_synchronization_video(self):
        """
        Creates temporary synchronization files for video modality (all
        cameras)

        It updates the attribute :attr:`.video_list_dict` with the paths to the
        temporary synchronization files.
        """

        # loop on cameras
        for video_id, video_list in self.video_list_dict.items():
            # get list of videos paths
            path_list = video_list[0]

            # get list of videos beginning datetime
            beginning_datetime_list = video_list[1]

            # get duration of of video files for first camera
            # (parallelization to improve performance)
            duration_list = []

            # check number of videos
            if len(path_list) > 10:
                # parallelize
                with ProcessPoolExecutor() as executor:
                    for r in executor.map(get_duration_video, path_list):
                        duration_list.append(r)

            else:
                for path in path_list:
                    duration_list.append(get_duration_video(path))

            # loop on video files
            # initialize list of data files ending datetime
            ending_datetime_list = [
                bd + timedelta(seconds=du)
                for bd, du in zip(beginning_datetime_list, duration_list)
            ]

            # create temporary synchronization files
            synchro_path_list = self.create_synchronization_files(
                video_id, "video", path_list, beginning_datetime_list,
                ending_datetime_list
            )

            # update list of data paths
            self.video_list_dict[video_id][0] = synchro_path_list


    def process_synchronization_single_widget(
        self, signal_id, flag_interval=False
    ):
        """
        Creates temporary synchronization files for signals or intervals in a
        specific widget

        It updates the attributes :attr:`.signal_list_dict` and/or
        :attr:`.interval_list_dict` with the paths to synchronization files

        :param signal_id: widget identifier (must be a key in
            :attr:`.signal_list_dict`)
        :type signal_id: str
        :param flag_interval: specify if interval data to synchronize
        :type flag_interval: bool
        """

        # check if interval
        if flag_interval:
            # get list of interval configurations
            config_list = self.interval_config_dict[signal_id]

            # get list of data info (paths and beginning datetimes)
            data_info_list = self.interval_list_dict[signal_id]

            # update signal ID to specify interval data
            signal_id = "interval-%s" % signal_id

        else:
            # get list of signal configurations
            config_list = self.signal_config_dict[signal_id]

            # get list of data info (paths and beginning datetimes)
            data_info_list = self.signal_list_dict[signal_id]

        # loop on sub-data
        for ite_sig, (data_info, config) in enumerate(
            zip(data_info_list, config_list)
        ):
            # get info for current data
            path_list, beginning_datetime_list = data_info
            _, _, _, key, freq, _ = config

            # initialize list of data files ending datetime
            ending_datetime_list = []

            # loop on data paths
            for path, beginning_datetime in zip(
                path_list, beginning_datetime_list
            ):
                # get frequency
                freq = self.get_data_frequency(path, freq)

                # get data file duration
                duration = data_loader.get_data_duration(
                    path, freq, key=key, flag_interval=flag_interval
                )

                # get ending datetime
                ending_datetime_list.append(
                    beginning_datetime + timedelta(seconds=duration)
                )

            # get synchronization files output format
            if freq == 0:
                output_fmt = "2D"

            else:
                output_fmt = "1D"
            
            # create temporary synchronization files
            synchro_path_list = self.create_synchronization_files(
                "%s-%s" % (signal_id, ite_sig), output_fmt, path_list,
                beginning_datetime_list, ending_datetime_list,
            )

            # check if interval data
            if flag_interval:
                # get original signal ID
                signal_id_orig = signal_id.split('-')[1]

                # update list of data paths
                self.interval_list_dict[signal_id_orig][ite_sig][0] = \
                    synchro_path_list
            
            else:
                # update list of data paths
                self.signal_list_dict[signal_id][ite_sig][0] = \
                    synchro_path_list


    def process_synchronization_all(self):
        """
        Creates temporary synchronization files for all videos, signals and
        intervals
        
        It updates the attributes :attr:`.video_list_dict`,
        :attr:`.signal_list_dict` and :attr:`.interval_list_dict` with the
        paths to temporary synchronization files.
        """

        # video synchronization
        self.process_synchronization_video()

        # loop on signal widgets
        for signal_id in self.signal_list_dict.keys():
            # check if any interval in the current widget
            if signal_id in self.interval_list_dict.keys():
                self.process_synchronization_single_widget(
                    signal_id, flag_interval=True
                )

            self.process_synchronization_single_widget(signal_id)


    def create_synchronization_files(
        self, data_name, output_fmt, data_path_list,
        data_beginning_datetime_list, data_ending_datetime_list
    ):
        """
        Creates temporary synchronization files for a given modality

        The reference for synchronization is given by
        :attr:`.ref_beg_datetime_list` and
        :attr:`.temporal_range_duration_split`. A synchronization file is
        created for each element of the list :attr:`.ref_beg_datetime_list`.

        See :ref:`synchro` for an example of temporary synchronization files.

        :param data_name: modality name (used for the output path to temporary
            synchronization file)
        :type data_name: str
        :param output_fmt: synchronization format in the temporary files,
            either "1D", "2D" or anything else, see :ref:`synchro` for details
        :type output_fmt: str
        :param data_path_list: paths to the data files to synchronize
        :type data_path_list: list
        :param data_beginning_datetime_list: instances of datetime.datetime
            with the beginning datetime of each data file to synchronize
        :type data_beginning_datetime_list: list
        :param data_ending_datetime_list: instances of datetime.datetime with
            the ending datetime of each data file to synchronize, same length
            as ``data_beginning_datetime_list``
        :type data_ending_datetime_list: list

        :returns: paths to the created synchronization files
        :rtype: list
        """

        # remove empty data files (where beginning and ending datetimes are the
        # same)
        inds_to_remove = []
        for ite_file, (beginning_datetime, ending_datetime) in enumerate(zip(
            data_beginning_datetime_list, data_ending_datetime_list
        )):
            duration = (ending_datetime - beginning_datetime).total_seconds()
            if duration == 0:
                inds_to_remove.append(ite_file)

        data_beginning_datetime_list = list(np.delete(
            np.array(data_beginning_datetime_list), inds_to_remove
        ))

        data_ending_datetime_list = list(np.delete(
            np.array(data_ending_datetime_list), inds_to_remove
        ))

        data_path_list = list(np.delete(
            np.array(data_path_list), inds_to_remove
        ))

        # initialize list of synchronization files names
        synchro_path_list = []

        # loop on beginning datetimes of reference data files
        for ite, ref_datetime in enumerate(self.ref_beg_datetime_list):
            # get temporal range duration of the file in the long recording
            if ite < len(self.ref_beg_datetime_list) - 1:
                temporal_range_duration = self.temporal_range_duration_split

            else:
                temporal_range_duration = self.temporal_range_duration_last

            # compute difference of beginning datetimes between reference and
            # signal
            start_data_diff_array = np.array([
                (beg_rec - ref_datetime).total_seconds()
                for beg_rec in data_beginning_datetime_list
            ])

            # get signal files sharing temporality with reference data file
            data_file_id_list = np.intersect1d(
                np.where(start_data_diff_array >= 0)[0],
                np.where(start_data_diff_array <= temporal_range_duration)[0]
            )

            # check if there is a signal file beginning before reference data
            # file
            before_ref_data_array = np.where(start_data_diff_array < 0)[0]
            if before_ref_data_array.shape[0] > 0:
                # check length of signal file beginning before reference data
                # file
                if data_ending_datetime_list[before_ref_data_array[-1]] > \
                        ref_datetime:
                    # update list of signal files sharing temporality with
                    # reference data file
                    data_file_id_list = np.hstack((
                        before_ref_data_array[-1], data_file_id_list
                    ))

            # get synchronization file name
            tmp_path = "%s/%s_%s_%s.txt" % (
                self.synchro_dir, os.path.basename(self.synchro_dir),
                data_name, ref_datetime.strftime("%Y-%m-%dT%H-%M-%S")
            )

            synchro_path_list.append(tmp_path)
            with open(tmp_path, 'w') as f:
                for ite_id, data_file_id in enumerate(data_file_id_list):
                    start_sec = start_data_diff_array[data_file_id]
                    data_path = data_path_list[data_file_id]

                    # check output format
                    if output_fmt == "1D":
                        # first data file
                        if ite_id == 0:
                            # check if data file begins before the reference
                            # temporal range
                            if start_sec <= 0:
                                f.write("%s%s%f\n" % (
                                    data_path, self.synchro_delimiter,
                                    -start_sec
                                ))

                            else:
                                f.write("None%s%f\n%s\n" % (
                                    self.synchro_delimiter, start_sec,
                                    data_path
                                ))

                        else:
                            # get beginning datetime of data file
                            beginning_datetime = \
                                data_beginning_datetime_list[data_file_id]

                            # get ending datetime of previous data file
                            prev_datetime = data_ending_datetime_list[
                                data_file_id_list[ite_id - 1]
                            ]

                            # compute temporal gap with previous data file
                            gap = (
                                beginning_datetime - prev_datetime
                            ).total_seconds()
                            
                            if gap > 0:
                                f.write("None%s%f\n" % (
                                    self.synchro_delimiter, gap
                                ))

                            f.write("%s\n" % data_path)

                    elif output_fmt == "2D":
                        f.write("%s%s%f\n" % (
                            data_path, self.synchro_delimiter, start_sec
                        ))

                    else:
                        end_sec = (
                            data_ending_datetime_list[data_file_id] -
                            ref_datetime
                        ).total_seconds()

                        end_sec = min(end_sec, temporal_range_duration)

                        f.write("%s%s%f%s%f\n" % (
                            data_path, self.synchro_delimiter,
                            start_sec, self.synchro_delimiter, end_sec
                        ))

        return synchro_path_list


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for managing the navigation along the recording files
    # *********************************************************************** #


    def get_current_file_configuration(self):
        """
        Gets configuration dictionaries for the current file in the long
        recording to provide to :class:`.ViSiAnnoT`

        It also sets :attr:`.temporal_range_duration` according to the value of
        :attr:`.ite_file`

        :returns:
            - **video_dict** (*dict*) -- video configuration
            - **signal_dict** (*dict*) -- signal configuration
            - **interval_dict** (*dict*) -- interval configuration
        """

        video_dict = {}
        for cam_id, (path_list, _) in self.video_list_dict.items():
            video_dict[cam_id] = \
                [path_list[self.ite_file]] + self.synchro_timestamp_config

        signal_dict = {}
        interval_dict = {}
        for signal_id, data_info_list in self.signal_list_dict.items():
            if signal_id in self.interval_list_dict.keys():
                interval_dict[signal_id] = []
                for (path_list, _), config in zip(
                    self.interval_list_dict[signal_id],
                    self.interval_config_dict[signal_id]
                ):
                    if self.ite_file < len(path_list):
                        interval_dict[signal_id].append(
                            [path_list[self.ite_file]] + config
                        )

            signal_dict[signal_id] = []
            for (path_list, _), config in zip(
                data_info_list, self.signal_config_dict[signal_id]
            ):
                signal_dict[signal_id].append(
                    [path_list[self.ite_file]] + config
                )

        if self.ite_file == self.nb_files - 1:
            self.temporal_range_duration = \
                self.temporal_range_duration_last

        else:
            self.temporal_range_duration = \
                self.temporal_range_duration_split

        return video_dict, signal_dict, interval_dict


    def change_file_in_long_rec(self, ite_file, *args, **kwargs):
        """
        Changes file in the long recording

        It loads new data files by calling
        :meth:`.ViSiAnnoT.prepare_new_file`. Then it updates the
        display with :meth:`.ViSiAnnoT.update_plot_new_frame`.

        :param ite_file: index of the new file in the long recording
        :type ite_file: int
        :param args: positional arguments of
            :meth:`.ViSiAnnoT.update_plot_new_frame`
        :param kwargs: keyword arguments of
            :meth:`.ViSiAnnoT.update_plot_new_frame`

        :returns: specify if the file has been effectively changed
        :rtype: bool
        """

        # disable playback during file changing
        if not self.flag_pause_status:
            flag_reset_pause = True
            self.flag_pause_status = True

        else:
            flag_reset_pause = False

        # set new file
        ok = self.prepare_new_file(ite_file)

        if ok:
            self.update_plot_new_frame(*args, **kwargs)

        if flag_reset_pause:
            self.flag_pause_status = False

        return ok


    def previous_file(self):
        """
        Loads previous file in the long recording
        """

        self.change_file_in_long_rec(
            self.ite_file - 1, self.frame_id + self.nframes,
            flag_previous_scroll=True
        )


    def next_file(self):
        """
        Loads next file in the long recording

        :returns: specify if the file has been effectively changed
        :rtype: bool
        """

        ok = self.change_file_in_long_rec(
            self.ite_file + 1, self.frame_id - self.nframes
        )

        return ok


    def prepare_new_file(self, ite_file):
        """
        Loads data of a new file in the long recording

        It sets the attribute :attr:`.ViSiAnnoT.ite_file`

        It does not set :attr:`.ViSiAnnoT.first_frame` and
        :attr:`.ViSiAnnoT.last_frame`, and it does not update signal plots.

        :param ite_file: index of the new file in the long recording
        :type ite_file: int

        :returns: specify if the new file has been effectively loaded
        :rtype: bool
        """

        # check recording id
        if ite_file >= 0 and ite_file < self.nb_files:
            self.ite_file = ite_file

            video_dict_current, signal_dict_current, interval_dict_current = \
                self.get_current_file_configuration()

            # set new data
            self.set_all_data(
                video_dict_current, signal_dict_current, interval_dict_current
            )

            # update video widget
            for video_id, data_video in self.video_data_dict.items():
                self.wid_vid_dict[video_id].setDataVideo(data_video)

            # set recording choice combo box
            if self.file_selection_widget is not None:
                # to prevent the combo box callback method from being called
                # (which would imply calling method change_file_in_long_rec
                # twice if file selection not done with combo box), the combo
                # box signal is blocked and then unblocked
                self.file_selection_widget.combo_box.blockSignals(True)
                self.file_selection_widget.combo_box.setCurrentIndex(
                    self.ite_file
                )
                self.file_selection_widget.combo_box.blockSignals(False)

            # reset selected item of combo box for temporal range from cursor
            if self.wid_from_cursor is not None:
                self.wid_from_cursor.combo_box.setCurrentIndex(0)

            return True

        else:
            return False


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
