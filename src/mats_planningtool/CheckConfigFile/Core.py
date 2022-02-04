# -*- coding: utf-8 -*-
"""Created on Tue Jun  4 13:37:48 2019

Checks the values given in the *Configuration File* set by *Set_ConfigFile*.

@author: David Skånberg
"""

import importlib
import logging
import sys
import ephem
from pylab import sign
from math import ceil as ceil

from mats_planningtool import Library

Logger = logging.getLogger("OPT_logger")


def CheckConfigFile(configFile):
    """ Core function of *CheckConfigFile*.

    Checks the values given in the *Configuration File* set by *Set_ConfigFile* and raises an error if any settings are found to be incompatible.
    Also prints out the currently selected *Configuration File* and the starting date and TLE it currently uses.

    """

    Library.SetupLogger(configFile.Logger_name())

    Timeline_settings = configFile.Timeline_settings()
    Operational_Science_Mode_settings = (
        configFile.Operational_Science_Mode_settings()
    )
    # Mode5_settings = configFile.Mode5_settings()
    Mode100_settings = configFile.Mode100_settings()
    Mode110_settings = configFile.Mode110_settings()
    Mode120_settings = configFile.Mode120_settings()
    Mode121_settings = configFile.Mode121_settings()
    Mode122_settings = configFile.Mode122_settings()
    Mode123_settings = configFile.Mode123_settings()
    Mode121_122_123_settings = configFile.Mode121_122_123_settings()
    Mode124_settings = configFile.Mode124_settings()
    Mode130_settings = configFile.Mode130_settings()
    Mode131_settings = configFile.Mode131_settings()
    Mode132_settings = configFile.Mode132_settings()
    Mode133_settings = configFile.Mode133_settings()
    Mode134_settings = configFile.Mode134_settings()

    try:
        Logger.info("Currently used Configuration File: " + configFile.config_file_name)
    except:
        Logger.error(
            "Currently stated Configuration File is invalid. Try running Set_ConfigFile."
        )
        raise ValueError
    try:
        Logger.info("Outputting file to directory: " + configFile.output_dir)
    except:
        Logger.error(
            "Output directory invalid."
        )
        raise ValueError
    
    try:
        Logger.info("Currently used starting date: " + Timeline_settings["start_date"])
    except:
        Logger.error(
            "Currently stated starting date is invalid. Try running Set_ConfigFile."
        )
        raise ValueError
    try:
        Logger.info("Currently used TLE: " + str(configFile.getTLE()))
    except:
        Logger.error("Currently stated TLE is invalid. Try running Set_ConfigFile.")
        raise ValueError

    if not (
        Timeline_settings["duration"]["duration"] > 0 and type(
            Timeline_settings["duration"]["duration"]) == int
    ):
        Logger.error('Timeline_settings["duration"]["duration"]')
        raise ValueError
    if not (
        43099.5 < ephem.Date(Timeline_settings["start_date"]) < 73049.5
        and type(Timeline_settings["start_date"]) == str
    ):
        Logger.error('Timeline_settings["start_date"]')
        raise ValueError
    if not (
        30 <= Timeline_settings["CMD_duration"]
        and type(Timeline_settings["CMD_duration"]) == int
    ):
        Logger.error('Timeline_settings["CMD_duration"]')
        raise ValueError
    if not (
        15 <= Timeline_settings["mode_separation"]
        and type(Timeline_settings["mode_separation"]) == int
    ):
        Logger.error('Timeline_settings["mode_separation"]')
        raise ValueError
    if not (
        1 <= Timeline_settings["CMD_separation"] <= 10
        and (
            type(Timeline_settings["CMD_separation"]) == int
            or type(Timeline_settings["CMD_separation"]) == float
        )
    ):
        Logger.error('Timeline_settings["CMD_separation"]')
        raise ValueError
    # if not( Timeline_settings['CMD_separation'] * 8 <= Timeline_settings['mode_separation'] ):
    #    Logger.error("Timeline_settings['CMD_separation'] * 8 <= Timeline_settings['mode_separation']. Possibility of time separation between CMDs are too large causing CMDs from Science Modes to overlap")
    #    raise ValueError
    if not (
        40 <= Timeline_settings["pointing_stabilization"]
        and type(Timeline_settings["pointing_stabilization"]) == int
    ):
        Logger.error("Timeline_settings['pointing_stabilization']")
        raise ValueError
    if not (
        10000 <= Timeline_settings["StandardPointingAltitude"] <= 300000
        and type(Timeline_settings["StandardPointingAltitude"]) == int
    ):
        Logger.error("Timeline_settings['StandardPointingAltitude']")
        raise ValueError
    if not (
        Timeline_settings["pointing_stabilization"] * 2
        < Timeline_settings["Mode1_2_5_minDuration"]
        and type(Timeline_settings["Mode1_2_5_minDuration"]) == int
    ):
        Logger.error("Timeline_settings['Mode1_2_5_minDuration']")
        raise ValueError
    if not (type(Timeline_settings["yaw_correction"]) == bool):
        Logger.error("Timeline_settings['yaw_correction']")
        raise TypeError
    if not (Timeline_settings["Choose_Operational_Science_Mode"] in [0, 1, 2, 5]):
        Logger.error(
            "Timeline_settings['Choose_Operational_Science_Mode'] != 0, 1, 2, or 5"
        )
        raise ValueError
    if not (
        0 <= abs(Timeline_settings["yaw_amplitude"]) < 20
        and (
            type(Timeline_settings["yaw_amplitude"]) == int
            or type(Timeline_settings["yaw_amplitude"]) == float
        )
    ):
        Logger.error("Timeline_settings['yaw_amplitude']")
        raise ValueError
    if not (
        0 <= abs(Timeline_settings["yaw_phase"])
        and (
            type(Timeline_settings["yaw_phase"]) == int
            or type(Timeline_settings["yaw_phase"]) == float
        )
    ):
        Logger.error("Timeline_settings['yaw_phase']")
        raise ValueError

    for key in Operational_Science_Mode_settings.keys():

        if key == "Choose_Mode5CCDMacro":
            if not (
                Operational_Science_Mode_settings[key]
                in [
                    "CustomBinning",
                    "HighResUV",
                    "HighResIR",
                    "LowPixel",
                    "FullReadout",
                    "BinnedCalibration",
                ]
            ):
                Logger.error(
                    'Operational_Science_Mode_settings["Choose_Mode5CCDMacro"]'
                )
                raise ValueError

        else:
            if key == "timestep":
                if not (Operational_Science_Mode_settings[key] < 50):
                    Logger.error('Operational_Science_Mode_settings["timestep"]')
                    raise ValueError
            elif key == "lat":
                if not (0 <= Operational_Science_Mode_settings[key] <= 90):
                    Logger.error('Operational_Science_Mode_settings["lat"]')
                    raise ValueError
            elif not (
                Operational_Science_Mode_settings[key] > 0
                and type(Operational_Science_Mode_settings[key]) == int
            ):
                Logger.error("Operational_Science_Mode_settings")
                raise ValueError

    # if not( 10000 <= Mode5_settings['pointing_altitude'] <= 300000 and type(Mode5_settings['pointing_altitude']) == int ):
    #    Logger.error("Mode5_settings['pointing_altitude']")
    #    raise ValueError

    if not (
        32 < Mode100_settings["pointing_duration"]
        and type(Mode100_settings["pointing_duration"]) == int
    ):
        Logger.error("Mode100_settings['pointing_duration']")
        raise ValueError
    if not (
        type(Mode100_settings["pointing_altitude_interval"]) == int
        and type(Mode100_settings["pointing_altitude_to"]) == int
        and type(Mode100_settings["pointing_altitude_from"]) == int
    ):
        Logger.error("Mode100_settings")
        raise TypeError
    if not (
        abs(Mode100_settings["pointing_altitude_interval"])
        <= abs(
            Mode100_settings["pointing_altitude_to"]
            - Mode100_settings["pointing_altitude_from"]
        )
    ):
        Logger.error("Mode100_settings['pointing_altitude_interval']")
        raise ValueError
    if not (
        0
        < Mode100_settings["pointing_altitude_interval"]
        * (
            Mode100_settings["pointing_altitude_to"]
            - Mode100_settings["pointing_altitude_from"]
        )
    ):
        Logger.error("Mode100_settings")
        raise ValueError
    if not (type(Mode100_settings["start_date"]) == str):
        Logger.error("Mode100_settings['start_date']")
        raise TypeError
    if not (
        type(Mode100_settings["Exp_Time_IR"]) == int
        and type(Mode100_settings["Exp_Time_UV"]) == int
    ):
        Logger.error(
            "Mode100_settings['Exp_Time_IR'] or Mode100_settings['Exp_Time_UV']"
        )
        raise TypeError
    numberOfAltitudes = int(
        abs(
            Mode100_settings["pointing_altitude_to"]
            - Mode100_settings["pointing_altitude_from"]
        )
        / abs(Mode100_settings["pointing_altitude_interval"])
        + 1
    )
    if not (
        Mode100_settings["Exp_Time_IR"]
        + numberOfAltitudes * Mode100_settings["ExpTime_step"]
        < Mode100_settings["pointing_duration"] * 1000
    ):
        Logger.error("Mode100_settings['pointing_duration']")
        raise ValueError
    if not (
        Mode100_settings["Exp_Time_UV"]
        + numberOfAltitudes * Mode100_settings["ExpTime_step"]
        < Mode100_settings["pointing_duration"] * 1000
    ):
        Logger.error("Mode100_settings['pointing_duration']")
        raise ValueError

    for key in Mode110_settings.keys():

        if key == "start_date":
            if not (type(Mode110_settings[key]) == str):
                Logger.error("Mode110_settings")
                raise ValueError
        elif key == "pointing_altitude_from" or key == "pointing_altitude_to":
            if not (-60000 <= Mode110_settings[key] <= 230000):
                Logger.error("Mode110_settings")
                raise ValueError
        elif key == "sweep_rate":
            if not (
                -5000 <= Mode110_settings[key] <= 5000 and Mode110_settings[key] != 0
            ):
                Logger.error("Mode110_settings")
                raise ValueError
        else:
            if not (Mode110_settings[key] > 0 and type(Mode110_settings[key]) == int):
                Logger.error("Mode110_settings")
                raise ValueError

    if sign(
        Mode110_settings["pointing_altitude_to"]
        - Mode110_settings["pointing_altitude_from"]
    ) != sign(Mode110_settings["sweep_rate"]):
        Logger.error("Mode110_settings")
        raise ValueError

    if not (
        -60000 <= Mode120_settings["pointing_altitude"] <= 230000
        and type(Mode120_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode120_settings['pointing_altitude']")
        raise ValueError
    if not (
        0 < Mode120_settings["timestep"] <= 10
        and type(Mode120_settings["timestep"]) == int
    ):
        Logger.error("Mode120_settings['timestep']")
        raise ValueError
    if not (
        Mode120_settings["freeze_start"]
        >= Timeline_settings["pointing_stabilization"]
        + 12 * Timeline_settings["CMD_separation"]
        and type(Mode120_settings["freeze_start"]) == int
    ):
        Logger.error("Mode120_settings")
        raise TypeError
    if not (type(Mode120_settings["V_offset"]) == list):
        Logger.error("Mode120_settings['V_offset'] != list")
    for x in range(len(Mode120_settings["V_offset"])):
        if not (
            abs(Mode120_settings["V_offset"][x]) <= 10
            and 0 <= abs(Mode120_settings["H_offset"]) <= 10
        ):
            Logger.error("Mode120_settings['V_offset'] or Mode120_settings['H_offset']")
            raise ValueError
    if not (type(Mode120_settings["start_date"]) == str):
        Logger.error("Mode120_settings['date']")
        raise TypeError
    if not (type(Mode120_settings["automatic"]) == bool):
        Logger.error("Mode120_settings['automatic']")
        raise TypeError
    if not (type(Mode120_settings["Vmag"]) == str):
        Logger.error("Mode120_settings['Vmag']")
    if not (
        0 < Mode120_settings["SnapshotTime"]
        and type(Mode120_settings["SnapshotTime"]) == int
    ):
        Logger.error("Mode120_settings['SnapshotTime']")
        raise ValueError
    if not (
        2 <= Mode120_settings["SnapshotSpacing"]
        and type(Mode120_settings["SnapshotSpacing"]) == int
    ):
        Logger.error("Mode120_settings['SnapshotSpacing']")
        raise ValueError
    if not (
        0 < Mode120_settings["TimeSkip"]["TimeSkip"] <= 2 * 3600 * 24
        and (
            type(Mode120_settings["TimeSkip"]["TimeSkip"]) == int
            or type(Mode120_settings["TimeSkip"]["TimeSkip"]) == float
        )
    ):
        Logger.error("Mode120_settings['TimeSkip']['TimeSkip']")
        raise ValueError
    if not (
        Timeline_settings["StandardPointingAltitude"]
        < Mode120_settings["pointing_altitude"]
        and type(Mode120_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode120_settings['pointing_altitude']")
        raise ValueError
    if not (Mode120_settings["TimeToConsider"]["TimeToConsider"] <= Timeline_settings["duration"]["duration"]):
        Logger.error(
            "Mode120_settings['TimeToConsider']['TimeToConsider'] > Timeline_settings['duration']['duration']"
        )
        raise ValueError
    if not (type(Mode120_settings["CCDSELs"]) == list):
        Logger.error("Mode120_settings['CCDSELs'] != list")
        raise TypeError
    if not (
        Mode120_settings["SnapshotSpacing"] * (len(Mode120_settings["CCDSELs"]) - 1)
        + Mode120_settings["SnapshotTime"]
        < Mode120_settings["freeze_duration"]
        <= 3600
    ):
        Logger.error(
            "Mode120_settings['SnapshotSpacing'] * (len(Mode120_settings['CCDSELs'])-1) + Mode120_settings['SnapshotTime'] > Mode120_settings['freeze_duration'] or Mode120_settings['freeze_duration'] > 3600"
        )
        raise ValueError
    for CCDSEL in Mode120_settings["CCDSELs"]:
        if not (CCDSEL in [1, 2, 4, 8, 16, 32]):
            Logger.error("Mode120_settings['CCDSELs'] element != [1,2,4,8,16,32]")
            raise ValueError

    if not (
        -60000 <= Mode121_122_123_settings["pointing_altitude"] <= 230000
        and type(Mode121_122_123_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode121_122_123_settings['pointing_altitude']")
        raise ValueError
    if not (
        0 < Mode121_122_123_settings["timestep"] <= 10
        and type(Mode121_122_123_settings["timestep"]) == int
    ):
        Logger.error("Mode121_122_123_settings['timestep']")
        raise ValueError
    if not (
        Mode121_122_123_settings["freeze_start"]
        >= Timeline_settings["pointing_stabilization"]
        + 12 * Timeline_settings["CMD_separation"]
        and type(Mode121_122_123_settings["freeze_start"]) == int
    ):
        Logger.error("Mode121_122_123_settings")
        raise TypeError
    if not (
        0 < abs(Mode121_122_123_settings["V_FOV"]) <= 5
        and 0 < abs(Mode121_122_123_settings["H_FOV"]) <= 10
    ):
        Logger.error(
            "Mode121_122_123_settings['V_FOV'] or Mode121_122_123_settings['H_FOV']"
        )
        raise ValueError
    if not (type(Mode121_122_123_settings["Vmag"]) == str):
        Logger.error("Mode121_122_123_settings['Vmag']")
        raise TypeError
    if not (
        0
        < Mode121_122_123_settings["SnapshotTime"]
        < Mode121_122_123_settings["freeze_duration"] - 10
        and type(Mode121_122_123_settings["SnapshotTime"]) == int
    ):
        Logger.error("Mode121_122_123_settings['SnapshotTime']")
        raise ValueError
    if not (
        Timeline_settings["StandardPointingAltitude"]
        < Mode121_122_123_settings["pointing_altitude"]
        and type(Mode121_122_123_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode121_122_123_settings['pointing_altitude']")
        raise ValueError
    if not (
        0 < Mode121_122_123_settings["TimeSkip"]["TimeSkip"] <= 2 * 3600 * 24
        and (
            type(Mode121_122_123_settings["TimeSkip"]["TimeSkip"]) == int
            or type(Mode121_122_123_settings["TimeSkip"]["TimeSkip"]) == float
        )
    ):
        Logger.error("Mode121_122_123_settings['TimeSkip']['TimeSkip']")
        raise ValueError
    if not (
        0 <= Mode121_122_123_settings["SnapshotSpacing"]
        and type(Mode121_122_123_settings["SnapshotSpacing"]) == int
    ):
        Logger.error("Mode121_122_123_settings['SnapshotSpacing']")
        raise ValueError
    if not (
        Mode121_122_123_settings["SnapshotSpacing"] * 6
        + Mode121_122_123_settings["SnapshotTime"]
        < Mode121_122_123_settings["freeze_duration"]
        <= 3600
    ):
        Logger.error(
            "Mode121_122_123_settings['SnapshotSpacing'] * 5 + Mode121_122_123_settings['SnapshotTime'] > Mode121_122_123_settings['freeze_duration'] or Mode121_122_123_settings['freeze_duration'] > 3600"
        )
        raise ValueError
    if not (
        Mode121_122_123_settings["TimeToConsider"]["TimeToConsider"] <= Timeline_settings["duration"]["duration"]
    ):
        Logger.error(
            "Mode121_122_123_settings['TimeToConsider']['TimeToConsider'] > Timeline_settings['duration']['duration']"
        )
        raise ValueError

    if not (
        Mode121_122_123_settings["SnapshotSpacing"]
        * (len(Mode121_settings["CCDSELs"]) - 1)
        + Mode121_122_123_settings["SnapshotTime"]
        < Mode121_122_123_settings["freeze_duration"]
        <= 3600
    ):
        Logger.error(
            "Mode121_122_123_settings['SnapshotSpacing'] * (len(Mode121_settings['CCDSELs'])-1) + Mode124_settings['SnapshotTime'] > Mode121_122_123_settings['freeze_duration'] or Mode121_122_123_settings['freeze_duration'] > 3600"
        )
        raise ValueError

    if not (type(Mode121_settings["CCDSELs"]) == list):
        Logger.error("Mode121_settings['CCDSELs'] != list")
        raise TypeError
    for CCDSEL in Mode121_settings["CCDSELs"]:
        if not (CCDSEL in [1, 2, 4, 8, 16, 32]):
            Logger.error("Mode121_settings['CCDSELs'] element != [1,2,4,8,16,32]")
            raise ValueError

    if not (type(Mode121_settings["start_date"]) == str):
        Logger.error("Mode121_settings['start_date']")
        raise TypeError
    if not (type(Mode122_settings["start_date"]) == str):
        Logger.error("Mode122_settings['start_date']")
        raise TypeError
    if not (type(Mode123_settings["start_date"]) == str):
        Logger.error("Mode123_settings['start_date']")
        raise TypeError

    if not (
        0 <= Mode122_settings["Exp_Time_IR"]
        and type(Mode122_settings["Exp_Time_IR"]) == int
    ):
        Logger.error("Mode122_settings['Exp_Time_IR']")
        raise ValueError
    if not (
        0 <= Mode122_settings["Exp_Time_UV"]
        and type(Mode122_settings["Exp_Time_UV"]) == int
    ):
        Logger.error("Mode122_settings['Exp_Time_UV']")
        raise ValueError
    if not (
        0 <= Mode123_settings["Exp_Time_IR"]
        and type(Mode123_settings["Exp_Time_IR"]) == int
    ):
        Logger.error("Mode123_settings['Exp_Time_IR']")
        raise ValueError
    if not (
        0 <= Mode123_settings["Exp_Time_UV"]
        and type(Mode123_settings["Exp_Time_UV"]) == int
    ):
        Logger.error("Mode123_settings['Exp_Time_UV']")
        raise ValueError

    if not (type(Mode121_settings["automatic"]) == bool):
        Logger.error("Mode121_settings['automatic']")
        raise TypeError
    if not (type(Mode122_settings["automatic"]) == bool):
        Logger.error("Mode122_settings['automatic']")
        raise TypeError
    if not (type(Mode123_settings["automatic"]) == bool):
        Logger.error("Mode123_settings['automatic']")
        raise TypeError

    if not (
        -60000 <= Mode124_settings["pointing_altitude"] <= 230000
        and type(Mode124_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode124_settings['pointing_altitude']")
        raise ValueError
    if not (
        0 < Mode124_settings["timestep"] <= 10
        and type(Mode124_settings["timestep"]) == int
    ):
        Logger.error("Mode124_settings['timestep']")
        raise ValueError
    if not (
        Mode124_settings["freeze_start"]
        >= Timeline_settings["pointing_stabilization"]
        + 12 * Timeline_settings["CMD_separation"]
        and type(Mode124_settings["freeze_start"]) == int
    ):
        Logger.error("Mode124_settings")
        raise TypeError
    if not (type(Mode124_settings["V_offset"]) == list):
        Logger.error("Mode124_settings['V_offset'] != list")
    for x in range(len(Mode124_settings["V_offset"])):
        if not (
            abs(Mode124_settings["V_offset"][x]) <= 1
            and 0 <= abs(Mode124_settings["H_offset"]) <= 10
        ):
            Logger.error("Mode124_settings['V_offset'] or Mode124_settings['H_offset']")
            raise ValueError
    if not (type(Mode124_settings["start_date"]) == str):
        Logger.error("Mode124_settings['start_date']")
        raise TypeError
    if not (type(Mode124_settings["automatic"]) == bool):
        Logger.error("Mode124_settings['automatic']")
        raise TypeError
    if not (
        0 < Mode124_settings["SnapshotTime"] < Mode124_settings["freeze_duration"] - 10
        and type(Mode124_settings["SnapshotTime"]) == int
    ):
        Logger.error("Mode124_settings['SnapshotTime']")
        raise ValueError
    if not (
        Timeline_settings["StandardPointingAltitude"]
        < Mode124_settings["pointing_altitude"]
        and type(Mode124_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode124_settings['pointing_altitude']")
        raise ValueError
    if not (
        0 <= Mode124_settings["SnapshotSpacing"]
        and type(Mode124_settings["SnapshotSpacing"]) == int
    ):
        Logger.error("Mode124_settings['SnapshotSpacing']")
        raise ValueError
    if not (type(Mode124_settings["CCDSELs"]) == list):
        Logger.error("Mode124_settings['CCDSELs'] != list")
        raise TypeError
    if not (
        Mode124_settings["SnapshotSpacing"] * (len(Mode124_settings["CCDSELs"]) - 1)
        + Mode124_settings["SnapshotTime"]
        < Mode124_settings["freeze_duration"]
        <= 3600
    ):
        Logger.error(
            "Mode124_settings['SnapshotSpacing'] * (len(Mode124_settings['CCDSELs'])-1) + Mode124_settings['SnapshotTime'] > Mode124_settings['freeze_duration'] or Mode124_settings['freeze_duration'] > 3600"
        )
        raise ValueError
    for CCDSEL in Mode124_settings["CCDSELs"]:
        if not (CCDSEL in [1, 2, 4, 8, 16, 32]):
            Logger.error("Mode124_settings['CCDSELs'] element != [1,2,4,8,16,32]")
            raise ValueError
    if not (Mode124_settings["TimeToConsider"]["TimeToConsider"] <= Timeline_settings["duration"]["duration"]):
        Logger.error(
            "Mode124_settings['TimeToConsider'] > Timeline_settings['duration']"
        )
        raise ValueError

    MaximumNumberOfCMDsInMacro = 12

    if not (
        Timeline_settings["CMD_separation"] <= Mode130_settings["SnapshotSpacing"]
        and type(Mode130_settings["SnapshotSpacing"]) == int
    ):
        Logger.error("Mode130_settings['SnapshotSpacing']")
        raise TypeError
    if not (
        Timeline_settings["pointing_stabilization"]
        + Timeline_settings["CMD_separation"] * MaximumNumberOfCMDsInMacro
        + Timeline_settings["mode_separation"]
        < Mode131_settings["mode_duration"]
        and type(Mode131_settings["mode_duration"]) == int
    ):
        Logger.error("Mode131_settings['mode_duration'] is too short")
        raise TypeError
    if not (
        Timeline_settings["pointing_stabilization"]
        + Timeline_settings["CMD_separation"] * MaximumNumberOfCMDsInMacro
        + Timeline_settings["mode_separation"]
        < Mode134_settings["mode_duration"]
        and type(Mode134_settings["mode_duration"]) == int
    ):
        Logger.error("Mode134_settings['mode_duration'] is too short")
        raise TypeError

    if not (
        -60000 <= Mode130_settings["pointing_altitude"] <= 230000
        and type(Mode130_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode130_settings['pointing_altitude']")
        raise ValueError
    if not (
        -60000 <= Mode131_settings["pointing_altitude"] <= 230000
        and type(Mode131_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode131_settings['pointing_altitude']")
        raise ValueError
    if not (
        -60000 <= Mode132_settings["pointing_altitude"] <= 230000
        and type(Mode132_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode132_settings['pointing_altitude']")
        raise ValueError
    if not (
        -60000 <= Mode133_settings["pointing_altitude"] <= 230000
        and type(Mode133_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode133_settings['pointing_altitude']")
        raise ValueError
    if not (
        -60000 <= Mode134_settings["pointing_altitude"] <= 230000
        and type(Mode134_settings["pointing_altitude"]) == int
    ):
        Logger.error("Mode134_settings['pointing_altitude']")
        raise ValueError

    if not (type(Mode130_settings["start_date"]) == str):
        Logger.error("Mode130_settings['start_date']")
        raise TypeError
    if not (type(Mode131_settings["start_date"]) == str):
        Logger.error("Mode131_settings['start_date']")
        raise TypeError
    if not (type(Mode132_settings["start_date"]) == str):
        Logger.error("Mode132_settings['start_date']")
        raise TypeError
    if not (type(Mode133_settings["start_date"]) == str):
        Logger.error("Mode133_settings['start_date']")
        raise TypeError
    if not (type(Mode134_settings["start_date"]) == str):
        Logger.error("Mode134_settings['start_date']")
        raise TypeError

    if not (
        type(Mode132_settings["Exp_Times_IR"]) == list
        and type(Mode132_settings["Exp_Times_UV"]) == list
    ):
        Logger.error(
            "Mode132_settings['Exp_Times_IR'] or Mode132_settings['Exp_Times_UV']"
        )
        raise TypeError
    if not (
        type(Mode133_settings["Exp_Times_IR"]) == list
        and type(Mode133_settings["Exp_Times_UV"]) == list
    ):
        Logger.error(
            "Mode133_settings['Exp_Times_IR'] or Mode133_settings['Exp_Times_UV']"
        )
        raise TypeError

    if not (
        len(Mode132_settings["Exp_Times_IR"]) == len(Mode132_settings["Exp_Times_UV"])
    ):
        Logger.error(
            "len(Mode132_settings['Exp_Times_IR']) != len(Mode132_settings['Exp_Times_UV'])"
        )
        raise TypeError
    if not (
        len(Mode133_settings["Exp_Times_IR"]) == len(Mode133_settings["Exp_Times_UV"])
    ):
        Logger.error(
            "len(Mode133_settings['Exp_Times_IR']) != len(Mode133_settings['Exp_Times_UV'])"
        )
        raise TypeError

    # Check that CCDsync waits for long enough time for full CCD readout (standard)

    # Standard CCDsettings
    _, _, FullReadout_synctime, _ = Library.SyncArgCalculator(
        configFile.CCD_macro_settings("FullReadout"),
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )
    _, _, CustomBinning_synctime, _ = Library.SyncArgCalculator(
        configFile.CCD_macro_settings("CustomBinning"),
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )
    _, _, HighResUV_synctime, _ = Library.SyncArgCalculator(
        configFile.CCD_macro_settings("HighResUV"),
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    _, _, HighResIR_syctime, _ = Library.SyncArgCalculator(
        configFile.CCD_macro_settings("HighResIR"),
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    _, _, BinnedCalibration, _ = Library.SyncArgCalculator(
        configFile.CCD_macro_settings("BinnedCalibration"),
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    max_normal_synctime = (
        max(
            max(FullReadout_synctime),
            max(CustomBinning_synctime),
            max(HighResUV_synctime),
            max(HighResIR_syctime),
            max(BinnedCalibration),
        )
        / 1000
    )

    if not Timeline_settings["CCDSYNC_Waittime"] > max_normal_synctime:
        Logger.error("Timeline_settings['CCDSYNC_Waittime']")
        raise ValueError

    Logger.info("CheckConfigFile passed.")
