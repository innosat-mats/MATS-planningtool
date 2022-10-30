# -*- coding: utf-8 -*-
"""Schedules the active Mode and saves the result in the Occupied_Timeline dictionary.

Part of Timeline_generator, as part of OPT.

"""

import logging
import sys
import csv
import os
from pylab import array, ceil, cos, sin, cross, dot, zeros, norm, pi, arccos, floor
from skyfield import api
from skyfield.data import hipparcos
from skyfield.api import wgs84, Star
import numpy as np
import datetime as DT

from mats_planningtool.Library import deg2HMS
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator, xyz2radec
from .Mode12X import UserProvidedDateScheduler

Logger = logging.getLogger("OPT_logger")


def Mode120(Occupied_Timeline, configFile):
    """Core function for the scheduling of Mode120.

    Determines if the scheduled date should be determined by simulating MATS or be user provided.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Settings = configFile.Mode120_settings()

    # for Offset_Index in range(len(Settings['V_offset'])):

    if(Settings['automatic'] == False):
        Occupied_Timeline, comment = UserProvidedDateScheduler(
            Occupied_Timeline, Settings, configFile)
    elif(Settings['automatic'] == True):
        SpottedStarList = Mode120_date_calculator(configFile)

        Occupied_Timeline, comment = Mode120_date_select(
            Occupied_Timeline, SpottedStarList, configFile)

    return Occupied_Timeline, comment


#########################################################################################
#####################################################################################################


def Mode120_date_calculator(configFile):
    """Subfunction, Simulates MATS FOV and the stars.

    Determines when stars are in the FOV at an vertical offset-angle equal to *#V-offset* and
    when pointing at an LP altitude equal to *#pointing_altitude*. \n

    (# as defined in the *Configuration File*). \n

    Saves the date and parameters regarding the spotting of a star.
    Also saves relevant data to an .csv file located in Output/.

    Arguments:
        configFile (obj): input config file

    Returns:
        SpottedStarList ((:obj:`list` of :obj:`dict`)) or (str): A list containing dictionaries containing parameters for each time a star is spotted.
        
    """

    Timeline_settings = configFile.Timeline_settings()
    Mode120_settings = configFile.Mode120_settings()

    ######################################################
    "Check how many times Mode120 have been scheduled"
    Mode120Iteration = configFile.Mode120Iteration
    "Make the Offset_Index go from 0 to len(Mode120_settings['V_offset'] for each time Mode120 is scheduled"
    Offset_Index = (Mode120Iteration-1) % (len(Mode120_settings['V_offset']))

    "Constants"
    V_offset = Mode120_settings['V_offset'][Offset_Index]
    H_offset = Mode120_settings['H_offset'][Offset_Index]
    priority = Mode120_settings['Priority']

    pointing_altitude = Mode120_settings['pointing_altitude']/1000
    yaw_correction = Timeline_settings['yaw_correction']

    Logger.debug('H_offset set to [degrees]: '+str(H_offset))
    Logger.debug('V_offset set to [degrees]: '+str(V_offset))
    Logger.debug('yaw_correction set to: '+str(yaw_correction))

    TLE = configFile.getTLE()
    Logger.debug('TLE used: '+TLE[0]+TLE[1])

    ####################################################

    "Simulation length and timestep"
    log_timestep = Mode120_settings['log_timestep']
    Logger.debug('log_timestep: '+str(log_timestep))

    timestep = Mode120_settings['timestep']  # In seconds
    Logger.info('timestep set to: '+str(timestep)+' s')

    if(Mode120_settings['TimeToConsider']['TimeToConsider'] <= Timeline_settings['duration']['duration']):
        duration = Mode120_settings['TimeToConsider']['TimeToConsider']
    else:
        duration = Timeline_settings['duration']['duration']
    Logger.info('Duration set to: '+str(duration)+' s')

    timesteps = int(ceil(duration / timestep))
    Logger.info('Maximum number of timesteps set to: '+str(timesteps))

    timeline_start = DT.datetime.strptime(Timeline_settings["start_date"],'%Y/%m/%d %H:%M:%S')
    initial_time = timeline_start + DT.timedelta(seconds=Mode120_settings['freeze_start'])
    current_time = initial_time
    Logger.info('Initial simulation date set to: '+str(initial_time))

    ##############################################
    ts = api.load.timescale(builtin=True)
    MATS_skyfield = api.EarthSatellite(TLE[0], TLE[1])

    planets = api.load('de421.bsp')
    earth=planets['Earth']

    "Get relevant stars"
    st_vec=[]

    with api.load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)
    df=df[df['magnitude']<=Mode120_settings['Vmag']]
    bright_stars = Star.from_dataframe(df)
    nstars=len(bright_stars.ra.hours)
    ts_initial=ts.utc(initial_time.year,initial_time.month,initial_time.day,initial_time.hour,initial_time.minute,initial_time.second)
    
    for st in range(nstars): 
        st_vec.append(earth.at(ts_initial).observe(bright_stars)[st].position.km)
        
    ##### Prepare the .csv file output #####
    star_list_excel = []
    star_list_excel.append(['Name'])
    star_list_excel.append(['t1'])
    star_list_excel.append(['long'])
    star_list_excel.append(['lat'])
    star_list_excel.append(['mag'])
    star_list_excel.append(['H_offset'])
    star_list_excel.append(['V_offset'])
    star_list_excel.append(['Optical Axis Dec (ICRS J2000)'])
    star_list_excel.append(['Optical Axis RA (ICRS J2000)'])
    star_list_excel.append(['Star Dec (ICRS J2000)'])
    star_list_excel.append(['Star RA (ICRS J2000)'])
    
    ############# Pre-allocate space ##########
    lat_MATS = zeros((timesteps, 1))
    long_MATS = zeros((timesteps, 1))
    optical_axis = zeros((timesteps, 3))
    stars_vert_offset = zeros((nstars,timesteps))
    stars_hori_offset = zeros((nstars,timesteps))
    stars_tot_offset = zeros((nstars,timesteps))
    star_counter = 0
    spotted_star_name = []
    spotted_star_timestamp = []
    spotted_star_timecounter = []
    skip_star_list = []

    Dec_optical_axis = zeros((timesteps, 1))
    RA_optical_axis = zeros((timesteps, 1))

    datetimes = []
    timestamps = zeros((timesteps, 1))

    "Prepare the output"
    SpottedStarList = []


    ######### SIMULATION ################

    Logger.info('')
    Logger.info('Start of simulation of MATS for Mode120')

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

        #### Caluclate star positions on CCD #########

        for nstar in range(nstars): 
            inst_xyz=np.matmul(Satellite_dict['InvRotMatrix'],st_vec[nstar])
            [xang,yang]=xyz2radec(inst_xyz,positivera=False,deg=True)
            stars_hori_offset[nstar,t] = xang
            stars_vert_offset[nstar,t] = yang
            stars_tot_offset[nstar,t]=np.rad2deg(np.arccos(np.dot(optical_axis[t],st_vec[nstar]/norm(st_vec[nstar]))))
        
        datetimes.append(current_time_datetime)
        timestamps[t]= current_time_datetime.timestamp()

        current_time = current_time+DT.timedelta(seconds=timestep)
        t = t + 1

    #Filtering on moon inside horizontal FOV and not too far outside vertical FOV (interpolation is done later)   
    horisontal_filter=3 #look for stars horizontally +- total degrees (Horistontal FOV is 6.06)
    vert_filter= 5 #look at stars vertically at +- this filter in degrees (Vertical FOV is 1.52)

    possibles=np.array([(istar,itime) for istar in range(nstars) for itime in range(len(timestamps))  
                    if ((abs(stars_hori_offset[istar,itime])< horisontal_filter) and (abs(stars_vert_offset[istar,itime])<vert_filter))])

    if(len(possibles) == 0):
        Logger.warning('Star not found in time to consider')
        return SpottedStarList

    for posstar in np.unique(possibles[:,0]):
        possible=np.array([possible for possible in possibles if possible[0]==posstar ])
        star_found = np.where(np.diff(possible[:,1])>2)[0] #check if there is a gap in the indeces larger than 2
        star_found = np.insert(star_found,0,0)
        star_found = np.append(star_found,len(possible))
        xvalue = np.zeros((len(star_found)-1,1)) #array to hold horizontal offset in degreess
        
        crosstime = []
        for i in range(len(star_found)-1):
            timerange=possibles[star_found[i]:star_found[i+1]]
            crosstime.append(DT.datetime.fromtimestamp(np.interp(V_offset,stars_vert_offset[posstar,timerange[:,1]][::-1],timestamps[timerange[:,1],0][::-1])))
            xvalue[i]=np.interp(crosstime[i].timestamp(),timestamps[timerange[:,1],0],stars_hori_offset[posstar,timerange[:,1]])

        star = df.loc[df.index[posstar]]
        # print("{:6d} {:7.2f} {:10.3f} {:10.3f}  {:10.5f}  {}".format (posstar, mag,
        #                                                 Mats(crosstime).FOV_ra,Mats(crosstime).FOV_dec,xvalue, crosstime))  
        for i in range(len(crosstime)):

            Satellite_dict_at_freezepoint = Satellite_Simulator(
            MATS_skyfield, crosstime[i], Timeline_settings, pointing_altitude, LogFlag, Logger)

            lat_MATS = Satellite_dict_at_freezepoint['Latitude [degrees]']
            long_MATS = Satellite_dict_at_freezepoint['Longitude [degrees]']

            optical_axis = Satellite_dict_at_freezepoint['OpticalAxis']
            Dec_optical_axis = Satellite_dict_at_freezepoint['Dec_OpticalAxis [degrees]']
            RA_optical_axis = Satellite_dict_at_freezepoint['RA_OpticalAxis [degrees]']

            "Add the spotted star to the exception list and timestamp it"
            spotted_star_name.append(star.name)
            spotted_star_timestamp.append(crosstime)

            "Append all relevent data for the star"
            star_list_excel[0].append(star.name)
            star_list_excel[1].append(crosstime[i].strftime("%Y-%m-%d %H:%M:%S"))
            star_list_excel[2].append(str(float(long_MATS)))
            star_list_excel[3].append(str(float(lat_MATS)))
            star_list_excel[4].append(str(star.magnitude))
            star_list_excel[5].append(str(xvalue[i][0]))
            star_list_excel[6].append(str(V_offset))
            star_list_excel[7].append(str(Dec_optical_axis))
            star_list_excel[8].append(str(RA_optical_axis))
            star_list_excel[9].append(str(star.dec_degrees))
            star_list_excel[10].append(str(star.ra_degrees))

            "Log data of star relevant to filtering process"

            SpottedStarList.append({'Date': crosstime[i].strftime("%Y-%m-%d %H:%M:%S.%f"), 'V-offset': V_offset, 'H-offset': xvalue[i],
                                    'long_MATS': float(long_MATS), 'lat_MATS': float(lat_MATS),
                                    'Dec_optical_axis': Dec_optical_axis, 'RA_optical_axis': RA_optical_axis,
                                    'Vmag': star.magnitude, 'Name': str(star.name), 'Dec': star.dec_degrees, 'RA': star.ra_degrees})

    ########################## END OF SIMULATION ############################

    Logger.info('')
    Logger.info('End of simulation for Mode120')
    Logger.info('')

    "Write spotted stars to file"
    try:
        os.mkdir('Output')
    except:
        pass

    while(True):
        try:
            file_directory = os.path.join('Output', sys._getframe(
                1).f_code.co_name+'_Visible_Stars__'+os.path.split(configFile.config_file_name)[1]+'__V_offset'+str(V_offset)+'.csv')
            with open(file_directory, 'w', newline='') as write_file:
                writer = csv.writer(write_file, dialect='excel-tab')
                writer.writerows(star_list_excel)
            Logger.info('Available Stars data saved to: '+file_directory)
            #print('Available Stars data saved to: '+file_directory)
            break
        except PermissionError:
            Logger.error(file_directory+' cannot be overwritten. Please close it')
            data = input('Enter anything to try again or 1 to exit')
            if(data == '1'):
                sys.exit()

    Logger.debug('Visible star list to be filtered:')
    for x in range(len(SpottedStarList)):
        Logger.debug(str(SpottedStarList[x]))
    Logger.debug('')

    Logger.debug('Exit '+str(__name__))
    Logger.debug('')

    return(SpottedStarList)


#####################################################################################################
#####################################################################################################


def Mode120_date_select(Occupied_Timeline, SpottedStarList, configFile):
    """Subfunction, Schedules a simulated date.

    A date is selected for which the brightest star is visible at the minimum distance to the given H-offset.
    If the date is occupied the same star will be selected with the 2nd minimum distance to the given H-offset and so on. 
    Another star will be chosen in chronological order of availabilty if all the times the brightest star is available are occupied.

    Arguments:
        Occupied_Timeline (:obj:`dict` of :obj:`list`): Dictionary with keys equal to planned and scheduled Modes/CMDs with entries equal to their start and end time as a list.
        SpottedStarList ((:obj:`list` of :obj:`dict`)): A list containing dictionaries containing parameters for each time a star is spotted.

    Returns:
        (tuple): tuple containing:
            (:obj:`dict` of :obj:`list`): Occupied_Timeline (updated with the result from the scheduled Mode). \n
            (str): Comment regarding the result of scheduling of the mode.

    """

    Mode120_settings = configFile.Mode120_settings()
    Timeline_settings = configFile.Timeline_settings()
    Mode120Iteration = configFile.Mode120Iteration


    "Get offset where the star should be"
    Offset_Index = (Mode120Iteration-1) % (len(Mode120_settings['V_offset']))
    H_offset = Mode120_settings['H_offset'][Offset_Index]

    Logger.info('Start of filtering function')

    if(len(SpottedStarList) == 0):
        Mode120_comment = 'Stars not visible (Empty SpottedStarList)'

        Logger.warning(Mode120_comment)
        #input('Enter anything to acknowledge and continue')

        return Occupied_Timeline, Mode120_comment

    star_min_mag_H_offset = []

    star_H_offset = [SpottedStarList[x]['H-offset']
                     for x in range(len(SpottedStarList))]

    star_V_offset = [SpottedStarList[x]['V-offset']
                     for x in range(len(SpottedStarList))]
    star_date = [SpottedStarList[x]['Date'] for x in range(len(SpottedStarList))]
    star_mag = [SpottedStarList[x]['Vmag'] for x in range(len(SpottedStarList))]
    star_name = [SpottedStarList[x]['Name'] for x in range(len(SpottedStarList))]
    long_MATS = [SpottedStarList[x]['long_MATS'] for x in range(len(SpottedStarList))]
    lat_MATS = [SpottedStarList[x]['lat_MATS'] for x in range(len(SpottedStarList))]
    Dec_optical_axis = [SpottedStarList[x]['Dec_optical_axis']
                        for x in range(len(SpottedStarList))]
    RA_optical_axis = [SpottedStarList[x]['RA_optical_axis']
                       for x in range(len(SpottedStarList))]

    star_mag_sorted = [abs(x) for x in star_mag]
    star_mag_sorted.sort()

    Logger.info('Brightest star magnitude: '+str(min(star_mag)))
    arbitraryLargeNumber = 1000

    "Extract all the H-offsets for the brightest star. Allows scheduling in order of rising H-offset for the brightest star"
    for x in range(len(SpottedStarList)):
        if(min(star_mag) == star_mag[x]):
            star_min_mag_H_offset.append(star_H_offset[x])

        # Just adds an arbitrary large H-offset value for stars other than the brightest to keep the list the same length.
        # This will also allow all instances with the brightest star to be scheduled first. Then later in random magnitude order.
        else:
            star_min_mag_H_offset.append(arbitraryLargeNumber)
            "Increase the arbitraryLargeNumber to keep H-offsets different, which allow scheduling of stars with other magnitudes than the brightest if needed"
            arbitraryLargeNumber += 1

    "Extract and sort the H-offsets."
    star_H_offset_abs = [abs(x-H_offset) for x in star_min_mag_H_offset]

    star_H_offset_sorted = [abs(x-H_offset) for x in star_min_mag_H_offset]
    star_H_offset_sorted.sort()
    Logger.debug('star_H_offset_abs: '+str(star_H_offset_abs))
    Logger.debug('star_H_offset_sorted: '+str(star_H_offset_sorted))

    restart = True
    iterations = 0
    "Selects date based on min H-offset, if occupied, select date for next min H-offset"
    while(restart == True):

        "If all available dates for the brightest star is occupied, no Mode120 will be schedueled"
        if(len(star_min_mag_H_offset) == iterations):
            Mode120_comment = 'No available time for Mode120 using the brightest available star'
            Logger.warning(Mode120_comment)
            #input('Enter anything to ackknowledge and continue')
            return Occupied_Timeline, Mode120_comment

        restart = False

        """Extract index of minimum H-offset for first iteration, 
        #then next smallest if 2nd iterations needed and so on. """
        x = star_H_offset_abs.index(star_H_offset_sorted[iterations])

        StartDate = star_date[x]

        StartDate = DT.datetime.strptime(StartDate,'%Y-%m-%d %H:%M:%S.%f') - DT.timedelta(seconds= Mode120_settings['freeze_start'])

        endDate =StartDate+DT.timedelta(seconds = Mode120_settings['freeze_start'] + Mode120_settings['freeze_duration'] + configFile.Timeline_settings()["pointing_stabilization"] + Timeline_settings['mode_separation'])

        "Check that the scheduled date is not before the start of the timeline"
        if(StartDate < DT.datetime.strptime(configFile.Timeline_settings()['start_date'],'%Y/%m/%d %H:%M:%S')):
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
                    if(busy_date[0] <= StartDate <= busy_date[1] or
                            busy_date[0] <= endDate <= busy_date[1] or
                            (StartDate < busy_date[0] and endDate > busy_date[1])):

                        iterations = iterations + 1
                        restart = True
                        break

    comment = ('Star name:'+star_name[x]+', V-offset: '+str(np.round(star_V_offset[x], 2))+', H-offset: '+str(np.round(star_H_offset[x], 2))+', V-mag: '+str(star_mag[x])+', Number of times date changed: '+str(iterations)
               + ', MATS (long,lat) in degrees = ('+str(np.round(long_MATS[x],2))+', '+str(np.round(lat_MATS[x],2))+'), optical-axis Dec (J2000 ICRS): '+str(np.round(Dec_optical_axis[x],2))+'), optical-axis RA (J2000 ICRS): '+str(np.round(RA_optical_axis[x],2)) +
               '), star Dec (J2000 ICRS): '+str(np.round(SpottedStarList[x]['Dec'],1))+', star RA (J2000 ICRS): '+str(np.round(SpottedStarList[x]['RA'],1)))

    Occupied_Timeline['Mode120'].append((StartDate, endDate))

    return Occupied_Timeline, comment
