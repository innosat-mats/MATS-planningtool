import datetime as DT
import matplotlib.pylab as plt
from numpy.linalg import norm
import numpy as  np
import skyfield.api as sfapi
from skyfield.api import wgs84
import skyfield.sgp4lib as sgp4lib
from mats_planningtool.OrbitSimulator import Geoidlib
from scipy.optimize import minimize_scalar
from skyfield.positionlib import ICRF
from skyfield.units import Distance
from skyfield.framelib import itrs

def rotate (unitvec, yaw, pitch, roll, deg=False):
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

def radec2xyz(ra,dec, deg=True):
    if deg:
        ra*=np.pi/180.
        dec*=np.pi/180.
    z=np.sin(dec)
    x=np.cos(ra)*np.cos(dec)
    y=np.sin(ra)*np.cos(dec)
    return [x,y,z]

        
def get_tle_dateDB (d):
    db=sqlite.connect('/Users/donal/mydocs/ODIN/Tle/odintletext.db')
    cur=db.cursor()
    sperday=24.*60*60
    doy=d-DT.datetime(d.year,1,1)
    datekey =((d.year-int(d.year/100)*100)*1000 + doy.days+doy.seconds/sperday)*100
    query="select tle1,tle2 from odintle where datekey between {} and {}"
    r=cur.execute(query.format(datekey,datekey+400)) #four day margin
    tle=r.fetchone()
    cur.close()
    db.close()
    return tle

def loadysb(d):
    ysb=[]
    with open('YBS.edb','r') as fb:
        for line in fb:
            if line[0] !='#' and len(line) >1 : 
                st=ephem.readdb(line)
                st.compute()
                ysb.append(st)
    return ysb
    
def funpitch(pitch,g,th,pos,yaw,rotmatrix):
    #print(pitch*180/np.pi)
    FOV=rotate(np.array([1,0,0]),yaw,pitch,0,deg=False)
    FOV=np.matmul(rotmatrix,FOV)
    tp=findtangent(g,pos,FOV)
    return((tp.fun-th)**2)

def funheight (s,g,pos,FOV):
    newp = pos + s * FOV
    g.position=Distance(m=newp)
    return wgs84.subpoint(g).elevation.m


def findtangent(g,pos,FOV):
    res=minimize_scalar(funheight,args=(g,pos,FOV),bracket=(1e5,3e5))
    return res

def findpitch (th,g,pos,yaw,rotmatrix):
    res=minimize_scalar(funpitch,args=(g,th,pos,yaw,rotmatrix),method="Bounded",bounds=(np.deg2rad(-30),np.deg2rad(-10)))
    return res.x


startdate=DT.datetime(2022,1,10,10)
date=startdate
timestep=DT.timedelta(days=1*0.5)
ts=sfapi.load.timescale()
tle=['1 99991U 21321B   22010.41666667  .00000000  00000-0  49154-3 0    13',
          '2 99991  97.3120  64.9140 0002205 122.9132 235.5287 15.01280112    07']  
sfodin = sgp4lib.EarthSatellite(tle[0],tle[1])

d=date#+offsetfromdate*timestep
timestep=DT.timedelta(seconds=60)
yaw=0
yawoffset=0
#plt.figure()

dateslist=[]
sublats=[]
sublons=[]
platslat=[]
platslon=[]
LTsat=[]
LTtp=[]
for tt in range(1500):
    d+=timestep
    dateslist.append(d.isoformat())
    t=ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
    g=sfodin.at(t)
    period= 2*np.pi/sfodin.model.nm
    ECI_pos=g.position.m
    ECI_vel=g.velocity.m_per_s
    vunit=np.array(ECI_vel)/norm(ECI_vel)
    mrunit=-np.array(ECI_pos)/norm(ECI_pos)
    yunit=np.cross(mrunit,vunit)
    rotmatrix=np.array([vunit,yunit,mrunit]).T 
    sublat_c=g.subpoint().latitude.degrees
    sublon_c=g.subpoint().longitude.degrees
    sublats.append(sublat_c)
    sublons.append(sublon_c)
    LTsat.append((d+DT.timedelta(seconds=sublon_c/15*60*60)).strftime('%H:%M:%S'))
    pitch=findpitch(92000,g, ECI_pos, np.deg2rad(yaw)+yawoffset, rotmatrix)
    yaw=-3.3*np.cos(np.deg2rad(tt*timestep.seconds/period/60*360-np.rad2deg(pitch)-0))
    #yaw =0
    #print(np.rad2deg(pitchdown))
    FOV=rotate(np.array([1,0,0]),np.deg2rad(yaw)+yawoffset,pitch,0,deg=False)
    FOV=np.matmul(rotmatrix,FOV)
    res = findtangent(g,ECI_pos,FOV)
    s=res.x
    newp = ECI_pos + s * FOV
#    pos_s=np.matmul(itrs.rotation_at(t),newp)
    newp=ICRF(Distance(m=newp).au,t=t,center=399)
    platslat.append(wgs84.subpoint(newp).latitude.degrees)
    platslon.append(wgs84.subpoint(newp).longitude.degrees)
    LTtp.append((d+DT.timedelta(seconds=platslon[-1]/15*60*60)).strftime('%H:%M:%S'))

with (open('testfile.txt','w')) as f:
    for i in range(len(dateslist)):
        #print (i) 
        f.write ('{:s} {:f} {:f} {:s} {:f} {:f} {:s}\n'.format(dateslist[i],sublats[i],sublons[i],LTsat[i],platslat[i],platslon[i],LTtp[i]))
f.close()