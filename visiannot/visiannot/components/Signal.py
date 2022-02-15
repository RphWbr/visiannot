# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.Signal`
"""

import numpy as np


class Signal():
    def __init__(
        self, data, freq, max_points=np.inf, plot_style=None, legend_text=""
    ):
        """
        Class defining a signal to plot in :class:`.ViSiAnnoT`

        The signal data can be accessed with the methods
        :meth:`.Signal.getData` and :meth:`.Signal.get_data_in_range`.

        The attributes have the prefix _, so one should call the get methods to
        access them.

        :param data: signal data, shape :math:`(n_{samples})` if regularly
            sampled (i.e. ``freq != 0``), or :math:`(n_{samples}, 2)` if not
            regularlay sampled (i.e. ``freq == 0``), then first column contains
            the timestamp in milliseconds and the second column contains the
            data
        :type data: numpy array
        :param freq: signal frequency, set it to ``0`` if not regularly sampled
        :type freq: int or float
        :param max_points: maximum number of points to display in
            :class:`.ViSiAnnoT` (used in :meth:`.Signal.get_data_in_range`)
        :type max_points: int
        :param plot_style: plot style of the signal, see
            https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html
        :type plot_style: dict
        :param legend_text: legend associated to the signal plot
        :type legend_text: str
        """

        if data is None:
            #: (*numpy array*) Signal data shape :math:`(n_{samples}, 2)`
            #: (even if regularly sampled), first column contains the timestamp
            #: in milliseconds and the second column contains the data
            self.data = np.empty((0, 2))

        elif len(data.shape) == 2:
            self.data = data

        elif len(data.shape) == 1:
            data_range = 1000 * np.arange(0, data.shape[0]) / freq
            self.data = np.vstack((data_range, data)).T

        #: (*int*) Signal frequency (``0`` if not regularly sampled)
        self.freq = freq

        #: (*int*) Maximum number of points to display in :class:`.ViSiAnnoT`
        self.max_points = max_points

        #: (*dict*) Plot style (default ``None``), see
        #: https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html
        self.plot_style = plot_style

        #: (*str*) Legend associated to the signal plot
        self.legend_text = legend_text


    def set_signal(self, *args, **kwargs):
        """
        Sets the instance with new values

        It calls the constructor.

        :param args: positional arguments of the constructor of
            :class:`.Signal`
        :param kwargs:
        :type kwargs: keyword arguments of the constructor of
            :class:`.Signal`
        """

        self.__init__(*args, **kwargs)


    def get_data_in_range(self, first_frame_ms, last_frame_ms):
        """
        Returns the signal data in the range defined by
        ``first_frame_ms:last_frame_ms``

        :param first_frame_ms: first frame of the range in milliseconds
        :type first_frame_ms: int
        :param last_frame_ms: last frame of the range in milliseconds
        :type last_frame_ms: int

        :returns: signal data in the range [first_frame_ms:last_frame_ms]
        :rtype: numpy array
        """

        # get start index
        start_indexes = np.where(self.data[:, 0] > first_frame_ms)[0]
        if start_indexes.shape[0] == 0:
            start_id = self.data.shape[0] - 1
        else:
            # substraction with 1 in order to get the point just before,
            # it looks better like that for signals with non constant frequency
            start_id = max(0, start_indexes[0] - 1)

        # get stop index
        stop_indexes = np.where(self.data[:, 0] < last_frame_ms)[0]
        if stop_indexes.shape[0] == 0:
            stop_id = 0
        else:
            # addition with 2 in order to get the point just after,
            # it looks better like that for signals with non constant frequency
            stop_id = min(self.data.shape[0], stop_indexes[-1] + 2)

        # reverse start and stop index if necessary
        if start_id > stop_id:
            start_id, stop_id = stop_id, start_id

        # downsampling if too much data to plot
        length = stop_id - start_id

        if length <= self.max_points:
            return self.data[start_id:stop_id]

        else:
            step = int(length / self.max_points)

            if self.data.ndim == 1:
                return np.vstack((
                    np.arange(start_id, stop_id, step),
                    self.data[start_id:stop_id:step]
                )).T

            else:
                return self.data[start_id:stop_id:step]
