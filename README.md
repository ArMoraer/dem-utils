DEM Generator
=============

Description
-----------

Creates a random DEM (Digital Elevation Model) using trees of gaussian kernels (see [Random DEM Generator](https://beyondthemaps.wordpress.com/2017/11/01/random-dem-generator/) for more details).

Dependencies
------------

This script was developed with Python 2.7 and relies on numpy (1.13.1) and osgeo (1.10.1).

Installation and use
--------------------

Just copy dem_generator.py to your computer and run the following command in a terminal: `python dem_generator.py <parameters>`

Parameters
----------

You can use `python dem_generator.py -h` to get a full list of possible parameters.

### Basic parameters

* Output DEM path (madatory). The DEM mus have a `.tif` extension.
* `--height <value>` DEM height in pixels (optional). Default value is 1000.
* `--width <value>` DEM width in pixels (optional). Default value is 1000.
* `--verbose` verbose mode (optional).

### Advanced parameters

The generation of a DEM relies on multiple and somewhat advanced parameters. Preset parameters can be used with the `--preset <mode>` option in order to avoid manually tuning these parameters. The `--preset` option currently supports two modes: `archipelago` and `mountainous_island`. See examples below:

![Example of archipelago mode](/img/archipelago-example.png "Example of archipelago mode")
_Example output of `python dem_generator.py /path/to/dem.tif --width 1500 --preset archipelago`_

![Example of mountainous island mode](/img/mountainous-island-example.png "Example of mountainous island mode")
_Example output of `python dem_generator.py /path/to/dem.tif --width 1500 --preset mountainous_island`_

If you want to manually tune the DEM generation parameters, here is the list of editable options -- they are all optional:

* `--waterratio <value>` ratio of water (i.e. negative elevation) in the DEM. Range: 0-1. Default value is 0.5.
* `--island` island mode; this means the borders (1-px padding) of the DEM will always have a negative value. This option may result in a final water ratio higher than the `--waterratio` option. Default value is False.
* `--scale <value>` scale of main features (for example, islands size) relative to the whole DEM. Range: 1-100. Default value is 20.
* `--detailslevel <value>` level of features details. Range: ≥0. Default value is 3.
* `--spread <value>` features spread. Range: 1-6. Default value is 3.
* `--roughness <value>` features roughness (higher value means more "mountainous"). Range: 1-10. Default value is 5.
* `--directionality <value>` features directionality (higher value means more elongated features). Range: 1-10. Default value is 5.

Warning: when increased, the `scale`, `detailslevel`, `spread` and `roughness` options can dramtically increase the generation time.

Here a few examples of the role of some parameters on the result:

* scale:

| ![Example of random DEM with scale = 10](/img/waterratio_0.6-scale_10.png "Scale = 10") | ![Example of random DEM with scale = 15](/img/waterratio_0.6-scale_15.png "Scale = 15") | ![Example of random DEM with scale = 20](/img/waterratio_0.6-scale_20.png "Scale = 20") |
| :---: | :---: | :---: |
| `--scale 10` | `--scale 15` | `--scale 20` (default) |

* details level:

| ![Example of random DEM with detailslevel = 1](/img/detailslevel_1.png "detailslevel = 1") | ![Example of random DEM with detailslevel = 3](/img/detailslevel_3.png "detailslevel = 3") | ![Example of random DEM with detailslevel = 5](/img/detailslevel_5.png "detailslevel = 5") |
| :---: | :---: | :---: |
| `--detailslevel 1` | `--detailslevel 3` (default) | `--detailslevel 5` |

* spread:

| ![Example of random DEM with spread = 1](/img/spread_1.png "Spread = 1") | ![Example of random DEM with spread = 3](/img/spread_3.png "Spread = 3") | ![Example of random DEM with spread = 5](/img/spread_5.png "Spread = 5") |
| :---: | :---: | :---: |
| `--spread 1` | `--spread 3` (default) | `--spread 5` |

* roughness:

| ![Example of random DEM with roughness = 1](/img/roughness_1.png "Roughness = 1") | ![Example of random DEM with roughness = 5](/img/roughness_5.png "Roughness = 5") | ![Example of random DEM with roughness = 8](/img/roughness_8.png "Roughness = 8") |
| :---: | :---: | :---: |
| `--roughness 1` | `--roughness 5` (default) | `--roughness 8` |

* directionality:

| ![Example of random DEM with directionality = 1](/img/directionality_1.png "Directionality = 1") | ![Example of random DEM with directionality = 5](/img/directionality_5.png "Directionality = 5") | ![Example of random DEM with directionality = 10](/img/directionality_10.png "Directionality = 10") |
| :---: | :---: | :---: |
| `--directionality 1` | `--directionality 5` (default) | `--directionality 10` |