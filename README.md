# Webmap Utilities - A QGis plugin for webmap building

The Webmap Utilities plugin offers tools to facilitate the construction of webmaps, that is, dynamic maps whose content varies according to the scale.

We encourage you to use our tagging system to manage your projects (we'll talk about that in the next section), but you can use some of the functionality separately if you prefer.

Here is a list of features we provide:

* Set of tools to work with zoom levels instead of scales.
* You can set the visibility (zoom level) of one or more layers or even a group of layers.
* The plugin offers visibility control functions to be used in the Data Defined Override option of the layers. For example: you might want each additional zoom level to show 10% more of the most populous cities on the map.
* We also offer functions to control numeric fields (label size, symbol size, transparency etc). For example: you might want the size of the labels to increase, at each zoom level, uniformly between 7pt to 12pt.
* With the tagging system we offer, it is easier to create templates and reproduce the idea of ​​previous maps. With a few clicks you can:
  - Re-organize your layers according to a previously defined arrangement.
  - Apply styles (QML files) to all tagged layers (raster or vector).
  - Download OSM data of all tagged vector layers.

## Requirements and dependencies

- Minimum QGis version: 3.28 (LTR)

## Quick Tutorial

### Preparing your project

You can get access to the plugin's tools by just right-clicking anywhere in icons toolbar and choosing **Webmap Plugin Toolbar**. Then click ![](/images/configure_project.png) to configure your project with the scales normally used for webmaps. You can change this later by going to Project -> Properties -> View Settings -> Project Predefined Scales and putting there the scales you want. Remember that whatever scales are set, the zoom level count always starts from 0. That is, level 0 is always the first scale defined in the list.

### ![](/images/apply_style.png) Controlling visibility of features using clusters

Suppose you have a vector layer containing cities in South America. It would not be interesting to show all cities at all zoom levels (scales), as it would leave the map confused and with many labels and icons overlapping. 

The **Clustered Visualization** algorithm solves this problem by grouping nearby cities (and thus creating clusters) and making visible only the most populous city in each group. This grouping of cities is done by distance: you can define, for example, that the groups are formed by cities whose distances to each other are 20km maximum.

With each new zoom level, the algorithm halves this distance and forms entirely new clusters. Cities that have already been shown previously remain visible, but a new city from each new cluster will become visible as well! This process is repeated for as many levels as the user wants.

### Generating a Shaded Relief

**Using the tagging system is not required here**

Our shaded relief tool creates two layers, in the order they need to be: one above the other. It works like this because each layer uses a light source with a different azimuth and different blend modes. This brings more details to the final shaded relief.

In addition, both layers receive the Aerial Perspective effect: the higher the layer, the greater the contrast. This is good for cartography because usually the lower portions of a region contains more cities, highways etc and less contrast means easier to recognize all these elements. Here is a good article about Aerial Perspective: http://www.reliefshading.com/design/aerial-perspective/.

Click on ![](/images/relief_creator.png) button to generate a Shaded Relief. The option **Aerial Perspective Intensity**, always between 0 and 100, increase/decrease the contrast between higher and lower altitudes. And the option **Angle Between Light Sources** controls the angle between the light sources: a number between 30 - 70 is generally a good choice; values close to 180 usually gives an undesirable plastic effect.

Remember that layers are generated in the order they need to be, so its a good idea to rename them to something like "hillshade top" and "hillshade bottom". After these steps, put you colored DEM file below 'hillshade bottom' layer.
