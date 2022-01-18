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
from h5py import File
from .ToolsAudio import getAudioWaveInfo, getDataAudio
from os import SEEK_END, SEEK_CUR
from warnings import catch_warnings, simplefilter


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

    :param path: typically ``__file__``
    :type path: str
    """

    if hasattr(sys, "_MEIPASS"):
        path_w = abspath(getattr(sys, "_MEIPASS"))

    else:
        path_w = dirname(realpath(path))

    return path_w


def convertIntervalsToTimeSeries(intervals, n_samples=0):
    """
    Converts intervals as 2D array to a time series of 0 and 1 (1D array)

    :param intervals: intervals in frame numbers, shape
        :math:`(n_{intervals}, 2)`
    :type intervals: numpy array or list
    :param n_samples: number of frames of the time series, default end frame of
        the last interval
    :type n_samples: int

    :returns: intervals as a time series, shape :math:`(n_{frames},)`
    :rtype: numpy array

    If the end time of an interval is -1 (second column of ``intervals``, then
    the end time is set to n_samples.

    Example::

        >>> a = np.array([[4, 5], [9, 12], [16, -1]])
        >>> convertIntervalsToTimeSeries(a, 20)
        array([0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 1., 1., 0., 0., 0., 0.,
               1., 1., 1., 1.])
    """

    if isinstance(intervals, np.ndarray):
        intervals = intervals.astype(int)

    if n_samples == 0:
        n_samples = intervals[-1, 1]
        if n_samples == -1:
            raise Exception("Intervals cannot be converted to time series")

    time_series = np.zeros((n_samples,))

    for interval in intervals:
        if interval[1] == -1:
            interval[1] = n_samples

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


def getDataIntervalAsTimeSeries(path, n_samples=0, key="", slicing=()):
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
    :param n_samples: number of samples of the time series, see
        :func:`.convertIntervalsToTimeSeries`
    :type n_samples: int
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: data[start:]
        - ``(start, stop)``: data[start:stop]
    :type slicing: tuple

    :returns: numpy array of shape :math:`(n_{samples},)` with intervals as a
        time series of 0 and 1
    :rtype: numpy array
    """

    if isfile(path):
        data_array = np.squeeze(getDataGeneric(path, key=key, ndmin=2))

        if data_array.ndim == 2:
            data_array[np.where(data_array < 0)] = 0
            data_array = convertIntervalsToTimeSeries(
                data_array, n_samples=n_samples
            )

    else:
        print("Time series full of NaN because file not found: %s" % path)
        data_array = np.nan * np.ones((n_samples,))

    if len(slicing) == 1:
        data_array = data_array[slicing[0]:]

    elif len(slicing) == 2:
        data_array = data_array[slicing[0]:slicing[1]]

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


def getDataDuration(
    path, freq, key='', flag_interval=False, **kwargs
):
    """
    Gets the ending date-time of a data file

    The beginning date-time must be in the path of the data files.

    :param path: path to the data file
    :type path: list
    :param freq: data frequency, set to ``0`` if signal not regularly sampled
    :type freq: float
    :param key: key to access the data (in case of .mat or .h5)
    :type key: str
    :param flag_interval: specify if data is intervals
    :type flag_interval: bool
    :param kwargs: keyword arguments of :func:`.getNbSamplesGeneric`

    :returns: duration of the data file in seconds
    :rtype: int
    """

    # check if interval data
    if flag_interval:
        # load intervals
        data = getDataInterval(path, key=key)

        if data.size > 0:
            # get ending frame of last interval
            last_frame = data[-1, -1]

            # get duration in seconds
            duration = last_frame / freq

        else:
            duration = 0

    else:
        # check if signal not regularly sampled
        if freq == 0:
            # get last sample of the data file
            last_sample = getLastSampleGeneric(path, key=key)

            if last_sample is not None:
                # get duration in seconds
                duration = last_sample[0] / 1000

            else:
                duration = 0

        else:
            # get number of samples
            nb_samples = getNbSamplesGeneric(path, key, **kwargs)

            # get duration in seconds
            duration = nb_samples / freq

    return duration


def getNbSamplesGeneric(path, key='', **kwargs):
    ext = path.split('.')[-1]

    if ext == "mat" or ext == "h5":
        with File(path, 'r') as f:
            nframes = f[key].shape[0]

    elif ext == "txt":
        with open(path, 'r') as f:
            nframes = len(f.readlines())

    elif ext == "wav":
        _, _, nframes = getAudioWaveInfo(path, **kwargs)

    else:
        raise Exception("Data format not supported: %s" % ext)

    return nframes


def getLastSampleGeneric(path, key=''):
    ext = path.split('.')[-1]

    if ext == "mat" or ext == "h5":
        with File(path, 'r') as f:
            dataset = f[key]

            # check if empty dataset
            if dataset.shape[0] == 0:
                last_sample = None

            else:
                last_sample = dataset[-1]

    elif ext == "txt":
        with open(path, 'rb') as f:
            try:
                f.seek(-2, SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, SEEK_CUR)

            # only one line in file
            except OSError:
                f.seek(0)

            last_line = f.readline().decode()

            if last_line == '':
                last_sample = None

    else:
        raise Exception("Data format not supported: %s" % ext)

    if last_sample is not None:
        try:
            last_sample = float(last_sample)

        except Exception:
            pass

    return last_sample


def getDataGeneric(path, key='', **kwargs):
    """
    Loads data from a file with format mat, h5, txt or wav

    :param path: path to the data file
    :type path: str
       string containing the path to the data
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str
    :param kwargs: keyword arguments of :func:`.getDataMat`,
        :func:`.getDataH5`, :func:`.getDataTxt` or
        :func:`.ToolsAudio.getDataAudio`, depending on file format

    :returns: data
    :rtype: numpy array

    It raises an exception if the format is not supported.
    """

    ext = path.split('.')[-1]

    if ext == "mat":
        data = getDataMat(path, key, **kwargs)

    elif ext == "h5":
        data = getDataH5(path, key, **kwargs)

    elif ext == "txt":
        data = getDataTxt(path, **kwargs)

    elif ext == "wav":
        _, data, _ = getDataAudio(path, **kwargs)

    else:
        raise Exception("Data format not supported: %s" % ext)

    return data


def getDataTxt(path, slicing=(), **kwargs):
    """
    Loads data from a txt file

    :param path: path to the data file
    :type path: str
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: data[start:]
        - ``(start, stop)``: data[start:stop]
    :type slicing: tuple
    :param kwargs: keyword arguments of numpy.loadtxt (in case of txt file)

    :returns: data
    :rtype: numpy array
    """

    # disable warnings
    with catch_warnings():
        simplefilter("ignore")
        data = np.loadtxt(path, **kwargs)

    if len(slicing) == 1:
        data = data[slicing[0]:]

    elif len(slicing) == 2:
        data = data[slicing[0]:slicing[1]]

    return data


def getDataMat(path, key, slicing=()):
    """
    Loads data from a mat file

    :param path: path to the data file
    :type path: str
    :param key: key to access the data
    :type key: str
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: data[start:]
        - ``(start, stop)``: data[start:stop]
    :type slicing: tuple

    :returns: data
    :rtype: numpy array
    """

    # try opening with loadmat, otherwise with h5py
    try:
        data = loadmat(path)[key]

        if len(slicing) == 1:
            data = data[slicing[0]:]

        elif len(slicing) == 2:
            data = data[slicing[0]:slicing[1]]

    except Exception:
        data = getDataH5(path, key, slicing=slicing)

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


def getDataH5(path, key, slicing=()):
    """
    Reads a dataset in a H5 file

    :param path: path to the file
    :type path: str
    :param key: path to the H5 dataset to load
    :type key: str
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: data[start:]
        - ``(start, stop)``: data[start:stop]
    :type slicing: tuple

    :returns: dataset or ``None`` if not found
    :rtype: numpy array
    """

    with File(path, 'r') as f:
        if key in f:
            if len(slicing) == 1:
                output = f[key][slicing[0]:]

            elif len(slicing) == 2:
                output = f[key][slicing[0]:slicing[1]]

            else:
                output = f[key][()]

        else:
            output = None

    return output
