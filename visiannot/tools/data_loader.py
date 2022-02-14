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
from os.path import isfile, split, abspath, dirname, realpath, splitext
from scipy.io import loadmat
from h5py import File, Dataset
from .audio_loader import get_audio_wave_info, get_data_audio
from os import SEEK_END, SEEK_CUR
from warnings import catch_warnings, simplefilter


def get_working_directory(path):
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


def convert_intervals_to_time_series(intervals, n_samples=0):
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
        >>> convert_intervals_to_time_series(a, 20)
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


def convert_time_series_to_intervals(data, value):
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
        >>> convert_time_series_to_intervals(a,0)
        array([[ 0,  4],
               [12, 16]])
        >>> convert_time_series_to_intervals(a,1)
        array([[5, 9]])
        >>> convert_time_series_to_intervals(a,5)
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


def get_data_interval(path, key=""):
    """
    Loads file containing temporal intervals, output shape
    :math:`(n_{intervals},2)`

    The file format must be supported by :func:`.get_data_generic`.

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

    data_array = get_data_generic(path, key=key)

    # check if intervals as time series
    if data_array.ndim == 1:
        # if only 2 samples, then it is considered as a single interval =>
        # shape (1, 2)
        if len(data_array) == 2:
            data_array = data_array[None, :]

        else:
            data_array = convert_time_series_to_intervals(data_array, 1)

    elif data_array.shape[0] == 0:
        data_array = np.empty((0, 2))

    return data_array


def get_data_interval_as_time_series(path, n_samples=0, key="", **kwargs):
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
        :func:`.convert_intervals_to_time_series`
    :type n_samples: int
    :param key: key to access the data in case of mat or h5 file, for txt file
        it is ignored
    :type key: str
    :param kwargs: keyword arguments of :func:`.slice_dataset`

    :returns: numpy array of shape :math:`(n_{samples},)` with intervals as a
        time series of 0 and 1
    :rtype: numpy array
    """

    if isfile(path):
        data_array = np.squeeze(get_data_generic(path, key=key, ndmin=2))

        if data_array.ndim == 2:
            data_array[np.where(data_array < 0)] = 0
            data_array = convert_intervals_to_time_series(
                data_array, n_samples=n_samples
            )

    else:
        print("Time series full of NaN because file not found: %s" % path)
        data_array = np.nan * np.ones((n_samples,))

    data_array = slice_dataset(data_array, **kwargs)

    return data_array


def get_txt_lines(path):
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


def get_data_duration(
    path, freq, key='', flag_interval=False, **kwargs
):
    """
    Gets the ending date-time of a data file (.mat, .h5 or .txt)

    It raises an exception if the format is not supported.

    The beginning date-time must be in the path of the data files.

    :param path: path to the data file
    :type path: list
    :param freq: data frequency, set to ``0`` if signal not regularly sampled
    :type freq: float
    :param key: key to access the data (in case of .mat or .h5)
    :type key: str
    :param flag_interval: specify if data is intervals
    :type flag_interval: bool
    :param kwargs: keyword arguments of :func:`.get_nb_samples_generic`

    :returns: duration of the data file in seconds
    :rtype: int
    """

    # clean key (in case a specific column is required when loading data)
    if " - " in key:
        key = key.split(" - ")[0]

    # check if interval data
    if flag_interval:
        # load intervals
        data = get_data_interval(path, key=key)

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
            last_sample = get_last_sample_generic(path, key=key)

            if last_sample is not None:
                # get duration in seconds
                duration = last_sample[0] / 1000

            else:
                duration = 0

        else:
            # get number of samples
            nb_samples = get_nb_samples_generic(path, key, **kwargs)

            # get duration in seconds
            duration = nb_samples / freq

    return duration


def get_nb_samples_generic(path, key='', **kwargs):
    """
    Gets number of samples in a data file (.mat, .h5 or .txt)

    It raises an exception if the format is not supported.

    :param path: path to the data file
    :type path: list
    :param key: key to access the data (in case of .mat or .h5)
    :type key: str

    :returns: number of samples
    :rtype: int
    """

    _, ext = splitext(path)

    if ext == ".h5":
        with File(path, 'r') as f:
            nb_samples = f[key].shape[0]

    elif ext == ".mat":
        with File(path, 'r') as f:
            shape = f[key].shape

            if len(shape) == 2:
                nb_samples = shape[1]

            else:
                nb_samples = shape[0]

    elif ext == ".txt":
        with open(path, 'r') as f:
            nb_samples = len(f.readlines())

    elif ext == ".wav":
        _, _, nb_samples = get_audio_wave_info(path, **kwargs)

    else:
        raise Exception("Data format not supported: %s" % ext)

    return nb_samples


def get_last_sample_generic(path, key=''):
    """
    Gets the last sample in a data file (.mat, .h5 or .txt)

    It raises an exception if the format is not supported.

    :param path: path to the data file
    :type path: list
    :param key: key to access the data (in case of .mat or .h5)
    :type key: str

    :returns: last sample
    :rtype: float or str
    """

    _, ext = splitext(path)

    if ext == ".mat" or ext == ".h5":
        with File(path, 'r') as f:
            dataset = f[key]

            # check if empty dataset
            if dataset.shape[0] == 0:
                last_sample = None

            else:
                last_sample = dataset[-1]

    elif ext == ".txt":
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


def get_data_generic(path, key='', **kwargs):
    """
    Loads data from a file (.h5, .mat or .txt)

    It raises an exception if the format is not supported.

    :param path: path to the data file
    :type path: str
       string containing the path to the data
    :param key: key to access the data (in case of .mat or .h5)
    :type key: str
    :param kwargs: keyword arguments of :func:`.get_data_mat`,
        :func:`.get_data_h5`, :func:`.get_data_txt` or
        :func:`.audio.get_data_audio`, depending on file format

    :returns: data
    :rtype: numpy array
    """

    _, ext = splitext(path)

    if ext == ".mat":
        data = get_data_mat(path, key, **kwargs)

    elif ext == ".h5":
        data = get_data_h5(path, key, **kwargs)

    elif ext == ".txt":
        data = get_data_txt(path, **kwargs)

    elif ext == ".wav":
        _, data, _ = get_data_audio(path, **kwargs)

    else:
        raise Exception("Data format not supported: %s" % ext)

    return data


def get_data_txt(path, slicing=(), **kwargs):
    """
    Loads data from a .txt file

    :param path: path to the data file
    :type path: str
    :param slicing: see keyword argument of :func:`.slice_dataset`
    :type slicing: tuple
    :param kwargs: keyword arguments of numpy.loadtxt

    :returns: data
    :rtype: numpy array
    """

    # disable warnings
    with catch_warnings():
        simplefilter("ignore")
        data = np.loadtxt(path, **kwargs)

    data = slice_dataset(data, slicing=slicing)

    return data


def get_data_mat(path, key, **kwargs):
    """
    Loads data from a .mat file

    :param path: path to the data file
    :type path: str
    :param key: key to access the data
    :type key: str
    :param kwargs: keyword arguments of :func:`.slice_dataset`

    :returns: data
    :rtype: numpy array
    """

    # try opening with loadmat, otherwise with h5py
    try:
        data = loadmat(path)[key]
        data = slice_dataset(data, **kwargs)

    except Exception:
        data = get_data_h5(path, key, **kwargs)

    return np.squeeze(data)


def get_attribute_h5(path, key_path):
    """
    Gets an attribute in a .h5 file

    :param path: path to the file
    :type path: str
    :param key_path: path to the attribute in the file
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


def get_attribute_generic(path, key):
    """
    Gets an attribute in a .mat or .h5 file

    :param path: path to the file
    :type path: str
    :param key_path: path to the attribute in the file
    :type key_path: str

    :returns: attribute (if the file is not .mat or .h5, it returns ``key``)
    """

    _, ext = splitext(path)

    if ext == ".mat":
        attr = get_data_mat(path, key)

    elif ext == ".h5":
        attr = get_attribute_h5(path, key)

    else:
        attr = key

    return attr


def get_data_h5(path, key, **kwargs):
    """
    Reads a dataset in a .h5 file

    :param path: path to the file
    :type path: str
    :param key: path to the H5 dataset to load
    :type key: str
    :param kwargs: keyword arguments of :func:`.slice_dataset`

    :returns: dataset
    :rtype: numpy array
    """

    with File(path, 'r') as f:
        # check if column index specified in key
        if ' - ' in key:
            key, col_ind = key.split(' - ')

            # check if column index specified by name
            if isinstance(col_ind, str) and "columns" in f[key].attrs:
                # get columns description
                col_desc = f[key].attrs["columns"].split(', ')

                # get column index
                col_ind = col_desc.index(col_ind)

            else:
                col_ind = int(col_ind)

        else:
            col_ind = None

        dataset = slice_dataset(f[key], **kwargs)

        # check if getting a specific column
        if col_ind is not None and dataset.ndim > 1:
            dataset = dataset[:, [0, col_ind]]

        return dataset


def slice_dataset(dataset, slicing=()):
    """
    Slices a dataset

    :param dataset: dataset to slice, might be a numpy array or a dataset in a
        HDF5 file
    :type dataset: numpy array or h5py.Dataset
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: ``data[start:]``
        - ``(start, stop)``: ``data[start:stop]``
        - ``("row", ind)``: ``data[ind]``
        - ``("col", ind)``: ``data[:, ind]`` (2D array only)
        - ``(ind, start, stop)``: data[:, start:stop]
    :type slicing: tuple

    :returns: sliced dataset
    :rtype: numpy array
    """

    # workaround in case of 1D dataset stored with shape (1, n) instead of (n,)
    shape = dataset.shape
    if len(shape) == 2 and shape[0] == 1 and shape[1] != 1:
        if (len(slicing) == 0 or len(slicing) > 0 and slicing[0] != "col"):
            if len(slicing) == 2:
                slicing = (0, slicing[0], slicing[1])

            elif len(slicing) == 1:
                slicing = (0, slicing[0], dataset.shape[1])

            else:
                slicing = (0, 0, dataset.shape[1])

    if len(slicing) == 1:
        output = dataset[slicing[0]:]

    elif len(slicing) == 2:
        if slicing[0] == "row":
            output = dataset[slicing[1]]

        elif slicing[0] == "col":
            output = dataset[:, slicing[1]]

        else:
            output = dataset[slicing[0]:slicing[1]]

    elif len(slicing) == 3:
        output = dataset[slicing[0], slicing[1]:slicing[2]]

    elif isinstance(dataset, Dataset):
        output = dataset[()]

    else:
        output = dataset

    return output
