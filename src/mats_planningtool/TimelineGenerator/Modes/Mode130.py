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


def Mode130(Occupied_Timeline):
    """Core function for the scheduling of Mode130.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.
    """

    Timeline_settings = OPT_Config_File.Timeline_settings()
    Settings = OPT_Config_File.Mode130_settings()

    "Get the initially planned date"
    if(Settings['start_date'] != '0'):
        initialDate = ephem.Date(Settings['start_date'])
        Logger.info('Mode specific start_date used as initial date')
    else:
        Logger.info('Timeline start_date used as initial date')
        initialDate = ephem.Date(Timeline_settings['start_date'])

    NumberOfCCDs = 7
    endDate = ephem.Date(initialDate + ephem.second * (Settings['SnapshotSpacing'] * NumberOfCCDs +
                                                       Timeline_settings['pointing_stabilization'] + Timeline_settings['mode_separation']))

    ############### Start of availability schedueler ##########################

    startDate, endDate, iterations = scheduler(Occupied_Timeline, initialDate, endDate)

    ############### End of availability schedueler ##########################

    comment = 'Number of times date postponed: ' + str(iterations)

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(0).f_code.co_name

    Occupied_Timeline[Mode_name].append((startDate, endDate))

    return Occupied_Timeline, comment
