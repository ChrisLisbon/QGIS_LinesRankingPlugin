# River network analysis use case

Welcome to the "River use case" page.
Here is information on how you can use the plugin to analyze the river network and prepare visualizations.

## Experiment setup 

- QGIS Desktop 3.34.3
- Windows
- Date: 04.02.2024
- Data: The Ob river as vector layer

We will use the Ob river data to perform analysis. Load data and assign projection `WGS 84 / UTM zone 40N`:

- Project: `Project` - `Properties` - `CRS` - `WGS 84 / UTM zone 40N`;
- Layer: `Processing` - `Toolbox` - `Reproject layer` - assign "WGS 84 / UTM zone 40N"

And obtain the following initial picture:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/ob_init.png" width="750"/>

Choose start point and launch the algorithm: 

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/ob_value.png" width="750"/>


## Shreve stream order

Visualize "ValueShreve" column and prepare a map

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/shreve_order_ob.png" width="750"/>

## Strahler stream order

Visualize "ValueStrahler" column and prepare a map

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/strahler_order_ob.png" width="750"/>

## Topological stream order 

Visualize "Rank" column and prepare a map

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/topological_order_ob.png" width="750"/>
