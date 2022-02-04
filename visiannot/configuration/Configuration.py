# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining class :class:`.Configuration` and function
:func:`.check_configuration`
"""


from PyQt5 import QtWidgets
from ast import literal_eval
import numpy as np
from ..tools import pyqt_overlayer


def check_configuration(config_id, config, config_type, flag_long_rec=True):
    """
    Checks if a configuration list has the right number of elements

    It raises an exception if it is not the case.

    :param config_id: configuration key in the configuration dictionary
    :type config_id: str
    :param config: configuration list
    :type config: list
    :param config_type: used to set the right number of
        elements, one of the following: "Video", "Signal", "Interval",
        "Threshold" or "YRange" (otherwise nothing happens)
    :type config_type: str
    :param flag_long_rec: specify if configuration in the context of
        :class:`.ViSiAnnoTLongRec`, otherwise :class:`.ViSiAnnoT` (it has an
        impact on "video", "signal" and "interval")
    :type flag_long_rec: bool
    """

    # get the right number of elements
    if config_type == "Video":
        if flag_long_rec:
            n = 5

        else:
            n = 4

    elif config_type == "Signal" or config_type == "Interval":
        if flag_long_rec:
            n = 8

        else:
            n = 7

    elif config_type == "Threshold":
        n = 2

    elif config_type == "YRange":
        n = 2

    else:
        n = None

    if n is not None:
        # get number of elements in configuration
        m = len(config)

        # check if wrong number of elements in configuration
        if n != m:
            raise Exception(
                "Wrong number of elements in signal configuration %s: %d "
                "instead of %d" % (config_id, m, n)
            )


class Configuration():
    def __init__(
        self, lay_parent, position, config_type, nb_level, elt_list,
        default_config_list, help_text='', config_base_name="config_",
        pos_dir=None, flag_dir_identical=False, flag_key=False,
        parent_config=None, children_config_name_list=[]
    ):
        """
        Class defining a configuration and its widget

        The widget is contained in :attr:`.Configuration.lay` and
        :attr:`.group_box`. The group box is added to the input window stored
        in the attribute :attr:`.lay_parent`.

        The configuration dictionary is stored in the attribute
        :attr:`.dict`.

        There are 3 callback methods for user interaction:

        - :meth:`.add_config_callback` => adding a
          (sub-)configuration
        - :meth:`.delete_configuration` => deleting a
          (sub-)configuration
        - :meth:`.set_directory` => setting the directory where to
          find data (if necessary)

        We can add a new configuration to the widget thanks to the push button
        "Add" (contained in :attr:`.button_group_add`).
        This will add an instance of QtWidgets.QGridLayout to
        :attr:`.Configuration.lay`, that we call a configuration grid.
        This configuration grid is contained in an instance of
        QtWidgets.QGroupBox. The configuration grids are stored in the list
        :attr:`.config_grid_list` and the configuration group
        boxes are stored in the list
        :attr:`.config_group_box_list`.

        On the one hand, for a given configuration grid, we can have a single
        configuration list to set, in this case :attr:`.nb_level`
        is set to 1. For example, this is the case for video configuration: for
        a given camera ID, there is only 1 video file to display.

        On the other hand, for a given configuration grid, we can have a list
        of configuration lists to set, in this case
        :attr:`.nb_level` is set to 2. For example, this the case
        for signal configuration: for a given signal type, there can be several
        data to plot on the same widget.

        The number of sub-configurations in each configuration grid is stored
        in the list :attr:`.nb_sub_list`.

        :param lay_parent: parent layout where the configuration group box is
            added
        :type lay_parent: QtWidgets.QGridLayout
        :param position: position of the configuration widget in the layout of
            the input window, length 2 ``(row, col)`` or 4
            ``(row, col, rowspan, colspan)``
        :type position: tuple of integers
        :param config_type: configuration type, see
            :attr:`.ConfigurationWindow.config_type_list`
        :type config_type: str
        :param nb_level: number of nesting levels for a configuration list,
            typically 1 (video) or 2 (signal)
        :type nb_level: int
        :param elt_list: list of the elements defining a configuration list
            in the group box, the length is equal to the length of a
            configuration list, each element is a tuple of length 3:

            - (*str*) Type of widget for the element, might be one of the
              following:

                - ``"edit"`` (QLineEdit, the value is a string),
                - ``"edit_freq"`` (QLineEdit, the value is converted to a float
                  if necessary, otherwise stick to a string),
                  ``"edit_float"`` (QLineEdit, the value is converted to a
                  float or an exception is raised if conversion failed),
                - ``"edit_literal"`` (QLineEdit, ``ast.literal_eval`` is
                  applied on the value, so that ``None`` or dictionary are
                  retrieved),
                - ``"spin"`` (QSpinBox, the value is an integer),
            - (*int*) Number of widgets for the element (for example, RGB color
              might be defined as 3 spin boxes, then the value is a tuple of 3
              elements),
            - (*dict*) Keyword parameters to pass to the element widget
              constructor (for example, for ``"spin"``, ``{"minimum": 0,
              "maximum": 255}``)
        :type elt_list: list
        :param default_config_list: default configuration list to display when
            adding a (sub-)configuration, make sure to give a nested list if
            ``nb_level`` equals 2
        :type default_config_list: list
        :param help_text: text to display in the help window, describing the
            different elements of a configuration list
        :type help_text: str
        :param config_base_name: base name of the configuration keys in
            :attr:`.dict`, the index of the configuration (in order of
            creation) is appended to ``config_base_name``
        :type config_base_name: str
        :param pos_dir: index of the widget element in ``elt_list`` which is a
            directory, it is then linked to a push button that opens a dialog
            window for selecting a directory
        :type pos_dir: int
        :param flag_dir_identical: in case ``pos_dir`` is not ``None``, specify
            if the directories of the different configurations must be the
            same, implying that when the directory of one configuration is
            modified, the directory of the other configurations is also modifed
            (currently only working when modifying directory with push button)
        :type flag_dir_identical: bool
        :param flag_key: specify if the configuration key can be modified
            thanks to a line edit (puts a QLineEdit widget element on the
            left side of each configuration)
        :type flag_key: bool
        :param parent_config: parent configuration, if a parent
            configuration is specified, then the configuration keys of
            :attr:`.dict` are forced to be the same as in the
            configuration parent dictionary
        :type parent_config: :class:`.Configuration`
        :param children_config_name_list: list of strings with the name of
            children configurations
        :type children_config_name_list: list
        """

        #: (*QtWidgets.QGridLayout*) See first positional argument of
        #: :class:`.Configuration` constructor
        self.lay_parent = lay_parent

        #: (*str*) See third positional argument of :class:`.Configuration`
        #: constructor
        self.type = config_type

        #: (*int*) Nesting level of configuration list, either ``1`` or ``2``
        #:
        #: - ``1``: single list (single line in configuration grid)
        #: - ``2``: list of lists (ability to add sub-configuration in
        #:   a configuration grid)
        #:
        #: The value of this attribute depends on the value of
        #: :attr:`.type`, as follows:
        #:
        #: - ``"Video"``: 1
        #: - ``"Signal"``: 2
        #: - ``"Interval"``: 2
        #: - ``"Threshold"``: 2
        #: - ``"YRange"``: 1
        #: - ``"AnnotEvent"``: 1
        #: - ``"AnnotImage"``: 1
        self.nb_level = nb_level

        #: (*list*) See fifth positional argument of :class:`.Configuration`
        #: constructor
        self.elt_list = elt_list

        #: (*int*) See sixth positional argument of :class:`.Configuration`
        #: constructor
        self.default_config_list = default_config_list

        #: (*int*) See keyword argument ``flag_dir_identical`` of
        #: :class:`.Configuration` constructor
        self.flag_dir_identical = flag_dir_identical

        #: (*int*) See keyword argument ``flag_key`` of :class:`.Configuration`
        #: constructor
        self.flag_key = flag_key

        #: (*int*) See keyword argument ``pos_dir`` of :class:`.Configuration`
        #: constructor
        self.pos_dir = pos_dir

        #: (*int*) Index of the widget element in the configuration grid which
        #: is a directory, it is then linked to a push button that opens a
        #: dialog window for selecting a directory
        #:
        #: It is equal to :attr:`.pos_dir`, unless :attr:`.flag_key` is set to
        #: ``True``, which implies that a QLineEdit is added at the beginning
        #: of the configuration grid, so the index is incremented by 1.
        self.pos_dir_grid = self.pos_dir
        if self.flag_key and self.pos_dir is not None:
            self.pos_dir_grid += 1

        #: (*int*) See keyword argument ``config_base_name`` of
        #: :class:`.Configuration` constructor
        self.config_base_name = config_base_name

        #: (:class:`.Configuration`) See keyword argument ``parent_config`` of
        #: :class:`.Configuration`
        self.parent_config = parent_config

        #: (*list*) Instances of :class:`.Configuration` containing the
        #: children configurations
        #:
        #: When a configuration is deleted, the children configuration with the
        #: same key are deleted as well.
        self.children_configuration_list = []

        #: (*dict*) Configuration dictionary, each item corresponds to one
        #: configuration grid of :attr:`.config_grid_list`, key is the
        #: configuration identifier (generated with :attr:`.config_base_name`),
        #: value is the configuration list (nested list in case of
        #: :attr:`.nb_level` equal to ``2``)
        #:
        #: The content of a configuration list depends on :attr:`.elt_list`,
        #: which specifies the type of its elements.
        #:
        #: Currently, 7 instances of :class:`.Configuration` are created in
        #: :class:`.ConfigurationWindow` (see :attr:`.config_type_list` for
        #: the corresponding configuration types). Here is the content of the
        #: configuration list according to the conifguration type:
        #:
        #: - ``"Video"`` (:attr:`.nb_level` is ``1``)
        #:
        #:      - (*str*) Directory where to find video files
        #:      - (*str*) File pattern
        #:      - (*str*) Delimiter for finding timestamp in file name
        #:      - (*str*) Position of the timestamp in file name after
        #:        splitting with delimiter
        #:      - (*str*) Format of timestamp string in file name
        #:
        #: - ``"Signal"`` (:attr:`.nb_level` is ``2`` => configuration list is
        #:   nested, configuration key is the name of the signal widget in
        #:   :class:`.ViSiAnnoT`)
        #:
        #:      - (*str*) Directory where to find data files
        #:      - (*str*) Key to access the data (in case of .h5 or .mat data
        #:        files)
        #:      - (*int* or *str*) Signal frequency, ``0`` if 2D data with
        #:        timestamps, it might be a string with the path to the key
        #:        containing the frequency in a .h5 or .mat file
        #:      - (*str*) File pattern
        #:      - (*str*) Delimiter for finding timestamp in file name
        #:      - (*str*) Position of the timestamp in file name after
        #:        splitting with delimiter
        #:      - (*str*) Format of timestamp string in file name
        #:      - (*dict*) Plot style (default is ``None``)
        #:
        #: - ``"AnnotEvent"`` (:attr:`.nb_level` is ``1``, configuration key is
        #:   the label)
        #:
        #:      - (*tuple*) RGB color
        #:
        #: - ``"AnnotImage"`` (:attr:`.nb_level` is ``1``)
        #:
        #:      - (*str*) Label
        #:
        #: - ``"Interval"`` (:attr:`.nb_level` is ``2`` => configuration list
        #:   is nested, child of ``Signal``)
        #:
        #:      - (*str*) Directory where to find data files
        #:      - (*str*) Key to access the data (in case of .h5 or .mat data
        #:        files)
        #:      - (*int* or *str*) Signal frequency, ``0`` if 2D data with
        #:        timestamps, it might be a string with the path to the key
        #:        containing the frequency in a .h5 or .mat file
        #:      - (*str*) File pattern
        #:      - (*str*) Delimiter for finding timestamp in file name
        #:      - (*str*) Position of the timestamp in file name after
        #:        splitting with delimiter
        #:      - (*str*) Format of timestamp string in file name
        #:      - (*tuple*) RGB color
        #:
        #: - ``"Threshold"`` (:attr:`.nb_level` is ``1``, child of ``Signal``)
        #:
        #:      - (*str*) Threshold value
        #:      - (*tuple*) RGB color
        #:
        #: - ``"YRange"`` (:attr:`.nb_level` is ``1``, child of ``Signal``)
        #:
        #:      - (*float*) Minimum value to display on Y axis in the
        #:        corresponding signal widget
        #:      - (*float*) Maximum value to display on Y axis in the
        #:        corresponding signal widget
        self.dict = {}

        #: (*list*) Instances of QtWidgets.QGridLayout containing the
        #: configuration grids (same order as :attr:`.config_group_box_list`),
        #: each grid corresponds to one key of :attr:`.dict`
        self.config_grid_list = []

        #: (*list*) Instances of QtWidgets.QGroupBox containing the
        #: configuration grids (same order as :attr:`.config_grid_list`),
        #: each group box corresponds to one key of :attr:`.dict`
        self.config_group_box_list = []

        #: (*list*) Integers with the number of sub-configurations for each
        #: configuration grid (same order as :attr:`.config_grid_list`)
        #:
        #: If :attr:`.nb_level` is equal to 1, then each element
        #: equals 1.
        #:
        #: An example of configuration:
        #:
        #: - config_key_1
        #:
        #:      - sub_config_11
        #:      - sub_config_12
        #:
        #: - config_key_2
        #:
        #:      - sub_config_21
        #:
        #: - config_key_3
        #:
        #:      - sub_config_31
        #:      - sub_config_32
        #:      - sub_config_33
        #:
        #: It will give ``self.nb_sub_list == [2, 1, 3]``.
        self.nb_sub_list = []

        #: (*list*) Each element is a list with the configuration grid index
        #: and the sub-configuration index corresponding to the push buttons
        #: "Change directory"/"Delete"
        #:
        #: In case of :attr:`.nb_level` equal to 2, the
        #: sub-configurations are not necessarily added in the order of
        #: display, so the push buttons "Change directory" / "Delete" are not
        #: necessarily added in the order of display. As a consequence, the
        #: button groups :attr:`.button_group_del` and
        #: :attr:`.button_group_dir` contain the push buttons in
        #: the order of addition, which is decorrelated to the the order of
        #: display.
        #:
        #: When listening to the callbacks methods
        #: :meth:`.delete_configuration` and
        #: :meth:`.set_directory`, the input argument is the push
        #: button index in the button group. We cannot link it explicitely to
        #: the configuration grid position. So, when a push button is added to
        #: the button group, the new sub-configuration grid position is
        #: appended to the list :attr:`.btn_id_to_config_id`.
        #:
        #: The position is expressed as a list with 2 integers:
        #:
        #: - index of the configuration grid (index in the list
        #:   :attr:`.config_grid_list`)
        #: - index of the sub-configuration grid inside the configuration grid
        #:
        #: An example of configuration with the zero-indexed order of addition
        #: (which gives the button index in the button group):
        #:
        #: - config_key_1
        #:
        #:      - sub_config_11 => 0
        #:      - sub_config_12 => 5
        #:
        #: - config_key_2
        #:
        #:      - sub_config_21 => 1
        #:
        #: - config_key_3
        #:
        #:      - sub_config_31 => 2
        #:      - sub_config_32 => 3
        #:      - sub_config_33 => 4
        #:
        #: It will give ``btn_id_to_config_id ==
        #: [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2], [0, 1]]``.
        self.btn_id_to_config_id = []

        #: (*int*) Number of rows in the group box header
        #:
        #: In all cases it equals ``1``.
        self.nb_rows_header = 1

        #: (*int*) Number of columns spanned by the configuration grids in the
        #: layout of :attr:`.group_box`, equivalent to the number of widgets in
        #: the group box header minus 1
        #:
        #: Computed as ``2 + len(children_config_name_list)``: in the group box
        #: header, there are two widgets ("Help" push button / check box for
        #: identical directories or empty QLabel) and as many push buttons as
        #: children configurations. The configuration grids must span all those
        #: widgets.
        self.config_grid_span = 2 + len(children_config_name_list)

        #: (*QtWidgets.QGridLayout*) Layout filling the group box
        #: :attr:`.group_box`
        self.lay = None

        #: (*QtWidgets.QGroupBox*) Group box where configuration grids are
        #: created
        self.group_box = None

        #: (*QtWidgets.QCheckBox*) Check box to specify if all directories
        #: are identical (when using the push button for changing directory),
        #: may be ``None``
        self.check_box = None

        #: (*QtWidgets.QButtonGroup*) Group of buttons for displaying
        #: children configuration windows
        self.button_group_children = QtWidgets.QButtonGroup()

        #: (*QtWidgets.QButtonGroup*) Group of buttons for changing directory
        self.button_group_dir = QtWidgets.QButtonGroup()

        #: (*QtWidgets.QButtonGroup*) Group of buttons for adding
        #: (sub-)configurations
        self.button_group_add = QtWidgets.QButtonGroup()

        #: (*QtWidgets.QButtonGroup*) Group of buttons for deleting
        #: (sub-)configurations
        self.button_group_del = QtWidgets.QButtonGroup()

        #: (*QtWidgets.QPushButton*) Push button for displaying help window
        self.button_help_show = None

        # create group box
        self.create_configuration_group_box(
            position, children_config_name_list
        )

        #: (*QtWidgets.QWidget*) Container of help window
        self.win_help = None

        #: (*QtWidgets.QPushButton*) Push button for hding help window
        self.button_help_hide = None

        # create help window
        self.create_help_window(help_text)

        # listen to callbacks
        self.button_group_add.buttonClicked[int].connect(
            self.add_config_callback
        )

        self.button_group_del.buttonClicked[int].connect(
            self.delete_configuration
        )

        self.button_group_dir.buttonClicked[int].connect(self.set_directory)

        self.button_help_show.clicked.connect(self.win_help.show)
        self.button_help_hide.clicked.connect(self.win_help.hide)


    def add_child_configuration(self, config_child):
        """
        Adds a child configuration to :attr:`.children_configuration_list`

        :param config_child: child configuration
        :type config_child: :class:`.Configuration`
        """

        self.children_configuration_list.append(config_child)


    def create_configuration_group_box(
        self, position, children_config_name_list
    ):
        """
        Creates group box and adds it to :attr:`.lay_parent`

        At this point, the group box contains only the header and one or
        several push buttons to add configurations.

        NB: make sure that :attr:`.type` is in
        :attr:`.ConfigurationWindow.config_type_list`.

        It sets the following attributes:

        - :attr:`.Configuration.lay`
        - :attr:`.group_box`
        - :attr:`.check_box`
        - :attr:`.button_help_show`
        - :attr:`.button_group_children`
        - :attr:`.button_group_add`

        :param position: position of the configuration group box in
            :attr:`.lay_parent`, length 2 ``(row, col)`` or
            4 ``(row, col, rowspan, colspan)``
        :type position: tuple
        :param children_config_name_list: names of the children configurations
        :type children_config_name_list: list
        """

        # create configuration group box
        self.lay, self.group_box = pyqt_overlayer.add_group_box(
            self.lay_parent, position, self.type
        )

        # create push button for help text
        self.button_help_show = pyqt_overlayer.add_push_button(
            self.lay, (0, 0), "Help", width=100
        )

        # check if check box needed for identical directories
        if self.flag_dir_identical:
            # create check box for setting identical directories
            self.check_box = QtWidgets.QCheckBox("All directories identical")
            self.check_box.setChecked(True)
            self.lay.addWidget(self.check_box, 0, 1)

        else:
            # add empty QLabel (for layout purpose)
            label_empty = QtWidgets.QLabel()
            self.lay.addWidget(label_empty, 0, 1)

        # create push buttons for children configurations if necessary
        for ite_child, children_config_name in \
                enumerate(children_config_name_list):
            # create push button for adding intervals
            push_button = pyqt_overlayer.add_push_button(
                self.lay,
                (0, 2 + ite_child),
                children_config_name
            )
            self.button_group_children.addButton(push_button, ite_child)

        # create push buttons for adding configuration
        push_button_add = pyqt_overlayer.add_push_button(
            self.lay, (0, self.config_grid_span), "Add", width=100
        )
        self.button_group_add.addButton(push_button_add, 0)


    def create_help_window(self, help_text):
        """
        Creates help window without showing it

        It has two widgets: a QLabel with the text and a push button for
        closing the window.

        :param help_text: text to be displayed
        :type help_text: str
        """

        # create window and layout
        self.win_help, lay = pyqt_overlayer.create_window(
            size=(800, 100), title="Help %s" % self.type, flag_show=False
        )

        # create scroll area
        scroll_lay, _ = pyqt_overlayer.add_scroll_area(lay, (0, 0))

        # add label with help text
        label = QtWidgets.QLabel(help_text)
        lay.addWidget(label, 0, 0)
        scroll_lay.addWidget(label)

        # add push button for closing help window
        self.button_help_hide = pyqt_overlayer.add_push_button(
            lay, (1, 0), "Close", width=80
        )


    def get_configuration_simple(self, config_grid, row_ind):
        """
        Reads the values filled in a single row of a configuration grid in
        order to get the corresponding configuration list

        In case of :attr:`.nb_level` equal to ``2``, it does nor return a
        nested configuration list, but the sub-configuration list at index
        ``row_ind``.

        In case of :attr:`.nb_level` equal to ``2``, set ``row_ind`` to ``0``.

        :param config_grid: configuration grid
        :type config_grid: QtWidgets.QGridLayout
        :param row_ind: index of the row in the configuration grid from which
            to retrieve the (sub-)configuration list
        :type row_ind: int
        """

        # check if configuration key is in the configuration grid
        if self.flag_key:
            # skip first widget element of the configuration grid
            # (configuration key)
            start_col_ind = 1

        else:
            # get all widget elements of the configuration grid row
            start_col_ind = 0

        # initialize configuration list
        config_list = []

        # loop on elements specifying configuration grid
        for ite_elt, (elt_type, elt_nb, _) in enumerate(self.elt_list):
            # get widget
            widget = config_grid.itemAtPosition(
                row_ind, start_col_ind + ite_elt
            ).widget()

            # check number of sub-elements
            if elt_nb > 1:
                # check type
                if elt_type == "spin":
                    value = pyqt_overlayer.set_spin_box_table(
                        widget.layout(), [], False
                    )[0]

            else:
                # check type
                if "edit" in elt_type:
                    # get value in widget
                    value = widget.text()

                    if elt_type == "edit_float" or elt_type == "edit_freq":
                        if value.count('.') < 2 and value.count(',') < 2 and \
                                value.count('-') < 2 and len(value) > 0:
                            value_clean = \
                                value.replace(',', '').replace('.', '')

                            if value_clean[0] == '-':
                                value_clean = value_clean[1:]

                        else:
                            value_clean = value

                        if value_clean.isdigit():
                            value = float(value.replace(',', '.'))

                        elif elt_type == "edit_float":
                            raise Warning(
                                "Wrong value in %s configuration n°%d, "
                                "element %d, expected a float, got %s" % (
                                    self.type, row_ind + 1,
                                    start_col_ind + ite_elt + 1, value
                                )
                            )

                    elif elt_type == "edit_literal":
                        # convert "None" to None or "{...}" to a dictionary
                        value = literal_eval(value)

                elif elt_type == "spin" or elt_type == "spin_double":
                    # get value in widget
                    value = widget.value()

            # append configuration list
            config_list.append(value)

        # check if only one element
        if len(self.elt_list) == 1:
            # return the single element instead of a list
            config_list = config_list[0]

        return config_list


    def set_dictionary(self):
        """
        Sets the attribute :attr:`.dict` with the current values
        filled in the configuration grids (:attr:`config_grid_list`)

        NB: make sure that :attr:`.type` is in
        :attr:`.ConfigurationWindow.config_type_list`.
        """

        # reset configuration dictionary
        self.dict = {}

        # loop on configurations
        for ite_config, (config_grid, config_group_box) in enumerate(zip(
            self.config_grid_list, self.config_group_box_list
        )):
            # check if configuration key available in configuration grid
            if self.flag_key:
                # get configuration key
                config_key = config_grid.itemAtPosition(0, 0).widget().text()

            # check if child configuration
            elif self.parent_config is not None:
                # get configuration key
                config_key = config_group_box.title()

            else:
                # get configuration key
                config_key = "%s%d" % (self.config_base_name, ite_config)

            # check level
            if self.nb_level == 1:
                config_list = self.get_configuration_simple(config_grid, 0)

                # update configuration dictionary
                self.dict[config_key] = config_list

            else:
                # get number of sub-configurations
                nb_sub_config = self.nb_sub_list[ite_config]

                # initialize configuration list
                config_list = []

                # loop on sub-configurations
                for ite_sub in range(nb_sub_config):
                    config_sub_list = self.get_configuration_simple(
                        config_grid, ite_sub
                    )

                    # append configuration list
                    config_list.append(config_sub_list)

                # update configuration dictionary
                self.dict[config_key] = config_list


    def set_directory(self, button_id):
        """
        Callback method for directory selection

        Connected to the signal ``buttonClicked[int]`` of
        :attr:`.button_group_dir`.

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        # get configuration grid index and sub-configuration index
        config_id, sub_config_id = self.btn_id_to_config_id[button_id]

        # get configuration grid
        config_grid = self.config_grid_list[config_id]

        # get directory edit line
        edit_dir = config_grid.itemAtPosition(
            sub_config_id, self.pos_dir_grid
        ).widget()

        # open dialog window to get directory
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select directory", edit_dir.text(),
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if directory != "":
            # if box checked => all directories are identical
            if self.check_box.isChecked():
                # initialize a list of configurations
                config_list_tmp = [self]

                # get children configurations, so that their directories are
                # updated as well
                for children_config in self.children_configuration_list:
                    # check if there are directories to set
                    if children_config.check_box is not None:
                        if children_config.check_box.isChecked():
                            config_list_tmp.append(children_config)

                # loop on configurations
                for config_tmp in config_list_tmp:
                    # loop on configuration grids
                    for ite_config, config_grid_tmp in \
                            enumerate(config_tmp.config_grid_list):
                        # get number of sub-configurations
                        nb_sub_config = config_tmp.nb_sub_list[ite_config]

                        # loop on sub-configurations
                        for ite_sub_config in range(nb_sub_config):
                            # set line edit
                            config_grid_tmp.itemAtPosition(
                                ite_sub_config, self.pos_dir_grid
                            ).widget().setText(directory)

            else:
                # set line edit
                edit_dir.setText(directory)


    def add_config_callback(self, button_id):
        """
        Callback method for adding a (sub-)configuration

        Connected to the signal buttonClicked[int] of
        :attr:`.button_group_add`.

        There are two kinds of buttons:

        - ``button_id == 0``: add a configuration
        - ``button_id >= 1``: add a sub-configuration (in case of
          :attr:`.nb_level` equal to 2)

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        # intialize boolean to specify if looking for identical directory
        flag_dir_identical = False

        # check if there is a check box for identical directories
        if self.check_box is not None:
            # check if directories identical and if there is already
            # a configuration
            if self.check_box.isChecked() and len(self.dict) > 0:
                flag_dir_identical = True

        # get configuration list
        if flag_dir_identical:
            # get directory of first configuration
            dir_tmp = self.config_grid_list[0].itemAtPosition(
                0, self.pos_dir_grid
            ).widget().text()

            # check number of levels
            if self.nb_level == 1:
                # update default configuration list
                self.default_config_list[self.pos_dir] = dir_tmp

            else:
                # update default configuration list
                for sublist in self.default_config_list:
                    sublist[self.pos_dir] = dir_tmp

        # add configuration
        if button_id == 0:
            # check if no parent configuration
            if self.parent_config is None:
                # get configuration key
                config_key = "%s%d" % (
                    self.config_base_name, len(self.config_grid_list) + 1
                )

            else:
                # get number of configurations
                nb_config = len(self.config_grid_list)

                # get number of configurations in parent
                nb_parent_config = len(self.parent_config.config_grid_list)

                # check if number of configurations is below the number of
                # configurations in parents
                if nb_config < nb_parent_config:
                    # set new configuration key, same as parent
                    config_key = self.parent_config.config_grid_list[
                        nb_config].itemAt(0).widget().text()

                    # get following parent configuration key if the current one
                    # already exists in configuration dictionary
                    while config_key in self.dict.keys():
                        nb_config = (nb_config + 1) % \
                            len(self.parent_config.config_grid_list)

                        config_key = self.parent_config.config_grid_list[
                            nb_config].itemAt(0).widget().text()

                else:
                    config_key = None

            # create configuration dictionary
            if config_key is None:
                config_dict = {}

            else:
                config_dict = {config_key: self.default_config_list}

            # add configuration
            self.add_configuration(config_dict)

        # add sub-configuration
        elif button_id >= 1:
            # loop on sub-configurations
            for config_sub_list in self.default_config_list:
                # add sub-configuration
                self.add_configuration_simple(
                    config_sub_list, config_id=button_id - 1,
                )


    def create_widgets_in_config_grid(
        self, config_grid, config_list, row_ind, start_col_ind
    ):
        """
        Creates widgets elements for a new configuration list in a
        configuration grid

        :param config_grid: configuration grid where to add a configuration
            list
        :type config_grid: QtWidgets.QGridLayout
        :param config_list: configuration list with the values to fill in
        :type config_list: list
        :param row_ind: index of the row in the configuration grid where to add
            the widgets elementst of the configuration list
        :type row_ind: int
        :param start_col_ind: index of the column in the configuration grid
            where to start to add widgets elements of the configuration list
        :type start_col_ind: int
        """

        # initialize column index of widget to add
        col_ind = start_col_ind

        # check number of elements in a configuration list
        if len(self.elt_list) == 1:
            # put the single element in a list
            config_list = [config_list]

        # loop on elements to create for a configuration
        for (elt_type, elt_nb, elt_params), value in \
                zip(self.elt_list, config_list):
            # check number of sub-elements
            if elt_nb > 1:
                # check element type
                if elt_type == "spin":
                    pyqt_overlayer.add_spin_box_table(
                        config_grid, (row_ind, col_ind), 1, elt_nb,
                        params=[elt_params]
                    )

                    pyqt_overlayer.set_spin_box_table(
                        config_grid.itemAtPosition(
                            row_ind, col_ind
                        ).widget().layout(),
                        [value], True
                    )

            else:
                # check element type
                if "edit" in elt_type:
                    # create line edit
                    widget = QtWidgets.QLineEdit(str(value), **elt_params)

                elif elt_type == "spin":
                    # create spin box
                    widget = QtWidgets.QSpinBox(**elt_params)
                    widget.setValue(value)

                elif elt_type == "spin_double":
                    # create spin double box
                    widget = QtWidgets.QDoubleSpinBox(**elt_params)
                    widget.setValue(value)

                # add element to configuration grid
                pyqt_overlayer.add_widget_to_layout(
                    config_grid, widget, (row_ind, col_ind)
                )

            # update column index
            col_ind += 1


    def add_configuration_simple(self, config_list, config_id=None):
        """
        Adds a single (sub-)configuration list to a configuration grid

        This method updates the following attributes:

        - :attr:`.nb_sub_list`
        - :attr:`.btn_id_to_config_id`
        - :attr:`.dict`
        - :attr:`.button_group_dir` with the created push buttons
          for directory selection (if any)
        - :attr:`.button_group_del` with the created push button
          for deleting

        :param config_list: configuration list with the values to fill in
        :type config_list: list
        :param config_id: index of the configuration grid where to add the
            (sub-)configuration, by default the last configuration grid of
            :attr:`.config_grid_list` is chosen
        :type config_id: int
        """

        # check if configuration key is in the configuration grid
        if self.flag_key:
            # skip first widget element of the configuration grid
            # (configuration key)
            start_col_ind = 1

        else:
            # get all widget elements of the configuration grid row
            start_col_ind = 0

        # get configuration grid index if necessary
        if config_id is None:
            config_id = len(self.config_grid_list) - 1

        # get configuration grid
        config_grid = self.config_grid_list[config_id]

        # get sub-configuration index (should always be 0 if number of levels
        # is 1)
        sub_ind = self.nb_sub_list[config_id]

        # create widgets in the configuration grid
        self.create_widgets_in_config_grid(
            config_grid, config_list, sub_ind, start_col_ind
        )

        # set column index
        col_ind = start_col_ind + len(self.elt_list)

        # check if directory contained in configuration grid
        if self.pos_dir is not None:
            # create push button for selecting directory
            push_button_dir = pyqt_overlayer.add_push_button(
                config_grid, (sub_ind, col_ind), "Change directory")

            # add to button group
            self.button_group_dir.addButton(
                push_button_dir, np.cumsum(self.nb_sub_list)[-1]
            )

            # update column index
            col_ind += 1

        # create push button for deleting configuration
        push_button_del = pyqt_overlayer.add_push_button(
            config_grid, (sub_ind, col_ind), "Delete"
        )

        # add to button group
        self.button_group_del.addButton(
            push_button_del, np.cumsum(self.nb_sub_list)[-1]
        )

        # update list to convert button index to configuration index
        self.btn_id_to_config_id.append(
            [config_id, self.nb_sub_list[config_id]]
        )

        # update number of sub-configurations
        self.nb_sub_list[config_id] += 1


    def add_configuration(self, config_dict):
        """
        Adds one or several configurations

        This method updates the following attributes:

        - :attr:`.config_grid_list`
        - :attr:`.config_group_box_list`
        - :attr:`.nb_sub_list`
        - :attr:`.btn_id_to_config_id`
        - :attr:`.dict`
        - :attr:`.button_group_dir` with the created push buttons
          for directory selection (if any)
        - :attr:`.button_group_del` with the created push button
          for deleting

        :param config_dict: dictionary of the configurations to add, see
            :attr:`.dict`
        :type config_dict: dict

        Each item of ``config_dict`` corresponds to one configuration, implying
        one created configuration grid. Value is a configuration list, which is
        nested if :attr:`.nb_level` is equal to ``2``, see :attr:`.dict`.
        """

        # initialize row index in the grid where to add the configuration grid
        row_start = len(self.config_grid_list) + self.nb_rows_header

        # loop on configurations
        for config_key, config_list in config_dict.items():
            # create configuration grid
            config_grid, config_group_box = pyqt_overlayer.add_group_box(
                self.lay, (row_start, 0, 1, self.config_grid_span)
            )

            # update lists
            self.config_grid_list.append(config_grid)
            self.config_group_box_list.append(config_group_box)
            self.nb_sub_list.append(0)

            # check if child
            if self.parent_config is not None:
                # set group box title as configuration key
                config_group_box.setTitle(config_key)

            # check if configuration key must be available in a line edit
            if self.flag_key:
                # create line edit for configuration key
                widget = QtWidgets.QLineEdit(config_key)
                pyqt_overlayer.add_widget_to_layout(config_grid, widget, (0, 0))

                # listen to callback
                widget.textChanged.connect(self.config_key_changed)

            # configuration level 1 => simple configuration
            if self.nb_level == 1:
                # check number of elements in configuration list
                check_configuration(config_key, config_list, self.type)

                # add configuration
                self.add_configuration_simple(config_list)

            # configuration level 2 => sub-configurations
            elif self.nb_level == 2:
                # create push button for adding a sub-configuration
                push_button = pyqt_overlayer.add_push_button(
                    self.lay, (row_start, self.config_grid_span), "Add sub"
                )

                # add push button to group button
                self.button_group_add.addButton(
                    push_button, len(self.config_grid_list)
                )

                # loop on sub-configurations
                for config_sub_list in config_list:
                    # check number of elements in configuration list
                    check_configuration(config_key, config_sub_list, self.type)

                    # add sub-configuration
                    self.add_configuration_simple(config_sub_list)

            # update index of the row in the grid where to add the
            # configuration grid
            row_start += 1

        # update configuration dictionary
        self.dict.update(config_dict)


    def config_key_changed(self, text):
        """
        Callback method for updating configuration key, as well as those of the
        children configurations, when it is edited in the QLineEdit

        Connected to the signal ``textChanged`` of the instances of
        QtWidgets.QLineEdit created in :meth:`.add_configuration`.

        It sets the attribute :attr:`.dict` and the configuration
        dictionary of the children configurations.

        :param text: updated configuration key
        :type text: str
        """

        # get index of the changed configuration grid
        ind = [
            config_grid.itemAtPosition(0, 0).widget().text()
            for config_grid in self.config_grid_list
        ].index(text)

        # get original configuration key
        config_key = list(self.dict.keys())[ind]

        # set configuration dictionary
        self.set_dictionary()

        # loop on children configuration
        for child_config in self.children_configuration_list:
            # check if original configuration key is in child configuration
            # dictionary
            if config_key in child_config.dict:
                # loop on configuration group boxes
                for child_config_group_box in \
                        child_config.config_group_box_list:
                    # check group box title
                    if child_config_group_box.title() == config_key:
                        # set group box title with new text
                        child_config_group_box.setTitle(text)

                # set child configuration dictionary
                child_config.set_dictionary()


    def delete_configuration(self, button_id):
        """
        Callback method for deleting a (sub-)configuration

        Connected to the signal buttonClicked[int] of
        :attr:`.button_group_del`.

        This method updates the following attributes:

        - :attr:`.dict`
        - :attr:`.config_grid_list`
        - :attr:`.config_group_box_list`
        - :attr:`.nb_sub_list`

        :param button_id: index of the button that has been pushed
        :type button_id: int
        """

        # update configuration dictionary with current values filled in
        self.set_dictionary()

        # get flatten index of the (sub-)configuration grid to delete
        config_id, sub_config_id = self.btn_id_to_config_id[button_id]

        # get configuration key corresponding to the configuration grid to
        # delete
        config_key = list(self.dict.keys())[config_id]

        # check level
        if self.nb_level == 1:
            # delete configuration from video dictionary
            del self.dict[config_key]

        elif self.nb_level == 2:
            # delete sub-configuration
            if self.nb_sub_list[config_id] > 1:
                del self.dict[config_key][sub_config_id]

            # delete whole configuration
            else:
                del self.dict[config_key]

                # loop on children configurations
                for child_config in self.children_configuration_list:
                    # check if child configuration must be deleted
                    if config_key in child_config.dict.keys():
                        del child_config.dict[config_key]
                        child_config.reset_display()

        # reset display
        self.reset_display()


    def reset_display(self):
        """
        Deletes the configuration grids in :attr:`.config_grid_list`) and
        replaces them with :attr:`.ConfigurationWindow.dict`

        This method updates the following attributes:

        - :attr:`.config_grid_list`
        - :attr:`.config_group_box_list`
        - :attr:`.nb_sub_list`
        """

        # delete the configuration widgets
        pyqt_overlayer.delete_widgets_from_layout(
            self.lay, len(self.config_grid_list) * self.nb_level
        )

        # reset the list of configuration grids
        self.config_grid_list = []

        # reset the list of configuration group boxes
        self.config_group_box_list = []

        # reset the list of number of sub-configurations for each configuration
        self.nb_sub_list = []

        self.btn_id_to_config_id = []

        # display the values of the configuration dictionary
        self.add_configuration(self.dict)
