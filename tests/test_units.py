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

    Satellite_dict,_ = run_Satellite_Simulator(60*20)

    assert np.linalg.norm(Satellite_dict['Position [km]'] - np.array([5402.42016169, 1231.53689184, 4213.39979245]))<1e-3
    assert np.linalg.norm(Satellite_dict['Velocity [km/s]'] - np.array([4.702034753185209, -0.23305121301179657, -5.926880234636016]))<1e-3
    assert np.linalg.norm(Satellite_dict['OrbitNormal'] - np.array([-0.11989762414733787, 0.9837248329260864, -0.13380075684911716]))<1e-3
    assert np.abs((Satellite_dict['OrbitalPeriod [s]'] -  5781.405357604852))<1e-3
    assert np.abs((Satellite_dict['Latitude [degrees]'] - 37.53148679514688))<1e-3
    assert np.abs((Satellite_dict['Longitude [degrees]'] - 6.724316837111286))<1e-3
    assert np.abs((Satellite_dict['Altitude [km]'] - 590.7634247518984))<1e-3
    assert np.linalg.norm(Satellite_dict['AscendingNode'] - np.array([-0.98372483, -0.11989762,  0.        ]))<1e-3
    assert np.abs((Satellite_dict['ArgOfLat [degrees]'] - 142.35419960240145))<1e-3
    assert np.abs((Satellite_dict['Yaw [degrees]'] - 0.6929335795171141))<1e-3
    assert np.abs((Satellite_dict['Pitch [degrees]'] - 21.84697932755591))<1e-6
    assert np.abs((Satellite_dict['Dec_OpticalAxis [degrees]'] - 29.96898374166494))<1e-3
    assert np.abs((Satellite_dict['RA_OpticalAxis [degrees]'] - 181.73266881417956))<1e-3
    assert np.abs((Satellite_dict['EstimatedLatitude_LP [degrees]'] - 58.810239085649776))<1e-3
    assert np.linalg.norm(Satellite_dict['OpticalAxis'] - np.array([-0.86671138, -0.02621802,  0.49999928]))<1e-6

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