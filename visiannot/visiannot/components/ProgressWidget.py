# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.ProgressWidget`
"""


import pyqtgraph as pg
from PyQt5 import QtCore
from ...tools.ToolsPyqtgraph import setTicksTextStyle, setTemporalTicks
from ...tools.ToolsDateTime import convertFrameToString, \
    convertFrameToAbsoluteDatetimeString


class ProgressWidget(pg.PlotWidget):
    def __init__(
        self, nframes, beginning_datetime, fps, parent=None,
        progress_style={'symbol': 'o', 'brush': '#F00', 'size': 7},
        bg_progress_style={'pen': {'color': 'b', 'width': 2}},
        line_style={'color': (0, 0, 0), 'width': 2},
        title='', title_style={'color': '#000', 'size': '9pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0,
        maximum_height=80, nb_ticks=5
    ):
        """
        Widget with the progression bar for video/signal navigation in a
        :class:`.ViSiAnnoT` window

        Inherits from **pyqtgraph.PlotWidget**, see
        https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.

        The constructor is re-implemented. It calls the constructor of
        PlotWidget and adds new attributes.

        :param nframes: number of frames in the progress bar
        :type nframes: int
        :param beginning_datetime: beginning datetime of the reference modality
            in the associated instance of :class:`.ViSiAnnoT`
        :type beginning_datetime: datetime.datetime
        :param fps: reference frequency of the associated instance of
            :class:`.ViSiAnnoT`
        :type fps: float
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
        :param maximum_height: maximum height in pixels of the widget
        :type maximum_height: int
        :param nb_ticks: number of ticks on the progress bar axis
        :type nb_ticks: int
        """

        # PlotWidget initialization
        pg.PlotWidget.__init__(self, parent)

        #: (*int*) Number of frames in the progress bar
        self.nframes = nframes

        #: (*float*) Reference frequency of the associated instance of
        #: :class:`.ViSiAnnoT`
        self.fps = fps

        #: (*int*) Number of ticks on the progress bar axis
        self.nb_ticks = nb_ticks

        #: (*datetime.datetime*) Beginning datetime of the reference modality
        #: in the associated instance of :class:`.ViSiAnnoT`
        self.beginning_datetime = beginning_datetime

        #: (*bool*) Specify if the sliding progress point is dragged
        self.flag_dragged = False

        #: (*pyqtgraph.PlotCurveItem*) Background progression bar
        self.progress_curve = pg.PlotCurveItem(
            [0, self.nframes], [0, 0], **bg_progress_style
        )
        self.addItem(self.progress_curve)

        #: (*pyqtgraph.ScatterPlotItem*) Sliding progress point
        self.progress_plot = pg.ScatterPlotItem([0], [0], **progress_style)
        self.addItem(self.progress_plot)

        # add infinite lines for first and last frames
        # (position not initialized)

        #: (*pyqtgraph.InfiniteLine*) Start boundary of the current temporal
        #: range in the associated :class:`.ViSiAnnoT` window
        self.first_line = pg.InfiniteLine(pen=line_style)
        self.addItem(self.first_line)

        #: (*pyqtgraph.InfiniteLine*) End boundary of the current temporal
        #: range in the associated :class:`.ViSiAnnoT` window
        self.last_line = pg.InfiniteLine(pen=line_style)
        self.addItem(self.last_line)

        # disable default mouse interaction
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setMenuEnabled(False)

        # set widget height
        self.setMaximumHeight(maximum_height)

        # no Y axis
        self.showAxis('left', show=False)

        # set X axis ticks style
        setTicksTextStyle(
            self.getAxis('bottom'), color=ticks_color, size=ticks_size,
            offset=ticks_offset
        )

        # set temporal ticks and X axis range
        setTemporalTicks(
            self, self.nb_ticks, (0, self.nframes, self.fps),
            self.beginning_datetime
        )

        # create title
        self.setTitle(title, **title_style)


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


    def mousePressEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point and launch the mouse dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if left button is clicked and dragging not launched
        if ev.button() == QtCore.Qt.LeftButton and not self.flag_dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self.nframes:
                # set new position of the sliding progress point
                self.progress_plot.setData([position], [0])

                # launch dragging
                self.flag_dragged = True


    def mouseMoveEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point while dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if dragging is launched
        if self.flag_dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self.nframes:
                # set new position of the sliding progress point
                self.progress_plot.setData([position], [0])


    def mouseReleaseEvent(self, ev):
        """
        Re-implemented in order to set the new position of the sliding
        progression point and terminate the mouse dragging

        :param ev: emitted when the mouse is clicked/moved
        :type ev: QtGui.QMouseEvent
        """

        # check if left button release and if dragging is launched
        if ev.button() == QtCore.Qt.LeftButton and self.flag_dragged:
            # get mouse position on the X axis
            position = self.getMouseXPosition(ev)

            # check boundaries
            if position >= 0 and position < self.nframes:
                # set new position of the sliding progress point
                self.progress_plot.setData([position], [0])

            # terminate dragging
            self.flag_dragged = False


    def setBoundaries(self, first_frame, last_frame):
        """
        Sets the position of the current temporal range boundaries
        (:attr:`.first_line` and :attr:`.last_frame`)

        :param first_frame: new position of the start boundary
        :type first_frame: int
        :param last_frame: new position of the end boundary
        :type last_frame: int
        """

        self.first_line.setValue(first_frame)
        self.last_line.setValue(last_frame)


    def updateTitle(self, frame_id, first_frame, last_frame):
        """
        Updates the title of the progress bar :attr:`.wid_progress`
        with the values of the current temporal range defined by
        :attr:`.first_frame` and :attr:`.last_frame`
        """

        current_range_string = convertFrameToString(
            last_frame - first_frame, self.fps
        )

        frame_id_string = convertFrameToAbsoluteDatetimeString(
            frame_id, self.fps, self.beginning_datetime
        )

        self.setTitle(
            '%s (frame %d) - temporal range duration: %s'
            % (frame_id_string, frame_id, current_range_string)
        )


    def setCurrentTemporalRange(self, frame_id, first_frame, last_frame):
        """
        Sets a new current temporal range in the progress bar (boundaries and
        title)

        :param frame_id: new position of the temporal cursor
        :type frame_id: int
        :param first_frame: new start position of the temporal range
        :type first_frame: int 
        :param last_frame: new end position of the temporal range
        :type last_frame: int
        """

        self.setBoundaries(first_frame, last_frame)
        self.updateTitle(frame_id, first_frame, last_frame)


    def setProgressPlot(self, frame_id):
        """
        Sets the position of the sliding progress point

        :param frame_id: new position of the sliding progress point
        :type frame_id: int
        """

        self.progress_plot.setData([frame_id], [0])


    def updateFromViSiAnnoT(
        self, nframes, beginning_datetime, *args
    ):
        """
        Sets the attributes related to the associated instance of
        :class:`.ViSiAnnoT` and updates the plot (useful for long recordings)

        The reference frequency should not change when changing file in a long
        recording, so no need to update it.

        :param nframes: number of frames in the progress bar
        :type nframes: int
        :param beginning_datetime: beginning datetime of the reference modality
            in the associated instance of :class:`.ViSiAnnoT`
        :type beginning_datetime: datetime.datetime
        :param args: positional arguments of :meth:`.setBoundaries`
        """

        # set attributes
        self.nframes = nframes
        self.beginning_datetime = beginning_datetime

        # set background progression bar
        self.progress_curve.setData([0, self.nframes], [0, 0])

        # set X axis ticks style
        setTemporalTicks(
            self, self.nb_ticks, (0, self.nframes, self.fps),
            self.beginning_datetime
        )

        # set boundaries and update title
        self.setCurrentTemporalRange(*args)
