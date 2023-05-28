# Functionality review

So, we have already installed the plugin in QGIS. 
It's the time to look at its functionality. 
In this document, we'll take a step-by-step look at how it can be used. 

## Data 

In the [repository with source code](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin)
there is a folder with data examples (you can download this files to your computer by clicking "Download raw file"). We will take 'river_example' vector layer from [example_data](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin/tree/master/example_data) folder.
Load this file into QGIS (and turn on Open Street Map: `Web` - `QuickWebServices` - `OSM` - `OSM Standard`):

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/load_river_example.png" width="750"/>

For visualization purposes we also can assign projection WGS 84 / UTM zone 49N: 
`Project` - `Properties` - `CRS` - `WGS 84 / UTM zone 49N`.

## Usage example (Point on a map) 

Open Lines Ranking plugin and choose option `Point on a map` - then just click to the place 
where the river flows into the ocean:

## Usage example (Select layer) 

## Results overview 

The plugin creates a new vector layer in which the following fields (in attributes table) appear:

- Field 1
- Field 2
- Field 3
