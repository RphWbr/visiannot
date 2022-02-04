# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber, Edouard Boustouler
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.VideoWidget`
"""

from os.path import splitext, basename
import pyqtgraph as pg
import numpy as np
from time import sleep
from ...tools.video_loader import transform_image
from ...tools.pyqt_overlayer import add_widget_to_layout


class VideoWidget(pg.PlotWidget):
    def __init__(self, visi_lay, widget_position, *args, **kwargs):
        """
        Subclass of **pyqtgraph.PlotWidget** for displaying a video

        The video data is not provided in the constructor, but with the method
        :meth:`.setImage`, then the method :meth:`.displayImage` displays the
        current frame. The method :meth:`.setAndDisplayImage` combines both.

        :param visi_lay: layout of the associated instance of
            :class:`.ViSiAnnoT`
        :type visi_lay: PyQt5.QtWidgets.QGridLayout
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param args: positional arguments of the method :meth:`.setWidgetTitle`
        :param kwargs: keyword arguments of the method :meth:`.setWidgetTitle`
        """

        # parent constructor
        pg.PlotWidget.__init__(self)
        self.setAspectLocked(True)
        self.setMenuEnabled(False)
        self.invertY(True)
        self.showAxis('left', show=False)
        self.showAxis('bottom', show=False)

        #: (*str*) Name of the video file without extension
        self.title = None
        self.setWidgetTitle(*args, **kwargs)

        #: (*int*) Index of the previously read frame
        self.previous_frame_id = None

        #: (*numpy array*) Current frame image
        self.image = None

        #: (*pyqtgraph.ImageItem*) Displayed image item
        self.img_item = pg.ImageItem(self.image)
        self.addItem(self.img_item)

        # add widget to the layout of the associated instance of ViSiAnnoT
        add_widget_to_layout(visi_lay, self, widget_position)


    def setImage(self, data_video, frame_id):
        """
        Reads video at the specified frame

        It sets the attributes :attr:`.previous_frame_id` and :attr:`.image`.

        :param data_video: video data to read
        :type data_video: cv2.VideoCapture
        :param frame_id: frame to read
        :type frame_id: int

        :returns: code (0 success, 1 pause, 2 error)
        :rtype: int
        """

        # check data video
        if data_video is not None:
            if self.previous_frame_id == frame_id - 1:
                pass

            elif self.previous_frame_id == frame_id:
                sleep(0.00001)

                return 1

            else:
                # set the video stream at the current frame
                data_video.set(1, frame_id)

            # read image
            ret, im = data_video.read()
            self.previous_frame_id = frame_id

        else:
            ret = False

        # check if reading is successful
        if ret:
            # cv2 returns BGR => converted to RGB
            # cv2 returns image with shape (height,width,3) => transposed to
            # (width, height, 3) for display
            self.image = transform_image(im)

            return 0

        else:
            # if no image read, returns black image
            self.image = np.zeros((100, 100, 3))

            return 2


    def displayImage(self):
        """
        Displays the current frame stored in :attr:`.image`

        It sets the attribute :attr:`.img_item`.
        """

        self.img_item.setImage(self.image)


    def setAndDisplayImage(self, *args):
        """
        Reads video at the specified frame and displays image

        It calls the methods :meth:`.setImage` and :meth:`.displayImage`.

        :param args: positional arguments of :meth:`.setImage`
        """

        self.setImage(*args)
        self.displayImage()


    def setWidgetTitle(self, video_path, **kwargs):
        """
        Sets the widget title with the file name without extension of the video

        :param video_path: path to the video file to read
        :type video_path: str
        :param kwargs: keyword arguments of the method
            :meth:`pyqtgraph.PlotWidget.setTitle`
        """

        self.title = splitext(basename(video_path))[0]
        self.setTitle(self.title, **kwargs)
