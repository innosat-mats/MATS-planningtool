# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 11:51:44 2019

@author: David
"""

import importlib


from .Mode12X import date_calculator, date_select, UserProvidedDateScheduler


def Mode123(Occupied_Timeline, configFile):
    """Core function for the scheduling of Mode121.

    Determines if the scheduled date should be determined by simulating MATS or be user provided.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """
    Settings = configFile.Mode123_settings()

    if(Settings['automatic'] == False):
        Occupied_Timeline, comment = UserProvidedDateScheduler(
            Occupied_Timeline, Settings, configFile)
    elif(Settings['automatic'] == True):
        date_magnitude_array = date_calculator(Settings, configFile)

        Occupied_Timeline, comment = date_select(
            Occupied_Timeline, date_magnitude_array, Settings, configFile)

    return Occupied_Timeline, comment
