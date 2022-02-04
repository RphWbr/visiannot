# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.AnnotImageWidget`
"""

from os.path import isdir
from os import mkdir, makedirs
from ...tools.pyqt_overlayer import add_widget_button_group, add_push_button
from ...tools.video_loader import transform_image
from cv2 import imwrite
from math import ceil


class AnnotImageWidget():
    def __init__(
        self, visi, widget_position, label_list, annot_dir, nb_table=5,
        flag_horizontal=True
    ):
        """
        Widget for image extraction

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: list or tuple
        :param nb_table: maximum number of radio buttons in
            :attr:`.radio_button_group` on a row
        :type nb_table: int
        :param flag_horizontal: specify if radio buttons are placed
            horizontally, otherwise vertically
        :type flag_horizontal: bool
        """

        #: (*str*) Directory where the images are saved, a sub-directory is
        #: automatically created for each label
        self.annot_dir = annot_dir

        # check type (if loaded from a configuration, then dictionary instead
        # of list)
        if isinstance(label_list, dict):
            # convert to list
            label_list = [k for k in label_list.values()]

        #: (*list*) Labels
        self.label_list = label_list

        # create directories if necessary
        if not isdir(self.annot_dir):
            makedirs(self.annot_dir)

        for label in self.label_list:
            label_dir = "%s/%s" % (self.annot_dir, label)
            if not isdir(label_dir):
                mkdir(label_dir)

        # check radio buttons layout
        if flag_horizontal:
            # get position of the push button
            pos_push_button = (
                ceil(len(self.label_list) / nb_table), 0
            )

        else:
            # get position of the push button
            pos_push_button = (
                min(len(self.label_list), nb_table), 0
            )


        #: (*QtWidgets.QButtonGroup*) Set of radio buttons for selecting a
        #: label
        self.radio_button_group = None
        grid, _, self.radio_button_group = add_widget_button_group(
            visi.lay, widget_position, self.label_list, button_type="radio",
            box_title="Image extraction", flag_horizontal=flag_horizontal,
            nb_table=nb_table
        )

        #: (:class:`.pyqt_overlayer.PushButton`) Push
        #: button for saving image extraction
        self.push_button = add_push_button(
            grid, pos_push_button, "Save", flag_enable_key_interaction=False
        )


        # listen to the callback method
        self.push_button.clicked.connect(lambda: self.call_push_button(visi))


    def call_push_button(self, visi):
        """
        Callback method for saving the image at current frame in ViSiAnnoT

        Connected to the signal ``clicked`` of :attr:`.push_button`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get current label
        current_label = self.radio_button_group.checkedButton().text()

        # get output directory
        output_dir = "%s/%s" % (self.annot_dir, current_label)

        # loop on cameras
        for wid_vid in visi.wid_vid_dict.values():
            # read image
            im = transform_image(wid_vid.image)

            # save image
            im_path = "%s/%s_%s.png" % (
                output_dir, wid_vid.title, visi.frame_id
            )
            imwrite(im_path, im)
            print("image saved: %s" % im_path)
