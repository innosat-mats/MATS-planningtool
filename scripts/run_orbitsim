from mats_planningtool.Library import utc_to_onboardTime
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator
from mats_planningtool.OrbitSimulator.MatsBana import findpitch
from mats_planningtool.Library import Satellite_Simulator as Satellite_Simulator_old

import ephem
from skyfield import api
import skyfield.sgp4lib as sgp4lib
from mats_planningtool import configFile as configFile
import numpy as np
from numpy.linalg import norm


ts = api.load.timescale()

def get_test_configfile():

    configfile = "./test_data/config_file_test.json"

    configfile_test = configFile.configFile(
        configfile,
        "2020/9/25 16:45:00",
        TLE1="1 54321U 19100G   20172.75043981 0.00000000  00000-0  75180-4 0  0014",
        TLE2="2 54321  97.7044   6.9210 0014595 313.2372  91.8750 14.93194142000010",
    )

    configfile_test.output_dir = 'test_data_output'

    return configfile_test


extratime = 20*60

configFile = get_test_configfile()
Settings = configFile.Mode120_settings()
Timeline_settings = configFile.Timeline_settings()

TLE = configFile.getTLE()
MATS_skyfield = api.EarthSatellite(TLE[0], TLE[1])

timeline_start = ephem.Date(Timeline_settings['start_date'])
current_time = ephem.Date(
    timeline_start + ephem.second*Settings['freeze_start'] + ephem.second*extratime)

Timeline_settings["yaw_correction"] = True
Timeline_settings["intrument_look_vector"]['x'] = -1

pointing_altitude = 92.5
Satellite_dict = Satellite_Simulator(
    MATS_skyfield, current_time, Timeline_settings, pointing_altitude)