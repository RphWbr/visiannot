# -*- coding: utf-8 -*-

from visiannot.visiannot import ViSiAnnoTLongRecFromConfigGUI, ViSiAnnoTLongRecFromConfigFile
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
        "-fcg",
        type=int,
        help="boolean (0 or 1) to specify if configuration GUI must be launched, default 1",
        default=1
    )

    args = parser.parse_known_args()
    config_path = abspath(args[0].config_path)
    flag_config_gui = args[0].flag_config_gui

    ####################
    # launch ViSiAnnoT #
    ####################

    if flag_config_gui:
        win_visiannot = ViSiAnnoTLongRecFromConfigGUI(path=config_path)

    else:
        win_visiannot = ViSiAnnoTLongRecFromConfigFile(config_path)
