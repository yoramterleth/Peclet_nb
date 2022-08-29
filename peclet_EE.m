%% peclet nb from earth engine info 

%% clean workspace 
close all
clear all 
clc

%% open csv file 
filename = 'SitKusa.csv' ; 

[C] = importcsv_EE([pwd '/csv_earth_engine/' filename]); 

%% compute Peclet nb:

%get slope as rise over run  
b_slope = tan(deg2rad(C.bed_slope)); 

% get distance from terminus 
% if the end of the line is lower than the start, profile runs from
% headwall to terminus...
if C.surf_elev(end) < C.surf_elev(1)
    dist_terminus = flipud(C.offset) ; 
else 
    dit_terminus = c.offset ; 
end 

% get Peclet 
Pe = 2 .* (b_slope ./ C.ice_thickness) .* dist_terminus  ; 

%% visulaise 
figure 
yyaxis left
plot(dist_terminus, C.bed_elev), hold on 
plot(dist_terminus, C.surf_elev)

yyaxis right
plot(dist_terminus, Pe)



