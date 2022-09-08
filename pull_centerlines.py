#-*- coding: utf-8 -*-

"""
Created on Wed Sep 7 14:41:24 2022

@author: Yoram

spun off OGIVE_finder, just to get the millan thicknesses and bed slope along the various profiles 


This script pulls the elevation and slope profiles of ArcticDEM, annd the ice thicknesses from Millan et al 2021 along a centerlines from 
Zhang et al (2022) - A new global dataset of mountain glacier centerlines and lengths (https://doi.org/10.5194/essd-14-3889-2022); 
available here: https://doi.org/10.11922/sciencedb.01643 

This dataset needs to be availaible in the working directory.
Arcitc DEM is pulled using Google earth engine tools.
Millan is pulled from earth engine, but should be present as an personal asset in earth engine... 

"""


# import modules and functions
import numpy as np 
from functools import reduce
import ee as ee
import geopandas as gp 
import geemap 
import os
from os.path import exists

from math import ceil

from numpy import genfromtxt


import matplotlib.pyplot as plt


# OGIVE_ functions contains the gee script to get at points 
from centerline_functions import line_to_points, buffer_points

# for GEE
ee.Initialize()


#%% select a glacier 
RGIglacier = ee.FeatureCollection('GLIMS/current').filter('glac_name=="Bering Glacier"')

# glacier name for file out
glacier_name = 'Bering'

#%% read in data 
print('Loading data...')

#%% load ArcticDEM, and convert to slope (in degrees)
elev = ee.Image("UMN/PGC/ArcticDEM/V3/2m_mosaic") 
slope = ee.Terrain.slope(elev)

#%% load in ice thickness from the GEE asset library 
# this could be improved to make the script more flexible...)
RGI = ee.Image('users/yoramterleth/THICKNESS_RGI')

#%% calculate the bed elevation and slope  
bed_elev = elev.subtract(RGI) 
bed_slope = ee.Terrain.slope(bed_elev)


#%% centerlines from Zhang 2022

#read in the shapefile 
centerlines = gp.read_file('C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/python_gee/centerlines/01_rgi60_Alaska_final_lines.shp')


# set the CRS to coincide with the ARctic dem one
centerlines = centerlines.to_crs(crs='EPSG:4269')

#%% select the centerlines to a specific glacier 

# get the outline from earth engine 
GLIMS = RGIglacier # ee.FeatureCollection('GLIMS/current').filter('glac_name=="Haenke Glacier"'); 

# convert this to a shapefile that can be used with geopandas
geemap.ee_to_shp(GLIMS,'C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/python_gee/centerlines/'+glacier_name+'_outline.shp' )

GLIMS_shp = gp.read_file('C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/python_gee/centerlines/'+glacier_name+'_outline.shp' )
GLIMS_shp = GLIMS_shp.to_crs(crs='EPSG:4269')

cl = gp.clip(centerlines, GLIMS_shp)

#%% plot the glacier outline and the centerlines we are pulling
ax = GLIMS_shp.plot()
ax = cl.plot()

#%% beginning of for loop ##

# intialize counters
outer_loop_nb = 0
inner_loop_nb = 0 

for i in cl.geometry.index:
    
    print('Working on multilinestring nb '+str(outer_loop_nb)+'...')   
    
    # get the multilinestring
    cl_set = cl.geometry[i]
    
    # sometimes xl_set is already a single string, in which case asking for a length throws an error... 
    # here we make a list depending on this
    try:
        string_id = range(len(cl_set))
    except: 
        string_id = [0]
    
    
    for j in string_id:
        
        print('Working on linestring nb '+str(inner_loop_nb)+'...')
        # get the individual strings
        
        # again, allow for cl_set to be asingle string already
        try: 
            centerline = cl_set[j]
        except: 
            centerline = cl_set
        
            
        #%% get the strings from the centerlines and convert to gee features 
        print('Converting centerlines to earth engine features...')
         
        x,y = centerline.coords.xy 
        cords = np.dstack((x,y)).tolist()
        double_list = reduce(lambda x,y: x+y, cords)
        ee_centerline = ee.Geometry.LineString(double_list)
        
                        
        #%% transorm the gee linestring to points 
        print('Getting points from centerlines...')
        
        # nb of points we want to pull; length depedent:
        # here we set 100 m intervals between points        
        point_nb = ceil(ee_centerline.length().getInfo() / 500) # 100 
        
        
        # length of the ee string
        length = ee_centerline.length()
        
        # step interval at which to get points
        step = ee_centerline.length().divide(point_nb)
        
        # distances at which each point needs to appear
        distances = ee.List.sequence(0,length, step)
        
        # cut up the linestring into pieces of that length 
        lines= ee.Geometry(ee_centerline).cutLines(distances).geometries()  
        
        # clear the pointz variable just in case 
        pointz = []   
        
        # apply the line to points function  
        pointz = line_to_points(ee.Geometry(ee_centerline), point_nb)
        
         
        # make a buffered points collection too: we will use this pulled data to detrend our profile later
        pts_buffered = pointz.map(buffer_points)
        
        # merge the points from each inner loop 
        if inner_loop_nb == 0: 
            pts_inner_loop = pts_buffered
        else: 
            pts_inner_loop = pts_inner_loop.merge(pts_buffered)
        
        # add to counter
        inner_loop_nb += 1 
        
        print('Added points to inner loop points.')
    
    # merge the points from each outer loop
    if outer_loop_nb == 0:
        pts_outer_loop = pts_inner_loop
    else:
        pts_outer_loop = pts_outer_loop.merge(pts_inner_loop)
        
    # add to counter 
    outer_loop_nb += 1
    print('Added points to outer loop points.')
        
#%% pull the actual data 

# concatenate the variables of interest from the dem as bands of an image, and add a dummy system start time 
topo = ee.Image.cat(elev, slope, bed_elev, bed_slope).set('system:time_start', ee.Date('2000-01-01').millis())


# set up the csv step needed for geemap.zonal_statistics()... this is clunky but it works remarkably well

# give the filenames
outdir = 'C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/csv_python/'
bufferfile = outdir + glacier_name +'_stats.csv'

# remove the file if it already exists   
if exists(bufferfile):
    os.remove(bufferfile)

# run zonal statistics functions, and save profiles to csv

print('Running zonal stats...')

geemap.zonal_statistics(topo,pts_outer_loop,bufferfile,statistics_type='MEAN',scale=2)

print('Saved point data to '+ bufferfile+ '. All done.')