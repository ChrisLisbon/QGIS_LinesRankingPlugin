# Installation

First, you will need install QGIS on your computer - follow this link for installation files 
and guide: https://qgis.org/en/site/forusers/download.html 

Then there is a need to install a plugin. Go to `Plugins` - `Manage and Install Plugins`

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/manage_plugins.png" width="750"/>

Then choose `Not installed` and write `Lines Ranking` into the search field:

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/install_plugin.png" width="750"/>

Then click Install plugin button. Congratulations, you just have installed a plugin!

Chek toolbar for icon <img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/master/icon.png" width="15"/>

<img src="https://raw.githubusercontent.com/ChrisLisbon/QGIS_LinesRankingPlugin/docs/images/installed_icon.png" width="750"/>

## Additional steps (for QGIS versions lower than 3.16)

For older versions of QGIS you will need to install the Python libraries: networkx, pandas

### Linux

In terminal execute commands:

```locate pip3```

```cd <your system pip3 path from previous step (e.g. cd /usr/bin/)>```

Install libraries:

```pip3 install pandas```

```pip3 install networkx```

### Windows

Open OSGeo4W Shell and run commands:

```pip install pandas```

```pip install networkx```

