# Algorithm

The calculation algorithm in its first version (2020) is 
described in detail in the article [The Algorithm for Ranking the Segments of the River Network for Geographic Information Analysis Based on Graphs](https://medium.com/swlh/the-algorithm-for-ranking-the-segments-of-the-river-network-for-geographic-information-analysis-b25cffb0d167?sk=f1475802bd96f8d14c994a6f87f7453d). 

If you would like to see a more concise description - welcome to this page!

The plugin is written in the Python programming language and uses other QGIS 
tools in its calculations. Therefore, it is worth highlighting two large functional blocks: 

- Pre-processing algorithms (external)
- Core logic

Pre-processing algorithms use QGIS tools to remove topological incorrectnesses 
in the layer, calculate segment lengths, and partition the river network into 
individual segments. Once the layer is preprocessed, it is transferred to the adjacency list (graph).

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/preprocessing_source_layer.png" width="750"/>

## Core logic 

The core logic is described in three steps:

- The assignment of the attributes `Rank` and `offspring` (internal technical attribute) for each node (segment)
- Detection of the "main river" - a sequence of nodes (segments) from the farthest river segment to the mouth of the river
- Assigning the `ValueShreve`, `ValueStrahler` and `Distance attributes`

After that, the graph nodes are again "transformed" into linear vector objects. The calculation is finished
