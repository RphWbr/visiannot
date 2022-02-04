# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining classes for creating pop-up windows in help menu bar
"""


from ...tools import pyqt_overlayer
from ...tools import pyqtgraph_overlayer
from ...tools.video_loader import read_image
from ...tools.data_loader import get_working_directory
from PyQt5.QtWidgets import QLabel, QWidget, QGridLayout
from PyQt5.QtCore import Qt
from importlib import import_module
from datetime import datetime


class WindowPopUp(QWidget):
    def __init__(self, title, width, height):
        """
        Base class for creating a pop-up window

        This is used for pop-up windows of the help menu in the menu bar of
        :class:`.ViSiAnnoT`.

        :param title: window title
        :type title: str
        :param width: window width in pixels
        :type width: int
        :param height: window height in pixels
        :type height: int
        """

        # create window
        QWidget.__init__(self)

        # create layout
        self.lay = QGridLayout(self)

        # set window title
        self.setWindowTitle(title)

        # set window size
        self.resize(width, height)


    def addLabel(self, text, pos, alignment=None, scroll_lay=None):
        """
        Adds a label in the layout of the pop-up window

        :param text: text of the label, it may be html
        :type text: str
        :param pos: position of the label in the layout, length 2
            ``(row, col)`` or 4 ``(row, col, rowspan, colspan)``
        :type pos: tuple
        :param alignment: constant defining the label alignment, see
            https://doc.qt.io/qt-5/qt.html#AlignmentFlag-enum
        :param scroll_lay: layout filling the scroll that must contain the
            label
        :type scroll_lay: QtWidgets.QGridLayout
        """

        # create label
        label = QLabel(text)

        # check if alignment to be set
        if alignment is not None:
            label.setAlignment(alignment)

        # add label to pop-up window layout
        pyqt_overlayer.add_widget_to_layout(self.lay, label, pos)

        # check if label to be added to scroll area
        if scroll_lay is not None:
            scroll_lay.addWidget(label)


class WindowAbout(WindowPopUp):
    def __init__(self):
        """
        Pop-up window with information about **ViSiAnnoT**
        """

        # call base class constructor
        WindowPopUp.__init__(self, "About ViSiAnnoT", 550, 300)

        # create scroll area
        scroll_lay, _ = pyqt_overlayer.add_scroll_area(self.lay, (0, 0))

        # title label
        text_title = "<b style='font-size:35px;'><u>ViSiAnnoT</u></b>"
        self.addLabel(
            text_title, (0, 0), alignment=Qt.AlignCenter, scroll_lay=scroll_lay
        )

        # acknowledgement label
        text_acknowledgement = """
            <p><b><u>Acknowledgement:</b></u> The initial development of\
            <b>ViSiAnnoT</b> was<br>
            made possible by a funding from the European Union’s Horizon<br>
            2020 research and innovation programme under grant<br>
            agreement No 689260 (Digi-NewB project).</p>
        """
        self.addLabel(text_acknowledgement, (1, 0), scroll_lay=scroll_lay)

        # load Digi-NewB logo
        dir_path = get_working_directory(__file__)
        logo_im = read_image('%s/Images/DIGI-NEWB.jpg' % dir_path)

        # add logo to layout
        logo_plot = pyqtgraph_overlayer.create_widget_logo(
            self.lay, (2, 0), logo_im
        )

        # add logo scroll area
        scroll_lay.addWidget(logo_plot)

        # copyright label
        text_copyright = "© 2018-%s Université Rennes 1 / Raphaël Weber" % \
            datetime.today().year
        self.addLabel(
            text_copyright, (3, 0), alignment=Qt.AlignCenter,
            scroll_lay=scroll_lay
        )

        # get ViSiAnnoT version
        version = import_module("visiannot").__version__

        # version label
        text_version = "Version %s" % version
        self.addLabel(
            text_version, (4, 0), alignment=Qt.AlignCenter,
            scroll_lay=scroll_lay
        )


class WindowLicense(WindowPopUp):
    def __init__(self):
        """
        Pop-up window with **ViSiAnnoT** License
        """

        # call base class constructor
        WindowPopUp.__init__(self, "ViSiAnnoT license", 600, 500)

        # create scroll area
        scroll_lay, _ = pyqt_overlayer.add_scroll_area(self.lay, (0, 0))

        # license label
        license_text = """
            Copyright Université Rennes 1 / INSERM (2018)
            Contributor: Raphaël Weber

            raphael.weber@univ-rennes1.fr

            This software is a computer program whose purpose is to provide a
            graphical user interface for the visualization and annotation of
            video and signal data.

            This software is governed by the CeCILL license under French law
            and abiding by the rules of distribution of free software. You can
            use, modify and/or redistribute the software under the terms of the
            CeCILL license as circulated by CEA, CNRS and INRIA at the
            following URL "http://www.cecill.info".

            As a counterpart to the access to the source code and rights to
            copy, modify and redistribute granted by the license, users are
            provided only with a limited warranty and the software's author,
            the holder of the economic rights, and the successive licensors
            have only limited liability.

            In this respect, the user's attention is drawn to the risks
            associated with loading, using, modifying and/or developing or
            reproducing the software by the user in light of its specific
            status of free software, that may mean that it is complicated to
            manipulate,  and that also therefore means that it is reserved for
            developers and experienced professionals having in-depth computer
            knowledge. Users are therefore encouraged to load and test the
            software's suitability as regards their requirements in conditions
            enabling the security of their systems and/or data to be ensured
            and, more generally, to use and operate it in the same conditions
            as regards security.

            The fact that you are presently reading this means that you have
            had knowledge of the CeCILL license and that you accept its terms.
        """

        self.addLabel(license_text, (0, 0), scroll_lay=scroll_lay)
