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
from inspect import isfunction
from importlib import import_module


if __name__ == '__main__':
    #############
    # arguments #
    #############
    parser = ArgumentParser()

    parser.add_argument(
        "--config-path",
        "-c",
        type=str,
        help="path to the configuration file, default ''",
        default=''
    )

    parser.add_argument(
        "--no-config-gui",
        "-n",
        action="store",
        nargs='?',
        help="specify if configuration GUI must not be launched",
        default=0
    )

    parser.add_argument(
        "--no-visi-gui",
        "-m",
        action="store",
        nargs='?',
        help="specify if ViSiAnnoT GUI must not be launched",
        default=0
    )

    parser.add_argument(
        "--config-update-function",
        "-u",
        type=str,
        help="name of a function to call before launching ViSiAnnoT (one "
        "positional argument: configuration path / returns updated "
        "configuration dictionary), module_name.function_name or "
        "package_name.subpackage_name.function_name",
        default=''
    )

    args, _ = parser.parse_known_args()
    config_path = abspath(args.config_path)
    no_config_gui = args.no_config_gui
    no_visi_gui = args.no_visi_gui
    config_update_function = args.config_update_function

    ####################
    # launch ViSiAnnoT #
    ####################

    # check if calling function before launching ViSiAnnoT
    if config_update_function != '':
        # get name of package/module and path/name of function in
        # package/module
        config_update_function_name_split = \
            config_update_function.split('.')
        package_name = '.'.join(config_update_function_name_split[:-1])
        function_name = config_update_function_name_split[-1]

        # import package
        try:
            package = import_module(package_name)
            if hasattr(package, function_name):
                # get member
                function = getattr(package, function_name)

                # check if function ideed
                if isfunction(function):
                    # update configuration dictionary
                    config_path = function(config_path)

                else:
                    print("Member %s found in %s, but not a function" % (
                        function_name, package_name
                    ))

            else:
                print("Function %s not found in %s" % (
                    function_name, package_name
                ))

        except Exception:
            print("Could not import package/module %s" % package_name)

    # check if configuration GUI
    if no_config_gui is not None:
        # check if ViSiAnnoT GUI
        if no_visi_gui is not None:
            win_visi = ViSiAnnoTLongRecFromConfigGUI(path=config_path)

        else:
            # only configuration GUI
            win_config = ConfigurationWindow(path=config_path)

    elif no_visi_gui is not None:
        # only ViSiAnnoT GUI
        win_visi = ViSiAnnoTLongRecFromConfigFile(config_path)

    else:
        print("Nothing to do!")
