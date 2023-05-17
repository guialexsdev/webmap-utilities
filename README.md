#Webmap Utilities - A QGis plugin for webmap building

##What it does?

The Webmap Utilities plugin offers tools to facilitate the construction of webmaps, that is, dynamic maps whose content varies according to the scale.

We encourage you to use our tagging system to manage your projects (we'll talk about that in the next section), but you can use some of the functionality separately if you prefer.

Here is a list of features we provide:

* Work with zoom levels instead of scales: we added a selector similar to the original QGis scales selector, but you select a zoom level instead of a scale.
* You can set the visibility (zoom level) of one or more layers or even a group of layers.
* The plugin offers visibility control functions, by feature, to be used in the Data Defined Override option of the layers. For example: you might want each additional zoom level to show 10% more of the most populous cities on the map.
* We also offer functions for numerical control. For example: you might want the size of the labels to increase, at each zoom level, uniformly between 7pt to 12pt.
* With the tagging system we offer, it is easier to create templates and reproduce the idea of ​​previous maps. With a few clicks you can:
  - Re-organize your layers according to a previously defined structure.
  - Apply styles (QML files) to all tagged layers (raster or vector).
  - Download OSM data of all tagged vector layers.

##Quick Tutorial


###Adding a tag

The tagging system is simple. First you define the category of each layers. For example, we might have multiple layers, perhaps from different sources, containing the villages in a given region. While all of these layers might have different names, they could all be categorized as 'village', as they will likely share several settings (style settings, for example).

The second step is to plan how the marked layers will be recognized. Currently, you can do this in 2 ways:

- Renaming your layer to contain the chosen category (or tag) at the beginning of the name. In our example, the name of one of the layers would be **villages_source1**, the other would be **villages_source2**.

- Inserting a Category in the layer's metadata. Just go to Properties -> Metadata -> Categories. In this case, it could just be 'villages'.

Now just go to the plugin's **Settings** option and register the tag. Don't forget to select the tag identification mode at the bottom of the screen.

###Adding a property to a tag

The next step is to insert some properties for the created tag. There are some predefined ones (but you can create your own too). Let's use, for example, the **_zoom_min** and **_zoom_max** properties. Together they control the range of scale, or rather zoom levels, at which a feature or all of them will be visible.

To add a property to the tag, go to the Settings -> Tags screen and right-click on the tag name. Click **Add Property...**. Select **_zoom_min**, enter the number 9 and click OK. Repeat the process for the **_zoom_max** property, but choosing the number 15, for example. That is, the features of our layers will only be visible between levels 9 and 15 of zoom.

At this time, the property is not yet taking effect. For that we need the next step. Let's go!

###Controlling a vector layer

Open Layer Properties. Let's work with the labels, for example. Define a basic style that you like. In the **Rendering** section, go to **Show Label** and click on **Edit** to open the Expressions screen.

Let's insert one of the control functions that the plugin provides. All these functions are under the headings 'Webmap - General' and 'Webmap - Visibility'.

Enter the following expression:

controlVisibility(@zoom_level)

Apply the style and go back to the canvas. Note that the features will only be visible in the defined range, between 9 and 15. The interesting thing is that you can create the **_zoom_min** and **_zoom_max** fields on the layer and set a specific value for one of the features, and these values ​​will only be valid for that feature. For example, if you set the range 8-16 just for feature X, only it will be visible at zoom levels 8 and 16.

Let's now use another function, one that works with Percentiles. It's a way to make features visible little by little. For example, at zoom 9, only 5% of the most populated villages will be visible; at the next level, it will be 15% of the villages with the highest population... and so on. This percentage value is called a percentile.

So here's the function that controls the visibility by Percentiles.

controlVisibilityByPercentilesIncrement(@zoom_level, 'population', 5, 10)

Explaining the arguments:

- 1st parameter: current zoom level.
- 2nd parameter: name of the attribute to be considered in the calculations.
- 3thd parameter: Minimum percentile (5%)
- 4th parameter: Percentile increment at each zoom level (10%).

###Other useful properties

- **_style**: add this property to your tag and choose a style file (QML). Every time you click the {X} icon, the style will be applied to the selected layer.
- **_osm_key**: Used to automatically download OSM data when clicking the {Y} icon. It's the key to research. Ex: place, highway, waterway etc. Need to exist alongside the other OSM properties
- **_osm_value**: Used to automatically download OSM data when clicking the {Y} icon. Is the value of the chosen key. Ex: town, primary_roads, river etc. Need to exist alongside the other OSM properties
- **_osm_type**: Type of layer to be downloaded from OSM. Options: points, lines, multilines to multipolygons. Need to exist alongside the other OSM properties.

###Rearrange layers

When you are done with the structure of your map layers, go to Settings -> Structure, click on Update and then Apply. The organization of the layers will then be recorded.

Every time you click on the {Z} icon, your project's layers will be reorganized (and groups created if necessary).

###Generating Shaded Relief

Our shaded relief tool, or hillshade, creates two layers, to be placed one above the other. It works like this because each layer uses a light source with a different azimuth. This brings more detail to the final shaded relief.

In addition, both layers receive the Aerial Perspective effect: the higher the layer, the greater the contrast. This is good for cartography because usually the lower portions of a region are where cities, highways etc are located... less contrast, easier to recognize all these elements.