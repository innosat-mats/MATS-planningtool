# -*- coding: utf-8 -*-
"""Contain Subfunctions used in *Timeline_gen* by Modes12X, where X is 0,1,2,3,4.

"""

import logging
import sys
import importlib
import ephem
from pylab import array, ceil, cos, sin, dot, zeros, norm, pi, arccos, floor
from astroquery.vizier import Vizier
from skyfield import api

from mats_planningtool.Library import Satellite_Simulator, deg2HMS, scheduler
from mats_planningtool import MATS_coordinates

Logger = logging.getLogger("OPT_logger")


def UserProvidedDateScheduler(Occupied_Timeline, Settings, configFile):
    """Schedules a single user provided date.

    Used by Mode120-124.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.
        Settings (dict): Dictionary containing settings for this simulation.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of the scheduling of the mode.


    """

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(1).f_code.co_name

    Timeline_settings = configFile.Timeline_settings()

    if(Settings['start_date'] == '0'):
        StartDate = ephem.Date(Timeline_settings['start_date'])
    else:
        try:
            StartDate = ephem.Date(Settings['start_date'])
        except:
            Logger.error('Could not get Settings["start_date"], exiting...')
            sys.exit()

    endDate = ephem.Date(StartDate+ephem.second * (
        Settings['freeze_start'] + Settings['freeze_duration'] + Timeline_settings['mode_separation']))

    ############### Start of availability schedueler ##########################

    StartDate, endDate, iterations = scheduler(Occupied_Timeline, StartDate, endDate)

    ############### End of availability schedueler ##########################

    comment = str(
        Mode_name)+' scheduled using a user given date, the date got postponed '+str(iterations)+' times'

    Occupied_Timeline[Mode_name].append((StartDate, endDate))

    return Occupied_Timeline, comment


def date_calculator(Settings, configFile):
    """Simulates MATS FOV and stars.

    Used by Mode121-123.
    Simuates MATS FOV and visible stars for one orbit then skips ahead for *Settings['Timeskip']* amount of days (as defined in the *Configuration File*). 
    Saves the date, pointing RA and Dec, and the magnitude of the brightest visible star at each timestep.

    Arguments:
        Settings (dict): Dictionary containing settings for this simulation.

    Returns:
        (array): Array containing date in first column and brightest magnitude visible in the second. Contains current Dec and RA in 3rd and 4th column respectively.

    """

    Timeline_settings = configFile.Timeline_settings()

    "To either calculate when stars are visible and schedule from that data or just schedule at a given time given by Mode120_settings['start_date']"
    if(Settings['automatic'] == False):

        if(Settings['start_date'] == '0'):
            date = ephem.Date(Timeline_settings['start_date'])
        else:
            try:
                date = ephem.Date(Settings['start_date'])
            except:
                Logger.error('Could not get Settings["start_date"], exiting...')
                sys.exit()

        return date

    elif(Settings['automatic'] == True):

        "Simulation length and timestep"
        log_timestep = Settings['log_timestep']
        Logger.debug('log_timestep: '+str(log_timestep))

        timestep = Settings['timestep']  # In seconds
        Logger.info('timestep set to: '+str(timestep)+' s')

        if(Settings['TimeToConsider']['TimeToConsider'] <= Timeline_settings['duration']['duration']):
            duration = Settings['TimeToConsider']['TimeToConsider']
        else:
            duration = Timeline_settings['duration']['duration']

        Logger.info('Duration set to: '+str(duration)+' s')

        timesteps = int(ceil(duration / timestep)) + 2
        Logger.info('Maximum number of timesteps set to: '+str(timesteps))

        timeline_start = ephem.Date(Timeline_settings['start_date'])

        initial_time = ephem.Date(
            timeline_start + ephem.second*Settings['freeze_start'])
        Logger.info('initial_time set to: '+str(initial_time))

        "Get relevant stars"
        result = Vizier(columns=['all'], row_limit=3000).query_constraints(
            catalog='I/239/hip_main', Vmag=Settings['Vmag'])
        star_cat = result[0]
        ROWS = star_cat[0][:].count()
        stars = []
        stars_dec = zeros((ROWS, 1))
        stars_ra = zeros((ROWS, 1))

        "Insert stars into Pyephem"
        for t in range(ROWS):
            s = "{},f|M|F7,{},{},{},2000/01/01 11:58:55.816"
            s = s.format(star_cat[t]['HIP'], deg2HMS(ra=star_cat[t]['_RA.icrs']), deg2HMS(
                dec=star_cat[t]['_DE.icrs']), star_cat[t]['Vmag'])
            stars.append(ephem.readdb(s))
            stars[t].compute(epoch='2000/01/01 11:58:55.816')
            stars_dec[t] = stars[t].dec
            stars_ra[t] = stars[t].ra

        Logger.debug('')
        Logger.debug('List of stars used: '+str(star_cat))
        Logger.debug('')

        "Calculate unit-vectors of stars"
        stars_x = cos(stars_dec) * cos(stars_ra)
        stars_y = cos(stars_dec) * sin(stars_ra)
        stars_z = sin(stars_dec)
        stars_r = array([stars_x, stars_y, stars_z])
        stars_r = stars_r.transpose()

        "Prepare the output"
        "Array containing date in first column and brightest magnitude visible in the second. Contains current Dec and RA in 3rd and 4th column"
        date_magnitude_array = zeros((timesteps, 4))
        "Set magntidues arbitrary large, which will correspond to no star being visible"
        date_magnitude_array[:, 1] = 100

        "Pre-allocate space"
        lat_MATS = zeros((timesteps, 1))
        long_MATS = zeros((timesteps, 1))
        optical_axis = zeros((timesteps, 3))
        stars_r_V_offset_plane = zeros((ROWS, 3))
        stars_r_H_offset_plane = zeros((ROWS, 3))
        stars_vert_offset = zeros((timesteps, ROWS))
        stars_hori_offset = zeros((timesteps, ROWS))
        r_V_offset_normal = zeros((timesteps, 3))
        r_H_offset_normal = zeros((timesteps, 3))
        star_counter = 0
        skip_star_list = []
        MATS_P = zeros((timesteps, 1))
        Dec_optical_axis = zeros((timesteps, 1))
        RA_optical_axis = zeros((timesteps, 1))

        angle_between_orbital_plane_and_star = zeros((timesteps, ROWS))

        "Constants"
        pointing_altitude = Settings['pointing_altitude']/1000
        V_FOV = Settings['V_FOV']
        H_FOV = Settings['H_FOV']  # 5.67 is actual H_FOV

        yaw_correction = Timeline_settings['yaw_correction']

        Logger.debug('H_FOV set to [degrees]: '+str(H_FOV))
        Logger.debug('V_FOV set to [degrees]: '+str(V_FOV))
        Logger.debug('yaw_correction set to: '+str(yaw_correction))

        TLE = configFile.getTLE()
        Logger.debug('TLE used: '+TLE[0]+TLE[1])

        MATS_skyfield = api.EarthSatellite(TLE[0], TLE[1])

        "Loop counter"
        t = 0

        TimeSkips = 0
        #time_skip_counter = 0
        # Days to skip ahead after each completed orbit
        Timeskip = Settings['TimeSkip']['TimeSkip']
        current_time = initial_time

        Logger.info('')
        Logger.info('Start of simulation of MATS for Mode121/122/123')

        ################## Start of Simulation ########################################
        "Loop and calculate the relevant angle of each star to each direction of MATS's FOV"
        while(current_time < timeline_start+ephem.second*duration):

            if(t*timestep % log_timestep == 0):
                LogFlag = True
            else:
                LogFlag = False

            Satellite_dict = Satellite_Simulator(
                MATS_skyfield, current_time, Timeline_settings, pointing_altitude, LogFlag, Logger)

            MATS_P[t] = Satellite_dict['OrbitalPeriod [s]']
            lat_MATS[t] = Satellite_dict['Latitude [degrees]']
            long_MATS[t] = Satellite_dict['Longitude [degrees]']
            optical_axis[t] = Satellite_dict['OpticalAxis']
            Dec_optical_axis[t] = Satellite_dict['Dec_OpticalAxis [degrees]']
            RA_optical_axis[t] = Satellite_dict['RA_OpticalAxis [degrees]']
            r_H_offset_normal[t] = Satellite_dict['Normal2H_offset']
            r_V_offset_normal[t] = Satellite_dict['Normal2V_offset']

            ############# End of Calculations of orbital and pointing vectors #####

            "Add current date to date_magnitude_array"
            date_magnitude_array[t, 0] = current_time
            "Add optical axis Dec and RA to date_magnitude_array"
            date_magnitude_array[t, 2] = Dec_optical_axis[t]
            date_magnitude_array[t, 3] = RA_optical_axis[t]

            ###################### Star-mapper ####################################

            "Check position of stars relevant to pointing direction"
            for x in range(ROWS):

                "Skip star if it is not visible during this epoch"
                if(stars[x].name in skip_star_list):
                    continue

                "Project 'star vectors' ontop pointing H-offset and V-offset plane"
                stars_r_V_offset_plane[x] = stars_r[0][x] - \
                    (dot(stars_r[0][x], r_V_offset_normal[t]) * r_V_offset_normal[t])

                stars_r_H_offset_plane[x] = stars_r[0][x] - \
                    (dot(stars_r[0][x], r_H_offset_normal[t]) * r_H_offset_normal[t])

                "Dot product to get the Vertical and Horizontal angle offset of the star in the FOV"
                stars_vert_offset[t][x] = arccos(dot(optical_axis[t], stars_r_V_offset_plane[x]) / (
                    norm(optical_axis[t]) * norm(stars_r_V_offset_plane[x]))) / pi*180
                stars_hori_offset[t][x] = arccos(dot(optical_axis[t], stars_r_H_offset_plane[x]) / (
                    norm(optical_axis[t]) * norm(stars_r_H_offset_plane[x]))) / pi*180

                "For first loop of stars, make exception list for stars not visible during this epoch"
                if(t == 1):

                    "To be able to skip stars far outside the orbital plane of MATS"
                    angle_between_orbital_plane_and_star[t][x] = arccos(
                        dot(stars_r[0][x], stars_r_V_offset_plane[x]) / norm(stars_r_V_offset_plane[x])) / pi*180

                    if(abs(angle_between_orbital_plane_and_star[t][x]) > H_FOV/2+(duration*2)/(365*24*3600)*360):
                        Logger.debug('Skip star: '+stars[x].name+', with angle_between_orbital_plane_and_star of: '+str(
                            angle_between_orbital_plane_and_star[t][x])+' degrees')
                        skip_star_list.append(stars[x].name)
                        continue

                "Check if star is in FOV"
                if(abs(stars_vert_offset[t][x]) < V_FOV/2 and abs(stars_hori_offset[t][x]) < H_FOV/2):
                    # print('Star number:',stars[x].name,'is visible at',stars_vert_offset[t][x],'degrees VFOV and', \
                    # stars_hori_offset[t][x],'degrees HFOV','during',ephem.Date(current_time))

                    if(t % log_timestep == 0 or t == 1):
                        Logger.debug('Current time: '+str(current_time))
                        Logger.debug('Star: '+stars[x].name+', with H-offset: '+str(
                            stars_hori_offset[t][x])+' V-offset: '+str(stars_vert_offset[t][x])+' in degrees is visible')

                    "Check if it is the brightest star spotted in the current FOV at the current date, and if so, replace the current value"
                    if(stars[x].mag < date_magnitude_array[t, 1]):
                        date_magnitude_array[t, 1] = stars[x].mag

                    star_counter = star_counter + 1

            ######################### End of star_mapper #############################

            "Increase Simulation Time with a timestep, or skip ahead if 1 orbit is completed"
            t += 1
            if(t*timestep >= MATS_P[t-1]*(TimeSkips+1)):
                current_time = ephem.Date(current_time+ephem.second*Timeskip)
                TimeSkips += 1
            else:
                current_time = ephem.Date(current_time+ephem.second*timestep)

            '''
            "Increment time with timestep or jump ahead in time if a whole orbit was completed"
            if( (current_time - initial_time)/ephem.second > (timeskip/ephem.second * time_skip_counter + MATS_P[t] * (time_skip_counter+1)) ):
                "If one orbit has passed -> increment 'current_time' with 'timeskip' amount of days"
                time_skip_counter = time_skip_counter + 1
                current_time = ephem.Date(current_time + timeskip)
            else:
                "Else just increment the current_time with timestep"
                current_time = ephem.Date(current_time + ephem.second * timestep)
            
            "Loop counter"
            t = t + 1
            '''
        ################## End of Simulation ########################################

        return(date_magnitude_array)


##################################################################################################
##################################################################################################


def date_select(Occupied_Timeline, date_magnitude_array, Settings, configFile):
    """Schedules a simulated date.

    Used by Mode121-123. A date is selected for when the brightest star visible; has the faintest magntitude compared
    to other brightest stars visible at other timesteps.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.
        date_magnitude_array (array): An Array containing date in first column and brightest magnitude visible in the second. Contains Dec and RA in 3rd and 4th column respectively. 

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of the scheduling of the mode.

    """

    Logger.info('Start of filtering function')
    Logger.debug('date_magnitude_array: '+str(date_magnitude_array))

    Timeline_settings = configFile.Timeline_settings()

    "Get the name of the parent function, which is always defined as the name of the mode"
    Mode_name = sys._getframe(1).f_code.co_name

    arbitraryLowNumber = -100

    restart = True

    loop_counter = 0

    "Loop for maximum magnitude visible until the date chosen is not occupied"
    while(restart == True):

        restart = False

        index_max_mag = date_magnitude_array[:, 1].argmax()
        value_max_mag = date_magnitude_array[:, 1].max()
        date_max_mag = date_magnitude_array[index_max_mag, 0]
        dec_max_mag = date_magnitude_array[index_max_mag, 2]
        RA_max_mag = date_magnitude_array[index_max_mag, 3]

        "If the all the magnitudes have been set arbitrary low (all dates occupied) or there are no simulated dates left (date=0) -> No Date available -> Exit"
        if(value_max_mag == arbitraryLowNumber or date_max_mag == 0):
            comment = 'No available time for '+Mode_name
            Logger.warning(comment)
            #input('Enter anything to ackknowledge and continue')
            return Occupied_Timeline, comment

        date = ephem.Date(ephem.Date(date_max_mag) -
                          ephem.second*(Settings['freeze_start']))
        endDate = ephem.Date(date+ephem.second * (
            Settings['freeze_start'] + Settings['freeze_duration'] + Timeline_settings['mode_separation']))

        "Extract the start and end date of each scheduled mode"
        for busy_dates in Occupied_Timeline.values():
            if restart:
                break
            if(busy_dates == []):
                continue
            else:
                "Extract the start and end date of each instance of a scheduled mode"
                for busy_date in busy_dates:

                    "If the planned date collides with any already scheduled ones -> post-pone and restart loop"
                    if(busy_date[0] <= date < busy_date[1] or
                            busy_date[0] < endDate <= busy_date[1] or
                            (date < busy_date[0] and endDate > busy_date[1])):

                        restart = True
                        "Set the current maximum magnitude arbitrary small to allow a new maximum magnitude date to be chosen in next loop"
                        date_magnitude_array[index_max_mag, 1] = arbitraryLowNumber
                        loop_counter = loop_counter + 1
                        break

    comment = 'Number of times date changed: ' + str(loop_counter)+', faintest magnitude visible (100 equals no stars visible): '+str(
        value_max_mag)+', Dec (J2000): '+str(dec_max_mag)+', RA (J2000): '+str(RA_max_mag)

    Occupied_Timeline[Mode_name].append((date, endDate))

    return Occupied_Timeline, comment
