# -*- coding: utf-8 -*-
#
# Copyright Université Rennes 1 / INSERM
# Contributor: Raphael Weber
#
# Under CeCILL license
# http://www.cecill.info

"""
Module defining :class:`.ViSiAnnoTLongRecFromConfigFile`
"""


from ..configuration import ConfigurationWindow
from .ViSiAnnoTLongRec import ViSiAnnoTLongRec


class ViSiAnnoTLongRecFromConfigFile(ViSiAnnoTLongRec):
    """
    Subclass of :class:`.ViSiAnnoTLongRec` for launching ViSiAnnoT directly
    from a configuration file

    It calls the method :meth:`.ConfigurationWindow.load_config_file` in order
    to load the configuration file. Then it calls the constructor of
    :class:`.ViSiAnnoTLongRec`.

    :param path_config: path to the configuration file, it may be directly a
        configuration dictionary
    :type path_config: str or dict
    """

    def __init__(self, path_config):
        # check type
        if isinstance(path_config, str):
            # load configuration file
            config_dict = ConfigurationWindow.load_config_file(
                path_config
            )

        else:
            config_dict = path_config

        # get list of positional arguments
        args = []
        for key in ["Video", "Signal"]:
            if key in config_dict.keys():
                args.append(config_dict[key])

            else:
                args.append({})

        # get list of keyword arguments
        kwargs = {}
        for key, kw in [
            ("AnnotEvent", "annotevent_dict"),
            ("AnnotImage", "annotimage_list"),
            ("Threshold", "threshold_dict"),
            ("Interval", "interval_dict"),
            ("YRange", "y_range_dict"),
            ("General", None)
        ]:
            if key in config_dict.keys():
                if kw is None:
                    kwargs.update(config_dict[key])

                else:
                    kwargs.update({kw: config_dict[key]})

        # launch ViSiAnnoT
        ViSiAnnoTLongRec.__init__(self, *args, **kwargs)
