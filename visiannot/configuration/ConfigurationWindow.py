# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining class :class:`.ConfigurationWindow`
"""


from PyQt5 import QtWidgets, QtCore, QtGui
import os
from configobj import ConfigObj
import numpy as np
from ..tools import pyqt_overlayer
from .Configuration import Configuration


class ConfigurationWindow():
    def __init__(self, path=""):
        """
        Class creating the window for configuring
        :class:`.ViSiAnnoTLongRec`

        :param path: path to the configuration file to load when
            creating the window, it might be a configuration dictionary
        :type path: str or dict

        The window is composed of 5 main widgets:

        - Video configuration
        - Signal configuration
        - Events annotation configuration
        - General configuration
        - Group box with load/save/done push buttons

        Each one of the video configuration, signal configuration and event
        annotation configuration is contained in an instance of
        :class:`Configuration`.

        The signal configuration has several configuration children (Interval,
        Threshold and YRange), each one displayed in a separate window.

        All the instances of :class:`Configuration` are stored in the
        dictionary :attr:`.meta_dict`.

        On the one hand, the attribute :attr:`ConfigurationWindow.lay` refers
        to the first level of QGridLayout, meaning the layout filling the whole
        window. On the other hand, the second level of QGridLayout fills the
        first level layout ConfigurationWindow.lay.
        These layouts are the configuration widgets (general =>
        ConfigurationWindow.general_lay, video =>
        ConfigurationWindow.meta_dict["Video"].lay, ...).

        The different types of configuration are stored in 7 dictionaries:

        - :attr:`ConfigurationWindow.general_dict`
        - ``ConfigurationWindow.meta_dict["Video"].dict``
        - ``ConfigurationWindow.meta_dict["Signal"].dict``
        - ``ConfigurationWindow.meta_dict["Interval"].dict``
        - ``ConfigurationWindow.meta_dict["Threshold"].dict``
        - ``ConfigurationWindow.meta_dict["AnnotEvent"].dict``
        - ``ConfigurationWindow.meta_dict["AnnotImage"].dict``

        When values are modified manually in the window, these dictionaries are
        not updated. The method :meth:`.set_configuration_dictionaries` must
        be called to do so.
        """

        #: (*dict*) Each value is an instances of :class:`Configuration`
        #: contained in the window
        #:
        #: The keys are:
        #:
        #: - Video
        #: - Signal
        #: - Interval
        #: - Threshold
        #: - YRange
        #: - AnnotEvent
        #: - AnnotImage
        #:
        #: See :attr:`Configuration.dict` for details.
        self.meta_dict = {}

        #: (*list*) Types of configuration, each element is a string and must
        #: be a key of :attr:`.meta_dict`
        self.config_type_list = [
            "Video", "Signal", "Interval", "Threshold", "YRange", "AnnotEvent",
            "AnnotImage"
        ]

        #: (*dict*) Same keys as :attr:`.general_dict`,
        #: value is the list of positions of the corresponding widgets in the
        #: general configuration widget
        #: (:attr:`.general_lay`)
        self.general_config_position_dict = {}

        #: (*QtWidgets.QGridLayout*) Layout of the general configuration widget
        self.general_lay = None

        #: (*QtWidgets.QGroupBox*) Group box of the general configuration
        #: widget
        self.general_group_box = None

        #: (*QtWidgets.QPushButton*) Push button for changing the directory of
        #: annotations
        self.general_push_button = None


        # *********************** create window ***************************** #

        #: (*QtWidgets.QApplication*) Display initializer
        self.app = pyqt_overlayer.initialize_gui()

        # set default font
        self.app.setFont(QtGui.QFont("Times", 12))

        #: (*QtWidgets.QWidget*) Container of main configuration window
        self.win = None

        #: (*QtWidgets.QGridLayout*) Layout of the main configuration window
        self.lay = None

        # create window
        self.win, self.lay = pyqt_overlayer.create_window(
            title="ViSiAnnoT configuration"
        )

        # create scroll area
        scroll_lay, _ = pyqt_overlayer.add_scroll_area(self.lay, (0, 0))


        # ******************** create video widget ************************** #

        self.meta_dict["Video"] = Configuration(
            self.lay,
            (0, 0),
            "Video",
            1,
            [
                ("edit", 1, {}), ("edit", 1, {}), ("edit", 1, {}),
                ("spin", 1, {"minimum": -2}), ("edit", 1, {})
            ],
            ['', '*.mp4', '_', 0, '%Y-%m-%dT%H-%M-%S'],
            help_text="1. Directory\
            2. File pattern\
            3. Timestamp delimiter\
            4. Timestamp position\
            5. Timestamp format",
            config_base_name="vid_",
            pos_dir=0,
            flag_dir_identical=True
        )

        # add configuration group box to scroll area
        scroll_lay.addWidget(self.meta_dict["Video"].group_box)


        # ******************** create signal widget ************************* #

        self.meta_dict["Signal"] = Configuration(
            self.lay,
            (1, 0),
            "Signal",
            2,
            [
                ("edit", 1, {}), ("edit", 1, {}), ("edit", 1, {}),
                ("spin", 1, {"minimum": -2}), ("edit", 1, {}), ("edit", 1, {}),
                ("edit_freq", 1, {}), ("edit_literal", 1, {})
            ],
            [['', '*', '_', 0, '%Y-%m-%dT%H-%M-%S', '', 0, None]],
            help_text="1. Signal widget name\
            2. Directory\
            3. File pattern\
            4. Timestamp delimiter\
            5. Timestamp position\
            6. Timestamp format\
            7. Key to access the data (for .mat or .h5), used as legend\
            8. Frequency (0 if 2D data with timestamp, -1 if same as video)\
            9. Plot style (default is None)",
            pos_dir=0,
            flag_dir_identical=True,
            flag_key=True,
            config_base_name="sig_",
            children_config_name_list=["Interval", "Threshold", "YRange"]
        )

        # add configuration group box to scroll area
        scroll_lay.addWidget(self.meta_dict["Signal"].group_box)

        # listen to callback
        self.meta_dict["Signal"].button_group_children.buttonClicked[int].connect(
            self.show_child_window
        )


        # **************** create annotEvent widget ************************* #

        self.meta_dict["AnnotEvent"] = Configuration(
            self.lay,
            (2, 0),
            "AnnotEvent",
            1,
            [
                ("spin", 4, [
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 100}
                ])
            ],
            (0, 0, 0, 50),
            help_text="1. Label\
            2. Color (RGBA)",
            flag_key=True,
            config_base_name="label_"
        )

        # add configuration group box to scroll area
        scroll_lay.addWidget(self.meta_dict["AnnotEvent"].group_box)


        # **************** create annotImage widget ************************* #

        self.meta_dict["AnnotImage"] = Configuration(
            self.lay, (3, 0), "AnnotImage", 1, [("edit", 1, {})], '',
            help_text="1. Label", config_base_name="label_"
        )

        # add configuration group box to scroll area
        scroll_lay.addWidget(self.meta_dict["AnnotImage"].group_box)


        # ******************* create general widget ************************* #
        self.create_widget_general((4, 0))

        # add group box to scroll area
        scroll_lay.addWidget(self.general_group_box)

        # listen to callback
        self.general_push_button.clicked.connect(
            self.set_directory_annotations
        )


        # ***************** create load/save/done widget ******************** #

        #: (*QtWidgets.QButtonGroup*) Group of buttons with the push buttons
        #: Load/Save/Done
        self.button_group_lsd = None

        _, group_box_lsd, self.button_group_lsd = \
            pyqt_overlayer.add_widget_button_group(
                self.lay, (5, 0), ["Load", "Save", "Done"],
                button_type="push", box_title="Configuration file", width=120
            )

        # set size
        group_box_lsd.setMaximumHeight(80)

        # listen to callback
        self.button_group_lsd.buttonClicked[int].connect(self.call_lsd)


        # ******************* create children windows ********************** #

        #: (*list*) Instances of QtWidgets.QWidget containing the children
        #: configuration windows
        self.children_win_list = []

        # interval configuration
        self.create_child_configuration_window(
            self.meta_dict["Signal"],
            "Interval",
            2,
            [
                ("edit", 1, {}), ("edit", 1, {}), ("edit", 1, {}),
                ("spin", 1, {"minimum": -2}), ("edit", 1, {}), ("edit", 1, {}),
                ("edit_freq", 1, {}), ("spin", 4, [
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 100}
                ])
            ],
            [['', '*', '_', 0, '%Y-%m-%dT%H-%M-%S', '', 0, (0, 0, 0, 50)]],
            help_text="1. Directory\
            2. File pattern\
            3. Timestamp delimiter\
            4. Timestamp position\
            5. Timestamp format\
            6. Key to access the data (for .mat or .h5)\
            7. Frequency (0 if timestamps, -1 if same as signal)\
            8. Color (RGBA)",
            pos_dir=0,
            flag_dir_identical=True,
            win_size=(1200, 400)
        )

        # threshold configuration
        self.create_child_configuration_window(
            self.meta_dict["Signal"],
            "Threshold",
            2,
            [
                ("edit_float", 1, {}),
                ("spin", 3, [
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255},
                    {"minimum": 0, "maximum": 255}
                ])
            ],
            [[0, (0, 0, 0, 50)]],
            help_text="1. Threhsold value\
            2. Color (RGBA)",
            win_size=(600, 400)
        )

        # Y range configuration
        self.create_child_configuration_window(
            self.meta_dict["Signal"],
            "YRange",
            1,
            [("edit_float", 1, {}), ("edit_float", 1, {})],
            [0, 0],
            help_text="1. Min value\
            2. Max value",
            win_size=(500, 400)
        )


        # ************** initialize general configuration ******************* #

        #: (*dict*) Default general configuration, see :attr:`.general_dict`
        #: for details
        self.general_dict_default = {
            "flag_synchro": False,
            "flag_pause_status": True,
            "layout_mode": 0,
            "zoom_factor": 2,
            "max_points": 5000,
            "nb_ticks": 10,
            "trunc_duration": [0, 0],
            "time_zone": "Europe/Paris",
            "flag_annot_overlap": False,
            "annot_dir": "Annotations",
            "from_cursor_list": [],
            "current_fmt": "%Y-%m-%dT%H:%M:%S.%s",
            "range_fmt": "%H:%M:%S.%s",
            "ticks_fmt": "%H:%M:%S.%s",
            "ticks_size": 12,
            "ticks_color": (93, 91, 89),
            "ticks_offset": 5,
            "y_ticks_width": 30,
            "font_name": "Times",
            "font_size": 12,
            "font_size_title": 16,
            "font_color": (0, 0, 0),
            "nb_table_annot": 5,
            "bg_color": (244, 244, 244),
            "bg_color_plot": (255, 255, 255),
            "height_widget_signal": 150
        }

        #: (*dict*) General configuration
        #:
        #: The keys and values are:
        #:
        #: - ``"flag_synchro"``: (*bool*) specify if the signals are
        #:   synchronized with video
        #: - ``"flag_pause_status"``: (*bool*) specify if the video is
        #:   paused at launching
        #: - ``"layout_mode"``: (*int*) either 0, 1 or 2
        #: - ``"zoom_factor"``: (*int*)
        #: - ``"max_points"``: (*int*)
        #: - ``"nb_ticks"``: (*int*)
        #: - ``"trunc_duration"``: (*list*) length 2 *(minute, second)*
        #: - ``"time_zone"``: (*str*) time zone (complying with pytz
        #:   package)
        #: - ``"flag_annot_overlap"``: (*bool*) specify if overlap of events
        #:   annotations is enabled
        #: - ``"annot_dir"``: (*str*) directory of the annotations
        #: - ``"from_cursor_list"``: (*list*) each element is a list of
        #:   length 2 *(minute, second)*
        #: - ``"current_fmt"``: (*str*) datetime string format of the current
        #:   temporal position in progress bar, see keyword argument ``fmt`` of
        #:   :func:`.convert_datetime_to_string`
        #: - ``"range_fmt"``: (*str*) datetime string format of the temporal
        #:   range duration in progress bar, see keyword argument ``fmt`` of
        #:   :func:`.convert_datetime_to_string`
        #: - ``"ticks_fmt"``: (*str*) datetime string format of X axis ticks
        #:   text, see keyword argument ``fmt`` of
        #:   :func:`.convert_datetime_to_string`
        #: - ``"ticks_size"``: (*int*) size of the ticks text in signal
        #:   plots
        #: - ``"ticks_color"``: (*list*) RGB color of ticks
        #: - ``"ticks_offset"``: (*int*) space in pixels between ticks and
        #:   associated values
        #: - ``"y_ticks_width"``: (*int*) horizontal space in pixels for the
        #:   of Y axis ticks in signal widgets
        #: - ``"font_name"``: (*str*) font of the text in ViSiAnnoT
        #: - ``"font_size"``: (*int*) font size in ViSiAnnoT
        #: - ``"font_size_title"``: (*int*) font size in ViSiAnnoT (title
        #:   of video widget and progress bar widget)
        #: - ``"font_color"``: (*list*) RGB color of font in ViSiAnnoT
        #: - ``"nb_table_annot"``: (*int*) maximum number of labels in one
        #:   row in annotation widgets
        #: - ``"bg_color"``: (*list*) RGB color of background in ViSiAnnoT
        #: - ``"bg_color_plot"``: (*list*) RGB color of background color of
        #:   signal plots
        self.general_dict = None

        # load configuration
        self.load(path)

        # infinite loop
        pyqt_overlayer.infinite_loop_gui(self.app)



    # *********************************************************************** #
    # ******************** ConfigurationWindow methods ********************** #
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for widget creation
    # *********************************************************************** #


    def create_widget_general(self, widget_position):
        """
        Adds a widget with the general configuration to the layout
        :attr:`ConfigurationWindow.lay`

        The widget is contained in an instance of QtWidgets.QGroupBox.

        This method sets the following attributes:

        - :attr:`.general_config_position_dict`.
        - :attr:`.general_group_box`.
        - :attr:`.general_lay`,
        - :attr:`.general_push_button`.

        :param widget_position: position of the group box in the parent grid
            layout, length 2 ``(row, col)`` or
            4 ``(row, col, rowspan, colspan)``
        :type widget_position: tuple of integers
        """

        # create general configuration group box
        self.general_lay, self.general_group_box = pyqt_overlayer.add_group_box(
            self.lay, widget_position, "General"
        )

        # minimum height of widgets in the group box
        height = 30

        # list of elements to add in the group box
        #
        # each element is a tuple of length 5:
        # - text to display next to the widget element
        # - corresponding key in the general configuration dictionary
        # - type of widget element ("check_box", "spin", "spin_double" or
        #   "edit")
        # - number of widget elements
        # - dictionary with keyword arguments to pass to the widget constructor
        elt_list = [
            ("Signals synchronized", "flag_synchro", "check_box", 1, {}),
            (
                "Video paused at launch", "flag_pause_status",
                "check_box", 1, {}
            ),
            (
                "Events annotations overlap", "flag_annot_overlap",
                "check_box", 1, {}
            ),
            (
                "Layout mode (1, 2 or 3)", "layout_mode", "spin", 1,
                {"minimum": 1, "maximum": 3}
            ),
            ("Time zone", "time_zone", "edit", 1, {}),
            (
                "Max nb of points to display", "max_points", "spin", 1,
                {"minimum": 1, "maximum": 100000}
            ),
            (
                "Minimum height in pixels of the signal widgets",
                "height_widget_signal", "spin", 1,
                {"minimum": 1, "maximum": 100000}
            ),
            (
                "Trunc duration (min, sec)", "trunc_duration", "spin", 2,
                {"minimum": 0, "maximum": 59}
            ),
            ("Zoom factor", "zoom_factor", "spin", 1, {"minimum": 1}),
            (
                "Datetime string format of the current temporal position in "
                "progress widget", "current_fmt", "edit", 1, {}
            ),
            (
                "Datetime string format of the temporal range duration in "
                "progress widget", "range_fmt", "edit", 1, {}
            ),
            (
                "Datetime string format of temporal ticks text", "ticks_fmt",
                "edit", 1, {}
            ),
            (
                "Number of Temporal ticks", "nb_ticks", "spin", 1,
                {"minimum": 1}
            ),
            (
                "Ticks color", "ticks_color", "spin", 3,
                {"minimum": 0, "maximum": 255}
            ),
            ("Ticks size", "ticks_size", "spin", 1, {"minimum": 1}),
            ("Ticks offset", "ticks_offset", "spin", 1, {"minimum": 1}),
            (
                "Width (px) of ticks text of Y axis in signal widgets",
                "y_ticks_width", "spin", 1, {"minimum": 1}
            ),
            ("Font name", "font_name", "edit", 1, {}),
            ("Font size", "font_size", "spin", 1, {"minimum": 1}),
            (
                "Font size (title)", "font_size_title", "spin", 1,
                {"minimum": 1}
            ),
            (
                "Font color", "font_color", "spin", 3,
                {"minimum": 0, "maximum": 255}
            ),
            (
                "Maximum number of labels in a row", "nb_table_annot", "spin",
                1, {"minimum": 1}
            ),
            (
                "Background color", "bg_color", "spin", 3,
                {"minimum": 0, "maximum": 255}
            ),
            (
                "Background color (signal plots)", "bg_color_plot", "spin", 3,
                {"minimum": 0, "maximum": 255}
            ),
            ("Annotations directory", "annot_dir", "edit", 1, {})
        ]

        # get number of rows in the widget
        nb_rows = len(elt_list)

        # get maximum number of columns for an element
        nb_cols_max = max([n for _, _, _, n, _ in elt_list])

        # loop on elements to add in the widget
        for i, (label, key, elt_type, elt_nb, elt_params) in \
                enumerate(elt_list):
            # add label
            q_label = QtWidgets.QLabel(label)
            q_label.setAlignment(QtCore.Qt.AlignRight)
            q_label.setAlignment(QtCore.Qt.AlignVCenter)
            self.general_lay.addWidget(q_label, i, 0)

            # get widget position
            wid_pos = (i, 1)

            # add key to configuration position dictionary
            self.general_config_position_dict[key] = []

            # loop on columns
            for j in range(elt_nb):
                # check element type
                if elt_type == "check_box":
                    widget = QtWidgets.QCheckBox(**elt_params)

                elif elt_type == "edit":
                    widget = QtWidgets.QLineEdit(**elt_params)

                elif elt_type == "spin_double":
                    widget = QtWidgets.QDoubleSpinBox(**elt_params)

                else:
                    widget = QtWidgets.QSpinBox(**elt_params)

                # set widget height
                widget.setMinimumHeight(height)

                # check number of columns
                if elt_nb == 1:
                    # update widget position
                    wid_pos += (1, nb_cols_max)

                else:
                    # update widget position
                    wid_pos = (i, j + 1)

                # update configuration position dictionary
                self.general_config_position_dict[key].append(wid_pos[:2])

                # add widget
                pyqt_overlayer.add_widget_to_layout(
                    self.general_lay, widget, wid_pos
                )

        # get index of row with annotation base directory
        i = [key for _, key, _, _, _ in elt_list].index("annot_dir")

        # create push button used to change the directory of anntotations
        self.general_push_button = pyqt_overlayer.add_push_button(
            self.general_lay, (i, nb_cols_max + 1), "Change directory",
            width=200
        )
        self.general_push_button.setMinimumHeight(height)

        # create list of "from cursor" durations
        pyqt_overlayer.add_spin_box_table(
            self.general_lay, (0, nb_cols_max + 2, nb_rows, 1), 10, 2,
            "'from cursor' durations (min, sec)", {"minimum": 0, "maximum": 59}
        )
        self.general_config_position_dict["from_cursor_list"] = \
            [(0, nb_cols_max + 2)]


    def create_child_configuration_window(
        self, parent_config, *args, win_size=(0, 0), **kwargs
    ):
        """
        Creates a window for a child configuration

        This method can be used when a configuration type is linked to another
        one so that the keys in Configuration.dict must be the same.

        For example, this applies to the signal configuration. We can specify
        some threshold values to plot on the signal widgets. The thresholds
        must be defined for an existing signal, so the keys in the
        configuration dictionary are the same as in the signal configuration.

        As a consequence, when a configuration grid is added in the child
        configuration window, it has automatically the same key as in the
        signal configuration and it cannot be changed. If the whole
        configuration grid for a given key is deleted in the signal
        configuration, then it is also deleted in the threshold configuration.

        This method sets the following attributes:

        - :attr:`.additional_win_list`.
        - :attr:`.additional_lay_list`.
        - :attr:`.meta_dict`.

        :param parent_config: parent configuration
        :type parent_config: :class:`.Configuration`
        :param args: positional arguments of :class:`.Configuration`
            constructor, starting from the third position
        :param win_size: window size :math:`(width, height)`, set one value to
            0 to maximize the window
        :type win_size: tuple
        :param kwargs: keyword arguments of :class:`.Configuration` constructor
            (excepted ``parent_config`` which is the first positional argument
            of this method)
        """

        # create configuration window
        win, lay = pyqt_overlayer.create_window(
            size=win_size, title="%s configuration" % args[0], flag_show=False
        )

        # create scroll area
        scroll_lay, scroll_area = pyqt_overlayer.add_scroll_area(lay, (0, 0))

        # set size
        scroll_area.setMinimumSize(win_size[0], win_size[1])

        # create configuration
        config = Configuration(
            lay, (0, 0), *args, **kwargs, parent_config=parent_config
        )

        # add configuration group box to scroll area
        scroll_lay.addWidget(config.group_box)

        # add child to parent configuration
        parent_config.add_child_configuration(config)

        # create push button for hiding configuration window
        push_button_ok = pyqt_overlayer.add_push_button(
            lay, (1, 0), "Ok", width=80
        )

        # listen to callback
        push_button_ok.clicked.connect(win.hide)

        # update attributes
        self.children_win_list.append(win)
        self.meta_dict[args[0]] = config


    # *********************************************************************** #
    # End group
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for the management of callbacks
    # *********************************************************************** #


    def show_child_window(self, button_id):
        """
        Callback method for opening child configuration window related to
        signal configuration

        Connected to the signal ``buttonClicked[int]`` of
        ``ConfigurationWindow.meta_dict["Signal"].button_group_children``.

        The group button
        ``ConfigurationWindow.meta_dict["Signal"].button_group_children``
        has as much buttons as children configurations (see
        :attr:`.Configuration.children_configuration_list` of
        ``ConfigurationWindow.meta_dict["Signal"]``).

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        self.children_win_list[button_id].show()


    def set_directory_annotations(self):
        """
        Callback method for annotations directory selection

        Connected to the signal ``clicked`` of
        :attr:`.general_push_button`.
        """

        # get text edit
        pos = self.general_config_position_dict["annot_dir"][0]
        edit_dir = self.general_lay.itemAtPosition(pos[0], pos[1]).widget()

        # open dialog window
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select video directory", edit_dir.text(),
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if directory != "":
            # set text edit
            edit_dir.setText(directory)


    def call_lsd(self, button_id):
        """
        Callback method for Load/Save/Done push buttons

        Connected to the signal ``buttonClicked[int]`` of the button group
        :attr:`.button_group_lsd`

        The group button ConfigurationWindow.button_group_lsd has 3 buttons:

        - button_id == 0 => load configuration file
        - button_id == 1 => save configuration file
        - button_id == 2 => set configuration dictionaries and close main
          window

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        # load
        if button_id == 0:
            # open a dialog window in order to get the configuration file name
            win = QtWidgets.QWidget()
            path = QtWidgets.QFileDialog.getOpenFileName(
                win, "Load configuration file", os.getcwd(), "*.ini"
            )[0]

            # load configuration file
            if path != "":
                self.load(path)

        # save
        elif button_id == 1:
            # open dialog window in order to get where to save the
            # configuration file
            path = QtWidgets.QFileDialog.getSaveFileName(
                None, "Save configuration file", os.getcwd(), "*.ini"
            )[0]

            # write configuration file
            if path != '':
                self.write_configobj_file(path)
                print("Configuration file written")

        # done
        elif button_id == 2:
            # set configuration dictionaries
            self.set_configuration_dictionaries()

            # close window(s)
            self.win.close()
            for win in self.children_win_list:
                win.close()
            print("Done with configuration")


    # *********************************************************************** #
    # End group
    # *********************************************************************** #


    # *********************************************************************** #
    # Group: Methods for loading/saving configuration
    # *********************************************************************** #


    @staticmethod
    def load_config_file(
        path,
        key_dict={
            "General": 0,
            "Video": 1,
            "Signal": 2,
            "Interval": 2,
            "Threshold": 2,
            "YRange": 1,
            "AnnotEvent": 1,
            "AnnotImage": 0
        }
    ):
        """
        Loads a configuration file

        :param path: path to the configuration file to load
        :type path: str
        :param key_dict: each item corresponds to a configuration type to
            retrieve, key is the configuration key, value is the number of
            nesting levels to apply for converting a nested dictionary (that
            may be retrieved by **ConfigObj**) to a nested list (equivalent to
            :attr:`.nb_level` of corresponding instance of
            :class:`.Configuration`)
        :type key_dict: dict

        :returns: configuration dictionary, with the same keys as ``key_dict``
        :rtype: dict
        """

        # load file
        config = ConfigObj(path, unrepr=True)

        # initialize output dictionary
        config_dict = {}

        # loop on configuration keys
        for key, convert_level in key_dict.items():
            if key in config.keys():
                if convert_level == 0:
                    config_dict[key] = config[key]

                else:
                    config_dict[key] = {}
                    for key_sub, dict_tmp in config[key].items():
                        config_dict[key][key_sub] = \
                            ConfigurationWindow.convert_dict_to_list_nested(
                                dict_tmp, level=convert_level
                        )

        return config_dict


    def load(self, path):
        """
        Loads a configuration file and store it directly in the configuration
        dictionaries

        It calls the static method :meth:`.load_config_file`
        and then sets the following attributes:

        - :attr:`.general_dict`
        - ``ConfigurationWindow.meta_dict[config_type].dict`` for config_type
          in :attr:`.config_type_list`

        :param path: path to the configuration file to load
        :type path: str
        """

        # check type
        if isinstance(path, str):
            # check if file exists
            if os.path.isfile(path):
                # load configuration file
                config_dict = ConfigurationWindow.load_config_file(path)
                print("Configuration file loaded")

            else:
                # default configuration
                config_dict = {}
                print("Configuration file not found, default configuration")

        else:
            # configuration dictionary passed as argument instead of a path
            config_dict = path

        # get general configuration
        if "General" in config_dict:
            self.general_dict = config_dict["General"]

            # check if missing keys in general configuration
            for key, default_value in self.general_dict_default.items():
                if key not in self.general_dict.keys():
                    self.general_dict[key] = default_value

        else:
            # get default general configuration
            self.general_dict = self.general_dict_default.copy()

        # update meta_dict attribute
        for config_type in self.config_type_list:
            if config_type in config_dict.keys():
                self.meta_dict[config_type].dict = config_dict[config_type]

            else:
                self.meta_dict[config_type].dict = {}

        # display configuration
        self.reset_display()


    def reset_display(self):
        """
        Deletes the whole configuration display and replaces it with the
        current values of the attribute dictionaries
        """

        # reset general
        self.set_general_configuration(True)

        # reset configurations
        for config_type in self.config_type_list:
            self.meta_dict[config_type].reset_display()


    def write_configobj_file(self, path):
        """
        Creates a .ini configuration file with the current configuration

        Before writing the file, the method calls
        :meth:`.set_configuration_dictionaries`.

        :param path: path to the configuration file to create
        :type path: str
        """

        # set configuration dictionaries
        self.set_configuration_dictionaries()

        # remove configuration file if necessary
        if os.path.isfile(path):
            os.remove(path)

        # create config object
        config = ConfigObj(path, unrepr=True)

        # convert general dictionary to config object
        config["General"] = self.general_dict

        # convert configuration dictionaries to config object
        for config_type in self.config_type_list:
            config[config_type] = self.meta_dict[config_type].dict

        # write configuration file
        config.write()


    def set_configuration_dictionaries(self):
        """
        Sets the configuration dictionaries with the values filled in the GUI

        The configuration dictionaries are:

        - :attr:`.general_dict`
        - ``ConfigurationWindow.meta_dict[config_type].dict`` for config_type
          in :attr:`.config_type_list`
        """

        self.set_general_configuration(False)
        for config_type in self.config_type_list:
            self.meta_dict[config_type].set_dictionary()


    def set_general_configuration(self, flag_display):
        """
        Displays the values in the general configuration widget from
        :attr:`.general_dict` or sets the values
        of :attr:`.general_dict` from the values filled in
        the general configuration widget (i.e.
        :attr:`.general_lay`)

        :param flag_display: specify if displaying values in the general
            configuration widget, if ``False`` then it sets the values of
            :attr:`.general_dict`
        :type flag_display: bool
        """

        # loop on elements
        for key, pos_list in self.general_config_position_dict.items():
            # check mode
            if not flag_display:
                # reset key in configuration dictionary
                self.general_dict[key] = []

            # loop on columns
            for ite_col, pos in enumerate(pos_list):
                # get widget
                widget = self.general_lay.itemAtPosition(
                    pos[0], pos[1]
                ).widget()

                # check element type
                if isinstance(widget, QtWidgets.QCheckBox):
                    # get method name
                    method_0 = "setChecked"
                    method_1 = "isChecked"

                elif isinstance(widget, QtWidgets.QSpinBox) or \
                        isinstance(widget, QtWidgets.QDoubleSpinBox):
                    # get method name
                    method_0 = "setValue"
                    method_1 = "value"

                elif isinstance(widget, QtWidgets.QLineEdit):
                    # get method name
                    method_0 = "setText"
                    method_1 = "text"

                else:
                    method_0, method_1 = None, None

                # check method name
                if method_0 is not None:
                    # check mode
                    if flag_display:
                        # check number of columns
                        if len(pos_list) > 1:
                            # set widget value
                            getattr(widget, method_0)(
                                self.general_dict[key][ite_col]
                            )

                        else:
                            # set widget value
                            getattr(widget, method_0)(self.general_dict[key])

                    else:
                        # update configuration dictionary
                        self.general_dict[key].append(
                            getattr(widget, method_1)()
                        )

            # check mode
            if method_0 is not None and not flag_display:
                # check if single column
                if len(pos_list) == 1:
                    # update configuration dictionary
                    self.general_dict[key] = self.general_dict[key][0]

        # deal with list of list of spin boxes (trunc duration)
        # get grid
        key = "from_cursor_list"
        pos = self.general_config_position_dict[key][0]
        grid = self.general_lay.itemAtPosition(
            pos[0], pos[1]
        ).widget().layout()

        # get value list
        value_list = self.general_dict[key]

        # list of list of spin boxes
        value_list = pyqt_overlayer.set_spin_box_table(
            grid, value_list, flag_display
        )

        if not flag_display:
            # delete empty durations (full of zeros)
            value_array = np.array(value_list)
            value_array = np.delete(
                value_array,
                np.where(value_array.sum(axis=1) == 0),
                axis=0
            )
            value_list = []
            for value in value_array:
                value_list.append(list(value))

            # update configuration dictionary
            self.general_dict[key] = value_list


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Static methods for converting dictionary to list
    # *********************************************************************** #


    @staticmethod
    def convert_dict_to_list(dic):
        """
        Puts the values of a dictionary in a list

        :param dic: dictionary
        :type dic: dict

        If dic is not a dictionary, then it returns ``dic``.

        :returns: list
        :rtype: list
        """

        if isinstance(dic, dict):
            return list(dic.values())

        else:
            return dic


    @staticmethod
    def convert_dict_to_list_nested(dic, level=1):
        """
        Puts the values of a nested dictionary in a nested list

        :param dic: dictionary
        :type dic: dict

        :returns: list of lists
        :rtype: list
        """

        dic_list = ConfigurationWindow.convert_dict_to_list(dic)

        if level == 1 or not isinstance(dic_list, list):
            return dic_list

        else:
            output = []
            for dic_tmp in dic_list:
                output.append(
                    ConfigurationWindow.convert_dict_to_list_nested(
                        dic_tmp, level=level - 1
                    )
                )

            return output


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
