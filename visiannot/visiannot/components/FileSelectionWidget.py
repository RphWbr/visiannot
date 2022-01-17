# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.FileSelectionWidget`
"""

from ...tools.ToolsPyQt import addComboBox


class FileSelectionWidget():
    def __init__(self, visi, widget_position):
        """
        Widget for selecting a file in a long recording (thanks to a combo box)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        """

        #: (*QtWidgets.QComboBox*) Combo box for recording file selection
        self.combo_box = None

        # create combo box widget
        _, group_box, self.combo_box = addComboBox(
            visi.lay, widget_position,
            [str(ite_file + 1) for ite_file in range(visi.nb_files)],
            box_title="File ID / %d" % visi.nb_files
        )

        group_box.setMaximumWidth(100)

        # listen to callbacks
        self.combo_box.currentIndexChanged.connect(
            lambda ite_file: self.fileSelection(ite_file, visi)
        )


    def fileSelection(self, ite_file, visi):
        """
        Callback method for selecting a new file in the long recording with the
        combo box

        Connected to the signal ``currentIndexChanged`` of :attr:`.combo_box`.

        :param ite_file: index of the file in the long recording selected in
            the combo box
        :type ite_file: int
        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # change recording
        visi.changeFileInLongRec(ite_file, 0)
