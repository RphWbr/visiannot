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

import pyqtgraph as pg
import numpy as np
from time import sleep
from ...tools.video_loader import transform_image
from ...tools.pyqt_overlayer import add_widget_to_layout


class VideoWidget(pg.PlotWidget):
    def __init__(self, lay, widget_position, data_video):
        """
        Subclass of **pyqtgraph.PlotWidget** for displaying a video

        :param lay: layout where the video widget must be displayed
        :type lay: PyQt5.QtWidgets.QGridLayout
        :param widget_position: position of the widget in the layout
        :type widget_position: tuple or list
        :param data_video: see value of :attr:`.ViSiAnnoT.video_data_dict`
        :type data_video: tuple
        """

        # parent constructor
        pg.PlotWidget.__init__(self)
        self.setAspectLocked(True)
        self.setMenuEnabled(False)
        self.invertY(True)
        self.showAxis('left', show=False)
        self.showAxis('bottom', show=False)

        #: (*cv2.VideoCapture*) Video data currently being played
        self.data_video = None

        #: (*str*) Basename of the video currently being played
        self.name = None

        #: (*tuple*) Information for video synchronization in case of long
        #: recording (ignored otherwise), 3 elements:
        #:
        #:  - (*list*) Instances of **cv2.VideoCapture** containing the
        #:    video data spanning the current file in the long recording
        #:  - (*list*) Names of the video files spanning the current file
        #:    in the long recording (same ordering than list of
        #:    **cv2.VideoCapture** instances)
        #:  - (*numpy array*) Array of shape *(n, 2)* (*n* is equal to the
        #:    length of the list of video data), each row corresponds to an
        #:    element of the list of **cv2.VideoCapture** instances (same
        #:    ordering) and contains the bounding frames that the video spans
        #:    in the current file in the long recording
        self.data_video_synchro = None

        #: (*float*) Temporal offset in frames number to apply to the current
        #: frame to read in case of long recording (ignored otherwise)
        self.offset_synchro = None

        self.setDataVideo(data_video)

        #: (*int*) Index of the previously read frame
        self.previous_frame_id = None

        #: (*numpy array*) Current frame image
        self.image = None

        #: (*pyqtgraph.ImageItem*) Displayed image item
        self.img_item = pg.ImageItem(self.image)
        self.addItem(self.img_item)

        # add widget to the layout of the associated instance of ViSiAnnoT
        add_widget_to_layout(lay, self, widget_position)


    def setDataVideo(self, data_video):
        """
        Sets the attributes with video data

        In case of long recording, it sets the attributes
        :attr:`.data_video_synchro` and resets the attributes
        :attr:`.data_video`, :attr:`.offset_synchro` and :attr:`.name` to
        ``None``. Otherwise, it only sets the attributes :attr:`.data_video`
        and :attr:`.name`.

        :param data_video: see third positional argument of the constructor of
            :class:`.VideoWidget`
        :type data_video: tuple
        """


        if len(data_video) == 3:
            self.data_video_synchro = data_video
            self.data_video = None
            self.name = None
            self.offset_synchro = None

        else:
            self.data_video, self.name = data_video


    def setSynchro(self, frame_id):
        """
        Finds the video file to read and the temporal offset to apply when
        reading frames

        It sets the attributes :attr:`.data_video`, :attr:`.name` and
        :attr:`.offset_synchro`.

        :param frame_id: next frame to read
        :type frame_id: int
        """

        data_video_list, path_list, frame_array = self.data_video_synchro

        # get indexes of videos containing the current frame
        video_inds = np.intersect1d(
            np.where(frame_array[:, 0] <= frame_id)[0],
            np.where(frame_array[:, 1] > frame_id)[0]
        )

        if len(video_inds) > 0:
            # get index of video containing the current frame
            video_ind = video_inds[0]

            # get temporal offset
            self.offset_synchro = frame_array[video_ind, 0]

            # get new video data if necessary
            if self.data_video != data_video_list[video_ind]:
                self.data_video = data_video_list[video_ind]
                self.name = path_list[video_ind]

        else:
            self.data_video = None
            self.name = None
            self.offset_synchro = None


    def setImage(self, frame_id):
        """
        Reads video at the specified frame

        It sets the attributes :attr:`.previous_frame_id` and :attr:`.image`.

        :param frame_id: frame to read
        :type frame_id: int

        :returns: code (0 success, 1 pause, 2 error)
        :rtype: int
        """

        # check if video data from a long recording
        if self.data_video_synchro is not None:
            # check if video data already found
            if self.data_video is not None:
                # check if frame ID outside video
                if frame_id - self.offset_synchro >= self.data_video.get(7) \
                        or frame_id - self.offset_synchro < 0:
                    # find new video data
                    self.setSynchro(frame_id)

            else:
                self.setSynchro(frame_id)

        # check data video
        if self.data_video is not None:
            # consecutive frame => no need to set frame
            if self.previous_frame_id == frame_id - 1:
                pass

            # pause
            elif self.previous_frame_id == frame_id:
                sleep(0.00001)

                return 1

            elif self.data_video_synchro is not None:
                # set the video stream at the current frame
                self.data_video.set(1, frame_id - self.offset_synchro)

            else:
                # set the video stream at the current frame
                self.data_video.set(1, frame_id)

            # read image
            ret, im = self.data_video.read()
                
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
