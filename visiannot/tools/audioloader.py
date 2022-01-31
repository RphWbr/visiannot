# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for loading audio files
"""


import wave
import numpy as np


def get_audio_wave_info(path):
    """
    Loads audio wave and gets frequency and number of samples

    :param path: path to the audio file
    :type path: str

    :returns:
        - **data_wave** (*wave.Wave_read*) -- see
          https://docs.python.org/3/library/wave.html#wave-read-objects
        - **freq** (*float*) -- frequency
        - **nframes** (*float*) -- number of samples
    """

    # get audio wave
    data_wave = wave.open(path, 'rb')

    # get frequency
    freq = data_wave.getframerate()

    # get number of samples
    nb_samples = data_wave.getnframes()

    return data_wave, freq, nb_samples


def get_data_audio(path, channel_id=0, slicing=()):
    """
    Loads audio data

    :param path: path to the audio file
    :type path: str
    :param channel_id: audio channel to be loaded as a numpy array, set it to
        ``-1`` to get all channels
    :type channel_id: int
    :param slicing: indexes for slicing output data:

        - ``()``: no slicing
        - ``(start,)``: ``data[start:]``
        - ``(start, stop)``: ``data[start:stop]``
    :type slicing: tuple

    :returns:
        - **data_wave** (*wave.Wave_read*) -- see
          https://docs.python.org/3/library/wave.html#wave-read-objects
        - **data_audio** (*numpy array*) -- audio signal, with all channels
          if ``channel_id`` is set to ``-1``
        - **freq** (*int*) -- frequency
    """

    # get audio wave and frequency
    data_wave, freq, nb_samples = get_audio_wave_info(path)

    # get audio data as a numpy array
    data_audio = data_wave.readframes(nb_samples)
    byte_length = int(len(data_audio) / nb_samples)

    if byte_length == 2:
        np_type = np.int8
    elif byte_length == 4:
        np_type = np.int16
    elif byte_length == 8:
        np_type = np.int32
    elif byte_length == 16:
        np_type = np.int64
    else:
        np_type = None

    if np_type is None:
        data_audio = np.empty((0,))

    else:
        data_audio = np.fromstring(data_audio, dtype=np_type).reshape(
            (nb_samples, data_wave.getnchannels())
        )

        # get specific channel if necessary
        if channel_id >= 0:
            data_audio = data_audio[:, channel_id]

        if len(slicing) == 1:
            data_audio = data_audio[slicing[0]:]

        elif len(slicing) == 2:
            data_audio = data_audio[slicing[0]:slicing[1]]

    return data_wave, data_audio, freq


def convert_key_to_channel_id(key_data):
    """
    Converts a key to access data (configuration for :class:`.ViSiAnnoT`) to
    the index of an audio channel

    The key must contain the word "left" or "right", otherwise default channel
    is ``0``.

    :param key_data: key with channel ID
    :type key_data: str

    :returns: channel ID
    :rtype: int
    """

    key_data_lower = key_data.lower()

    if "left" in key_data_lower:
        channel_id = 0

    elif "right" in key_data_lower:
        channel_id = 1

    else:
        channel_id = 0

    return channel_id
