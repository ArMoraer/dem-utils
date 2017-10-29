DEM Generator
=============

Description
-----------

Creates a random DEM (Digital Elevation Model) using trees of gaussian kernels.

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


![Example of archipelago mode](/img/archipelago.png "Example of archipelago mode")
_Example of the output of `python dem_generator.py /path/to/dem.tif --width 1500 --preset archipelago`_

![Example of mountainous island mode](/img/mountainous-island-example.png "Example of mountainous island mode")
_Example of the output of `python dem_generator.py /path/to/dem.tif --width 1500 --preset mountainous_island`_

If you want to manually tune the DEM generation parameters, here is the list of editable options -- they are all optional:

* `--waterratio <value>` ratio of water (i.e. negative elevation) in the DEM. Range: 0-1. Default value is 0.5.
* `--island` island mode; this means the borders (1-px padding) of the DEM will always have a negative value. This option may result in a final water ratio higher than the `--waterratio` option. Default value is False.
* `--scale <value>` scale of main features (for example, islands size) relative to the whole DEM. Range: 1-100. Default value is 20.
* `--detailslevel <value>` level of features details. Range: ≥0. Default value is 3.
* `--spread <value>` features spread. Range: 1-6. Default value is 3.
* `--roughness <value>` features roughness (higher value means more "mountainous"). Range: 1-10. Default value is 5.
* `--directionality <value>` features directionality (higher value means more elongated features). Range: 1-10. Default value is 5.

Warning: when increased, the `scale`, `detailslevel`, `spread` and `roughness` options can dramtically increase the generation time.