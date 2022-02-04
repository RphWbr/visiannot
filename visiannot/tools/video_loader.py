# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber, Edouard Boustouler
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for loading image and video files
"""


from cv2 import imread, VideoCapture
import numpy as np
from os.path import isfile
from tinytag import TinyTag


def transform_image(im, RGB_combination="BGR", flag_transpose=True):
    """
    Changes the order of an image channels in order to get RGB color,
    may reverse the first and second axis (in order to transform shape
    :math:`(width, height, 3)` to :math:`(height, width, 3)`).

    Particularly useful to display images retrieved with openCV.
    Indeed, openCV returns images of shape :math:`(width, height, 3)` with BGR
    color.

    :param im: image array of shape :math:`(width, height, 3)`, where third
        axis is a 3-channel color
    :type im: numpy array
    :param RGB_combination: order of the color channel
        (as with openCV)
    :type RGB_combination: str
    :param flag_transpose: specify if first axis and second axis must be
        reversed
    :type flag_transpose: bool

    :returns: image array of shape :math:`(height, width, 3)` where third axis
        is RGB color
    :rtype: numpy array

    If ``im`` is not a numpy array or is not a 3D array, then the output is
    ``im``.
    """

    if not isinstance(im, np.ndarray) or im.ndim != 3:
        return im

    else:
        if RGB_combination == "RGB":
            inds = [0, 1, 2]
        elif RGB_combination == "RBG":
            inds = [0, 2, 1]
        elif RGB_combination == "GRB":
            inds = [1, 0, 2]
        elif RGB_combination == "GBR":
            inds = [1, 2, 0]
        elif RGB_combination == "BRG":
            inds = [2, 0, 1]
        elif RGB_combination == "BGR":
            inds = [2, 1, 0]

        im_out = im[:, :, inds]
        if flag_transpose:
            im_out = np.transpose(im_out, axes=(1, 0, 2))

        return im_out


def read_image(path):
    """
    Reads an image with openCV

    :param path: path to the image file
    :type path: str

    :returns: RGB image array of shape :math:`(width, height, 3)`
    :rtype: numpy array
    """

    im = imread(path)

    # because of opencv, convert BGR to RGB and invert width/height
    return transform_image(im)


def get_data_video(path):
    """
    Loads video data with openCV

    :param path: path to the video file
    :type path: str

    :returns:
        - **data_video** (*cv2.VideoCapture*) (``None`` if video file does not
          exist)
        - **nframes** (*int*) -- number of frames in the video (0 if video file
          does not exist)
        - **fps** (*int* or *float*) - frame rate of the video (-1 if video
          file does not exist)
    """

    # check if video file exists
    if isfile(path):
        # get video data
        data_video = VideoCapture(path)

        # get number of frames and fps
        nframes = int(data_video.get(7))
        fps = data_video.get(5)

        return data_video, nframes, fps

    else:
        return None, 0, -1


def get_duration_video(path):
    """
    Gets duration of a video file

    :param path: path to the video file
    :type path: str

    :returns: video file duration in seconds
    :rtype: float
    """

    # check if video file exists
    if isfile(path):
        duration = TinyTag.get(path).duration
        if duration is None:
            raise Warning("Empty metadata for video %s" % path)

        return duration

    else:
        return 0
