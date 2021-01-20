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


def Mode133(Occupied_Timeline):
    """Core function for the scheduling of Mode133.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Timeline_settings = OPT_Config_File.Timeline_settings()
    Settings = OPT_Config_File.Mode133_settings()

    "Get the initially planned date"
    if Settings["start_date"] != "0":
        initialDate = ephem.Date(Settings["start_date"])
        Logger.info("Mode specific start_date used as initial date")
    else:
        Logger.info("Timeline start_date used as initial date")
        initialDate = ephem.Date(Timeline_settings["start_date"])

    NumberOfCMDsPerAltitude = 12

    if len(Settings["Exp_Times_UV"]) <= len(Settings["Exp_Times_IR"]):
        duration = (
            Settings["session_duration"]
            + Timeline_settings["CMD_separation"] * NumberOfCMDsPerAltitude
            + Timeline_settings["pointing_stabilization"]
        ) * len(Settings["Exp_Times_UV"])
    elif len(Settings["Exp_Times_IR"]) < len(Settings["Exp_Times_UV"]):
        duration = (
            Settings["session_duration"]
            + Timeline_settings["CMD_separation"] * NumberOfCMDsPerAltitude
            + Timeline_settings["pointing_stabilization"]
        ) * len(Settings["Exp_Times_IR"])

    """
    NumberOfCMDStepsInMacro = 12
    
    if( len(Settings['Exp_Times_UV']) <= len(Settings['Exp_Times_IR'])):
        duration = ( Settings['session_duration']+ NumberOfCMDStepsInMacro * Timeline_settings['CMD_separation'] ) * len(Settings['Exp_Times_UV'])+Timeline_settings['pointing_stabilization'] + Timeline_settings['mode_separation']
    elif( len(Settings['Exp_Times_IR']) < len(Settings['Exp_Times_UV']) ):
        duration = ( Settings['session_duration']+ NumberOfCMDStepsInMacro * Timeline_settings['CMD_separation'] ) * len(Settings['Exp_Times_IR'])+Timeline_settings['pointing_stabilization'] + Timeline_settings['mode_separation']
    
    """

    endDate = ephem.Date(
        initialDate + ephem.second * (duration + Timeline_settings["mode_separation"])
    )

    ############### Start of availability schedueler ##########################

    startDate, endDate, iterations = scheduler(Occupied_Timeline, initialDate, endDate)

    ############### End of availability schedueler ##########################

    comment = "Number of times date postponed: " + str(iterations)

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(0).f_code.co_name

    Occupied_Timeline[Mode_name].append((startDate, endDate))

    return Occupied_Timeline, comment
