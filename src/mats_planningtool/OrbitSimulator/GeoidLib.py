#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Geoidlib.py
#  
#  Copyright 2018 Donal Murtagh <donal.murtagh@chalmers.se>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
#WGS84
from numpy import cos, sin, tan, pi,arcsin, arctan, arctan2,sqrt, abs
a=6378137.0
#f=298.257223563
#e=1/f
f=1/298.257223563
#f=1e-6
e=sqrt(f*(2-f))  # fixat per lantmeteriet sida 2021-1-07 
def Rcurv (phi) : 
    Rn=a/sqrt(1-e*e*(sin(phi)**2))
    return Rn
def geodetic_lat2geocentric_lat (phi, h=0.0,deg=True) :
    if deg :
        phi*=pi/180
    Rn=Rcurv(phi)
    phi_c=arctan((1-e**2*Rn/(Rn+h))*tan(phi))
    if deg :
        phi_c*=180/pi
    return phi_c
    
def geocentric_lat2geodetic_lat (phi_c, h=0.0, deg=True):
    if deg :
        phi_c*=pi/180
    Rn=Rcurv(phi_c)
    phi=arctan(tan(phi_c)/(1-e*e*Rn/(Rn+h)))
    #recompute Rn using phi
    Rn=Rcurv(phi)
    phi=arctan(tan(phi_c)/(1-e*e*Rn/(Rn+h)))
    if deg :
        phi*=180/pi
    return phi
    
def geodetic2xyzECEF (phi,lamda,h=0.0,deg=True):
    if deg :
        phi*=pi/180
        lamda*=pi/180
    Rn=Rcurv(phi)
    x=(Rn+h)*cos(phi)*cos(lamda)
    y=(Rn+h)*cos(phi)*sin(lamda)
    z=((1-e*e)*Rn+h)*sin (phi)
    return [x,y,z]
    
def xyxECEF2geodetic (x,y,z, deg=False):
    lamda=arctan2(y,x)
    r=sqrt(x*x+y*y+z*z)
    p=sqrt(x*x+y*y)
    phi_c=arcsin(z/r)
    phi_iter=phi_c
    phi=0.0
    Rn=Rcurv(phi_iter)
    counter = 0
    while abs(phi-phi_iter)>0.00000000001:
        phi=phi_iter
        h=p/cos(phi_iter)-Rn
        Rn=Rcurv(phi_iter)
        phi_iter = arctan(z/p/(1-e*e*Rn/(Rn+h)))
        counter+=1
    phi=phi_iter    
    h=p/cos(phi)-Rn
    if deg :
        phi*=180/pi
        lamda*=180/pi
    return [phi,lamda,h]    
        
def earth_radius (phi,deg=False):
    if deg :
        phi/=180/pi
    return sqrt(1./(cos(phi)**2/a**2+sin(phi)**2/(a*(1-f))**2));
        
    
    