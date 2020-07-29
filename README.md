# Lines ranking (QGIS)

QGIS plugin for ranking lines features based on the position of starting point

## Description

The plugin calculates the rank of each segment of the connected river network and the number of tributaries flowing into the segment.

The algorithm is based on constructing a mathematical representation of the network in the form of a graph, taking into account the segment length. The output can be used for visual visualizations and network explorations.

Required dependencies (python libraries): pandas, networkx. $pip install pandas $pip install networkx (for QGIS python interpreter, see docs for details)

## Requirements

* QGIS 3.14+
* Python libraries: networkx, pandas

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