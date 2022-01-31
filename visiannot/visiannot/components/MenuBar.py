# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.MenuBar`
"""

from . import WindowsPopUp
from PyQt5.QtWidgets import QMenuBar, QAction
import webbrowser


class MenuBar(QMenuBar):
    def __init__(self, win_parent, lay_parent):
        """
        Menu bar item

        :param win_parent: container of the parent window
        :type win_parent: QtWidgets.QWidget
        :param lay_parent: layout of the parent window, where to add the menu
            bar
        :type lay_parent: QtWidgets.QGridLayout

        In order to add a menu or an action, the method
        :meth:`.addMenuAndActions` may be used.
        """

        # call parent class constructor
        QMenuBar.__init__(self, win_parent)

        # add menu bar to parent layout
        lay_parent.setMenuBar(self)

        # hide menu bar
        self.hide()

        #: (*QtWidgets.QWidget*) Container of the parent window
        self.win_parent = win_parent

        #: (:class:`.WindowAbout`) Container of the pop-up window with
        #: information about **ViSiAnnoT**
        self.win_about = WindowsPopUp.WindowAbout()

        #: (:class:`.WindowLicense`) Container of the pop-up window with
        #: **ViSiAnnoT** license
        self.win_license = WindowsPopUp.WindowLicense()

        # add a menu with actions to menu bar
        self.add_menu_with_actions(
            "Help", {
                "Documentation": MenuBar.open_documentation,
                "License": self.win_license.show,
                "About ViSiAnnoT": self.win_about.show
            }
        )


    def add_menu_with_actions(self, menu_name, action_dict):
        """
        Adds menus with actions to menu bar

        :param menu_name: name of the menu to add
        :type menu_name: str
        :param action_dict: actions to add in the menu, each element
            corresponds one action, key is the action name, value is the slot
            method to be called when activating the action
        :type action_dict: dict
        """

        # add menu to menu bar
        menu = self.addMenu(menu_name)

        # loop on actions to add to the menu
        for action_name, slot_method in action_dict.items():
            # create action item
            action = QAction(action_name, self.win_parent)

            # add action to menu
            menu.addAction(action)

            # connect action to slot method
            action.triggered.connect(slot_method)


    @staticmethod
    def open_documentation():
        """
        Static method for launching the default web browser and loading
        **ViSiAnnoT** ReadTheDocs documentation
        """

        url = "https://visiannot.readthedocs.io/en/latest/"
        webbrowser.open(url, new=2)
