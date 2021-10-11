# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

from visiannot.visiannot import ViSiAnnoTLongRecFromConfigFile, \
    ViSiAnnoTLongRecFromConfigGUI
from visiannot.configuration import ConfigurationWindow
from argparse import ArgumentParser
from os.path import abspath

if __name__ == '__main__':
    #############
    # arguments #
    #############
    parser = ArgumentParser()

    parser.add_argument(
        "--config_path",
        "-conf",
        type=str,
        help="path to the configuration file, default ''",
        default=''
    )

    parser.add_argument(
        "--flag_config_gui",
        "-fconf",
        type=int,
        help="boolean (0 or 1) to specify if configuration GUI must be launched, default 1",
        default=1
    )

    parser.add_argument(
        "--flag_visi_gui",
        "-fvisi",
        type=int,
        help="boolean (0 or 1) to specify if ViSiAnnoT GUI must be launched, default 1",
        default=1
    )

    args = parser.parse_known_args()
    config_path = abspath(args[0].config_path)
    flag_config_gui = args[0].flag_config_gui
    flag_visi_gui = args[0].flag_visi_gui

    ####################
    # launch ViSiAnnoT #
    ####################

    # check if configuration GUI
    if flag_config_gui:
        # check if ViSiAnnoT GUI
        if flag_visi_gui:
            win_visi = ViSiAnnoTLongRecFromConfigGUI(path=config_path)

        else:
            # only configuration GUI
            win_config = ConfigurationWindow(path=config_path)

    elif flag_visi_gui:
        # only ViSiAnnoT GUI
        win_visi = ViSiAnnoTLongRecFromConfigFile(config_path)

    else:
        print("Nothing to do!")
