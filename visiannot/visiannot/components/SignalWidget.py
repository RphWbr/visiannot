# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.SignalWidget` and :class:`.PlotItemCustom`
"""


import pyqtgraph as pg
from PyQt5.QtWidgets import QSizePolicy
from ...tools.ToolsPyqtgraph import setTicksTextStyle


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
    def __init__(
        self, parent=None, background='default', kwargs_plot_item={},
        kwargs_axes={}
    ):
        """
        Subclass of **pyqtgraph.PlotWidget** so that he effect of "auto-range"
        button is applied only on Y axis

        The constructor is re-implemented so that a PlotItemCustom instance is
        used as the central item of the widget.

        See https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.

        :param parent: first positional argument of **pyqtgraph.GraphicsView**
        :param background: second positional argument of
            **pyqtgraph.GraphicsView**
        :param kwargs_plot_item: keyword arguments of the constructor of
            :class:`.PlotItemCustom`
        :type kwargs_plot_item: dict
        :param kwargs_axes: keyword arguments of :meth:`.setAxesStyle`
        :type kwargs_axes: dict
        """

        pg.GraphicsView.__init__(self, parent, background)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.enableMouse(False)

        self.plotItem = PlotItemCustom(**kwargs_plot_item)
        self.setCentralItem(self.plotItem)

        for m in [
            'addItem', 'removeItem', 'autoRange', 'clear', 'setXRange',
            'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled',
            'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange',
            'setLimits', 'register', 'unregister', 'viewRect'
        ]:
            setattr(self, m, getattr(self.plotItem, m))

        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

        # disable default mouse interaction
        self.setMouseEnabled(x=False)

        # disable plot menu
        self.setMenuEnabled(False)

        # set axes style
        self.setAxesStyle(**kwargs_axes)


    def setAxesStyle(
        self, y_range=[], left_label='',
        left_label_style={'color': '#000', 'font-size': '10pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0
    ):
        """
        Sets style of left and bottom axes

        For details about color, see
        https://pyqtgraph.readthedocs.io/en/latest/functions.html#color-pen-and-brush-functions

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
        """

        # set axes font
        setTicksTextStyle(
            self.getAxis('left'), color=ticks_color, size=ticks_size,
            offset=ticks_offset
        )

        setTicksTextStyle(
            self.getAxis('bottom'), color=ticks_color, size=ticks_size,
            offset=ticks_offset
        )

        # set Y axis label
        self.getAxis('left').setLabel(text=left_label, **left_label_style)

        # disable auto-range on X axis
        self.enableAutoRange(axis='x', enable=False)

        # check if Y range is to be set
        if len(y_range) == 2 and y_range[0] < y_range[1]:
            # set Y range
            self.setYRange(y_range[0], y_range[1])

            # disable default mouse interaction
            self.setMouseEnabled(y=False)

            # hide auto range button
            self.hideButtons()

        else:
            # enable auto-range on Y axis
            self.enableAutoRange(axis='y', enable=True)
