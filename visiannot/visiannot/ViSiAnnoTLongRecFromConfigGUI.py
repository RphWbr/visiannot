# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.ViSiAnnoTLongRecFromConfigGUI`
"""


from ..configuration import ConfigurationWindow
from .ViSiAnnoTLongRecFromConfigFile import ViSiAnnoTLongRecFromConfigFile


class ViSiAnnoTLongRecFromConfigGUI(ViSiAnnoTLongRecFromConfigFile):
    """
    Subclass of :class:`.ViSiAnnoTLongRecFromConfigFile` for launching
    configuration GUI before launching ViSiAnnoT
    """

    def __init__(self):
        # configuration GUI
        win_config = ConfigurationWindow()

        # get configuration dictionaries
        config_dict = {"General": win_config.general_dict}
        for key, config in win_config.meta_dict.items():
            config_dict[key] = config.dict
        
        # launch ViSiAnnoT
        ViSiAnnoTLongRecFromConfigFile.__init__(self, config_dict)
