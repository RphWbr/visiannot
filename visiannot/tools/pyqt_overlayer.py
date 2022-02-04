# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with sub-classes and functions for GUI creation with PyQt5

See https://pypi.org/project/PyQt5 and
https://doc.qt.io/qt-5/reference-overview.html
"""


from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
from sys import flags, argv


# *************************************************************************** #
# ************************* QtWidgets subclasses **************************** #
# *************************************************************************** #

class ComboBox(QtWidgets.QComboBox):
    """
    Subclass of QtWidgets.QComboBox so that key press events are ignored
    """

    def keyPressEvent(self, ev):
        """
        Re-implemented so that key press events are ignored
        """

        pass


class PushButton(QtWidgets.QPushButton):
    """
    Subclass of QtWidgets.QPushButton so that key press events are ignored
    """

    def keyPressEvent(self, ev):
        """
        Re-implemented so that key press events are ignored
        """

        pass


class ScrollArea(QtWidgets.QScrollArea):
    """
    Subclass of QtWidgets so that wheel events are ignored
    """

    def wheelEvent(self, ev):
        """
        Re-implemented so that wheel events are ignored
        """

        pass


# *************************************************************************** #
# ******************************* Functions ********************************* #
# *************************************************************************** #

def initialize_gui():
    """
    Creates a GUI application for display

    :returns: instance of QtCore.QCoreApplication or QtWidgets.QApplication
    """

    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(argv)

    return app


def infinite_loop_gui(app):
    """
    Creates an event loop for a given GUI application, so that the windows
    do not disappear right after being created

    :param app: GUI application
    :type app: QtCore.QCoreApplication or QtWidgets.QApplication
    """

    if (flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app.instance().exec_()


def infinite_loop_gui_parallel(app, win):
    """
    Creates a specific event loop for a given window while an event loop is
    already running, the specific event loop is stopped when the window is
    closed

    :param app: GUI application
    :type app: QtCore.QCoreApplication or QtWidgets.QApplication
    :param win: window on which the parallel event loop is applied
    :type win: QtWidgets.QWidget
    """

    while win.isVisible():
        app.processEvents()
    app.processEvents()


def get_directory_dialog(desc_text="Select directory", dir_root=None):
    """
    Opens a dialog window in order to select a directory

    :param desc_text: short description text to be displayed as the dialog
        window title
    :type desc_text: str
    :param dir_root: initial directory where to go when launching the dialog
        window, default current working directory
    :type dir_root: str
    """

    app = initialize_gui()
    dir_selected = QFileDialog.getExistingDirectory(
        None, desc_text, dir_root, QFileDialog.ShowDirsOnly
    )
    app.quit()

    return dir_selected


def add_spin_box_table(grid, pos, nb_rows, nb_cols, name="", params={}):
    """
    Adds a table of spin boxes to an instance of QtWidgets.QGridLayout

    The spin boxes are contained in an instance of QtWidgets.QGroupBox filled
    by an instance of QtWidgets.QGridLayout, see func:`.add_group_box`.

    :param grid: parent layout where the spin boxes are added
    :type grid: QtWidgets.QGridLayout
    :param pos: position of the group box containing the spin boxes in the
        parent layout, length 2 ``(row, col)`` or 4
        ``(row, col, rowspan, colspan)``
    :type pos: tuple of integers
    :param nb_rows: number of rows in the table of spin boxes
    :type nb_rows: int
    :param nb_cols: number of columns in the table of spin boxes
    :type nb_cols: int
    :param name: name of the group box containing the spin boxes
    :type name: str
    :param params: keyword arguments of the constructor of QtWidgets.QSpinBox
        (e.g. {"minimum": 0, "maximum": 255}), it might be a nested list of
        length ``nb_rows`` x ``nb_cols`` if the parameters differ from on spin
        box to another
    :type params: dict or list

    :returns:
        - **grid_sub** -- instance of QtWidgets.QGridLayout containing the
          table of spin boxes
        - **goup_box**  -- instance of QtWidgets.QGroupBox containing the table
          of spin boxes
    """

    # create group box
    grid_sub, group_box = add_group_box(grid, pos, name)

    # add spin boxes in the group box
    for i in range(nb_rows):
        for j in range(nb_cols):
            if isinstance(params, list):
                spin_box = QtWidgets.QSpinBox(**params[i][j])

            else:
                spin_box = QtWidgets.QSpinBox(**params)

            grid_sub.addWidget(spin_box, i, j)

    return grid_sub, group_box


def set_spin_box_table(grid, value_list_list, flag_display):
    """
    Sets the values of a table of spin boxes from an input list of lists
    or returns the values of a table of spin boxes

    :param grid: layout containing only the table of spin boxes, see
        :func:`.add_spin_box_table` for creating one
    :type grid: QtWidgets.QGridLayout
    :param value_list_list: in case of ``flag_display`` set to ``True``, each
        element is a list of values for setting the table of spin boxes --
        otherwise, let it be an empty list
    :type value_list_list: list
    :param flag_display: specify if displaying values in the table of spin
        boxes
    :type flag_display: bool

    :returns: each element is a list containing the values in the table of spin
        boxes (same as input argument ``value_list_list`` in case of
        ``flag_display`` set to ``True``)
    :rtype: list
    """

    # if setting value_list_list, reset its value
    if not flag_display:
        value_list_list = []

    # get number of columns in the grid
    nb_cols = grid.columnCount()

    # get number of rows in the grid
    nb_rows = grid.rowCount()

    # loop on the number of rows
    for i in range(nb_rows):
        # initialize temporary list for setting value_list_list
        list_tmp = []

        # loop on the number of columns
        for j in range(nb_cols):
            # get spin box
            spin_box = grid.itemAtPosition(i, j).widget()

            # if setting display, check length of value_list_list
            if flag_display:
                if i < len(value_list_list):
                    # set spin box value
                    spin_box.setValue(value_list_list[i][j])
                else:
                    # set spin box value
                    spin_box.setValue(0)

            # if setting value_list_list
            else:
                # append temporary list
                list_tmp.append(spin_box.value())

        if not flag_display:
            value_list_list.append(list_tmp)

    return value_list_list


def add_line_edit_list(grid, pos, nb_rows, name=""):
    """
    Adds a list of line edits to a layout

    The line edits are contained in an instance of QtWidgets.QGroupBox filled
    by an instance of QtWidgets.QGridLayout, see
    :func:`.add_group_box`.

    :param grid: parent layout where the line edits are added
    :type grid: QtWidgets.QGridLayout
    :param pos: position of the group box containing the spin boxes in the
        parent layout, length 2 ``(row, col)`` or 4
        ``(row, col, rowspan, colspan)``
    :type pos: tuple of integers
    :param nb_rows: number of rows in the list of line edits
    :type nb_rows: int
    :param name: name of the group box containing the spin boxes
    :type name: str

    :returns:
        - **grid_sub** -- instance of QtWidgets.QGridLayout containing the
          instances of QLineEdit
        - **goup_box**  -- instance of QtWidgets.QGroupBox containing the
          instances of QLineEdit
    """

    # create group box
    grid_sub, group_box = add_group_box(grid, pos, name)

    # add spin boxes in the group box
    for i in range(nb_rows):
        edit = QtWidgets.QLineEdit()
        grid_sub.addWidget(edit, i, 0)

    return grid_sub, group_box


def set_line_edit_list(grid, value_list, flag_display):
    """
    Sets the values of a list of lines edits from an input list or returns the
    values of a table of lines edits

    :param grid: layout containing only the list of lines edits, see
        :func:`.add_line_edit_list` for creating one
    :type grid: QtWidgets.QGridLayout
    :param value_list: in case of ``flag_display`` set to ``True``, each
        element is a string for setting the list of lines edits --
        otherwise, let it be an empty list
    :type value_list: list
    :param flag_display: specify if displaying values in the list of lines
        edits
    :type flag_display: bool

    :returns: list of values contained in the list of lines edits
        (same as input argument ``value_list`` in case of ``flag_display`` set
        to ``True``)
    :rtype: list
    """

    # if setting value_list, reset its value
    if not flag_display:
        value_list = []

    # get number of rows in the grid <=> number of items in the list
    nb_rows = grid.count()

    # loop on the number of rows
    for i in range(nb_rows):
        # get edit text
        edit = grid.itemAtPosition(i, 0).widget()

        if flag_display:
            if i < len(value_list):
                # set edit text
                edit.setText(value_list[i])
            else:
                # set edit text
                edit.setText("")

        else:
            # append value list
            value_list.append(edit.text())

    return value_list


def add_widget_to_layout(lay, wid, wid_pos):
    """
    Adds a widget to a layout

    an instance of QtWidgets.QGridLayout (or any )

    It raises an error if the widget position is not a tuple/list of length 2
    or 4.

    :param lay: parent layout where the widget is added (may be any other
        layout class with a method ``addWidget``)
    :type lay: QtWidgets.QGridLayout
    :param wid: widget to be added, it must be an instance of a sub-class of
        QtWidgets.QWidget
    :param wid_pos: position of the widget in the parent layout, length 2
        ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type wid_pos: tuple of integers
    """

    wpl = len(wid_pos)
    if wpl != 2 and wpl != 4 and not isinstance(wid_pos, tuple) and \
            not isinstance(wid_pos, list):
        raise ValueError('Widget postition incorrect: ' + str(wid_pos))
    else:
        if wpl == 2:
            lay.addWidget(wid, wid_pos[0], wid_pos[1])
        elif wpl == 4:
            lay.addWidget(wid, wid_pos[0], wid_pos[1], wid_pos[2], wid_pos[3])


def add_group_box(layout, position, title=""):
    """
    Adds a group box to a grid layout

    Another grid layout is created to fill the group box.

    The function raises an error if the length of ``position`` is not 2 or 4.

    :param layout: parent layout where the group box is added
    :type layout: QtWidgets.QGridLayout
    :param position: position of the group box in the parent layout, length 2
        ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type position: tuple of integers
    :param title: group box title
    :type title: str

    :returns:
        - **grid** (*QtWidgets.QGridLayout*) -- layout filling the group box
        - **group_box** (*QtWidgets.QGroupBox*)
    """

    # create the group box
    group_box = QtWidgets.QGroupBox(title)

    # create grid layout and set it to the group box
    grid = QtWidgets.QGridLayout(group_box)

    # add the group box to the layout
    add_widget_to_layout(layout, group_box, position)

    return grid, group_box


def add_push_button(
    layout, position, text, width=0, flag_enable_key_interaction=True,
    color=None
):
    """
    Adds a push button to a grid layout

    The function raises an error if the length of ``position`` is not 2 or 4.

    :param layout: parent layout where the push button is added
    :type layout: QtWidgets.QGridLayout
    :param position: position of the button in the parent layout, length 2
        ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type position: tuple of integers
    :param text: text displayed in the push button
    :type text: str
    :param width: width of the push button in pixels, set to ``0`` for
        automatic
    :type width: int
    :param flag_enable_key_interaction: specify if key press interaction is
        enabled
    :type flag_enable_key_interaction: bool
    :param color: color in RGB format
    :type color: tuple

    :returns: push button item (instance of *QtWidgets.QPushButton* or
        :class:`.PushButton`)
    """

    # create push button
    if flag_enable_key_interaction:
        push_button = QtWidgets.QPushButton(text)

    else:
        push_button = PushButton(text)

    # set width
    if width > 0:
        push_button.setFixedWidth(width)

    # set key interaction
    push_button.setAutoDefault(flag_enable_key_interaction)

    # set color
    if color is not None:
        push_button.setStyleSheet(
            "QPushButton { color: rgb(%d,%d,%d) }" % color
        )

    # add push button to the layout
    add_widget_to_layout(layout, push_button, position)

    return push_button


def add_radio_button(layout, position, text, flag_checked=False, color=None):
    """
    Adds a radio button to a grid layout

    The function raises an error if the length of ``position`` is not 2 or 4.

    :param layout: parent layout where the radio button is added
    :type layout: QtWidgets.QGridLayout
    :param position: position of the button in the parent layout, length 2
        ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type position: tuple of integers
    :param text: text displayed next to the radio button
    :type text: str
    :param flag_checked: specify if button is initially checked
    :type flag_checked: bool
    :param color: color in RGB format
    :type color: tuple

    :returns: radio button item
    :rtype: QtWidgets.QRadioButton
    """

    # create radio button
    radio_button = QtWidgets.QRadioButton(text)

    # set color
    if color is not None:
        radio_button.setStyleSheet(
            "QRadioButton { color: rgb(%d,%d,%d) }" % color
        )

    # set checked
    if flag_checked:
        radio_button.setChecked(True)

    # add radio button to the layout
    add_widget_to_layout(layout, radio_button, position)

    return radio_button


def add_check_box(layout, position, text, flag_checked=False, color=None):
    """
    Adds a check box to a grid layout

    The method raises an error if the length of position is not 2 or 4.

    :param layout: parent layout where the check box is added
    :type layout: QtWidgets.QGridLayout
    :param position: position of the check box in the parent layout, length 2
        ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type position: tuple of integers
    :param text: text displayed next to the check box
    :type text: str
    :param flag_checked: specify if check box is initially checked
    :type flag_checked: bool
    :param color: color in RGB format
    :type color: tuple

    :returns: check box item
    :rtype: QtWidgets.QCheckBox
    """

    # create radio button
    check_box = QtWidgets.QCheckBox(text)

    # set color
    if color is not None:
        check_box.setStyleSheet("QCheckBox { color: rgb(%d,%d,%d) }" % color)

    # set checked
    if flag_checked:
        check_box.setChecked(True)

    # add radio button to the layout
    add_widget_to_layout(layout, check_box, position)

    return check_box


def add_scroll_area(
    layout, position, width=0, height=0, flag_ignore_wheel_event=False
):
    """
    Adds a scroll area to a grid layout

    The scroll area is added to the parent layout. A specific layout (instance
    of QtWidgets.QGridLayout) is created for the scroll area.

    :param layout: parent layout where the scroll area is added
    :type layout: QtWidgets.QGridLayout
    :param position: position of the items in the parent layout to be included
        in the scroll area, length 2 ``(row, col)`` or 4
        ``(row, col, rowspan, colspan)``
    :type position: tuple of integers
    :param width: width of the scroll area in pixels, set to ``0`` if
        automatic
    :type width: int or float
    :param height: height of the scroll area in pixels, set to ``0`` if
        automatic
    :type height: int or float
    :param flag_ignore_wheel_event: specify if wheel event is ignored
    :type flag_ignore_wheel_event: bool

    :returns:
        - **scroll_lay** (*QtWidgets.QGridLayout*) -- layout filling the scroll
          area
        - **scroll_area** (*QtWidgets.QScrollArea*) -- scroll area item

    To add a widget to the scroll area, use ``scroll_lay.addWidget(widget)``.
    """

    # create scroll area
    if flag_ignore_wheel_event:
        scroll_area = ScrollArea()

    else:
        scroll_area = QtWidgets.QScrollArea()

    scroll_area.setWidgetResizable(True)

    # set size
    if width > 0:
        scroll_area.setFixedWidth(width)
    if height > 0:
        scroll_area.setFixedHeight(height)

    # create scroll widget
    scroll_widget = QtWidgets.QWidget()

    # set scroll widget to scroll area
    scroll_area.setWidget(scroll_widget)

    # create scroll layout
    scroll_lay = QtWidgets.QGridLayout(scroll_widget)

    # set scroll area to input layout
    add_widget_to_layout(layout, scroll_area, position)

    return scroll_lay, scroll_area


def create_window(
    size=(0, 0), title=None, bg_color=(240, 240, 240), flag_show=True
):
    """
    Creates a window

    The geometry of the window can be updated afterward, see
    http://doc.qt.io/qt-4.8/application-windows.html#window-geometry for
    details.

    If pyqtgraph items are to be added in the window, the background color
    won't apply to them. To get the same background color for pyqtgraph items,
    the following line must be added:
    ``pyqtgraph.setConfigOption('background',color)``.

    :param size: size of the window in pixels, length 2 ``(width, height)``,
        set one value to 0 in order to have the window maximized in the
        corresponding direction
    :type size: tuple
    :param title: window title
    :type title: str
    :param bg_color: background color of the window, either (RGB) or (RGBA)
    :type bg_color: tuple or list
    :param flag_show: specify if the window must be displayed
    :type flag_show: bool

    :returns:
        - **win** (*QtWidgets.QWidget*) -- window container
        - **layout** (*QtWidgets.QGridLayout*) -- layout filling the window
    """

    # create the window and the layout to fill it
    win = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout(win)

    # set the background color
    if len(bg_color) == 3:
        color = QtGui.QColor(bg_color[0], bg_color[1], bg_color[2])
    elif len(bg_color) == 4:
        color = QtGui.QColor(
            bg_color[0], bg_color[1], bg_color[2], bg_color[3]
        )

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, color)
    win.setPalette(palette)
    win.setAutoFillBackground(True)

    # set the window title
    if isinstance(title, str):
        win.setWindowTitle(title)

    if 0 in size:
        # set the window size when minimized
        screen_resolution = QtWidgets.QApplication.desktop().screenGeometry()
        win.resize(
            screen_resolution.width() - 80, screen_resolution.height() - 200
        )

        # maximize window by default
        win.showMaximized()

    else:
        win.resize(size[0], size[1])

    # show the window
    if flag_show:
        win.show()

    return win, layout


def add_widget_button_group(
    lay, widget_position, label_list, button_type="radio", color_list=[],
    box_title="", flag_horizontal=True, nb_table=0, **kwargs
):
    """
    Creates a group box with a group of buttons and adds it to a parent layout

    The buttons are added in the order of the input label list. It may be
    eihter a row or a column of buttons (``nb_table == 0``), or a table of
    buttons (``nb_table != 0``).

    :param lay: parent layout where the group box is added
    :type lay: QtWidgets.QGridLayout
    :param widget_position: position of the group box in the parent layout,
        length 2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple of integers
    :param label_list: string labels of the buttons
    :type label_list: list
    :param button_type: type of the buttons (``"radio"``, ``"push"`` or
        ``"check_box"``), in case of ``"radio"`` first button is checked, in
        case of ``"check_box"`` exclusivity is set to False and no button is
        checked
    :type button_type: str
    :param color_list: RGB color for each button
    :type color_list: list
    :param box_title: title of the group box containing the radio buttons
    :type box_title: str
    :param flag_horizontal: specify if buttons are displayed horizontally
    :type flag_horizontal: bool
    :param nb_table: number of buttons on a single row, set to ``0`` if all
        buttons on 1 row, if the length of ``label_list`` is greater than
        ``nb_table``, then the buttons are added on several rows
    :type nb_table: int
    :param kwargs: keyword arguments of the funtion that adds the button to the
        layout filling the group box (:func:`.add_radio_button`,
        :func:`.add_push_button` or :func:`.add_check_box`)

    :returns:
        - **grid** (*QtWidgets.QGridLayout*) -- layout filling the group box
        - **group_box** (*QtWidgets.QGroupBox*) -- widget added to the parent
          layout
        - **group_button** (*QtWidgets.QButtonGroup*) -- item containing the
          buttons
    """

    # create group box containing the radio buttons
    grid, group_box = add_group_box(lay, widget_position, box_title)

    # create group for radio buttons
    group_button = QtWidgets.QButtonGroup()

    # create buttons
    for ite_label, label in enumerate(label_list):
        # check if color
        if color_list != []:
            kwargs["color"] = tuple(color_list[ite_label][:3])

        # get button position
        if flag_horizontal:
            if nb_table == 0:
                position = (0, ite_label)

            else:
                position = (int(ite_label / nb_table), ite_label % nb_table)
        else:
            if nb_table == 0:
                position = (ite_label, 0)

            else:
                position = (ite_label % nb_table, int(ite_label / nb_table))

        # create button and add it to the layout
        if button_type == "radio":
            button = add_radio_button(grid, position, label, **kwargs)

        elif button_type == "check_box":
            button = add_check_box(grid, position, label, **kwargs)

        elif button_type == "push":
            button = add_push_button(grid, position, label, **kwargs)

        else:
            raise ValueError(
                "Wrong type of button, got %s, it should be 'radio', 'push' "
                "or 'check_box'" % button
            )

        # add radio button to the group of radio buttons
        group_button.addButton(button, ite_label)

        # check first radio button
        if button_type == "radio" and ite_label == 0:
            button.setChecked(True)

        # set exclusice to False for check box
        elif button_type == "check_box":
            group_button.setExclusive(False)

    return grid, group_box, group_button


def add_combo_box(
    lay, widget_position, item_list, box_title=None,
    flag_enable_key_interaction=True
):
    """
    Creates a group box with a combo box and adds it to a grid layout

    :param lay: parent layout where the group box is added
    :type lay: QtWidgets.QGridLayout
    :param widget_position: position of the group box in the parent layout,
        length 2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple of integers
    :param item_list: items of the combo box, each element is a string
    :type item_list: list
    :param box_title: title of the group box containing the combo box
    :type box_title: str
    :param flag_enable_key_interaction: specify if key press interaction is
        enabled
    :type flag_enable_key_interaction: bool

    :returns:
        - **grid** (*QtWidgets.QGridLayout*) -- layout filling the group box
        - **group_box** (*QtWidgets.QGroupBox*) -- widget added to the parent
          layout
        - **combo_box** (:class:`.ComboBox` or *QtWidgets.QComboBox*)
          - combo box item
    """

    # create combo box
    if flag_enable_key_interaction:
        combo_box = QtWidgets.QComboBox()

    else:
        combo_box = ComboBox()

    # add items
    combo_box.addItems(item_list)

    # check if group box must be created
    if box_title is not None:
        # create group box
        grid, group_box = add_group_box(lay, widget_position, box_title)

        # add combo box to group box
        grid.addWidget(combo_box, 0, 0)

    else:
        grid, group_box = None, None

        # add combo box to layout
        add_widget_to_layout(lay, combo_box, widget_position)

    return grid, group_box, combo_box


def delete_widgets_from_layout(grid, nb_items_to_delete=None):
    """
    Deletes a specified number of widgets in a grid layout

    The widgets are deleted in the inverse order of creation in the layout.

    :param grid: layout where widgets must be deleted
    :type grid: QtWidgets.QGridLayout
    :param nb_items_to_delete: number of widgets to delete, by default all
        widgets
    :type nb_items_to_delete: int
    """

    nb_items = grid.count()

    if nb_items_to_delete is None or nb_items < nb_items_to_delete:
        nb_items_to_delete = nb_items

    for i in reversed(range(nb_items - nb_items_to_delete, nb_items)):
        wid_to_remove = grid.itemAt(i).widget()
        wid_to_remove.setParent(None)
        wid_to_remove.deleteLater()


def set_style_sheet(app, font_name, font_size, font_color, qobj_list):
    """
    Sets the style sheet for a list of Qt classes in a QApplication

    :param app: GUI application in which the style sheet must be set
    :type app: QtCore.QCoreApplication or QtWidgets.QApplication
    :param font_name: font name
    :type font_name: str
    :param font_size: size of the font in pt
    :type font_size: int or float
    :param font_color: color (RGB) of the font
    :type font_color: tuple or list
    :param qobj_list: each element is a string of the Qt class on which the
        style sheet is applied
    :type qobj_list: list
    """

    # get style sheet string
    style_string = "color: rgb(%d,%d,%d); font: %s; font-size: %dpt" % (
        font_color[0], font_color[1], font_color[2], font_name, font_size
    )

    style_sheet_string = ""
    for qobj in qobj_list:
        style_sheet_string += "%s {%s} " % (qobj, style_string)

    # set style sheet
    app.setStyleSheet(style_sheet_string)
