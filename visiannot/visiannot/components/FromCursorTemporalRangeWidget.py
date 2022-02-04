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

from ...tools.datetime_converter import convert_time_to_frame
from ...tools.pyqt_overlayer import add_combo_box


class FromCursorTemporalRangeWidget():
    def __init__(self, visi, widget_position, from_cursor_list):
        """
        Widget for selecting a duration of temporal range to be started at
        the current frame in ViSiAnnoT

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param from_cursor_list: durations of temporal range to be started at
            the current frame in ViSiAnnoT, each element is a list of integers
            with 2 elements ``(minute, second)``
        :type from_cursor_list: list
        """

        #: (*list*) Durations of temporal range to be started at the current
        #: position of the temporal cursor in the associated instance of
        #: :class:`.ViSiAnnoT`
        #:
        #: Each element is a list of integers with 2 elements:
        #: ``(minute, second)``.
        self.from_cursor_list = from_cursor_list

        # items to display in the combo box
        combo_item_list = [""] + [
            '{:>02}:{:>02}'.format(from_cursor[0], from_cursor[1])
            for from_cursor in self.from_cursor_list
        ]

        #: (:class:`.pyqt_overlayer.ComboBox`) Combo box for
        #: selecting a temporal range starting at the current frame
        _, _, self.combo_box = add_combo_box(
            visi.lay, widget_position, combo_item_list,
            box_title="Temporal range duration",
            flag_enable_key_interaction=False
        )

        # listen to the callback method
        self.combo_box.currentIndexChanged.connect(
            lambda ite_combo: self.call_combo_from_cursor(ite_combo, visi)
        )


    def call_combo_from_cursor(self, ite_combo, visi):
        """
        Callback method for selecting a pre-defined temporal range that begins
        at the current temporal cursor position

        Connected to the signal ``currentIndexChanged`` of the attribute
        :attr:`.combo_box`.

        It sets :attr:`.first_frame` to :attr:`.frame_id`
        and :attr:`.last_frame` so that the temporal range spans the
        selected value of the combo box :attr:`.combo_box`.
        Then it calls the method :meth:`.update_signal_plot`.

        :param ite_combo: index of the selected value in the combo box
            :attr:`.combo_box`
        :type ite_combo: int
        """

        # check if the value selected in the combo box is not empty
        if ite_combo > 0:
            # get the value of the combo box and convert it to frame number
            ite_combo -= 1
            frame_interval = convert_time_to_frame(
                visi.fps, minute=self.from_cursor_list[ite_combo][0],
                sec=self.from_cursor_list[ite_combo][1]
            )

            # define new range
            visi.first_frame = visi.frame_id
            visi.last_frame = min(visi.frame_id + frame_interval, visi.nframes)

            # update plots signals
            visi.update_signal_plot(flag_reset_combo_from_cursor=False)
