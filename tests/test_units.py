"""
Created on Mon Feb 4 16:56:23 2021

Unit tests for single functions

@author: Ole Martin Christensen
"""

from mats_planningtool.Library import utc_to_onboardTime,Satellite_Simulator
from mats_planningtool.OrbitSimulator.MatsBana import Satellite_Simulator as Satellite_Simulator_Donal
from mats_planningtool.OrbitSimulator.MatsBana import findpitch

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
    
    configFile = get_test_configfile()
    Settings = configFile.Mode120_settings()
    Timeline_settings = configFile.Timeline_settings()
    
    TLE = configFile.getTLE()
    MATS_skyfield = api.EarthSatellite(TLE[0], TLE[1])
    
    timeline_start = ephem.Date(Timeline_settings['start_date'])
    current_time = ephem.Date(
        timeline_start + ephem.second*Settings['freeze_start'])

    Timeline_settings["yaw_correction"] = True
    Timeline_settings["yaw_phase"] = 0

    pointing_altitude = 92.5
    Satellite_dict = Satellite_Simulator(
        MATS_skyfield, current_time, Timeline_settings, pointing_altitude)

    assert np.linalg.norm(Satellite_dict['Position [km]'] - np.array([-2749.37428943,   531.49744563,  6359.4555113 ]))<1e-3
    assert np.linalg.norm(Satellite_dict['Velocity [km/s]'] - np.array([6.90179808, 1.23085971, 2.87630014]))<1e-3
    assert np.linalg.norm(Satellite_dict['OrbitNormal'] - np.array([-0.11962339,  0.98374384, -0.13393392]))<1e-3
    assert (Satellite_dict['OrbitalPeriod [s]'] -  5764.543426286832)<1e-6
    assert (Satellite_dict['Latitude [degrees]'] == 66.2518721740933)<1e-6
    assert (Satellite_dict['Longitude [degrees]'] == 167.98938387874895)<1e-6
    assert (Satellite_dict['Altitude [km]'] == 588.4421145683573)<1e-6
    assert np.linalg.norm(Satellite_dict['AscendingNode'] - np.array([-0.98374384, -0.11962339,  0.        ]))<1e-3
    assert (Satellite_dict['ArgOfLat [degrees]'] == 67.44674503995131)<1e-6
    assert (Satellite_dict['Yaw [degrees]'] == -3.4202478726957044)<1e-6
    assert (Satellite_dict['Pitch [degrees]'] == 111.61338774886056)<1e-6
    #assert np.linalg.norm(Satellite_dict['OpticalAxis'] - np.array([-0.69266389, -0.23351756, -0.6824121 ]))<1e-3
    #assert (Satellite_dict['Dec_OpticalAxis [degrees]'] == -43.032421988221735)<1e-6
    #assert (Satellite_dict['RA_OpticalAxis [degrees]'] == 198.6304891481579)<1e-6
    #assert np.linalg.norm(Satellite_dict['Normal2H_offset' ]- np.array([-0.70002371, -0.01024573,  0.7140461 ]))<1e-3

    Satellite_dict_Donal = Satellite_Simulator_Donal(MATS_skyfield, current_time, Timeline_settings, pointing_altitude)
    Satellite_dict_Donal

if __name__ == "__main__":

    test_utc_to_onboardTime()
    test_findpitch()
    test_Satellite_Simulator()