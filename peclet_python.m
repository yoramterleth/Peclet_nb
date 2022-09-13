%% script to compute peclet nb along all the centerlines

close all 
clear all
clc


%% glacier name 
glacier_name = 'SitKusa' ; 

%% import shapefile of glacier outline 
% centerlines
RGI = shaperead([pwd '/python_gee/centerlines/' glacier_name '_outline.shp']);
disp('Imported outline shapefile.')
%% import the centerline data 
D = importcsv_python2([pwd '/csv_python/' glacier_name '_stats.csv']); 

disp('Imported centerline data shapefile.')

sorted_D = sortrows(D, {'offset'}); 
dist_terminus = cumsum(sorted_D.offset); 

strings = sortrows(D, {'systemindex'}); 

%dist_terminus = cumsum(strings.offset); 

%% get distances 
disp('Retreiving distances from terminus based on flowaccumulation DEM...')

dist_terminus = get_offsets(D.lat,D.lon,D.elev, glacier_name) ; 
dist_terminus(dist_terminus<5000) = nan ; 

%% compute Peclet nb:
disp('Computing Pe...')
%get slope as rise over run  
b_slope = tan(deg2rad(D.bed_slope)); 


% get Peclet %% essy still! 
Pe = 2 .* (b_slope ./ D.Ho) .* (dist_terminus')  ; 

% get rid of weird values from 0 divisions
%Pe(Pe>500)=nan ; 
Pe(Pe> nanmean(Pe)+1*nanstd(Pe) | Pe < nanmean(Pe)- 1*nanstd(Pe)) = nan ; 

%% visualize 
disp('Plotting...')

figure 
plot(RGI.X, RGI.Y,'linewidth',1.5,'color',rgb('steel blue')), hold on 
lat_lon_proportions()
xlabel('Longitude')
ylabel('Latitude')
grid on 
scatter(D.lon, D.lat,30,Pe,'filled')
colormap(plasma(256))
c = colorbar ; 
ylabel(c, 'Pe')
title(glacier_name)
caxis([0,500])



