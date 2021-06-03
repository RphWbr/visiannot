# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1
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
import sys
from collections import OrderedDict
from ..tools import ToolsPyQt
from ..tools import ToolsPyqtgraph
from ..tools import ToolsDateTime
from ..tools import ToolsData
from ..tools import ToolsImage
from ..tools import ToolsAudio
from .ViSiAnnoT import ViSiAnnoT


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
            - (*str*) Key to access the data (in case of .mat or .h5 file),
            - (*int* or *float* or *str*) Signal frequency, set it to ``0`` if
              signal non regularly sampled, set it to ``-1`` if same frequency
              as :attr:`.ViSiAnnoT.fps`, it may be a string with the path to
              the frequency attribute in a .h5 file,
            - (*str*) Pattern to find signal files,
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
            - ``"rec_choice"``
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
        # ****************** search for video paths ************************* #
        # ******************************************************************* #

        #: (*dict*) Key is a camera ID. Value is a list along the video files
        #: in the long recording, where each element is a configuration list
        #: (see first positional argument of :class:`.ViSiAnnoT` constructor
        #: for details about configuration list)
        self.video_dict_list = OrderedDict()

        # dictionary containing the current video file path
        video_dict_current = OrderedDict()

        # nested list of video paths
        video_path_list = []

        # nested list of beginning datetime of video files
        video_datetime_list = []

        # nested list of duration of video files
        video_duration_list = []

        # loop on cameras
        for ite_id, (video_id, (dir_video, pattern, delimiter, pos, fmt)) in \
                enumerate(video_dict.items()):
            # get list of video paths for current camera
            video_path_list_tmp = sorted(glob("%s/%s" % (dir_video, pattern)))

            # check if any video file
            if video_path_list_tmp == []:
                raise Exception(
                    "Wrong input video directory for video %s - %s" %
                    (video_id, dir_video)
                )

            # initialize list of beginning datetime of video files for current
            # camera
            video_datetime_list_tmp = []

            # initialize list of duration of video files for current camera
            video_duration_list_tmp = []

            # loop on paths
            for video_path in video_path_list_tmp:
                # get beginning datetime of the video file
                beginning_datetime = ToolsDateTime.getDatetimeFromPath(
                    video_path, delimiter, pos, fmt, time_zone=time_zone
                )

                # append list
                video_datetime_list_tmp.append(beginning_datetime)

                # get information for video duration
                _, nframes, fps = ToolsImage.getDataVideo(video_path)

                # check fps
                if fps > 0:
                    # append list of video duration
                    video_duration_list_tmp.append(nframes / fps)

                    # store fps as an attribute
                    if not hasattr(self, "fps"):
                        self.fps = fps

                else:
                    # append list of video duration
                    video_duration_list_tmp.append(0)

            # sort video paths by chronological order
            sort_indexes = np.argsort(video_datetime_list_tmp)

            # append lists
            video_path_list.append(
                [video_path_list_tmp[i] for i in sort_indexes]
            )

            video_datetime_list.append(
                [video_datetime_list_tmp[i] for i in sort_indexes]
            )

            video_duration_list.append(
                [video_duration_list_tmp[i] for i in sort_indexes]
            )

        # check if more than one camera
        # then check for "holes" in cameras
        if len(video_dict) > 1:
            # get maximum number of video files with regard to camera
            nb_vid_max = max([len(sub_list) for sub_list in video_path_list])

            # get number of cameras
            nb_camera = len(video_dict)

            # loop on video files
            for ite_vid in range(nb_vid_max):
                # loop on cameras (skipping first camera because of reference)
                for ite_id in range(1, nb_camera):
                    # get delta in seconds between the current camera and the
                    # first camera
                    delta = (
                        video_datetime_list[ite_id][ite_vid] -
                        video_datetime_list[0][ite_vid]
                    ).total_seconds()

                    # check if delta is more than 1 second
                    if abs(delta) > 1:
                        # check if missing file for current camera
                        if delta > 0:
                            ite_id_tmp = ite_id
                            ite_id_tmp_comp = 0

                        # missing file for first camera
                        else:
                            ite_id_tmp = 0
                            ite_id_tmp_comp = ite_id

                        # insert fake video file to fill the hole
                        video_path_list[ite_id_tmp].insert(ite_vid, '')

                        video_datetime_list[ite_id_tmp].insert(
                            ite_vid,
                            video_datetime_list[ite_id_tmp_comp][ite_vid]
                        )

                        video_duration_list[ite_id_tmp].insert(
                            ite_vid,
                            video_duration_list[ite_id_tmp_comp][ite_vid]
                        )

        # update dictionaries
        for ite_id, video_id in enumerate(video_dict.keys()):
            self.video_dict_list[video_id] = [
                [
                    path, video_dict[video_id][2],
                    video_dict[video_id][3], video_dict[video_id][4]
                ] for path in video_path_list[ite_id]
            ]

            video_dict_current[video_id] = self.video_dict_list[video_id][0]


        # ******************************************************************* #
        # ****************** get files beginning time *********************** #
        # ******************************************************************* #

        #: (*list*) Instances of datetime.datetime with the beginning datetime
        #: of each video file (or first signal if no video)
        #:
        #: The list of video files that is used is in the first value of
        #: :attr:`.ViSiAnnoTLongRec.video_dict_list`
        #: (or :attr:`.ViSiAnnoTLongRec.signal_dict_list` in case
        #: :attr:`.ViSiAnnoTLongRec.video_dict_list` is empty).
        self.rec_beginning_datetime_list = []

        #: (*list*) Durations in seconds of each video file (or first signal if
        #: no video)
        self.rec_duration_list = []

        # check if there is any video
        if any(self.video_dict_list):
            self.rec_beginning_datetime_list = video_datetime_list[0]
            self.rec_duration_list = video_duration_list[0]

        # no video
        else:
            # get info for first signal
            data_dir, key_data, freq, path_pattern_data, delimiter, pos, fmt, \
                _ = list(signal_dict.values())[0][0]

            # get list of signal files paths
            data_list_tmp = sorted(
                glob('%s/%s' % (data_dir, path_pattern_data))
            )

            # check if any file
            if len(data_list_tmp) == 0:
                raise Exception(
                    "Empty directory for first signal: %s - %s" %
                    (data_dir, path_pattern_data)
                )

            # store frequency as an attribute
            if isinstance(freq, str):
                self.fps = ToolsData.getAttributeGeneric(
                    data_list_tmp[0], freq
                )

            else:
                self.fps = freq

            # loop on signal files
            for path in data_list_tmp:
                # get data length
                data = ToolsData.getDataGeneric(path, key_data)

                if data is not None:
                    nframes = data.shape[0]

                    # get beginning datetime
                    date_time = ToolsDateTime.getDatetimeFromPath(
                        path, delimiter, pos, fmt, time_zone=time_zone
                    )

                    # append lists
                    self.rec_duration_list.append(nframes / self.fps)
                    self.rec_beginning_datetime_list.append(date_time)

            # sort signal paths by chronological order
            sort_indexes = np.argsort(self.rec_beginning_datetime_list)

            self.rec_beginning_datetime_list = [
                self.rec_beginning_datetime_list[i] for i in sort_indexes
            ]

            self.rec_duration_list = [
                self.rec_duration_list[i] for i in sort_indexes
            ]


        # ******************************************************************* #
        # ******************* search for signal files *********************** #
        # ******************************************************************* #

        #: (*str*) Directory where to save temporary files for synchrnonization
        self.tmp_name = "sig-tmp"

        #: (*str*) Delimiter for parsing temporary files for synchronization
        self.tmp_delimiter = " *=* "

        # check if asynchronous signals
        if not self.flag_synchro:
            # create temporary directory for signals if not synchro with video
            if not os.path.isdir(self.tmp_name):
                os.mkdir(self.tmp_name)

            # delete content from temporary directory
            else:
                from shutil import rmtree
                rmtree(self.tmp_name, ignore_errors=True)
                os.mkdir(self.tmp_name)

        print("Synchronized: %d" % self.flag_synchro)

        #: (*dict*) Each item corresponds to one signal widget, key is the data
        #: type of the widget, value is a nested list of signal configurations
        #:
        #: Each element of the nested list corresponds to one signal plot and
        #: is a list along the signal files in the long recording, where each
        #: element is a configuration list (see second positional argument of
        #: :class:`.ViSiAnnoT` constructor for details about the configuration
        #: list).
        self.signal_dict_list = OrderedDict()

        #: (*dict*) Each item corresponds to one signal widget on which to plot
        #: intervals, key is the data type of the widget, value is a nested
        #: list of interval configurations.
        #:
        #: Each element of the nested list corresponds to one type of interval
        #: and is a list along the interval files in the long recording, where
        #: each element is a configuration list (see second keyword argument
        #: ``interval_dict`` of :class:`.ViSiAnnoT` constructor for details
        #: about the configuration list).
        self.interval_dict_list = OrderedDict()

        # get signal configuration
        signal_dict_current, interval_dict_current = \
            self.getSignalConfigurationAllTypes(
                signal_dict, interval_dict, time_zone=time_zone
            )


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
                poswid_dict['rec_choice'] = (4, nb_video + 5)
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
                poswid_dict['rec_choice'] = (3, nb_video + 5)
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
                poswid_dict['rec_choice'] = (2, nb_video + 3)
                poswid_dict['progress'] = (3, 0, 1, nb_video + 4)

            else:
                raise Exception("No layout configuration given - got mode %d, must be 1, 2 or 3" % layout_mode)


        # ******************************************************************* #
        # *********************** launch ViSiAnnoT ************************** #
        # ******************************************************************* #

        # check if any video
        if any(video_dict_current):
            #: (*str*) Base name of the annotation files
            #:
            #: Label and annotation type is added when loading/saving
            #: annotation files)
            self.annot_file_base = os.path.splitext(
                os.path.basename(list(video_dict_current.values())[0][0])
            )[0]

        else:
            # get base name of annotation files
            self.annot_file_base = os.path.splitext(
                os.path.basename(list(signal_dict_current.values())[0][0][0])
            )[0]

        # lauch ViSiAnnoT for first video/signal file
        ViSiAnnoT.__init__(
            self, video_dict_current, signal_dict_current,
            interval_dict=interval_dict_current, poswid_dict=poswid_dict,
            flag_long_rec=True, layout_mode=layout_mode, **kwargs
        )

        # udpate number of recordings
        self.rec_nb = len(self.rec_beginning_datetime_list)


        # ******************************************************************* #
        # ******************* previous/next recording *********************** #
        # ******************************************************************* #

        # read images
        if hasattr(sys, "_MEIPASS"):
            dir_path = os.path.abspath(getattr(sys, "_MEIPASS"))

        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))

        previous_path = '%s/Images/previous.jpg' % dir_path
        next_path = '%s/Images/next.jpg' % dir_path

        previous_im = ToolsImage.readImage(previous_path)
        next_im = ToolsImage.readImage(next_path)

        #: (*QtWidgets.QGridlayout*) Widget of the "previous rec" image
        self.wid_previous = ToolsPyqtgraph.createWidgetLogo(
            self.lay, poswid_dict['previous'], previous_im, box_size=50
        )

        #: (*QtWidgets.QGridlayout*) Widget of the "next rec" image
        self.wid_next = ToolsPyqtgraph.createWidgetLogo(
            self.lay, poswid_dict['next'], next_im, box_size=50
        )

        # for documentation onyl
        #: (*QtWidgets.QComboBox*) Combo box for recording file selection
        self.combo_rec_choice = None

        # create combo box widget
        _, group_box, self.combo_rec_choice = ToolsPyQt.addComboBox(
            self.lay, poswid_dict['rec_choice'],
            [str(rec_id + 1) for rec_id in range(self.rec_nb)],
            box_title="File ID / %d" % self.rec_nb
        )

        group_box.setMaximumWidth(100)

        # listen to callbacks
        self.wid_previous.scene().sigMouseClicked.connect(
            self.mouseClickedPrevious
        )
        self.wid_next.scene().sigMouseClicked.connect(self.mouseClickedNext)
        self.combo_rec_choice.currentIndexChanged.connect(self.recChoice)


        # ******************************************************************* #
        # *********************** infinite loop ***************************** #
        # ******************************************************************* #
        ToolsPyQt.infiniteLoopDisplay(self.app)

        # close streams, delete temporary folders
        self.stopProcessing()


    # *********************************************************************** #
    # Group: Methods  for converting converting an input signal configuration to a list of signal configurations compliant with ViSiAnnoT
    # *********************************************************************** #


    def getSignalConfigurationSingleType(
        self, type_data, data_info_list, flag_raise_exception=True, **kwargs
    ):
        """
        Converts the configuration lists for a specific signal widget and for
        the whole long recording

        It can be used for signal configuration or intervals configuration.

        :param type_data: data type of the signal widget
        :type type_data: str
        :param data_info_list: list of configuration lists, each element is a
            list of length 8:

            - (*str*) Directory where to find the data files,
            - (*str*) Key to access the data (in case of .h5 or .mat files),
            - (*float* or *str*) Data frequency
            - (*str*) Pattern to find the data files,
            - (*str*) Delimiter to get beginning datetime in the data file
              name,
            - (*int*) Position of the beginning datetime in the data file
              name, according to the delimiter,
            - (*str*) Format of the beginning datetime in the data file name
              (either ``"posix"`` or a format compliant with
              ``datetime.strptime()``),
            - (*dict*) Plot style.
        :type data_info_list: list
        :param flag_raise_exception: specify if an exception must be raised
            when no data files are found
        :type flag_raise_exception: bool
        :param kwargs: keyword arguments of the function
            :func:`.getBeginningEndingDateTimeFromList`

        :returns:
            - **config_whole_rec_list** (*list*) -- nested list where each
              element is a configuration list and corresponds to one file in
              the long recording. Each element corresponds to one
              signal/interval and is a nested list where each element
              corresponds to one file in the long recording with 4 elements
              (path to the data file, key to access data, frequency, plot
              style)
            - **config_current_list** (*list*) -- configuration list of the
              first file in the long recording. Each element corresponds to one
              signal/interval and is a list with 4 elements (path to the data
              file, key to access data, frequency, plot style)
        """

        # initialize list of configuration for the whole recording
        config_whole_rec_list = []

        # initialize list of current configuration (i.e. for the first file
        # of the recording)
        config_current_list = []

        # loop on sub-configurations
        for data_dir, key, freq, pattern, delimiter, pos, fmt, plot_style in \
                data_info_list:
            # get list of data paths of the recording
            path_list = sorted(glob('%s/%s' % (data_dir, pattern)))

            # get number of files in the recording
            nb_files = len(path_list)

            # check if any file
            if nb_files > 0:
                # get frequency attribute if necessary
                if os.path.splitext(path_list[0])[1] == ".wav":
                    _, freq = ToolsAudio.getAudioWaveFrequency(
                        path_list[0]
                    )

                elif isinstance(freq, str):
                    freq = ToolsData.getAttributeGeneric(
                        path_list[0], freq
                    )

                elif freq == -1:
                    freq = self.fps

                # synchro is OK
                if self.flag_synchro:
                    # get configuration
                    configuration = list(zip(
                        path_list,
                        nb_files * [key],
                        nb_files * [freq],
                        nb_files * [delimiter],
                        nb_files * [pos],
                        nb_files * [fmt],
                        nb_files * [plot_style]
                    ))

                # synchro is not OK
                else:
                    # get beginning/ending time of files
                    beginning_datetime_list, ending_datetime_list = \
                        ToolsDateTime.getBeginningEndingDateTimeFromList(
                            path_list, key, freq, delimiter, pos, fmt, **kwargs
                        )

                    # create temporary synchronization files
                    sync_path_list = \
                        ViSiAnnoTLongRec.createSynchronizationFiles(
                            path_list,
                            type_data,
                            key,
                            self.rec_beginning_datetime_list,
                            self.rec_duration_list,
                            beginning_datetime_list,
                            ending_datetime_list,
                            self.tmp_name,
                            self.tmp_delimiter
                        )

                    # get number of synchronization files
                    nb_files = len(sync_path_list)

                    # get configuration
                    configuration = list(zip(
                        sync_path_list,
                        nb_files * [key],
                        nb_files * [freq],
                        nb_files * ['_'],
                        nb_files * [-1],
                        nb_files * ["%Y-%m-%dT%H-%M-%S"],
                        nb_files * [plot_style]
                    ))

                config_whole_rec_list.append(configuration)

                # get current intervals files
                config_current_list.append(configuration[0])

            elif flag_raise_exception:
                raise Exception('wrong input data directory\ngot: %s - %s' %
                                (type_data, data_dir))

        return config_whole_rec_list, config_current_list


    def getSignalConfigurationAllTypes(
        self, signal_dict, interval_dict, **kwargs
    ):
        """
        Converts signal and interval configurations to configuration lists
        compliant with :class:`.ViSiAnnoT`

        It sets the following attributes:

        - :attr:`.ViSiAnnoTLongRec.signal_dict_list`
        - :attr:`.ViSiAnnoTLongRec.interval_dict_list` (must be initialized)

        :param signal_dict: see second positional argument of
            :class:`.ViSiAnnoTLongRec` constructor
        :type signal_dict: dict
        :param interval_dict: see keyword argument of
            :class:`.ViSiAnnoTLongRec` constructor
        :type interval_dict: dict
        :param kwargs: keyword arguments of the function
            :func:`.getBeginningEndingDateTimeFromList`

        :returns:
            - **signal_dict_current** (*list*) -- signal configuration of the
              first file in the long recording. Each element corresponds to one
              signal and is a list with 7 elements (see positional argument
              ``signal_dict`` of :class:`.ViSiAnnoT` constructor)
            - **interval_dict_current** (*list*) -- interval configuration of
              the first file in the long recording. Each element corresponds to
              one interval and is a list with 7 elements (see keyword argument
              ``interval_dict`` of :class:`.ViSiAnnoT` constructor)
        """

        # dictionary containing the curent signals configuration
        signal_dict_current = OrderedDict()

        # dictionary containing the current files of intervals and the color to
        # plot
        interval_dict_current = OrderedDict()

        # loop on data types
        for type_data, data_info_list in signal_dict.items():
            # check if there are intervals
            if type_data in interval_dict.keys():
                # get interval configuration for the data type
                self.signal_dict_list[type_data], \
                    signal_dict_current[type_data] = \
                    self.getSignalConfigurationSingleType(
                        type_data, interval_dict[type_data], **kwargs
                )

            # get signal configuration for the data type
            self.signal_dict_list[type_data], \
                signal_dict_current[type_data] = \
                self.getSignalConfigurationSingleType(
                    type_data, data_info_list, **kwargs
            )

        return signal_dict_current, interval_dict_current


    @staticmethod
    def createSynchronizationFiles(
        data_path_list, type_data, key_data, ref_beginning_datetime_list,
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
        :param type_data: data type, used for the name of the synchronization
            files
        :type type_data: str
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

        # initialize list of synchronization files names
        synchro_path_list = []

        # loop on videos beginning date time
        for video_date_time, video_duration \
                in zip(ref_beginning_datetime_list, ref_duration_list):
            # compute difference of start time between video and signal files
            start_sig_diff_array = np.array([
                (beg_rec - video_date_time).total_seconds()
                for beg_rec in data_beginning_datetime_list
            ])

            # get signal files sharing temporality with video
            sig_file_id_list = np.intersect1d(
                np.where(start_sig_diff_array >= 0)[0],
                np.where(start_sig_diff_array <= video_duration)[0]
            )

            # check if there is a signal file beginning before video
            before_video_sig_array = np.where(start_sig_diff_array < 0)[0]
            if before_video_sig_array.shape[0] > 0:
                # check length of signal file beginning before video
                if data_ending_datetime_list[before_video_sig_array[-1]] > \
                        video_date_time:
                    # update list of signal files sharing temporality with video
                    sig_file_id_list = np.hstack((
                        before_video_sig_array[-1], sig_file_id_list
                    ))

            # get synchronization file name
            tmp_file_name = "%s/%s_%s-%s_%s.txt" % \
                (output_dir, output_dir, type_data, key_data.replace('/', '_'),
                 ToolsDateTime.convertDatetimeToString(video_date_time, fmt=1)
                 )

            synchro_path_list.append(tmp_file_name)
            with open(tmp_file_name, 'w') as f:
                for ite_id, sig_file_id in enumerate(sig_file_id_list):
                    # check first signal file
                    if ite_id == 0:
                        # if first signal file begins before the video
                        if start_sig_diff_array[sig_file_id] < 0:
                            # in case of TQRS, start second is computed from
                            #: the very beginning
                            start_sec = int((
                                video_date_time -
                                data_beginning_datetime_list[sig_file_id]
                            ).total_seconds())

                            start_sig_file = data_path_list[sig_file_id]

                            f.write("%s%s%d\n" % (
                                start_sig_file, delimiter, start_sec
                            ))

                        else:
                            start_sec = int((
                                data_beginning_datetime_list[sig_file_id] -
                                video_date_time
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


    def changeFileInLongRec(
        self, rec_id, new_frame_id, flag_previous_scroll=False
    ):
        """
        Changes file in the long recording

        It loads new data files by calling
        :meth:`.ViSiAnnoTLongRec.prepareNewRecording`. Then it updates the
        display.

        :param rec_id: index of the new file in the long recording
        :type rec_id: int
        :param new_frame_id: new current frame number (sampled at the
            reference frequency :attr:`.ViSiAnnoT.fps`)
        :type new_frame_id: int
        :param flag_previous_scroll: specify if the new file is reach backward
            by scrolling
        :type flag_previous_scroll: bool

        :returns: specify if the file has been effectively changed
        :rtype: bool
        """

        # set new recording
        ok = self.prepareNewRecording(rec_id)

        if ok:
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

            # update signals plot
            self.updateSignalPlot()

            # update progress bar
            self.wid_progress.getProgressCurve().setData(
                [0, self.nframes], [0, 0]
            )

            # update annotation regions plot if necessary
            if len(self.annotevent_label_list) > 0:
                if self.annotevent_button_label_list[3].text() == "On":
                    self.clearAnnotEventRegions()
                    self.annotevent_description_dict = {}
                    self.plotAnnotEventRegions()

        return ok


    def previousRecording(self):
        """
        Loads previous file in the long recording
        """

        self.changeFileInLongRec(
            self.rec_id - 1, self.frame_id + self.nframes,
            flag_previous_scroll=True
        )


    def mouseClickedPrevious(self):
        """
        Callback method for loading previous file in the long recording after
        having clicked on the "previous" image

        Connected to the signal ``sigMouseClicked`` of the attribute ``scene``
        of :attr:`.ViSiAnnoTLongRec.wid_previous`.
        """

        self.changeFileInLongRec(self.rec_id - 1, 0)


    def nextRecording(self):
        """
        Loads next file in the long recording

        :returns: specify if the file has been effectively changed
        :rtype: bool
        """

        ok = self.changeFileInLongRec(
            self.rec_id + 1, self.frame_id - self.nframes
        )

        return ok


    def mouseClickedNext(self):
        """
        Callback method for loading next file in the long recording after
        having clicked on the "next" image

        Connected to the signal ``sigMouseClicked`` of the attribute ``scene``
        of :attr:`.ViSiAnnoTLongRec.wid_next`.
        """

        self.changeFileInLongRec(self.rec_id + 1, 0)


    def prepareNewRecording(self, rec_id):
        """
        Loads data of a new file in the long recording

        It does not set :attr:`.ViSiAnnoT.first_frame` and
        :attr:`.ViSiAnnoT.last_frame`, and it does not update signal plots.

        :param rec_id: index of the new file in the long recording
        :type rec_id: int

        :returns: specify if the new file has been effectively loaded
        :rtype: bool
        """

        # check recording id
        if rec_id >= 0 and rec_id < self.rec_nb:
            self.rec_id = rec_id

            # get new video data
            video_dict_current = OrderedDict()
            for video_id, video_dict_list_tmp in self.video_dict_list.items():
                video_dict_current[video_id] = video_dict_list_tmp[self.rec_id]

                # set video widget title
                file_name, _ = os.path.splitext(
                    os.path.basename(video_dict_current[video_id][0])
                )

                self.wid_vid_dict[video_id].setTitle(file_name)
                self.vid_file_name_dict[video_id] = file_name

            # get new signals and intervals
            signal_dict_current = OrderedDict()
            interval_dict_current = OrderedDict()
            for type_data in self.signal_dict_list.keys():
                # signal
                signal_dict_current[type_data] = []
                for config_list in self.signal_dict_list[type_data]:
                    signal_dict_current[type_data].append(
                        config_list[self.rec_id]
                    )

                # additinal intervals
                if type_data in self.interval_dict_list.keys():
                    interval_dict_current[type_data] = []
                    for interval_config_list in \
                            self.interval_dict_list[type_data]:
                        if self.rec_id < len(interval_config_list):
                            interval_dict_current[type_data].append(
                                interval_config_list[self.rec_id]
                            )

            # set new data
            self.setAllData(
                video_dict_current, signal_dict_current, interval_dict_current
            )

            # update progress bar
            self.setTemporalTicks(
                self.wid_progress, (0, self.nframes, self.fps)
            )
            self.wid_progress.updateNFrames(self.nframes)

            # set recording choice combo box
            self.combo_rec_choice.setCurrentIndex(self.rec_id)

            # reset combo boxes
            try:
                self.combo_trunc.setCurrentIndex(0)
            except Exception:
                pass

            try:
                self.combo_from_cursor.setCurrentIndex(0)
            except Exception:
                pass

            return True

        else:
            return False


    def recChoice(self, ite_rec):
        """
        Callback method for choosing a new file in the long recording with the
        combo box

        Connected to the signal ``currentIndexChanged`` of
        :attr:`.ViSiAnnoTLongRec.combo_rec_choice`.

        :param ite_rec: index of the new file in the long recording selected
            in the combo box
        :type ite_rec: int
        """

        # change recording
        self.changeFileInLongRec(ite_rec, 0)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
