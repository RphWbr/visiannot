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
from pkgutil import iter_modules


def findFunctionRecursive(package_name, function_name):
    """
    Finds a particular function by its name in a package or module

    It reaches all sub-packages and sub-modules recursively.

    :param package_name: name of the package or module where to look,
        it might be a sub-package or a sub-module with the absolute name
        (e.g. ``"pkg.sub1.sub2.moduleA"``)
    :type package_name: str
    :param function_name: name of the function to look for
    :type function_name: str

    :returns: function, None if not found
    """

    # initialize member
    member = None

    # importing (sub-)package/module may fail in some cases
    try:
        # import package/module
        package = import_module(package_name)

        # initialize boolean to specify if member found
        flag_ok = False

        # check if member is in module
        if hasattr(package, function_name):
            # get member
            member_tmp = getattr(package, function_name)

            # check if member has the specified type and that it is defined in
            # the current module
            if isfunction(member_tmp) and \
                    package.__name__ == member_tmp.__module__:
                flag_ok = True
                member = member_tmp

        # check if member not found in the current package/module
        if not flag_ok:
            # check if package
            if hasattr(package, "__path__"):
                # loop on sub-packages and sub-modules
                for info in iter_modules(package.__path__):
                    # get sub-package (or sub-module) name
                    subpackage_name = "%s.%s" % (package_name, info.name)

                    # recursive call
                    member = findFunctionRecursive(
                        subpackage_name, function_name
                    )

                    # check if member found
                    if member is not None:
                        break

    except Exception:
        print(
            "Could not import package/module %s in findFunctionRecursive" %
            package_name
        )

    return member


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
        help="specify if configuration GUI must be launched",
        default=0
    )

    parser.add_argument(
        "--no-visi-gui",
        "-m",
        action="store",
        nargs='?',
        help="specify if ViSiAnnoT GUI must be launched",
        default=0
    )

    parser.add_argument(
        "--config-update-function",
        "-u",
        type=str,
        help="name of a function to call before launching ViSiAnnoT (one positional argument: configuration path / returns updated configuration dictionary), module_name.function_name or package_name.subpackage_name.function.name",
        default=''
    )

    args = parser.parse_known_args()
    config_path = abspath(args[0].config_path)
    no_config_gui = args[0].no_config_gui
    no_visi_gui = args[0].no_visi_gui
    config_update_function = args[0].config_update_function

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

        # find function
        config_update_function = findFunctionRecursive(
            package_name, function_name
        )

        # check if function found
        if config_update_function is not None:
            # update configuration dictionary
            config_path = config_update_function(config_path)

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
