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
        self, video_dict, signal_dict, interval_dict={}, flag_synchro=True,
        layout_mode=1, poswid_dict={}, **kwargs
    ):
        """
        Subclass of :class:`.ViSiAnnoT` for managing a long recording with
        several files

        First, it searches the list of paths to the video/signal files. If
        signals are not synchronized with videos, then it creates temporary
        files with info for synchronization. Each created file corresponds to
        one video file and contains the path to the signal file to use with the
        starting second.

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
        :param flag_synchro: specify if video and signal are synchronized, in
            case there is no video and several signals that are not
            synchronized with each other, then ``flag_synchro`` can be set to
            ``False`` and the synchronization reference is the first signal
        :type flag_synchro: bool
        :param layout_mode: layout mode of the window for positioning the
            widgets, one of the following:

            - ``1`` (focus on video, works better with a big screen),
            - ``2`` (focus on signal, suitable for a laptop screen),
            - ``3`` (compact display with some features disabled).
        :type layout_mode: int
        :param poswid_dict: custom position of the widgets in the window,
            default ``{}`` to use the positions defined by the layout mode (see
            input ``layout_mode``). Value is a tuple of length 2 ``(row, col)``
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
            - ``"previous"``
            - ``"next"``
            - ``"file_selection"``
            - ``"progress"``
        :type poswid_dict: dict
        :param kwargs: keyword arguments of :class:`.ViSiAnnoT` constructor
        """

        # check input dictionaries are empty
        if not any(video_dict) and not any(signal_dict):
            raise Exception("Input dictionaries are empty")

        #: (*bool*) Specify if video and signal are synchronized
        #:
        #: In case there is no video and several signals not synchronized, then
        #: ``synchro`` can be set to False and the synchronization reference is
        #: the first signal
        self.flag_synchro = flag_synchro

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
        self.video_list_dict = {}

        # get list of video paths and beginning datetimes for each camera
        self.set_video_list_dict(video_dict, time_zone=time_zone)

        ###########################
        # get reference frequency #
        ###########################

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
        self.interval_list_dict = {}

        # get list of data paths and beginning datetimes for each signal and
        # interval
        self.set_signal_interval_list(
            signal_dict, interval_dict, time_zone=time_zone
        )

        #: (*str*) Directory where to save temporary files for synchrnonization
        self.tmp_name = "sig-tmp"

        #: (*str*) Delimiter for parsing temporary files for synchronization
        self.tmp_delimiter = " *=* "

        #: (*list*) Beginning datetimes of the files of the reference modality
        self.ref_beg_datetime_list = None

        #: (*list*) Durations of the files of the reference modality
        self.ref_duration_list = None

        # check if asynchronous signals
        print("Synchronized: %d" % self.flag_synchro)
        if not self.flag_synchro:
            # create temporary directory for signals if not synchro with
            # reference modality
            if not os.path.isdir(self.tmp_name):
                os.mkdir(self.tmp_name)

            # delete content from temporary directory
            else:
                from shutil import rmtree
                rmtree(self.tmp_name, ignore_errors=True)
                os.mkdir(self.tmp_name)

            # check if more than one camera
            if len(video_dict) > 1:
                # check for holes in video files (so that the reference
                # modality is not corrupted with holes)
                self.check_holes_video(time_zone=time_zone)

            # synchronize signals and intervals w.r.t. reference modality and
            # create temporary synchronization files
            self.process_synchronization_all()

        else:
            # check for holes in video, signal and interval files
            self.check_holes_video_signal_interval(time_zone=time_zone)


        # ******************************************************************* #
        # *********************** layout definition ************************* #
        # ******************************************************************* #

        # define window organization if none provided
        if not any(poswid_dict):
            poswid_dict = {}
            nb_video = len(video_dict)

            # check layout mode
            if layout_mode == 1:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 5, 1)
                poswid_dict['select_trunc'] = (0, nb_video, 1, 3)
                poswid_dict['select_from_cursor'] = (0, nb_video + 3, 1, 3)
                poswid_dict['select_manual'] = (1, nb_video, 1, 6)
                poswid_dict['annot_event'] = (2, nb_video, 1, 6)
                poswid_dict['annot_image'] = (3, nb_video, 1, 6)
                poswid_dict['visi'] = (4, nb_video)
                poswid_dict['zoomin'] = (4, nb_video + 1)
                poswid_dict['zoomout'] = (4, nb_video + 2)
                poswid_dict['previous'] = (4, nb_video + 3)
                poswid_dict['next'] = (4, nb_video + 4)
                poswid_dict['file_selection'] = (4, nb_video + 5)
                poswid_dict['progress'] = (5, 0, 1, nb_video + 6)

            elif layout_mode == 2:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 4, 1)
                poswid_dict['select_trunc'] = (1, nb_video, 1, 3)
                poswid_dict['select_from_cursor'] = (1, nb_video + 3, 1, 3)
                poswid_dict['select_manual'] = (2, nb_video, 1, 6)
                poswid_dict['annot_event'] = (0, nb_video + 6, 4, 1)
                poswid_dict['annot_image'] = (0, nb_video, 1, 6)
                poswid_dict['visi'] = (3, nb_video)
                poswid_dict['zoomin'] = (3, nb_video + 1)
                poswid_dict['zoomout'] = (3, nb_video + 2)
                poswid_dict['previous'] = (3, nb_video + 3)
                poswid_dict['next'] = (3, nb_video + 4)
                poswid_dict['file_selection'] = (3, nb_video + 5)
                poswid_dict['progress'] = (4, 0, 1, nb_video + 7)

            elif layout_mode == 3:
                for ite_video, video_id in enumerate(video_dict.keys()):
                    poswid_dict[video_id] = (0, ite_video, 3, 1)
                poswid_dict['annot_event'] = (0, nb_video, 3, 1)
                poswid_dict['annot_image'] = (0, nb_video + 1, 1, 3)
                poswid_dict['visi'] = (1, nb_video + 1)
                poswid_dict['zoomin'] = (1, nb_video + 2)
                poswid_dict['zoomout'] = (1, nb_video + 3)
                poswid_dict['previous'] = (2, nb_video + 1)
                poswid_dict['next'] = (2, nb_video + 2)
                poswid_dict['file_selection'] = (2, nb_video + 3)
                poswid_dict['progress'] = (3, 0, 1, nb_video + 4)

            else:
                raise Exception(
                    "No layout configuration given - got mode %d, "
                    "must be 1, 2 or 3" % layout_mode
                )


        # ******************************************************************* #
        # *********************** launch ViSiAnnoT ************************** #
        # ******************************************************************* #

        # get configuration dictionaries for first file
        self.ite_file = 0
        video_dict_current, signal_dict_current, interval_dict_current = \
            self.get_current_file_configuration()

        # lauch ViSiAnnoT
        ViSiAnnoT.__init__(
            self, video_dict_current, signal_dict_current,
            interval_dict=interval_dict_current, poswid_dict=poswid_dict,
            flag_long_rec=True, layout_mode=layout_mode, **kwargs
        )

        # update number of files for reference modality in the recording
        if any(video_dict):
            self.nb_files = len(list(self.video_list_dict.values())[0][0])

        else:
            self.nb_files = len(list(self.signal_list_dict.values())[0][0][0])


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


    @staticmethod
    def check_holes(data_list_dict, **kwargs):
        """
        Checks if there are holes in the list of data files when comparing
        different modalities

        It updates the positional argument ``data_list_dict`` by filling the
        holes with a fake empty data file.

        :param data_list_dict: each item corresponds to one modality - key is
            the modality name - value is a list of length 2:

            - list of paths to data files
            - list of beginning datetimes of data files
        :type data_list_dict: dict
        :param kwargs: keyword arguments of :func:`.convert_string_to_datetime`
        """

        # initialize data file iteration index
        i = 0

        # get list of modalities
        mod_list = list(data_list_dict.keys())

        # loop on data files
        while True:
            # initialize array of beginning datetime of current file for all
            # modalities
            timestamp_array = np.empty((0,))

            # loop on modalities
            for mod in mod_list:
                # get beginning datetime
                if i < len(data_list_dict[mod][1]):
                    ts = data_list_dict[mod][1][i].timestamp()

                else:
                    ts = np.nan

                timestamp_array = np.concatenate((timestamp_array, [ts]))

            # check if no more data files to check
            if np.sum(np.isnan(timestamp_array)) == timestamp_array.shape[0]:
                break

            # get earliest timestamp
            timestamp_first = np.nanmin(timestamp_array)

            # convert to datetime
            datetime_first = datetime_converter.convert_string_to_datetime(
                timestamp_first, "posix", **kwargs
            )

            # compute timestamp difference with earliest timestamp for all
            # modalities
            diff_array = timestamp_array - timestamp_first

            # get modalities with a hole (if delta below 1 second, then
            # considered as OK)
            mod_inds = np.concatenate((
                np.where(diff_array > 1)[0], np.where(np.isnan(diff_array))[0]
            ))

            # loop on modalities with a hole
            for mod_ind in mod_inds:
                # get modality name
                mod = mod_list[mod_ind]

                # insert fake data file to fill the hole
                data_list_dict[mod][0].insert(i, '')
                data_list_dict[mod][1].insert(i, datetime_first)

            # iterate on data files
            i += 1
                

    def check_holes_video(self, **kwargs):
        """
        Checks if there are holes in the list of video files when comparing
        the different cameras

        It updates the attribute :attr:`.video_list_dict` by filling the holes
        with a fake empty video file.

        :param kwargs: keyword arguments of :meth:`.check_holes`
        """

        ViSiAnnoTLongRec.check_holes(self.video_list_dict, **kwargs)


    def check_holes_video_signal_interval(self, **kwargs):
        """
        Checks if there are holes in the list of signal files when comparing
        the different cameras and signals

        :param kwargs: keyword arguments of :meth:`.check_holes`

        It updates the attributes :attr:`.video_list_dict` and
        :attr:`.signal_list_dict` by filling the holes with a fake empty
        video/signal file.
        """

        # concatenate dictionaries with list of data paths and timestamps
        # for video and signal
        data_list_dict = self.video_list_dict.copy()

        for sig_id, data_list_list in self.signal_list_dict.items():
            for ite_sig, data_list in enumerate(data_list_list):
                tmp_sig_id = "%s--%d" % (sig_id, ite_sig)
                data_list_dict[tmp_sig_id] = data_list

            if sig_id in self.interval_list_dict.keys():
                for ite_inter, data_list \
                        in enumerate(self.interval_list_dict[sig_id]):
                    tmp_inter_id = "interval--%s--%d" % (sig_id, ite_inter)
                    data_list_dict[tmp_inter_id] = data_list

        ViSiAnnoTLongRec.check_holes(data_list_dict, **kwargs)

        # update video list dictionary
        for cam_id in self.video_list_dict.keys():
            self.video_list_dict[cam_id] = data_list_dict[cam_id]
            del data_list_dict[cam_id]

        # update signal list dictionary
        for sig_id_full in data_list_dict.keys():
            sig_id_split = sig_id_full.split('--')
            if sig_id_split[0] == "interval":
                sig_id = sig_id_split[1]
                ite_sig = sig_id_split[2]
                ite_sig = int(ite_sig)
                self.interval_list_dict[sig_id][ite_sig] = \
                    data_list_dict[sig_id_full]

            else:
                sig_id = sig_id_split[0]
                ite_sig = sig_id_split[1]
                ite_sig = int(ite_sig)
                self.signal_list_dict[sig_id][ite_sig] = \
                    data_list_dict[sig_id_full]


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


    @staticmethod
    def replace_holes(path_list_list):
        """
        Replaces holes in the list of data paths of first modality with another
        modality

        :param path_list_list: nested list, each element corresponds to one
            modality and is the corresponding list of data paths, first element
            is first modality
        :type path_list_list: list

        :returns: updated list of data paths of first modality
        :rtype: list
        """

        # copy list so that the original one is not modified afterwards
        path_list = list(path_list_list[0])

        hole_inds = np.where(np.array(path_list) == '')[0]
        for hole_ind in hole_inds:
            for path_list_tmp in path_list_list[1:]:
                path_tmp = path_list_tmp[hole_ind]
                if path_tmp != '':
                    path_list[hole_ind] = path_tmp
                    break

        return path_list


    def set_reference_modality_info(self):
        """
        Finds the beginning datetimes and the durations of the files of
        reference modality along the recording

        The reference modality is the first camera, or the first signal
        in case there is no video.

        It sets the attributes :attr:`.ref_beg_datetime_list` and
        :attr:`.ref_duration_list`
        """

        # check if any video => first camera is the reference modality for
        # synchronization
        if any(self.video_list_dict):
            # get list of beginning datetimes for first camera
            self.ref_beg_datetime_list = \
                list(self.video_list_dict.values())[0][1]

            # get list of video paths for first camera
            path_list_list = [pl for pl, _ in self.video_list_dict.values()]
            path_list = ViSiAnnoTLongRec.replace_holes(path_list_list)

            # get duration of of video files for first camera
            # (parallelization to improve performance)
            self.ref_duration_list = []

            # check number of videos
            if len(path_list) > 10:
                # parallelize
                with ProcessPoolExecutor() as executor:
                    for r in executor.map(get_duration_video, path_list):
                        self.ref_duration_list.append(r)

            else:
                for path in path_list:
                    self.ref_duration_list.append(get_duration_video(path))

        # no video => first signal is the reference modality for
        # synchronization
        else:
            # get list beginning datetimes for first signal
            sig_id_0 = list(self.signal_list_dict.keys())[0]
            self.ref_beg_datetime_list = self.signal_list_dict[sig_id_0][0][1]

            # get list of data paths for first signal
            path_list_list = [pl for pl, _ in self.video_list_dict.values()]
            path_list = ViSiAnnoTLongRec.replace_holes(path_list_list)

            # get configuration of first signal
            key = self.signal_config_dict[sig_id_0][0][3]
            freq = self.signal_config_dict[sig_id_0][0][4]

            # initialize list of data files duration for fist signal
            self.ref_duration_list = []

            # loop on data files of first signal
            for path in path_list:
                # get frequency
                freq = self.get_data_frequency(path, freq)

                # get duration
                self.ref_duration_list.append(
                    data_loader.get_data_duration(path, freq, key=key)
                )

            # update configuration of first signal to match temporary
            # synchronization files
            self.signal_config_dict[sig_id_0][0][0] = '_'
            self.signal_config_dict[sig_id_0][0][1] = 2
            self.signal_config_dict[sig_id_0][0][2] = "%Y-%m-%dT%H-%M-%S"


    def process_synchronization_single_widget(
        self, signal_id, flag_interval=False
    ):
        """
        Creates temporary synchronization files for signals or intervals in a
        specific widget and updates the attribute :attr:`.signal_list_dict` or
        :attr:`.interval_list_dict` with the synchronization files

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
            # get list of interval configurations
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
            
            # create temporary synchronization files
            synchro_path_list = ViSiAnnoTLongRec.create_synchronization_files(
                path_list, "%s-%s" % (signal_id, ite_sig),
                self.ref_beg_datetime_list, self.ref_duration_list,
                beginning_datetime_list, ending_datetime_list, self.tmp_name,
                self.tmp_delimiter
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
        Creates temporary synchronization files for all signals and intervals
        and updates the attributes :attr:`.signal_list_dict` and
        :attr:`.interval_list_dict` with the synchronization files

        First it calls :meth:`.set_reference_modality_info`, then it calls
        :meth:`.process_synchronization_single_widget` for each signal
        widget.
        """

        self.set_reference_modality_info()

        # loop on signal widgets
        for signal_id in self.signal_list_dict.keys():
            # check if any interval in the current widget
            if signal_id in self.interval_list_dict.keys():
                self.process_synchronization_single_widget(
                    signal_id, flag_interval=True
                )

            self.process_synchronization_single_widget(signal_id)


    @staticmethod
    def create_synchronization_files(
        data_path_list, signal_id, ref_beginning_datetime_list,
        ref_duration_list, data_beginning_datetime_list,
        data_ending_datetime_list, output_dir, delimiter
    ):
        """
        Class method for creating synchronization files

        The reference for synchronization is given by
        ``ref_beginning_datetime_list`` and ``ref_duration_list``. A
        synchronization file is created for each element of those lists.

        An example of synchronization file::

            None *=* 30
            dir/file1.h5

        It means that for the first 30 seconds there is no signal, then there
        is the file "signal dir/file1.h5" until the end of the reference file
        is reached.

        Another example::

            dir/file2.h5 *=* 50
            dir/file3.h5
            dir/file4.h5

        It means that the first 50 seconds of the file "dir/file2.h5" are
        excluded, then there is the full file "dir/file3.h5", then there is the
        file "dir/file4.h5" until the end of the reference file is reached.

        :param data_path_list: paths to the data files to synchronize
        :type data_path_list: list
        :param signal_id: signal identifier, used for the name of the
            synchronization files
        :type signal_id: str
        :param ref_beginning_datetime_list: instances of datetime.datetime with
            the beginning datetime of each reference file
        :type ref_beginning_datetime_list: list
        :param ref_duration_list: durations of each reference file in seconds,
            same length as ``ref_beginning_datetime_list``
        :type ref_duration_list: list
        :param data_beginning_datetime_list: instances of datetime.datetime
            with the beginning datetime of each data file to synchronize
        :type data_beginning_datetime_list: list
        :param data_ending_datetime_list: instances of datetime.datetime with
            the ending datetime of each data file to synchronize, same length
            as ``data_beginning_datetime_list``
        :type data_ending_datetime_list: list
        :param output_dir: directory where to save the synchronization files
        :type output_dir: str
        :param delimiter: delimiter between data path and starting second in
            the synchronization file, in the examples above it is ``" *=* "``
        :type delimiter: str

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

        for ind in inds_to_remove:
            data_beginning_datetime_list.pop(ind)
            data_ending_datetime_list.pop(ind)

        # initialize list of synchronization files names
        synchro_path_list = []

        # loop on beginning datetimes of reference data files
        for ref_datetime, ref_duration \
                in zip(ref_beginning_datetime_list, ref_duration_list):
            # compute difference of beginning datetimes between reference and
            # signal
            start_sig_diff_array = np.array([
                (beg_rec - ref_datetime).total_seconds()
                for beg_rec in data_beginning_datetime_list
            ])

            # get signal files sharing temporality with reference data file
            sig_file_id_list = np.intersect1d(
                np.where(start_sig_diff_array >= 0)[0],
                np.where(start_sig_diff_array <= ref_duration)[0]
            )

            # check if there is a signal file beginning before reference data
            # file
            before_ref_sig_array = np.where(start_sig_diff_array < 0)[0]
            if before_ref_sig_array.shape[0] > 0:
                # check length of signal file beginning before reference data
                # file
                if data_ending_datetime_list[before_ref_sig_array[-1]] > \
                        ref_datetime:
                    # update list of signal files sharing temporality with
                    # reference data file
                    sig_file_id_list = np.hstack((
                        before_ref_sig_array[-1], sig_file_id_list
                    ))

            # get synchronization file name
            tmp_path = "%s/%s_%s_%s.txt" % (
                output_dir, output_dir, signal_id,
                ref_datetime.strftime("%Y-%m-%dT%H-%M-%S")
            )

            synchro_path_list.append(tmp_path)
            with open(tmp_path, 'w') as f:
                for ite_id, sig_file_id in enumerate(sig_file_id_list):
                    # check first signal file
                    if ite_id == 0:
                        # if first signal file begins before the reference data
                        # file
                        if start_sig_diff_array[sig_file_id] < 0:
                            # in case of TQRS, start second is computed from
                            #: the very beginning
                            start_sec = int((
                                ref_datetime -
                                data_beginning_datetime_list[sig_file_id]
                            ).total_seconds())

                            start_sig_file = data_path_list[sig_file_id]

                            f.write("%s%s%d\n" % (
                                start_sig_file, delimiter, start_sec
                            ))

                        else:
                            start_sec = int((
                                data_beginning_datetime_list[sig_file_id] -
                                ref_datetime
                            ).total_seconds())

                            end_sig_file = data_path_list[sig_file_id]

                            f.write("None%s%d\n%s\n" % (
                                delimiter, start_sec, end_sig_file
                            ))

                    else:
                        f.write("%s\n" % data_path_list[sig_file_id])

        return synchro_path_list


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for managing the navigation along the recording files
    # *********************************************************************** #


    def get_current_file_configuration(self):
        """
        Gets configuration dictionaries for the current file in the recording
        to provide to :class:`.ViSiAnnoT`

        :returns:
            - **video_dict** (*dict*) -- video configuration
            - **signal_dict** (*dict*) -- signal configuration
            - **interval_dict** (*dict*) -- interval configuration
        """

        video_dict = {}
        for cam_id, (path_list, _) in self.video_list_dict.items():
            video_dict[cam_id] = \
                [path_list[self.ite_file]] + self.video_config_dict[cam_id]

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

        return video_dict, signal_dict, interval_dict


    def change_file_in_long_rec(
        self, ite_file, new_frame_id, flag_previous_scroll=False
    ):
        """
        Changes file in the long recording

        It loads new data files by calling
        :meth:`.ViSiAnnoTLongRec.prepare_new_file`. Then it updates the
        display.

        :param ite_file: index of the new file in the long recording
        :type ite_file: int
        :param new_frame_id: new current frame number (sampled at the
            reference frequency :attr:`.ViSiAnnoT.fps`)
        :type new_frame_id: int
        :param flag_previous_scroll: specify if the new file is reach backward
            by scrolling
        :type flag_previous_scroll: bool

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
            # reset previous frame id
            for wid_vid in self.wid_vid_dict.values():
                wid_vid.previous_frame_id = None

            # update frame id
            self.update_frame_id(new_frame_id)

            # new temporal range
            current_range = self.last_frame - self.first_frame
            if not flag_previous_scroll:
                self.first_frame = 0
                self.last_frame = min(current_range, self.nframes)
            else:
                self.first_frame = max(0, self.nframes - current_range)
                self.last_frame = self.nframes

            # update progress bar
            self.wid_progress.updateFromViSiAnnoT(
                self.nframes, self.first_frame, self.last_frame, self.fps,
                self.beginning_datetime
            )

            # update signals plot
            self.update_signal_plot()

            # update annotation regions plot if necessary
            if self.wid_annotevent is not None:
                if self.wid_annotevent.push_text_list[3].text() == "On":
                    self.wid_annotevent.clear_regions(self)
                    self.wid_annotevent.description_dict = {}
                    self.wid_annotevent.plot_regions(self)

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

            # loop on cameras
            for cam_id, config in video_dict_current.items():
                # set video widget title
                self.wid_vid_dict[cam_id].setWidgetTitle(config[0])

            # set new data
            self.set_all_data(
                video_dict_current, signal_dict_current, interval_dict_current
            )

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

            # set items of combo box for truncated temporal ranges
            if self.wid_trunc is not None:
                self.wid_trunc.set_trunc(self)

            # reset selected item of combo box for temporal range from cursor
            if self.wid_from_cursor is not None:
                self.wid_from_cursor.combo_box.setCurrentIndex(0)

            return True

        else:
            return False


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
