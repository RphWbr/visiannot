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
    def __init__(self, data, freq, max_points=np.inf,
                 plot_style=None, legend_text=""):
        """
        Class defining a signal to plot in :class:`.ViSiAnnoT`

        The signal data can be accessed with the methods
        :meth:`.Signal.getData` and :meth:`.Signal.getDataInRange`.

        The attributes have the prefix _, so one should call the get methods to
        access them.

        :param data: signal data, shape :math:`(n_{samples})` if regularly
            sampled (i.e. ``freq != 0``), or :math:`(n_{samples}, 2)` if not
            regularlay sampled (i.e. ``freq == 0``), then first column contains
            the timestamp in milliseconds and the second column contains the
            data
        :type data: numpy array
        :param freq: signal frequency, set it to 0 if not regularly sampled
        :type freq: int or float
        :param max_points: maximum number of points to display in
            :class:`.ViSiAnnoT` (used in :meth:`.Signal.getDataInRange`)
        :type max_points: int
        :param plot_style: plot style of the signal, see
            https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotdataitem.html
            for details
        :type plot_style: dict
        :param legend_text: legend associated to the signal plot
        :type legend_text: str
        """

        if data is None:
            self._data = np.empty((0, 2))

        elif len(data.shape) == 2:
            self._data = data

        elif len(data.shape) == 1:
            data_range = 1000 * np.arange(0, data.shape[0]) / freq
            self._data = np.vstack((data_range, data)).T

        self._freq = freq
        self._max_points = max_points
        self._plot_style = plot_style
        self._legend_text = legend_text


    def getData(self):
        """
        Get method

        :returns: signal data, shape :math:`(n_{samples}, 2)` (even if
            regularly sampled), first column contains the timestamp in
            milliseconds and the second column contains the data
        :rtype: numpy array
        """

        return self._data


    def getFreq(self):
        """
        Get method

        :returns: signal frequency (``0`` if not regularly sampled)
        :rtype: int
        """

        return self._freq


    def getPlotStyle(self):
        """
        Get method

        :returns: plot style, might be ``None``
        :rtype: dict
        """

        return self._plot_style


    def getMaxPoints(self):
        """
        Get method

        :returns: maximum number of points to display in :class:`.ViSiAnnoT`
        :rtype: int
        """

        return self._max_points

    def getLegendText(self):
        """
        Get method

        :returns: legend associated to the signal plot
        :rtype: str
        """

        return self._legend_text


    def setSignal(self, *args, **kwargs):
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


    def getDataInRange(self, first_frame_ms, last_frame_ms):
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
        start_indexes = np.where(self._data[:, 0] > first_frame_ms)[0]
        if start_indexes.shape[0] == 0:
            start_id = self._data.shape[0] - 1
        else:
            # substraction with 1 in order to get the point just before,
            # it looks better like that for signals with non constant frequency
            start_id = max(0, start_indexes[0] - 1)

        # get stop index
        stop_indexes = np.where(self._data[:, 0] < last_frame_ms)[0]
        if stop_indexes.shape[0] == 0:
            stop_id = 0
        else:
            # addition with 2 in order to get the point just after,
            # it looks better like that for signals with non constant frequency
            stop_id = min(self._data.shape[0], stop_indexes[-1] + 2)

        # reverse start and stop index if necessary
        if start_id > stop_id:
            start_id, stop_id = stop_id, start_id

        # downsampling if too much data to plot
        length = stop_id - start_id

        if length <= self._max_points:
            return self._data[start_id:stop_id]

        else:
            step = int(length / self._max_points)

            if self._data.ndim == 1:
                return np.vstack((
                    np.arange(start_id, stop_id, step),
                    self._data[start_id:stop_id:step]
                )).T

            else:
                return self._data[start_id:stop_id:step]


    def downsampleSignal(self, new_freq):
        """
        Sets the instance with a new signal frequency

        Once the signal data is downsampled, the method calls the method
        :meth:`.Signal.setSignal`.

        NB: make sure that this method is called only if the signal is
        regularly sampled.

        :param new_freq: new frequency of the signal, make sure that it is
            littler than the current frequency
        :type new_freq: int or float
        """

        # downsampling factor
        factor = int(self._freq / new_freq)

        # get data values
        data = self._data[:, 1]

        # check if data size is divisible by downsampling factor
        if (data.shape[0] / factor).is_integer():
            # downsample
            new_data = Signal.downSample(data, factor)
        else:
            # fill data with nan
            fill_nb = round(
                (int(data.shape[0] / factor) + 1 - data.shape[0] / factor) * factor
            )

            new_data = np.hstack((data, np.nan * np.ones((fill_nb,))))

            # downsample
            new_data = Signal.downSample(new_data, factor)

            # delete nan
            nan_nb = np.where(np.isnan(new_data))[0].shape[0]
            if nan_nb > 0:
                new_data = new_data[:-nan_nb]

        # reset signal
        self.setSignal(
            new_data, new_freq, plot_style=self._plot_style,
            legend_text=self._legend_text
        )


    @staticmethod
    def downSample(data, factor):
        """
        Downsamples the input data by the specified factor using mean

        :param data: signal data to downsample, shape :math:`(n_{frames},)`
        :type data: numpy array
        :param factor: downsampling factor, make sure that
            :math:`n_{frames}/factor` is an integer
        :type factor: int

        :returns: downsampled signal data, shape :math:`(n_{frames}/factor,)`
        :rtype: numpy array
        """

        return data.reshape(-1, factor).mean(axis=1)
