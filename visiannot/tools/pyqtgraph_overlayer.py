# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for scientific graphics with pyqtgraph

See https://pyqtgraph.readthedocs.io/en/latest
"""


import pyqtgraph as pg
from PyQt5.QtGui import QFont
from .pyqt_overlayer import create_window, add_widget_to_layout, initialize_gui
import numpy as np
from .datetime_converter import convert_frame_to_absolute_datetime_string, \
    convert_timedelta_to_absolute_datetime_string


def set_background_color(color=(255, 255, 255)):
    """
    Sets background color of pyqtgraph widgets (independent of PyQt5 widgets)

    :param color: background color as a string or RGB
        (see https://pyqtgraph.readthedocs.io/en/latest/style.html for details)
    :type color: str or tuple
    """

    pg.setConfigOption('background', color)


def initialize_gui_and_bg_color(color=(255, 255, 255)):
    """
    Creates a Qt application for display and sets background color of the
    pyqtgraph widgets

    It calls the functions :func:`.initialize_gui` and
    :func:`.set_background_color`.

    :param color: background color as a string or RGB
        (see https://pyqtgraph.readthedocs.io/en/latest/style.html for details)
    :type color: str or tuple

    :returns: instance of QtCore.QCoreApplication or QtWidgets.QApplication
    """

    app = initialize_gui()
    set_background_color(color=color)

    return app


def create_widget(
    lay, widget_position, widget_size=(0, 0), widget_title=None,
    title_style={'color': '#0000', 'size': '9pt'},
    x_range=[], y_range=[], axes_label_dict={"left": None, "bottom": None},
    flag_invert_x=False, flag_invert_y=False, flag_aspect_locked=False,
    flag_plot_menu=True
):
    """
    Creates a 2D widget and adds it to a grid layout

    The widget content is empty.

    :param lay: parent layout where the widget is added
    :type lay: QtWidgets.QGridLayout
    :param widget_position: position of the widget in the parent layout,
        length 2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple
    :param widget_size: maximum size of the widget, length 2
        ``(width, height)``, set a value to 0 in order to have an automatic
        sizing in the corresponding axis
    :type widget_size: tuple
    :param widget_title: widget title, basic HTML allowed
    :type widget_title: str
    :param title_style: title style
    :type title_style: dict
    :param x_range: range values on the X axis, length 2 ``(x_min, x_max)``
    :type x_range: tuple
    :param y_range: range values on the Y axis, length 2 ``(y_min, y_max)``
    :type y_range: tuple
    :param axes_label_dict: axes to show and their respective label

        - Key is the axis identifier (``"left"``, ``"right"``,
          ``"bottom"`` or ``"top"``)
        - Value is the associated label as a list of length 2:

            - axis label (*str*)
            - label style (*dict*), e.g.
              ``{'color': '#000', 'font-size': '10pt'}``
        - In case no label is associated to the axis, set the corresponding
          value to ``None``
    :type axes_label_dict: dict
    :param flag_invert_x: specify if the X axis must be inverted
    :type flag_invert_x: bool
    :param flag_invert_y: specify if the Y axis must be inverted
    :type flag_invert_y: bool
    :param flag_aspect_locked: specify if the aspect ratio must be locked
    :type flag_aspect_locked: bool
    :param flag_plot_menu: specify if the plot menu is enabled
    :type flag_plot_menu: bool

    :returns: widget
    :rtype: pyqtgraph.PlotWidget
    """

    # create the widget
    widget = pg.PlotWidget()

    # axes settings
    widget.showAxis('left', show=False)
    widget.showAxis('bottom', show=False)
    for axis, label_info in axes_label_dict.items():
        widget.showAxis(axis, show=True)
        if label_info is not None:
            if label_info[1] is None:
                widget.getAxis(axis).setLabel(text=label_info[0])

            else:
                widget.getAxis(axis).setLabel(
                    text=label_info[0], **label_info[1]
                )

    # invert axis
    if isinstance(flag_invert_x, bool):
        widget.invertX(flag_invert_x)

    if isinstance(flag_invert_y, bool):
        widget.invertY(flag_invert_y)

    # set title
    widget.setTitle(widget_title, **title_style)

    # set the widget size
    if widget_size[0] == 0 and widget_size[1] != 0:
        widget.setMaximumHeight(widget_size[1])

    elif widget_size[0] != 0 and widget_size[1] == 0:
        widget.setMaximumWidth(widget_size[0])

    elif widget_size[0] != 0 and widget_size[1] != 0:
        widget.setMaximumSize(widget_size[0], widget_size[1])

    # set aspect locked or not
    widget.setAspectLocked(flag_aspect_locked)

    # set plot menu
    widget.setMenuEnabled(flag_plot_menu)

    # set the range
    if (isinstance(x_range, tuple) or isinstance(x_range, list)) and \
            len(x_range) == 2:
        widget.setXRange(x_range[0], x_range[1])

    if (isinstance(y_range, tuple) or isinstance(y_range, list)) and \
            len(y_range) == 2:
        widget.setYRange(y_range[0], y_range[1])

    # add the widget to the layout
    add_widget_to_layout(lay, widget, widget_position)

    return widget


def create_widget_image(
    lay, widget_position, im=None, title=None,
    title_style={'color': '#000', 'size': '9pt'}
):
    """
    Creates a widget containing an image and adds it to a grid layout

    :param lay: parent layout where the widget is added
    :type lay: QtWidgets.QGridLayout
    :param widget_position: position of the widget in the parent layout, length
        2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple
    :param im: RGB image array of shape :math:`(width, height, 3)`
    :type im: numpy array
    :param title: widget title
    :type title: str
    :param title_style: widget title style
    :type title_style: dict

    :returns:
        - **widget** (*pyqtgraph.PlotWidget*) -- image container
        - **img** (*pyqtgraph.ImageItem*) -- image item
    """

    # create the widget
    widget = create_widget(
        lay, widget_position, widget_title=title, title_style=title_style,
        axes_label_dict={}, flag_invert_y=True, flag_aspect_locked=True,
        flag_plot_menu=False
    )

    # create image item and add it to the widget
    img = pg.ImageItem(im)
    widget.addItem(img)

    return widget, img


def create_widget_logo(lay, widget_position, im, box_size=None):
    """
    Creates a widget with no mouse interaction containing an image and adds it
    to a grid layout

    :param lay: parent layout where the widget is added
    :type lay: QtWidgets.QGridLayout
       instance of QtWidgets.QGridLayout where the widget is added
    :param widget_position: position of the widget in the parent layout, length
        2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple
    :param im: RGB image array of shape :math:`(width, height, 3)`
    :type im: numpy array
    :param box_size: size of the image, either an integer if same value for
        width and height, or a tuple of length 2 ``(width, height)``
    :type box_size: int or tuple

    :returns: widget containing the image
    :rtype: pyqtgraph.PlotWidget
    """

    widget, _ = create_widget_image(lay, widget_position, im=im)
    widget.setMouseEnabled(x=False, y=False)
    widget.hideButtons()

    if box_size is not None:
        if isinstance(box_size, int):
            widget.setMaximumSize(box_size, box_size)

        elif (isinstance(box_size, tuple) or isinstance(box_size, list)) and \
                len(box_size) == 2:
            widget.setMaximumSize(box_size[0], box_size[1])

    return widget


def set_ticks_text_style(axis_item, color="#000", size=9, **kwargs):
    """
    Sets ticks text style of an axis item

    See https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/axisitem.html
    for details.

    :param axis_item: axis for which the style of ticks text must be set
    :type axis_item: pyqtgraph.AxisItem
    :param color: color of the text in HEX string or RGB format
    :type color: str or tuple
    :param size: font size of the text in pt
    :type size: float or int
    :param kwargs: keyword arguments of :meth:`setStyle` applied on
        ``axis_item``, see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/axisitem.html#pyqtgraph.AxisItem.setStyle
    """

    # set ticks color
    axis_item.setPen(color=color)
    axis_item.setTextPen(color=color)

    # create font with desired size
    font = QFont()
    font.setPointSize(size)

    # set ticks size
    axis_item.setTickFont(font)

    # set offset
    axis_item.setStyle(**kwargs)


def set_temporal_ticks(
    widget, nb_ticks, temporal_info, ref_datetime, **kwargs
):
    """
    Sets the ticks of the X axis of a widget in datetime format and the X axis
    range according to a temporal range

    It creates temporal labels for ticks in the format specified by ``fmt``.
    The first (resp. last) tick is defined by the first (resp. last) value of
    the temporal range, which might be expressed in milliseconds or in number
    of frames.

    :param widget: widget where to set X axis ticks and X axis range,
        it may be any sub-class of **pyqtgraph.PlotWidget**
    :param nb_ticks: number of ticks to display on the X axis
    :type nb_ticks: int
    :param temporal_info: temporal range, there are two ways to specify it:

        - ``(first_frame_ms, last_frame_ms)``, the temporal range is
          expressed in milliseconds,
        - ``(first_frame, last_frame, freq)``, the temporal range is
          expressed in number of frames sampled at the frequency ``freq``
    :type temporal_info: list
    :param ref_datetime: reference datetime for temporal range (if the
        first value of the temporal range is ``0``, then the tick value is
        ``ref_datetime``)
    :type ref_datetime: datetime.datetime
    :param kwargs: keyword arguments of :func:`.convert_datetime_to_string`
    :type fmt: str
    """

    start = temporal_info[0]
    stop = temporal_info[1]
    temporal_range = [
        start + i * (stop - start) / (nb_ticks - 1)
        for i in range(nb_ticks - 1)
    ] + [stop]

    # X axis range
    widget.setXRange(start, stop)

    if len(temporal_info) == 3:
        freq = temporal_info[2]

        # define temporal labels
        temporal_labels = [
            convert_frame_to_absolute_datetime_string(
                frame_id, freq, ref_datetime, **kwargs
            )
            for frame_id in temporal_range
        ]

    else:
        # define temporal labels
        temporal_labels = [
            convert_timedelta_to_absolute_datetime_string(
                ref_datetime, {"milliseconds": msec}, **kwargs
            )
            for msec in temporal_range
        ]

    # set ticks
    ticks = [[(frame, label) for frame, label in
              zip(temporal_range, temporal_labels)], []]
    axis = widget.getAxis('bottom')
    axis.setTicks(ticks)


def add_plot_to_widget(
    widget, data, flag_clear=False, flag_nan_void=True,
    plot_style={'pen': {'color': 'b', 'width': 1}}
):
    """
    Adds a plot item to a 2D widget

    For details about plot style, see
    https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html

    For details about color, see
    https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

    :param widget: widget where the plot must be displayed
    :type widget: pyqtgraph.PlotWidget
    :param data: data to plot, two possibilites:

        - shape :math:`(n, 2)`, first column contains X values, second column
          contains Y values, if only one point to plot make sure to have
          shape :math:`(1, 2)`
        - shape :math:`(n,)`, only Y values, then X values are the array
          indexes
    :type data: numpy array
    :param flag_clear: specify if content currently displayed must be cleared
        before plotting the data
    :type flag_clear: bool
    :param flag_nan_void: specify if NaN values must be handled by
        **pyqtgraph.PlotDataItem** by setting the keyword argument ``connect``
        to ``"finite"``, see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html#pyqtgraph.PlotDataItem.__init__
    :type flag_nan_void: bool
    :param plot_style: plot style, keys are keyword arguments of the
        constructor of pyqtgraph.PlotDataItem, see link above
    :type plot_style: dict

    :returns: plot item (or a list of pyqtgraph.PlotDataItem in case
        ``nan_void`` is true)
    :rtype: pyqtgraph.PlotDataItem
    """

    if flag_clear:
        widget.clear()

    if flag_nan_void:
        plot_style["connect"] = "finite"

    plot = pg.PlotDataItem(data, **plot_style)
    widget.addItem(plot)

    return plot


def basic_plot(data, opts_win_dict={}, opts_wid_dict={}, **kwargs):
    """
    Creates a window with a 2D plot

    For details about plot style, see
    https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html

    For details about color, see
    https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

    :param data: data to plot, two possibilites:

        - shape :math:`(n, 2)`, first column contains X values, second column
          contains Y values, if only one point to plot make sure to have
          shape :math:`(1, 2)`
        - shape :math:`(n,)`, only Y values, then X values are the array
          indexes
    :type data: numpy array
    :param opts_win_dict: keyword arguments of the function
        :func:`.create_window`
    :type opts_win_dict: dict
    :param opts_wid_dict: keyword arguments of the function
        :func:`.create_widget`
    :type opts_wid_dict: dict
    :param kwargs: keyword arguments of :func:`.add_plot_to_widget`

    :returns:
        - **win** (*QWidgets.QWidget*) -- window container
        - **lay** (*QWidgets.QGridLayout*) -- layout
        - **widget** (*pyqtgraph.PlotWidget*) -- 2D widget filling the whole
          layout
        - **plot** (*pyqtgraph.PlotDataItem*) -- plot item
    """

    win, lay = create_window(**opts_win_dict)

    if "bg_color" in opts_win_dict.keys():
        set_background_color(opts_win_dict["bg_color"])

    widget = create_widget(lay, (0, 0), **opts_wid_dict)

    plot = add_plot_to_widget(widget, data, **kwargs)

    return win, lay, widget, plot


def basic_image_plot(im, **kwargs):
    """
    Creates a window with an image

    :param im: RGB image array of shape :math:`(width, height, 3)`
    :type im: numpy array
    :param kwargs: keyword arguments of the function
        :func:`.create_window`, if background color of the window is
        specified, then it is also applied to the image widget

    :returns:
        - **win** (*QWidgets.QWidget*) -- window container
        - **lay** (*QWidgets.QGridLayout*) -- layout
        - **widget** (*pyqtgraph.PlotWidget*) -- 2D widget filling the whole
          layout
        - **img** (*pyqtgraph.ImageItem*) -- image item
    """

    win, lay = create_window(**kwargs)

    if "bg_color" in kwargs.keys():
        set_background_color(kwargs["bg_color"])

    widget, img = create_widget_image(lay, (0, 0), im=im)

    return win, lay, widget, img


def add_legend_to_widget(
    widget, item_dict, position='inside', legend_wid_size=(0, 0), **kwargs
):
    """
    Adds a legend to a 2D widget

    If specified, this function creates a widget dedicated to the legend,
    instead of having a legend item inside the 2D widget.

    :param widget: widget containing the plot items to legend
    :type widget: pyqtgraph.PlotWidget
    :param item_dict: plot items to legend, key is the plot item and value
        is the associated legend text
    :type item_dict: dict
    :param position: legend mode

        - ``"inside"``:  legend item inside the widget
        - ``"right"``: legend item is in a new widget created at the right side
          of the widget
        - ``"bottom"``:  legend is in a new widget created at the bottom side
          of the 2D widget
    :type position: str
    :param legend_wid_size: size of the created legend widget, length 2
        ``(width, height)`` in case ``position`` is ``"right"`` or
        ``"bottom"``
    :type legend_wid_size: tuple
    :param kwargs: keyword arguments of ``pyqtgraph.LegendItem`` constructor,
        see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/legenditem.html

    :returns:
        - **legend** (*-pyqtgraph.LegendItem*) -- legend item
        - **legend_widget** (*pyqtgraph.PlotWidget*) -- widget containing the
          legend item if it has been created (otherwise ``None``)
    """

    if position == 'inside':
        # create legend
        legend = pg.LegendItem(**kwargs)
        legend.setParentItem(widget.graphicsItem())
        legend_widget = None

    elif position == 'right' or position == 'bottom':
        # get the list of the window children, first element is the layout
        # the others are the widgets
        win_children_list = widget.parent().children()

        # get the layout
        layout = win_children_list[0]

        # get the widget index in the layout
        wid_ind = layout.indexOf(widget)

        # get the widget position in the layout
        wid_pos = layout.getItemPosition(wid_ind)

        # get the legend widget position in the layout
        if position == 'right':
            legend_wid_pos = (wid_pos[0] + (wid_pos[2] - 1),
                              wid_pos[1] + wid_pos[3],
                              wid_pos[2], 1)
        elif position == 'bottom':
            legend_wid_pos = (wid_pos[0] + wid_pos[2],
                              wid_pos[1] + (wid_pos[3] - 1),
                              1, wid_pos[3])

        # check if the legend widget has already been created
        if layout.itemAtPosition(legend_wid_pos[0], legend_wid_pos[1]) is None:
            # create the legend widget
            legend_widget = create_widget(
                layout, legend_wid_pos, axes_label_dict={}
            )

            # set the size of the legend widget
            if legend_wid_size[0] == 0 and legend_wid_size[1] != 0:
                legend_widget.setMaximumHeight(legend_wid_size[1])

            elif legend_wid_size[0] != 0 and legend_wid_size[1] == 0:
                legend_widget.setMaximumWidth(100)

            elif legend_wid_size[0] != 0 and legend_wid_size[1] != 0:
                legend_widget.setMaximumSize(
                    legend_wid_size[0], legend_wid_size[1]
                )

        else:
            # get the widget that contains the legend
            # assuming that it is the element right after the widget
            legend_widget = \
                win_children_list[win_children_list.index(widget) + 1]

        # create legend
        legend = pg.LegendItem(**kwargs)
        legend.setParentItem(legend_widget.graphicsItem())


    # set the legend item to the corresponding item and label
    for item, item_label in item_dict.items():
        legend.addItem(item, item_label)

    return legend, legend_widget


def add_text_item_to_widget(
    widget, pos, flag_arrow=False, text_alignement=None,
    opts_text_dict={"color": 'k', "anchor": (0.5, 0.5)},
    opts_arrow_dict={
        'headLen': 15, 'tipAngle': 20, 'pen': '#000000', 'brush': '#000000'
    }
):
    """
    Adds a text item to a 2D widget, possibly along with an arrow

    For details about color, see
    https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

    :param widget: widget where the text item must be displayed
    :type widget: pyqtgraph.PlotWidget
    :param pos: position of the text item in the widget, length 2 ``(x, y)``
    :type pos: tuple
    :param flag_arrow: specify if an arrow must be added
    :type flag_arrow: bool
    :param text_alignement: flag for specifying text alignement, particularly
        useful in case of multi-line text, see
        https://doc.qt.io/qt-5/qt.html#AlignmentFlag-enum for the possible
        values, for example: ``Qt.AlignCenter``, imported as
        ``from PyQt5.QtCore import Qt``
    :param opts_text_dict: keyword arguments of the constructor of
        ``pyqtgraph.TextItem``, see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/textitem.html#pyqtgraph.TextItem
    :type opts_text_dict: dict
    :param opts_arrow_dict: keyword arguments of the constructor of
        ``pyqtgraph.ArrowItem``, see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/arrowitem.html#pyqtgraph.ArrowItem
    :type opts_arrow_dict: dict

    Regarding ``anchor`` argument in ``TextItem``, ``(0, 0)`` => top left,
    ``(1, 0)`` => top right, ``(1, 0)`` => bottom left, ``(1, 1)`` => bottom
    right.

    Regarding ``opts_arrow_dict``, the position of the arrow item is specified
    by the keyword argument ``pos``.

    :returns:
        - **text_item** (*pyqtgraph.TextItem*)
        - **arrow_item** (*pyqtgraph.ArrowItem*) -- may be ``None`` if arrow
          not specified
    """

    # create text item
    text_item = pg.TextItem(**opts_text_dict)

    # text alignement
    if text_alignement is not None:
        option = text_item.textItem.document().defaultTextOption()
        option.setAlignment(text_alignement)
        text_item.textItem.document().setDefaultTextOption(option)
        text_item.textItem.setTextWidth(
            text_item.textItem.boundingRect().width()
        )

    # set the text item position
    text_item.setPos(pos[0], pos[1])

    # add the text item to the widget
    widget.addItem(text_item)

    # create an arrow item if specified and add it to the widget
    if flag_arrow:
        arrow_item = pg.ArrowItem(**opts_arrow_dict)
        widget.addItem(arrow_item)
    else:
        arrow_item = None

    return text_item, arrow_item


def set_color_map(values, colors, lut_dim=256):
    """
    Creates a color map

    See https://pyqtgraph.readthedocs.io/en/latest/colormap.html for details.

    :param values: values spanning the color map, at least two values are
        required, it may be a 1D numpy array
    :type values: list or tuple
    :param colors: colors corresponding to the values, must be the same length
        as ``values``, each element is a (RGB) color
    :type colors: list or numpy array
    :param lut_dim: dimension of the look up table
    :type lut_dim: int

    :returns:
        - **color_map** (*pyqtgraph.ColorMap*)
        - **lut** (*numpy array*) -- color of the look up table, shape
          ``(lut_dim, 4)``
    """

    color_map = pg.ColorMap(values, colors)
    lut = color_map.getLookupTable(values[0], values[-1], lut_dim)

    return color_map, lut


def create_widget_color_bar(
    lay, widget_position, color_map, lut, ticks_values, widget_width=80,
    ticks_val_formatting="%s", img_width=5
):
    """
    Creates a widget with a color bar (useful for the legend of a heat map)

    :param lay: parent layout where the widget is added
    :type lay: QtWidgets.QGridLayout
    :param widget_position: position of the widget in the parent layout, length
        2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple
    :param color_map: color map to define the color bar
    :type color_map: pyqtgraph.ColorMap
    :param lut: look up table to define the color bar
    :type lut: numpy array
    :param ticks_values: values of the ticks to display
    :type ticks_values: list or tuple
    :param widget_width: width of the widget in pixels
    :type widget_width: int
    :param ticks_val_formatting: formatting pattern of the ticks text
    :type ticks_val_formatting: str
    :param img_width: width of the color bar in pixels
    :type img_width: int

    :returns:
        - **wid_bar** (*pyqtgraph.PlotWidget*) -- widget
          containing the color bar
        - **bar_img_item** (*pyqtgraph.ImageItem*) -- image item of the color
          bar
    """

    # legend color bar image
    lut_img = np.expand_dims(lut, axis=0)
    lut_img = np.tile(lut_img, (img_width, 1, 1))

    # create legend widget
    wid_bar, bar_img_item = create_widget_image(
        lay, widget_position, im=lut_img
    )
    wid_bar.invertY(False)
    wid_bar.setMaximumWidth(widget_width)
    wid_bar.showAxis("right")

    # loop on ticks values
    bar_ticks = []
    for val in ticks_values:
        # color corresponding to value
        val_color = color_map.map(val)[:3]

        # get similarity between the LUT and the value color
        lut_val_similarity = np.sum(lut == val_color, axis=1)

        # get color index in LUT
        color_ind = np.where(lut_val_similarity == 3)[0]
        if color_ind.shape[0] > 0:
            color_ind = color_ind[0]

        else:
            # if value color not in LUT, look for the closest
            color_inds = np.where(lut_val_similarity == 2)[0]
            diff_sum_prev = -np.inf
            for ite, color_ind_tmp in enumerate(color_inds):
                diff_sum = np.abs(
                    np.sum(lut[color_ind_tmp].astype(int) - val_color)
                )

                if diff_sum >= diff_sum_prev and ite > 0:
                    color_ind = color_inds[ite - 1]
                    break
                diff_sum_prev = diff_sum

        # update ticks list
        bar_ticks.append((color_ind, ticks_val_formatting % val))

    # set Y ticks
    right_axis = wid_bar.getAxis("right")
    right_axis.setTicks([bar_ticks])
    right_axis.setStyle(stopAxisAtTick=(True, True))

    return wid_bar, bar_img_item


def add_mean_std_plot_to_widget(
    wid, data_mean, data_std, data_X=None, pen_std_style={'color': 'k'},
    n_population_list=[], **kwargs
):
    """
    Adds a plot item to a 2D widget, a vertical line is associated to each
    point of the plot item, particularly useful to display a mean/median curve
    with the standard deviation

    The method raises an exception if ``data_mean`` and ``data_std`` or
    ``data_mean`` and ``data_X`` do not have the same length.

    :param wid: widget where to add the plot items
    :type wid: pyqtgraph.PlotWidget
    :param data_mean: mean/median values (1D array)
    :type data_mean: numpy array
    :param data_std: standard deviation values (1D array), same length as
        ``data_mean``
    :type data_std: numpy array
    :param data_X: coordinates of the mean/std values on the X axis (1D array),
        must have the same length as ``data_mean``
    :type data_X: numpy array
    :param pen_std_style: style of the standard deviation plot item
    :type pen_std_style: dict
    :param n_population_list: number of samples at each point (same length than
        ``data_mean``), a text item is then added near each point
    :type n_population_list: list
    :param kwargs: keyword arguments of the function
        :func:`.add_plot_to_widget`, used for the plot item of
        the mean/median values

    :returns:
        - **mean_plot** (*pyqtgraph.PlotDataItem*) -- plot item of the
          mean/median values
        - **std_plot** (*pyqtgraph.PlotDataItem*) -- plot item of the standard
          deviation values
        - **text_item_list** (*list*) -- text items (pyqtgraph.TextItem) of the
          number of samples at each point, empty list if ``n_population_list``
          is empty
    """

    # check shape
    if data_mean.shape[0] != data_std.shape[0]:
        raise Exception(
            "Mean and std do not have the same shape: %d vs %d" %
            (data_mean.shape[0], data_std.shape[0])
        )

    elif data_X is not None:
        if data_mean.shape[0] != data_X.shape[0]:
            raise Exception(
                "Mean and X array do not have the same shape: %d vs %d" %
                (data_mean.shape[0], data_X.shape[0])
            )

    # format mean array if X data is provided
    if data_X is None:
        data_mean_tmp = data_mean
    else:
        data_mean_tmp = np.vstack((data_X, data_mean)).T

    # format list of samples number
    if len(n_population_list) != data_mean.shape[0]:
        n_population_list = [None for i in range(data_mean.shape[0])]

    # plot mean data
    mean_plot = add_plot_to_widget(wid, data_mean_tmp, **kwargs)

    # create X data if necessary
    if data_X is None:
        data_X = np.arange(data_mean.shape[0])

    # get X axis step
    if data_X.shape[0] > 1:
        x_step = data_X[1] - data_X[0]
    else:
        x_step = 1

    # initialize std curve array
    data_std_tmp = np.empty((0, 2))

    # loop on median values
    text_item_list = []
    for x, med, std, nb_samples in zip(
        data_X, data_mean, data_std, n_population_list
    ):
        # check if not NaN
        if ~np.isnan(med):
            # create std curve sub-array
            data = np.array([
                [x, med - std],
                [x, med + std],
                [x - x_step / 4, med - std],
                [x + x_step / 4, med - std],
                [x - x_step / 4, med + std],
                [x + x_step / 4, med + std]
            ])

            # concatenate std curve array
            data_std_tmp = np.concatenate((data_std_tmp, data))

            # add text item with number of data
            if nb_samples is not None:
                text_item, _ = add_text_item_to_widget(
                    wid, (x + x_step / 8, med + std / 2),
                    opts_text_dict={
                        "text": "%d" % nb_samples, "color": 'k',
                        "anchor": (0.5, 0.5)
                    }
                )
                text_item_list.append(text_item)

    # plot std curve
    std_plot = pg.PlotCurveItem(
        data_std_tmp[:, 0], data_std_tmp[:, 1], pen=pen_std_style,
        connect="pairs"
    )

    wid.addItem(std_plot)

    return mean_plot, std_plot, text_item_list


def remove_item_in_widgets(wid_list, item_list):
    """
    Removes an item from a list of widgets

    :param wid_list: widgets where to remove an item, each element must
        have a method ``removeItem`` (for example an instance of
        **pyqtgraph.PlotWidget**)
    :type wid_list: list
    :param item_list: items to remove from widgets, same length as
        ``wid_list``, each element corresponds to one element of
        ``wid_list``
    :type item_list: list
    """

    for wid, item in zip(wid_list, item_list):
        wid.removeItem(item)


def add_region_to_widget(bound_1, bound_2, wid, color):
    """
    Creates a region item (**pyqtgraph.LinearRegionItem**) and displays it in a
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
        region = pg.LinearRegionItem(
            movable=False, brush=color, pen={'color': color, 'width': 1}
        )

    except Exception:
        region = pg.LinearRegionItem(movable=False, brush=color)

    # set region boundaries
    region.setRegion([bound_1, bound_2])

    # add region to widget
    wid.addItem(region)

    return region
