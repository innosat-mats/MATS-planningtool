# -*- coding: utf-8 -*-
"""
Tests are used during the commisioning phase of the satellite. The Tests are defined by Ole Martin Christensen. \n

Generates and calculates parameters for each Test used during the commisioning phase, and converts them to strings,
then calls for macros, which will generate commands in the XML-file. \n

Functions on the form "X", where the X is any Test, except for 'All_Tests' which schedules every Test.
    
    **Arguments:**
        **root** (*lxml.etree.Element*):  XML tree structure. Main container object for the ElementTree API. \n
        **date** (*ephem.Date*): Starting date of the Test. On the form of the ephem.Date class. \n
        **duration** (*int*): The duration of the test [s]. \n
        **relativeTime** (*int*): The starting time of the mode with regard to the start of the timeline [s]. \n
        **Timeline_settings** (*dict*): Dictionary containing the settings of the Timeline given in either the *Science_Mode_Timeline* or the *Configuration File*. \n
        **Test_settings** (*dict*): Dictionary containing the settings of the *Test* given in the *Science_Mode_Timeline*.

    Returns:
        None

When creating new Test functions it is crucial that the function name is
*Test_name*, where *Test_name* is the same as the string used in the Science Mode Timeline.

@author: David Skånberg
"""

from mats_planningtool.XMLGenerator.Modes_and_Tests.Macros_Commands import Macros, Commands
import ephem
import logging
import sys
import importlib
import skyfield.api
from pylab import dot, arccos, zeros, pi, sin, cos, arctan, cross, norm, sqrt
import datetime as DT
from mats_planningtool import Library
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator
#from mats_planningtool_Config_File import Logger_name, Timeline_settings, getTLE


Logger = logging.getLogger("OPT_logger")

###########################################################################################################
def WDWJQ_3010(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings):
    """WDWJQ_3010. 

    Schedules WDWJQ_3010 with defined parameters.
    """

    Logger.info('')
    Logger.info('Start of WDWJQ_3010')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    CCD_settings = configFile.CCD_macro_settings('CustomBinning')

    JPEGQs = Test_settings['JPEGQs']
    WDWs =Test_settings['WDWs']
    altitudes = Test_settings['Altitudes']
    ExpTimes = Test_settings['ExpTimes']
    SnapshotSpacing = 5

    Mode_name = sys._getframe(0).f_code.co_name

    t = 0

    initial_relativeTime = relativeTime

    "Start looping the CCD settings and call for macros"
    for JPEGQ in JPEGQs:
        for WDW in WDWs:
            for altitude in altitudes:
                for ExpTime in ExpTimes:


                    for key in CCD_settings.keys():
                        CCD_settings[key]['JPEGQ'] = JPEGQ
                        CCD_settings[key]['WDW'] = WDW
                        CCD_settings[key]['TEXPMS'] = ExpTime

                            
                    comment = (Mode_name+', '+str(date)+', '+', pointing_altitude = '+str(altitude) +
                                ', ExpTime = '+str(ExpTime)+', JPEGQ = '+str(JPEGQ))
                    Logger.debug(comment)

                    relativeTime = Macros.Snapshot_Limb_Pointing_macro(root, round(
                        relativeTime, 2), CCD_settings, pointing_altitude=altitude, SnapshotSpacing=SnapshotSpacing, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

                    relativeTime = relativeTime + SnapshotSpacing

                    relativeTime = Macros.NadirSnapshot_Limb_Pointing_macro(root, round(
                        relativeTime, 2), CCD_settings, pointing_altitude=altitude, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)


    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of WDWJQ_3010')

    return relativeTime, current_time

####################################################################################




###########################################################################################################
def FFEXP_3000(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings):
    """FFEXP_3000. 

    Schedules FFEXP_3000 with defined parameters.
    """

    Logger.info('')
    Logger.info('Start of FFEXP_3000')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    CCD_settings = configFile.CCD_macro_settings('FullReadout')

    ExpTimes = Test_settings['ExpTimes']
    SnapshotTimes = Test_settings['SnapshotTimes']
    altitude = Test_settings['Altitude']
    SnapshotSpacing = 10

    Mode_name = sys._getframe(0).f_code.co_name

    t = 0

    initial_relativeTime = relativeTime
    starttime = DT.datetime.strptime(Timeline_settings['start_date'],'%Y/%m/%d %H:%M:%S')

    "Start looping the CCD settings and call for macros"
    for SnapshotTime in SnapshotTimes:

        snaptime =  DT.datetime.strptime(SnapshotTime,'%Y/%m/%d %H:%M:%S')
        relativeTime = (snaptime-starttime).seconds

        for ExpTime in ExpTimes:

            for key in CCD_settings.keys():
                CCD_settings[key]['TEXPMS'] = ExpTime

                    
            comment = (Mode_name+', '+str(snaptime)+', '+', pointing_altitude = '+str(altitude) +
                        ', ExpTime = '+str(ExpTime))
            Logger.debug(comment)

            relativeTime = Macros.Snapshot_Limb_Pointing_macro(root, round(
                relativeTime, 2), CCD_settings, pointing_altitude=altitude, SnapshotSpacing=SnapshotSpacing, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

            relativeTime = relativeTime + SnapshotSpacing

            relativeTime = Macros.NadirSnapshot_Limb_Pointing_macro(root, round(
                relativeTime, 2), CCD_settings, pointing_altitude=altitude, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)



    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of FFEXP_3000')

    return relativeTime, current_time

####################################################################################



######################################################################################

def STAR_3040(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings):
    """STAR_3040. 

    Schedules STAR_3040 with defined parameters.
    """

    Logger.info('')
    Logger.info('Start of STAR_3040')
    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    CCD_settings = configFile.CCD_macro_settings('FullReadout')
    ExpTimes = Test_settings['ExpTimes']
    SnapshotSpacing = 5
    pointing_altitude = Test_settings["pointing_altitude"]
    pointing_altitude_end = Test_settings["pointing_altitude_end"] #this is a dummy variable just to get correct time for limb reset

    Mode_name = sys._getframe(0).f_code.co_name
    comment = Mode_name + " starting date: " + str(date) + ", " + str(Test_settings)

    freeze_start_utc = ephem.Date(date + ephem.second * Test_settings["freeze_start"])
    FreezeTime = freeze_start_utc

    FreezeDuration = Test_settings["freeze_duration"]
    SnapshotSpacing = Test_settings["SnapshotSpacing"]

    Logger.debug("freeze_start_utc: " + str(freeze_start_utc))
    Logger.debug("FreezeDuration: " + str(FreezeDuration))

    comment = comment + ", Snapshot_Inertial_macro"
    
    #FIXME: This is a bit ugly, probably FreezeTime_rel should be used as input argument
    startdate = DT.datetime.strptime(Timeline_settings["start_date"],'%Y/%m/%d %H:%M:%S')
    FreezeTime_rel = int((FreezeTime.datetime()-startdate).total_seconds())


    TEXPIMS = 120000

    relativeTime = Commands.TC_pafMode(
        root, relativeTime, MODE=2, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment
    )

    relativeTime = Commands.TC_acfLimbPointingAltitudeOffset(
        root,
        relativeTime,
        Initial=pointing_altitude,
        Final=pointing_altitude,
        Rate=0,
        Timeline_settings=Timeline_settings,
        configFile=configFile,
        comment=comment,
    )

    relativeTime = Macros.SetCCDs_macro(
        root,
        relativeTime,
        CCD_settings,
        TEXPIMS,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    relativeTime = Commands.TC_acsPayloadAttitudeFreeze(
        root,
        FreezeTime_rel,
        FreezeDuration=FreezeDuration,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )

    for ExpTime in ExpTimes:
        
        for key in CCD_settings.keys():
            CCD_settings[key]['TEXPMS'] = ExpTime

        "CCDSEL arguments in order of increasing TEXPMS"
        CCDSELs = Test_settings["CCDSELs"]

        relativeTime = Macros.SetCCDs_macro(
            root,
            relativeTime,
            CCD_settings,
            TEXPIMS=TEXPIMS,
            Timeline_settings=Timeline_settings, configFile=configFile,
            CCDList = CCDSELs,
            comment=comment,
        )
        
        for CCDSEL in CCDSELs:
            relativeTime = Commands.TC_pafCCDSnapshot(
                root,
                relativeTime,
                CCDSEL=CCDSEL,
                Timeline_settings=Timeline_settings, configFile=configFile,
                comment=comment,
            )

            relativeTime += SnapshotSpacing + CCD_settings[CCDSEL]['TEXPMS']/1000

    configFile.current_pointing = pointing_altitude_end #should be calulated from Freeze time

    relativeTime = Commands.TC_acfLimbPointingAltitudeOffset(
        root,
        relativeTime,
        Initial=Timeline_settings["StandardPointingAltitude"],
        Final=Timeline_settings["StandardPointingAltitude"],
        Rate=0,
        Timeline_settings=Timeline_settings, configFile=configFile,
        comment=comment,
    )
    # relativeTime = Commands.TC_pafMode(root, relativeTime, MODE = 1, Timeline_settings = Timeline_settings, configFile=configFile, comment = comment)

    Logger.info('End of STAR_3040')

    return relativeTime

####################################################################################



###########################################################################################################
def LMBF_3050(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings):
    """LMBF_3050. 

    Schedules LMBF_3050 with defined parameters.
    """

    Logger.info('')
    Logger.info('Start of LMBF_3050')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    CCD_settings = configFile.CCD_macro_settings('FullReadout')

    ExpTimes = Test_settings['ExpTimes']
    SnapshotTimes = Test_settings['SnapshotTimes']
    altitude = Test_settings['Altitude']
    SnapshotSpacing = 5

    Mode_name = sys._getframe(0).f_code.co_name

    initial_relativeTime = relativeTime
    starttime = DT.datetime.strptime(Timeline_settings['start_date'],'%Y/%m/%d %H:%M:%S')

    "Start looping the CCD settings and call for macros"
    for SnapshotTime in SnapshotTimes:

        snaptime =  DT.datetime.strptime(SnapshotTime,'%Y/%m/%d %H:%M:%S')
        relativeTime = (snaptime-starttime).seconds

        for ExpTime in ExpTimes:

            for key in CCD_settings.keys():
                CCD_settings[key]['TEXPMS'] = ExpTime

                    
            comment = (Mode_name+', '+str(snaptime)+', '+', pointing_altitude = '+str(altitude) +
                        ', ExpTime = '+str(ExpTime))
            Logger.debug(comment)

            relativeTime = Macros.Snapshot_Limb_Pointing_macro(root, round(
                relativeTime, 2), CCD_settings, pointing_altitude=altitude, SnapshotSpacing=SnapshotSpacing, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of LMBF_3050')

    return relativeTime, current_time

####################################################################################




def All_Tests(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings=['Limb_functional_test', 'Photometer_test_1', 'CCD_stability_test', 'Nadir_functional_test']):
    """ Runs all the Test functions which have their function name as a string in the input *Test_settings*.

    Allows the tests to be dynamically scheduled. Meaning that when the previous test is done another done starts immediately after. 
    This eliminates the need to give an approximated duration of any specfic Test as their exact duration is unknown beforehand.

    """

    "Set duration to length of timeline to allow all tests to be scheduled"
    duration = Timeline_settings['duration']['duration']

    if('Limb_functional_test' in Test_settings):
        relativeTime, date = Limb_functional_test(
            root, date, duration=duration, relativeTime=relativeTime, Timeline_settings=Timeline_settings, configFile=configFile)
    if('Photometer_test_1' in Test_settings):
        relativeTime, date = Photometer_test_1(
            root, date, duration=5400, relativeTime=relativeTime, Timeline_settings=Timeline_settings, configFile=configFile)
    if('CCD_stability_test' in Test_settings):
        relativeTime, date = CCD_stability_test(
            root, date, duration=duration, relativeTime=relativeTime, Timeline_settings=Timeline_settings, configFile=configFile)
    if('Nadir_functional_test' in Test_settings):
        relativeTime, date = Nadir_functional_test(
            root, date, duration=duration, relativeTime=relativeTime, Timeline_settings=Timeline_settings, configFile=configFile)

    "Update duration in the Timeline"
    root[0][2][1].text = str(relativeTime + Timeline_settings['mode_separation'])


def Limb_functional_test(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings={'ExpTimes': [1000, 2000, 4000, 8000, 16000]}):
    """Limb_functional_test. 

    Schedules Limb_functional_test with defined parameters and simulates MATS propagation from TLE.
    Scheduling of all daylight and nighttime commands are separated timewise and all commands for one of the two is scheduled first.
    """

    Logger.info('')
    Logger.info('Start of Limb_functional_test')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    log_timestep = 500
    Logger.debug('log_timestep [s]: '+str(log_timestep))

    TLE = configFile.getTLE()

    CCD_settings = configFile.CCD_macro_settings('FullReadout')

    duration_flag = 0

    JPEGQs = [100, 95]
    WDWs = [7, 128]
    altitudes = [50000, 70000, 90000, 110000, 130000, 160000, 200000]
    ExpTimes = Test_settings['ExpTimes']
    SnapshotSpacing = 5

    R_mean = 6371  # km
    Altitude_defining_night = 45  # km
    Altitude_defining_day = 25  # km

    #lat = Test_settings['lat']/180*pi
    lat = 30

    Mode_name = sys._getframe(0).f_code.co_name

    "Estimation of the angle [degrees] between the sun and the LP when it enters eclipse"
    #NightDayAngle = arccos(R_mean/(R_mean+Altitude_defining_night))/pi*180 + 90

    NightAngle = arccos(R_mean/(R_mean+Altitude_defining_night))/pi*180 + 90
    DayAngle = arccos(R_mean/(R_mean+Altitude_defining_day))/pi*180 + 90

    Logger.debug('')
    Logger.debug('NightAngle : '+str(NightAngle))
    Logger.debug('DayAngle : '+str(DayAngle))

    timestep = 4
    t = 0

    initial_relativeTime = relativeTime

    "Consecutively schedule all Macros for day, and then night"
    for mode in ['Day', 'Night']:

        "Altitudes that defines the LP"
        for altitude in altitudes:

            "Start looping the CCD settings and call for macros"
            for JPEGQ, WDW in zip(JPEGQs, WDWs):

                for key in CCD_settings.keys():
                    CCD_settings[key]['JPEGQ'] = JPEGQ
                    CCD_settings[key]['WDW'] = WDW

                for ExpTime in ExpTimes:

                    for key in CCD_settings.keys():
                        CCD_settings[key]['TEXPMS'] = ExpTime

                    ############################################################################
                    ########################## Orbit simulator #################################
                    ############################################################################

                    MATS_skyfield = skyfield.api.EarthSatellite(TLE[0], TLE[1])

                    "Calculate the current angle between MATS and the Sun and the latitude of the LP"
                    "and Loop until it is either day or night and the right latitude"
                    while(True):

                        mode_relativeTime = relativeTime - initial_relativeTime
                        current_time = ephem.Date(date+ephem.second*mode_relativeTime)
                        current_time_datetime = current_time.datetime()

                        if(mode_relativeTime > duration and duration_flag == 0):
                            Logger.warning(
                                'Warning!! The scheduled time for the Test has ran out.')
                            #input('Enter anything to continue:\n')
                            duration_flag = 1

                        if(t*timestep % log_timestep == 0):
                            LogFlag = True
                        else:
                            LogFlag = False

                        Satellite_dict = Satellite_Simulator(
                            MATS_skyfield, current_time, Timeline_settings, altitude/1000, LogFlag, Logger)

                        r_MATS = Satellite_dict['Position [km]']
                        lat_MATS = Satellite_dict['Latitude [degrees]']
                        lat_LP = Satellite_dict['EstimatedLatitude_LP [degrees]']

                        sun_angle = Library.SunAngle(r_MATS, current_time)

                        if(LogFlag == True):
                            Logger.debug('sun_angle: '+str(sun_angle))

                        if((sun_angle < DayAngle and abs(lat_LP) <= lat and mode == 'Day') or
                                (sun_angle > NightAngle and abs(lat_LP) <= lat and mode == 'Night')):

                            Logger.debug('!!Break of Loop!!')
                            Logger.debug('Loop Counter (t): '+str(t))
                            Logger.debug('current_time: '+str(current_time))
                            Logger.debug('lat_MATS [degrees]: '+str(lat_MATS))
                            Logger.debug('lat_LP [degrees]: '+str(lat_LP))
                            Logger.debug('sun_angle [degrees]: '+str(sun_angle))
                            Logger.debug('mode: '+str(mode))
                            Logger.debug('')

                            break

                        "Increase Loop counter"
                        t = t+1

                        "Timestep for propagation of MATS"
                        relativeTime = round(relativeTime + timestep, 2)

                    ############################################################################
                    ########################## End of Orbit simulator ##########################
                    ############################################################################

                    comment = (Mode_name+', '+str(date)+', '+str(mode)+', pointing_altitude = '+str(altitude) +
                               ', ExpTime = '+str(ExpTime)+', JPEGQ = '+str(JPEGQ))
                    Logger.debug(comment)

                    relativeTime = Macros.Snapshot_Limb_Pointing_macro(root, round(
                        relativeTime, 2), CCD_settings, pointing_altitude=altitude, SnapshotSpacing=SnapshotSpacing, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

                    # relativeTime = Macros.Limb_functional_test_macro(root = root, relativeTime = str(relativeTime),
                    #                           pointing_altitude = str(altitude), ExpTime = str(ExpTime),
                    #                           JPEGQ = JPEGQ, comment=comment)

                    #"Postpone next command until at least the end of ExpTime"
                    #relativeTime = round(relativeTime + ExpTime/1000,2)

    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of Limb_functional_test')

    return relativeTime, current_time





#############################################################################################

#############################################################################################


def Photometer_test_1(root, date, relativeTime, duration, Timeline_settings, configFile, Test_settings={'ExpTimes': [1000, 2000, 4000, 8000, 16000]}):
    """Photometer_test_1

    Sets the payload in operational mode and then cycles PM settings as defined in the Test.
    """

    # Test_settings = params_checker(Test_settings,Mode=X=_settings)

    Logger.info('')
    Logger.info('Start of Photometer_test_1')

    Logger.debug('')

    CCD_settings = configFile.CCD_macro_settings('BinnedCalibration')
    ExpTimes = Test_settings['ExpTimes']

    initial_relativeTime = relativeTime

    session_duration = 120

    Test_name = sys._getframe(0).f_code.co_name

    Photometer_test_1_duration = duration

    pointing_altitude = Timeline_settings['StandardPointingAltitude']

    "Start looping the TEXPMS for the Photometer and call for macros"
    while(True):
        mode_relativeTime = round(relativeTime - initial_relativeTime, 2)

        if(mode_relativeTime >= Photometer_test_1_duration):
            break

        for ExpTime in ExpTimes:
            ExpInt = ExpTime + 500

            PM_settings = {'TEXPMS': ExpTime, 'TEXPIMS': ExpInt}
            comment = (Test_name+', '+str(date) +
                       ', ExpTime = '+str(ExpTime)+', ExpInt = '+str(ExpInt))

            Logger.debug(comment)

            relativeTime = Macros.Operational_Limb_Pointing_macro(root, relativeTime=relativeTime, CCD_settings=CCD_settings,
                                                                  PM_settings=PM_settings, pointing_altitude=pointing_altitude,
                                                                  Timeline_settings=Timeline_settings,  configFile=configFile, comment=comment)

            "Postpone Next PM settings"
            relativeTime = relativeTime + session_duration

    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of Photometer_test_1')

    return relativeTime, current_time


##############################################################################################

##############################################################################################


def Nadir_functional_test(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings={'ExpTimes': [1000, 2000, 4000, 8000, 16000]}):
    """Nadir_functional_test

    Schedules Nadir_functional_test with defined parameters and simulates MATS propagation from TLE.
    Scheduling of all daylight and nighttime commands are separated timewise and all commands for one of the two is scheduled first.
    """

    Logger.info('')
    Logger.info('Start of Nadir_functional_test')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))

    CCD_settings = configFile.CCD_macro_settings('FullReadout')
    altitude = Timeline_settings['StandardPointingAltitude']

    ExpTimes = Test_settings['ExpTimes']

    log_timestep = 500
    Logger.debug('log_timestep [s]: '+str(log_timestep))

    duration_flag = 0

    JPEGQs = [100, 95]
    WDWs = [7, 128]

    initial_relativeTime = relativeTime

    TLE = configFile.getTLE()
    MATS_skyfield = skyfield.api.EarthSatellite(TLE[0], TLE[1])

    Altitude_defining_night = 45  # km
    Altitude_defining_day = 25  # km
    R_mean = 6371

    # Estimation of the angle [degrees] between the sun and the FOV position when it enters eclipse
    NightAngle = arccos(R_mean/(R_mean+Altitude_defining_night))/pi*180 + 90
    DayAngle = arccos(R_mean/(R_mean+Altitude_defining_day))/pi*180 + 90

    Logger.debug('')
    Logger.debug('DayAngle : '+str(DayAngle))
    Logger.debug('NightAngle : '+str(NightAngle))
    Logger.debug('')

    withinLat = 30

    Mode_name = sys._getframe(0).f_code.co_name

    t = 0
    timestep = 4

    # latMargin = 360/5400 * timestep * 5 #Overly estimated change of latitude per timestep

    "Start looping the CCD nadir settings and call for macros"
    for mode in ['Day', 'Night']:

        for JPEGQ, WDW in zip(JPEGQs, WDWs):

            CCD_settings[64]['JPEGQ'] = JPEGQ
            CCD_settings[64]['WDW'] = WDW

            for ExpTime in ExpTimes:

                CCD_settings[64]['TEXPMS'] = ExpTime

                ############################################################################
                ########################## Orbit simulator #################################
                ############################################################################

                # for lat in [-30, 0, 30]:

                "Calculate the current angle between MATS and the Sun"
                "and Loop until it is either day or night and the right latitude"
                while(True):

                    mode_relativeTime = relativeTime - initial_relativeTime
                    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

                    if(mode_relativeTime > duration and duration_flag == 0):
                        Logger.warning(
                            'Warning!! The scheduled time for the Test has ran out.')
                        #input('Enter anything to continue:\n')
                        duration_flag = 1

                    if(t*timestep % log_timestep == 0):
                        LogFlag = True
                    else:
                        LogFlag = False

                    Satellite_dict = Satellite_Simulator(
                        MATS_skyfield, current_time, Timeline_settings, altitude/1000, LogFlag, Logger)

                    r_MATS = Satellite_dict['Position [km]']
                    lat_MATS = Satellite_dict['Latitude [degrees]']

                    sun_angle = Library.SunAngle(r_MATS, current_time)

                    if(t*timestep % log_timestep == 0 == 0 or t == 1):
                        Logger.debug('')
                        Logger.debug('current_time: '+str(current_time))
                        Logger.debug('lat_MATS [degrees]: '+str(lat_MATS))
                        Logger.debug('sun_angle [degrees]: '+str(sun_angle))
                        Logger.debug('mode: '+str(mode))
                        Logger.debug('')

                    # if( (sun_angle < DayAngle and lat-latMargin <= lat_MATS <= lat+latMargin and mode == 'Day' ) or
                    #   (sun_angle > NightAngle and lat-latMargin <= lat_MATS <= lat+latMargin and mode == 'Night' )):
                    if((sun_angle < DayAngle and abs(lat_MATS) < withinLat and mode == 'Day') or
                            (sun_angle > NightAngle and abs(lat_MATS) < withinLat and mode == 'Night')):

                        Logger.debug('!!Break of Loop!!')
                        Logger.debug('Loop Counter (t): '+str(t))
                        Logger.debug('current_time: '+str(current_time))
                        Logger.debug('lat_MATS [degrees]: '+str(lat_MATS))
                        Logger.debug('sun_angle [degrees]: '+str(sun_angle))
                        Logger.debug('mode: '+str(mode))

                        Logger.debug('')
                        break

                    "Increase Loop counter"
                    t = t+1

                    "Timestep for propagation of MATS"
                    relativeTime = round(relativeTime + timestep, 1)

                ############################################################################
                ########################## End of Orbit simulator ##########################
                ############################################################################

                comment = (Mode_name+', '+str(date)+', '+', pointing_altitude = '+str(altitude) +
                           ', ExpTime = '+str(ExpTime)+', JPEGQ = '+str(JPEGQ))

                Logger.debug(comment)

                relativeTime = Macros.NadirSnapshot_Limb_Pointing_macro(
                    root=root, relativeTime=relativeTime, pointing_altitude=altitude, CCD_settings=CCD_settings,      Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

                #"Postpone next command until at least the end of ExpTime"
                #relativeTime = round(float(relativeTime) + ExpTime/1000,2)

    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of Nadir_functional_test')

    return relativeTime, current_time


#######################################################################################################

def CCD_stability_test(root, date, duration, relativeTime, Timeline_settings, configFile, Test_settings={'ExpTimes': [1000, 2000, 4000, 8000, 16000, 32000]}):
    """CCD_stability_test. 

    Schedules CCD_stability_test with defined parameters and simulates MATS propagation from TLE.
    """

    Logger.info('')
    Logger.info('Start of CCD_stability_test')

    Logger.debug('Test_settings from Science Mode List: '+str(Test_settings))
    # Test_settings = params_checker(Test_settings,Mode=X=_settings)

    CCD_settings = configFile.CCD_macro_settings('FullReadout')

    JPEGQs = [100]
    WDWs = [7]
    altitudes = [200000]
    ExpTimes = Test_settings['ExpTimes']
    SnapshotSpacing = 5

    initial_relativeTime = relativeTime

    Mode_name = sys._getframe(0).f_code.co_name

    "Loop thorugh pointing altitudes"
    for altitude in altitudes:

        "Start looping the CCD settings and call for macros"
        for JPEGQ, WDW in zip(JPEGQs, WDWs):

            "Set all CCDs"
            for key in CCD_settings.keys():
                CCD_settings[key]['JPEGQ'] = JPEGQ
                CCD_settings[key]['WDW'] = WDW

            for ExpTime in ExpTimes:

                "Change TEXPMS for all the CCDs"
                for key in CCD_settings.keys():
                    CCD_settings[key]['TEXPMS'] = ExpTime

                comment = (Mode_name+', '+str(date)+', pointing_altitude = '+str(altitude) +
                           ', ExpTime = '+str(ExpTime)+', JPEGQ = '+str(JPEGQ))

                Logger.debug(comment)

                relativeTime = Macros.Snapshot_Limb_Pointing_macro(root, round(relativeTime, 2), CCD_settings, pointing_altitude=altitude,
                                                                   SnapshotSpacing=SnapshotSpacing, Timeline_settings=Timeline_settings, configFile=configFile, comment=comment)

                #"Postpone next command until at least the end of ExpTime"
                #relativeTime = round(relativeTime + ExpTime/1000,2)

    mode_relativeTime = relativeTime - initial_relativeTime
    current_time = ephem.Date(date+ephem.second*mode_relativeTime)

    Logger.info('End of CCD_stability_test')

    return relativeTime, current_time


#############################################################################################

#############################################################################################
