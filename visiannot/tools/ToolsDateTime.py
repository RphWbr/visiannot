# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module with functions for date-time management
"""


import os
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone
from .ToolsData import getDataGeneric


def getBeginningEndingDateTimeFromList(
    file_path_list, key_data, freq_data, *args, **kwargs
):
    """
    Gets the beginning and ending date-time of a list of data files

    The beginning date-time must be in the path of the data files.

    :param file_path_list: list of paths to the data files
    :type file_path_list: list
    :param key_data: key to access the data (in case of .mat or .h5)
    :type key_data: str
    :param freq_data: data frequency
    :type freq_data: int or float
    :param args: positional arguments of :func:`.getDatetimeFromPath`, minus
        the first one
    :param kwargs: keyword arguments of
        :func:`.getDatetimeFromPath` (keyword argument
        ``fmt`` will be ignored here)

    :returns:
        - **beginning_datetime_list** (*list*) -- instances of
          datetime.datetime (beginning date-time of the files)
        - **ending_datetime_list** (*list*) -- instances of datetime.datetime
          (ending date-time of the files)
    """

    beginning_datetime_list = []
    ending_datetime_list = []

    for path in file_path_list:
        # get file beginning date time
        b_date_time = getDatetimeFromPath(path, *args, **kwargs)

        # get data length
        data = getDataGeneric(path, key_data)

        # check if any data
        if data.size > 0:
            # check if signal not regularly sampled
            if freq_data == 0:
                # get duration in seconds
                duration_sec = data[-1, 0] / 1000

            # regularly sampled signal
            else:
                # get duration in seconds
                duration_sec = data.shape[0] / freq_data

            # get file ending date time
            e_date_time = b_date_time + timedelta(seconds=duration_sec)


        else:
            e_date_time = b_date_time
            duration_sec = 0

        # append lists
        beginning_datetime_list.append(b_date_time)
        ending_datetime_list.append(e_date_time)

    # sort paths by chronological order
    sort_indexes = np.argsort(beginning_datetime_list)

    beginning_datetime_list = [
        beginning_datetime_list[i] for i in sort_indexes
    ]

    ending_datetime_list = [
        ending_datetime_list[i] for i in sort_indexes
    ]

    return beginning_datetime_list, ending_datetime_list


def getDatetimeFromPath(
    path, datetime_del, datetime_pos, datetime_fmt, **kwargs
):
    """
    Gets datetime contained in a file name

    :param path: path where to find datetime
    :type path: str
    :param datetime_del: delimiter to get beginning datetime in the file name
    :type datetime_del: str
    :param datetime_pos: position of the beginning datetime in the file name,
        according to the delimiter
    :type datetime_pos: str
    :param datetime_fmt: format of the beginning datetime in the file name
        (either ``"posix"`` or a format compliant with ``datetime.strptime()``
        see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    :type datetime_fmt: str
    :param kwargs: keyword arguments of :func:`.convertStringToDatetime`

    If datetime is not in the file name, then set to ``None`` one of the
    following positional argument: ``datetime_del``, ``datetime_pos``,
    ``datetime_fmt``. By default the returned datetime is
    ``datetime(2000, 1, 1, 0, 0, 0)``.

    :returns: datetime
    :rtype: datetime.datetime
    """

    if datetime_del is None or datetime_pos is None or datetime_fmt is None:
        return datetime(2000, 1, 1, 0, 0, 0)

    else:
        # get file basename
        basename = os.path.splitext(os.path.basename(path))[0]

        # get datetime string
        datetime_str = basename.split(datetime_del)[datetime_pos]

        return convertStringToDatetime(datetime_str, datetime_fmt, **kwargs)


def convertSectimeToTime(time):
    """
    Converts time in seconds to time as hour/minute/second/msec

    :param time: time in seconds
    :type time: int or float

    :returns:
        - **hour** (*int*)
        - **minute** (*int*)
        - **second** (*int*)
        - **millisecond** (*int*)
    """

    hour = int(time / 3600)
    minute = int(time / 60) - 60 * hour
    sec = int(time - 60 * (minute + 60 * hour))
    msec = int(1000 * (time - int(time)))

    return hour, minute, sec, msec


def convertFrameToTime(frame_nb, fps):
    """
    Converts frame number to time as hour/minute/second/msec

    :param frame_nb: frame number
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float

    :returns:
        - **hour** (*int*)
        - **minute** (*int*)
        - **second** (*int*)
        - **millisecond** (*int*)
    """

    return convertSectimeToTime(float(frame_nb) / fps)


def convertTimeToString(hour, minute, sec, msec=0):
    """
    Converts time as hour/minute/second/msec to string "HH:MM:SS.sss"

    :param hour:
    :type hour: int
    :param minute:
    :type minute: int
    :param sec:
    :type sec: int
    :param msec:
    :type msec: int

    :returns: time with format "HH:MM:SS.sss"
    :rtype: str
    """

    return '{:>02}:{:>02}:{:>02}.{:>03}'.format(hour, minute, sec, msec)


def convertDatetimeToString(date_time, fmt=0):
    """
    Converts datetime to string "yyyy-mm-ddTHH:MM:SS.SSS" or
    "yyyy-mm-ddTHH-MM-SS"

    :param date_time: datetime to convert
    :type date_time: datetime.datetime
    :param fmt: output format, ``0`` => "HH:MM:SS.SSS" or ``1`` =>
        "HH-MM-SS" (no milliseconds)
    :type fmt: int

    :returns: date-time string
    :rtype: str
    """

    date_string = '{:>04}-{:>02}-{:>02}'.format(
        date_time.year, date_time.month, date_time.day
    )

    time_string = convertTimeToString(
        date_time.hour, date_time.minute, date_time.second,
        int(date_time.microsecond / 1000)
    )

    date_time_string = "%sT%s" % (date_string, time_string)
    if fmt == 1:
        date_time_string = date_time_string.replace(":", "-")[:19]

    return date_time_string


def convertFrameToString(frame_nb, fps):
    """
    Converts frame number to string "HH:MM:SS.sss"

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float

    :returns: time with format "HH:MM:SS.sss"
    :rtype: str
    """

    hour, minute, sec, msec = convertFrameToTime(frame_nb, fps)
    return convertTimeToString(hour, minute, sec, msec)


def convertStringToDatetime(datetime_str, fmt, time_zone=None):
    """
    Converts date-time string to datetime

    :param content: date-time string
    :type content: str
    :param fmt: date-time string format, might be ``posix``, ``format_T``
        (``%Y-%m-%dT%H:%M:%S.sss``, where ``sss`` is millisecond),
        or any format supported by ``datetime.strptime``
    :type fmt: str
    :param time_zone: timezone compliant with package pytz
    :type time_zone: str

    :returns: datetime
    :rtype: datetime.datetime
    """

    # convert string to datetime
    if fmt == "posix":
        date_time = datetime.fromtimestamp(int(datetime_str))

    elif fmt == "format_T":
        date_time = datetime.strptime(datetime_str[:19], "%Y-%m-%dT%H:%M:%S")
        date_time = date_time.replace(
            microsecond=int(datetime_str[20:]) * 1000
        )

    else:
        date_time = datetime.strptime(datetime_str, fmt)

    # timezone
    if time_zone is not None:
        pst = timezone(time_zone)
        date_time = pst.localize(date_time)

    return date_time


def convertStringColonToFrame(time_string, fps):
    """
    Converts time string to frame number

    :param time_string: time in format "HH:MM:SS", "MM:SS" or "SS"
        (there can be milliseconds appended ".sss")
    :type time_string: str
    :param fps: frequency related to the converted frame number
    :type fps: int or float

    :returns: frame number
    :rtype: int
    """

    time_string = time_string.split(':')

    if len(time_string) == 3:
        hour = int(time_string[0])
        minute = int(time_string[1])

        sec_split = time_string[2].split('.')
        if len(sec_split) == 1:
            sec = int(time_string[2])
            msec = 0
        else:
            sec = sec_split[0]
            msec = sec_split[1]

    elif len(time_string) == 2:
        hour = 0
        minute = int(time_string[0])

        sec_split = time_string[1].split('.')
        if len(sec_split) == 1:
            sec = int(time_string[1])
            msec = 0
        else:
            sec = sec_split[0]
            msec = sec_split[1]

    elif len(time_string) == 1:
        hour, minute = 0, 0

        sec_split = time_string[0].split('.')
        if len(sec_split) == 1:
            sec = int(time_string[0])
            msec = 0
        else:
            sec = sec_split[0]
            msec = sec_split[1]
    else:
        hour, minute, sec, msec = 0, 0, 0, 0

    return convertTimeToFrame(fps, hour, minute, sec, msec)


def convertTimeToFrame(fps, hour=0, minute=0, sec=0, msec=0):
    """
    Converts time as hour/minute/second/millisecond to frame number

    :param fps: frequency related to the converted frame number
    :type fps: int or float
    :param hour:
    :type hour: int
    :param minute:
    :type minute: int
    :param sec:
    :type sec: int
    :param msec:
    :type msec: int

    :returns: frame number
    :rtype: int
    """

    return int(fps * (3600 * hour + 60 * minute + sec + msec / 1000))


def convertAbsoluteDatetimeStringToFrame(
    content, fps, beginning_datetime, **kwargs
):
    """
    Converts absolute date-time string to frame number

    The input beginning datetime is substracted to the absolute datetime to
    convert, so that the converted frame number is relative to the input
    beginning datetime.

    :param content: absolute datetime string in format
        ``"%Y-%m-%dT%H:%M:%S.sss"``, where ``sss`` is millisecond
    :type content: str
    :param fps: frequency related to the converted frame number
    :type fps: int or float
    :param beginning_datetime: beginning datetime which is the reference for
        the converted frame number
    :type beginning_datetime: datetime.datetime
    :param kwargs: keyword argument of
        :func:`.ToolsDateTime.convertStringToDatetime`

    :returns: frame number
    :rtype: int
    """

    date_time = convertStringToDatetime(content, "format_T", **kwargs)
    return convertAbsoluteDatetimeToFrame(date_time, fps, beginning_datetime)


def convertAbsoluteDatetimeToFrame(date_time, fps, beginning_datetime):
    """
    Converts absolute datetime to frame number

    The input beginning datetime is substracted to the absolute datetime to
    convert, so that the converted frame number is relative to the input
    beginning datetime.

    :param content: absolute datetime
    :type content: instace of datetime.datetime
    :param fps: frequency related to the converted frame number
    :type fps: int or float
    :param beginning_datetime: beginning datetime which is the reference for
        the converted frame number
    :type beginning_datetime: datetime.datetime

    :returns: frame number
    :rtype: int
    """

    seconds = (date_time - beginning_datetime).total_seconds()

    sec = int(seconds)
    msec = int(1000 * (seconds - sec))

    return convertTimeToFrame(fps, sec=sec, msec=msec)


def convertFrameToAbsoluteDatetime(frame_nb, fps, beginning_datetime):
    """
    Converts frame number to absolute datetime

    The input beginning datetime is added to the frame number,
    so that the converted datetime is absolute.

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime

    :returns: absolute datetime
    :rtype: datetime.datetime
    """

    hour, minute, sec, msec = convertFrameToTime(frame_nb, fps)
    date_time = beginning_datetime + timedelta(
        hours=hour, minutes=minute, seconds=sec, milliseconds=msec
    )

    return date_time


def convertFrameToAbsoluteTimeString(frame_nb, fps, beginning_datetime):
    """
    Converts frame number to absolute time string "HH:MM:SS.sss" (date not
    provided)

    The input beginning datetime is added to the frame number,
    so that the converted time string is absolute.

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime

    :returns: absolute time "HH:MM:SS.sss" (date not provided)
    :rtype: str
    """

    date_time = convertFrameToAbsoluteDatetime(
        frame_nb, fps, beginning_datetime
    )

    return convertTimeToString(
        date_time.hour, date_time.minute, date_time.second,
        int(date_time.microsecond / 1000)
    )


def convertMsecToAbsoluteTimeString(msec, beginning_datetime):
    """
    Converts milliseconds to absolute time string "HH:MM:SS.sss"
    (date not provided)

    The input beginning datetime is added to the input milliseconds,
    so that the converted time string is absolute.

    :param msec: milliseconds to convert
    :type msec: int
    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime

    :returns: absolute time "HH:MM:SS.sss" (date not provided)
    :rtype: str
    """

    date_time = beginning_datetime + timedelta(milliseconds=msec)

    return convertTimeToString(
        date_time.hour, date_time.minute, date_time.second,
        int(date_time.microsecond / 1000)
    )


def convertFrameToAbsoluteDatetimeString(
    frame_nb, fps, beginning_datetime, **kwargs
):
    """
    Converts frame number to absolute datetime string

    The input beginning datetime is added to the frame number,
    so that the converted datetimetime string is absolute.

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime
    :param kwargs: keyword arguments of :func:`.convertDatetimeToString`

    :returns: absolute datetime
    :rtype: str
    """

    date_time = convertFrameToAbsoluteDatetime(
        frame_nb, fps, beginning_datetime
    )

    return convertDatetimeToString(date_time, **kwargs)
