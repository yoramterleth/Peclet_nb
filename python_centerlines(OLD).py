# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 10:13:08 2022

@author: Yoram

this script aims at pulling values from rasters along the centerlines of glaciers. 
utilizing the google earth engine functionalities when possible
"""



import numpy as np 
from functools import reduce
import ee as ee
import geopandas as gp 
import pandas as pd

import matplotlib.pyplot as plt

from list_all_assets import get_asset_list

#from ee_converter import feature2ee
from ee_converter import feature2ee

ee.Initialize()



#%% read in data 

# read in the shapefile 
centerlines = gp.read_file('C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/OGIVES/findr/centerlines/01_rgi60_Alaska_final_lines.shp')



# select only the really long glaciers for now 
centerlines = centerlines[centerlines.MaxL>20000]

centerlines = centerlines.to_crs(crs='EPSG:4269')

#%% convert the centerlines for use in gee 
CC = feature2ee(centerlines)

# get the spatial extent of our shapefile 
AOI = ee.Geometry.Polygon(centerlines.total_bounds) 

centerline_IDs = centerlines.GLIMS_ID[:]

centerline_IDs.index


#%% load the corresponding RGI outline 
GLIMS = ee.FeatureCollection('GLIMS/current').filter('glac_name=="centerlines.GLIMS_ID[12]')

#%% load and clip the corresponding part of ArcticDEM
elev = ee.Image("UMN/PGC/ArcticDEM/V3/2m_mosaic").clip(GLIMS).select('elevation')
slope = ee.Terrain.slope(elev)

#%% get the strings from the centerlines and convert to gee features 
centerline = centerlines.geometry[12][0]

x,y = centerline.coords.xy # .exterior.coords.xy
cords = np.dstack((x,y)).tolist()
double_list = reduce(lambda x,y: x+y, cords)
ee_centerline = ee.Geometry.LineString(double_list)

#%% transorm the gee linestring to points 

# nb of points we want to pull
point_nb = 1000 

# length of the ee string
length = ee_centerline.length()

# step interval at which to get points
step = ee_centerline.length().divide(point_nb)

# distances at which each point needs to appear
distances = ee.List.sequence(0,length, step)

# cut up the linestring into pieces of that length 
lines= ee.Geometry(ee_centerline).cutLines(distances).geometries()  

def makePointFeature(coord, offset):
    pt = ee.Algorithms.GeometryConstructors.Point(coord);
    coords = pt.coordinates(); # set coords as feature property
    
    newpt = ee.Feature(pt).set({'offset':offset,
                                'lat':ee.List(coords).get(0),
                                'lon':ee.List(coords).get(1)})
    return newpt


def point_line(s):
    line = ee.List(s).get(0)
    offset = ee.List(s).get(1)
    # make first point 
    point = makePointFeature(ee.Geometry(line).coordinates().get(0), offset)
    return point
    
def line_to_points(linestring, count):
    length = linestring.length()
    step = linestring.length().divide(count)
    distances = ee.List.sequence(0,length,step)
    
    lines = ee.Geometry(linestring).cutLines(distances).geometries()
    
    points = lines.zip(distances).map(point_line)
    
    #points = points.add(makePointFeature(linestring.coordinates().get(-1),length))
    
    pts = ee.FeatureCollection(points)
    
    return pts

# buffer points function, will be mapped ofver all points in collection 
def buffer_points(pt):
    radius = 45 
    bp = ee.Feature(pt).buffer(radius)
    
    return bp

# define function to rename and timestamp images 
def apply_red(img,fc):
    #img, fc = par 
    
    fcSub = fc.filterBounds(img.geometry())
    
    # image properties 
    scale = img.projection().nominalScale()
    crs = img.projection().crs()
    
    img_out = img.reduceRegions(collection=fcSub, reducer=ee.Redcuer.mean(),scale=scale,crs=crs)
    
    return img_out

    # img = ee.Image(img.select(bands, bandsRename)).set(datetimeName, img.date().format(datetimeFormat)).set('timestamp', img.get('system:time_start'))
    
    
    
    #%% END OF DAY ON 08/31: HOW TO PASS 2 ARGUMENTS TO MAPPED FUNCTION?!
    # TUPLE DOES NOT WORK BECAUSE ONE CAN OMNLY MAP OVER A FEATURE COLLECTION... 
    
    # https://gis.stackexchange.com/questions/302760/gee-imagecollection-map-with-multiple-input-function 
    
    
# define the zonalstats function 
def zonal_stats(ic, fc, params):
    
    par = (ic,fc)
    
    pts_info = ic.map(apply_red)
    # initialize parameters
    # imgRep = ee.Image(ic.first()),
    # imgProps = ee.Feature(None).copyProperties(imgRep).propertyNames()
    
    # params = {'reducer': ee.Reducer.mean(),
    # 'datetimeName' : 'datetime',
    # 'datetimeFormat' : 'YYYY-MM-dd HH:mm:ss',
    # # copy over params from previous image 
    # 'bands' : imgRep.bandNames(),
    # 'bandsRename' : imgRep.bandNames(),
    # 'imgProps':imgProps}
    
    # subset points that intersect image 
    fc_sub = fc.filterbounds(img.geometry())
    
    # reduce the image by region 
    
    
    
    
 
# clear the pointz variable just in case 
pointz = []   

# apply the line to points function  
pointz = line_to_points(ee.Geometry(ee_centerline), 1000)

# apply the bufferpoints function 
pts_topo = pointz.map(buffer_points)

# concatenate the variables of interest from the dem as bands of an image, and add a dummy system start time 
topo = ee.Image.cat(elev, slope).set('system:time_start', ee.Date('2000-01-01').millis())

# wrap the single image into an Imagecollection for use with the zonalstats function
topoCol = ee.ImageCollection([topo])

# Define parameters for the zonalStats function.
#params = ['bands',[0, 1], bandsRename= ['surf_elev', 'surf_slope']];

#%% 


import geemap 

gdf = geemap.ee_to_pandas(pointz)

#%% select arctic dem at centerlines 


#%%
fig, ax = plt.subplots(figsize=(10,10))
#centerlines.plot(ax=ax)
plt.scatter(gdf.lon,gdf.lat)
#pointz.draw('red',20)
#GLIMS.plot(ax=ax)
plt.show()



#%% 

AOIcords = ee.Geometry.Point(-140.06626387006307,59.97044608327772) # [[-140.06626387006307,59.97044608327772],[-139.50596113568807,59.97044608327772],[-139.50596113568807,60.220347186815644], [-140.06626387006307,60.220347186815644],[-140.06626387006307,59.97044608327772]]
AOI = AOIcords.buffer(1e4)



DEM = ee.Image('USGS/3DEP/10m')# .clip(AOI)
scale = 10 # scale in meters 

DEMvals = DEM.sampleRectangle(region=AOI).get('elevation')
DEMv = np.array(DEMvals.getInfo())

get_asset_list(None)


#%% 

