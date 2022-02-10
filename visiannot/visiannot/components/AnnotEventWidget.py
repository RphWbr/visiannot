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
from ...tools import pyqt_overlayer
from ...tools.data_loader import get_txt_lines
from ...tools import datetime_converter
from ...tools.pyqtgraph_overlayer import remove_item_in_widgets
import numpy as np
from datetime import timedelta


class AnnotEventWidget():
    def __init__(
        self, visi, widget_position, label_dict, annot_dir,
        flag_annot_overlap=False, **kwargs
    ):
        """
        Widget for events annotation

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
        :param flag_annot_overlap: specify if overlap of events annotations is
            enabled
        :type flag_annot_overlap: bool
        :param kwargs: keyword arguments of :meth:`.create_widget`
        """

        #: (*str*) Text for empty annotation timestamp next to push buttons
        #: "Start" and "Stop"
        self.empty_annotation = "YYYY-MM-DDThh:mm:ss.ssssss"

        #: (*str*) Datetime string format of the annotations timestamps
        self.timestamp_format = "%Y-%m-%dT%H:%M:%S.%f"

        #: (*str*) Directory where the annotations are saved
        self.annot_dir = annot_dir

        #: (*bool*) Specify if overlap of events annotations is enabled
        self.flag_annot_overlap = flag_annot_overlap

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

        #: (*list*) Labels of the events annotation
        self.label_list = list(label_dict.keys())

        #: (*list*) Colors of the events annotation labels
        #:
        #: each element is a list of length 4 with the RGBA color
        self.color_list = list(label_dict.values())

        # add transparency for color if needed
        for annot_color in self.color_list:
            if isinstance(annot_color, list) and len(annot_color) == 3:
                annot_color.append(80)

        #: (*numpy array*) Array with unsaved annotated event
        #:
        #: Shape :math:`(n_{label}, 2)`, where :math:`n_{label}` is the
        #: length of :attr:`.label_list`. Each row corresponds to a label
        #: and is composed of the beginning datetime and ending datetime of
        #: the current annotation not saved yet.
        self.annot_array = np.zeros((len(self.label_list), 2), dtype=object)

        #: (*dict*) Events annotations descriptions to be displayed
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

        if len(self.label_list) > 0:
            #: (*list*) Path to the annotation file of the currently selected
            #: label
            self.path = self.get_path(self.label_list[0])

            # create directory if necessary
            if not isdir(self.annot_dir):
                makedirs(self.annot_dir)

            # create annotation file with duration of video files
            # (or first signal if no video)
            self.create_annot_duration(visi)

        else:
            self.path = None

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
        self.create_widget(visi.lay, widget_position, **kwargs)

        #: (*dict*) Lists of region items (pyqtgraph.LinearRegionItem)
        #: for the display of events annotations
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
        self.plot_regions(visi)

        # listen to the callback methods
        self.button_group_push.buttonClicked[int].connect(
            lambda button_id: self.call_push_button(button_id, visi)
        )

        self.button_group_radio_label.buttonClicked.connect(
            lambda ev: self.call_radio(ev, visi)
        )

        self.button_group_radio_disp.buttonClicked.connect(
            lambda: self.plot_regions(visi)
        )

        self.button_group_check_custom.buttonClicked.connect(
            lambda: self.plot_regions(visi)
        )


    # *********************************************************************** #
    # Group: Widget creation
    # *********************************************************************** #


    def create_widget(self, lay, widget_position, nb_table=5):
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
        grid, _ = pyqt_overlayer.add_group_box(
            lay, widget_position, title="Events annotation"
        )

        # create widget with radio buttons (annotation labels)
        _, _, self.button_group_radio_label = \
            pyqt_overlayer.add_widget_button_group(
                grid, (0, 0, 1, 2), self.label_list,
                color_list=self.color_list,
                box_title="Current label selection", nb_table=nb_table
            )

        # get number of annotations already stored
        if isfile(self.path):
            nb_annot = len(get_txt_lines(self.path))

        else:
            nb_annot = 0

        # create push buttons with a text next to it
        button_text_list = ["Start", "Stop", "Add", "Delete last", "Display"]
        push_text_list = [
            self.empty_annotation,
            self.empty_annotation,
            "Nb: %d" % nb_annot,
            "",
            "On"
        ]

        for ite_button, (text, label) in enumerate(zip(
            button_text_list, push_text_list
        )):
            # add push button
            push_button = pyqt_overlayer.add_push_button(
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
        _, _, self.button_group_radio_disp = \
            pyqt_overlayer.add_widget_button_group(
                grid, (2 + ite_button, 0, 1, 2),
                ["Current label", "All labels", "Custom (below)"],
                box_title="Display mode"
            )

        # create check boxes with labels
        _, _, self.button_group_check_custom = \
            pyqt_overlayer.add_widget_button_group(
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


    def get_path(self, label):
        """
        Gets path to the annotation file corresponding to the input label

        :param label: events annotation label
        :type label: str

        :returns: path
        :rtype: str
        """

        return '%s/%s_%s-datetime.txt' % (
            self.annot_dir, self.file_name_base, label
        )


    def create_annot_duration(self, visi):
        """
        Creates annotation events files for the duration of each file of the
        reference modality (only one file if not a long recording)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # get path to annotation file
        output_path = self.get_path(self.protected_label)

        # check if annotation file does not exist
        if not isfile(output_path):
            # check if long recording in ViSiAnnoT
            if visi.flag_long_rec:
                with open(output_path, 'w') as f:
                    # loop on beginning datetime and duration of reference
                    # modality files in the long recording
                    for beg_datetime, duration in zip(
                        visi.ref_beg_datetime_list,
                        visi.ref_duration_list
                    ):
                        # get end datetime
                        end_datetime = beg_datetime + timedelta(
                            seconds=duration
                        )

                        # convert datetime to string
                        beg_string = beg_datetime.strftime(
                            self.timestamp_format
                        )

                        end_string = end_datetime.strftime(
                            self.timestamp_format
                        )

                        # write annotation file
                        f.write("%s - %s\n" % (beg_string, end_string))

            # not a long recording
            else:
                with open(output_path, 'w') as f:
                    # get end datetime
                    end_datetime = visi.beginning_datetime + timedelta(
                        seconds=visi.nframes / visi.fps
                    )

                    # convert datetime to string
                    beg_string = visi.beginning_datetime.strftime(
                        self.timestamp_format
                    )

                    end_string = end_datetime.strftime(self.timestamp_format)

                    # write annotation file
                    f.write("%s - %s\n" % (beg_string, end_string))


    def call_radio(self, ev, visi):
        """
        Callback method for changing label

        Connected to the signal ``buttonClicked`` of
        :attr:`.button_group_radio_label`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param ev: radio button that has been clicked
        :type ev: QtWidgets.QRadioButton
        """

        # get the new annotation file name
        self.change_label(visi, ev.text())


    def change_label(self, visi, new_label):
        """
        Changes label and loads corresponding annotation file

        It sets the value of the following attributes:

        - :attr:`.current_label_id` with the index of the new label in
          :attr:`.label_list`
        - :attr:`.path` with the new annotation file path (by
          calling :meth:`.get_path`)

        It also manages the display of the annotations.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param new_label: new annotation label
        :type new_label: str
        """

        # update current label
        self.current_label_id = self.label_list.index(new_label)

        # get the new annotation file name
        self.path = self.get_path(new_label)

        # get number of annotation already stored
        if isfile(self.path):
            nb_annot = len(get_txt_lines(self.path))

        else:
            nb_annot = 0

        # update label with the number of annotations
        self.push_text_list[2].setText("Nb: %d" % nb_annot)

        # update label with the start timestamp
        if self.annot_array[self.current_label_id, 0] == 0:
            self.push_text_list[0].setText(self.empty_annotation)

        else:
            self.push_text_list[0].setText(
                self.annot_array[self.current_label_id, 0]
            )

        # update label with end timestamp
        if self.annot_array[self.current_label_id, 1] == 0:
            self.push_text_list[1].setText(self.empty_annotation)

        else:
            self.push_text_list[1].setText(
                self.annot_array[self.current_label_id, 1]
            )

        # plot annotations
        self.plot_regions(visi)


    def get_annot_id_from_position(self, visi, position):
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
        if isfile(self.path):
            # convert mouse position to datetime
            position_date_time = \
                datetime_converter.convert_frame_to_absolute_datetime(
                    position, visi.fps, visi.beginning_datetime
                )

            # get annotations for current label
            lines = get_txt_lines(self.path)

            # loop on annotations
            for ite_annot, line in enumerate(lines):
                # get annotation
                line = line.replace("\n", "")

                start_datetime = datetime_converter.convert_string_to_datetime(
                    line.split(" - ")[0], self.timestamp_format,
                    time_zone=visi.time_zone
                )

                end_datetime = datetime_converter.convert_string_to_datetime(
                    line.split(" - ")[1], self.timestamp_format,
                    time_zone=visi.time_zone
                )

                diff_start = (
                    position_date_time - start_datetime
                ).total_seconds()

                diff_end = (
                    end_datetime - position_date_time
                ).total_seconds()

                # check if mouse position is in the annotation interval
                if diff_start >= 0 and diff_end >= 0:
                    annot_id = ite_annot
                    break

        return annot_id


    def call_push_button(self, button_id, visi):
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
            self.set_timestamp(visi, visi.frame_id, 0)

        # set ending time of the annotated interval
        elif button_id == 1:
            self.set_timestamp(visi, visi.frame_id, 1)

        # add the annotated interval to the annotation file
        elif button_id == 2:
            self.add(visi)

        # delete last annotation
        elif button_id == 3:
            # check if annotation file exists and annotation file is not empty
            if isfile(self.path) and \
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


    def set_timestamp(self, visi, frame_id, annot_position):
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
            # set timestamp
            self.annot_array[self.current_label_id, annot_position] = \
                datetime_converter.convert_frame_to_absolute_datetime_string(
                    frame_id, visi.fps, visi.beginning_datetime,
                    self.timestamp_format
            )

            # display the beginning time of the annotated interval
            self.push_text_list[annot_position].setText(
                self.annot_array[self.current_label_id, annot_position]
            )


    def reset_timestamp(self):
        """
        Resets the timestamps of the current unsaved annotation for the current
        label

        It sets ``self.annot_array[self.current_label_id]`` to zeros.
        """

        # reset the beginning and ending times of the annotated interval
        self.annot_array[self.current_label_id] = np.zeros((2,))

        # reset the displayed beginning and ending times of the annotated
        # interval
        self.push_text_list[0].setText(self.empty_annotation)
        self.push_text_list[1].setText(self.empty_annotation)


    def add(self, visi):
        """
        Adds an annotation to the current label

        It sets the attribute :attr:`.path`.

        If the annotation start timestamp or end timestamp is not defined, then
        nothing happens.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # check if start timestamp or end timestamp of the annotated interval
        # is empty
        if np.count_nonzero(self.annot_array[self.current_label_id]) < 2:
            print("Empty annotation !!! Cannot write file.")

        # otherwise all good
        else:
            # convert timestamps to datetime
            annot_datetime_0 = datetime_converter.convert_string_to_datetime(
                self.annot_array[self.current_label_id, 0],
                self.timestamp_format, time_zone=visi.time_zone
            )

            annot_datetime_1 = datetime_converter.convert_string_to_datetime(
                self.annot_array[self.current_label_id, 1],
                self.timestamp_format, time_zone=visi.time_zone
            )

            # check if annotation must be reversed
            if (annot_datetime_1 - annot_datetime_0).total_seconds() < 0:
                self.annot_array[self.current_label_id, [0, 1]] = \
                    self.annot_array[self.current_label_id, [1, 0]]

            # initialize boolean to specify if annotation must be saved
            flag_ok = True

            # check if annotations overlap disabled
            if not self.flag_annot_overlap:
                # check if annotation overlaps with previous annotations
                if isfile(self.path):
                    flag_ok = self.check_overlap(
                        self.path, annot_datetime_0, annot_datetime_1,
                        time_zone=visi.time_zone
                    )

            # check if annotation must be saved
            if flag_ok:
                with open(self.path, 'a') as file:
                    file.write("%s - %s\n" % (
                        self.annot_array[self.current_label_id, 0],
                        self.annot_array[self.current_label_id, 1]
                    ))

                # update the number of annotations
                nb_annot = int(
                    self.push_text_list[2].text().split(': ')[1]
                ) + 1

                self.push_text_list[2].setText("Nb: %d" % nb_annot)

                # if display mode is on, display the appended interval
                if self.push_text_list[3].text() == "On" and \
                        self.current_label_id in self.region_dict.keys():
                    region_list = self.add_region(
                        visi,
                        self.annot_array[self.current_label_id, 0],
                        self.annot_array[self.current_label_id, 1],
                        color=self.color_list[self.current_label_id]
                    )

                    self.region_dict[self.current_label_id].append(region_list)

            else:
                print(
                    "Cannot save annotation because it overlaps with an "
                    "existing annotation"
                )

            # reset the beginning and ending times of the annotated
            # interval
            self.reset_timestamp()


    def check_overlap(
        self, annot_path, annot_datetime_0, annot_datetime_1, **kwargs
    ):
        # get existing annotations
        annot_array_total = np.loadtxt(
            annot_path, dtype=str, delimiter=" - ", ndmin=2
        ).flatten()

        # loop on current annotation boundaries
        diff_array = np.empty((0, len(annot_array_total)))
        for annot_bound in [annot_datetime_0, annot_datetime_1]:
            # compute difference with boundaries of existing annotations
            diff_array_tmp = np.array([(
                datetime_converter.convert_string_to_datetime(
                    d, self.timestamp_format, **kwargs) - annot_bound
            ).total_seconds() for d in annot_array_total])

            # binarize difference array
            diff_array = np.concatenate((
                diff_array, np.where(diff_array_tmp > 0, 1, 0)[None, :]
            ))

        # check if no overlap
        if np.sum(np.diff(diff_array, axis=0)) == 0:
            return True

        else:
            return False


    def delete(self, visi, annot_id):
        """
        Deletes a specific annotation for the current label

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param annot_id: index of the annotation to delete
        :type annot_id: int
        """

        # read annotation file lines
        lines = get_txt_lines(self.path)

        # remove line of the annotation
        del lines[annot_id]

        # rewrite annotation file
        with open(self.path, 'w') as file:
            file.writelines(lines)

        # update number of annotations
        nb_annot = max(
            0, int(self.push_text_list[2].text().split(': ')[1]) - 1
        )

        self.push_text_list[2].setText("Nb: %d" % nb_annot)

        # delete annotation description if necessary
        if self.current_label_id in self.description_dict.keys():
            description_dict = self.description_dict[self.current_label_id]

            if annot_id in description_dict.keys():
                remove_item_in_widgets(
                    visi.wid_sig_list, description_dict[annot_id]
                )

                del description_dict[annot_id]

            elif annot_id == -1 and nb_annot in description_dict.keys():
                remove_item_in_widgets(
                    visi.wid_sig_list, description_dict[nb_annot]
                )

                del description_dict[nb_annot]

        # if display mode is on, remove the deleted annotation
        if self.push_text_list[3].text() == "On":
            visi.remove_region_in_widgets(
                self.region_dict[self.current_label_id][annot_id]
            )

            del self.region_dict[self.current_label_id][annot_id]


    def delete_clicked(self, visi, position):
        """
        Deletes an annotion that is clicked on

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param position: frame number (sampled at the reference frequency
            :attr:`.ViSiAnnoT.fps`) corresponding to the mouse position on the
            X axis of the signal widgets
        :type position: int
        """

        # get annotated event ID
        annot_id = self.get_annot_id_from_position(visi, position)

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


    def plot_regions(self, visi):
        """
        Plots events annotations, depending on the display mode selected with
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
                    self.clear_regions_single_label(visi, label_id)

            # loop on labels to plot
            for label_id, color in plot_dict.items():
                # check if label not already displayed
                if label_id not in self.region_dict.keys():
                    # get annotation path
                    label = self.label_list[label_id]
                    annot_path = self.get_path(label)

                    # initialize list of region items for the label
                    region_annotation_list = []

                    # check if annotation file exists
                    if isfile(annot_path):
                        # read annotation file
                        lines = get_txt_lines(annot_path)

                        # loop on annotations
                        for annot_line in lines:
                            # display region
                            annot_line_content = annot_line.split(' - ')

                            region_list = self.add_region(
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
                            visi.add_item_to_signals(description_list)


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
            self.plot_regions(visi)

        # display mode is on, put it off
        else:
            self.clear_regions(visi)

            # notify that display mode is now off
            self.push_text_list[3].setText("Off")


    def clear_regions(self, visi):
        """
        Clears the display of annotations for all labels (but does not
        delete the annotations)

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        # loop on labels
        for label_id in range(len(self.label_list)):
            self.clear_regions_single_label(visi, label_id)


    def clear_regions_single_label(self, visi, label_id):
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
                visi.remove_region_in_widgets(region_list)
            del self.region_dict[label_id]

        # clear descriptions display
        if label_id in self.description_dict:
            for description_list in \
                    self.description_dict[label_id].values():
                remove_item_in_widgets(
                    visi.wid_sig_list, description_list
                )


    def add_region(self, visi, bound_1, bound_2, **kwargs):
        """
        Displays a region in the progress bar and the signal widgets

        It converts the bounds to frame numbers and then calls the
        method :meth:`.ViSiAnnoT.add_region_to_widgets`.

        :param visi: associated instance of :class:`.ViSiAnnoT`
        :param bound_1: start datetime of the region
        :type bound_1: str
        :param bound_2: end datetime of the region
        :type bound_2: str
        :param kwargs: keyword arguments of
            :meth:`.ViSiAnnoT.add_region_to_widgets`
        """

        # convert bounds to frame numbers
        frame_1 = datetime_converter.convert_absolute_datetime_string_to_frame(
            visi.fps, visi.beginning_datetime, bound_1, self.timestamp_format,
            time_zone=visi.time_zone
        )

        frame_2 = datetime_converter.convert_absolute_datetime_string_to_frame(
            visi.fps, visi.beginning_datetime, bound_2, self.timestamp_format,
            time_zone=visi.time_zone
        )

        # check date-time (useful for longRec)
        if frame_1 >= 0 and frame_1 < visi.nframes \
            or frame_2 >= 0 and frame_2 < visi.nframes \
                or frame_1 < 0 and frame_2 >= visi.nframes:
            # display region in each signal plot
            region_list = visi.add_region_to_widgets(
                frame_1, frame_2, **kwargs
            )

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
        annot_id = self.get_annot_id_from_position(visi, pos_frame)

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
                remove_item_in_widgets(
                    visi.wid_sig_list, description_dict[annot_id]
                )

                # delete list of description text items from dictionary
                del description_dict[annot_id]

            else:
                # get list of Y position of the mouse in each signal widget
                pos_y_list = visi.get_mouse_y_position(ev)

                # get date-time string annotation
                annot = get_txt_lines(self.path)[annot_id]

                # get date-time start/stop of the annotation
                start, stop = annot.replace("\n", "").split(" - ")

                # convert date-time string to datetime
                start = datetime_converter.convert_string_to_datetime(
                    start, self.timestamp_format, time_zone=visi.time_zone
                )

                stop = datetime_converter.convert_string_to_datetime(
                    stop, self.timestamp_format, time_zone=visi.time_zone
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
                    visi.create_text_item(
                        description, pos_ms, pos_y_list, border_color=color
                )


    def clear_descriptions(self, visi):
        """
        Clears the display of all the annotations descriptions

        :param visi: associated instance of :class:`.ViSiAnnoT`
        """

        for description_dict in self.description_dict.values():
            for description_list in description_dict.values():
                remove_item_in_widgets(visi.wid_sig_list, description_list)

        self.description_dict = {}


    # *********************************************************************** #
    # End group
    # *********************************************************************** #
