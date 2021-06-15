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


def getAudioWaveFrequency(path):
    """
    Loads audio wave and gets frequency

    :param path: path to the audio file
    :type path: str

    :returns:
        - **data_wave** (*wave.Wave_read*) -- see
          https://docs.python.org/3/library/wave.html#wave-read-objects
        - **freq** (*int* or *float*) -- frequency
    """

    # get audio wave
    data_wave = wave.open(path, 'rb')

    # get frequency
    freq = data_wave.getframerate()

    return data_wave, freq


def getDataAudio(path, channel_id=0):
    """
    Loads audio data

    :param path: path to the audio file
    :type path: str
    :param channel_id: audio channel to be loaded as a numpy array, set it to
        ``-1`` to get all channels
    :type channel_id: int

    :returns:
        - **data_wave** (*wave.Wave_read*) -- see
          https://docs.python.org/3/library/wave.html#wave-read-objects
        - **data_audio** (*numpy array*) -- audio signal, with all channels
          if ``channel_id`` is set to ``-1``
        - **freq** (*int*) -- frequency
    """

    # get audio wave and frequency
    data_wave, freq = getAudioWaveFrequency(path)

    # get audio data as a numpy array
    data_audio = data_wave.readframes(data_wave.getnframes())
    byte_length = int(len(data_audio) / data_wave.getnframes())

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
            (data_wave.getnframes(), data_wave.getnchannels())
        )

        # get specific channel if necessary
        if channel_id >= 0:
            data_audio = data_audio[:, channel_id]

    return data_wave, data_audio, freq


def convertKeyToChannelId(key_data):
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
