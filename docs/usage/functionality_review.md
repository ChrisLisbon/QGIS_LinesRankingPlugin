# Functionality review

So, we have already installed the plugin in QGIS. 
It's the time to look at its functionality. 
In this document, we'll take a step-by-step look at how it can be used. 

## Data 

In the [repository with source code](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin)
there is a folder with data examples (you can download this files to your computer by clicking "Download raw file"). We will take 'river_example' vector layer from [example_data](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin/tree/master/example_data) folder.
Load this file into QGIS (and turn on Open Street Map: `Web` - `QuickWebServices` - `OSM` - `OSM Standard`.

Perform re-projection to WGS 84 / UTM zone 49N: 

- Project: `Project` - `Properties` - `CRS` - `WGS 84 / UTM zone 49N`;
- Layer: `Processing` - `Toolbox` - `Reproject layer` - assign "WGS 84 / UTM zone 49N"

Save layer as permanent vector `shp` (or any other) file. 

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/load_river_example.png" width="750"/>


## Usage example (Point on a map) 

Open Lines Ranking plugin and choose option `Point on a map` - then just click to the place 
where the river flows into the ocean. Then the following results obtained:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/river_finished.png" width="750"/>

## Usage example (Select layer) 

You can also use a one-point vector layer to assign the starting point run the algorithm.
We can use `start_point_example`. Re-project the layer: `Processing` - `Toolbox` - `Reproject layer` - assign "WGS 84 / UTM zone 49N".

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/start_point_layer.png" width="750"/>

## Results overview 

The plugin creates a new vector layer in which the following fields (in attributes table) appear:

- **ValueShreve** - total number of tributaries. You can consider this value as "[Shreve stream order](https://en.wikipedia.org/wiki/Stream_order)". 
- **ValueStrahler** - Strahler order.
- **Rank** - distance to the segment from the starting point in a categorized form: rank 1 means 
  that this segment is adjacent to the starting point. rank 2 are those adjacent to segments 
  with rank 1, etc. This coefficient can be considered the inverse of the "[Topological order](https://en.wikipedia.org/wiki/Stream_order#Horton_and_topological_stream_orders)"
- **Distance** - distance to the segment from the starting point
