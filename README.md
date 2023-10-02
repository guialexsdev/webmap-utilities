# Webmap Utilities - A QGis plugin for webmap building

This plugin offers tools to help you create webmaps.

Here is a list of features:

- Avoid showing hundred of features at once. Use our hierarchical, clustered or grid-based visualization engine.
- Apply the Aerial Perspective effect to control the contrast of your hillshade.
- Create a special Relief Shading that gives more detail to the terrain while softening the visual aspect.
- Set the visibility of your layers or group of layers using zoom levels instead of scales.
- Change scale using a zoom level selector.

## QGis Plugin Repository

https://plugins.qgis.org/plugins/webmap_utilities/

## Requirements and dependencies

- Minimum QGis version: 3.28 (LTR)

## Quick Tutorial

### Preparing your project

You can get access to the plugin's tools by just right-clicking anywhere in icons toolbar and choosing **Webmap Plugin Toolbar**. Then click ![](/images/configure_project.png) icon to configure your project with the scales normally used for webmaps. You can change this later by going to Project -> Properties -> View Settings -> Project Predefined Scales and putting there the scales you want. Remember that whatever scales are set, the zoom level count always starts from 0. That is, level 0 is always the first scale defined in the list.

### ![](/images/cluster_view.png) Controlling visibility of features using clusters

Suppose you have a vector layer containing cities of South America. It would not be interesting to show all cities at all zoom levels (scales), as it would leave the map confused and with many labels and icons overlapping. 

The **Clustered Visualization** algorithm solves this problem by grouping nearby cities (and thus creating clusters) and making visible only the most populous city in each group, using an attribute called **population** for example. This cities clusterization is done by distance: you can define, for example, that the groups are formed by cities whose distances to each other are 20km maximum. 

At each new zoom level, the algorithm halves this distance and forms entirely new clusters. Cities that have already been shown previously remain visible, but a new city from each new cluster will become visible as well! This process is repeated for as many levels as the user wants.

To run this algorithm, click ![](/images/cluster_view.png) and follow the guidelines described there. The result is a vector layer containing the same attributes as the original layer, but adding a new attribute whose default name is **_visibility_offset**. This attribute needs to be used together with the **visibilityByOffset** function (provided by the plugin) in the Data Defined Override option of the layer symbology.

For example, if we want to control the visibility of labels we would go to Layer Properties -> Simbology -> Rendering -> Show Label -> Edit and use the function **visibilityByOffset**. The first argument of the function indicates from which zoom level the layer will be visible, while the second argument is the attribute created by the algorithm. See the image below:

![](/images/using_visibility_offset.png)

### ![](/images/grid_visualization.png) Controlling visibility of features using grids

Another way to control features visibility is by using a grid view. It works like this: the algorithm creates an imaginary grid of regularly spaced points and makes visible only the feature closest to each point. At each new zoom, the distance between grid points is halved and a new feature is made visible.

To run this algorithm, click ![](/images/grid_visualization.png) and follow the instructions described there. The remaining procedures are the same as described in the previous section.

### ![](/images/aerial_perspective.png) Applying Aerial Perspective to a Hillshade

This algorithm applies the Aerial Perspective effect to a hillshade. This effect consists in reducing the contrast of a hillshade in lower regions and increasing it in higher regions. The result is more pleasant hillshade layer.

To use this algorithm, click ![](/images/aerial_perspective.png) and follow the instructions described there.

### ![](/images/relief_creator.png) Creating a Shaded Relief with two light sources

This algorithm combines two hillshades, created with two different light sources and with different brightness and contrast settings, to generate a Shaded Relief visually light and with good level of detail. The Aerial Perspective effect is automatically applied. 

To use this algorithm, click ![](/images/relief_creator.png) and follow the instructions described there.

### Other functionalities

- Zoom level selector to complement the QGis scale selector.
- Right-click on a layer and then **Set Layer Zoom Level Visibility** to configure layer visibility using zoom levels instead of scales.
