# -*- coding: utf-8 -*
"""Functions that are commonly used by the Operational Planning Tool.
"""

import ephem
import importlib
import time
import logging
import os
import sys
import astropy.time
from pylab import (
    cos,
    sin,
    cross,
    dot,
    arctan,
    sqrt,
    array,
    arccos,
    pi,
    floor,
    around,
    norm,
)
from skyfield import api

from mats_planningtool import MATS_coordinates


timescale_skyfield = api.load.timescale(builtin=True)
database_skyfield = api.load("de421.bsp")


def rot_arbit(angle, u_v):
    """Takes an angle in radians and a unit vector and outputs a rotation matrix around that vector

    Arguments:
        angle (int): Angle in radians.
        u_v (list): Unit vector

    Returns:
        (array): Rotation matrix

    """

    rot_mat = array(
        [
            (
                cos(angle) + u_v[0] ** 2 * (1 - cos(angle)),
                u_v[0] * u_v[1] * (1 - cos(angle)) - u_v[2] * sin(angle),
                u_v[0] * u_v[2] * (1 - cos(angle)) + u_v[1] * sin(angle),
            ),
            (
                u_v[1] * u_v[0] * (1 - cos(angle)) + u_v[2] * sin(angle),
                cos(angle) + u_v[1] ** 2 * (1 - cos(angle)),
                u_v[1] * u_v[2] * (1 - cos(angle)) - u_v[0] * sin(angle),
            ),
            (
                u_v[2] * u_v[0] * (1 - cos(angle)) - u_v[1] * sin(angle),
                u_v[2] * u_v[1] * (1 - cos(angle)) + u_v[0] * sin(angle),
                cos(angle) + u_v[2] ** 2 * (1 - cos(angle)),
            ),
        ]
    )

    return rot_mat


def deg2HMS(ra="", dec="", roundOf=False):
    """Takes a declination or a RAAN angle in degrees and converts it to DMS or HMS format respectively

    Only one (and only one!) of the inputs (ra or dec) shall be provided.

    Arguments:
        ra (str): RAAN angle in degrees.
        dec (str): Declination angle in degrees.
        roundOf (bool): True for rounding of seconds to nearest integer. False for seconds with decimals.

    Returns:
        (str): RAAN or Declination angle in HMS format.

    """

    RA, DEC, rs, ds = "", "", "", ""

    if dec:
        if str(dec)[0] == "-":
            ds, dec = "-", abs(dec)
        deg = int(dec)
        decM = abs(int((dec - deg) * 60))
        if roundOf:
            decS = int((abs((dec - deg) * 60) - decM) * 60)
        else:
            decS = (abs((dec - deg) * 60) - decM) * 60
        DEC = "{0}{1} {2} {3}".format(ds, deg, decM, decS)

    elif ra:
        if str(ra)[0] == "-":
            rs, ra = "-", abs(ra)
        raH = int(ra / 15)
        raM = int(((ra / 15) - raH) * 60)
        if roundOf:
            raS = int(((((ra / 15) - raH) * 60) - raM) * 60)
        else:
            raS = ((((ra / 15) - raH) * 60) - raM) * 60
        RA = "{0}{1} {2} {3}".format(rs, raH, raM, raS)

    return RA or DEC


def lat_2_R(lat):
    """Takes a geodetic latitude and puts out the distance from the center of an ellipsoid Earth to the surface

    Arguments:
        lat (float): Geodetic Latitude angle [degrees].

    Returns:
        (float): Geocentric distance [km]

    """

    R_polar = 6356.752314245
    R_eq = 6378.137

    lat = lat / 180 * pi

    R = sqrt(
        ((R_eq ** 2 * cos(lat)) ** 2 + (R_polar ** 2 * sin(lat)) ** 2)
        / ((R_eq * cos(lat)) ** 2 + (R_polar * sin(lat)) ** 2)
    )

    # e = sqrt(1-R_polar**2/R_eq**2)
    # R = R_eq/sqrt(1-e**2*sin(lat/180*pi)**2)
    # R = sqrt( ( (R_eq**2*cos(lat))**2 + (R_polar**2*sin(lat))**2 ) / ( (R_eq*cos(lat))**2 + (R_polar*sin(lat))**2 ) )

    return R


def lat_calculator(Satellite_skyfield, date):
    """ Function that calculates the latitude of a skyfield.sgp4lib.EarthSatellite object at a certain date

    Mainly used to approximate the latitude of the LP as the LP is close to being in the same plane as the orbital plane. 
    So if the orbital position angle between LP and MATS is known (and MATS orbit is circular), then the time difference is known, then this function can be used to calculate the lat of MATS at a previous location to estimate the LPs current latitude.

    Used only in Timeline_gen and XML_gen to estimate LPs latitude without using computational difficult methods to save run time.  

    Arguments:
        Satellite_skyfield (:obj:`skyfield.sgp4lib.EarthSatellite`): A Skyfield object representing an EarthSatellite defined by a TLE.
        date (:obj:`datetime.datetime`): The date of the calculation.

    Returns: 
        (float): Latitude given in degrees.
    """

    year = date.year
    month = date.month
    day = date.day
    hour = date.hour
    minute = date.minute
    second = date.second + date.microsecond / 1000000

    date_skyfield = timescale_skyfield.utc(year, month, day, hour, minute, second)

    satellite_geo = Satellite_skyfield.at(date_skyfield)
    satellite_subpoint = satellite_geo.subpoint()
    latitude = satellite_subpoint.latitude.degrees

    return latitude


def scheduler(Occupied_Timeline, date, endDate):
    """ Function that checks if the scheduled time is available.

    Changes the date until available or until no time is determined to be available.

    Arguments:
        Occupied_Timeline (dict): A dictionary of currently planned Modes containing lists with their scheduled times ([startDate, endDate]) as ephem.Date class.
        date (:obj:`ephem.Date`): The scheduled startdate of the current Mode.
        endDate (:obj:`ephem.Date`): The scheduled end-date of the current Mode.

    Returns: 
        (tuple): tuple containing:

            - **date** (*ephem.Date*): The scheduled startdate (potentially changed).
            - **endDate** (*ephem.Date*): The scheduled end-date (potentially changed).
            - **iterations** (*int*): The number of times the scheduled date got changed.

    """

    iterations = 0
    restart = True
    "## Checks if date is available and postpones starting date of mode until available"
    while restart == True:
        restart = False

        "Extract the start and end dates of scheduled mode"
        for busy_dates in Occupied_Timeline.values():
            if restart:
                break
            if busy_dates == []:
                continue
            else:

                "Extract the start and end date of each instance of a scheduled mode"
                for busy_date in busy_dates:

                    "If the planned date collides with any already scheduled ones -> post-pone and restart loop"
                    if (
                        busy_date[0] <= date < busy_date[1]
                        or busy_date[0] < endDate <= busy_date[1]
                        or (date < busy_date[0] and endDate > busy_date[1])
                    ):

                        endDate = ephem.Date(endDate + abs(date - busy_date[1]))
                        date = ephem.Date(busy_date[1])

                        iterations = iterations + 1
                        restart = True
                        break

    return date, endDate, iterations


def dict_comparator(dict1, dict2, Logger=None):
    """Function which compares the keys of two dictionaries and outputs a new dictionary. 

    A dict_new will be created containing all the keys and values of dict2. Then for any keys that 
    exist in both dict1 and dict_new, dict_new's keys will have their values replaced by the ones in dict1.

    Used to compare settings given in a Science Mode Timeline to the same kind of settings given in the Configuration File.

    WARNING! All keys in dict1 must also exist in dict2.

    Arguments:
        dict1 (dict):
        dict2 (dict): 
        Logger (:obj:`logging.Logger`): Logger used to log the result. 

    Returns:
        (dict): dict_new

    """

    "Check if the dictionaries are different"
    if dict1 != dict2:
        dict_new = dict2
        "Loop through keys and exchange values"
        for key in dict1.keys():
            dict_new[key] = dict1[key]
    else:
        dict_new = dict1

    if Logger != None:
        Logger.debug("params from Science Mode List: " + str(dict1))
        Logger.debug("params after params_checker function: " + str(dict_new))
        Logger.info("params used: " + str(dict_new))

    return dict_new


def utc_to_onboardTime(utc_date):
    """Function which converts a date in utc into onboard time (GPS) in seconds and rounds to nearest 10th of a second.

    Arguments:
        utc_date (:obj:`ephem.Date`): The date as a ephem.Date object.

    Returns:
        (float): Onboard GPS time in seconds.

    """

    utc_TimeObject = astropy.time.Time(utc_date.datetime(), scale="utc")
    onboardGPSTime = around(utc_TimeObject.gps, 1)

    return onboardGPSTime


def SetupLogger(LoggerName):
    """Removes previous handlers and sets up a logger with both a file handler and a stream handler.

    Arguments:
        LoggerName (str): The name of the Logger.

    Returns:
        None
    """

    Logger = logging.getLogger(LoggerName)
    name = sys._getframe(1).f_code.co_name
    "######## Try to Create a directory for storage of Logs #######"
    try:
        os.mkdir("Logs_" + name)
    except:
        pass

    "Remove all previous handlers of the logger"
    for handler in Logger.handlers[:]:
        Logger.removeHandler(handler)

    timestr = time.strftime("%Y%m%d-%H%M%S")
    logstring = os.path.join("Logs_" + name, name + "__" + timestr + ".log")
    Handler = logging.FileHandler(logstring, mode="a")
    formatter = logging.Formatter(
        "%(levelname)6s : %(message)-80s :: %(module)s :: %(funcName)s"
    )
    Handler.setFormatter(formatter)
    Logger.addHandler(Handler)
    Logger.setLevel(logging.DEBUG)

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(formatter)
    Logger.addHandler(streamHandler)


def calculate_time_per_row(NCOL, NCBIN, NCBINFPGA, NRSKIP, NROW, NRBIN, NFLUSH):
    """This function provides an estimated amount of time for a CCD readout.

    Note that minor "transition" states may have been omitted resulting in 
    somewhat shorter readout times (<0.1%).

    Default timing setting is:\n
    ccd_r_timing <= x"A4030206141D"&x"010303090313"

    All pixel timing setting is the final count of a counter that starts at 0,
    so the number of clock cycles exceeds the setting by 1.

    Created by Georgi Olentsenko at KTH.

    Arguments:
        NCOL (int): Number of columns
        NCBIN (int): Number of columns to bin
        NCBINFPGA (int): Binning with FPGA
        NRSKIP (int): Number of rows to skip
        NROW (int): Number of rows
        NRBIN (int): Number of rows to bin
        NFLUSH (int): Number of pre-exposure flushes

    Returns:
        (float): Readout time in ms. 

    """

    # image parameters
    ncol = int(NCOL) + 1
    ncolbinC = int(NCBIN)
    if ncolbinC == 0:
        ncolbinC = 1
    ncolbinF = 2 ** int(NCBINFPGA)

    nrow = int(NROW)
    nrowbin = int(NRBIN)
    if nrowbin == 0:
        nrowbin = 1
    nrowskip = int(NRSKIP)

    n_flush = int(NFLUSH)

    # timing settings
    full_timing = 0  # TODO <-- meaning?

    # full pixel readout timing
    time0 = 1 + 19  # x13%TODO
    time1 = 1 + 3  # x03%TODO
    time2 = 1 + 9  # x09%TODO
    time3 = 1 + 3  # x03%TODO
    time4 = 1 + 3  # x03%TODO
    time_ovl = 1 + 1  # x01%TODO

    # fast pixel readout timing
    timefast = 1 + 2  # x02%TODO
    timefastr = 1 + 3  # x03%TODO

    # row shift timing
    row_step = 1 + 164  # xA4%TODO

    clock_period = 30.517  # master clock period, ns 32.768 MHz

    # there is one extra clock cycle, effectively adding to time 0
    Time_pixel_full = (
        1 + time0 + time1 + time2 + time3 + time4 + 3 * time_ovl
    ) * clock_period

    # this is the fast timing pixel period
    Time_pixel_fast = (1 + 4 * timefast + 3 * time_ovl + timefastr) * clock_period

    # here we calculate the number of fast and slow pixels
    # NOTE: the effect of bad pixels is disregarded here

    if full_timing == 1:
        n_pixels_full = 2148
        n_pixels_fast = 0
    else:
        if ncolbinC < 2:  # no CCD binning
            n_pixels_full = ncol * ncolbinF
        else:  # there are two "slow" pixels for one superpixel to be read out
            n_pixels_full = 2 * ncol * ncolbinF
        n_pixels_fast = 2148 - n_pixels_full

    # time to read out one row
    T_row_read = n_pixels_full * Time_pixel_full + n_pixels_fast * Time_pixel_fast

    # shift time of a single row
    T_row_shift = (64 + row_step * 10) * clock_period

    # time of the exposure start delay from the start_exp signal # n_flush=1023
    T_delay = T_row_shift * n_flush

    # total time of the readout
    T_readout = T_row_read * (nrow + nrowskip + 1) + T_row_shift * (1 + nrowbin * nrow)

    # "smearing time"
    # (this is the time that any pixel collects electrons in a wrong row, during the shifting.)
    # For smearing correction, this is the "extra exposure time" for each of the rows.
    T_row_extra = T_row_read + T_row_shift * nrowbin

    return T_readout / 1e6, T_delay / 1e6, T_row_extra / 1e6


def SyncArgCalculator(CCD_settings, ExtraOffset, ExtraIntervalTime):
    """Calculates appropriate arguments for the CCD Synchonize CMD.

    Does not take into account the nadir CCD as it is not required to synchronize, because interference caused by the nadir CCD is low.
    The CCDs are offset in order of ExposureTime (TEXPMS) with the CCD with the shortest ExposureTime being the leading CCD. \n
    CCDs with ExposureTime equal to zero are skipped. \n
    The offset calculations depend on the Readout Time, which depends on the binning settings of the CCDs. \n
    The ExposureInterval Time (TEXPIMS) depends on the longest combined Readout Time and ExposureTime for a CCD aswell as the 
    leading CCD's Exposure Time to prevent collision between
    readout of the leading CCD and the final CCD. If the combined TransferTime is estimated to be longer than TEXPIMS; TEXPIMS is set to the estimated combined TransferTime to prevent CRB crash. 

    Arguments:
        CCD_settings (dict of dict of int): Dictionary containing settings for the CCDs.
        ExtraOffset (int): Extra offset time [ms] that is added to an estimated ReadoutTime.
        ExtraIntervalTime (int): Extra time [ms] that is added to the calculated Exposure Interval Time.

    Returns:
        (tuple): tuple containing:

            - **CCDSEL** (*int*): Calculated CCDSEL argument for the CCD Synchronize CMD.
            - **NCCD** (*int*): Calculated NCCD argument for the CCD Synchronize CMD.
            - **TEXPIOFS** (*list of int*): Calculated TEXPIOFS argument for the CCD Synchronize CMD.
            - **TEXPIMS** (*int*): Calculated minimum Exposure Interval Time [ms].

    """

    CCDSEL_16 = CCD_settings[16]
    CCDSEL_32 = CCD_settings[32]
    CCDSEL_1 = CCD_settings[1]
    CCDSEL_8 = CCD_settings[8]
    CCDSEL_2 = CCD_settings[2]
    CCDSEL_4 = CCD_settings[4]

    "Calculate Readout Times for the CCDs"
    ReadOutTime = []

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_16["NCOL"],
        NCBIN=CCDSEL_16["NCBIN"],
        NCBINFPGA=CCDSEL_16["NCBINFPGA"],
        NRSKIP=CCDSEL_16["NRSKIP"],
        NROW=CCDSEL_16["NROW"],
        NRBIN=CCDSEL_16["NRBIN"],
        NFLUSH=CCDSEL_16["NFLUSH"],
    )
    ReadOutTime_16 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_16))

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_32["NCOL"],
        NCBIN=CCDSEL_32["NCBIN"],
        NCBINFPGA=CCDSEL_32["NCBINFPGA"],
        NRSKIP=CCDSEL_32["NRSKIP"],
        NROW=CCDSEL_32["NROW"],
        NRBIN=CCDSEL_32["NRBIN"],
        NFLUSH=CCDSEL_32["NFLUSH"],
    )
    ReadOutTime_32 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_32))

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_1["NCOL"],
        NCBIN=CCDSEL_1["NCBIN"],
        NCBINFPGA=CCDSEL_1["NCBINFPGA"],
        NRSKIP=CCDSEL_1["NRSKIP"],
        NROW=CCDSEL_1["NROW"],
        NRBIN=CCDSEL_1["NRBIN"],
        NFLUSH=CCDSEL_1["NFLUSH"],
    )
    ReadOutTime_1 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_1))

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_8["NCOL"],
        NCBIN=CCDSEL_8["NCBIN"],
        NCBINFPGA=CCDSEL_8["NCBINFPGA"],
        NRSKIP=CCDSEL_8["NRSKIP"],
        NROW=CCDSEL_8["NROW"],
        NRBIN=CCDSEL_8["NRBIN"],
        NFLUSH=CCDSEL_8["NFLUSH"],
    )
    ReadOutTime_8 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_8))

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_2["NCOL"],
        NCBIN=CCDSEL_2["NCBIN"],
        NCBINFPGA=CCDSEL_2["NCBINFPGA"],
        NRSKIP=CCDSEL_2["NRSKIP"],
        NROW=CCDSEL_2["NROW"],
        NRBIN=CCDSEL_2["NRBIN"],
        NFLUSH=CCDSEL_2["NFLUSH"],
    )
    ReadOutTime_2 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_2))

    T_readout, T_delay, T_Extra = calculate_time_per_row(
        NCOL=CCDSEL_4["NCOL"],
        NCBIN=CCDSEL_4["NCBIN"],
        NCBINFPGA=CCDSEL_4["NCBINFPGA"],
        NRSKIP=CCDSEL_4["NRSKIP"],
        NROW=CCDSEL_4["NROW"],
        NRBIN=CCDSEL_4["NRBIN"],
        NFLUSH=CCDSEL_4["NFLUSH"],
    )
    ReadOutTime_4 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_4))

    """
    T_readout, T_delay, T_Extra = calculate_time_per_row(NCOL = CCDSEL_64['NCOL'], NCBIN = CCDSEL_64['NCBIN'], NCBINFPGA = CCDSEL_64['NCBINFPGA'], 
                                                         NRSKIP = CCDSEL_64['NRSKIP'], NROW = CCDSEL_64['NROW'], 
                                                         NRBIN = CCDSEL_64['NRBIN'], NFLUSH = CCDSEL_64['NFLUSH'])
    ReadOutTime_64 = T_readout + T_delay + T_Extra
    ReadOutTime.append(int(ReadOutTime_64))
    """

    "Sort ExposureTimes of the CCDs"
    ExpTimes = [
        CCDSEL_16["TEXPMS"],
        CCDSEL_32["TEXPMS"],
        CCDSEL_1["TEXPMS"],
        CCDSEL_8["TEXPMS"],
        CCDSEL_2["TEXPMS"],
        CCDSEL_4["TEXPMS"],
    ]
    ExpTimes.sort()

    "Add arbitrary numbers to allow the offset time to be positioned at the right spot"
    TEXPIOFS = [-1, -1, -1, -1, -1, -1, -1]

    ExpIntervals = []
    x = 0
    # ExtraOffset = Timeline_settings['CCDSYNC_ExtraOffset']
    # ExtraIntervalTime = Timeline_settings['CCDSYNC_ExtraIntervalTime']
    CCDSEL = 0

    Flag_16 = False
    Flag_32 = False
    Flag_1 = False
    Flag_8 = False
    Flag_2 = False
    Flag_4 = False
    # Flag_64 = False

    OffsetTime = 0
    previous_ExpTime = 0

    TransferTimes = []
    TransfertimePerPixel = 0.01  # in ms

    "Calculate offset time in order of ExposureTime"
    for ExpTime in ExpTimes:

        ExpTimeIncrease = ExpTime - previous_ExpTime
        OffsetTime = OffsetTime - ExpTimeIncrease
        if OffsetTime < 0:
            OffsetTime = 0

        if ExpTime == 0:
            continue
        elif ExpTime == CCDSEL_16["TEXPMS"] and Flag_16 == False:
            Flag_16 = True

            TEXPIOFS.insert(4, int(round(OffsetTime / 10, 0) * 10))
            OffsetTime = OffsetTime + (ReadOutTime_16 + ExtraOffset)

            ExpIntervals.append(
                ReadOutTime_16 + CCDSEL_16["TEXPMS"] + ExtraIntervalTime
            )

            "Save estimated TransferTime"
            # if( CCDSEL_16['NCOL'] * CCDSEL_16['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            TransferTimes.append(
                CCDSEL_16["NCOL"] * CCDSEL_16["NROW"] * TransfertimePerPixel
            )

            CCDSEL += 16

        elif ExpTime == CCDSEL_32["TEXPMS"] and Flag_32 == False:
            Flag_32 = True

            TEXPIOFS.insert(5, int(round(OffsetTime / 10, 0) * 10))

            OffsetTime = OffsetTime + (ReadOutTime_32 + ExtraOffset)

            ExpIntervals.append(
                ReadOutTime_32 + CCDSEL_32["TEXPMS"] + ExtraIntervalTime
            )

            "Save estimated TransferTime"
            # if( CCDSEL_32['NCOL'] * CCDSEL_32['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            TransferTimes.append(
                CCDSEL_32["NCOL"] * CCDSEL_32["NROW"] * TransfertimePerPixel
            )

            CCDSEL += 32

        elif ExpTime == CCDSEL_1["TEXPMS"] and Flag_1 == False:
            Flag_1 = True

            TEXPIOFS.insert(0, int(round(OffsetTime / 10, 0) * 10))
            OffsetTime = OffsetTime + (ReadOutTime_1 + ExtraOffset)

            ExpIntervals.append(ReadOutTime_1 + CCDSEL_1["TEXPMS"] + ExtraIntervalTime)

            "Save estimated TransferTime"
            # if( CCDSEL_1['NCOL'] * CCDSEL_1['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            TransferTimes.append(
                CCDSEL_1["NCOL"] * CCDSEL_1["NROW"] * TransfertimePerPixel
            )

            CCDSEL += 1

        elif ExpTime == CCDSEL_8["TEXPMS"] and Flag_8 == False:
            Flag_8 = True

            TEXPIOFS.insert(3, int(round(OffsetTime / 10, 0) * 10))

            OffsetTime = OffsetTime + (ReadOutTime_8 + ExtraOffset)

            ExpIntervals.append(ReadOutTime_8 + CCDSEL_8["TEXPMS"] + ExtraIntervalTime)

            "Save estimated TransferTime"
            # if( CCDSEL_8['NCOL'] * CCDSEL_8['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            TransferTimes.append(
                CCDSEL_8["NCOL"] * CCDSEL_8["NROW"] * TransfertimePerPixel
            )

            CCDSEL += 8

        elif ExpTime == CCDSEL_2["TEXPMS"] and Flag_2 == False:
            Flag_2 = True

            TEXPIOFS.insert(1, int(round(OffsetTime / 10, 0) * 10))

            OffsetTime = OffsetTime + (ReadOutTime_2 + ExtraOffset)

            ExpIntervals.append(ReadOutTime_2 + CCDSEL_2["TEXPMS"] + ExtraIntervalTime)

            "Save estimated TransferTime"
            # if( CCDSEL_2['NCOL'] * CCDSEL_2['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            TransferTimes.append(
                CCDSEL_2["NCOL"] * CCDSEL_2["NROW"] * TransfertimePerPixel
            )

            CCDSEL += 2

        elif ExpTime == CCDSEL_4["TEXPMS"] and Flag_4 == False:
            Flag_4 = True

            TEXPIOFS.insert(2, int(round(OffsetTime / 10, 0) * 10))

            OffsetTime = OffsetTime + (ReadOutTime_4 + ExtraOffset)

            ExpIntervals.append(ReadOutTime_4 + CCDSEL_4["TEXPMS"] + ExtraIntervalTime)

            "Save estimated TransferTime"
            TransferTimes.append(
                CCDSEL_4["NCOL"] * CCDSEL_4["NROW"] * TransfertimePerPixel
            )
            # if( CCDSEL_4['NCOL'] * CCDSEL_4['NROW'] * TransfertimePerPixel >=  ExpIntervals[len(ExpIntervals)-1] ):
            #    ExpIntervals[len(ExpIntervals)-1] = CCDSEL_4['NCOL'] * CCDSEL_4['NROW'] * TransfertimePerPixel

            CCDSEL += 4

        """
        elif( ExpTime == CCDSEL_64['TEXPMS'] and Flag_64 == False):
            Flag_64 = True
            
            TEXPIOFS.insert(6, int(round(OffsetTime/10,0)*10))
            
            OffsetTime = OffsetTime + (ReadOutTime_64+ExtraOffset)
            
            ExpIntervals.append(ReadOutTime_64 + CCDSEL_64['TEXPMS'] + ExtraIntervalTime)
            CCDSEL += 64
            
        """
        previous_ExpTime = ExpTime
        x += 1

    "Remove arbitrary numbers after TEXPOIFS arguments have been positioned correctly"
    for x in range(TEXPIOFS.count(-1)):
        TEXPIOFS.remove(-1)

    TransferTimesCombined = sum(TransferTimes)

    ExpInterval = max(ExpIntervals)

    for FirstExpTime in ExpTimes:
        if FirstExpTime != 0:
            break

    "Increase the IntervalTime if it is too short, meaning that the Exposure and Readout of the last CCD interferes with the Readout of the leading CCD"
    if FirstExpTime <= max(TEXPIOFS):
        ExpInterval = ExpInterval + (max(TEXPIOFS) - FirstExpTime)
    if TransferTimesCombined > ExpInterval:
        ExpInterval = TransferTimesCombined

    TEXPIMS = int(round(ExpInterval, -2))

    NCCD = bin(CCDSEL).count("1")

    return CCDSEL, NCCD, TEXPIOFS, TEXPIMS


def OrderingOfCCDSnapshots(CCD_settings):
    """Calculates a list of CCDSEL (1,2,4,8,16,32) arguments corresponding to their TEXPMS in increasing order.

    Used to take snapshots in increasing order of TEXPMS, which will prevent streaks from simultaneous readouts to occur when snapshots are staggered.
    Any CCDs with TEXPMS equal to 0 will be ignored and not added to the list.

    Arguments:
        CCD_settings (dict of dict of int): Dictionary containing settings for the CCDs.

    Returns:
        (list of int): List containing CCDSEL arguments in the order of increasing TEXPMS.

    """

    CCDSEL_16 = CCD_settings[16]
    CCDSEL_32 = CCD_settings[32]
    CCDSEL_1 = CCD_settings[1]
    CCDSEL_8 = CCD_settings[8]
    CCDSEL_2 = CCD_settings[2]
    CCDSEL_4 = CCD_settings[4]

    "Sort ExposureTimes of the CCDs"
    ExpTimes = [
        CCDSEL_16["TEXPMS"],
        CCDSEL_32["TEXPMS"],
        CCDSEL_1["TEXPMS"],
        CCDSEL_8["TEXPMS"],
        CCDSEL_2["TEXPMS"],
        CCDSEL_4["TEXPMS"],
    ]
    ExpTimes.sort()

    CCDSEL = []

    "Make a list with CCDSEL arguments in increasing order of TEXPMS, CCDs with TEXPMS equal to 0 are ignored"
    for ExpTime in ExpTimes:
        if CCDSEL_16["TEXPMS"] == ExpTime and 16 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(16)
        elif CCDSEL_32["TEXPMS"] == ExpTime and 32 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(32)
        elif CCDSEL_1["TEXPMS"] == ExpTime and 1 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(1)
        elif CCDSEL_8["TEXPMS"] == ExpTime and 8 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(8)
        elif CCDSEL_2["TEXPMS"] == ExpTime and 2 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(2)
        elif CCDSEL_4["TEXPMS"] == ExpTime and 4 not in CCDSEL and ExpTime != 0:
            CCDSEL.append(4)

    return CCDSEL


def CCDSELExtracter(CCDSEL):
    """Extract the individual CCDSEL (64, 32, 16, 8, 4, 2, 1) arguments from a number CCDSEL argument assuming the CCDSEL argument is valid.

    Argument:
        CCDSEL (int): Value between 0 and 127 which represent the selection of a number of CCDs.

    Returns:
        (list of int): List containing individual CCDSEL arguments.

    """

    CCDSELs = [64, 32, 16, 8, 4, 2, 1]
    IndividualCCDSEL = []

    for CCD in CCDSELs:
        if CCDSEL != 0:
            rest = CCDSEL % CCD

            if rest in CCDSELs:
                IndividualCCDSEL.append(rest)
                CCDSEL -= rest
                if CCD <= CCDSEL:
                    IndividualCCDSEL.append(CCD)
                    CCDSEL -= CCD
            else:
                # elif( rest == 0 ):
                # IndividualCCDSEL.append(CCD)
                # CCDSEL -= CCD
                if CCD <= CCDSEL:
                    IndividualCCDSEL.append(CCD)
                    CCDSEL -= CCD

    return IndividualCCDSEL


def Satellite_Simulator(
    Satellite_skyfield,
    SimulationTime,
    Timeline_settings,
    pointing_altitude,
    LogFlag=False,
    Logger=None,
):
    """Simulates a single point in time for a Satellite using Skyfield and also the pointing of the satellite.

    Only estimates the actual pointing definition used by OHB as it is uncertain if the algorithm to calculate the LP here is the same as the one OHB uses. 
    The LP is calculated with an algorithm derived by Nick Lloyd at University of Saskatchewan, 
    Canada (nick.lloyd@usask.ca), and is part of
    the operational code for both OSIRIS and SMR on-board- the Odin satellite. An offset is added to the pointing altitude to better mimic OHBs actual LP.

    Arguments:
        Satellite_skyfield (:obj:`skyfield.sgp4lib.EarthSatellite`): A Skyfield object representing an EarthSatellite defined by a TLE.
        SimulationTime (:obj:`ephem.Date`): The time of the simulation.
        Timeline_settings (dict): A dictionary containing relevant settings to the simulation.
        pointing_altitude (float): Contains the pointing altitude of the simulation [km].
        LogFlag (bool): If data from the simulation shall be logged.
        Logger (:obj:`logging.Logger`): Logger used to log the result from the simulation if LogFlag == True.

    Returns:
        (dict): Dictionary containing simulated data.

    """

    U = 398600.441800000  # Earth gravitational parameter
    R_mean = 6371.000
    celestial_eq = [0, 0, 1]

    "Offset the pointing altitude slightly which improves the estimation of OHBs actual pointing"
    pointing_altitude = pointing_altitude + 0.3

    yaw_correction = Timeline_settings["yaw_correction"]

    current_time_datetime = ephem.Date(SimulationTime).datetime()
    year = current_time_datetime.year
    month = current_time_datetime.month
    day = current_time_datetime.day
    hour = current_time_datetime.hour
    minute = current_time_datetime.minute
    second = current_time_datetime.second + current_time_datetime.microsecond / 1000000

    current_time_skyfield = timescale_skyfield.utc(
        year, month, day, hour, minute, second
    )

    Satellite_geo = Satellite_skyfield.at(current_time_skyfield)
    v_Satellite = Satellite_geo.velocity.km_per_s
    r_Satellite = Satellite_geo.position.km
    Satellite_distance = Satellite_geo.distance().km
    Satellite_subpoint = Satellite_geo.subpoint()
    lat_Satellite = Satellite_subpoint.latitude.degrees
    long_Satellite = Satellite_subpoint.longitude.degrees
    alt_Satellite = Satellite_subpoint.elevation.km

    r_Satellite_unit_vector = r_Satellite / norm(r_Satellite)

    "Semi-Major axis of Satellite, assuming circular orbit"
    Satellite_p = norm(r_Satellite)

    "Orbital Period of Satellite"
    orbital_period = 2 * pi * sqrt(Satellite_p ** 3 / U)

    "Initial Estimated pitch or elevation angle for Satellite pointing (angle between negativ velocity vector and optical axis in the orbital plane)"
    OrbAngleBetweenSatelliteAndLP = (
        arccos((R_mean + pointing_altitude) / (Satellite_distance)) / pi * 180
    )

    time_between_LP_and_Satellite = orbital_period * OrbAngleBetweenSatelliteAndLP / 360

    "Estimation of lat of LP using the position of Satellite at a previous time"
    date_of_Satellitelat_is_equal_2_current_LPlat = ephem.Date(
        SimulationTime - ephem.second * time_between_LP_and_Satellite
    ).datetime()
    lat_LP = lat_calculator(
        Satellite_skyfield, date_of_Satellitelat_is_equal_2_current_LPlat
    )
    R_earth_LP = lat_2_R(lat_LP)

    "More accurate estimated pitch or elevation angle for Satellite pointing"
    OrbAngleBetweenSatelliteAndLP = (
        arccos((R_earth_LP + pointing_altitude) / (Satellite_distance)) / pi * 180
    )

    Pitch = 90 + OrbAngleBetweenSatelliteAndLP

    "############# Calculations of orbital and pointing vectors ############"
    "Vector normal to the orbital plane of Satellite"
    normal_orbit = cross(r_Satellite, v_Satellite)
    normal_orbit = normal_orbit / norm(normal_orbit)

    "Calculate intersection between the orbital plane and the equator"
    ascending_node = cross(celestial_eq, normal_orbit)

    "Argument of latitude"
    arg_of_lat = (
        arccos(
            dot(ascending_node, r_Satellite) / norm(r_Satellite) / norm(ascending_node)
        )
        / pi
        * 180
    )

    "To determine if Satellite is moving towards the ascending node"
    if dot(cross(ascending_node, r_Satellite), normal_orbit) <= 0:
        arg_of_lat = 360 - arg_of_lat

    if yaw_correction == True:
        yaw_offset_angle = Timeline_settings["yaw_amplitude"] * cos(
            arg_of_lat / 180 * pi
            - (Pitch - 90) / 180 * pi
            - Timeline_settings["yaw_phase"] / 180 * pi
        )
    elif yaw_correction == False:
        yaw_offset_angle = 0

    "Rotate 'vector to Satellite', to represent pointing direction"
    rot_mat = rot_arbit(Pitch / 180 * pi, -normal_orbit)
    optical_axis = rot_mat @ (r_Satellite)

    "Apply yaw to optical_axis, meaning to rotate around the vector to Satellite"
    rot_mat = rot_arbit(yaw_offset_angle / 180 * pi, -r_Satellite_unit_vector)
    optical_axis = rot_mat @ optical_axis
    optical_axis_unit_vector = optical_axis / norm(optical_axis)

    "Rotate 'vector to Satellite', to represent vector normal to satellite H-offset "
    rot_mat = rot_arbit((Pitch - 90) / 180 * pi, -normal_orbit)
    r_H_offset_normal = rot_mat @ r_Satellite
    r_H_offset_normal = r_H_offset_normal / norm(r_H_offset_normal)

    "If pointing direction has a Yaw defined, Rotate yaw of normal to pointing direction H-offset plane, meaning to rotate around the vector to Satellite"
    rot_mat = rot_arbit(yaw_offset_angle / 180 * pi, -r_Satellite_unit_vector)
    r_H_offset_normal = rot_mat @ r_H_offset_normal
    r_H_offset_normal = r_H_offset_normal / norm(r_H_offset_normal)

    "Rotate negative orbital plane normal to make it into a normal to the V-offset plane"
    r_V_offset_normal = rot_mat @ -normal_orbit
    r_V_offset_normal = r_V_offset_normal / norm(r_V_offset_normal)

    "Calculate Dec and RA of optical axis"
    Dec_optical_axis = (
        arctan(optical_axis[2] / sqrt(optical_axis[0] ** 2 + optical_axis[1] ** 2))
        / pi
        * 180
    )
    RA_optical_axis = (
        arccos(
            dot([1, 0, 0], [optical_axis[0], optical_axis[1], 0])
            / norm([optical_axis[0], optical_axis[1], 0])
        )
        / pi
        * 180
    )
    if optical_axis[1] < 0:
        RA_optical_axis = 360 - RA_optical_axis

    if LogFlag == True and Logger != None:
        Logger.debug("")

        Logger.debug("SimulationTime time: " + str(SimulationTime))
        Logger.debug("Semimajor axis in km: " + str(Satellite_p))
        Logger.debug("Orbital Period in s: " + str(orbital_period))
        Logger.debug("Vector to Satellite [km]: " + str(r_Satellite))
        Logger.debug("Latitude in degrees: " + str(lat_Satellite))
        Logger.debug("Longitude in degrees: " + str(long_Satellite))
        Logger.debug("Altitude in km: " + str(alt_Satellite))
        Logger.debug("Satellite_distance [km]: " + str(Satellite_distance))

        Logger.debug("R_earth_LP [km]: " + str(R_earth_LP))

        Logger.debug("Pitch [degrees]: " + str(Pitch))
        Logger.debug("Yaw [degrees]: " + str(yaw_offset_angle))
        Logger.debug("ArgOfLat [degrees]: " + str(arg_of_lat))
        Logger.debug("Latitude of LP: " + str(lat_LP))
        Logger.debug("Optical Axis: " + str(optical_axis_unit_vector))
        Logger.debug(
            "Orthogonal direction to H-offset plane: " + str(r_H_offset_normal)
        )
        Logger.debug(
            "Orthogonal direction to V-offset plane: " + str(r_V_offset_normal)
        )
        Logger.debug("Orthogonal direction to the orbital plane: " + str(normal_orbit))

    Satellite_dict = {
        "Position [km]": r_Satellite,
        "Velocity [km/s]": v_Satellite,
        "OrbitNormal": normal_orbit,
        "OrbitalPeriod [s]": orbital_period,
        "Latitude [degrees]": lat_Satellite,
        "Longitude [degrees]": long_Satellite,
        "Altitude [km]": alt_Satellite,
        "AscendingNode": ascending_node,
        "ArgOfLat [degrees]": arg_of_lat,
        "Yaw [degrees]": yaw_offset_angle,
        "Pitch [degrees]": Pitch,
        "OpticalAxis": optical_axis_unit_vector,
        "Dec_OpticalAxis [degrees]": Dec_optical_axis,
        "RA_OpticalAxis [degrees]": RA_optical_axis,
        "Normal2H_offset": r_H_offset_normal,
        "Normal2V_offset": r_V_offset_normal,
        "EstimatedLatitude_LP [degrees]": lat_LP,
    }

    # return r_Satellite, lat_Satellite, long_Satellite, alt_Satellite, optical_axis_unit_vector, Dec_optical_axis, RA_optical_axis, r_H_offset_normal, r_V_offset_normal, orbital_period
    return Satellite_dict


'''
def IntrinsicEulerAnglesSLOF( VelocityVector, NegativeOrbitalNormal, NegativePosVector,):
    """Calculates intrinsic Euler angles (ZYZ or Yaw, Pitch, Roll) defined from SLOF (Spacecraft Local Orbit Frame)
    
    Arguments:
        VelocityVector (array): Velocity vector in GCRS. X basis vector in SLOF.
        NegativeOrbitalNormal (array): Negative orbital normal vector in GCRS. Y basis vector in SLOF.
        NegativePosVector (array): Negative positional vector in GCRS. Z basis vector in SLOF.
        
    Returns:
        (tuple): tuple containing:
            
            - **Yaw** (*float*): Yaw angle in degrees.
            - **Pitch** (*float*): Pitch angle in degrees.
            - **Roll** (*float*): Roll angle in degrees.
        
        
    
    """
    
    "Define SLOF basis"
    z_SLOF = NegativePosVector
    z_SLOF = z_SLOF / norm(z_SLOF)
    y_SLOF = NegativeOrbitalNormal
    y_SLOF = y_SLOF / norm(y_SLOF)
    x_SLOF = VelocityVector
    x_SLOF = x_SLOF / norm(x_SLOF)
    
    "Convert ECI coordinates to SLOF"
    dcm_SLOF_coordinate_system = array( ([x_SLOF[0], y_SLOF[0], z_SLOF[0]], [x_SLOF[1], y_SLOF[1], z_SLOF[1]], [x_SLOF[2], y_SLOF[2], z_SLOF[2]]) )
    dcm_change_of_basis_ECI_to_SLOF = transpose(dcm_SLOF_coordinate_system)
    r_change_of_basis_ECI_to_SLOF = R.from_dcm(dcm_change_of_basis_ECI_to_SLOF)
    
    optical_axis_SLOF = r_change_of_basis_ECI_to_SLOF.apply( optical_axis[t,:])
    r_V_offset_normal_SLOF = r_change_of_basis_ECI_to_SLOF.apply( r_V_offset_normal )
    r_H_offset_normal_SLOF = r_change_of_basis_ECI_to_SLOF.apply( r_H_offset_normal )
    
    
    
    "Find rotation and Euler angles from definition of optical axis in SLOF"
    basis_SLOF = array( ( (optical_axis_SLOF), (r_V_offset_normal_SLOF), (r_H_offset_normal_SLOF) ) )
    basis_ECI = array( ( (0,0,-1), (0,1,0), (1,0,0) ) )
    rotation, sensitivity_matrix = R.match_vectors(basis_SLOF, basis_ECI)
    
    Euler_angles[t,:] = rotation.as_euler('ZYZ', degrees=True)
    yaw_offset_angle[t] = Euler_angles[t,0]
    pitch_MATS[t] = Euler_angles[t,1]
    roll_MATS[t] = Euler_angles[t,2]
'''


def SunAngle(PositionVector, SimulationTime):
    """Calculates angle between a position vector and the position vector of the Sun.

    Simulates a single point in time for the Sun observed from Earth using Skyfield and then calculates the angle between the position vector of the Sun and the given input position vector.
    Used to determine the eclipse angle of the Sun angle of the position.

    Arguments:
        PositionVector (array): Position vector.
        SimulationTime (:obj:`ephem.Date`): The time of the simulation.

    Returns:
        (float): The sun angle [degrees].

    """

    current_time_datetime = ephem.Date(SimulationTime).datetime()
    year = current_time_datetime.year
    month = current_time_datetime.month
    day = current_time_datetime.day
    hour = current_time_datetime.hour
    minute = current_time_datetime.minute
    second = current_time_datetime.second + current_time_datetime.microsecond / 1000000

    current_time_skyfield = timescale_skyfield.utc(
        year, month, day, hour, minute, second
    )

    Sun = database_skyfield["Sun"]
    Earth = database_skyfield["Earth"]

    SunFromEarth = Earth.at(current_time_skyfield).observe(Sun)
    r_SunFromEarth_km = SunFromEarth.position.km

    SunAngle = arccos(
        dot(PositionVector, r_SunFromEarth_km)
        / (norm(r_SunFromEarth_km) * norm(PositionVector))
    )
    SunAngle = SunAngle / pi * 180

    return SunAngle


def FreezeDuration_calculator(pointing_altitude1, pointing_altitude2, TLE2):
    """Function that calculates the angle between two tangential altitudes and then calculates
    the time it takes for orbital position angle of a satellite in a circular orbit to change by the same amount.

    Used to estimate the duration of an attitude freeze for which the pointing altitude reorients itself to the standard pointing altitude.

    Arguments:
        pointing_altitude1 (int): First tangential pointing altitude in m
        pointing_altitude2 (int): Second tangential pointing altitude in m
        TLE2 (str): Second row of a TLE.

    Returns:
        (int): FreezeDuration, Time [s] it takes for the satellites orbital position angle to change 
        by the same amount as the angle between the two tangential pointing altitudes as seen from the satellite.
    """

    U = 398600.4418  # Earth gravitational parameter
    MATS_P = 24 * 3600 / float(TLE2[52:63])  # Orbital Period of MATS [s]
    MATS_p = ((MATS_P / 2 / pi) ** 2 * U) ** (
        1 / 3
    )  # Semi-major axis of MATS assuming circular orbit [km]
    R_mean = 6371  # Mean Earth radius [km]
    pitch1 = arccos((R_mean + pointing_altitude1 / 1000) / (MATS_p)) / pi * 180
    pitch2 = arccos((R_mean + pointing_altitude2 / 1000) / (MATS_p)) / pi * 180
    pitch_angle_difference = abs(pitch1 - pitch2)

    "#The time it takes for the orbital position angle to change by the same amount as"
    "#the angle between the pointing axes"
    FreezeDuration = int(round(MATS_P * (pitch_angle_difference) / 360, 0))

    return FreezeDuration
