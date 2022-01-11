# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.AnnotEventWidget`
"""

from os.path import isdir, basename, isfile
from os import makedirs
from PyQt5 import QtWidgets, QtCore
from ...tools import ToolsPyQt
from ...tools.ToolsData import getTxtLines
from ...tools.ToolsDateTime import convertDatetimeToString, \
    convertAbsoluteDatetimeStringToFrame, convertStringToDatetime, \
    convertFrameToAbsoluteDatetime, convertFrameToAbsoluteDatetimeString
from ...tools.ToolsPyqtgraph import removeItemInWidgets
import numpy as np
from datetime import timedelta


class AnnotEventWidget():
    def __init__(
        self, visi, widget_position, label_dict, annot_dir, **kwargs
    ):
        """
        Widget for event annotation

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param widget_position: position of the widget in the layout of the
            associated instance of :class:`.ViSiAnnoT`
        :type widget_position: tuple or list
        :param label_dict: key is the label, value is the associated color
            (RGB or RGBA) ; in case RGB color is provided, then a transparency
            value of 80 is automatically added
        :type label_dict: dict
        :param annot_dir: directory where the annotations are saved
        :type annot_dir: str
        :param kwargs: keyword arguments of :meth:`.createWidget`
        """

        #: (*str*) Directory where the annotations are saved
        self.annot_dir = annot_dir

        #: (*str*) Base name of the annotation files (to which is appended
        #: the label)
        #:
        #: It is defined as the basename of the annotation directory
        #: :attr:`.annot_dir`.
        self.file_name_base = basename(self.annot_dir)

        #: (*str*) Label automatically created for getting duration of video
        #: files (or first signal if no video)
        #:
        #: It cannot be used for manual annotation, so it is ignored if
        #: specified by the user in the keyword argument ``annotevent_dict`` of
        #: :class:`.ViSiAnnoT` constructor.
        self.protected_label = "DURATION"

        # check if protected label in list of labels
        if self.protected_label in label_dict.keys():
            del label_dict[self.protected_label]
            print(
                "Label %s for events annotation is protected and cannot be\
                used for manual annotation, so it is ignored" %
                self.protected_label
            )

        #: (*list*) Labels of the event annotation
        self.label_list = list(label_dict.keys())

        #: (*list*) Colors of the event annotation labels
        #:
        #: each element is a list of length 4 with the RGBA color
        self.color_list = list(label_dict.values())

        # add transparency for color if needed
        for annot_color in self.color_list:
            if isinstance(annot_color, list) and len(annot_color) == 3:
                annot_color.append(80)

        #: (*numpy array*) Array with unsaved annotated event
        #:
        #: Shape :math:`(n_{label}, 2, 2)`, where :math:`n_{label}` is the
        #: length of :attr:`.label_list`. For a given label with index ``n`` in
        #: :attr:`.label_list`, the sub-array
        #: ``self.annot_array[n]`` is organized as follows:
        #:
        #: =====================  ===============================================
        #: start datetime string  start frame index in the format "recId_frameId"
        #: end datetime string    end frame index in the format "recId_frameId"
        #: =====================  ===============================================
        self.annot_array = np.zeros(
            (len(self.label_list), 2, 2), dtype=object
        )

        #: (*dict*) Event annotations descriptions to be displayed
        #:
        #: Key is the index of a label in :attr:`.label_list`. Value is a
        #: dictionary:
        #:
        #:      - Key is an integer with the annotation ID (index in the
        #:        annotation file)
        #:      - Value is a list of instances of **pyqtgraph.TextItem** with
        #:        the description, same length and order as
        #:        :attr:`.ViSiAnnoT.wid_sig_list`, so that one element
        #:        corresponds to one signal widget
        self.description_dict = {}

        #: (*list*) Way of storing event annotations
        #:
        #: Two elements:
        #:
        #: - ``"datetime"``: datetime string in the format
        #:   ``%Y-%M-%DT%h-%m-%s.%ms``
        #: - ``"frame"``: recId_frameId
        self.annot_type_list = ["datetime", "frame"]

        if len(self.label_list) > 0:
            #: (*list*) Files names of event annotation
            #:
            #: Same length as :attr:`.annot_type_list`, there is
            #: one file for each annotation type.
            self.path_list = self.getPathList(
                self.label_list[0]
            )

            # create directory if necessary
            if not isdir(self.annot_dir):
                makedirs(self.annot_dir)

            # create annotation file with duration of video files
            # (or first signal if no video)
            self.createAnnotDuration(visi)

        else:
            self.path_list = []

        #: (*int*) Index of the currently selected label, with respect to the
        #: list :attr:`.label_list`
        self.current_label_id = 0

        #: (*QtWidgets.QButtonGroup*) Set of radio buttons for selecting a
        #: label
        self.button_group_radio_label = None

        #: (*QtWidgets.QButtonGroup*) Set of radio buttons for selecting a
        #: display option
        self.button_group_radio_disp = None

        #: (*QtWidgets.QButtonGroup*) Set of check boxes for custom display
        self.button_group_check_custom = None

        #: (*QtWidgets.QButtonGroup*) Set of push buttons for annotation
        #: (Sart, Stop, Add, Delete last, Display)
        self.button_group_push = QtWidgets.QButtonGroup()

        #: (*list*) Instances of **QtWidgets.QLabel** containing the text
        #: next to the push buttons grouped in :attr:`.button_group_push`
        self.push_text_list = []

        # create widget with button groups and add it to the layout of
        # ViSiAnnoT
        self.createWidget(visi.lay, widget_position, **kwargs)

        #: (*dict*) Lists of region items (pyqtgraph.LinearRegionItem)
        #: for the display of event annotations
        #:
        #: Key is a label index. Value is a list of lists, each sublist
        #: corresponds to one annotation and contains
        #: :math:`n_{wid} + 1` region items, where :math:`n_{wid}` is
        #: the length of :attr:`.ViSiAnnoT.wid_sig_list` (number of
        #: signal widgets), the additional region item is for the
        #: progress bar (:attr:`.ViSiAnnoT.wid_progress`).
        #:
        #: For example, for 3 signal widgets and for a given label with
        #: 2 annotations, the value of the dictionary would be::
        #:
        #:      [
        #:          [
        #:              annot1_widProgress, annot1_wid1, annot1_wid2,
        #:              annot1_wid3
        #:          ],
        #:          [
        #:              annot2_widProgress, annot2_wid1, annot2_wid2,
        #:              annot2_wid3
        #:          ]
        #:      ]
        self.region_dict = {}

        # plot annotations
        self.plotRegions(visi)

        # listen to the callback methods
        self.button_group_push.buttonClicked[int].connect(
            lambda button_id: self.callPushButton(button_id, visi)
        )

        self.button_group_radio_label.buttonClicked.connect(
            lambda ev: self.callRadio(ev, visi)
        )

        self.button_group_radio_disp.buttonClicked.connect(
            lambda: self.plotRegions(visi)
        )

        self.button_group_check_custom.buttonClicked.connect(
            lambda: self.plotRegions(visi)
        )


    # *********************************************************************** #
    # Group: Widget creation
    # *********************************************************************** #


    def createWidget(self, lay, widget_position, nb_table=5):
        """
        Creates a widget with the events annotation tool and adds it to the
        layout of the associated instance of :class:`.ViSiAnnoT`

        Make sure the attribute :attr:`.label_list` is
        defined before calling this method.

        It sets the following attributes:

        - :attr:`.button_group_radio_label`
        - :attr:`.button_group_push` (must be initialized)
        - :attr:`.push_text_list` (must be initialized)
        - :attr:`.button_group_radio_disp`
        - :attr:`.button_group_check_custom`

        :param lay: layout of the associated instance of :class:`.ViSiAnnoT`
        :type lay: QtWidgets.QGridLayout
        :param widget_position: position of the widget in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type widget_position: list or tuple
        :param nb_table: maximum number of radio buttons (resp. check boxes) in
            :attr:`.button_group_radio_label` (resp.
            :attr:`.button_group_check_custom`) on a row
        :type nb_table: int
        """

        # create group box
        grid, _ = ToolsPyQt.addGroupBox(
            lay, widget_position, title="Events annotation"
        )

        # create widget with radio buttons (annotation labels)
        _, _, self.button_group_radio_label = ToolsPyQt.addWidgetButtonGroup(
            grid, (0, 0, 1, 2), self.label_list, color_list=self.color_list,
            box_title="Current label selection", nb_table=nb_table
        )

        # get number of annotations already stored (default first label)
        if isfile(self.path_list[0]):
            lines = getTxtLines(self.path_list[0])
            nb_annot = len(lines)
        else:
            nb_annot = 0

        # create push buttons with a text next to it
        button_text_list = ["Start", "Stop", "Add", "Delete last", "Display"]
        push_text_list = [
            "YYYY-MM-DD hh:mm:ss.sss",
            "YYYY-MM-DD hh:mm:ss.sss",
            "Nb: %d" % nb_annot,
            "",
            "On"
        ]

        for ite_button, (text, label) in enumerate(zip(
            button_text_list, push_text_list
        )):
            # add push button
            push_button = ToolsPyQt.addPushButton(
                grid, (1 + ite_button, 0), text,
                flag_enable_key_interaction=False
            )

            # add push button to group for push buttons
            self.button_group_push.addButton(push_button, ite_button)

            # add label next to the push button
            if label != '':
                q_label = QtWidgets.QLabel(label)
                q_label.setAlignment(QtCore.Qt.AlignVCenter)
                grid.addWidget(q_label, 1 + ite_button, 1)
                self.push_text_list.append(q_label)

        # create widget with radio buttons (display options)
        _, _, self.button_group_radio_disp = ToolsPyQt.addWidgetButtonGroup(
            grid, (2 + ite_button, 0, 1, 2),
            ["Current label", "All labels", "Custom (below)"],
            box_title="Display mode"
        )

        # create check boxes with labels
        _, _, self.button_group_check_custom = ToolsPyQt.addWidgetButtonGroup(
            grid, (3 + ite_button, 0, 1, 2), self.label_list,
            color_list=self.color_list, box_title="Custom display",
            button_type="check_box", nb_table=nb_table
        )


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Annotation management
    # *********************************************************************** #


    def getPathList(self, label):
        """
        Gets the path of the annotation files corresponding to the input label

        :param label: event annotation label
        :type label: str

        :returns: paths of the annotation files, each element corresponds to an
            annotation type (see :attr:`.annot_type_list`)
        :rtype: list
        """

        path_list = []
        for annot_type in self.annot_type_list:
            path_list.append(
                '%s/%s_%s-%s.txt' % (
                    self.annot_dir, self.file_name_base, label, annot_type
                )
            )

        return path_list


    def createAnnotDuration(self, visi):
        """
        Creates annotation events files for the duration of each file of the
        reference modality (only one file if not a long recording)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get path of annotation files
        output_path_0 = "%s/%s_%s-datetime.txt" % (
            self.annot_dir, self.file_name_base, self.protected_label
        )

        output_path_1 = "%s/%s_%s-frame.txt" % (
            self.annot_dir, self.file_name_base, self.protected_label
        )

        # check if annotation file does not exist
        if not isfile(output_path_0):
            # check if long recording in ViSiAnnoT
            if visi.flag_long_rec:
                # annotation type: datetime
                with open(output_path_0, 'w') as f:
                    # loop on beginning datetime and duration of reference
                    # modality files in the long recording
                    for beg_datetime, duration in zip(
                        visi.rec_beginning_datetime_list,
                        visi.rec_duration_list
                    ):
                        # get end datetime
                        end_datetime = beg_datetime + timedelta(
                            seconds=duration
                        )

                        # convert datetime to string
                        beg_string = convertDatetimeToString(beg_datetime)
                        end_string = convertDatetimeToString(end_datetime)

                        # write annotation file
                        f.write("%s - %s\n" % (beg_string, end_string))

                # annotation type: frame
                with open(output_path_1, 'w') as f:
                    # loop on duration of reference modality files in the long
                    # recording
                    for ite_file, duration in enumerate(
                        visi.rec_duration_list
                    ):
                        # write annotation file
                        f.write("%d_0 - %d_%d\n" % (
                            ite_file, ite_file, int(duration * visi.fps)
                        ))

            # not a long recording
            else:
                # annotation type: datetime
                with open(output_path_0, 'w') as f:
                    # get end datetime
                    end_datetime = visi.beginning_datetime + timedelta(
                        seconds=visi.nframes / visi.fps
                    )

                    # convert datetime to string
                    beg_string = convertDatetimeToString(
                        visi.beginning_datetime
                    )

                    end_string = convertDatetimeToString(
                        end_datetime
                    )

                    # write annotation file
                    f.write("%s - %s\n" % (beg_string, end_string))

                # annotation type: frame
                with open(output_path_1, 'w') as f:
                    # write annotation file
                    f.write("0_0 - 0_%d\n" % visi.nframes)


    def callRadio(self, ev, visi):
        """
        Callback method for changing label

        Connected to the signal ``buttonClicked`` of
        :attr:`.button_group_radio_label`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param ev: radio button that has been clicked
        :type ev: QtWidgets.QRadioButton
        """

        # get the new annotation file name
        self.changeLabel(visi, ev.text())


    def changeLabel(self, visi, new_label):
        """
        Changes label and loads corresponding annotation files

        It sets the value of the following attributes:

        - :attr:`.current_label_id` with the index of the new label in
          :attr:`.label_list`
        - :attr:`.path_list` with the new list of annotation file paths (by
          calling :meth:`.getPathList`)

        It also manages the display of the annotations.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param new_label: new annotation label
        :type new_label: str
        """

        # update current label
        self.current_label_id = self.label_list.index(new_label)

        # get the new annotation file name
        self.path_list = self.getPathList(new_label)

        # get number of annotation already stored
        if isfile(self.path_list[0]):
            lines = getTxtLines(self.path_list[0])
            nb_annot = len(lines)

        else:
            nb_annot = 0

        # update label with the number of annotations
        self.push_text_list[2].setText("Nb: %d" % nb_annot)

        # update label with the start and end time
        non_zero_array = np.count_nonzero(
            self.annot_array[self.current_label_id], axis=1
        )

        if non_zero_array[0] < 2:
            self.push_text_list[0].setText(
                "YYYY-MM-DD hh:mm:ss.sss"
            )
        else:
            self.push_text_list[0].setText(
                self.annotevent_array[self.current_label_id, 0, 0]
            )

        if non_zero_array[1] < 2:
            self.push_text_list[1].setText(
                "YYYY-MM-DD hh:mm:ss.sss"
            )
        else:
            self.push_text_list[1].setText(
                self.annot_array[self.current_label_id, 1, 0]
            )

        # plot annotations
        self.plotRegions(visi)


    def getAnnotIdFromPosition(self, visi, position):
        """
        Looks for the index of the annotation at the given frame for the
        current label

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`)
        :type position: int

        :returns: index of the annotation (i.e. line number in the annotation
            file), returns ``-1`` if no annotation at ``position``
        :rtype: int
        """

        # initialize output
        annot_id = -1

        # check if annotation file exists
        if isfile(self.path_list[0]):
            # convert mouse position to datetime
            position_date_time = convertFrameToAbsoluteDatetime(
                position, visi.fps, visi.beginning_datetime
            )

            # get annotations for current label
            lines = getTxtLines(self.path_list[0])

            # loop on annotations
            for ite_annot, line in enumerate(lines):
                # get annotation
                line = line.replace("\n", "")

                start_date_time = convertStringToDatetime(
                    line.split(" - ")[0], "format_T", time_zone=visi.time_zone
                )

                end_date_time = convertStringToDatetime(
                    line.split(" - ")[1], "format_T", time_zone=visi.time_zone
                )

                diff_start = (
                    position_date_time - start_date_time
                ).total_seconds()

                diff_end = (
                    end_date_time - position_date_time
                ).total_seconds()

                # check if mouse position is in the annotation interval
                if diff_start >= 0 and diff_end >= 0:
                    annot_id = ite_annot
                    break

        return annot_id


    def callPushButton(self, button_id, visi):
        """
        Callback method for managing annotation with push buttons

        Connected to the signal ``buttonClicked[int]`` of the attribute
        attr:`.button_group_push`.

        There are 5 buttons and they have an effect on the unsaved current
        annotation of the current label:

        - ``button_id == 0``: set start timestamp at the current frame
          :attr:`.ViSiAnnoT.frame_id`
        - ``button_id == 1``: set ending datetime with the current frame
          :attr;`.ViSiAnnoT.frame_id`
        - ``button_id == 2``: add annotation defined by the current timestamps
        - ``button_id == 3``: delete last annotation
        - ``button_id == 4``: on/off display

        :param button_id: index of the button that has been pushed
        :type button_id: int
        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # set beginning time of the annotated interval
        if button_id == 0:
            self.setTimestamp(visi, visi.frame_id, 0)

        # set ending time of the annotated interval
        elif button_id == 1:
            self.setTimestamp(visi, visi.frame_id, 1)

        # add the annotated interval to the annotation file
        elif button_id == 2:
            self.add(visi)

        # delete last annotation
        elif button_id == 3:
            # check if annotation file exists and annotation file is not empty
            if isfile(self.path_list[0]) and \
                    int(self.push_text_list[2].text().split(': ')[1]) > 0:
                self.delete(visi, -1)

            else:
                print(
                    "Cannot delete annotation since annotation file does not "
                    "exist or is empty"
                )

        # display the annotated intervals
        elif button_id == 4:
            self.display(visi)


    def setTimestamp(self, visi, frame_id, annot_position):
        """
        Sets the start or end timestamp of the current unsaved annotation for
        the current label

        It sets the values of
        ``self.annot_array[self.current_label_id, annot_position]``.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param frame_id: frame number of the timestamp (sampled at the
            reference frequency :attr:`.ViSiAnnoT.fps`)
        :type frame_id: int
        :param annot_position: specify if start timestamp (``0``) or end
            timestamp (``1``)
        :type annot_position: int
        """

        if (annot_position == 0 or annot_position == 1) and \
                len(self.label_list) > 0:
            # set timestamp in datetime string format
            self.annot_array[self.current_label_id, annot_position, 0] = \
                convertFrameToAbsoluteDatetimeString(
                    frame_id, visi.fps, visi.beginning_datetime
            )

            # set timestamp in frame format
            self.annot_array[self.current_label_id, annot_position, 1] = \
                '%d_%d' % (visi.rec_id, frame_id)

            # display the beginning time of the annotated interval
            self.push_text_list[annot_position].setText(
                self.annot_array[self.current_label_id, annot_position, 0]
            )


    def resetTimestamp(self):
        """
        Resets the timestamps of the current unsaved annotation for the current
        label

        It sets ``self.annot_array[self.current_label_id]`` to zeros.
        """

        # reset the beginning and ending times of the annotated interval
        self.annot_array[self.current_label_id] = np.zeros((2, 2))

        # reset the displayed beginning and ending times of the annotated
        # interval
        self.push_text_list[0].setText("YYYY-MM-DD hh:mm:ss.sss")
        self.push_text_list[1].setText("YYYY-MM-DD hh:mm:ss.sss")


    def add(self, visi):
        """
        Adds an annotation to the current label

        It writes in the annotation files (:attr:`.path_list`).

        If the annotation start timestamp or end timestamp is not defined, then
        nothing happens.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # check if start timestamp or end timestamp of the annotated interval
        # is empty
        if np.count_nonzero(self.annot_array[self.current_label_id]) < 4:
            print("Empty annotation !!! Cannot write file.")

        # otherwise all good
        else:
            # convert timestamps to datetime
            annot_datetime_0 = convertStringToDatetime(
                self.annot_array[self.current_label_id, 0, 0],
                "format_T", time_zone=visi.time_zone
            )

            annot_datetime_1 = convertStringToDatetime(
                self.annot_array[self.current_label_id, 1, 0],
                "format_T", time_zone=visi.time_zone
            )

            # check if annotation must be reversed
            if (annot_datetime_1 - annot_datetime_0).total_seconds() < 0:
                self.annot_array[self.current_label_id, [0, 1]] = \
                    self.annot_array[self.current_label_id, [1, 0]]

            # append the annotated interval to the annotation file
            for ite_annot_type, annot_path in enumerate(self.path_list):
                with open(annot_path, 'a') as file:
                    file.write(
                        "%s - %s\n" % (
                            self.annot_array[
                                self.current_label_id, 0, ite_annot_type
                            ],
                            self.annot_array[
                                self.current_label_id, 1, ite_annot_type
                            ]
                        )
                    )

            # update the number of annotations
            nb_annot = int(self.push_text_list[2].text().split(': ')[1]) + 1
            self.push_text_list[2].setText("Nb: %d" % nb_annot)

            # if display mode is on, display the appended interval
            if self.push_text_list[3].text() == "On" and \
                    self.current_label_id in self.region_dict.keys():
                region_list = self.addRegion(
                    visi,
                    self.annot_array[self.current_label_id, 0, 0],
                    self.annot_array[self.current_label_id, 1, 0],
                    color=self.color_list[self.current_label_id]
                )

                self.region_dict[self.current_label_id].append(region_list)

            # reset the beginning and ending times of the annotated interval
            self.resetTimestamp()


    @staticmethod
    def deleteLineInFile(path, line_id):
        """
        Class method for deleting a line in a txt file

        :param path: path to the text file
        :type path: str
        :param line_id: number of the line to delete (zero-indexed)
        :type line_id: int
        """

        # read annotation file lines
        lines = getTxtLines(path)

        # remove specified line
        del lines[line_id]

        # rewrite annotation file
        with open(path, 'w') as file:
            file.writelines(lines)


    def delete(self, visi, annot_id):
        """
        Deletes a specific annotation for the current label

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param annot_id: index of the annotation to delete
        :type annot_id: int
        """

        # delete annotation in the txt file
        for annot_path in self.path_list:
            AnnotEventWidget.deleteLineInFile(annot_path, annot_id)

        # update number of annotations
        nb_annot = max(
            0, int(self.push_text_list[2].text().split(': ')[1]) - 1
        )

        self.push_text_list[2].setText("Nb: %d" % nb_annot)

        # delete annotation description if necessary
        if self.current_label_id in self.description_dict.keys():
            description_dict = self.description_dict[self.current_label_id]

            if annot_id in description_dict.keys():
                removeItemInWidgets(
                    visi.wid_sig_list, description_dict[annot_id]
                )

                del description_dict[annot_id]

            elif annot_id == -1 and nb_annot in description_dict.keys():
                removeItemInWidgets(
                    visi.wid_sig_list, description_dict[nb_annot]
                )

                del description_dict[nb_annot]

        # if display mode is on, remove the deleted annotation
        if self.push_text_list[3].text() == "On":
            visi.removeRegionInWidgets(
                self.region_dict[self.current_label_id][annot_id]
            )

            del self.region_dict[self.current_label_id][annot_id]


    def deleteClicked(self, visi, position):
        """
        Deletes an annotion that is clicked on

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`) corresponding to the mouse position on the
            X axis of the signal widgets
        :type position: int
        """

        # get annotated event ID
        annot_id = self.getAnnotIdFromPosition(visi, position)

        # check if an annotated event must be deleted
        if annot_id >= 0:
            # delete annotation
            self.delete(visi, annot_id)


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Display management
    # *********************************************************************** #


    def plotRegions(self, visi):
        """
        Plots event annotations, depending on the display mode selected with
        :attr:`.button_group_radio_disp`

        Make sure that the attribute :attr:`.region_dict` is already created.

        It checks if the display mode is on before plotting.

        Connected to the signal ``buttonClicked`` of
        :attr:`.button_group_radio_disp` and
        :attr:`.button_group_check_custom`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # check if display mode is on
        if self.push_text_list[3].text() == "On":
            # get display mode
            button_id = self.button_group_radio_disp.checkedId()

            # display current label
            if button_id == 0:
                plot_dict = {
                    self.current_label_id:
                    self.color_list[self.current_label_id]
                }

            # display all labels
            elif button_id == 1:
                plot_dict = {}
                for label_id, color in enumerate(self.color_list):
                    plot_dict[label_id] = color

            # display custom
            elif button_id == 2:
                plot_dict = {}
                for label_id, color in enumerate(self.color_list):
                    if self.button_group_check_custom.button(
                        label_id
                    ).isChecked():
                        plot_dict[label_id] = color

            # loop on labels already plotted
            label_id_list = list(self.region_dict.keys())
            for label_id in label_id_list:
                # if label not to be plotted anymore
                if label_id not in plot_dict.keys():
                    # clear display
                    self.clearRegionsSingleLabel(visi, label_id)

            # loop on labels to plot
            for label_id, color in plot_dict.items():
                # check if label not already displayed
                if label_id not in self.region_dict.keys():
                    # get annotation path
                    label = self.label_list[label_id]
                    annot_path = self.getPathList(label)[0]

                    # initialize list of region items for the label
                    region_annotation_list = []

                    # check if annotation file exists
                    if isfile(annot_path):
                        # read annotation file
                        lines = getTxtLines(annot_path)

                        # loop on annotations
                        for annot_line in lines:
                            # display region
                            annot_line_content = annot_line.split(' - ')

                            region_list = self.addRegion(
                                visi,
                                annot_line_content[0],
                                annot_line_content[1].replace("\n", ""),
                                color=color
                            )

                            # append list of region items for the label
                            region_annotation_list.append(region_list)

                    # update dictionary of region items
                    self.region_dict[label_id] = region_annotation_list

                    # display annotations description
                    if label_id in self.description_dict.keys():
                        for description_list in \
                                self.description_dict[label_id].values():
                            visi.addItemToSignals(description_list)


    def display(self, visi):
        """
        Mananges the display of annotations (on/off)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # if display mode is off, put it on
        if self.push_text_list[3].text() == "Off":
            # notify that display mode is now on
            self.push_text_list[3].setText("On")

            # display regions from the annotation file
            self.plotRegions(visi)

        # display mode is on, put it off
        else:
            self.clearRegions(visi)

            # notify that display mode is now off
            self.push_text_list[3].setText("Off")


    def clearRegions(self, visi):
        """
        Clears the display of annotations for all labels (but does not
        delete the annotations)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # loop on labels
        for label_id in range(len(self.label_list)):
            self.clearRegionsSingleLabel(visi, label_id)


    def clearRegionsSingleLabel(self, visi, label_id):
        """
        Clears the display of annotations for a specific label

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param label_id: index of the label in the list
            :attr:`.ViSiAnnoT.annotevent_label_list`
        :type label_id: int
        """

        # clear annotations display
        if label_id in self.region_dict.keys():
            for region_list in self.region_dict[label_id]:
                visi.removeRegionInWidgets(region_list)
            del self.region_dict[label_id]

        # clear descriptions display
        if label_id in self.description_dict:
            for description_list in \
                    self.description_dict[label_id].values():
                removeItemInWidgets(
                    visi.wid_sig_list, description_list
                )


    def addRegion(self, visi, bound_1, bound_2, **kwargs):
        """
        Displays a region in the progress bar and the signal widgets

        It converts the bounds to frame numbers and then calls the
        method :meth:`.ViSiAnnoT.addRegionToWidgets`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param bound_1: start datetime of the region
        :type bound_1: str
        :param bound_2: end datetime of the region
        :type bound_2: str
        :param kwargs: keyword arguments of
            :meth:`.ViSiAnnoT.addRegionToWidgets`
        """

        # convert bounds to frame numbers
        frame_1 = convertAbsoluteDatetimeStringToFrame(
            bound_1, visi.fps, visi.beginning_datetime,
            time_zone=visi.time_zone
        )

        frame_2 = convertAbsoluteDatetimeStringToFrame(
            bound_2, visi.fps, visi.beginning_datetime,
            time_zone=visi.time_zone
        )

        # check date-time (useful for longRec)
        if frame_1 >= 0 and frame_1 < visi.nframes \
            or frame_2 >= 0 and frame_2 < visi.nframes \
                or frame_1 < 0 and frame_2 >= visi.nframes:
            # display region in each signal plot
            region_list = visi.addRegionToWidgets(frame_1, frame_2, **kwargs)

            return region_list

        else:
            return []


    # *********************************************************************** #
    # End group
    # *********************************************************************** #

    # *********************************************************************** #
    # Group: Annotation description
    # *********************************************************************** #


    def description(self, visi, ev, pos_frame, pos_ms):
        """
        Creates and displays text items in signal widgets with the description
        of the annotation that has been clicked on

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param ev: radio button that has been clicked
        :type ev: QtWidgets.QRadioButton
        :param pos_frame: frame number (sampled at the reference frequency
            :attr:`ViSiAnnoT.fps`) corresponding to the mouse position on the X
            axis of the signal widget
        :type pos_frame: int
        :param pos_ms: mouse position on the X axis of the signal widget in
            milliseconds
        :type pos_ms: float
        """

        # get annotation ID that has been clicked
        annot_id = self.getAnnotIdFromPosition(visi, pos_frame)

        # check if mouse clicked on an annotation
        if annot_id >= 0:
            # get dictionary with description text items for the current label
            if self.current_label_id in self.description_dict.keys():
                description_dict = self.description_dict[self.current_label_id]

            # create dictionary with description items for the current label
            else:
                description_dict = {}

                self.description_dict[self.current_label_id] = description_dict

            # check if description already displayed
            if annot_id in description_dict.keys():
                # remove display
                removeItemInWidgets(
                    visi.wid_sig_list, description_dict[annot_id]
                )

                # delete list of description text items from dictionary
                del description_dict[annot_id]

            else:
                # get list of Y position of the mouse in each signal widget
                pos_y_list = visi.getMouseYPosition(ev)

                # get date-time string annotation
                annot = getTxtLines(self.path_list[0])[annot_id]

                # get date-time start/stop of the annotation
                start, stop = annot.replace("\n", "").split(" - ")

                # convert date-time string to datetime
                start = convertStringToDatetime(
                    start, "format_T", time_zone=visi.time_zone
                )

                stop = convertStringToDatetime(
                    stop, "format_T", time_zone=visi.time_zone
                )

                # compute annotation duration
                duration = (stop - start).total_seconds()

                # get annotation description
                description = "%s - %.3f s" % (
                    self.label_list[self.current_label_id],
                    duration
                )

                # get description color
                color = self.color_list[self.current_label_id]

                # create list of description text items for the annotation
                self.description_dict[self.current_label_id][annot_id] = \
                    visi.createTextItem(
                        description, pos_ms, pos_y_list, border_color=color
                )


    def clearDescriptions(self, visi):
        """
        Clears the display of all the annotations descriptions

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        for description_dict in self.description_dict.values():
            for description_list in description_dict.values():
                removeItemInWidgets(visi.wid_sig_list, description_list)

        self.description_dict = {}


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
