# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for loading and saving data files
"""


import numpy as np
import sys
from os.path import isfile, split, abspath, dirname, realpath
from scipy.io import loadmat
from h5py import File, Dataset
from .ToolsAudio import getDataAudio


def getWorkingDirectory(path):
    """
    Gets working directory when ViSiAnnoT is launched, which depends on wether
    it is launched as a Python script or an executable (generated with
    PyInstaller)

    Typically, ``path`` is the path to a Python module of **visiannot** that is
    being executed.

    In case it is launched as a Python script, it returns the absolute path to
    the directory containing the module.

    In case it is launched as an executable generated with PyInstaller, it
    returns the path to the temporary directory created by PyInstaller where
    are putted source code and related data files.

    :param path: typically ``__file``
    :type path: str
    """

    if hasattr(sys, "_MEIPASS"):
        path_w = abspath(getattr(sys, "_MEIPASS"))

    else:
        path_w = dirname(realpath(path))

    return path_w


def convertIntervalsToTimeSeries(intervals, nframes):
    """
    Converts intervals as 2D array to a time series of 0 and 1 (1D array)

    :param intervals: intervals in frame numbers, shape
        :math:`(n_{intervals}, 2)`
    :type intervals: numpy array or list
    :param nframes: number of frames of the time series

    :returns: intervals as a time series, shape :math:`(n_{frames},)`
    :rtype: numpy array

    If the end time of an interval is -1 (second column of ``intervals``, then
    the end time is set to nframes.

    Example::
        >>> a = np.array([[4, 5], [9, 12], [16, -1]])
        >>> convertIntervalsToTimeSeries(a, 20)
        array([0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 1., 1., 0., 0., 0., 0.,
               1., 1., 1., 1.])
    """

    if isinstance(intervals, np.ndarray):
        intervals = intervals.astype(int)
    time_series = np.zeros((nframes,))
    for interval in intervals:
        if interval[1] == -1:
            interval[1] = nframes
        time_series[interval[0]:interval[1]] = 1

    return time_series


def convertTimeSeriesToIntervals(data, value):
    """
    Gets the intervals of a 1D signal with a specific value

    :param data: 1D array
    :type data: numpy array
    :param value: value that defines the intervals to retrieve from ``data``

    :return: 2D array with indexes of intervals (ending index is not included
        in the interval, as with ``range`` in Python)
    :rtype: numpy array

    Example::
        >>> a = np.array([0, 0, 0, 0, 5, 1, 1, 1, 1, 5, 5, 5, 0, 0, 0, 0])
        >>> convertTimeSeriesToIntervals(a,0)
        array([[ 0,  4],
               [12, 16]])
        >>> convertTimeSeriesToIntervals(a,1)
        array([[5, 9]])
        >>> convertTimeSeriesToIntervals(a,5)
        array([[ 4,  5],
               [ 9, 12]])
    """

    if np.isnan(value):
        inds = np.where(np.isnan(data))[0]

    else:
        inds = np.where(data == value)[0]

    if inds.shape[0] == 0:
        return np.empty((0, 2), dtype=int)

    else:
        inds_inds_diff = np.where(np.diff(inds) > 1)[0]

        start_inds = np.hstack((inds[0:1], inds[inds_inds_diff + 1]))

        end_inds = np.hstack(
            (inds[inds_inds_diff] + 1, np.array([inds[-1] + 1]))
        )

        return np.vstack((start_inds, end_inds)).T


def getDataInterval(path, key=""):
    """
    Loads file containing temporal intervals, output shape
    :math:`(n_{intervals},2)`

    The file format must be supported by :func:`.ToolsData.getDataGeneric`.

    The data can be stored in two ways:

    - shape :math:`(n_{intervals},2)`, where each line contains the start frame
      and end frame of an interval, then no conversion is needed
    - shape :math:`(n_{samples},)` with 0 and 1, then it is converted to shape
      :math:`(n_{intervals},2)`

    :param path: path to the data file
    :type path: str
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str

    :returns: numpy array of shape :math:`(n_{intervals},2)` with intervals in
        frames number
    :rtype: numpy array
    """

    if isfile(path):
        data_array = np.squeeze(getDataGeneric(path, key=key, ndmin=2))
        if data_array.ndim == 1:
            data_array = convertTimeSeriesToIntervals(data_array, 1)
        elif data_array.shape[0] == 0:
            data_array = np.empty((0, 2))
    else:
        data_array = np.empty((0, 2))

    return data_array


def getDataIntervalAsTimeSeries(path, n_samples, key=""):
    """
    Loads file containing temporal intervals, output shape
    :math:`(n_{samples},)`

    The data can be stored in two ways:

    - shape :math:`(n_{intervals},2)`, where each line contains the start frame
      and end frame of an interval, then it is converted to shape
      :math:`(n_{samples},)`, so the number of frames must be specified
      (allowed formats: txt, mat, h5)
    - shape :math:`(n_{samples},)` with 0 and 1, then no conversion is needed
      (allowed formats: mat, h5)

    :param path: path to the data file
    :type path: str
    :param n_samples: number of samples of the time series
    :type n_samples: int
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str

    :returns: numpy array of shape :math:`(n_{samples},)` with intervals as a
        time series of 0 and 1
    :rtype: numpy array
    """

    if isfile(path):
        data_array = getDataGeneric(path, key=key, ndmin=2)
        if data_array.ndim == 2:
            data_array[np.where(data_array < 0)] = 0
            data_array = convertIntervalsToTimeSeries(data_array, n_samples)

    else:
        print("Time series full of NaN because file not found: %s" % path)
        data_array = np.nan * np.ones((n_samples,))

    return data_array


def getTxtLines(path):
    """
    Loads a file as a list of lines

    :param path: path to the text file
    :type pat: str

    :returns: list of strings with the lines of the file
    :rtype: list
    """

    with open(path, 'r') as f:
        lines = f.readlines()

    return lines


def getDataGeneric(path, key="", **kwargs):
    """
    Loads data from a file with format mat, h5, txt or wav

    :param path: path to the data file
    :type path: str
       string containing the path to the data
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str
    :param kwargs: keyword arguments of numpy.loadtxt (in case of txt file) or
        :func:`.ToolsAudio.getDataAudio` (in case of wav file)

    :returns: data
    :rtype: numpy array

    It raises an exception if the format is not supported.
    """

    ext = path.split('.')[-1]

    if ext == "mat":
        data = getDataMat(path, key)

    elif ext == "h5":
        data = getDataH5(path, key)

    elif ext == "txt":
        # disable warnings
        from warnings import catch_warnings, simplefilter
        with catch_warnings():
            simplefilter("ignore")
            data = np.loadtxt(path, **kwargs)

    elif ext == "wav":
        _, data, _ = getDataAudio(path, **kwargs)

    else:
        raise Exception("Data format not supported: %s" % ext)

    return data


def getDataMat(path, key):
    """
    Loads data from a mat file

    :param path: path to the data file
    :type path: str
    :param key: key to access the data
    :type key: str

    :returns: data
    :rtype: numpy array
    """

    # try opening with loadmat, otherwise with h5py
    try:
        data = loadmat(path)[key]

    except Exception:
        data = getDataH5(path, key)

    return np.squeeze(data)


def getAttributeH5(path, key_path):
    """
    Gets an attribute in a h5 file

    :param path: path to the file
    :type path: str
    :param key_path: key path to the attribute in the file
    :type key_path: str

    :returns: attribute
    """

    dataset_path, key = split(key_path)

    with File(path, 'r') as f:
        if dataset_path != "":
            attr = f[dataset_path].attrs[key]

        else:
            attr = f.attrs[key]

    return attr


def getAttributeGeneric(path, key):
    """
    Gets an attribute in a mat or h5 file

    :param path: path to the file
    :type path: str
    :param key_path: key path to the attribute in the file
    :type key_path: str

    If the file is not mat or h5, it returns key.

    :returns: attribute
    """

    ext = path.split('.')[-1]

    if ext == "mat":
        attr = getDataMat(path, key)

    elif ext == "h5":
        attr = getAttributeH5(path, key)

    else:
        attr = key

    return attr


def recursiveReadH5(parent_item):
    """
    Recursive function to read data from a h5py file object while preserving
    nested architecture

    It reaches the last group level recursively.

    If the parent item is a H5 dataset, then the function returns a numpy
    array. Otherwise it returns a dictionary, where the key corresponds to one
    H5 group and the value correponds to the H5 group content (may it be a
    nested group, a numpy array in case of H5 dataset or a string/int/float in
    case of H5 attribute). The attributes of a H5 dataset are not retrieved,
    it only works for attributes of a H5 group.

    :param parent_item: h5py file object

    :returns: all data contained in ``parent_item``
    :rtype: dict or numpy array
    """

    # check if parent item is a dataset
    if isinstance(parent_item, Dataset):
        # output is a numpy array
        output = parent_item[()]

    else:
        # output is a dictionary
        output = {}

        # get attributes
        for key, value in parent_item.attrs.items():
            output[key] = value

        # loop on items of the next level
        for key, item in parent_item.items():
            # recursive call
            output[key] = recursiveReadH5(item)

    return output


def getDataH5(path, root_path='/'):
    """
    Reads the whole content of a H5 file or a specific dataset/group

    It calls the recursive function :func:`.recursiveReadH5`.

    :param path: path to the file
    :type path: str
    :param root_path: path to the H5 group or H5 dataset where to start
        retrieving data, default ``'/'`` (file root)
    :type key_path: str

    :returns: three options:

    - (*dict*) -- in case ``root_path`` points to a H5 group, all data
      contained in the H5 group
    - (*numpy array*) -- in case ``root_path`` points to a H5 dataset
    - ``None`` -- in case ``root_path`` points to a location that is not in the
      file
    """

    with File(path, 'r') as f:
        if root_path in f:
            output = recursiveReadH5(f[root_path])
        else:
            output = None

    return output
