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
from ...tools.pyqtgraph_overlayer import set_ticks_text_style, \
    set_temporal_ticks
from ...tools.pyqt_overlayer import add_widget_to_layout
from ...tools.datetime_converter import convert_frame_to_string, \
    convert_frame_to_absolute_datetime_string


class ProgressWidget(pg.PlotWidget):
    def __init__(
        self, visi, widget_position, parent=None,
        progress_style={'symbol': 'o', 'brush': '#F00', 'size': 7},
        bg_progress_style={'pen': {'color': 'b', 'width': 2}},
        line_style={'color': (0, 0, 0), 'width': 2},
        title='', title_style={'color': '#000', 'size': '9pt'},
        ticks_color="#000", ticks_size=9, ticks_offset=0,
        maximum_height=80, nb_ticks=5, current_fmt="%Y-%m-%dT%H:%M:%S.%s",
        range_fmt="%H:%M:%S.%s", ticks_fmt="%H:%M:%S.%s"
    ):
        """
        Widget with the progression bar for video/signal navigation in a
        :class:`.ViSiAnnoT` window

        Inherits from **pyqtgraph.PlotWidget**, see
        https://pyqtgraph.readthedocs.io/en/latest/widgets/plotwidget.html
        for details about parent class.

        The constructor is re-implemented. It calls the constructor of
        PlotWidget and adds new attributes.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
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
        :param current_fmt: datetime string format of the current temporal
            position in progress bar, see
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        :type current_fmt: str
        :param range_fmt: datetime string format of the temporal range
            duration in progress bar, see keyword argument ``fmt`` of
            :func:`.convert_datetime_to_string`
        :type range_fmt: str
        :param ticks_fmt: datetime string format of X axis ticks text, see
            keyword argument ``fmt`` of :func:`.convert_datetime_to_string`
        :type ticks_fmt: str
        """

        # PlotWidget initialization
        pg.PlotWidget.__init__(self, parent)

        #: (*int*) Number of frames on the progress bar (defined by the
        #: associated instance of :class:`.ViSiAnnoT`)
        self.nframes = visi.nframes

        #: (*str*) Datetime string format of the current temporal position in
        #: progress bar
        self.current_fmt = current_fmt

        #: (*str*) Datetime string format of the temporal range duration in
        #: progress bar
        self.range_fmt = range_fmt

        #: (*str*) Datetime string format of the text of X axis ticks
        self.ticks_fmt = ticks_fmt

        #: (*int*) Number of ticks on the progress bar axis
        self.nb_ticks = nb_ticks

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

        self.setBoundaries(visi.first_frame, visi.last_frame)

        # disable default mouse interaction
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        self.setMenuEnabled(False)

        # set widget height
        self.setMaximumHeight(maximum_height)

        # no Y axis
        self.showAxis('left', show=False)

        # set X axis ticks style
        set_ticks_text_style(
            self.getAxis('bottom'), color=ticks_color, size=ticks_size,
            tickTextOffset=ticks_offset
        )

        # set temporal ticks and X axis range
        set_temporal_ticks(
            self, self.nb_ticks, (0, self.nframes, visi.fps),
            visi.beginning_datetime, fmt=self.ticks_fmt
        )

        # create title
        self.setTitle(title, **title_style)
        self.updateTitle(visi.fps, visi.beginning_datetime)

        # add widget to the layout of the associated instance of ViSiAnnoT
        add_widget_to_layout(visi.lay, self, widget_position)

        # listen to the callback method
        self.progress_plot.sigPlotChanged.connect(
            lambda: self.mouseDraggedProgress(visi)
        )


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

        :param first_frame: new position of the start boundary
        :type first_frame: int
        :param last_frame: new position of the end boundary
        :type last_frame: int
        """

        self.first_line.setValue(first_frame)
        self.last_line.setValue(last_frame)


    def updateTitle(self, fps, beginning_datetime):
        """
        Updates the title of the progress bar

        :param fps: reference frequency of the associated instance of
            :class:`.ViSiAnnoT`
        :type fps: float
        :param beginning_datetime: beginning datetime of the reference modality
            of the associated instance of :class:`.ViSiAnnoT`
        :type beginning_datetime: datetime.datetime
        """

        current_range_string = convert_frame_to_string(
            self.last_line.value() - self.first_line.value(), fps,
            fmt=self.range_fmt
        )

        temporal_position = int(
            self.progress_plot.getData()[0][0]
        )

        frame_id_string = convert_frame_to_absolute_datetime_string(
            temporal_position, fps, beginning_datetime, fmt=self.current_fmt
        )

        self.setTitle(
            '%s (frame %d) - temporal range duration: %s'
            % (frame_id_string, temporal_position, current_range_string)
        )


    def setProgressPlot(self, frame_id):
        """
        Sets the position of the sliding progress point

        :param frame_id: new position of the sliding progress point
        :type frame_id: int
        """

        self.progress_plot.setData([frame_id], [0])


    def updateFromViSiAnnoT(
        self, nframes, first_frame, last_frame, fps, beginning_datetime
    ):
        """
        Sets the attribute :attr:`.ProgressWidget.nframes` with regards to the
        associated instance of :class:`.ViSiAnnoT` and updates the plot (useful
        for long recordings)

        :param nframes: new number of frames in the progress bar with regards
            to the associated instance of :class:`.ViSiAnnoT`
        :type nframes: int
        :param first_frame: new position of the start boundary in frame number
        :type first_frame: int
        :param last_frame: new position of the end boundary in frame number
        :type last_frame: int
        :param fps: reference frequency of the associated instance of
            :class:`.ViSiAnnoT`
        :type fps: float
        :param beginning_datetime: beginning datetime of the reference modality
            of the associated instance of :class:`.ViSiAnnoT`
        :type beginning_datetime: datetime.datetime
        """

        # set attributes
        self.nframes = nframes

        # set background progression bar
        self.progress_curve.setData([0, self.nframes], [0, 0])

        # set X axis ticks style
        set_temporal_ticks(
            self, self.nb_ticks, (0, self.nframes, fps), beginning_datetime,
            fmt=self.ticks_fmt
        )

        self.setBoundaries(first_frame, last_frame)


    def mouseDraggedProgress(self, visi):
        """
        Callback method for mouse dragging of the navigation point in the
        progress bar

        It updates the current frame :attr:`.ViSiAnnoT.frame_id` at the
        current position defined by the mouse in the progress bar widget.

        Connected to the signal ``sigPlotChanged`` of the scatter plot item of
        :attr:`.wid_progress` (accessed with the method
        :meth:`graphicsoverlayer.pyqtgraph_overlayer.ProgressWidget.getProgressPlot`).
        """

        # check if dragging
        if self.flag_dragged:
            # get the temporal position
            temporal_position = int(
                self.progress_plot.getData()[0][0]
            )

            # update current frame
            visi.update_frame_id(temporal_position)

            # define new range
            current_range = visi.last_frame - visi.first_frame

            if visi.frame_id + current_range >= self.nframes:
                visi.first_frame = self.nframes - current_range
                visi.last_frame = self.nframes

            else:
                visi.first_frame = visi.frame_id
                visi.last_frame = visi.first_frame + current_range

            # update plots signals
            visi.update_signal_plot()
