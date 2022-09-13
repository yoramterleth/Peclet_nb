# -*- coding: utf-8 -*-
"""

get_GLIMS_shapefiles 


Created on Fri Sep  9 13:07:42 2022

@author: Yoram
"""

import geemap 
import ee
import geopandas as gp

ee.Initialize()

#%% select a glacier #####################################################################
RGIglacier = ee.FeatureCollection('GLIMS/current').filter('glac_name=="Austfonna, -"')

# optional to use ID for non named glaciers 
 # RGIglacier = ee.FeatureCollection('GLIMS/current').filter('glac_id=="G209330E63184N"')


# glacier name for file out
glacier_name = 'Bassin3'

########################################################################################


# convert this to a shapefile and save it 
geemap.ee_to_shp(RGIglacier,'C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/RGI_outlines/'+glacier_name+'_outline.shp' )

GLIMS_shp = gp.read_file('C:/Users/Yoram/OneDrive - University of Idaho\Desktop/PhD pos/SURGE_CYCLES/peclet_nb/RGI_outlines/'+glacier_name+'_outline.shp' )


#%% plot the glacier outline and the centerlines we are pulling
ax = GLIMS_shp.plot()