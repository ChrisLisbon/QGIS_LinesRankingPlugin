<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/ranking.png" width="650"/>

Welcome to [QGIS Lines Ranking plugin](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin) documentation!

[Official plugin page is here](https://plugins.qgis.org/plugins/lines_ranking/#plugin-about)

## Applications

The plugin can be used to rank any linear vector layers. 
One of the most common cases in which it can be used is river network analysis (mainly - **stream ordering**):

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/images/application.png" width="750"/>

As can be seen from the image above, in the process of the plugin's execution the attributes are assigned to elements of 
the vector layer of the river network (and then based on the values of these attributes are visualized). 

With this plugin it is possible to analyze any linear vector objects, 
the structure of which is similar to a river net. For example, roads network, railroad system or 
any other logistic.

## Documentation structure 

The official documentation of the plugin is divided into two large parts:

- "How-to guides" and "Use cases" - detailed user documentation and examples of analyses which can be performed
- Theoretical issues - a detailed description of how the algorithms in this plugin work

## Want to contribute or give feedback

Feel free to prepare issue, Pull Request (PR) or contact us if you have any questions. 
Contacts can be found in ['About us'](about.md) page.

## Our publications

We have written several articles that explain how the plugin works. Feel free investigate such a resources in addition to official documentation: 

- [Stream Ordering: How And Why a Geo-Scientist Sometimes Needed to Rank Rivers on a Map](https://medium.com/towards-data-science/stream-ordering-how-and-why-a-geo-scientist-sometimes-needed-to-rank-rivers-on-a-map-360dce356df5) (eng);
- [The Algorithm for Ranking the Segments of the River Network for Geographic Information Analysis Based on Graphs](https://medium.com/swlh/the-algorithm-for-ranking-the-segments-of-the-river-network-for-geographic-information-analysis-b25cffb0d167?sk=f1475802bd96f8d14c994a6f87f7453d) (eng);
- [Алгоритм ранжирования сегментов речной сети с использованием графов для геоинформационного анализа](https://habr.com/ru/articles/514526/) (rus)

## Additional materials 
- [Jupyter notebook with processing code](https://github.com/Dreamlone/State_Hydrological_Institute/blob/master/River_ranking.ipynb) (rus)

## Notes

Please note that we have not tested this plugin on macOS. 
Therefore, if you are using macOS, errors may occur. 