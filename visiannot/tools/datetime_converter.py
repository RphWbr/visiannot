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
from decimal import Decimal

#: (*str*) Default time string format
TIME_FMT = "%H:%M:%S"


def convert_datetime_to_string(date_time, fmt=TIME_FMT):
    """
    Converts a datetime to a string

    :param date_time:
    :type date_time: datetime.datetime or datetime.time
    :param fmt: output string format, might be ``posix`` or any format
        supported by **datetime** (see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes),
        it is also possible to use the code ``%s`` for milliseconds (in this
        case, it must be the last code of the format)
    :type fmt: str

    :returns: formatted datetime string
    :rtype: str
    """

    # check string format
    if fmt == "posix":
        datetime_str = date_time.timestamp()

    elif "%s" in fmt:
        fmt = fmt.replace("%s", "%f")
        datetime_str = date_time.strftime(fmt)
        datetime_str = datetime_str[:-3]

    else:
        datetime_str = date_time.strftime(fmt)

    return datetime_str


def convert_string_to_datetime(datetime_str, fmt, time_zone=None):
    """
    Converts datetime string to datetime

    :param content: date-time string
    :type content: str
    :param fmt: date-time string format, might be ``posix`` or any format
        supported by **datetime** (see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes),
        it is also possible to use the code ``%s`` for milliseconds (in
        this case, it must be the last code of the format)
    :type fmt: str
    :param time_zone: timezone compliant with package **pytz**
    :type time_zone: str

    :returns: datetime
    :rtype: datetime.datetime
    """

    # convert string to datetime
    if fmt == "posix":
        date_time = datetime.fromtimestamp(int(datetime_str))

    elif "%s" in fmt:
        fmt = fmt.replace("%s", "%f")
        datetime_str += "000"
        date_time = datetime.strptime(datetime_str, fmt)

    else:
        date_time = datetime.strptime(datetime_str, fmt)

    # timezone
    if time_zone is not None:
        pst = timezone(time_zone)
        date_time = pst.localize(date_time)

    return date_time


def get_datetime_from_path(
    path, datetime_del, datetime_pos, fmt, **kwargs
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
    :param fmt: format of the beginning datetime in the file name
        (either ``"posix"`` or a format compliant with ``datetime.strptime()``,
        see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    :type fmt: str
    :param kwargs: keyword arguments of :func:`.convert_string_to_datetime`

    If datetime is not in the file name, then set to ``None`` one of the
    following positional argument: ``datetime_del``, ``datetime_pos``, ``fmt``.

    If datetime is not found in the path, by default the function returns
    ``datetime(2000, 1, 1, 0, 0, 0)``.

    :returns: datetime
    :rtype: datetime.datetime
    """

    date_time = datetime(2000, 1, 1, 0, 0, 0)

    if datetime_del is not None and datetime_pos is not None \
            and fmt is not None:
        # get file basename
        basename = os.path.splitext(os.path.basename(path))[0]

        # split basename
        basename_split = basename.split(datetime_del)

        # check split length
        if len(basename_split) >= datetime_pos + 1:
            # get datetime string
            datetime_str = basename.split(datetime_del)[datetime_pos]

            date_time = convert_string_to_datetime(
                datetime_str, fmt, **kwargs
            )

    return date_time


def convert_seconds_to_time(time_sec):
    """
    Converts time in seconds to time as hour/minute/second/microsecond

    :param time: time in seconds
    :type time: int or float

    :returns:
        - **hour** (*int*)
        - **minute** (*int*)
        - **second** (*int*)
        - **microsecond** (*int*)
    """

    hour = int(time_sec / 3600)
    minute = int(time_sec / 60) - 60 * hour
    sec = int(time_sec - 60 * (minute + 60 * hour))
    msec = int(1000000 * (Decimal(str(time_sec)) - int(time_sec)))

    return hour, minute, sec, msec


def convert_frame_to_time(frame_nb, fps):
    """
    Converts frame number to time as hour/minute/second/microsecond

    :param frame_nb: frame number
    :type frame_nb: int
    :param fps: frequency related to the frame number
    :type fps: int or float
 
    :returns: see output of :func:`.convert_seconds_to_time`
    """

    return convert_seconds_to_time(float(frame_nb) / fps)


def convert_time_to_string(hour, minute, sec, msec=0, **kwargs):
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
    :param kwargs: keyword arguments of :func:`.convert_datetime_to_string`

    :returns: time string
    :rtype: str
    """

    # get time
    time_obj = time(hour, minute, sec, msec)

    # convert to string
    time_str = convert_datetime_to_string(time_obj, **kwargs)

    return time_str


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


def convert_time_to_frame(fps, hour=0, minute=0, sec=0, msec=0):
    """
    Converts time as hour/minute/second/microsecond to frame number

    :param fps: frequency related to the converted frame number
    :type fps: int or float
    :param hour:
    :type hour: int
    :param minute:
    :type minute: int
    :param sec:
    :type sec: int
    :param msec: microsecond
    :type msec: int

    :returns: frame number
    :rtype: int
    """

    return int(fps * (3600 * hour + 60 * minute + sec + msec / 1000000))


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
    msec = int(1000000 * (seconds - sec))

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
        hours=hour, minutes=minute, seconds=sec, microseconds=msec
    )

    return date_time


def convert_timedelta_to_absolute_datetime_string(
    beginning_datetime, delta_dict, **kwargs
):
    """
    Converts a time delta to absolute datetime string

    The time delta is added to the beginning datetime, so that the output
    datetime string is absolute.

    :param beginning_datetime: reference datetime to get absolute datetime
    :type beginning_datetime: datetime.datetime
    :param delta_dict: keyword arguments of
        https://docs.python.org/3/library/datetime.html#timedelta-objects
        (e.g. ``{"milliseconds": 500}``)
    :type delta_dict: dict
    :param kwargs: keyword arguments :func:`.convert_datetime_to_string`

    :returns: absolute datetime
    :rtype: str
    """

    date_time = beginning_datetime + timedelta(**delta_dict)

    return convert_datetime_to_string(date_time, **kwargs)


def convert_frame_to_absolute_datetime_string(
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
    :param kwargs: keyword arguments :func:`.convert_datetime_to_string`

    :returns: absolute datetime
    :rtype: str
    """

    date_time = convert_frame_to_absolute_datetime(
        frame_nb, fps, beginning_datetime
    )

    return convert_datetime_to_string(date_time, **kwargs)
