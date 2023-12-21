# -*- coding: utf-8 -*-
"""Contain Mode functions which generates and calculates parameters for each mode, 
then calls for Macros/Commands functions located in the *Macros_Commands* package, which will in turn write commands to the XML tree object *root*.

Functions on the form "X", where X is any Mode:

    **Arguments:**
        **root** (*lxml.etree.Element*):  XML tree structure. Main container object for the ElementTree API. \n
        **date** (*ephem.Date*): Starting date of the Mode. On the form of the ephem.Date class. \n
        **duration** (*int*): The duration of the mode [s]. \n
        **relativeTime** (*int*): The starting time of the mode with regard to the start of the timeline [s]. \n
        **Timeline_settings** (*dict*): Dictionary containing the settings of the Timeline given in the *Science_Mode_Timeline*. If no Timeline settings were present in the Science Mode Timeline, they were instead taken from the *Configuration File*. \n
        **Mode_settings** (*dict*): Dictionary containing the settings of the Mode given in the *Science_Mode_Timeline*.

    **Returns:**
        None

When creating new Mode functions it is crucial that the function name is
*X*, where *X* is the same as the string used in the *Science Mode Timeline*. Because OPT will automatically look for any function with the same name as the string in the *Science Mode Timeline*
        
@author: David Skånberg
"""


from mats_planningtool.XMLGenerator.Modes_and_Tests.Macros_Commands import Macros, Commands
from mats_planningtool.Library import (
    dict_comparator,
    utc_to_onboardTime,
    SunAngle,
    CCDSELExtracter,
    SyncArgCalculator,
)
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator
import ephem
import logging
import sys
import pylab
import importlib
import skyfield.api
import copy
from enum import Enum
import datetime as DT
from mats_planningtool import Library

# Timeline_settings = configFile.Timeline_settings()
Logger = logging.getLogger("OPT_logger")


"######### Operational Science Modes #########################"
"##############################################################"

def write_comment(current_state,current_time,Mode_settings,lat_LP,sun_angle):
    comment = (
        current_state
        + ": "
        + str(current_time)
        + ", parameters: "
        + str(Mode_settings)
        + " position: "
        + str(lat_LP)
        + " sun angle"
        + str(sun_angle)
    )

    return comment

def check_lat(lat_position,lat_limit):

    if lat_limit == -999:
        return True
    if lat_limit<0:
        return lat_position<lat_limit
    return lat_position>lat_limit

def Mode5(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode5

    **Macro:** Operational_Limb_Pointing_macro \n
    **CCD_Macro:** Chosen in the settings of the Mode. \n

    """

    pointing_altitude = Timeline_settings["StandardPointingAltitude"]

    Mode_settings_ConfigFile = configFile.Operational_Science_Mode_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    CCD_settings = configFile.CCD_macro_settings(
        Mode_settings["Choose_Mode5CCDMacro"]
    )
    PM_settings = configFile.PM_settings()

    Mode_name = sys._getframe(0).f_code.co_name.replace("", "")
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

    # pointing_altitude = Mode_settings['pointing_altitude']

    # Macros.Custom_Binning_Macro(root,relativeTime, pointing_altitude=pointing_altitude, Timeline_settings = Timeline_settings, comment = comment)
    Macros.Operational_Limb_Pointing_macro(
        root,
        relativeTime,
        CCD_settings,
        PM_settings=PM_settings,
        pointing_altitude=pointing_altitude,
        Timeline_settings=Timeline_settings, configFile=configFile,
        TEXPIMS_fixed=Mode_settings['TEXPIMS'],
        comment=comment,
    )


############################################################################################

def Mode6(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode6

    **Macro:** Operational_Limb_Pointing_macro \n
    **CCD_Macro:** Chosen in the settings of the Mode. \n

    """

    pointing_altitude = Timeline_settings["StandardPointingAltitude"]

    Mode_settings_ConfigFile = configFile.Operational_Science_Mode_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    CCD_settings = configFile.CCD_macro_settings("HighResUV")
    PM_settings = configFile.PM_settings()

    Mode_name = sys._getframe(0).f_code.co_name.replace("", "")
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

    # pointing_altitude = Mode_settings['pointing_altitude']

    # Macros.Custom_Binning_Macro(root,relativeTime, pointing_altitude=pointing_altitude, Timeline_settings = Timeline_settings, comment = comment)
    Macros.Operational_Limb_Pointing_macro(
        root,
        relativeTime,
        CCD_settings,
        PM_settings=PM_settings,
        pointing_altitude=pointing_altitude,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

###################################################################################################

def Mode7(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode7

    **Macro:** Operational_Limb_Pointing_macro \n
    **CCD_Macro:** Chosen in the settings of the Mode. \n

    """

    pointing_altitude = Timeline_settings["StandardPointingAltitude"]

    Mode_settings_ConfigFile = configFile.Operational_Science_Mode_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    CCD_settings = configFile.CCD_macro_settings("HighResIR")
    PM_settings = configFile.PM_settings()

    Mode_name = sys._getframe(0).f_code.co_name.replace("", "")
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

    # pointing_altitude = Mode_settings['pointing_altitude']

    # Macros.Custom_Binning_Macro(root,relativeTime, pointing_altitude=pointing_altitude, Timeline_settings = Timeline_settings, comment = comment)
    Macros.Operational_Limb_Pointing_macro(
        root,
        relativeTime,
        CCD_settings,
        PM_settings=PM_settings,
        pointing_altitude=pointing_altitude,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

###################################################################################################

def Mode1(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode1

    **Macro:** Operational_Limb_Pointing_macro \n
    **CCD_Macro:** HighResUV \n

    Disable exposure on UV channels for +-lat degrees latitude equatorwards.
    Stop/Start Nadir at dusk/dawn below MATS.
    Simulates MATS and the LP with or without yaw movement to be able to predict and schedule commands in the XML-file.

    """

    zeros = pylab.zeros
    pi = pylab.pi
    arccos = pylab.arccos

    CCD_settings = copy.deepcopy(configFile.CCD_macro_settings("HighResUV"))
    PM_settings = configFile.PM_settings()
    Mode_settings_ConfigFile = configFile.Operational_Science_Mode_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    timestep = Mode_settings["timestep"]

    mode_change_time = Timeline_settings["Mode1_2_5_minDuration"]


    log_timestep = Mode_settings["log_timestep"]
    Logger.debug("log_timestep [s]: " + str(log_timestep))

    TLE = configFile.getTLE()

    "Pre-allocate space"
    lat_MATS = zeros((duration, 1))
    r_MATS = zeros((duration, 3))
    optical_axis = zeros((duration, 3))
    lat_LP = zeros((duration, 1))
    MATS_P = zeros((duration, 1))

    sun_angle = zeros((duration, 1))
    lat_LP = zeros((duration, 1))

    R_mean = 6371000  # Radius of Earth in m
    pointing_altitude = Timeline_settings["StandardPointingAltitude"]
    lat = Mode_settings["lat"]

    # Altitude in km where sun is deemed to reflect in atmosphere, determining night and day below satellite"
    heightAboveSurface = 35000

    # Estimation of the angle between the sun and the FOV position when it enters eclipse
    MATS_nadir_eclipse_angle = (
        arccos(R_mean / (R_mean + heightAboveSurface)) / pi * 180 + 90
    )

    Logger.debug("MATS_nadir_eclipse_angle : " + str(MATS_nadir_eclipse_angle))
    Logger.debug("")


    ########################## Global setup ################

    comment = "Mode 1 setup"
    
    CCDSEL, NCCD, TEXPIOFS, TEXPIMS = SyncArgCalculator(
        CCD_settings,
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    relativeTime = Commands.TC_pafMode(
        root, relativeTime, MODE=2, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment
    )

    # relativeTime_OperationalMode = relativeTime+Timeline_settings['pointing_stabilization']
    relativeTime = Commands.TC_acfLimbPointingAltitudeOffset(
        root,
        relativeTime,
        Initial=pointing_altitude,
        Final=pointing_altitude,
        Rate=0,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Commands.TC_pafPM(
        root,
        relativeTime,
        TEXPMS=PM_settings["TEXPMS"],
        TEXPIMS=PM_settings["TEXPIMS"],
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Macros.SetCCDs_macro(
        root,
        relativeTime,
        CCD_settings=CCD_settings,
        TEXPIMS=TEXPIMS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Commands.TC_pafCCDSYNCHRONIZE(
        root,
        relativeTime,
        CCDSEL=CCDSEL,
        NCCD=NCCD,
        TEXPIOFS=TEXPIOFS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    #Simulate satellite and generate mode
    t = -1

    MATS_skyfield = skyfield.api.EarthSatellite(TLE[0], TLE[1])

    new_relativeTime = relativeTime
    current_time = ephem.Date(date)

    sattelite_state = {"UV_on": True, "Nadir_on": True}
    changetime = []
    all_states = []
    # for t in range(int(duration/timestep)):
    "Simulation begins here"
    while current_time < ephem.second * duration + ephem.Date(date):

        t += 1

        if t != 0:
            "Incremented time from scheduling CMDs"
            CMD_scheduling_delay = new_relativeTime - relativeTime
            "Increment with timestep each loop and add any added time from CMD scheduling"
            current_time = ephem.Date(
                current_time + ephem.second * (timestep + CMD_scheduling_delay)
            )
            # current_time = ephem.Date( current_time+ephem.second*(new_relativeTime-relativeTime) )
            relativeTime = new_relativeTime + timestep

        new_relativeTime = relativeTime

        if t * timestep % log_timestep == 0:
            LogFlag = True
        else:
            LogFlag = False

        Satellite_dict = Satellite_Simulator(
            MATS_skyfield,
            current_time,
            Timeline_settings,
            pointing_altitude / 1000,
            LogFlag,
            Logger,
        )

        r_MATS[t] = Satellite_dict["Position [km]"]
        MATS_P[t] = Satellite_dict["OrbitalPeriod [s]"]
        lat_MATS[t] = Satellite_dict["Latitude [degrees]"]
        optical_axis[t] = Satellite_dict["OpticalAxis"]
        lat_LP[t] = Satellite_dict["EstimatedLatitude_LP [degrees]"]
        sun_angle[t] = Satellite_dict["SolarZenithAngleNadir"]

        if t * timestep % log_timestep == 0:
            Logger.debug("sun_angle [degrees]: " + str(sun_angle[t]))

        ############# Initial Mode setup ##########################################

        if t == 0:

            "Check if night or day"
            if sun_angle[t] > MATS_nadir_eclipse_angle:

                if ~check_lat(lat_LP[t],lat):
                    current_state = "Mode1_night_UV_off"
                    comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])
                    # new_relativeTime = Macros.Mode1_macro(root,relativeTime, pointing_altitude=pointing_altitude, UV_on = False, nadir_on = True, Timeline_settings = Timeline_settings, comment = comment)
                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = False, Nadir_on = True,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )
                
                elif check_lat(lat_LP[t],lat):
                    current_state = "Mode1_night_UV_on"
                    comment = (
                        current_state
                        + ": "
                        + str(current_time)
                        + ", parameters: "
                        + str(Mode_settings)
                    )
                    # new_relativeTime = Macros.Mode1_macro(root,relativeTime, pointing_altitude=pointing_altitude, UV_on = True, nadir_on = True, Timeline_settings = Timeline_settings, comment = comment)
                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = True, Nadir_on = True,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )

            elif sun_angle[t] < MATS_nadir_eclipse_angle:

                if ~check_lat(lat_LP[t],lat):
                    current_state = "Mode1_day_UV_off"
                    comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])

                    # new_relativeTime = Macros.Mode1_macro(root,relativeTime,pointing_altitude, UV_on = False, nadir_on = False, Timeline_settings = Timeline_settings, comment = comment)
                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = False, Nadir_on = False,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )

                elif check_lat(lat_LP[t],lat):
                    current_state = "Mode1_day_UV_on"
                    comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])
                    # new_relativeTime = Macros.Mode1_macro(root,relativeTime,pointing_altitude, UV_on = True, nadir_on = False, Timeline_settings = Timeline_settings, comment = comment)
                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = True, Nadir_on = False,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )

            Logger.debug(current_state)
            Logger.debug("")

            all_states.append(current_state)

        ############# End of Initial Mode setup ###################################

        
        if t != 0:
            ####################### SCI-mode Operation planner ################

            #Check status
            nadir_on = sun_angle[t] > MATS_nadir_eclipse_angle
            uv_on = check_lat(lat_LP[t],lat)
            #print('correct state: nadir %s uv %s : current state: nadir %s uv %s' % (nadir_on, uv_on, sattelite_state["Nadir_on"], sattelite_state["UV_on"]))
            correct_state = (sattelite_state["UV_on"] == uv_on) and (sattelite_state["Nadir_on"] == nadir_on)
            #print('change state %s ' % (not correct_state))

            if (not correct_state):
                print('Changing state')
                changetime.append(t)

                Logger.debug("")
                if nadir_on and uv_on:
                    current_state = "Mode1_night_UV_on"
                elif ~nadir_on and uv_on:
                    current_state = "Mode1_day_UV_on"
                elif nadir_on and ~uv_on:
                    current_state = "Mode1_night_UV_off"
                elif ~nadir_on and ~uv_on: 
                    current_state = "Mode1_day_UV_off"
                else:
                    raise Exception
                comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])

                new_relativeTime = Macros.Mode1(
                    root,
                    relativeTime,
                    CCD_settings,
                    TEXPIMS,
                    sattelite_state,
                    UV_on = uv_on, Nadir_on = nadir_on,
                    Timeline_settings=Timeline_settings, configFile=configFile,
                    comment=comment,
                )

                Logger.debug(current_state)
                Logger.debug("current_time: " + str(current_time))
                Logger.debug("lat_MATS [degrees]: " + str(lat_MATS[t]))
                Logger.debug("lat_LP [degrees]: " + str(lat_LP[t]))
                Logger.debug("sun_angle [degrees]: " + str(sun_angle[t]))
                Logger.debug("")
            
            all_states.append(current_state)
            ############### End of SCI-mode operation planner #################

       
    
    color_dict = { 'Mode1_night_UV_on':'red', 'Mode1_day_UV_on':'blue', 'Mode1_night_UV_off':'black', 'Mode1_day_UV_off':'green'}    
    print('test')

#######################################################################################


def Mode2(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode2

    **Macro:** Operational_Limb_Pointing_macro \n
    **CCD_Macro:** HighResIR \n

    Stop/Start Nadir at dusk/dawn below MATS.
    Simulates MATS and the LP with or without yaw movement to be able to predict and schedule commands in the XML-file.

    """

    zeros = pylab.zeros
    pi = pylab.pi
    arccos = pylab.arccos

    CCD_settings = copy.deepcopy(configFile.CCD_macro_settings("HighResUV"))
    PM_settings = configFile.PM_settings()
    Mode_settings_ConfigFile = configFile.Operational_Science_Mode_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    timestep = Mode_settings["timestep"]

    mode_change_time = Timeline_settings["Mode1_2_5_minDuration"]


    log_timestep = Mode_settings["log_timestep"]
    Logger.debug("log_timestep [s]: " + str(log_timestep))

    TLE = configFile.getTLE()

    "Pre-allocate space"
    lat_MATS = zeros((duration, 1))
    r_MATS = zeros((duration, 3))
    optical_axis = zeros((duration, 3))
    lat_LP = zeros((duration, 1))
    MATS_P = zeros((duration, 1))

    sun_angle = zeros((duration, 1))
    lat_LP = zeros((duration, 1))

    R_mean = 6371000  # Radius of Earth in m
    pointing_altitude = Timeline_settings["StandardPointingAltitude"]
    lat = Mode_settings["lat"]

    # Altitude in km where sun is deemed to reflect in atmosphere, determining night and day below satellite"
    heightAboveSurface = 35000

    # Estimation of the angle between the sun and the FOV position when it enters eclipse
    MATS_nadir_eclipse_angle = (
        arccos(R_mean / (R_mean + heightAboveSurface)) / pi * 180 + 90
    )

    Logger.debug("MATS_nadir_eclipse_angle : " + str(MATS_nadir_eclipse_angle))
    Logger.debug("")


    ########################## Global setup ################

    comment = "Mode 2 setup"
    
    CCDSEL, NCCD, TEXPIOFS, TEXPIMS = SyncArgCalculator(
        CCD_settings,
        Timeline_settings["CCDSYNC_ExtraOffset"],
        Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    relativeTime = Commands.TC_pafMode(
        root, relativeTime, MODE=2, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment
    )

    # relativeTime_OperationalMode = relativeTime+Timeline_settings['pointing_stabilization']
    relativeTime = Commands.TC_acfLimbPointingAltitudeOffset(
        root,
        relativeTime,
        Initial=pointing_altitude,
        Final=pointing_altitude,
        Rate=0,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Commands.TC_pafPM(
        root,
        relativeTime,
        TEXPMS=PM_settings["TEXPMS"],
        TEXPIMS=PM_settings["TEXPIMS"],
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Macros.SetCCDs_macro(
        root,
        relativeTime,
        CCD_settings=CCD_settings,
        TEXPIMS=TEXPIMS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Commands.TC_pafCCDSYNCHRONIZE(
        root,
        relativeTime,
        CCDSEL=CCDSEL,
        NCCD=NCCD,
        TEXPIOFS=TEXPIOFS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    #Simulate satellite and generate mode
    t = -1

    MATS_skyfield = skyfield.api.EarthSatellite(TLE[0], TLE[1])

    new_relativeTime = relativeTime
    current_time = ephem.Date(date)

    sattelite_state = {"UV_on": True, "Nadir_on": True}

    # for t in range(int(duration/timestep)):
    "Simulation begins here"
    while current_time < ephem.second * duration + ephem.Date(date):

        t += 1

        if t != 0:
            "Incremented time from scheduling CMDs"
            CMD_scheduling_delay = new_relativeTime - relativeTime
            "Increment with timestep each loop and add any added time from CMD scheduling"
            current_time = ephem.Date(
                current_time + ephem.second * (timestep + CMD_scheduling_delay)
            )
            # current_time = ephem.Date( current_time+ephem.second*(new_relativeTime-relativeTime) )
            relativeTime = new_relativeTime + timestep

        new_relativeTime = relativeTime

        if t * timestep % log_timestep == 0:
            LogFlag = True
        else:
            LogFlag = False

        Satellite_dict = Satellite_Simulator(
            MATS_skyfield,
            current_time,
            Timeline_settings,
            pointing_altitude / 1000,
            LogFlag,
            Logger,
        )

        r_MATS[t] = Satellite_dict["Position [km]"]
        MATS_P[t] = Satellite_dict["OrbitalPeriod [s]"]
        lat_MATS[t] = Satellite_dict["Latitude [degrees]"]
        optical_axis[t] = Satellite_dict["OpticalAxis"]
        lat_LP[t] = Satellite_dict["EstimatedLatitude_LP [degrees]"]
        sun_angle[t] = Satellite_dict["SolarZenithAngleNadir"]

        if t * timestep % log_timestep == 0:
            Logger.debug("sun_angle [degrees]: " + str(sun_angle[t]))

        ############# Initial Mode setup ##########################################

        if t == 0:

            "Check if night or day"
            if sun_angle[t] > MATS_nadir_eclipse_angle:

                current_state = "Mode2_night"
                comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])
                new_relativeTime = Macros.Mode1(
                    root,
                    relativeTime,
                    CCD_settings,
                    TEXPIMS,
                    sattelite_state,
                    UV_on = False, Nadir_on = True,
                    Timeline_settings=Timeline_settings, configFile=configFile,
                    comment=comment,
                )

            elif sun_angle[t] < MATS_nadir_eclipse_angle:

                current_state = "Mode2_day"

                new_relativeTime = Macros.Mode1(
                    root,
                    relativeTime,
                    CCD_settings,
                    TEXPIMS,
                    sattelite_state,
                    UV_on = False, Nadir_on = False,
                    Timeline_settings=Timeline_settings, configFile=configFile,
                    comment=comment,
                )

            Logger.debug(current_state)
            Logger.debug("")

        ############# End of Initial Mode setup ###################################

        if t != 0:
            ####################### SCI-mode Operation planner ################

            # Check dusk
            if (
                sun_angle[t] >= MATS_nadir_eclipse_angle
                and sun_angle[t - 1] < MATS_nadir_eclipse_angle
            ):

                if (new_relativeTime+mode_change_time) <= Timeline_settings["duration"]["duration"]:

                    Logger.debug("")
                    current_state = "Mode2_night"
                    comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])

                    # new_relativeTime = Macros.Mode1_macro(root, relativeTime, pointing_altitude, UV_on = False, nadir_on = True, Timeline_settings = Timeline_settings, comment = comment)

                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = False, Nadir_on = True,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )

                    Logger.debug(current_state)
                    Logger.debug("current_time: " + str(current_time))
                    Logger.debug("lat_MATS [degrees]: " + str(lat_MATS[t]))
                    Logger.debug("lat_LP [degrees]: " + str(lat_LP[t]))
                    Logger.debug("sun_angle [degrees]: " + str(sun_angle[t]))
                    Logger.debug("")



            # Check dawn
            if (
                sun_angle[t] <= MATS_nadir_eclipse_angle
                and sun_angle[t - 1] > MATS_nadir_eclipse_angle
            ):

                if (new_relativeTime+mode_change_time) <= Timeline_settings["duration"]["duration"]:

                    Logger.debug("")
                    current_state = "Mode2_day"
                    comment = write_comment(current_state,current_time,Mode_settings,lat_LP[t],sun_angle[t])

                    new_relativeTime = Macros.Mode1(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS,
                        sattelite_state,
                        UV_on = False, Nadir_on = False,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        comment=comment,
                    )

                    Logger.debug(current_state)
                    Logger.debug("current_time: " + str(current_time))
                    Logger.debug("lat_MATS [degrees]: " + str(lat_MATS[t]))
                    Logger.debug("lat_LP [degrees]: " + str(lat_LP[t]))
                    Logger.debug("sun_angle [degrees]: " + str(sun_angle[t]))
                    Logger.debug("")


            ############### End of SCI-mode operation planner #################


################################################################################################

"######### Calibration Modes ##################################"
"##############################################################"


def Mode100(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """ Mode100

    **Macro**: Operational_Limb_Pointing_macro. \n
    **CCD_Macro**: BinnedCalibration with configurable exposure time of UV and IR CCDs. \n

    Successively point at altitudes from X-Y in Operational Mode in intervals of Z with increasing Exposure Times.
    Where X is *pointing_altitude_from*, Y is *pointing_altitude_to, and Z is *pointing_altitude_interval*.
    All defined in *Mode100_settings*.

    """

    CCD_settings = configFile.CCD_macro_settings("BinnedCalibration")
    PM_settings = configFile.PM_settings()
    Mode_settings_ConfigFile = configFile.Mode100_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    Mode_name = sys._getframe(0).f_code.co_name
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

    pointing_altitude_from = Mode_settings["pointing_altitude_from"]
    pointing_altitude_to = Mode_settings["pointing_altitude_to"]
    pointing_altitude_interval = Mode_settings["pointing_altitude_interval"]
    ExpTimeUV = Mode_settings["Exp_Time_UV"]
    ExpTimeIR = Mode_settings["Exp_Time_IR"]
    ExpTime_step = Mode_settings["ExpTime_step"]

    number_of_altitudes = int(
        abs(
            (pointing_altitude_to - pointing_altitude_from) / pointing_altitude_interval
            + 1
        )
    )
    pointing_altitudes = [
        pointing_altitude_from + x * pointing_altitude_interval
        for x in range(number_of_altitudes)
    ]

    # Mode_macro = getattr(Macros,Mode_name+'_macro')
    relativeTimeEndOfMode = (
        relativeTime + duration - Timeline_settings["mode_separation"]
    )  # go to idle mode separation (s) before endDate
    initial_relativeTime = relativeTime
    duration_flag = 0
    x = 0
    "Schedule macros for steadily increasing pointing altitudes and exposure times"
    for pointing_altitude in pointing_altitudes:
        mode_relativeTime = relativeTime - initial_relativeTime
        CCD_settings[16]["TEXPMS"] = ExpTimeUV + x * ExpTime_step
        CCD_settings[32]["TEXPMS"] = ExpTimeUV + x * ExpTime_step
        CCD_settings[1]["TEXPMS"] = ExpTimeIR + x * ExpTime_step
        CCD_settings[8]["TEXPMS"] = ExpTimeIR + x * ExpTime_step
        CCD_settings[2]["TEXPMS"] = ExpTimeIR + x * ExpTime_step
        CCD_settings[4]["TEXPMS"] = ExpTimeIR + x * ExpTime_step

        if mode_relativeTime > duration and duration_flag == 0:
            Logger.warning(
                "Warning!! The scheduled time for " + Mode_name + " has ran out."
            )
            # input('Enter anything to ackknowledge and continue:\n')
            duration_flag = 1

        # relativeTime = Mode_macro(root, round(relativeTime,2), CCD_settings,
        #                          pointing_altitude = pointing_altitude, Timeline_settings = Timeline_settings, comment = comment)
        relativeTime = Macros.Operational_Limb_Pointing_macro(
            root,
            round(relativeTime, 2),
            CCD_settings,
            PM_settings=PM_settings,
            pointing_altitude=pointing_altitude,
            Timeline_settings=Timeline_settings,
            configFile=configFile,
            comment=comment,
        )

        relativeTime = relativeTime + Mode_settings["pointing_duration"]

        x += 1

    Commands.TC_pafMode(
        root,
        relativeTimeEndOfMode,
        MODE=2,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )


##############################################################################################

##############################################################################################


def Mode110(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode110

    **Macro**: Operational_Sweep_macro. \n
    **CCD_Macro**: BinnedCalibration with configurable exposure time of UV and IR CCDs. \n


    Scan atmosphere from X to Y altitudes with a rate of Z.
    Where X, Y, Z is defined in *Mode110_settings*.

    """

    CCD_settings = configFile.CCD_macro_settings("BinnedCalibration")
    PM_settings = configFile.PM_settings()
    Mode_settings_ConfigFile = configFile.Mode110_settings()

    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    ExpTimeUV = Mode_settings["Exp_Time_UV"]
    ExpTimeIR = Mode_settings["Exp_Time_IR"]
    CCD_settings[16]["TEXPMS"] = ExpTimeUV
    CCD_settings[32]["TEXPMS"] = ExpTimeUV
    CCD_settings[1]["TEXPMS"] = ExpTimeIR
    CCD_settings[8]["TEXPMS"] = ExpTimeIR
    CCD_settings[2]["TEXPMS"] = ExpTimeIR
    CCD_settings[4]["TEXPMS"] = ExpTimeIR

    Mode_name = sys._getframe(0).f_code.co_name
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

    pointing_altitude_from = Mode_settings["pointing_altitude_from"]
    pointing_altitude_to = Mode_settings["pointing_altitude_to"]
    sweep_rate = Mode_settings["sweep_rate"]

    relativeTimeEndOfMode = (
        relativeTime + duration - Timeline_settings["mode_separation"]
    )  # go to idle mode separation (s) before endDate

    # Mode_macro = getattr(Macros,Mode_name+'_macro')

    Macros.Operational_Sweep_macro(
        root,
        round(relativeTime, 2),
        CCD_settings,
        PM_settings=PM_settings,
        pointing_altitude_from=pointing_altitude_from,
        pointing_altitude_to=pointing_altitude_to,
        sweep_rate=sweep_rate,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    Commands.TC_pafMode(
        root,
        relativeTimeEndOfMode,
        MODE=2,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )


####################################################################################################

#######################################################################################################


def Mode12X(
    root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings, CCD_settings,
        dark_settings=None,
):
    """Subfunction of Mode12X, where X is 0,1,2,3....

    **Macro**: Snapshot_Inertial_macro. \n

    Arguments:
        CCD_settings (:obj:`dict` of :obj:`dict` of int): Settings for the CCDs. Defined in the *Configuration File*.

    Stare at a point in inertial reference frame and take a Snapshot with each CCD except nadir and also do not have TEXPMS set to 0.

    """

    Mode_name = sys._getframe(1).f_code.co_name.replace("", "")
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)
    star_name = ""
    comment = comment + ", " + star_name

    freeze_start_utc = ephem.Date(date + ephem.second * Mode_settings["freeze_start"])

    comment = comment + ", freeze at" + str(freeze_start_utc)

    Snapshot_relativeTime = (
        relativeTime + Mode_settings["freeze_start"] + Mode_settings["SnapshotTime"]
    )

    FreezeTime = freeze_start_utc
    FreezeDuration = Mode_settings["freeze_duration"]
    FreezeStabilization = Mode_settings["freeze_stabilization"]
    
    pointing_altitude = Mode_settings["pointing_altitude"]
    pointing_altitude_end = Mode_settings["pointing_altitude_end"]

    SnapshotSpacing = Mode_settings["SnapshotSpacing"]

    Logger.debug("freeze_start_utc: " + str(freeze_start_utc))
    #Logger.debug("FreezeTime [GPS]: " + str(FreezeTime))
    Logger.debug("FreezeDuration: " + str(FreezeDuration))

    Macros.Snapshot_Inertial_macro(
        root,
        round(relativeTime, 2),
        CCD_settings,
        FreezeTime=FreezeTime,
        FreezeDuration=FreezeDuration,
        FreezeStabilization=FreezeStabilization,
        pointing_altitude=pointing_altitude,
        pointing_altitude_end=pointing_altitude_end,
        StandardPointingAltitude=Timeline_settings["StandardPointingAltitude"],
        SnapshotSpacing=SnapshotSpacing,
        Snapshot_relativeTime=Snapshot_relativeTime,
        Timeline_settings=Timeline_settings,
        configFile=configFile,
        CCDSELs=Mode_settings["CCDSELs"],
        comment=comment,
        dark_channels = Mode_settings["dark_channels"],
        dark_settings=dark_settings,
    )


################################################################################################


def Mode120(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """Mode120

    **Macro**: Snapshot_Inertial_macro. \n
    **CCD_Macro**: FullReadout \n

    Stare at a point in inertial reference frame and take one Snapshot with each CCDSEL argument defined by the 'CCDSELs' settings and also do not have TEXPMS set to 0. 
    Used for star calibration.

    """

    Mode_settings_ConfigFile = configFile.Mode120_settings()
    Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

    CCD_settings = configFile.CCD_macro_settings("FullReadout")
    dark_settings = None
    if len(Mode_settings["dark_channels"])>0:
        dark_settings = configFile.CCD_macro_settings(Mode_settings["dark_settings"])
    # "Set TEXPMS to 0 for CCDs that are not going to take snapshots"
    # for CCDSEL in [1, 2, 4, 8, 16, 32, 64]:
    #     if CCDSEL in Mode_settings["CCDSELs"]:
    #         continue
    #     else:
    #         CCD_settings[CCDSEL]["TEXPMS"] = 0

    Mode12X(
        root,
        date,
        duration,
        relativeTime,
        Timeline_settings=Timeline_settings,
        configFile=configFile,
        Mode_settings=Mode_settings,
        CCD_settings=CCD_settings,
        dark_settings=dark_settings
    )


################################################################################################

def SNAPSHOT(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """SNAPSHOT. 

    Schedules SNAPSHOT with defined parameters.
    """

    Logger.info('')
    Logger.info('Start of SNAPSHOT')

    Logger.debug('Test_settings from Science Mode List: '+str(Mode_settings))

    CCD_settings = configFile.CCD_macro_settings('FullReadout')

    ExpTimes = Mode_settings['ExpTimes']
    SnapshotTimes = Mode_settings['SnapshotTimes']
    pointing_altitude = Mode_settings['pointing_altitude']
    SnapshotSpacing = Mode_settings['SnapshotSpacing']
    CCDSELs = Mode_settings['CCDSELs']

    Mode_name = sys._getframe(0).f_code.co_name

    t = 0

    initial_relativeTime = relativeTime
    starttime = DT.datetime.strptime(Timeline_settings['start_date'],'%Y/%m/%d %H:%M:%S')
    
    Disregarded, Disregarded, Disregarded, TEXPIMS = Library.SyncArgCalculator(
    CCD_settings,
    Timeline_settings["CCDSYNC_ExtraOffset"],
    Timeline_settings["CCDSYNC_ExtraIntervalTime"],
    )

    relativeTime = Commands.TC_pafMode(
        root, relativeTime, MODE=2, Timeline_settings=Timeline_settings, configFile=configFile, comment=""
    )

    if pointing_altitude != -1:
        relativeTime = Commands.TC_acfLimbPointingAltitudeOffset(
            root,
            relativeTime,
            Initial=pointing_altitude,
            Final=pointing_altitude,
            Rate=0,
            Timeline_settings=Timeline_settings, configFile=configFile,
        )
    
    relativeTime = Macros.SetCCDs_macro(
        root,
        relativeTime,
        CCD_settings,
        TEXPIMS=TEXPIMS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment="",
    )

    change = False


    "Start looping the CCD settings and call for macros"
    for SnapshotTime in SnapshotTimes:
        snaptime =  DT.datetime.strptime(SnapshotTime,'%Y/%m/%d %H:%M:%S')
        relativeTime = (snaptime-starttime).seconds
        
        for CCD in CCDSELs:

            for ExpTime in ExpTimes:

                if CCD_settings[CCD]['TEXPMS'] != ExpTime:
                    CCD_settings[CCD]['TEXPMS'] = ExpTime
                    change = True

                if change:
                    relativeTime = Macros.SetCCDs_macro(
                        root,
                        relativeTime,
                        CCD_settings,
                        TEXPIMS=TEXPIMS,
                        Timeline_settings=Timeline_settings, configFile=configFile,
                        CCDList = [CCD],
                        comment="",
                    )

                    change = False
                
                snaptime_real = (DT.timedelta(seconds=relativeTime) + starttime)

                comment = (Mode_name+', '+str(snaptime_real)+', '+', pointing_altitude = '+str(pointing_altitude) +
                            ', ExpTime = '+str(ExpTime))
                
                Logger.debug(comment)

                relativeTime = Commands.TC_pafCCDSnapshot(
                    root,
                    relativeTime,
                    CCDSEL=CCD,
                    Timeline_settings=Timeline_settings, configFile=configFile,
                    comment=comment,
                )
                
                relativeTime = relativeTime + SnapshotSpacing + ExpTime/1000




    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of SNAPSHOT')

    return relativeTime, current_time


# ##############################################################################################


# def Mode121(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode121

#     **Macro**: Snapshot_Inertial_macro. \n
#     **CCD_Macro**: FullReadout \n

#     Stare at a point in inertial reference frame and take one Snapshot with each CCDSEL argument defined by the 'CCDSELs' settings and also do not have TEXPMS set to 0.

#     """

#     Mode_settings_ConfigFile = configFile.Mode121_settings()
#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     CCD_settings = configFile.CCD_macro_settings("FullReadout")
#     "Set TEXPMS to 0 for CCDs that are not going to take snapshots"
#     for CCDSEL in [1, 2, 4, 8, 16, 32, 64]:
#         if CCDSEL in Mode_settings["CCDSELs"]:
#             continue
#         else:
#             CCD_settings[CCDSEL]["TEXPMS"] = 0

#     Mode12X(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         configFile=configFile,
#         Mode_settings=Mode_settings,
#         CCD_settings=CCD_settings,
#     )


# ############################################################################################


# def Mode122(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode122

#     **Macro**: Snapshot_Inertial_macro. \n
#     **CCD_Macro**: BinnedCalibration with configurable exposure time of UV and IR CCDs. \n

#     Stare at a point in inertial reference frame and take a Snapshot with each CCD except nadir and also do not have TEXPMS set to 0.

#     """

#     Mode_settings_ConfigFile = configFile.Mode122_settings()
#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     CCD_settings = configFile.CCD_macro_settings("BinnedCalibration")
#     ExpTimeUV = Mode_settings["Exp_Time_UV"]
#     ExpTimeIR = Mode_settings["Exp_Time_IR"]
#     CCD_settings[16]["TEXPMS"] = ExpTimeUV
#     CCD_settings[32]["TEXPMS"] = ExpTimeUV
#     CCD_settings[1]["TEXPMS"] = ExpTimeIR
#     CCD_settings[8]["TEXPMS"] = ExpTimeIR
#     CCD_settings[2]["TEXPMS"] = ExpTimeIR
#     CCD_settings[4]["TEXPMS"] = ExpTimeIR

#     Mode12X(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         configFile=configFile,
#         Mode_settings=Mode_settings,
#         CCD_settings=CCD_settings,
#     )


# ################################################################################################

# ############################################################################################


# def Mode123(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode123


#     **Macro**: Snapshot_Inertial_macro. \n
#     **CCD_Macro**: LowPixel with configurable exposure time of UV and IR CCDs. \n

#     Stare at a point in inertial reference frame and take a Snapshot with each CCD except nadir and also do not have TEXPMS set to 0.


#     """

#     Mode_settings_ConfigFile = configFile.Mode123_settings()
#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     CCD_settings = configFile.CCD_macro_settings("LowPixel")
#     ExpTimeUV = Mode_settings["Exp_Time_UV"]
#     ExpTimeIR = Mode_settings["Exp_Time_IR"]
#     CCD_settings[16]["TEXPMS"] = ExpTimeUV
#     CCD_settings[32]["TEXPMS"] = ExpTimeUV
#     CCD_settings[1]["TEXPMS"] = ExpTimeIR
#     CCD_settings[8]["TEXPMS"] = ExpTimeIR
#     CCD_settings[2]["TEXPMS"] = ExpTimeIR
#     CCD_settings[4]["TEXPMS"] = ExpTimeIR

#     Mode12X(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         configFile=configFile,
#         Mode_settings=Mode_settings,
#         CCD_settings=CCD_settings,
#     )


# ##############################################################################################


# def Mode124(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode124

#     **Macro**: Snapshot_Inertial_macro. \n
#     **CCD_Macro**: FullReadout. \n

#     Stare at a point in inertial reference frame and take one Snapshot with each CCDSEL argument defined by the 'CCDSELs' settings and also do not have TEXPMS set to 0. 
#     Used for moon calibration.
#     """

#     Mode_settings_ConfigFile = configFile.Mode124_settings()
#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     CCD_settings = configFile.CCD_macro_settings("FullReadout")

#     "Set TEXPMS to 0 for CCDs that are not going to take snapshots"
#     for CCDSEL in [1, 2, 4, 8, 16, 32]:
#         if CCDSEL in Mode_settings["CCDSELs"]:
#             continue
#         else:
#             CCD_settings[CCDSEL]["TEXPMS"] = 0

#     Mode12X(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         configFile=configFile,
#         Mode_settings=Mode_settings,
#         CCD_settings=CCD_settings,
#     )


# ##############################################################################################


# ################################################################################################


# def Mode130(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode130

#     **Macro**: Snapshot_Limb_Pointing_macro. \n
#     **CCD_Macro**: FullReadout. \n

#     Look at fixed limb altitude and take Snapshots with all CCD except nadir  and also do not have TEXPMS set to 0.
#     """

#     CCD_settings = configFile.CCD_macro_settings("FullReadout")
#     Mode_settings_ConfigFile = configFile.Mode130_settings()

#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     Mode_name = sys._getframe(0).f_code.co_name
#     comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

#     pointing_altitude = Mode_settings["pointing_altitude"]
#     SnapshotSpacing = Mode_settings["SnapshotSpacing"]

#     # Mode_macro = getattr(Macros,Mode_name+'_macro')

#     Macros.Snapshot_Limb_Pointing_macro(
#         root,
#         round(relativeTime, 2),
#         CCD_settings,
#         pointing_altitude=pointing_altitude,
#         SnapshotSpacing=SnapshotSpacing,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )


# #####################################################################################################

# ##############################################################################################


# def Mode131(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode131

#     **Macro**: Operational_Limb_Pointing_macro. \n
#     **CCD_Macro**: FullReadout. \n

#     Look at fixed limb altitude in operational mode.
#     """

#     CCD_settings = configFile.CCD_macro_settings("FullReadout")
#     PM_settings = configFile.PM_settings()
#     Mode_settings_ConfigFile = configFile.Mode131_settings()

#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     Mode_name = sys._getframe(0).f_code.co_name
#     comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

#     pointing_altitude = Mode_settings["pointing_altitude"]
#     relativeTimeEndOfMode = (
#         relativeTime + duration - 2*Timeline_settings["mode_separation"] - Timeline_settings["pointing_stabilization"]
#     )  # go to idle mode separation (s) before endDate

#     "CMDs and Macros"
#     Macros.Operational_Limb_Pointing_macro(
#         root,
#         round(relativeTime, 2),
#         CCD_settings,
#         PM_settings=PM_settings,
#         pointing_altitude=pointing_altitude,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )

#     Commands.TC_pafMode(
#         root,
#         relativeTimeEndOfMode-Timeline_settings["mode_separation"],
#         MODE=2,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )

#     Commands.TC_acfLimbPointingAltitudeOffset(
#         root,
#         relativeTimeEndOfMode,
#         Initial=Timeline_settings["StandardPointingAltitude"],
#         Final=Timeline_settings["StandardPointingAltitude"],
#         Rate=0,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )


# ################################################################################################

# ##############################################################################################


# def Mode132_133(
#         root, date, duration, relativeTime, Timeline_settings, Mode_settings, configFile, CCD_settings):
#     """Subfunction of Mode132 and Mode133

#     **Macro**: Operational_Limb_Pointing_macro. \n

#     Arguments:
#         CCD_settings (:obj:`dict` of :obj:`dict` of int): Settings for the CCDs. Defined in the *Configuration File*.

#     Look at fixed limb altitude in operational mode with a set of exposure times for UV and IR CCDs.
#     """

#     Mode_name = sys._getframe(1).f_code.co_name.replace("", "")
#     comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

#     PM_settings = configFile.PM_settings()
#     pointing_altitude = Mode_settings["pointing_altitude"]
#     relativeTimeEndOfMode = (
#         relativeTime + duration - Timeline_settings["mode_separation"]
#     )  # go to idle mode separation (s) before endDate

#     for ExpTimeUV, ExpTimeIR in zip(
#         Mode_settings["Exp_Times_UV"], Mode_settings["Exp_Times_IR"]
#     ):

#         CCD_settings[16]["TEXPMS"] = ExpTimeUV
#         CCD_settings[32]["TEXPMS"] = ExpTimeUV
#         CCD_settings[1]["TEXPMS"] = ExpTimeIR
#         CCD_settings[8]["TEXPMS"] = ExpTimeIR
#         CCD_settings[2]["TEXPMS"] = ExpTimeIR
#         CCD_settings[4]["TEXPMS"] = ExpTimeIR
#         relativeTime = Macros.Operational_Limb_Pointing_macro(
#             root,
#             round(relativeTime, 2),
#             CCD_settings,
#             PM_settings=PM_settings,
#             pointing_altitude=pointing_altitude,
#             Timeline_settings=Timeline_settings,
#             configFile=configFile,
#             comment=comment,
#         )

#         relativeTime = relativeTime + Mode_settings["session_duration"]

#     Commands.TC_pafMode(
#         root,
#         relativeTimeEndOfMode,
#         MODE=2,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )


# ################################################################################################

# ################################################################################################


# def Mode132(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode132

#     **Macro**: Operational_Limb_Pointing_macro. \n
#     **CCD_Macro**: BinnedCalibration with changing exposure times for UV and IR CCDs. \n

#     Look at fixed limb altitude in operational mode for a set duration with each exposure time.
#     """

#     CCD_settings = configFile.CCD_macro_settings("BinnedCalibration")
#     Mode_settings_ConfigFile = configFile.Mode132_settings()

#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     Mode132_133(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         Mode_settings=Mode_settings,
#         configFile=configFile,
#         CCD_settings=CCD_settings,
#     )


# ##############################################################################################

# ################################################################################################


# def Mode133(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode133,

#     **Macro**: Operational_Limb_Pointing_macro. \n
#     **CCD_Macro**: LowPixel with changing exposure times for UV and IR CCDs. \n

#     Look at fixed limb altitude in operational mode for a set duration with each exposure time.
#     """

#     CCD_settings = configFile.CCD_macro_settings("LowPixel")
#     Mode_settings_ConfigFile = configFile.Mode133_settings()

#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     Mode132_133(
#         root,
#         date,
#         duration,
#         relativeTime,
#         Timeline_settings=Timeline_settings,
#         Mode_settings=Mode_settings,
#         configFile=configFile,
#         CCD_settings=CCD_settings,
#     )


# ##############################################################################################

# ##############################################################################################


# def Mode134(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
#     """Mode134, Operational_Limb_Pointing_macro.

#     **Macro**: Operational_Limb_Pointing_macro. \n
#     **CCD_Macro**: CustomBinning \n

#     Look at fixed limb altitude in Operational Mode.
#     """

#     CCD_settings = configFile.CCD_macro_settings("CustomBinning")
#     PM_settings = configFile.PM_settings()
#     Mode_settings_ConfigFile = configFile.Mode134_settings()

#     Mode_settings = dict_comparator(Mode_settings, Mode_settings_ConfigFile, Logger)

#     Mode_name = sys._getframe(0).f_code.co_name
#     comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)

#     pointing_altitude = Mode_settings["pointing_altitude"]
#     relativeTimeEndOfMode = (
#         relativeTime + duration - Timeline_settings["mode_separation"]
#     )  # go to idle mode separation (s) before endDate

#     "CMDs and Macros"
#     Macros.Operational_Limb_Pointing_macro(
#         root,
#         round(relativeTime, 2),
#         CCD_settings,
#         PM_settings=PM_settings,
#         pointing_altitude=pointing_altitude,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )


#     Commands.TC_pafMode(
#         root,
#         relativeTimeEndOfMode-Timeline_settings["pointing_stabilization"]-Timeline_settings["CMD_separation"],
#         MODE=2,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )

#     Commands.TC_acfLimbPointingAltitudeOffset(
#         root,
#         relativeTimeEndOfMode-Timeline_settings["pointing_stabilization"],
#         Initial=Timeline_settings["StandardPointingAltitude"],
#         Final=Timeline_settings["StandardPointingAltitude"],
#         Rate=0,
#         Timeline_settings=Timeline_settings, configFile=configFile,
#         comment=comment,
#     )
    


################################################################################################

##############################################################################################


##############################################################################################


def X(root, date, duration, relativeTime, Timeline_settings, configFile, Mode_settings={}):
    """This is a template for a new mode or test. Exchange 'X' for the name of the new mode/test"

    Currently this template mode only schedules a *TC_acfLimbPointingAltitudeOffset* CMD.
    """

    "Calls for settings stated in the Configuration File"
    # Mode_settings_ConfigFile = configFile.X_settings()
    "Calls for CCD settings for a specific CCD macro, here the CCD macro is 'CustomBinning'"
    CCD_settings = configFile.CCD_macro_settings("CustomBinning")

    "Compares settings given in the Science Mode Timeline to settings given in the Configuration File"
    # Mode_settings = dict_comparator(Mode_settings,Mode_settings_ConfigFile)

    Mode_name = sys._getframe(0).f_code.co_name
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Mode_settings)
    relativeTimeEndOfMode = (
        relativeTime + duration - Timeline_settings["mode_separation"]
    )

    Commands.TC_acfLimbPointingAltitudeOffset(
        root,
        round(relativeTime, 2),
        Initial=120000,
        Final=120000,
        Rate=0,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    "A call for the macro called Operational_Limb_Pointing_macro"
    Macros.Operational_Limb_Pointing_macro(
        root=root,
        relativeTime=round(relativeTime, 2),
        CCD_settings=CCD_settings,
        PM_settings=configFile.PM_settings,
        pointing_altitude=120000,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    Commands.TC_pafMode(
        root,
        relativeTimeEndOfMode,
        MODE=2,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )


#######################################################################################################
