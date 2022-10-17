"""
Created on Mon Feb 4 16:56:23 2021

Unit tests for single functions

@author: Ole Martin Christensen
"""

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

def test_utc_to_onboardTime():
    d = ephem.Date('2022/11/30 16:23:45.12')
    output = utc_to_onboardTime(d)

    assert output == 1353860643.1

def test_findpitch():
    tle=['1 99991U 21321B   22010.41666667  .00000000  00000-0  49154-3 0    13',
          '2 99991  97.3120  64.9140 0002205 122.9132 235.5287 15.01280112    07']
    sfodin = sgp4lib.EarthSatellite(tle[0],tle[1])
    
    t=ts.utc(2022,1,11,11,0,0)
    g=sfodin.at(t)
    ECI_pos=g.position.m
    ECI_vel=g.velocity.m_per_s
    vunit=np.array(ECI_vel)/norm(ECI_vel)
    mrunit=-np.array(ECI_pos)/norm(ECI_pos)
    yunit=np.cross(mrunit,vunit)
    ECI_pos = np.array([-2612904.44464064, -4229765.15126377, -4853795.12503612])
    rotmatrix=np.array([vunit,yunit,mrunit]).T 
    pitch=findpitch(92000,t, ECI_pos, 0.01821138006266897, rotmatrix)
    assert (pitch-0.38048642231615376)<1e-9

def test_Satellite_Simulator():

    Satellite_dict,Satellite_dict_old = run_Satellite_Simulator(60*20)

    assert np.linalg.norm(Satellite_dict['Position [km]'] - np.array([-2749.37428943,   531.49744563,  6359.4555113 ]))<1e-3
    assert np.linalg.norm(Satellite_dict['Velocity [km/s]'] - np.array([6.90179808, 1.23085971, 2.87630014]))<1e-3
    assert np.linalg.norm(Satellite_dict['OrbitNormal'] - np.array([-0.11962339,  0.98374384, -0.13393392]))<1e-3
    assert np.abs((Satellite_dict['OrbitalPeriod [s]'] -  5781.405442710422))<1e-3
    assert np.abs((Satellite_dict['Latitude [degrees]'] - 66.2518721740933))<1e-3
    assert np.abs((Satellite_dict['Longitude [degrees]'] - 167.98515928719192))<1e-3
    assert np.abs((Satellite_dict['Altitude [km]'] - 588.4421145683573))<1e-3
    assert np.linalg.norm(Satellite_dict['AscendingNode'] - np.array([-0.98374384, -0.11962339,  0.        ]))<1e-3
    assert np.abs((Satellite_dict['ArgOfLat [degrees]'] - 67.44587321842594))<1e-3
    assert np.abs((Satellite_dict['Yaw [degrees]'] - -3.421236658595461))<1e-3
    assert np.abs((Satellite_dict['Pitch [degrees]'] - 21.648870551653236))<1e-6
    assert np.abs((Satellite_dict['Dec_OpticalAxis [degrees]'] - -43.04102760757912))<1e-3
    assert np.abs((Satellite_dict['RA_OpticalAxis [degrees]'] - 198.6252475912853))<1e-3
    assert np.abs((Satellite_dict['EstimatedLatitude_LP [degrees]'] - 45.45170931631043))<1e-3
    assert np.linalg.norm(Satellite_dict['Normal2H_offset'] - np.array([-0.70003147, -0.01020216,  0.71403911]))
    assert np.linalg.norm(Satellite_dict['Normal2V_offset'] - np.array([ 0.17362442, -0.97232546,  0.15632581]))
    assert np.linalg.norm(Satellite_dict['OpticalAxis'] - np.array([-0.69268355, -0.23340761, -0.68242977]))<1e-6

def run_Satellite_Simulator(extratime = 0):
    '''
    This test runs an old MATS orbit (looking backwards) to keep consistency with
    Davids simulator. Only difference with new simulator is the definition of Pitch
    and that the optical coordinate is returned differently.. 
    '''
    
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

    Satellite_dict_old = Satellite_Simulator_old(
        MATS_skyfield, current_time, Timeline_settings, pointing_altitude)

    return Satellite_dict,Satellite_dict_old   


if __name__ == "__main__":

    #test_utc_to_onboardTime()
    #test_findpitch()
    test_Satellite_Simulator()