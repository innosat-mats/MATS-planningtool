# -*- coding: utf-8 -*-
"""Schedules the active Mode and saves the result in the Occupied_Timeline dictionary.

Part of Timeline_generator, as part of OPT.

"""


import sys
import logging
import importlib
from pylab import cross, ceil, dot, zeros, sqrt, norm, pi, arccos, arctan
from skyfield import api
import datetime as DT
import numpy as np

from mats_planningtool.Library import scheduler
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator,xyz2radec

from .Mode12X import UserProvidedDateScheduler

Logger = logging.getLogger("OPT_logger")


def Mode124(Occupied_Timeline, configFile):
    """Core function for the scheduling of Mode124.

    Determines if the scheduled date should be determined by simulating MATS or be user provided.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Settings = configFile.Mode124_settings()

    if(Settings['automatic'] == False):
        Occupied_Timeline, comment = UserProvidedDateScheduler(
            Occupied_Timeline, Settings, configFile)
    elif(Settings['automatic'] == True):
        SpottedMoonList = date_calculator(configFile)

        Occupied_Timeline, comment = date_select(
            Occupied_Timeline, SpottedMoonList, configFile)

    return Occupied_Timeline, comment


###############################################################################################
###############################################################################################


def date_calculator(configFile):
    """Subfunction, Simulates MATS FOV and the Moon.

    Determines when the Moon is in the FOV at an vertical offset-angle equal to *#V-offset* and
    when pointing at an LP altitude equal to *#pointing_altitude*. \n

    (# as defined in the *Configuration File*). \n

    Saves the date and parameters regarding the spotting of the Moon to the variable SpottedMoonList.

    Arguments:
        configFile (obj): input config file

    Returns:
        SpottedMoonList ((:obj:`list` of :obj:`dict`)) or (str): A list containing dictionaries containing parameters for each time the Moon is spotted. Or just a date depending on 'automatic' in *Mode124_settings*.

    """

    Timeline_settings = configFile.Timeline_settings()
    Mode124_settings = configFile.Mode124_settings()

    log_timestep = Mode124_settings['log_timestep']
    Logger.debug('log_timestep: '+str(log_timestep))

    ##################################################

    "Check how many times Mode124 have been scheduled"
    Mode124Iteration = configFile.Mode124Iteration
    "Make the Offset_Index go from 0 to len(Mode124_settings['V_offset']"
    Offset_Index = (Mode124Iteration-1) % (len(Mode124_settings['V_offset']))

    "Constants"
    V_offset = Mode124_settings['V_offset'][Offset_Index]
    H_offset = Mode124_settings['H_offset'][Offset_Index]
    pointing_altitude = Mode124_settings['pointing_altitude']/1000

    Moon_orbital_period = 3600*24*27.32
    yaw_correction = Timeline_settings['yaw_correction']

    Logger.debug('H_offset set to [degrees]: '+str(H_offset))
    Logger.debug('V_offset set to [degrees]: '+str(V_offset))
    Logger.debug('Moon_orbital_period [s]: '+str(Moon_orbital_period))
    Logger.debug('yaw_correction set to: '+str(yaw_correction))

    TLE = configFile.getTLE()
    Logger.debug('TLE used: '+TLE[0]+TLE[1])

    ##########################################################

    "Simulation length and timestep"

    timestep = Mode124_settings['timestep']  # In seconds
    Logger.info('Timestep set to [s]: '+str(timestep))

    if(Mode124_settings['TimeToConsider']['TimeToConsider'] <= Timeline_settings['duration']['duration']):
        duration = Mode124_settings['TimeToConsider']['TimeToConsider']
    else:
        duration = Timeline_settings['duration']['duration']
    Logger.info('Duration set to [s]: '+str(duration))

    timesteps = int(ceil(duration / timestep))

    timeline_start = DT.datetime.strptime(Timeline_settings['start_date'],'%Y/%m/%d %H:%M:%S')
    initial_time = timeline_start + DT.timedelta(seconds = Mode124_settings['freeze_start'])

    Logger.info('Initial simulation date set to: '+str(initial_time))

    Moon_vert_offset = zeros((timesteps, 1))
    Moon_hori_offset = zeros((timesteps, 1))
    Moon_tot_offset = zeros((timesteps, 1))
    SpottedMoonList = []

    Dec_optical_axis = zeros((timesteps, 1))
    RA_optical_axis = zeros((timesteps, 1))
    optical_axis = zeros((timesteps, 3))

    datetimes = []
    timestamps = zeros((timesteps, 1))

    ###LOAD SKYFIELD###
    ts = api.load.timescale(builtin=True)
    MATS_skyfield = api.EarthSatellite(TLE[0], TLE[1])

    planets = api.load('de421.bsp')
    Moon = planets['Moon']
    Earth = planets['Earth']


    current_time = initial_time

    Logger.info('')
    Logger.info('Start of simulation for Mode124')

    ######### SIMULATION ################
    t = 0
    while(current_time < initial_time+DT.timedelta(seconds = duration)):

        if(t*timestep % log_timestep == 0):
            LogFlag = True
        else:
            LogFlag = False

        Satellite_dict = Satellite_Simulator(
            MATS_skyfield, current_time, Timeline_settings, pointing_altitude, LogFlag, Logger)

        optical_axis[t] = Satellite_dict['OpticalAxis']
        yaw_offset_angle = Satellite_dict['Yaw [degrees]'] #Only needed to look outside of orbit plane

        ############# End of Calculations of orbital and pointing vectors #####

        current_time_datetime = current_time
        year = current_time_datetime.year
        month = current_time_datetime.month
        day = current_time_datetime.day
        hour = current_time_datetime.hour
        minute = current_time_datetime.minute
        second = current_time_datetime.second + current_time_datetime.microsecond/1000000

        current_time_skyfield = ts.utc(year, month, day, hour, minute, second)

        #### Caluclate moon position on CCD #########

        moonpos=Earth.at(current_time_skyfield).observe(Moon)
        moonpos_km = moonpos.position.km
        moonpos_ra_dec = moonpos.radec()
        inst_xyz=np.matmul(Satellite_dict['InvRotMatrix'],moonpos_km)
        [xang,yang]=xyz2radec(inst_xyz,positivera=False,deg=True) #degrees
        Moon_hori_offset[t] = xang #degrees
        Moon_vert_offset[t] = yang #degrees
        Moon_tot_offset[t]=np.rad2deg(np.arccos(np.dot(optical_axis[t],moonpos_km/norm(moonpos_km))))
        
        datetimes.append(current_time_datetime)
        timestamps[t]= current_time_datetime.timestamp()

        current_time = current_time+DT.timedelta(seconds=timestep)
        t = t + 1

    #Filtering on moon inside horizontal FOV and not too far outside vertical FOV (interpolation is done later)   
    horisontal_filter=3 #look for stars horizontally +- total degrees (Horistontal FOV is 6.06)
    vert_filter= 5 #look at stars vertically at +- this filter in degrees (Vertical FOV is 1.52)

    possibles=np.array([(itime) for itime in range(len(Moon_hori_offset))  
                    if (((abs(Moon_hori_offset[itime]))< horisontal_filter) and (abs(Moon_vert_offset[itime])< vert_filter))])

    if(len(possibles) == 0):
        Logger.warning('Moon not found in time to consider')
        return SpottedMoonList


    moon_found = np.where(np.diff(possibles)>2)[0] #check if there is a gap in the indeces larger than 2
    moon_found = np.insert(moon_found,0,0)
    moon_found = np.append(moon_found,len(possibles))

    xvalue = np.zeros((len(moon_found),1)) #array to hold horizontal offset in degreess

    crosstime = []
    for i in range(len(moon_found)-1):
        timerange=possibles[moon_found[i]:moon_found[i+1]]
        crosstime.append(DT.datetime.fromtimestamp(np.interp(V_offset,Moon_vert_offset[timerange,0][::-1],timestamps[timerange,0][::-1])))
        xvalue[i]=np.interp(crosstime[i].timestamp(),timestamps[timerange,0],Moon_hori_offset[timerange,0])

    for i in range(len(crosstime)):
        Satellite_dict_at_freezepoint = Satellite_Simulator(
            MATS_skyfield, crosstime[i], Timeline_settings, pointing_altitude, LogFlag, Logger)

        lat_MATS = Satellite_dict_at_freezepoint['Latitude [degrees]']
        long_MATS = Satellite_dict_at_freezepoint['Longitude [degrees]']

        optical_axis = Satellite_dict_at_freezepoint['OpticalAxis']
        Dec_optical_axis = Satellite_dict_at_freezepoint['Dec_OpticalAxis [degrees]']
        RA_optical_axis = Satellite_dict_at_freezepoint['RA_OpticalAxis [degrees]']

        SpottedMoonList.append({'Date': crosstime[i].strftime("%Y-%m-%d %H:%M:%S.%f"), 'V-offset': V_offset, 'H-offset': xvalue[i].item(),
                                        'long_MATS': float(long_MATS), 'lat_MATS': float(lat_MATS), 'Dec': moonpos_ra_dec[1].degrees, 'RA': moonpos_ra_dec[0]._degrees,
                                        'Dec FOV': Dec_optical_axis, 'RA FOV': RA_optical_axis, 'FOV': optical_axis})        

    return SpottedMoonList


###############################################################################################
###############################################################################################


def date_select(Occupied_Timeline, SpottedMoonList, configFile):
    """Subfunction, Schedules a simulated date.

    A date is selected for which the Moon is visible as close as possible to the given H-offset (from config file), yet not
    overlapping with previously scheduled mode. 

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes together with their start and end time in a list. The list is empty if the Mode is unscheduled.
        SpottedMoonList ((:obj:`list` of :obj:`dict`)): A list containing dictionaries containing parameters for each time the Moon is spotted.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """
    Logger.info('Start of filtering function')

    Mode124_settings = configFile.Mode124_settings()
    
    "Check how many times Mode124 have been scheduled"
    Mode124Iteration = configFile.Mode124Iteration

    "Get offset where the moon should be"
    Offset_Index = (Mode124Iteration-1) % (len(Mode124_settings['V_offset']))
    H_offset = Mode124_settings['H_offset'][Offset_Index]

    if(len(SpottedMoonList) == 0):

        comment = 'Moon not visible (SpottedMoonList is empty)'
        Logger.warning('')
        Logger.warning(comment)
        #input('Enter anything to acknowledge and continue\n')
        return Occupied_Timeline, comment

    Moon_H_offset = [SpottedMoonList[x]['H-offset']
                     for x in range(len(SpottedMoonList))]
    Moon_V_offset = [SpottedMoonList[x]['V-offset']
                     for x in range(len(SpottedMoonList))]
    Moon_date = [SpottedMoonList[x]['Date'] for x in range(len(SpottedMoonList))]
    MATS_long = [SpottedMoonList[x]['long_MATS'] for x in range(len(SpottedMoonList))]
    MATS_lat = [SpottedMoonList[x]['lat_MATS'] for x in range(len(SpottedMoonList))]

    Moon_H_offset_abs = [abs(x-H_offset) for x in Moon_H_offset] #difference between wanted offset and true offset
    Moon_H_offset_sorted = [abs(x-H_offset) for x in Moon_H_offset] #sorted array
    Moon_H_offset_sorted.sort()

    restart = True
    iterations = 0
    "Selects date based on min H-offset, if occupied, select date for next min H-offset"
    while(restart == True):

        if(len(Moon_H_offset) == iterations):
            comment = 'No time available for Mode124'
            Logger.error('')
            Logger.error(comment)
            #input('Enter anything to ackknowledge and continue')
            return Occupied_Timeline, comment

        restart = False

        """Extract index of  minimum H-offset for first iteration, 
        then next smallest if 2nd iterations needed and so on"""
        x = Moon_H_offset_abs.index(Moon_H_offset_sorted[iterations])

        date = DT.datetime.strptime(Moon_date[x],'%Y-%m-%d %H:%M:%S.%f')
        #Add time before freeze to allow for setting CCDs and moving instrument
        date = date-DT.timedelta(seconds=Mode124_settings['freeze_start'])

        endDate = date+DT.timedelta(seconds=Mode124_settings['freeze_start'] +
                                                Mode124_settings['freeze_duration'] +
                                                configFile.Timeline_settings()["pointing_stabilization"] + 
                                                configFile.Timeline_settings()['mode_separation'])

        "Check that the scheduled date is not before the start of the timeline"
        if(date < DT.datetime.strptime(configFile.Timeline_settings()['start_date'],'%Y/%m/%d %H:%M:%S')):
            iterations = iterations + 1
            restart = True
            continue

        "Extract Occupied dates and if they clash, restart loop and select new date"
        for busy_dates in Occupied_Timeline.values():
            if restart:
                break
            if(busy_dates == []):
                continue
            else:
                "Extract the start and end date of each instance of a scheduled mode"
                for busy_date in busy_dates:

                    if(busy_date[0] <= date <= busy_date[1] or
                            busy_date[0] <= endDate <= busy_date[1] or
                            (date < busy_date[0] and endDate > busy_date[1])):

                        iterations = iterations + 1
                        restart = True
                        break

    comment = ('V-offset: '+str(round(Moon_V_offset[x], 2))+', H-offset: '+str(round(Moon_H_offset[x], 2))+', Times date changed: '+str(iterations) +
               ', MATS (long,lat) in degrees = ('+str(round(MATS_long[x], 2))+', '+str(round(MATS_lat[x], 2))+'), Moon Dec (J2000) [degrees]: ' +
               str(round(SpottedMoonList[x]['Dec'], 2))+', Moon RA (J2000) [degrees]: '+str(round(SpottedMoonList[x]['RA'], 2))+', OpticalAxis Dec = '+str(round(SpottedMoonList[x]['Dec FOV'], 2)) +
               ', Optical Axis RA = '+str(round(SpottedMoonList[x]['RA FOV'], 2)))

    Occupied_Timeline['Mode124'].append((date, endDate))

    return Occupied_Timeline, comment
