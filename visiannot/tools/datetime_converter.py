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
from datetime import datetime, timedelta, time
from pytz import timezone


def get_datetime_from_path(
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
        (either ``"posix"`` or a format compliant with ``datetime.strptime()``,
        see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    :type datetime_fmt: str
    :param kwargs: keyword arguments of :func:`.convert_string_to_datetime`

    If datetime is not in the file name, then set to ``None`` one of the
    following positional argument: ``datetime_del``, ``datetime_pos``,
    ``datetime_fmt``.

    If datetime is not found in the path, by default the function returns
    ``datetime(2000, 1, 1, 0, 0, 0)``.

    :returns: datetime
    :rtype: datetime.datetime
    """

    date_time = datetime(2000, 1, 1, 0, 0, 0)

    if datetime_del is not None and datetime_pos is not None \
            and datetime_fmt is not None:
        # get file basename
        basename = os.path.splitext(os.path.basename(path))[0]

        # split basename
        basename_split = basename.split(datetime_del)

        # check split length
        if len(basename_split) >= datetime_pos + 1:
            # get datetime string
            datetime_str = basename.split(datetime_del)[datetime_pos]

            date_time = convert_string_to_datetime(
                datetime_str, datetime_fmt, **kwargs
            )

    return date_time


def convert_seconds_to_time(time_sec):
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

    hour = int(time_sec / 3600)
    minute = int(time_sec / 60) - 60 * hour
    sec = int(time_sec - 60 * (minute + 60 * hour))
    msec = int(1000 * (time_sec - int(time_sec)))

    return hour, minute, sec, msec


def convert_frame_to_time(frame_nb, fps):
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

    return convert_seconds_to_time(float(frame_nb) / fps)


def convert_time_to_string(hour, minute, sec, msec=0, fmt="%H:%M:%S"):
    """
    Converts time as hour/minute/second/microsecond to time string

    :param hour:
    :type hour: int
    :param minute:
    :type minute: int
    :param sec:
    :type sec: int
    :param msec: microsecond
    :type msec: int

    :returns: time string
    :rtype: str
    """

    return time(hour, minute, sec, msec).strftime(fmt)


def convert_frame_to_string(frame_nb, fps, **kwargs):
    """
    Converts frame number to time string

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
    :param kwargs: keyword arguments of :func:`.convert_time_to_string`
        (``msec`` is ignored)

    :returns: time string
    :rtype: str
    """

    hour, minute, sec, msec = convert_frame_to_time(frame_nb, fps)
    kwargs["msec"] = msec

    return convert_time_to_string(hour, minute, sec, **kwargs)


def convert_string_to_datetime(datetime_str, fmt, time_zone=None):
    """
    Converts datetime string to datetime

    :param content: date-time string
    :type content: str
    :param fmt: date-time string format, might be ``posix`` or any format
        supported by ``datetime.strptime`` (see
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)
    :type fmt: str
    :param time_zone: timezone compliant with package pytz
    :type time_zone: str

    :returns: datetime
    :rtype: datetime.datetime
    """

    # convert string to datetime
    if fmt == "posix":
        date_time = datetime.fromtimestamp(int(datetime_str))

    else:
        date_time = datetime.strptime(datetime_str, fmt)

    # timezone
    if time_zone is not None:
        pst = timezone(time_zone)
        date_time = pst.localize(date_time)

    return date_time


def convert_string_colon_to_frame(time_string, fps):
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

    return convert_time_to_frame(fps, hour, minute, sec, msec)


def convert_time_to_frame(fps, hour=0, minute=0, sec=0, msec=0):
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


def convert_absolute_datetime_string_to_frame(
    fps, beginning_datetime, *args, **kwargs
):
    """
    Converts absolute date-time string to frame number

    The input beginning datetime is substracted to the absolute datetime to
    convert, so that the converted frame number is relative to the input
    beginning datetime.

    :param fps: frequency related to the converted frame number
    :type fps: int or float
    :param beginning_datetime: beginning datetime which is the reference for
        the converted frame number
    :type beginning_datetime: datetime.datetime
    :param args: positional arguments of :func:`.convert_string_to_datetime`
    :param kwargs: keyword argument of
        :func:`.convert_string_to_datetime`

    :returns: frame number
    :rtype: int
    """

    date_time = convert_string_to_datetime(*args, **kwargs)
    frame_id = convert_absolute_datetime_to_frame(
        date_time, fps, beginning_datetime
    )

    return frame_id


def convert_absolute_datetime_to_frame(date_time, fps, beginning_datetime):
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

    return convert_time_to_frame(fps, sec=sec, msec=msec)


def convert_frame_to_absolute_datetime(frame_nb, fps, beginning_datetime):
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

    hour, minute, sec, msec = convert_frame_to_time(frame_nb, fps)
    date_time = beginning_datetime + timedelta(
        hours=hour, minutes=minute, seconds=sec, milliseconds=msec
    )

    return date_time


def convert_frame_to_absolute_time_string(frame_nb, fps, beginning_datetime, **kwargs):
    """
    Converts frame number to absolute time string (date not provided)

    The input beginning datetime is added to the frame number,
    so that the converted time string is absolute.

    :param frame_nb: frame number to convert
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime

    :returns: absolute time string (date not provided)
    :rtype: str
    """

    date_time = convert_frame_to_absolute_datetime(
        frame_nb, fps, beginning_datetime
    )

    return convert_time_to_string(
        date_time.hour, date_time.minute, date_time.second,
        int(date_time.microsecond), **kwargs
    )


def convert_msec_to_absolute_time_string(
    msec, beginning_datetime, fmt="%H:%M:%S"
):
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

    return date_time.strftime(fmt)


def convert_frame_to_absolute_datetime_string(
    frame_nb, fps, beginning_datetime, fmt
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
    :param fmt: format of the datetime string, see
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    :type fmt: str

    :returns: absolute datetime
    :rtype: str
    """

    date_time = convert_frame_to_absolute_datetime(
        frame_nb, fps, beginning_datetime
    )

    return date_time.strftime(fmt)
