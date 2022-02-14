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
from PyQt5.QtCore import Qt
from ...tools import pyqtgraph_overlayer
from ...tools.pyqt_overlayer import add_widget_to_layout


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
        self, visi, widget_position, parent=None, background='default',
        wid_height=150, cursor_style={'color': "F00", 'width': 1},
        cursor_dragged_style={'color': "F0F", 'width': 2}, **kwargs
    ):
        """
        Subclass of **pyqtgraph.PlotWidget** so that he effect of "auto-range"
        button is applied only on Y axis

        The constructor is re-implemented so that an instance of
        :class:`.PlotItemCustom` is used as the central item of the widget.

        See https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param parent: first positional argument of **pyqtgraph.GraphicsView**
        :param background: second positional argument of
            **pyqtgraph.GraphicsView**
        :param kwargs: keyword arguments of :meth:`.setAxesStyle`
        """

        # parent constructor
        pg.GraphicsView.__init__(self, parent, background)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.enableMouse(False)

        #: Instance of :class:`.PlotItemCustom`, central item of the widget
        self.plotItem = PlotItemCustom()
        self.setCentralItem(self.plotItem)

        # transfer methods from central plot item to the widget
        for m in [
            'addItem', 'removeItem', 'autoRange', 'clear', 'setXRange',
            'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled',
            'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange',
            'setLimits', 'register', 'unregister', 'viewRect'
        ]:
            setattr(self, m, getattr(self.plotItem, m))

        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)

        # disable mouse interaction on X axis
        self.setMouseEnabled(x=False)

        # disable plot menu
        self.setMenuEnabled(False)

        # set widget height
        self.setMinimumHeight(wid_height)

        # set axes style
        self.setAxesStyle(**kwargs)

        #: (*list*) Signal plots in the widget, each element corresponds to one
        #: signal and is an instance of **pyqtgraph.PlotDataItem**
        self.plot_list = []

        #: (*pyqtgraph.InfiniteLine*) Temporal cursor
        self.cursor = pg.InfiniteLine(
            angle=90, movable=True, pen=cursor_style,
            hoverPen=cursor_dragged_style
        )
        self.cursor.setPos(0)
        self.addItem(self.cursor)

        #: (*list*) Displayed temporal intervals, each element is a list of
        #: instances of **pyqtgraph.LinearRegionItem**
        self.region_interval_list = []

        # add widget to the layout of the associated instance of ViSiAnnoT
        add_widget_to_layout(visi.lay, self, widget_position)

        # listen to callback
        self.scene().sigMouseClicked.connect(
            lambda ev: self.signalMouseClicked(ev, visi)
        )
        self.cursor.sigDragged.connect(
            lambda cursor: self.currentCursorDragged(cursor, visi)
        )


    def setAxesStyle(
        self, y_range=[], left_label='',
        left_label_style={'color': '#000', 'font-size': '10pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0, y_ticks_width=30
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
        :param y_ticks_width: horizontal space in pixels for the text of Y axis
            ticks
        :type y_ticks_width: int
        """

        # set axes font
        pyqtgraph_overlayer.set_ticks_text_style(
            self.getAxis('left'), color=ticks_color, size=ticks_size,
            tickTextOffset=ticks_offset, autoExpandTextSpace=False,
            tickTextWidth=y_ticks_width
        )

        pyqtgraph_overlayer.set_ticks_text_style(
            self.getAxis('bottom'), color=ticks_color, size=ticks_size,
            tickTextOffset=ticks_offset
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


    def createPlotItems(
        self, first_frame_ms, last_frame_ms, sig_list, interval_list,
        threshold_list
    ):
        """
        Creates signal plot items, interval region items and threshold lines

        It also sets the bounds of :attr:`.cursor`.

        :param first_frame_ms: start timestamp of the temporal range to display
            (in milliseconds)
        :type first_frame_ms: float
        :param last_frame_ms: end timestamp of the temporal range to display
            (in milliseconds)
        :type last_frame_ms: float
        :param sig_list: signals to plot, each element is an instance of
            :class:`.Signal`
        :type sig_list: list 
        :param interval_list: intervals to plot, each element is a list of
            length 3:

            - (*numpy array*) Intervals data, shape :math:`(n_{intervals}, 2)`
            - (*float*) Frequency (``0`` if timestamps)
            - (*tuple*) Plot color (RGBA)
        :type interval_list: list
        :param threshold_list: thresholds to plot, each element is a list of
            length 2:

            - (*float*) Value of the threshold on Y axis
            - (*tuple*) Color to plot (RGB), it can also be a string with HEX
              color
        :type threshold_list: list
        """

        # set bounds of the temporal cursor (for dragging)
        # last_frame - 1 => prevents from moving to next temporal range window
        self.cursor.setBounds([first_frame_ms, last_frame_ms - 1])

        # create legend item if necessary
        if len(sig_list) > 1:
            legend = pg.LegendItem(offset=(0, 10))
            legend.setParentItem(self.graphicsItem())

        # loop on signals to plot
        for sig in sig_list:
            # get sub-array of the signal in the temporal range
            data_in_current_range = sig.get_data_in_range(
                first_frame_ms, last_frame_ms
            )

            # plot signal in the widget
            plot = pyqtgraph_overlayer.add_plot_to_widget(
                self, data_in_current_range, flag_nan_void=True,
                plot_style=sig.plot_style
            )
            self.plot_list.append(plot)

            # add legend
            if len(sig_list) > 1 and sig.legend_text != "":
                legend.addItem(plot, sig.legend_text)

        # loop on intervals to plot
        for intervals, freq, color in interval_list:
            self.plotIntervals(intervals, freq, color)

        # loop on thresholds to plot
        for value, color in threshold_list:
            infinite_line = pg.InfiniteLine(
                pos=value, angle=0, pen={'color': color, 'width': 1}
            )
            self.addItem(infinite_line)


    def updatePlotItems(
        self, first_frame_ms, last_frame_ms, sig_list, interval_list
    ):
        """
        Updates signal plot items, interval region items and threshold lines

        It also sets the bounds of :attr:`.cursor`.

        :param first_frame_ms: start timestamp of the temporal range to display
            (in milliseconds)
        :type first_frame_ms: int
        :param last_frame_ms: end timestamp of the temporal range to display
            (in milliseconds)
        :type last_frame_ms: int
        :param sig_list: signals to plot, each element is an instance of
            :class:`.Signal`
        :type sig_list: list 
        :param interval_list: intervals to plot, each element is a list of
            length 3:

            - (*numpy array*) Intervals data, shape :math:`(n_{intervals}, 2)`
            - (*float*) Frequency (``0`` if timestamps)
            - (*tuple*) Plot color (RGBA)
        :type interval_list: list
        """

        # update temporal cursor bounds (for dragging)
        # last_frame - 1 => prevents from moving to next temporal range window
        self.cursor.setBounds([first_frame_ms, last_frame_ms - 1])

        # loop on signals to plot
        for sig, sig_plot in zip(sig_list, self.plot_list):
            # get data in the current temporal range
            data_in_current_range = sig.get_data_in_range(
                first_frame_ms, last_frame_ms
            )

            # check if empty signal in the temporal range
            if data_in_current_range.shape[0] == 0:
                sig_plot.clear()

            else:
                # signal plot
                sig_plot.setData(data_in_current_range, connect="finite")

        # plot intervals regions
        self.clearIntervalsRegions()
        for interval, freq, color in interval_list:
            self.plotIntervals(interval, freq, color)


    def clearIntervalsRegions(self):
        """
        Clears the display of intervals regions

        It sets the attribute :attr:`.region_interval_list` to an empty list.
        """

        for region_list in self.region_interval_list:
            for region in region_list:
                self.removeItem(region)

        self.region_interval_list = []


    def plotIntervals(self, data_interval, freq, color):
        """
        Plots intervals data as a region

        It appends the attribute :attr:`.region_interval_list` with the
        displayed region

        :param data_interval: intervals to be displayed, shape
            :math:`(n_{intervals}, 2)`, each line is an interval with start
            frame and end frame (sampled at ``freq``), relatively to the start
            timestamp of the data file) ; the intervals might be expressed in
            milliseconds, then ``freq`` must be set to ``0``
        :type data_interval: numpy array
        :param freq: sampling frequency of intervals frames, set it to ``0`` if
            intervals expressed in milliseconds
        :type freq: float
        :param color: plot color (RGBA)
        :type color: tuple or list
        """

        region_list = []
        for interval in data_interval:
            det_0 = interval[0]
            det_1 = interval[1]

            # convert interval frames to milliseconds
            if freq > 0:
                det_0 = 1000.0 * det_0 / freq
                det_1 = 1000.0 * det_1 / freq

            # plot region
            region = pyqtgraph_overlayer.add_region_to_widget(
                det_0, det_1, self, color
            )
            region_list.append(region)

        self.region_interval_list.append(region_list)


    def getMouseTemporalPosition(self, ev):
        """
        Gets the position of the mouse on the X axis

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent

        :returns: position of the mouse on the X axis, ``-1`` if the mouse
            clicked on a label item (most likely the widget title)
        :rtype: float
        """

        # check what is being clicked
        for item in self.scene().items(ev.scenePos()):
            # if widget title is checked, nothing is returned
            if type(item) is pg.graphicsItems.LabelItem.LabelItem:
                return -1

        # map the mouse position to the plot coordinates
        position = self.getViewBox().mapToView(ev.pos()).x()

        return position


    def signalMouseClicked(self, ev, visi):
        """
        Callback method for managing mouse click on the signal widget

        Connected to the signal ``sigMouseClicked`` of the attribute
        :attr:`scene`.

        On one hand, it allows to define manually a temporal interval on which
        to zoom by calling the method :meth:`.zoom_or_annot_clicked`.

        On the other hand, it allows to define a new annotation and to add it
        the annotation file by calling the method
        :meth:`zoom_or_annot_clicked`. Also, it allows to delete
        manually a specific events annotation by calling the method
        :meth:`.delete_clicked` on the attribute
        :attr:`.ViSiAnnoT.wid_annotevent`.

        It also updates the position of the temporal cursor by calling the
        method :meth:`.currentCursorClicked`.

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        keyboard_modifiers = ev.modifiers()

        # map the mouse position to the plot coordinates
        pos_ms = self.getMouseTemporalPosition(ev)

        # convert from plot coordinates to frame number sampled at reference
        # frequency in ViSiAnnoT
        pos_frame = visi.convert_ms_to_frame_ref(pos_ms)

        # check if mouse clicked on a signal widget
        if pos_frame >= 0:
            # check if left button clicked
            if ev.button() == Qt.LeftButton:
                # crtl+shift key => delete annotation
                if keyboard_modifiers == \
                        (Qt.ControlModifier | Qt.ShiftModifier):
                    # only when display mode is on
                    if visi.wid_annotevent.push_text_list[3].text() == "On":
                        visi.wid_annotevent.delete_clicked(visi, pos_frame)

                # alt key => display description
                elif keyboard_modifiers == Qt.AltModifier:
                    visi.wid_annotevent.description(
                        visi, ev, pos_frame, pos_ms
                    )

                # no key modifier (only left button clicked)
                else:
                    self.currentCursorClicked(pos_frame, visi)

            elif ev.button() == Qt.RightButton:
                visi.zoom_or_annot_clicked(ev, pos_frame, pos_ms)


    def currentCursorClicked(self, position, visi):
        """
        Sets the current frame :attr:`.frame_id` at the specified
        position

        If the specified position is out of bounds of the current temporal
        range defined by :attr:`.first_frame` and :attr:`.last_frame`,
        then the current frame is not set.

        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`)
        :type position: int
        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # check if temporal_position is in the current range
        if position >= visi.first_frame and position < visi.last_frame:
            # update current frame
            visi.update_frame_id(position)


    def currentCursorDragged(self, cursor, visi):
        """
        Callback method for mouse dragging of the temporal cursor in a signal
        widget

        It updates the current frame :attr:`.ViSiAnnoT.frame_id` at the current
        position of the temporal cursor.

        Connected to the signal ``sigDragged`` of the attribute :attr:`.cursor`

        :param cursor: temporal cursor that is dragged
        :type cursor: pyqtgraph.InfiniteLine
        """

        # update frame id (convert frame id from signal to ref)
        visi.update_frame_id(visi.convert_ms_to_frame_ref(int(cursor.value())))
