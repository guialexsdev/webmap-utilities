# Webmap Utilities - A QGis plugin for webmap building

## What it does?

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

## Quick Tutorial

### Adding a tag

The tagging system is simple. First you define the category - tha Tag - of each layer. For example, we might have multiple layers, perhaps from different sources, containing the villages in a given region. While all of these layers might have different names, they could all be categorized as 'village', as they will likely share several settings (styling options, for example). So, our tag for our village vector layers is simple **village**.

Next we need to plan how the tagged layers will be recognized by the plugin. Currently, you can do this in 2 ways:

- Renaming your layer to contain the chosen tag at the beginning of the name. In our example, the name of one of the layers would be **villages source1**, the other would be **villages source2**.

- Inserting a Category in the layer's metadata. Just go to Properties -> Metadata -> Categories. In this case, it could just be 'villages'.

Now go to the plugin's ![](/images/settings.png) **Settings**  and register the tag with button ![](/images/symbologyAdd.png) **Add new tag...**. Don't forget to select the tag identification mode at the bottom of the screen.

![Settings: add new tag clicking the + icon and choose identification mode at the bottom os the screen.](/images/step_adding_tag.png)

### Adding a property to a tag

The next step is to insert some properties to the created tag. There are some predefined ones (but you can create your own too). Let's use, for example, the `_zoom_min` and `_zoom_max` properties. Together they control the range of zoom levels at which a feature or all of them will be visible.

To add a property to the tag, go to ![](/images/settings.png) **Settings** -> Tags  and right-click on the tag name. Click **Add Property...**. Select `_zoom_min`, enter the number 9 and click OK. Repeat the process for the `_zoom_max` property, but choosing the number 15, for example. That is, the features of our 'villages' tagged layers will only be visible between levels 9 and 15 of zoom. At this time, the property is not yet taking effect. For that we need the next step. Let's go!

![Add property to a tag](/images/step_add_property.png)

**Other useful properties**

- `_style`: add this property to your tag and choose a style file (QML). 
- `_osm_key`: OSM key. Ex: place, highway, waterway etc. Need to exist alongside the other OSM properties
- `_osm_value`: Together with `_osm_key`, they form a 'query' to fetch OSM data. Ex: town, primary_roads, river etc. Need to exist alongside the other OSM properties
- `_osm_type`: Type of layer to be downloaded from OSM. Options: points, lines, multilines to multipolygons. Need to exist alongside the other OSM properties.

### Controlling a vector layer

Open Layer Properties. Let's work with the labels, for example. First, define a basic style that you like. Then in **Rendering** section, go to **Show Label**, **Data defined override** and click on **Edit** option to open the Expressions screen.

![Apply Data defined override to a label visibility](/images/step_controlling_layer1.png)

Let's insert one of the control functions provided by the plugin. All these functions are under 'Webmap - General' and 'Webmap - Visibility'.

Enter the following expression:

```
controlVisibility(@zoom_level)
```

Apply the style and go back to the canvas. Note that the features will only be visible in the defined range, between 9 and 15. The interesting thing is that you can create the `_zoom_min` and `_zoom_max` fields on the layer and set a specific value for one of the features, and these values ​​will only be valid for that feature. For example, if you set the range 8-16 just for feature X, only it will be visible at zoom levels 8 and 16.

Let's now use another function, one that works with Percentiles. It's a way to make features visible little by little. For example, at zoom 9, only 5% of the most populated villages will be visible; at the next level, it will be 15% of the villages with the highest population... and so on. This percentage value is called a percentile.

So here's the function that controls the visibility by Percentiles.

```
controlVisibilityByPercentilesIncrement(@zoom_level, 'population', 5, 10)
```

Explaining the arguments:

- 1st parameter: current zoom level.
- 2nd parameter: name of the attribute to be considered in the calculations.
- 3thd parameter: Minimum percentile (5%)
- 4th parameter: Percentile increment at each zoom level (10%).

### Automatically applying styles

Every time you click the ![](/images/apply_style.png) icon, a style will be applied to each tagged layer. Which style will be applied depends on `_style` property value assigned to the tag.

### Structure: rearranging layers

When you are done with the structure (arrangement) of your map layers, go to Settings -> Structure, click on Update and then Apply. The organization of the layers will then be recorded. Every time you click on the ![](/images/apply_structure.png) icon, your project's layers will be reorganized (and groups created if necessary).

### Generating Shaded Relief

Our shaded relief tool creates two layers, in the order they need to be: one above the other. It works like this because each layer uses a light source with a different azimuth and different blend modes. This brings more details to the final shaded relief.

In addition, both layers receive the Aerial Perspective effect: the higher the layer, the greater the contrast. This is good for cartography because usually the lower portions of a region are where cities, highways etc are located... less contrast, easier to recognize all these elements. Here is a good article about Aerial Perspective: http://www.reliefshading.com/design/aerial-perspective/.

Click on ![](/images/relief_creator.png) button to generate a Shaded Relief.
