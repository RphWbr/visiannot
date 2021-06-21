# -*- coding: utf-8 -*-

from visiannot.visiannot import ViSiAnnoTLongRecFromConfigGUI
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

    args = parser.parse_known_args()
    config_path = abspath(args[0].config_path)

    ####################
    # launch ViSiAnnoT #
    ####################
    win_visiannot = ViSiAnnoTLongRecFromConfigGUI(path=config_path)
