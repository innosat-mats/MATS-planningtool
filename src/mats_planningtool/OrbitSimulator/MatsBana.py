import datetime as DT
import matplotlib.pylab as plt
from numpy.linalg import norm
import numpy as  np
import skyfield.api as sfapi
from skyfield.api import wgs84
import skyfield.sgp4lib as sgp4lib
#from mats_planningtool.OrbitSimulator import Geoidlib
from scipy.optimize import minimize_scalar
from skyfield.positionlib import ICRF
from skyfield.units import Distance
from skyfield.framelib import itrs
from mats_planningtool.Library import rot_arbit
import ephem


ts = sfapi.load.timescale()

def rotate (unitvec, yaw, pitch, roll, deg=False):
    """Rotates a unitvector applying yaw, pitch and roll (in that order)

    Arguments:
        unitvec (:obj:np.array): the 3 element unit vector to be rotated
        yaw (float): yaw angle to appply
        pitch (float): pitch angle to appply
        roll (float): roll angle to appply
        deg (Boolean): true if yaw,pitch and roll is given in degrees (default False)

    Returns:
        (:obj:np.array): Rotated unit vector
    """
    def Rx (v,th):
        s=np.sin(th)
        c=np.cos(th)
        return np.matmul([[1,0,0],[0,c,-s],[0,s,c]],v)
    def Ry (v,th):
        s=np.sin(th)
        c=np.cos(th)
        return np.matmul([[c,0,s],[0,1,0],[-s,0,c]],v)
    def Rz (v,th):
        s=np.sin(th)
        c=np.cos(th)
        return np.matmul([[c,-s,0],[s,c,0],[0,0,1]],v)
    if deg :
        roll*=(np.pi/180)
        pitch*=(np.pi/180)
        yaw*=(np.pi/180)
    return Rz(Ry(Rx(unitvec,roll),pitch),yaw)

def xyz2radec(vector, deg=False, positivera=False):
    ra = np.arctan2(vector[1],vector[0])
    if positivera : 
        if ra <0 : ra+=2*np.pi
    dec = np.arcsin(vector[2]/np.sqrt(np.dot(vector,vector)))
    if deg :
        ra*=180./np.pi
        dec*=180./np.pi
    return [ra,dec]

# def radec2xyz(ra,dec, deg=True):
#     if deg:
#         ra*=np.pi/180.
#         dec*=np.pi/180.
#     z=np.sin(dec)
#     x=np.cos(ra)*np.cos(dec)
#     y=np.sin(ra)*np.cos(dec)
#     return [x,y,z]

        
# def get_tle_dateDB (d):
#     db=sqlite.connect('/Users/donal/mydocs/ODIN/Tle/odintletext.db')
#     cur=db.cursor()
#     sperday=24.*60*60
#     doy=d-DT.datetime(d.year,1,1)
#     datekey =((d.year-int(d.year/100)*100)*1000 + doy.days+doy.seconds/sperday)*100
#     query="select tle1,tle2 from odintle where datekey between {} and {}"
#     r=cur.execute(query.format(datekey,datekey+400)) #four day margin
#     tle=r.fetchone()
#     cur.close()
#     db.close()
#     return tle

# def loadysb(d):
#     ysb=[]
#     with open('YBS.edb','r') as fb:
#         for line in fb:
#             if line[0] !='#' and len(line) >1 : 
#                 st=ephem.readdb(line)
#                 st.compute()
#                 ysb.append(st)
#     return ysb
    
def funpitch(pitch,current_time,tangent_height,pos,yaw,rotmatrix,look_vector=None):
    if look_vector is None:
        look_vector = np.array([1,0,0])
    FOV=rotate(look_vector,yaw,pitch,0,deg=False)
    FOV=np.matmul(rotmatrix,FOV)
    tangent_point_solution=findtangent(current_time,pos,FOV)
    return ((tangent_point_solution.fun-tangent_height)**2)

def funheight(scaling_factor,current_time,pos,FOV):
    newp = pos + scaling_factor * FOV
    newp=ICRF(Distance(m=newp).au,t=current_time,center=399)
    return wgs84.subpoint(newp).elevation.m 


def findtangent(current_time,pos,FOV):
    #dokument!
    scaling_factor=minimize_scalar(funheight,args=(current_time,pos,FOV),bracket=(1e5,3e5))
    return scaling_factor

def findpitch (tangent_height,current_time,pos,yaw,rotmatrix,look_vector=None):
    if look_vector is None:
        look_vector = np.array([1,0,0])
    pitch=minimize_scalar(funpitch,args=(current_time,tangent_height,pos,yaw,rotmatrix,look_vector),method="Bounded",bounds=(np.deg2rad(-30),np.deg2rad(30)))
    return pitch.x


def Satellite_Simulator(
    Satellite_skyfield,
    SimulationTime,
    Timeline_settings,
    pointing_altitude,
    LogFlag=False,
    Logger=None,
):
    """Simulates a single point in time for a Satellite using Skyfield and also the pointing of the satellite.

    This is Donals implementation

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

    if type(SimulationTime) is DT.datetime:
        current_time_datetime = SimulationTime
    else:
        current_time_datetime = ephem.Date(SimulationTime).datetime()
    
    year = current_time_datetime.year
    month = current_time_datetime.month
    day = current_time_datetime.day
    hour = current_time_datetime.hour
    minute = current_time_datetime.minute
    second = current_time_datetime.second + current_time_datetime.microsecond / 1000000

    current_time_skyfield = ts.utc(
        year, month, day, hour, minute, second
    )

    #Get satellite position and orbital period
    Satellite_geo = Satellite_skyfield.at(current_time_skyfield)
    orbital_period= 2*np.pi/Satellite_skyfield.model.nm 
    ECI_pos=Satellite_geo.position.m
    ECI_vel=Satellite_geo.velocity.m_per_s

    "############# Calculations of orbital and pointing vectors ############"
    "Vector normal to the orbital plane of Satellite"

    "Calculate intersection between the orbital plane and the equator"
    celestial_pole = [0, 0, 1]
    vunit=np.array(ECI_vel)/norm(ECI_vel)
    mrunit=-np.array(ECI_pos)/norm(ECI_pos)
    normal_orbit=np.cross(mrunit,vunit)
    ascending_node = np.cross(celestial_pole, -normal_orbit)

    "Argument of latitude" #FIXME: check sign
    arg_of_lat = (
        np.arccos(
            np.dot(ascending_node, -mrunit) / norm(mrunit) / norm(ascending_node)
        )
        / np.pi
        * 180
    ) #argument of latitude in degrees

    rotmatrix=np.array([vunit,normal_orbit,mrunit]).T 
    sublat_c,sublon_c = wgs84.latlon_of(Satellite_geo)
    sublat_c = sublat_c.degrees
    sublon_c = sublon_c.degrees
    alt_Satellite = wgs84.height_of(Satellite_geo).m
    
    instrument_look_vector = np.array([Timeline_settings["intrument_look_vector"]['x'],Timeline_settings["intrument_look_vector"]['y'],Timeline_settings["intrument_look_vector"]['z']])

    pitch=findpitch(pointing_altitude*1e3,current_time_skyfield, ECI_pos, 0, rotmatrix, instrument_look_vector)
    #calculate yaw offset angle
    yaw_correction = Timeline_settings["yaw_correction"]
    if yaw_correction == True:
        #check consistency here
        yaw_offset_angle=Timeline_settings["yaw_amplitude"]*np.cos(np.deg2rad(arg_of_lat)-pitch-np.deg2rad(Timeline_settings["yaw_phase"])) #check if this is optimal

    elif yaw_correction == False:
        yaw_offset_angle = 0
    
    pitch=findpitch(pointing_altitude*1e3,current_time_skyfield, ECI_pos, np.deg2rad(yaw_offset_angle), rotmatrix, instrument_look_vector)

    #Get the center of the field of view
    FOV_satellite=rotate(instrument_look_vector,np.deg2rad(yaw_offset_angle),pitch,0,deg=False)
    FOV_sky=np.matmul(rotmatrix,FOV_satellite)
    [FOV_ra,FOV_dec]=xyz2radec(FOV_sky,deg=True,positivera=True)
    
    #Get tangent point
    scaling_factor = findtangent(current_time_skyfield,ECI_pos,FOV_sky).x #find distance to the nearest point to the geoid (m)
    tangent_point = ECI_pos + scaling_factor * FOV_sky #position in ECI units of the tangent point
    tangent_point=ICRF(Distance(m=tangent_point).au,t=current_time_skyfield,center=399)
    tangent_point_lat = (wgs84.subpoint(tangent_point).latitude.degrees)
    tangent_point_lon = (wgs84.subpoint(tangent_point).longitude.degrees)
      
    "Rotate 'vector to Satellite', to represent vector normal to satellite H-offset "
    #FIXME: Normal orbit sign
    rot_mat = rot_arbit(pitch, normal_orbit)
    r_H_offset_normal = rot_mat @ ECI_pos
    r_H_offset_normal = r_H_offset_normal / norm(r_H_offset_normal)

    "If pointing direction has a Yaw defined, Rotate yaw of normal to pointing direction H-offset plane, meaning to rotate around the vector to Satellite"
    rot_mat = rot_arbit(np.deg2rad(yaw_offset_angle), mrunit)
    r_H_offset_normal = rot_mat @ r_H_offset_normal
    r_H_offset_normal = r_H_offset_normal / norm(r_H_offset_normal)

    "Rotate negative orbital plane normal to make it into a normal to the V-offset plane"
    r_V_offset_normal = rot_mat @ -normal_orbit
    r_V_offset_normal = r_V_offset_normal / norm(r_V_offset_normal)

    if LogFlag == True and Logger != None:
        Logger.debug("")

        Logger.debug("SimulationTime time: " + str(SimulationTime))
        Logger.debug("Orbital Period in s: " + str(orbital_period*60))
        Logger.debug("Vector to Satellite [km]: " + str(ECI_pos*1e3))
        Logger.debug("Latitude in degrees: " + str(sublat_c))
        Logger.debug("Longitude in degrees: " + str(sublon_c))
        Logger.debug("Altitude in km: " + str(alt_Satellite*1e3))

        Logger.debug("Pitch [degrees]: " + str(np.rad2deg(pitch)))
        Logger.debug("Yaw [degrees]: " + str(yaw_offset_angle))
        Logger.debug("ArgOfLat [degrees]: " + str(arg_of_lat))
        Logger.debug("Latitude of LP: " + str(tangent_point_lat))
        Logger.debug("Longitude of LP: " + str(tangent_point_lon))

        Logger.debug("Optical Axis: " + str(FOV_sky))
        Logger.debug(
            "Orthogonal direction to H-offset plane: " + str(r_H_offset_normal)
        )
        Logger.debug(
            "Orthogonal direction to V-offset plane: " + str(r_V_offset_normal)
        )
        Logger.debug("Orthogonal direction to the orbital plane: " + str(normal_orbit))

    Satellite_dict = {
        "Position [km]": ECI_pos*1e-3,
        "Velocity [km/s]": ECI_vel*1e-3,
        "OrbitNormal": -normal_orbit,
        "OrbitalPeriod [s]": orbital_period*60,
        "Latitude [degrees]": sublat_c,
        "Longitude [degrees]": sublon_c,
        "Altitude [km]": alt_Satellite*1e-3,
        "AscendingNode": ascending_node,
        "ArgOfLat [degrees]": arg_of_lat,
        "Yaw [degrees]": yaw_offset_angle,
        "Pitch [degrees]": np.rad2deg(pitch),
        "OpticalAxis": FOV_sky,
        "Dec_OpticalAxis [degrees]": FOV_dec,
        "RA_OpticalAxis [degrees]": FOV_ra,
        "Normal2H_offset": r_H_offset_normal,
        "Normal2V_offset": -r_V_offset_normal,
        "EstimatedLatitude_LP [degrees]": tangent_point_lat,
        "EstimatedLongitude_LP [degrees]": tangent_point_lon,
    }

    return Satellite_dict

# startdate=DT.datetime(2022,1,10,10)
# date=startdate
# timestep=DT.timedelta(days=1*0.5)
# ts=sfapi.load.timescale()
# tle=['1 99991U 21321B   22010.41666667  .00000000  00000-0  49154-3 0    13',
#           '2 99991  97.3120  64.9140 0002205 122.9132 235.5287 15.01280112    07']  
# sfodin = sgp4lib.EarthSatellite(tle[0],tle[1])

# d=date#+offsetfromdate*timestep
# timestep=DT.timedelta(seconds=60)
# yaw=0
# yawoffset=0
# #plt.figure()

# dateslist=[]
# sublats=[]
# sublons=[]
# platslat=[]
# platslon=[]
# LTsat=[]
# LTtp=[]
# for tt in range(1500):
#     d+=timestep
#     dateslist.append(d.isoformat())
#     t=ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
#     g=sfodin.at(t)
#     period= 2*np.pi/sfodin.model.nm
#     ECI_pos=g.position.m
#     ECI_vel=g.velocity.m_per_s
#     vunit=np.array(ECI_vel)/norm(ECI_vel)
#     mrunit=-np.array(ECI_pos)/norm(ECI_pos)
#     yunit=np.cross(mrunit,vunit)
#     rotmatrix=np.array([vunit,yunit,mrunit]).T 
#     sublat_c=g.subpoint().latitude.degrees
#     sublon_c=g.subpoint().longitude.degrees
#     sublats.append(sublat_c)
#     sublons.append(sublon_c)
#     LTsat.append((d+DT.timedelta(seconds=sublon_c/15*60*60)).strftime('%H:%M:%S'))
#     pitch=findpitch(92000,g, ECI_pos, np.deg2rad(yaw)+yawoffset, rotmatrix)
#     yaw=-3.3*np.cos(np.deg2rad(tt*timestep.seconds/period/60*360-np.rad2deg(pitch)-0))
#     #yaw =0
#     #print(np.rad2deg(pitchdown))
#     FOV=rotate(np.array([1,0,0]),np.deg2rad(yaw)+yawoffset,pitch,0,deg=False)
#     FOV=np.matmul(rotmatrix,FOV)
#     res = findtangent(g,ECI_pos,FOV)
#     s=res.x
#     newp = ECI_pos + s * FOV
# #    pos_s=np.matmul(itrs.rotation_at(t),newp)
#     newp=ICRF(Distance(m=newp).au,t=t,center=399)
#     platslat.append(wgs84.subpoint(newp).latitude.degrees)
#     platslon.append(wgs84.subpoint(newp).longitude.degrees)
#     LTtp.append((d+DT.timedelta(seconds=platslon[-1]/15*60*60)).strftime('%H:%M:%S'))

# with (open('testfile.txt','w')) as f:
#     for i in range(len(dateslist)):
#         #print (i) 
#         f.write ('{:s} {:f} {:f} {:s} {:f} {:f} {:s}\n'.format(dateslist[i],sublats[i],sublons[i],LTsat[i],platslat[i],platslon[i],LTtp[i]))
# f.close()