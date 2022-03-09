# -*- coding: utf-8 -*-
"""Schedules the active Mode and saves the result in the Occupied_Timeline dictionary.

Part of Timeline_generator, as part of OPT.

"""

import ephem
import sys
import logging
import importlib
import datetime as DT

from mats_planningtool.Library import scheduler

Logger = logging.getLogger("OPT_logger")


def Mode132(Occupied_Timeline, configFile):
    """Core function for the scheduling of Mode132.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Timeline_settings = configFile.Timeline_settings()
    Settings = configFile.Mode132_settings()

    "Get the initially planned date"
    if Settings["start_date"] != "0":
        initialDate = DT.datetime.strptime(Settings["start_date"],'%Y/%m/%d %H:%M:%S')
        Logger.info("Mode specific start_date used as initial date")
    else:
        initialDate = initialDate = DT.datetime.strptime(Timeline_settings["start_date"],'%Y/%m/%d %H:%M:%S')
        Logger.info("Timeline start_date used as initial date")

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
    endDate = initialDate + DT.timedelta(seconds = duration + Timeline_settings["mode_separation"])

    ############### Start of availability schedueler ##########################

    startDate, endDate, iterations = scheduler(Occupied_Timeline, initialDate, endDate)

    ############### End of availability schedueler ##########################

    comment = "Number of times date postponed: " + str(iterations)

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(0).f_code.co_name

    Occupied_Timeline[Mode_name].append((startDate, endDate))

    return Occupied_Timeline, comment
