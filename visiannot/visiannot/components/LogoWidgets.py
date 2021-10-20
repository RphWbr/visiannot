# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining classes for creating a widget with a logo image on which it is
possible to click on to activate an action
"""

from ...tools.ToolsPyqtgraph import createWidgetLogo
from ...tools.ToolsImage import readImage
from ...tools.ToolsData import getWorkingDirectory


# get directory of the module
MODULE_DIR = getWorkingDirectory(__file__)


class LogoWidget():
    def __init__(self, visi, widget_position, im_name):
        """
        Base class of widgets with a single image on which it is possible to
        click in order to activate an action

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the progress widget in the layout
            of the associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param im_name: file name of the image to display in the widget, it
            must be located in the folder ``Images`` next to the module
        :type im_path: str
        """

        # get absolute path to the image
        im_path = "%s/Images/%s.jpg" % (MODULE_DIR, im_name)

        # create widget with image and add it to the layout of the
        # associated instance of ViSiAnnoT
        wid = createWidgetLogo(
            visi.lay, widget_position, readImage(im_path), box_size=50
        )

        # listen to callback
        wid.scene().sigMouseClicked.connect(lambda: self.callback(visi))


    def callback(self):
        """
        Callback method called when the widged is cliked on, to be
        re-implemented in the child class
        """

        pass


class ZoomWidget(LogoWidget):
    def __init__(self, *args, zoom_factor=2):
        """
        Base class of widgets for zoom (in / out)

        Compared to :class:`.LogoWidget`, it just adds the attribute
        :attr:`.zoom_factor`.

        :param args: positional arguments of the constructor of
            :class:`.LogoWidget`
        :param zoom_factor: zoom factor
        :type zoom_factor: float
        """

        #: (*float*) Zoom factor
        self.zoom_factor = zoom_factor

        # parent constructor
        LogoWidget.__init__(self, *args)


class ZoomInWidget(ZoomWidget):
    def callback(self, visi):
        """
        Callback method for zooming in

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get current X axis range
        axis = visi.wid_sig_list[0].getAxis('bottom')
        axis_range_min, axis_range_max = axis.range[0], axis.range[1]

        # convert from signal to ref
        axis_range_min = visi.convertMsToFrameRef(axis_range_min)
        axis_range_max = visi.convertMsToFrameRef(axis_range_max)

        # check if current range is large enough for zoom in
        if axis_range_max - axis_range_min > 5:
            # compute the range on the left/right side of the temporal cursor
            left = visi.frame_id - axis_range_min
            right = axis_range_max - visi.frame_id

            # compute the first frame and the last frame after zooming
            visi.first_frame = max(
                int(visi.frame_id - left / self.zoom_factor), visi.first_frame
            )

            visi.last_frame = min(
                int(visi.frame_id + right / self.zoom_factor), visi.last_frame
            )

            # update signals plots
            visi.updateSignalPlot()


class ZoomOutWidget(ZoomWidget):
    def callback(self, visi):
        """
        Callback method for zooming out

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get current X axis range
        axis = visi.wid_sig_list[0].getAxis('bottom')
        axis_range_min, axis_range_max = axis.range[0], axis.range[1]

        # convert from signal to ref
        axis_range_min = visi.convertMsToFrameRef(axis_range_min)
        axis_range_max = visi.convertMsToFrameRef(axis_range_max)

        # compute the range on the left/right side of the temporal cursor
        left = visi.frame_id - axis_range_min
        right = axis_range_max - visi.frame_id

        # compute the first frame and the last frame after zooming
        visi.first_frame = max(int(visi.frame_id - left * self.zoom_factor), 0)

        visi.last_frame = min(
            int(visi.frame_id + right * self.zoom_factor), visi.nframes
        )

        # update signals plots
        visi.updateSignalPlot()


class FullVisiWidget(LogoWidget):
    def callback(self, visi):
        """
        Callback method for zooming out to the full temporal range

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # update range: full file
        visi.first_frame = 0
        visi.last_frame = visi.nframes

        # update signal plots
        visi.updateSignalPlot()
