# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.file_selectionWidget`
"""

from ...tools.pyqt_overlayer import add_combo_box


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
        _, group_box, self.combo_box = add_combo_box(
            visi.lay, widget_position,
            [str(ite_file + 1) for ite_file in range(visi.nb_files)],
            box_title="File ID / %d" % visi.nb_files
        )

        group_box.setMaximumWidth(100)

        # listen to callbacks
        self.combo_box.currentIndexChanged.connect(
            lambda ite_file: self.file_selection(ite_file, visi)
        )


    def file_selection(self, ite_file, visi):
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
        visi.change_file_in_long_rec(ite_file, 0)
