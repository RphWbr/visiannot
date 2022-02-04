# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.TimeEditWidget`
"""

from PyQt5.QtWidgets import QDateTimeEdit, QTimeEdit, QLabel
from PyQt5 import QtCore
from ...tools.pyqt_overlayer import add_push_button, add_group_box
from ...tools import datetime_converter
import numpy as np
from datetime import datetime
from pytz import timezone


class CustomTemporalRangeWidget():
    def __init__(self, visi, widget_position):
        """
        Widget for custom temporal range

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        """

        # create group box
        grid, _ = add_group_box(
            visi.lay, widget_position, "Custom temporal range"
        )

        # add qlabel
        q_label = QLabel("Start date-time")
        q_label.setAlignment(QtCore.Qt.AlignRight)
        grid.addWidget(q_label, 0, 0)

        #: (*QtWidgets.QDateTimeEdit*) Editor of starting datetime of
        #: custom temporal range, intialized with beginning datetime of the
        #: associated instance of :class:`.ViSiAnnoT`
        self.edit_start = QDateTimeEdit(QtCore.QDateTime(
            QtCore.QDate(
                visi.beginning_datetime.year,
                visi.beginning_datetime.month,
                visi.beginning_datetime.day
            ),
            QtCore.QTime(
                visi.beginning_datetime.hour,
                visi.beginning_datetime.minute,
                visi.beginning_datetime.second
            )
        ))
        self.edit_start.setDisplayFormat("yyyy-MM-dd - hh:mm:ss")
        grid.addWidget(self.edit_start, 0, 1)

        #: (*QtWidgets.QPushButton*) Push button for defining the starting
        #: datetime of custom temporal range as the current frame
        self.current_push = add_push_button(grid, (0, 2), "Current")

        # add qlabel
        q_label = QLabel("Temporal range duration")
        q_label.setAlignment(QtCore.Qt.AlignRight)
        grid.addWidget(q_label, 1, 0)

        #: (*QtWidgets.QTimeEdit*) Editor of the duration of custom
        #: temporal range
        self.edit_duration = QTimeEdit()
        self.edit_duration.setDisplayFormat("hh:mm:ss")
        grid.addWidget(self.edit_duration, 1, 1)

        #: (*QtWidgets.QPushButton*) Push button for validating custom
        #: temporal range
        self.time_edit_push = add_push_button(grid, (1, 2), "Ok")

        # listen to the callback methods
        self.current_push.clicked.connect(lambda: self.time_edit_current(visi))
        self.time_edit_push.clicked.connect(lambda: self.time_edit_ok(visi))


    def time_edit_current(self, visi):
        """
        Callback method to set :attr:`.edit_start` to the current
        frame :attr:`.ViSiAnnoT.frame_id`

        Connected to the signal ``clicked`` of :attr:`.current_push`.
        """

        current_datetime = \
            datetime_converter.convert_frame_to_absolute_datetime(
                visi.frame_id, visi.fps, visi.beginning_datetime
            )

        self.edit_start.setDate(
            QtCore.QDate(current_datetime.year,
                         current_datetime.month,
                         current_datetime.day)
        )

        self.edit_start.setTime(
            QtCore.QTime(current_datetime.hour,
                         current_datetime.minute,
                         current_datetime.second)
        )


    def time_edit_ok(self, visi):
        """
        Callback method to set the temporal range
        (:attr:`.ViSiAnnoT.first_frame` and :attr:`.ViSiAnnoT.last_frame`) to
        the custom temporal range (manually defined with :attr:`.edit_duration`
        and :attr:`.edit_start`)

        If :attr:`.edit_duration` is 0, then the current temporal range
        duration is kept.

        Connected to the signal ``clicked`` of :attr:`.time_edit_push`.
        """

        # get duration time edit
        duration_qtime = self.edit_duration.time()
        duration_hour = duration_qtime.hour()
        duration_minute = duration_qtime.minute()
        duration_sec = duration_qtime.second()

        # check duration
        if duration_hour == 0 and duration_minute == 0 and duration_sec == 0:
            duration_hour, duration_minute, duration_sec, _ = \
                datetime_converter.convert_frame_to_time(
                    visi.last_frame - visi.first_frame, visi.fps
                )

        # get start date-time
        start_qdate = self.edit_start.date()
        start_qtime = self.edit_start.time()
        start_date_time = datetime(
            start_qdate.year(), start_qdate.month(), start_qdate.day(),
            start_qtime.hour(), start_qtime.minute(), start_qtime.second()
        )
        pst = timezone(visi.time_zone)
        start_date_time = pst.localize(start_date_time)

        # get start frame
        start_frame = datetime_converter.convert_absolute_datetime_to_frame(
            start_date_time, visi.fps, visi.beginning_datetime
        )

        # check temporal coherence
        coherence = True
        if start_frame < 0 or start_frame >= visi.nframes:
            # check long recordings
            if visi.flag_long_rec:
                # get recording id
                start_ref_diff_array = np.array(
                    [(beg_rec - start_date_time).total_seconds()
                        for beg_rec in visi.ref_beg_datetime_list]
                )

                new_ite_file = np.where(start_ref_diff_array >= 0)[0]

                if new_ite_file.shape[0] == 0:
                    coherence = False
                    print(
                        "wrong input: start time is above the ending of the "
                        "recordings"
                    )

                elif new_ite_file.shape[0] == start_ref_diff_array.shape[0]:
                    coherence = False
                    print(
                        "wrong input: start time is below the beginning of "
                        "the recording"
                    )

                else:
                    # change recording
                    new_ite_file = new_ite_file[0] - 1
                    coherence = visi.prepare_new_file(new_ite_file)

            else:
                print(
                    "wrong input: start time is below the beginning of the "
                    "recordings or above the ending of the recording"
                )

                coherence = False

        # go for it
        if coherence:
            # define new range
            start_frame = datetime_converter.convert_absolute_datetime_to_frame(
                start_date_time, visi.fps, visi.beginning_datetime
            )

            if len(visi.wid_sig_list) > 0:
                visi.first_frame = start_frame

                visi.last_frame = min(
                    visi.nframes,
                    visi.first_frame + datetime_converter.convert_time_to_frame(
                        visi.fps, duration_hour, duration_minute, duration_sec
                    )
                )

            # udpdate current frame
            visi.update_frame_id(start_frame)

            # update signals plots
            visi.update_signal_plot()

            # update annotation regions plot
            if visi.wid_annotevent is not None:
                visi.wid_annotevent.clear_regions(visi)
                visi.wid_annotevent.plot_regions(visi)
