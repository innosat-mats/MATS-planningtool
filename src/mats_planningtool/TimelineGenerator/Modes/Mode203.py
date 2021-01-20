# -*- coding: utf-8 -*-
"""Schedules the active Mode and saves the result in the Occupied_Timeline dictionary.

Part of Timeline_generator, as part of OPT.

"""


import ephem
import sys
import logging
import importlib

from mats_planningtool.Library import scheduler
from mats_planningtool import Globals

OPT_Config_File = importlib.import_module(Globals.Config_File)
Logger = logging.getLogger(OPT_Config_File.Logger_name())


def Mode203(Occupied_Timeline):

    initial_date = date_calculator()

    Occupied_Timeline, comment = date_select(Occupied_Timeline, initial_date)

    return Occupied_Timeline, comment


##################################################################################################
##################################################################################################


def date_calculator():

    try:
        initial_date = Mode = X = _settings()["start_time"]
        Logger.info("Mode specific start_time used as initial date")
    except:
        Logger.warning(
            "!!Error raised in try statement!! Could not use Mode specific start_time; Timeline start_time used as initial date"
        )
        initial_date = OPT_Config_File.Timeline_settings()["start_time"]

    return initial_date


##################################################################################################
##################################################################################################


def date_select(Occupied_Timeline, initial_date):

    date = initial_date

    try:
        Logger.info("Mode specific mode_duration used as initial date")
        endDate = ephem.Date(
            initial_date
            + ephem.second * OPT_Config_File.Timeline_settings()["mode_separation"]
            + ephem.second * Mode203_settings()["mode_duration"]
        )
    except:
        Logger.info("Mode 203 does not exist")
        Logger.info("Timeline mode_duration used as initial date")
        endDate = ephem.Date(
            initial_date
            + ephem.second * OPT_Config_File.Timeline_settings()["mode_separation"]
            + ephem.second * OPT_Config_File.Timeline_settings()["mode_duration"]
        )

    ############### Start of availability schedueler ##########################

    date, endDate, iterations = scheduler(Occupied_Timeline, date, endDate)

    ############### End of availability schedueler ##########################

    comment = "Number of times date postponed: " + str(iterations)

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(1).f_code.co_name

    Occupied_Timeline[Mode_name].append((date, endDate))

    return Occupied_Timeline, comment
