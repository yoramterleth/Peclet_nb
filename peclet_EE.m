%% peclet nb from earth engine info with full Felikson 2021 formulation

%% clean workspace 
close all
clear all 
clc

%% open csv file 
glaciername = 'Bassin3' ; 
filename = [glaciername '.csv'] ; 

%[C] = importcsv_EE([pwd '/csv_earth_engine/' filename]); 
[C] = import_EE_arcticDEM([pwd '/csv_earth_engine/' filename]); 

%% compute Peclet nb:

%% smooth slope by ten times the avergae thickness with second degree Savitzky-Golay method 

% get window length
W = floor((10*nanmean(C.ice_thickness)) / nanmean(diff(C.offset))) ; 
disp(['Step length is ' num2str(mean(diff(C.offset))) '. Window length is ' num2str(W) ' m.'])

% smooth bed 
smooth_bed = smooth(C.bed_elev,W,'sgolay') ; 

% smooth ice thickness 
smooth_Ho = smooth(C.ice_thickness,W,'sgolay') ; 

% smooth surface
smooth_surf = smooth(C.surf_elev,W,'sgolay') ; 

figure 
plot(C.offset, smooth_bed), hold on 
plot(C.offset, C.bed_elev)
%% 

%get slope as rise over run  
%b_slope = tan(deg2rad(smooth_bed)); 
b_slope = [0;diff(smooth_bed)]./[0;diff(C.offset)] ; 

% get slope in ice thickness as rise over run
H_slope = [0; diff(smooth_Ho)] ./ [0; diff(C.offset)] ; 

% get distance from terminus 
% if the end of the line is lower than the start, profile runs from
% headwall to terminus...
if C.surf_elev(end) < C.surf_elev(1)
    dist_terminus = flipud(C.offset) ; 
else 
    dist_terminus = C.offset ; 
end 

%% get Peclet 
m = 1 ; 

% hard bed sliding law pecelt, should be similar to feliskon et al
Pe2 = ((((m+1)*b_slope) ./ ( m * smooth_Ho)) - (((m+1) * H_slope)./ smooth_Ho)) .* dist_terminus  ; 

Pe = 2 .* (b_slope ./ C.ice_thickness) .* dist_terminus  ; 

%% visulaise 
figure 
subplot(1,3,[1 2])
yyaxis left
plot(dist_terminus/1000, smooth_bed,'linewidth',1.5), hold on 
plot(dist_terminus/1000, smooth_surf,'linewidth',1.5)
ylabel('elevation (m a.s.l.)')

yyaxis right
plot(dist_terminus/1000, Pe,'linewidth',1.2)
ylabel('Pe')
%ylim([-2,5])
legend('bed','ice surface','Pe')
xlabel('centerline distance from terminus (km)')
title(filename(1:end-4))


% %%% map 

% import shapefile of glacier outline 
RGI = shaperead([pwd '/RGI_outlines/' glaciername '_outline.shp']); 
RGI = RGI(11); 

%figure(3)
subplot(1,3,3)
plot(RGI.X, RGI.Y,'linewidth',1.5,'color',rgb('steel blue')), hold on 
lat_lon_proportions()
xlabel('Longitude')
ylabel('Latitude')

grid on 
scatter(C.lon, C.lat,30,Pe,'filled')
colormap(plasma(256))
c = colorbar ; 
ylabel(c, 'Pe')
title(glaciername)
%caxis([-50 50])
%caxis([0,500])


%%
figure 
plot(dist_terminus, b_slope), hold on 
%plot(dist_terminus, b2_slope)

figure 
plot(Pe), hold on , plot(Pe2)
