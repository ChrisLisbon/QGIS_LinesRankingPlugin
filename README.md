![ranking.png](https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/ranking.png)

# Lines ranking (QGIS)

QGIS plugin for ranking lines features based on the position of starting point

## Description

The plugin calculates the rank of each segment of the connected river network and the number of tributaries flowing into the segment.

The algorithm is based on constructing a mathematical representation of the network in the form of a graph, taking into account the segment length. The output can be used for cartographical visualizations and network explorations.

## Requirements

* QGIS 3.14+
* Python libraries: networkx, pandas

### How to install plugin:

This plugin is available in official QGIS plugins repository - use menu Modules in QGIS 3.14+ to find it.

Alternatively you can download code from this repository and put it in directory lines_ranking in your local QGIS plugins folder.

### How to install requirements:

#### Linux

In terminal execute commands:

`$ locate pip3`

`$ cd <your system pip3 path from previous step (e.g. cd /usr/bin/)>`

Install libraries:

`$ pip3 install pandas`

`$ pip3 install networkx`

#### Windows

Open OSGeo4W Shell and run commands:

`$ pip install pandas`

`$ pip install networkx`

## Additional materials 

* [Jupyter notebook with processing code](https://github.com/Dreamlone/State_Hydrological_Institute/blob/master/River_ranking.ipynb)
