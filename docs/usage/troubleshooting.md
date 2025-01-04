# Troubleshooting

This page provides some tips you can use in case something goes wrong.

## General advices

**Coordinate reference system (CRS) issues**: Before starting to use the algorithm, please make sure that the project uses metric projection. 
Also the layers used in the calculation (both linear and point layers) should be converted to this projection.

CRS of the project and layers must be the same. For example - `WGS 84 / UTM zone 49N` (select the most appropriate one for your layer): 

- Project: `Project` - `Properties` - `CRS` - `WGS 84 / UTM zone 49N`;
- Layer: `Processing` - `Toolbox` - `Reproject layer` - assign "WGS 84 / UTM zone 49N". Save result into file.

**How to view the error log**: usually, when something goes wrong, QGIS generates 
a window with a warning that an error has occurred, which shows all 
the necessary information from the operating system to the version of QGIS. 
Then you can do an export to a txt file of such logs. 
If such a window does not appear automatically, you can view the 
logs through `View` - `Panels` - `Log Messages` and then launch the plugin.

## Action plan if plugin does not produce result

1. Check if you are using the latest version of the plugin. [Plugin versions page](https://plugins.qgis.org/plugins/lines_ranking/#plugin-versions). If not the latest - update;
2. Make sure the plugin is installed correctly. To do this, put aside your sample data for a few minutes and try using the data (check 'river_example' vector layer from [example_data](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin/tree/master/example_data) folder) that is in the repository. For example, download layer "river_example.shp" and then follow the instructions in section ["Functionality review"](functionality_review.md). Then proceed to step 3. If you cannot reproduce the example, see step 3 anyway;
3. Create qgis project and save it in the folder. Plugin is utilizing [python tempfile module][https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir],
   so it is trying to save intermediate files which might appear during plugin execution in temporal folder identified by `gettempdir` function.
   `gettempdir` determines folder based on some internal logic which might be influenced by QGIS environment.
   In case the writing permissions for temporal folder (to save something to the "C:" drive for example) are not granted, 
   the plugin will crash with an error (PermissionError). It might help to create a folder on another drive (if possible), for example, 
   "D:", save the project there, exit. Open the project again and continue working in it;
4. Change `Snapping threshold (in map units)` parameter - try, for example, 50, 100, 150.
5. If you use the geopackage file (`.gpkg`), save it to a `.shp` file and try to run the algorithm again

If none of the above steps help, you can always contact the plugin developers for help. 

## Ask developers for help

So, you tried all the steps above and nothing worked. It looks like the plugin really doesn't work with your data. In that case, use the following template to report the error:

* **Brief task description:** Briefly (in a few sentences) describe what you want to do
* **Brief issue description:** Briefly describe what is not working, For example, "the plugin does not start ranking segments, but terminates after 5% completion"
* **Data:** If possible, please attach a sample of the data with which the plugin fails to run
* **Technical information**: Please specify which OS you are using, what version of QGIS and what version of the plugin is installed. Which coordinate reference system (CRS) you are using
* **Error logs**: send error logs in txt file format, to save logs, see instructions above

You can use two ways to report the error: 

* **GitHub issues**: follow [this page](https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin/issues) and make a post
* **Direct email message**: send message to `mik.sarafanov@gmail.com` with the topic "Lines Ranking plugin issue" and description according to template. Feel free to text me in English and Russian languages
