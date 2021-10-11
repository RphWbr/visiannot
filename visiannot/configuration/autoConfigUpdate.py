# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining functions for updating configuration dictionary before
launching GUI
"""


from .ConfigurationWindow import ConfigurationWindow
from ..tools.ToolsPyQt import getDirectoryDialog
from os.path import basename


def updateDataAndAnnotationDirectory(config_path):
    """
    Opens a dialog window for selecting a directory containing data to display
    in ViSiAnnoT, loads a configuration file and updates configuration
    dictionary with the selected directory

    :param config_path: path to configuration file to load
    :type config_path: str

    The configuration file may contain the key ``data_dir_base`` in the section
    ``General``. Thus, the dialog window opens at the location specified by
    this key.

    Once the data directory is selected, the following field are updated in the
    configuration dictionary:

    - First field of the "Video" and "Signal" sub-configurations (data
      directory)
    - Key ``annot_dir``in section ``General``(annotation directory).

    The annotation directory is updated as follows:
    ``annotBase/recName/patID``, where ``annotBase`` is the initial value of
    the annotation directory in the configuration file, ``recName`` is the
    basename of the selected data directory and
    ``patID = recName.split('_')[0]``.
    """

    # get configuration
    config_dict = ConfigurationWindow.loadConfigFile(config_path)

    # select data directory
    if "data_dir_base" in config_dict["General"].keys():
        data_dir_base = config_dict["General"]["data_dir_base"]
        del config_dict["General"]["data_dir_base"]

    else:
        data_dir_base = None
    
    dir_data = getDirectoryDialog(dir_root=data_dir_base)

    if dir_data == "":
        print("No input directory specified => exit")
        from sys import exit
        exit()

    # set configuration dictionaries
    if "Video" in config_dict.keys():
        for value_list in config_dict["Video"].values():
            value_list[0] = dir_data

    if "Signal" in config_dict.keys():
        for value_list_list in config_dict["Signal"].values():
            for value_list in value_list_list:
                value_list[0] = dir_data

    # get baby id
    rec_name = basename(dir_data)
    bb = rec_name.split("_")[0]
    config_dict["General"]["annot_dir"] = "%s/%s/%s" % (
        config_dict["General"]["annot_dir"], rec_name, bb
    )

    return config_dict
