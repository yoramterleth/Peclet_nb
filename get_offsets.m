function [offsets] = get_offsets(lat,lon,elev, glacier_name)

%% get distance from terminus 
addpath(genpath('C:\Users\Yoram\Downloads\topotoolbox-master'))

D.lat = lat ; 
D.lon = lon ; 
D.elev = elev ; 

%% load tiff file 
DEM = GRIDobj([pwd '/python_gee/centerlines/' glacier_name 'DEM.tif']) ; 
FD  = FLOWobj(DEM);

dist = flowdistance(FD,'upstream') ; 

% if strcmp(glacier_name, 'Turner') | strcmp(glacier_name,'Haenke')
%     dist.Z = flipud(dist.Z); 
% end 

%dist.Z = flipud(rot90(dist.Z)) ; 

%% coords 
xx = [dist.georef.SpatialRef.XWorldLimits(1):dist.georef.SpatialRef.CellExtentInWorldX:dist.georef.SpatialRef.XWorldLimits(2)-1]'; 
yy = [dist.georef.SpatialRef.YWorldLimits(2):-dist.georef.SpatialRef.CellExtentInWorldY:dist.georef.SpatialRef.YWorldLimits(1)+11]'; 

[xxx, yyy ] = meshgrid(xx,yy); 

[lat , lon ] = polarstereo_inv(xxx,yyy,[],[],70,-45) ;% dist.georef.SpatialRef.XWorldLimits',dist.georef.SpatialRef.YWorldLimits')
%lat = abs(lat) ; 
% make coord grids for dist 
%lat = [D.lat(end):(D.lat(1)-D.lat(end))/dist.size(1):D.lat(1)]; 
%lon = [D.lon(end):(D.lon(1)-D.lon(end))/dist.size(2):D.lon(1)]; 
% lat = [min(D.lat): (max(D.lat)-min(D.lat))/dist.size(2):max(D.lat)];
% lon = [min(D.lon): (max(D.lon)-min(D.lon))/dist.size(1):max(D.lon)];
% 
% [lon, lat] = meshgrid(lon(2:end), lat(2:end)) ; 



figure
pcolor(lon,lat,dist.Z), shading flat
lat_lon_proportions()
grid on 

%% pull ice thickness and dem data along N centerline
for i = 1: length(D.elev)
    
    % pull the corresponding locations from MIllan 
    diff_y = lat(:)- D.lat(i);
    diff_x = lon(:)- D.lon(i) ; 
    difference = sqrt(diff_y.^2 + diff_x.^2);
    gp = find(difference == min(difference));

    offsets(i) = dist.Z(gp); 
%     H.x(i) = c.x(i) ; 
%     H.y(i) = c.y(i) ; 
%     H.z(i) = dem(gp) ; 
%     H.bed(i) = bed(gp) ;
%     H.bslope(i) = slope(gp) ; % tan(slope(gp)*pi/180) ; 
end 

% create matrices
% [x, y ] = meshgrid(D.lon, D.lat); 
% m = numel(D.lon);
% 
% [Xq,Yq,vq] = griddata(D.lon,D.lat,D.elevation,x,y); 
% 
% figure 
% pcolor(Xq,Yq,vq), shading flat
% figure 
% pcolor(x,y,z), shading flat
% d = GRIDobj(x,y,z);

end 