# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with sub-classes and functions for scientific graphics with pyqtgraph

See https://pyqtgraph.readthedocs.io/en/latest
"""


import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QSizePolicy
from .ToolsPyQt import createWindow, addWidgetToLayout, initializeDisplay
import numpy as np


# *************************************************************************** #
# *************************************************************************** #
# ************************** Pyqtgraph subclass ***************************** #
# *************************************************************************** #
# *************************************************************************** #

class PlotItemCustom(pg.graphicsItems.PlotItem.PlotItem):
    """
    Subclass of **pyqtgraph.graphicsItems.PlotItem.PlotItem** so that the
    effect of "auto-range" button is applied only on Y axis

    The method autoBtnClicked is re-implemented.

    See https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotitem.html
    for details.
    """

    def autoBtnClicked(self):
        """
        Re-implemented
        """

        self.enableAutoRange(axis='y', enable=True)


class SignalWidget(pg.PlotWidget):
    def __init__(self, parent=None, background='default', **kargs):
        """
        Subclass of **pyqtgraph.PlotWidget** so that he effect of "auto-range"
        button is applied only on Y axis

        The constructor is re-implemented so that a PlotItemCustom instance is
        used as the central item of the widget.

        See https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.
        """

        pg.GraphicsView.__init__(self, parent, background)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.enableMouse(False)

        self.plotItem = PlotItemCustom(**kargs)
        self.setCentralItem(self.plotItem)

        for m in [
            'addItem', 'removeItem', 'autoRange', 'clear', 'setXRange',
            'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled',
            'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange',
            'setLimits', 'register', 'unregister', 'viewRect'
        ]:
            setattr(self, m, getattr(self.plotItem, m))

        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)


class ProgressWidget(pg.PlotWidget):
    def __init__(
        self, nframes, parent=None,
        progress_style={'symbol': 'o', 'brush': '#F00', 'size': 7},
        bg_progress_style={'pen': {'color': 'b', 'width': 2}},
        line_style={'color': (0, 0, 0), 'width': 2},
        title=None, title_style={'color': '#000', 'size': '9pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0
    ):
        """
        Subclass of **pyqtgraph.PlotWidget** that defines the widget used as a
        progression bar for video/signal navigation in :class:`.ViSiAnnoT`
        window

        See https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.

        The constructor is re-implemented. It calls the constructor of
        PlotWidget and adds new attributes.

        NB: attributes have the prefix _, so one should use the get methods to
        access them.

        :param nframes: number of frames in the progress bar
        :type nframes: int
        :param parent: see
            https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        :param progress_style: plot style of the sliding progression point
        :type progress_style: dict
        :param bg_progress_style: plot style of the background progression bar
        :type bg_progress_style: dict
        :param line_style: plot style of the current temporal range bounds
        :type line_style: dict
        :param title: progress bar title
        :type title: str
        :param title_style: title style
        :type title_style: dict
        :param ticks_color: color of the ticks text in HEX string or RGB format
        :type ticks_color: str or tuple
        :param ticks_size: font size of the ticks text in pt
        :type ticks_size: float or int
        :param ticks_offset: ticks text offset
        :type ticks_offset: int
        """

        # PlotWidget initialization
        pg.PlotWidget.__init__(self, parent)

        # input attributes
        self._nframes = nframes
        self._dragged = False

        # add background bar
        self._progress_curve = pg.PlotCurveItem(
            [0, self._nframes], [0, 0], **bg_progress_style
        )
        self.addItem(self._progress_curve)

        # add sliding progress point
        self._progress_plot = pg.ScatterPlotItem([0], [0], **progress_style)
        self.addItem(self._progress_plot)

        # add infinite lines for first and last frames
        # (position not initialized)
        self._first_line = pg.InfiniteLine(pen=line_style)
        self.addItem(self._first_line)
        self._last_line = pg.InfiniteLine(pen=line_style)
        self.addItem(self._last_line)

        # disable default mouse interaction
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setMenuEnabled(False)

        # no Y axis
        self.showAxis('left', show=False)

        # set X axis ticks style
        setTicksTextStyle(self.getAxis('bottom'), color=ticks_color,
                          size=ticks_size, offset=ticks_offset)

        # set title
        self.setTitle(title, **title_style)


    def getNFrames(self):
        """
        Get method for attribute nframes

        :returns: number of frames
        :rtype: int
        """

        return self._nframes


    def getProgressCurve(self):
        """
        Get method for attribute progress_curve

        :returns: background progression bar
        :rtype: pyqtgraph.PlotCurveItem
        """

        return self._progress_curve


    def getDragged(self):
        """
        Get method for attribute dragged

        :returns: specify if the sliding progress point is dragged
        :rtype: bool
        """

        return self._dragged


    def getProgressPlot(self):
        """
        Get method for attribute progress_plot

        :returns: sliding progress point
        :rtype: pyqtgraph.ScatterPlotItem
        """

        return self._progress_plot


    def getFirstLine(self):
        """
        Get method for attribute first_line

        :returns: start boundary of the current temporal range in the
            associated :class:`.ViSiAnnoT` window
        :rtype: pyqtgraph.InfiniteLine
        """

        return self._first_line


    def getLastLine(self):
        """
        Get method for attribute first_line

        :returns: end boundary of the current temporal range in the associated
            :class:`.ViSiAnnoT` window
        :rtype: pyqtgraph.InfiniteLine
        """

        return self._last_line


    def getMouseXPosition(self, ev):
        """
        Computes the position of the mouse on the X axis in the progress plot
        coordinates

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent

        :returns: position of the mouse
        :rtype: int
        """

        return self.getViewBox().mapToView(ev.pos()).x()


    def updateNFrames(self, nframes):
        """
        Sets a new value for the number of frames in the progress bar

        :param nframes: new number of frames in the progress bar
        :type nframes: int
        """

        self._nframes = nframes
        self._progress_curve.setData([0, self._nframes], [0, 0])


    def mousePressEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point and launch the mouse dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if left button is clicked and dragging not launched
        if ev.button() == QtCore.Qt.LeftButton and not self._dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self._nframes:
                # set new position of the sliding progress point
                self._progress_plot.setData([position], [0])

                # launch dragging
                self._dragged = True


    def mouseMoveEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point while dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if dragging is launched
        if self._dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self._nframes:
                # set new position of the sliding progress point
                self._progress_plot.setData([position], [0])


    def mouseReleaseEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point and terminate the mouse dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if left button release and if dragging is launched
        if ev.button() == QtCore.Qt.LeftButton and self._dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self._nframes:
                # set new position of the sliding progress point
                self._progress_plot.setData([position], [0])

            # terminate dragging
            self._dragged = False


# *************************************************************************** #
# *************************************************************************** #
# ***************************** Functions *********************************** #
# *************************************************************************** #
# *************************************************************************** #

def setBackgroundColor(color=(255, 255, 255)):
    """
    Sets background color of pyqtgraph widgets (independent of PyQt5 widgets)

    :param color: background color as a string or RGB
        (see https://pyqtgraph.readthedocs.io/en/latest/style.html for details)
    :type color: str or tuple
    """

    pg.setConfigOption('background', color)


def initializeDisplayAndBgColor(color=(255, 255, 255)):
    """
    Creates a Qt application for display and sets background color of the
    pyqtgraph widgets

    It calls the functions :func:`.ToolsPyQt.initializeDisplay` and
    :func:`.Toolspyqtgraph.setBackgroundColor`.

    :param color: background color as a string or RGB
        (see https://pyqtgraph.readthedocs.io/en/latest/style.html for details)
    :type color: str or tuple

    :returns: instance of QtCore.QCoreApplication or QtWidgets.QApplication
    """

    app = initializeDisplay()
    setBackgroundColor(color=color)

    return app


def create2DWidget(
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
    addWidgetToLayout(lay, widget, widget_position)

    return widget


def createWidgetImage(lay, widget_position, im=None, title=None,
                      title_style={'color': '#000', 'size': '9pt'}):
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
        - **widget** (:class:`.ToolsPyqtgraph.PlotWidget`) -- image container
        - **img** (*pyqtgraph.ImageItem*) -- image item
    """

    # create the widget
    widget = create2DWidget(
        lay, widget_position, widget_title=title, title_style=title_style,
        axes_label_dict={}, flag_invert_y=True, flag_aspect_locked=True,
        flag_plot_menu=False
    )

    # create image item and add it to the widget
    img = pg.ImageItem(im)
    widget.addItem(img)

    return widget, img


def createWidgetLogo(lay, widget_position, im, box_size=None):
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
    :rtype: ToolsPyqtgraph.PlotWidget
    """

    widget, _ = createWidgetImage(lay, widget_position, im=im)
    widget.setMouseEnabled(x=False, y=False)
    widget.hideButtons()

    if box_size is not None:
        if isinstance(box_size, int):
            widget.setMaximumSize(box_size, box_size)

        elif (isinstance(box_size, tuple) or isinstance(box_size, list)) and \
                len(box_size) == 2:
            widget.setMaximumSize(box_size[0], box_size[1])

    return widget


def createWidgetSignal(
    lay, widget_position, y_range=[], left_label='',
    left_label_style={'color': '#000', 'font-size': '10pt'},
    ticks_color="#000", ticks_size=9, ticks_offset=0
):
    """
    Creates a widget for plotting signals (see
    :class:`.ToolsPyqtgraph.SignalWidget) and adds it to a grid layout (used in
    :class:`.ViSiAnnoT`)

    For details about color, see
    https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

    :param lay: parent layout where the widget is added
    :type lay: QtWidgets.QGridLayout
       instance of QtWidgets.QGridLayout where the widget is added
    :param widget_position: position of the widget in the parent layout, length
        2 ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
    :type widget_position: tuple
    :param y_range: visible Y range, length 2 ``(y_min, y_max)``, set to
        ``[]`` for auto range
    :type y_range: tuple
    :param left_label: label for Y axis
    :type left_label: str
    :param left_label_style: axis label title style
    :type left_label_style: dict
    :param ticks_color: color of the ticks text in HEX string or RGB format
    :type ticks_color: str or tuple
    :param ticks_size: font size of the ticks text in pt
    :type ticks_size: float or int
    :param ticks_offset: ticks text offset
    :type ticks_offset: int

    :returns: widget containing the signals plots
    :rtype: ToolsPyQt.SignalWidget
    """

    # create the widget
    widget = SignalWidget()

    # add the widget to the layout
    addWidgetToLayout(lay, widget, widget_position)

    # disable default mouse interaction
    widget.setMouseEnabled(x=False)

    # disable plot menu
    widget.setMenuEnabled(False)

    # set axes font
    setTicksTextStyle(
        widget.getAxis('left'), color=ticks_color, size=ticks_size,
        offset=ticks_offset
    )

    setTicksTextStyle(
        widget.getAxis('bottom'), color=ticks_color, size=ticks_size,
        offset=ticks_offset
    )

    # set Y axis label
    widget.getAxis('left').setLabel(text=left_label, **left_label_style)

    # disable auto-range on X axis
    widget.enableAutoRange(axis='x', enable=False)

    # check if Y range is to be set
    if len(y_range) == 2 and y_range[0] < y_range[1]:
        # set Y range
        widget.setYRange(y_range[0], y_range[1])

        # disable default mouse interaction
        widget.setMouseEnabled(y=False)

        # hide auto range button
        widget.hideButtons()

    else:
        # enable auto-range on Y axis
        widget.enableAutoRange(axis='y', enable=True)

    return widget


def setTicksTextStyle(axis_item, color="#000", size=9, offset=0):
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
    :param offset: text offset
    :type offset: int
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
    axis_item.setStyle(tickTextOffset=offset)


def deleteNaNForPlot(data):
    """
    Deletes NaNs from an array so that they are ignored for plotting

    :param data: array where to delete NaNs, shape :math:`(n,)` or
        :math:`(n, 2)` (where first column contains timestamp, second column
        contains data value), list and tuple are also supported
    :type data: numpy array

    :returns: array without NaNs, shape :math:`(m, 2)`, with :math:`m \leq n` ;
        if the input array is 1D (shape :math:`(n,)`), then the first column of
        the output array contains the index of each point in the input array
    :rtype: numpy array
    """

    if isinstance(data, list) or isinstance(data, tuple):
        data = np.array(data)

    if data.ndim == 1:
        data = np.vstack((
            np.arange(data.shape[0]), data
        )).T

    data = np.delete(data, np.where(np.isnan(data[:, 1])), axis=0)

    return data


def addPlotTo2DWidget(
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
    :param flag_nan_void: specify how to handle NaN values

        - ``False``: default behaviour of pyqtgraph
        - ``True``: there is no plotting where NaN

        NB: when calling the method ``plot.setData(data_array)``, the behaviour
        is back to default. If NaNs must be ignored, the function
        :func:`.ToolsPyqtgraph.deleteNaNForPlot` must be called before.
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
        data = deleteNaNForPlot(data)

    plot = pg.PlotDataItem(data, **plot_style)
    widget.addItem(plot)

    return plot


def basic2DPlot(
    data, opts_win_dict={}, opts_wid_dict={},
    plot_style={'pen': {'color': 'b', 'width': 1}}
):
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
        :func:`.ToolsPyQt.createWindow`
    :type opts_win_dict: dict
    :param opts_wid_dict: keyword arguments of the function
        :func:`.ToolsPyqtgraph.create2DWidget`
    :type opts_wid_dict: dict
    :param plot_style: plot style, keys are keyword arguments of the
        constructor of pyqtgraph.PlotDataItem, see link above
    :type plot_style: dict

    :returns:
        - **win** (*QWidgets.QWidget*) -- window container
        - **lay** (*QWidgets.QGridLayout*) -- layout
        - **widget** (*pyqtgraph.PlotWidget*) -- 2D widget filling the whole
          layout
        - **plot** (*pyqtgraph.PlotDataItem*) -- plot item
    """

    win, lay = createWindow(**opts_win_dict)

    if "bg_color" in opts_win_dict.keys():
        setBackgroundColor(opts_win_dict["bg_color"])

    widget = create2DWidget(lay, (0, 0), **opts_wid_dict)

    plot = addPlotTo2DWidget(widget, data, plot_style=plot_style)

    return win, lay, widget, plot


def basicImagePlot(im, **kwargs):
    """
    Creates a window with an image

    :param im: RGB image array of shape :math:`(width, height, 3)`
    :type im: numpy array
    :param kwargs: keyword arguments of the function
        :func:`.ToolsPyQt.createWindow`, if background color of the window is
        specified, then it is also applied to the image widget

    :returns:
        - **win** (*QWidgets.QWidget*) -- window container
        - **lay** (*QWidgets.QGridLayout*) -- layout
        - **widget** (*pyqtgraph.PlotWidget*) -- 2D widget filling the whole
          layout
        - **img** (*pyqtgraph.ImageItem*) -- image item
    """

    win, lay = createWindow(**kwargs)

    if "bg_color" in kwargs.keys():
        setBackgroundColor(kwargs["bg_color"])

    widget, img = createWidgetImage(lay, (0, 0), im=im)

    return win, lay, widget, img


def addLegendTo2DWidget(
    widget, item_dict, size=None, offset=(0, 0), position='inside',
    legend_wid_size=(0, 0)
):
    """
    Adds a legend to a 2D widget

    If specified, this function creates a widget dedicated to the legend,
    instead of having a legend item inside the 2D widget.

    :param widget: widget containing the plot items to legend
    :type widget: pyqtgraph.PlotWidget
    :param item_dict: plot items to legend, key is the legend label and value
        is the associated plot item
    :type item_dict: dict
    :param size: size of the legend item, length 2 ``(width, height)``
    :type size: tuple
    :param offset: offset position in pixels of the legend item in the widget
    :type offset: tuple
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

    :returns:
        - **legend** (*-pyqtgraph.LegendItem*) -- legend item
        - **legend_widget** (*pyqtgraph.PlotWidget*) -- widget containing the
          legend item if it has been created (otherwise ``None``)
    """

    if position == 'inside':
        # create legend
        legend = pg.LegendItem(size=size, offset=offset)
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
        if layout.itemAtPosition(legend_wid_pos[0], legend_wid_pos[1]) == None:
            # create the legend widget
            legend_widget = create2DWidget(
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
        legend = pg.LegendItem(size=size, offset=offset)
        legend.setParentItem(legend_widget.graphicsItem())


    # set the legend item to the corresponding item and label
    for item_label, item in item_dict.items():
        legend.addItem(item, item_label)

    return legend, legend_widget


def addTextItemTo2DWidget(
    widget, pos, text='', color="#000000", html=None, anchor=(0.5, 0.5),
    border=None, fill=None, angle=0, flag_arrow=False, arrow_angle=0,
    arrow_style={
        'headLen': 15, 'tipAngle': 20, 'pen': '#000000', 'brush': '#000000'
    }
):
    """
    Adds a text item to a 2D widget

    For details about color, see
    https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

    :param widget: widget where the text item must be displayed
    :type widget: pyqtgraph.PlotWidget
    :param pos: position of the text item in the widget, length 2 ``(x, y)``
    :type pos: tuple
    :param text: text to display
    :type text: str
    :param color: text color, may be a tuple with RGB or a HEX string
    :type color: str or tuple
    :param html: html text to display, it overwrites ``text`` and ``color``
    :type html: str
    :param anchor: coordinate of the text item that is anchored to its position
        ``pos`` (``(0, 0)`` => top left, ``(1, 0)`` => top right, ``(1, 0)`` =>
        bottom left, ``(1, 1)`` => bottom right
    :type anchor: tuple
    :param border: color of the border, may be a tuple with RGB or a HEX
        string
    :type border: str or tuple
    :param fill: color used when filling within the border, may be a tuple with
        RGB or a HEX
    :type fill: str or tuple
    :param angle: angle in degrees to rotate the text item
    :type angle: float
    :param flag_arrow: specify if an arrow must be added
    :type flag_arrow: bool
    :param arrow_angle: angle in degrees to rotate the arrow
        (arrow pointing to the left)
    :type arrow_angle: float
    :param arrow_style: see
        https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/arrowitem.html#pyqtgraph.ArrowItem.setStyle
    :type arrow_style: dict

    :returns:
        - **text_item** (*pyqtgraph.TextItem*)
        - **arrow_item** (*pyqtgraph.ArrowItem*) -- may be ``None`` if arrow
          not specified
    """

    # create text item
    text_item = pg.TextItem(
        text=text, color=color, html=html, anchor=anchor, border=border,
        fill=fill, angle=angle
    )

    # set the text item position
    text_item.setPos(pos[0], pos[1])

    # add the text item to the widget
    widget.addItem(text_item)

    # create an arrow item if specified and add it to the widget
    if flag_arrow:
        arrow_item = pg.ArrowItem(pos=pos, angle=arrow_angle)
        arrow_item.setStyle(**arrow_style)
        widget.addItem(arrow_item)
    else:
        arrow_item = None

    return text_item, arrow_item


def createColorMap(values, colors, lut_dim=256):
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


def createWidgetColorBar(
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
        - **wid_bar** (:class:`.ToolsPyqtgraph.PlotWidget`) -- widget
          containing the color bar
        - **bar_img_item** (*pyqtgraph.ImageItem*) -- image item of the color
          bar
    """

    # legend color bar image
    lut_img = np.expand_dims(lut, axis=0)
    lut_img = np.tile(lut_img, (img_width, 1, 1))

    # create legend widget
    wid_bar, bar_img_item = createWidgetImage(lay, widget_position, im=lut_img)
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


def addMeanStdPlotTo2DWidget(
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
        :func:`.ToolsPyqtgraph.addPlotTo2DWidget`, used for the plot item of
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
    mean_plot = addPlotTo2DWidget(wid, data_mean_tmp, **kwargs)

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
            data = np.array([[x, med - std],
                             [x, med + std],
                             [x - x_step / 4, med - std],
                             [x + x_step / 4, med - std],
                             [x - x_step / 4, med + std],
                             [x + x_step / 4, med + std]])

            # concatenate std curve array
            data_std_tmp = np.concatenate((data_std_tmp, data))

            # add text item with number of data
            if nb_samples is not None:
                text_item, _ = addTextItemTo2DWidget(
                    wid, (x + x_step / 8, med + std / 2),
                    text="%d" % nb_samples
                )
                text_item_list.append(text_item)

    # plot std curve
    std_plot = pg.PlotCurveItem(
        data_std_tmp[:, 0], data_std_tmp[:, 1], pen=pen_std_style,
        connect="pairs"
    )

    wid.addItem(std_plot)

    return mean_plot, std_plot, text_item_list
