// compute the peclet numbers along a profile

// this script uses the first centerline from a file that that intersects the glacier polygon.
// if the user prefers to draw in a centerline themselves, change the variable name at line 80 to their given var name

////////////////////////////////////////////////
// name the csv file with the centerline info 
var file_out = 'Whillans' ; 
///////////////////////////////////////////////

// import the glims outlines
var GLIMS = ee.FeatureCollection('GLIMS/current')//.filter(ee.Filter.bounds(AOI))//.filter('glac_name=="Kamb Ice Stream"');
//print(GLIMS)

var dataset = ee.Image('USGS/LIMA/MOSAIC');
var antarctica = dataset.select(['B3', 'B2', 'B1']);
var antarcticaVis = {
  min: 0.0,
  max: 10000.0,
};

Map.addLayer(antarctica, antarcticaVis, 'Antartica Imagery (RGB)');


var mosaic = ee.Image('UMN/PGC/REMA/V1_1/8m');

Map.setCenter(-61, -75, 3);

var elevationVis = {
  bands: ['elevation'],
  min: -50.0,
  max: 2000.0,
  palette: ['0d13d8', '60e1ff', 'ffffff'],
};

Map.addLayer(mosaic, elevationVis, 'REMA_DEM_mosaic_8m');
var exaggeration = 100;
var hillshade = ee.Terrain.hillshade(mosaic.multiply(exaggeration));
Map.addLayer(hillshade, null, 'ETOPO1 Hillshade');

////////////////////////////////////////////////////////////////////////////////////
// load bedmachine surface elevation from assets: in my case named bed_machine_surf
var elev = Ant_dem
///////////////////////////////////////////////////////////////////////////////////

var slope = ee.Terrain.slope(elev);

/////////////////////////////////////////////////////////////////////////////////////////
// provide the correct ice thickness, loaded from assets: in my case named bed_machine_Ho 
var Ho = Ant_Ho
/////////////////////////////////////////////////////////////////////////////////////////

// smooth the ice thickness to get rid of Millan artefacts 
// Define a boxcar or low-pass kernel.
var boxcar = ee.Kernel.square({
  radius: 10, units: 'pixels', normalize: true
});

// Smooth the image by convolving with the boxcar kernel.
var Ho = Ho.convolve(boxcar);

//smooth the surface topography too
var elev = elev.convolve(boxcar); 

// caluclate bed topography
var bed_elev = Ant_bed
var bed_slope = ee.Terrain.slope(bed_elev);

// also smooth the bed slop, for good measure
var bed_slope = bed_slope.convolve(boxcar) ; 


// Adding layers to map:
Map.addLayer(bed_elev, {min: -1000, max: 2500}, 'bed_elev');


// function to get points from centerline
function lineToPoints(lineString, count) {
  var length = lineString.length();
  var step = lineString.length().divide(count);
  var distances = ee.List.sequence(0, length, step)

  function makePointFeature(coord, offset) {
    var pt = ee.Algorithms.GeometryConstructors.Point(coord);
    var coords = pt.coordinates(); // set coords as feature property
    
    return new ee.Feature(pt).set({'offset': offset,
                                  'lat': ee.List(coords).get(0),
                                  'lon': ee.List(coords).get(1)
    })
  }
  
  var lines = lineString.cutLines(distances).geometries();

  var points = lines.zip(distances).map(function(s) {
    var line = ee.List(s).get(0);
    var offset = ee.List(s).get(1)
    return makePointFeature(ee.Geometry(line).coordinates().get(0), offset)
  })
  
  points = points.add(makePointFeature(lineString.coordinates().get(-1), length))

  return new ee.FeatureCollection(points);
}

// actually get at the points: 

//////////////////////////////////////////////////////////////////////////////////////////////////////////
// here if the users prefers to draw in a centerline, change to the name of the centerline... ////////////
var points = lineToPoints(ee.Geometry(WHIL), 5000)                                         ////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////


// function to buffer the points (prepare to extract raster data)
function bufferPoints(radius, bounds) {
  return function(pt) {
    pt = ee.Feature(pt);
    return bounds ? pt.buffer(radius).bounds() : pt.buffer(radius);
  };
}

// function to get data at buffered points 
function zonalStats(ic, fc, params) {
  // Initialize internal params dictionary.
  var _params = {
    reducer: ee.Reducer.mean(),
    scale: null,
    crs: null,
    bands: null,
    bandsRename: null,
    imgProps: null,
    imgPropsRename: null,
    datetimeName: 'datetime',
    datetimeFormat: 'YYYY-MM-dd HH:mm:ss'
  };

  // Replace initialized params with provided params.
  if (params) {
    for (var param in params) {
      _params[param] = params[param] || _params[param];
    }
  }

  // Set default parameters based on an image representative.
  var imgRep = ic.first();
  var nonSystemImgProps = ee.Feature(null)
    .copyProperties(imgRep).propertyNames();
  if (!_params.bands) _params.bands = imgRep.bandNames();
  if (!_params.bandsRename) _params.bandsRename = _params.bands;
  if (!_params.imgProps) _params.imgProps = nonSystemImgProps;
  if (!_params.imgPropsRename) _params.imgPropsRename = _params.imgProps;

  // Map the reduceRegions function over the image collection.
  var results = ic.map(function(img) {
    // Select bands (optionally rename), set a datetime & timestamp property.
    img = ee.Image(img.select(_params.bands, _params.bandsRename))
      .set(_params.datetimeName, img.date().format(_params.datetimeFormat))
      .set('timestamp', img.get('system:time_start'));

    // Define final image property dictionary to set in output features.
    var propsFrom = ee.List(_params.imgProps)
      .cat(ee.List([_params.datetimeName, 'timestamp']));
    var propsTo = ee.List(_params.imgPropsRename)
      .cat(ee.List([_params.datetimeName, 'timestamp']));
    var imgProps = img.toDictionary(propsFrom).rename(propsFrom, propsTo);

    // Subset points that intersect the given image.
    var fcSub = fc.filterBounds(img.geometry());

    // Reduce the image by regions.
    return img.reduceRegions({
      collection: fcSub,
      reducer: _params.reducer,
      scale: _params.scale,
      crs: _params.crs
    })
    // Add metadata to each feature.
    .map(function(f) {
      return f.set(imgProps);
    });
  }).flatten().filter(ee.Filter.notNull(_params.bandsRename));

  return results;
}

// apply points buffer function
var ptsTopo = points.map(bufferPoints(45, false));

// Concatenate elevation, bbed elevation, bed slope and ice thickness as four bands of an image.
var topo = ee.Image.cat(elev, bed_elev, bed_slope, Ho)
  // Computed images do not have a 'system:time_start' property; add a dummy one
  .set('system:time_start', ee.Date('2000-01-01').millis());

// Wrap the single image in an ImageCollection for use in the zonalStats function.
var topoCol = ee.ImageCollection([topo]);

// Define parameters for the zonalStats function.
var params = {
  bands: [0, 1, 2, 3],
  bandsRename: ['surf_elev', 'bed_elev', 'bed_slope', 'ice_thickness']
};

// Extract zonal statistics per point per image.
var ptsTopoStats = zonalStats(topoCol, ptsTopo, params);

// print the collection
print(ptsTopoStats);


// VISULAIZATION + EXPORT //////////////////////////////////////////////

// add the cenerline points to map .... !! use this to check whether we have the centerline of interest!
Map.addLayer(points)

// add ice thickness to map 
var I_T_Vis = {
  min: 0.0,
  max: 3000.0,
  palette: ['0d13d8', '60e1ff', 'ffffff'],
};

Map.addLayer(Ho,I_T_Vis,'Ice Thickness');

Map.addLayer(Kamb2, {color: 'green'},'centerlines');

// export pulled info to csv in drive 
Export.table.toDrive({
  collection: ptsTopoStats,
  folder: 'cycles',
  description: file_out,
  fileFormat: 'CSV'
});
