# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 12:24:46 2019

@author: David
"""


import ephem
import sys
import logging
import importlib

from mats_planningtool.Library import scheduler
from mats_planningtool import Globals

Logger = logging.getLogger("OPT_logger")


def Mode131(Occupied_Timeline, configFile):
    """Core function for the scheduling of Mode131.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Timeline_settings = configFile.Timeline_settings()
    Settings = configFile.Mode131_settings()

    "Get the initially planned date"
    if Settings["start_date"] != "0":
        initialDate = ephem.Date(Settings["start_date"])
        Logger.info("Mode specific start_date used as initial date")
    else:
        Logger.info("Timeline start_date used as initial date")
        initialDate = ephem.Date(Timeline_settings["start_date"])

    endDate = ephem.Date(
        initialDate
        + ephem.second
        * (Settings["mode_duration"] + Timeline_settings["mode_separation"])
    )

    ############### Start of availability schedueler ##########################

    startDate, endDate, iterations = scheduler(Occupied_Timeline, initialDate, endDate)

    ############### End of availability schedueler ##########################

    comment = "Number of times date postponed: " + str(iterations)

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(0).f_code.co_name

    Occupied_Timeline[Mode_name].append((startDate, endDate))

    return Occupied_Timeline, comment
