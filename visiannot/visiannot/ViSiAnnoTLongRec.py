# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
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
from ..tools import ToolsPyQt
from ..tools import ToolsDateTime
from ..tools import ToolsData
from ..tools import ToolsImage
from ..tools import ToolsAudio
from .ViSiAnnoT import ViSiAnnoT, checkConfiguration
from .components.LogoWidgets import PreviousWidget, NextWidget
from .components.FileSelectionWidget import FileSelectionWidget


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
                        "path/to/folder1", "", 50, "*_motion.txt", '_', 1,
                        "%Y-%m-%dT%H-%M-%S", None
                    ]
                ],
                "sig_2": [
                    [
                        "path/to/folder2", "ecg", 0, "*_physio.h5", '_', 0,
                        "posix", {'pen': {'color': 'm', 'width': 1}
                    ],
                    [
                        "path/to/folder2", "resp", -1, "*_physio.h5", '_', 0,
                        "posix",None
                    ]
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
                "Audio L": [[
                    "path/to/folder", "Left channel", 0, "*_audio.wav", '_',
                    1, "%Y-%m-%dT%H-%M-%S", None
                ]],
                "Audio R": [[
                    "path/to/folder", "Right channel", 0, "*_audio.wav", '_',
                    1, "%Y-%m-%dT%H-%M-%S", None]]
                }
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
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int*) Signal frequency, set it to ``-1`` if same frequency as
              :attr:`.ViSiAnnoT.fps`, it may be a string with the path to the
              frequency attribute in a .h5 file,
            - (*str*) Pattern to find interval files,
            - (*str*) Delimiter to get beginning datetime in the interval file
              name,
            - (*int*) Position of the beginning datetime in the interval file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the interval file
              name (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
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
            - ``3`` (compact display with some features disabled),
            - ``4`` (even more compact display, image extraction tool is
              disabled).
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
        self.setVideoListDict(video_dict, time_zone=time_zone)

        # check if more than one camera
        if len(video_dict) > 1:
            # check for "holes" in videos
            self.checkVideoHoles()

        ###########################
        # get reference frequency #
        ###########################

        # check if any video
        if any(video_dict):
            # get fps
            ite_vid = 0
            cam_id_0 = list(video_dict.keys())[0]
            self.fps = 0
            while self.fps <= 0:
                _, _, self.fps = ToolsImage.getDataVideo(
                    self.video_list_dict[cam_id_0][0][ite_vid]
                )

                ite_vid += 1

        # no video
        else:
            # get first signal configuration
            signal_id = list(signal_dict.keys())[0]
            signal_config = list(signal_dict.values())[0][0]

            # check number of elements in first signal configuration
            checkConfiguration(signal_id, signal_config, "Signal")

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
            self.fps = self.getDataFrequency(data_list_tmp[0], freq)


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
        #: list of signal paths and list of
        #: beginning datetimes
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
        self.setSignalIntervalList(
            signal_dict, interval_dict, time_zone=time_zone
        )

        #: (*str*) Directory where to save temporary files for synchrnonization
        self.tmp_name = "sig-tmp"

        #: (*str*) Delimiter for parsing temporary files for synchronization
        self.tmp_delimiter = " *=* "

        self.ref_beg_datetime_list = None
        self.ref_duration_list = None

        # check if asynchronous signals
        print("Synchronized: %d" % self.flag_synchro)
        if not self.flag_synchro:
            # create temporary directory for signals if not synchro with video
            if not os.path.isdir(self.tmp_name):
                os.mkdir(self.tmp_name)

            # delete content from temporary directory
            else:
                from shutil import rmtree
                rmtree(self.tmp_name, ignore_errors=True)
                os.mkdir(self.tmp_name)

            # synchronize signals and intervals w.r.t. video and create
            # temporary synchronization files
            self.processSynchronizationAll()


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
            self.getCurrentFileConfiguration()

        # lauch ViSiAnnoT
        ViSiAnnoT.__init__(
            self, video_dict_current, signal_dict_current,
            interval_dict=interval_dict_current, poswid_dict=poswid_dict,
            flag_long_rec=True, layout_mode=layout_mode, **kwargs
        )

        # udpate number of recordings
        self.nb_files = len(self.ref_beg_datetime_list)


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
            #: (:class:`.FileSelectionWidget`) Widget for selecting a in a
            #: combo box
            self.file_selection_widget = FileSelectionWidget(
                self, poswid_dict["file_selection"]
            )

        else:
            self.file_selection_widget = None


        # *********************** infinite loop ***************************** #
        ToolsPyQt.infiniteLoopDisplay(self.app)

        # close streams, delete temporary folders
        self.stopProcessing()


    # *********************************************************************** #
    # Group: Methods for finding data files of the long recording
    # *********************************************************************** #


    @staticmethod
    def getPathList(
        config_id, config_list, config_type, flag_raise_exception=False,
        **kwargs
    ):
        # check number of elements in configuration
        checkConfiguration(config_id, config_list, config_type)

        # get configuration
        data_dir, pattern, delimiter, pos, fmt = config_list[:5]

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
            beginning_datetime = ToolsDateTime.getDatetimeFromPath(
                path, delimiter, pos, fmt, **kwargs
            )

            # append list
            datetime_list.append(beginning_datetime)

        # sort data paths by chronological order
        sort_indexes = np.argsort(datetime_list)
        path_list = [path_list[i] for i in sort_indexes]
        datetime_list = [datetime_list[i] for i in sort_indexes]

        return [path_list, datetime_list]


    def setVideoListDict(self, video_dict, **kwargs):
        """
        It sets the following attribute :attr:`.video_list_dict`
        """

        # initialize dictionaries
        self.video_list_dict = {}

        # loop on cameras
        for ite_id, (video_id, video_config) in enumerate(video_dict.items()):
            # get list of video paths and beginning datetimes
            self.video_list_dict[video_id] = self.getPathList(
                video_id, video_config, "Video", flag_raise_exception=True,
                **kwargs
            )


    def checkVideoHoles(self):
        """
        It updates the following attribute :attr:`.video_list_dict`
        """

        # get maximum number of video files with regard to camera
        nb_vid_max = max(
            [len(v_list[0]) for v_list in self.video_list_dict.values()]
        )

        # get list of camera IDs
        cam_id_list = list(self.video_list_dict.keys())

        # get first camera ID
        cam_id_0 = cam_id_list[0]

        # loop on video files
        for ite_vid in range(nb_vid_max):
            # loop on cameras (skipping first camera because of reference)
            for cam_id in cam_id_list[1:]:
                flag_missing_first = False
                flag_missing_current = False

                # check if above first camera range
                if ite_vid >= len(self.video_list_dict[cam_id_0][0]):
                    flag_missing_first = True

                elif ite_vid >= len(self.video_list_dict[cam_id][0]):
                    flag_missing_current = True

                else:
                    # get delta in seconds between the current camera and
                    # the first camera
                    delta = (
                        self.video_list_dict[cam_id][1][ite_vid] -
                        self.video_list_dict[cam_id_0][1][ite_vid]
                    ).total_seconds()

                    # check if delta is more than 1 second
                    if abs(delta) > 1:
                        # check if missing file for current camera
                        if delta > 0:
                            flag_missing_current = True

                        # missing file for first camera
                        else:
                            flag_missing_first = True

                # check if missing camera
                if flag_missing_first or flag_missing_current:
                    if flag_missing_current:
                        cam_id_hole = cam_id
                        cam_id_comp = cam_id_0

                    else:
                        cam_id_hole = cam_id_0
                        cam_id_comp = cam_id

                    # insert fake video file to fill the hole
                    self.video_list_dict[cam_id_hole][0].insert(ite_vid, '')
                    self.video_list_dict[cam_id_hole][1].insert(
                        ite_vid, self.video_list_dict[cam_id_comp][1][ite_vid]
                    )


    def setSignalIntervalList(self, signal_dict, interval_dict, **kwargs):
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
                        self.getPathList(
                            signal_id, data_info, "Interval", **kwargs
                        )
                    )

                self.interval_list_dict[signal_id] = interval_list_tmp

            # loop on signal configurations for current signal
            signal_list_tmp = []
            for data_info in data_info_list:
                signal_list_tmp.append(
                    self.getPathList(signal_id, data_info, "Signal", **kwargs)
                )

            self.signal_list_dict[signal_id] = signal_list_tmp


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Methods for signal synchronization
    # *********************************************************************** #


    def setReferenceModalityInfo(self):
        """
        It sets the attributes :attr:`.ref_beg_datetime_list` and
        :attr:`.ref_duration_list`
        """

        # check if any video => first camera is the reference modality for
        # synchronization
        if any(self.video_list_dict):
            # get list of paths and beginning datetime for first camera
            cam_id_0 = list(self.video_list_dict.keys())[0]
            path_list = self.video_list_dict[cam_id_0][0]
            self.ref_beg_datetime_list = self.video_list_dict[cam_id_0][1]

            # initialize list of videos duration for fist camera
            self.ref_duration_list = []

            # loop on videos of first camera
            for path in path_list:
                # get video information
                _, nframes, fps = ToolsImage.getDataVideo(path)

                # check fps
                if fps > 0:
                    # get duration
                    self.ref_duration_list.append(nframes / fps)

                else:
                    self.ref_duration_list.append(0)

        # no video => first signal is the reference modality for
        # synchronization
        else:
            # get list of paths and beginning datetime for first signal
            sig_id_0 = list(self.signal_list_dict.keys())[0]
            path_list = self.signal_list_dict[sig_id_0][0][0]
            self.ref_beg_datetime_list = self.signal_list_dict[sig_id_0][0][1]

            # get configuration of first signal
            key = self.signal_config_dict[sig_id_0][0][3]
            freq = self.signal_config_dict[sig_id_0][0][4]

            # initialize list of data files duration for fist signal
            self.ref_duration_list = []

            # loop on data files of first signal
            for path in path_list:
                # get frequency
                freq = self.getDataFrequency(path, freq)

                # get duration
                self.ref_duration_list.append(
                    ToolsData.getDataDuration(path, freq, key=key)
                )

            # update configuration of first signal to match temporary
            # synchronization files
            self.signal_config_dict[sig_id_0][0][0] = '_'
            self.signal_config_dict[sig_id_0][0][1] = 2
            self.signal_config_dict[sig_id_0][0][2] = "%Y-%m-%dT%H-%M-%S"


    def setSynchronizationTemporaryPaths(self, signal_id, flag_interval=False):
        # check if interval
        if flag_interval:
            # specify interval in data type for the temporary synchronization
            # file
            signal_id = "interval-%s" % signal_id

            # get list of interval configurations
            config_list = self.interval_config_dict[signal_id]

            # get list of data info (paths and beginning datetimes)
            data_info_list = self.interval_list_dict[signal_id]

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
                freq = self.getDataFrequency(path, freq)

                # get data file duration
                duration = ToolsData.getDataDuration(
                    path, freq, key=key, flag_interval=flag_interval
                )

                # get ending datetime
                ending_datetime_list.append(
                    beginning_datetime + timedelta(seconds=duration)
                )
            
            # create temporary synchronization files    
            synchro_path_list = self.createSynchronizationFiles(
                path_list, signal_id, key, self.ref_beg_datetime_list,
                self.ref_duration_list, beginning_datetime_list,
                ending_datetime_list, self.tmp_name, self.tmp_delimiter
            )

            # update list of data paths
            if flag_interval:
                self.interval_list_dict[signal_id][ite_sig][0] = \
                    synchro_path_list
            
            else:
                self.signal_list_dict[signal_id][ite_sig][0] = \
                    synchro_path_list


    def processSynchronizationAll(self):
        self.setReferenceModalityInfo()

        # loop on signal widgets
        for signal_id in self.signal_list_dict.keys():
            # check if any interval in the current widget
            if signal_id in self.interval_list_dict.keys():
                self.setSynchronizationTemporaryPaths(
                    signal_id, flag_interval=True
                )

            self.setSynchronizationTemporaryPaths(signal_id)


    @staticmethod
    def createSynchronizationFiles(
        data_path_list, signal_id, key_data, ref_beginning_datetime_list,
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
        :param signal_id: signal type, used for the name of the synchronization
            files
        :type signal_id: str
        :param key_data: key to access data (in case of .h5 or .mat files),
            used for the name of the synchronization files
        :type key_data: str
        :param ref_beginning_datetime_list: instances of datetime.datetime with
            the beginning datetime of each reference file
        :type ref_beginning_datetime_list: list
        :param ref_duration_list: durations of each reference file in seconds
        :type ref_duration_list: list
        :param data_beginning_datetime_list: instances of datetime.datetime
            with the beginning datetime of each data file to synchronize
        :type data_beginning_datetime_list: list
        :param data_ending_datetime_list: instances of datetime.datetime with
            the ending datetime of each data file to synchronize
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
            tmp_file_name = "%s/%s_%s-%s_%s.txt" % \
                (output_dir, output_dir, signal_id, key_data.replace('/', '_'),
                 ToolsDateTime.convertDatetimeToString(ref_datetime, fmt=1)
                 )

            synchro_path_list.append(tmp_file_name)
            with open(tmp_file_name, 'w') as f:
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


    def getCurrentFileConfiguration(self):
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
                        self.interval_list_dict[signal_id].append(
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


    def changeFileInLongRec(
        self, ite_file, new_frame_id, flag_previous_scroll=False
    ):
        """
        Changes file in the long recording

        It loads new data files by calling
        :meth:`.ViSiAnnoTLongRec.prepareNewFile`. Then it updates the
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
        ok = self.prepareNewFile(ite_file)

        if ok:
            # reset previous frame id
            for wid_vid in self.wid_vid_dict.values():
                wid_vid.previous_frame_id = None

            # update frame id
            self.updateFrameId(new_frame_id)

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
            self.updateSignalPlot()

            # update annotation regions plot if necessary
            if self.wid_annotevent is not None:
                if self.wid_annotevent.push_text_list[3].text() == "On":
                    self.wid_annotevent.clearRegions(self)
                    self.wid_annotevent.description_dict = {}
                    self.wid_annotevent.plotRegions(self)

        if flag_reset_pause:
            self.flag_pause_status = False

        return ok


    def previousFile(self):
        """
        Loads previous file in the long recording
        """

        self.changeFileInLongRec(
            self.ite_file - 1, self.frame_id + self.nframes,
            flag_previous_scroll=True
        )


    def nextFile(self):
        """
        Loads next file in the long recording

        :returns: specify if the file has been effectively changed
        :rtype: bool
        """

        ok = self.changeFileInLongRec(
            self.ite_file + 1, self.frame_id - self.nframes
        )

        return ok


    def prepareNewFile(self, ite_file):
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
                self.getCurrentFileConfiguration()

            # loop on cameras
            for cam_id, config in video_dict_current.items():
                # set video widget title
                self.wid_vid_dict[cam_id].setWidgetTitle(config[0])

            # set new data
            self.setAllData(
                video_dict_current, signal_dict_current, interval_dict_current
            )

            # set recording choice combo box
            if self.file_selection_widget is not None:
                # to prevent the combo box callback method from being called
                # (which would imply calling method changeFileInLongRec twice
                # if file selection not done with combo box), the combo box
                # signal is blocked and then unblocked
                self.file_selection_widget.combo_box.blockSignals(True)
                self.file_selection_widget.combo_box.setCurrentIndex(
                    self.ite_file
                )
                self.file_selection_widget.combo_box.blockSignals(False)

            # set items of combo box for truncated temporal ranges
            if self.wid_trunc is not None:
                self.wid_trunc.setTrunc(self)

            # reset selected item of combo box for temporal range from cursor
            if self.wid_from_cursor is not None:
                self.wid_from_cursor.combo_box.setCurrentIndex(0)

            return True

        else:
            return False


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
