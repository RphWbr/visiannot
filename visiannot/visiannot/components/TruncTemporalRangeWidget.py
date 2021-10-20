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

        #: (*int*) Number of frames correpsonding to duration of truncated
        #: temporal ranges
        self.nframes_trunc = convertTimeToFrame(
            visi.fps, minute=trunc_duration[0], sec=trunc_duration[1]
        )

        # check if trunc duration is above the total number of frames or
        # default => set it to 0
        if self.nframes_trunc > visi.nframes or self.nframes_trunc == 0:
            print("Duration of truncated temporal range is above the total number of frames => widget not created")
            
            #: (*int*) Number of splits
            self.nb_trunc = 0

            #: (:class:`.ToolsPyQt.ComboBox`) Combo box for selecting a
            #: truncated temporal range
            self.combo_trunc = None

        else:
            # get number of splits
            self.nb_trunc = round(visi.nframes / self.nframes_trunc)

            # set last frame of associated instance of ViSiAnnoT
            visi.last_frame = self.nframes_trunc

            # create combo box and add it to the layout of the associated
            # instance of ViSiAnnoT
            _, _, self.combo_trunc = addComboBox(
                visi.lay, widget_position, self.getTruncIntervals(visi),
                box_title="%dmin %ds temporal range" % tuple(trunc_duration),
                flag_enable_key_interaction=False
            )
            self.combo_trunc.setCurrentIndex(1)

            # listen to the callback method
            self.combo_trunc.currentIndexChanged.connect(
                lambda ite_trunc: self.callComboTrunc(ite_trunc, visi)
            )


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
        :attr:`.combo_trunc`

        Connected to the signal ``currentIndexChanged`` of
        :attr:`.combo_trunc`.

        It sets the temporal range (:attr:`.first_frame` and
        :attr:`.last_frame`) with the selected value in the combo
        box. The current frame :attr:`.frame_id` is set to the new
        :attr:`.first_frame`. Then it calls the method
        :meth:`.updateSignalPlot`.

        :param ite_trunc: index of the selected value in the combo box
            :attr:`.combo_trunc`
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
