import ephem 
import datetime as DT
import sqlite3 as sqlite
import matplotlib.pylab as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path
from numpy.linalg import norm
import matplotlib.animation as animation
import numpy as  np
import skyfield.sgp4lib as sgp4lib
import skyfield.api as sfapi
from skyfield.api import wgs84
from skyfield.units import Distance
from mats_planningtool.OrbitSimulator import Geoidlib
from scipy.optimize import minimize_scalar
from skyfield.framelib import itrs

def rotate (unitvec, roll, pitch, yaw, deg=False):
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

class Matssky(object):
    def __init__(self,ax,startdate=DT.datetime(2022,1,10,10,0,0)):
        self.ax=ax
        self.date=startdate
        self.timestep=DT.timedelta(seconds=1*5)
        self.ts=sfapi.load.timescale()
        self.tle=['1 99991U 21321B   22010.41666667  .00000000  00000-0  49154-3 0    13',
                  '2 99991  97.3120  64.9140 0002205 122.9132 235.5287 15.01280112    07']
        self.sfodin = sgp4lib.EarthSatellite(self.tle[0],self.tle[1])
        self.ysb=loadysb(startdate)
        self.planets = sfapi.load('de421.bsp')
        self.st_vec=[]
        self.FOV_ra=0
        self.FOV_dec=0        
        st_x=[]
        st_y=[]
        st_area=[]
        maxmag=10**(-0.4*-1)
        minmag=6.
        rotmatrix=self.rot_matrix(self.sfodin,self.date)
        #self.ax.set_xlim([-0.05,+0.05])
        #self.ax.set_ylim([-0.008,+0.008])
        self.ax.set_xlim([-0.1,+0.1])
        self.ax.set_ylim([-0.016,+0.016])
        ax.invert_yaxis()  #Now defined +Z as nadir
        for st in self.ysb: 
            if st.mag < minmag:
                self.st_vec.append(radec2xyz(st.ra,st.dec,deg=False))
                #transform to instrument coordinates
                inst_xyz=np.matmul(rotmatrix,self.st_vec[-1])
                [xang,yang]=xyz2radec(inst_xyz,positivera=True)
                st_x.append(xang)
                st_y.append(yang)
                st_area.append(100*((10**(-0.4*st.mag))/maxmag))
        # Add the moon
        self.moon=self.planets['Moon']
        self.earth=self.planets['Earth']
        d=self.date
        t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
        print (t)
        moonpos=self.earth.at(t).observe(self.moon).radec()
        print (moonpos)
        # Treat as extra star  but should realy be in the update part since it moves fast
        #could be done there for the correct time but the vector would need to be recalculated
        moon_ra = moonpos[0].radians
        moon_dec = moonpos[1].radians
        print ("Moon RA = {}, Dec= {}".format(moon_ra*180/np.pi,moon_dec*180/np.pi))
        self.st_vec.append(radec2xyz(moon_ra,moon_dec,deg=False))
        #transform to instrument coordinates
        inst_xyz=np.matmul(rotmatrix,self.st_vec[-1])
        [xang,yang]=xyz2radec(inst_xyz,positivera=True)
        st_x.append(xang)
        st_y.append(yang)
        st_area.append(2000) #should be about half the vertical FOv
        self.scatter = self.ax.scatter(st_x,st_y,s=st_area,color='w')
        self.title=ax.text(0.5,0.9,"Datetime = {}, FOV_ra = {:+5.2f}, FOV_dec = {:+5.2f}".format(self.date.isoformat(),self.FOV_ra,self.FOV_dec)
                           ,transform=ax.transAxes, ha="center")

        #title = ax.text(0.5,0.85, "", bbox={'facecolor':'w', 'alpha':0.5, 'pad':5},
                #transform=ax.transAxes, ha="center")
        
    def update (self,frame):
        self.date+= self.timestep
        d=self.date
        t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
        moonpos=self.earth.at(t).observe(self.moon).radec()
        moon_ra = moonpos[0].radians
        moon_dec = moonpos[1].radians
        #print ("Moon RA = {}, Dec= {}".format(moon_ra*180/np.pi,moon_dec*180/np.pi))
        self.st_vec[-1]=(radec2xyz(moon_ra,moon_dec,deg=False))
        rotmatrix=self.rot_matrix(self.sfodin,self.date)
        st_x=[]
        st_y=[]
        for i,st_vec in enumerate(self.st_vec):
            inst_xyz=np.matmul(rotmatrix,st_vec)
            [xang,yang]=xyz2radec(inst_xyz)
            st_x.append(xang)
            st_y.append(yang)
        self.scatter.set_offsets(list(zip(st_x,st_y)))
        self.title.set_text("Datetime = {}, FOV_ra = {:+5.2f}, FOV_dec = {:+5.2f}".format(self.date.isoformat(),self.FOV_ra,self.FOV_dec))
        #self.ax.figure.canvas.draw()
        return self.ax,
        
    def rot_matrix(self,sfodin, d):
        t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
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
        #yaw=-3.3*np.cos(np.deg2rad(tt*timestep.seconds/period/60*360-np.rad2deg(pitch)-0))
        #yawing not implemented  Needs fraction of orbit
        yaw =0
        yawoffset=0
        pitch=findpitch(92000,g, ECI_pos, np.deg2rad(yaw)+yawoffset, rotmatrix)
        FOV=rotate(np.array([1,0,0]),np.deg2rad(yaw)+yawoffset,pitch,0,deg=False)
        #FOV=np.matmul(rotmatrix,FOV)
        Rotmatrix=np.array([vunit,yunit,mrunit]).T 
        v_dash=np.matmul(Rotmatrix,FOV)
        [self.FOV_ra,self.FOV_dec]=xyz2radec(v_dash,deg=True)
        r_dash=np.cross(v_dash,yunit)
        rotmatrix=np.linalg.inv(np.array([v_dash,yunit,r_dash]).T) 
        #raise NotImplementedError()
        return rotmatrix



plt.close('all')
plt.style.use('dark_background')
plt.rcParams['figure.figsize'] = [12, 2]
fig,ax=plt.subplots()
matssky=Matssky(ax,startdate=DT.datetime(2022,1,10,10,0))  #see the moon
#matsFOV=MatsFOV(ax,startdate=DT.datetime(2009,9,22,8,14,40))  #see Sirius"
plt.tight_layout()

ani = animation.FuncAnimation(fig, matssky.update, interval=50,
                             blit=True)


plt.show()

class Skymap(object):
    def __init__(self,ax,startdate=DT.datetime(2022,1,10,10)):
        self.ax=ax
        self.date=startdate
        self.timestep=DT.timedelta(days=1*0.5)
        self.ts=sfapi.load.timescale()
        self.tle=['1 99991U 21321B   22010.41666667  .00000000  00000-0  49154-3 0    13',
                  '2 99991  97.3120  64.9140 0002205 122.9132 235.5287 15.01280112    07']  
        self.sfodin = sgp4lib.EarthSatellite(self.tle[0],self.tle[1])
        self.ysb=loadysb(startdate)
        self.planets = sfapi.load('de421.bsp')
        self.st_vec=[]
        self.FOV_ra=0
        self.FOV_dec=0        
        st_x=[]
        st_y=[]
        st_area=[]
        maxmag=10**(-0.4*-1)
        minmag=2.       
        for st in self.ysb: 
            if st.mag < minmag:
                st_x.append(st.ra)
                st_y.append(st.dec)
                st_area.append(100*((10**(-0.4*st.mag))/maxmag))
        # Add the moon
        self.moon=self.planets['Moon']
        self.earth=self.planets['Earth']
        self.sun=self.planets['Sun']
        d=self.date
        t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
        self.scatter = self.ax.scatter(st_x,st_y,s=st_area,color='w')
  
        fov_ras,fov_decs,sunpos,moonpos=self.getfovs(self.sfodin,self.date)
        self.title=ax.text(0.5,0.9,"Datetime = {}".format(self.date.isoformat())
                           ,transform=ax.transAxes, ha="center")            
        FOV_ras,FOV_decs,sunpos,moonpos = self.getfovs(self.sfodin,self.date) 
        self.line=Line2D(FOV_ras,FOV_decs,marker='.', color='g',linestyle='None')
        ax.add_line(self.line)
        moon_ra = moonpos[0].radians
        moon_dec = moonpos[1].radians
        sun_ra=sunpos[0].radians
        sun_dec=sunpos[1].radians    
        self.moonpatch=plt.scatter(moon_ra,moon_dec,s=300.,color='w')
        self.sunpatch=plt.scatter(sun_ra,sun_dec,s=1000.,color='w') 
        #title = ax.text(0.5,0.85, "", bbox={'facecolor':'w', 'alpha':0.5, 'pad':5},
                #transform=ax.transAxes, ha="center")
        
    def update (self,frame):
        self.date+= self.timestep
        FOV_ras,FOV_decs,sunpos,moonpos = self.getfovs(self.sfodin,self.date)
        self.line.set_ydata(FOV_decs)
        self.line.set_xdata(FOV_ras)
        self.title.set_text("Datetime = {}".format(self.date.isoformat()))
        moon_ra = moonpos[0].radians
        moon_dec = moonpos[1].radians
        sun_ra=sunpos[0].radians
        sun_dec=sunpos[1].radians
        #verts,codes=makemoonpath(moon_ra-sun_ra, moon_dec-sun_dec)
        #moonpath=Path(np.array(verts),np.array(codes, dtype=np.uint8))
        #self.moonpatch.set_paths([moonpath])
        self.moonpatch.set_offsets((moon_ra,moon_dec))
        self.sunpatch.set_offsets((sun_ra,sun_dec))
        return self.ax,
        
    def getfovs(self,sfodin, d0):
        delta=DT.timedelta(seconds=1*60)
        d=d0
        t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
        moonpos=self.earth.at(t).observe(self.moon).radec()
        sunpos=self.earth.at(t).observe(self.sun).radec() 
        FOV_ras=[]
        FOV_decs=[]
        for i in range(100):
            d=d0+i*delta
            t=self.ts.utc(d.year,d.month,d.day,d.hour,d.minute,d.second)
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
            #yaw=-3.3*np.cos(np.deg2rad(tt*timestep.seconds/period/60*360-np.rad2deg(pitch)-0))
            yaw =0
            yawoffset=0
            pitch=findpitch(92000,g, ECI_pos, np.deg2rad(yaw)+yawoffset, rotmatrix)
            FOV=rotate(np.array([1,0,0]),np.deg2rad(yaw)+yawoffset,pitch,0,deg=False)
            FOV=np.matmul(rotmatrix,FOV)
            [FOV_ra,FOV_dec]=xyz2radec(FOV,positivera=True)
            FOV_ras.append(FOV_ra)
            FOV_decs.append(FOV_dec)
            
            #raise NotImplementedError()
        return FOV_ras,FOV_decs, sunpos,moonpos

plt.rcParams['figure.figsize'] = [12, 8]
plt.close('all')
plt.style.use('dark_background')
fig,ax=plt.subplots()
skymap=Skymap(ax,startdate=DT.datetime(2022,1,10,10))  
plt.tight_layout()

ani = animation.FuncAnimation(fig, skymap.update, interval=50,
                             blit=True)

