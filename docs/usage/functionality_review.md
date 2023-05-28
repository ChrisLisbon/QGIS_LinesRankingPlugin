# Functionality review

So, we have already installed the plugin in QGIS. 
It's the time to look at its functionality. 
In this document, we'll take a step-by-step look at how it can be used. 

## Data 

In the [repository with source code](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin)
there is a folder with data examples (you can download this files to your computer by clicking "Download raw file"). We will take 'river_example' vector layer from [example_data](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin/tree/master/example_data) folder.
Load this file into QGIS (and turn on Open Street Map: `Web` - `QuickWebServices` - `OSM` - `OSM Standard`
.
Perform re-projection to WGS 84 / UTM zone 49N: 

- Project: `Project` - `Properties` - `CRS` - `WGS 84 / UTM zone 49N`;
- Layer: `Processing` - `Toolbox` - `Reproject layer` - assign "WGS 84 / UTM zone 49N"

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/load_river_example.png" width="750"/>


## Usage example (Point on a map) 

Open Lines Ranking plugin and choose option `Point on a map` - then just click to the place 
where the river flows into the ocean. Then the following results obtained:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/river_finished.png" width="750"/>

## Usage example (Select layer) 

## Results overview 

The plugin creates a new vector layer in which the following fields (in attributes table) appear:

- Rank
- Value
- Distance

All three new fields can be seen in the attribute table: `rank_attributes` - `Open Attribute Table`.

We can also see that our layer is smaller than the original layer - some parts of the river have gone off. For example, check 
this picture:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/missing_parts.png" width="750"/>

**This is ok** - the topology of vector layers may contain errors, so some elements of the vector layer do not fit tightly together:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/topology_issues.png" width="750"/>

To fix this, pay attention to the algorithm parameter `Snapping threshold (in map units)`. 
We can set the number to 500 meters, for example, and then all layer gaps that do not exceed 500 meters will be combined:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/th_500.png" width="750"/>

## Visualization 

To better understand what values have been assigned to this layer, we suggest preparing some visualizations.

### Value

`rank_attributes` - `Properties` - `Symbology` - `Graduated`. Then choose 'Value' field for `Value`
and 'Size' for `Method` and click `Classify`: 

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/results_vis_values.png" width="750"/>

Thus, using the Value attribute you can show the total number of tributaries. 

### Rank 

`rank_attributes` - `Properties` - `Symbology` - `Graduated`. Then choose 'Rank' field for `Value`
and 'Color' for `Method` and click `Classify`: 

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/results_vis_rank.png" width="750"/>

With the help of assigned ranks you can determine how far the river section (segment) is located from the estuary - in terms of the remoteness of the graph nodes. 

### Distance 

The Rank attribute gives an incomplete idea of the remoteness of the segments. Therefore, 
if you are interested in distance in meters, use the "Distance" attribute to visualize.

`rank_attributes` - `Properties` - `Symbology` - `Graduated`. Then choose 'Distance' field for `Value`
and 'Color' for `Method` and click `Classify`: 

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/results_vis_distance.png" width="750"/>

With the help of assigned ranks you can determine how far the river section (segment) is located from the estuary - in terms of the actual distance metrics. 
