# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for loading ViSiAnnoT event annotation files
"""


import numpy as np
from os.path import isfile
from .ToolsData import convertIntervalsToTimeSeries


def readAnnotation(path, delimiter=" - "):
    """
    Reads an annotation file

    :param path: path of the annotation file
    :type path: str

    :param delimiter: delimiter used to split each line of the annotation file
        in columns
    :type delimiter: str

    :returns: array of shape :math:`(n,2)` where the first column is the start
        time of the annotation and the second column is the end time of the
        annotation, or shape :math:`(0,2)` if empty annotation
    :rtype: numpy array
    """

    annot_array = np.loadtxt(path, dtype=str, delimiter=delimiter, ndmin=2)
    if annot_array.shape[0] == 0:
        annot_array = np.empty((0, 2), dtype=str)

    return annot_array


def addElement(dic, key, element):
    """
    Appends an element to a list in a dictionary where each value is a list

    :param dic: input dictionary
    :type dic: dict
    :param key: key to the list to append
    :type key: any type that the key might be
    :param element: element to append

    If ``key`` does not exist in ``dic``, then it is created and the value is
    initialized with ``[element]``.
    """

    if key not in dic.keys():
        dic[key] = []

    dic[key].append(element)


def readAnnotFrames(path, nb_files=-1, delimiter=" - "):
    """
    Reads an annotation file in format vid-id_frame-id as a list of lists of
    intervals in frame number

    Each element of the output list corresponds to one video (or signal) file.

    This element is a list of lists with the annotation intervals in frame
    number contained in this file (it can be an empty list if there are no
    annotations in this file).

    If an annotation interval spans several files, then the last end frame is
    set to -1 to specify that the annotation interval continues after the file.

    :param path: path to the annotation file in the format vid-id_frame-id
    :type path: str

    :param nb_files: number of files in the annotated recording,
        set to ``-1`` to ignore
    :type nb_files: int

    :param delimiter: delimiter used to split each line of the annotation file
        in columns
    :type delimiter: str

    :returns: list of lists of lists or empty list if file does not exist
    :rtype: list

    Example::

        nb_files = 12

        Annotation file
        1_40 - 1_150
        1_151 - 2_300
        5_2 - 5_230
        5_250 - 5_300
        5_305 - 5_600
        6_10 - 8_50

        Output list
        [[],
         [[40, 150], [151, -1]],
         [[0, 300]],
         [],
         [],
         [[2, 230], [250, 300], [305, 600]],
         [[10, -1]],
         [[0, -1]],
         [[0, 50]],
         [],
         [],
         []]
    """

    # initialize output dictionary
    result_dict = {}

    # check if file exists
    if isfile(path):
        # read file line-wise
        annot_array = readAnnotation(path, delimiter=delimiter)

        # loop on annotation lines
        for annot_0, annot_1 in annot_array:
            # read line
            vid_0 = int(annot_0.split("_")[0])
            frame_0 = int(annot_0.split("_")[1])
            vid_1 = int(annot_1.split("_")[0])
            frame_1 = int(annot_1.split("_")[1])

            # check if annotation spans several
            if vid_1 > vid_0:
                addElement(result_dict, vid_0, [frame_0, -1])

                for vid_id in range(vid_0 + 1, vid_1):
                    addElement(result_dict, vid_id, [0, -1])

                addElement(result_dict, vid_1, [0, frame_1])

            else:
                addElement(result_dict, vid_0, [frame_0, frame_1])

    # get maximum video id
    if len(result_dict) > 0:
        max_vid_id = max(result_dict.keys())
    else:
        max_vid_id = -1

    # convert output dictionary to list
    result_list = []
    for vid_id in range(max_vid_id + 1):
        if vid_id in result_dict.keys():
            result_list.append(result_dict[vid_id])
        else:
            result_list.append([])

    # check number of files in the annotated recording
    if nb_files > 0:
        result_list += [[] for i in range(nb_files - len(result_list))]

    return result_list


def convertAnnotArray(
    annot_path, nb_frames_list, fps, ref_fps=25, flag_invert=False
):
    """
    Loads an annotation file as a time series of 0 and 1

    :param annot_path: path to the annotation file
    :type annot_path: str
    :param nb_frames_list: list with number of frames in each file of the
        annotated recording
    :type nb_frames_list: list
    :param fps: output frequency, must be below or equal to ``ref_fps``
    :type fps: int or float
    :param ref_fps: frequency of the annotated signal
    :type ref_fps: int or float
    :param flag_invert: Specify if 0 and 1 must be inverted in the
        output signal
    :type flag_invert: bool

    :returns: 1D numpy array with the annotation as a time series of 0 and 1
    :rtype: numpy array
    """

    # compute factor between predictions frame rate and video frame rate
    factor = int(ref_fps / fps)

    # initialize annotation array
    output_array = np.array([])

    # get annotation intervals
    annot_list_list = readAnnotFrames(annot_path, nb_files=len(nb_frames_list))

    # loop on intervals
    for inter_list, nb_frames in zip(annot_list_list, nb_frames_list):
        # get annotation as a time series
        annot = convertIntervalsToTimeSeries(inter_list, nb_frames)

        # downsample to output fps
        output_array = np.concatenate((output_array, annot[::factor]))

    # invert 0 and 1
    if flag_invert:
        output_array = -output_array + 1

    return output_array
