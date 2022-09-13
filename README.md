# Peclet_nb
collection of srcipts to investigate the peclet number. 

## An overview of what does what: 

### Javascript:

These script run in the earth engine code editor. They do require the user to have the Millan ice thicknesses as an asset and to import them and rename them, as RGI I believe. 
- peclet_get_cl_data.js lets the user draw in an AOI and a centerline, and pulls data from it from the USGS 3DEP 10 m DEM. So this only works in the USA. 
- peclet_get_data_ArcticDEM.js lets the user pull data from anywhere ArcticDEM has coverage. Note that the correct ice thicknesses have to be loaded. 

### Python/Earth engine

These are python scripts but run with the EE and GEEMAP modules.
- pull_centerlines.py gets values from ArcticDEM same as the above scripts, but along all the centerlines given in the Zhang et al database (https://doi.org/10.11922/sciencedb.0164). 
- centerline_functions.py has some helpers for pull_centerlines.py
- get_GLIMS_shapefiles.py is just a script that gets the RGI outline of your choice from earth engine, and loads it to a shapefile.

### Matlab
These actually compute Pe and make plots (sorry, I just like Matlab better for plots, and I don't know how to use geopandas hydrology tools. 
They use the csv files exported by the earth engine or python scripts. 
-Peclet_EE.m computes the Pe from the earth engine code editor output. Users do need to select whether they got data with arctic dem or USGS dem. 
-Peclet_python.m does the same but with the Zhang centerlines. 
- get_offsets.m is a helper for Peclet_python.m: it computes the distance to the terminus using Matlab's topotoolbox. 
- other .m scripts are helpers to load data. 
