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

from ...tools.ToolsDateTime import convertTimeToFrame, \
    convertFrameToAbsoluteTimeString
from ...tools.ToolsPyQt import addComboBox


class TruncTemporalRangeWidget():
    def __init__(self, visi, widget_position, trunc_duration):
        """
        Widget for selecting truncated temporal range

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the progress widget in the layout
            of the associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param trunc_duration: duration of the truncated temporal ranges, 2
            integer elements ``(minute, second)``
        :type trunc_duration: tuple or list
        """

        #: (*tuple* or *list*)
        self.trunc_duration = trunc_duration

        #: (*int*) Number of frames correpsonding to duration of truncated
        #: temporal ranges
        self.nframes_trunc = 0

        #: (*int*) Number of splits
        self.nb_trunc = 0

        #: (:class:`.ToolsPyQt.ComboBox`) Combo box for selecting a truncated
        #: temporal range
        self.combo_box = None

        # check trunc duration
        if self.trunc_duration[0] == 0 and self.trunc_duration[1] == 0:
            print("Duration of truncated temporal range is 0 => widget not created")

        else:
            # create combo box and add it to the layout of the associated
            # instance of ViSiAnnoT
            _, _, self.combo_box = addComboBox(
                visi.lay, widget_position, [],
                box_title="%dmin %ds temporal range" % tuple(trunc_duration),
                flag_enable_key_interaction=False
            )

            # set truncated duration and combo box items
            self.setTrunc(visi)

            # initialize selected item of the combo box
            self.combo_box.setCurrentIndex(1)

            # set last frame of associated instance of ViSiAnnoT
            visi.last_frame = self.nframes_trunc
            
            # listen to the callback method
            self.combo_box.currentIndexChanged.connect(
                lambda ite_trunc: self.callComboTrunc(ite_trunc, visi)
            )


    def setTrunc(self, visi):
        """
        Sets duration of truncated temporal ranges and combo box items

        It sets the attributes :attr:`.nframes_trunc`, :attr:`.combo_box`

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get number of frames corresponding to the duration of truncated
        # temporal ranges
        self.nframes_trunc = convertTimeToFrame(
            visi.fps, minute=self.trunc_duration[0], sec=self.trunc_duration[1]
        )

        # check if truncated duration is above the total number of frames
        # => set it to 0
        if self.nframes_trunc > visi.nframes or self.nframes_trunc == 0:
            print("Duration of truncated temporal range is above the current file duration => empty widget")
            self.nframes_trunc = 0
            self.nb_trunc = 0
            self.combo_box.clear()

        else:
            # get number of splits
            self.nb_trunc = round(visi.nframes / self.nframes_trunc)

            # set combo box items
            self.combo_box.clear()
            self.combo_box.addItems(self.getTruncIntervals(visi))


    def getTruncIntervals(self, visi):
        """
        Gets the strings associated to the truncated temporal ranges

        :param visi: associated instance of :class:`.ViSiAnnoT`

        :returns: list of strings
        :rtype: list
        """

        trunc_list = ['']
        for ite_trunc in range(self.nb_trunc):
            string_1 = convertFrameToAbsoluteTimeString(
                ite_trunc * self.nframes_trunc, visi.fps,
                visi.beginning_datetime
            )

            if (ite_trunc + 1) == self.nb_trunc:
                string_2 = convertFrameToAbsoluteTimeString(
                    visi.nframes, visi.fps, visi.beginning_datetime
                )

            else:
                string_2 = convertFrameToAbsoluteTimeString(
                    (ite_trunc + 1) * self.nframes_trunc, visi.fps,
                    visi.beginning_datetime
                )

            label = "%s - %s" % (string_1, string_2)
            trunc_list.append(label)

        return trunc_list


    def callComboTrunc(self, ite_trunc, visi):
        """
        Callback method for selecting a part of the video/signal defined by
        :attr:`.trunc_duration` via the combo box
        :attr:`.combo_box`

        Connected to the signal ``currentIndexChanged`` of
        :attr:`.combo_box`.

        It sets the temporal range (:attr:`.ViSiAnnoT.first_frame` and
        :attr:`.ViSiAnnoT.last_frame`) with the selected value in the combo
        box. The current frame :attr:`.ViSiAnnoT.frame_id` is set to the new
        :attr:`.ViSiAnnoT.first_frame`. Then it calls the method
        :meth:`.ViSiAnnoT.updateSignalPlot`.

        :param ite_trunc: index of the selected value in the combo box
            :attr:`.combo_box`
        :type ite_trunc: int
        """

        # check if the value selected in the combo box is not the first one
        # (empty one)
        if ite_trunc > 0:
            # define new range
            ite_trunc -= 1
            visi.first_frame = ite_trunc * self.nframes_trunc
            visi.last_frame = min(
                (ite_trunc + 1) * self.nframes_trunc, visi.nframes
            )

            # update plots signals
            visi.updateSignalPlot(flag_reset_combo_trunc=False)

            # update frame id
            visi.updateFrameId(ite_trunc * self.nframes_trunc)
