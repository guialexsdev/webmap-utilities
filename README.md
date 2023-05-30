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

- Minimum QGis version 3.28
- You need to install QuickOSM plugin before installing Webmap Utilities.

## Installing

Click here to download the zip file. To install, open Qgis and go to Plugins -> Manage and Install Plugins -> Install from ZIP.

## Quick Tutorial

Before continuing, download this vector layer and this style (QML). The layer contains cities of Pensilvania state, EUA. It will be used in this tutorial.

### Preparing your project

You can get access to the plugin's tools by just right-clicking anywhere in icons toolbar and choosing **Webmap Plugin Toolbar**. Then, click ![](/images/configure_project.png) button to initialize your project. It will save some predefined settings to your project variables and add predefined scales that corresponds to the zoom level range of 0-20. You only need to do it once and after that all buttons will be available.

![](/images/toolbar_only.png)

### Controlling visibility of a layer

One of the first problems when designing a webmap is to decide what will be shown at each zoom level or scale. Say that our cities has a visibility range that begins at level 5 and finishes at level 15. Of course you can do this by just using the **Scale dependent visibility** option that Qgis already offer, but you need to memorize which scale corresponds to which zoom level. To avoid it you may use our **Set layer zoom level visibility** tool, that works with zoom levels instead of scales. Right-click a layer to get access to that option.

![](/images/set_visibility_by_zoom_level.png)

But what if you add another layer of cities to the project? You will certainly need to set visibility again, one more time for each extra layer you add. Not a big problem yet, but it will be, as soon as you have a map with many layers that need to be replicated to another area. And what if you need to show at level 4 only a single feature, an important feature? To resolve these and other problems we propose a tagging system: tags that identifies your layers and control them by default or user defined properties. So, let us define a tag and 2 properties to control the visibility of our layer.

![](/images/city_tag_properties.png)

Click ![](/images/settings.png) **Settings** button. The first screen is the one that manages all tags of a project. Click ![](/images/symbologyAdd.png) **Add new tag...** to insert a new tag. Give it meaningful name like **city**. And before proceed, make sure that our layer begins with the word **city**, that is how the plugin recognize that a layer belongs to a tag. Now right click the tag name and then **Add property**. Open the list of properties and select `_zoom_min`. In value field type the number 5. Every layer tagged with the word **city** will only be visbile at zoom level 5. Click OK and repeat the process to add the property `_zoom_max` with value 15. Exit Settings screen pressing OK to see the result. Now go to the labels properties of the layer and then to **Rendering** properties. Edit Data Defined Override of **Show label** option and type the following function:

`visibilityByZoomRange('_zoom_min', '_zoom_max')`

![](/images/normal_visibility.png)

Go back to the canvas and zoom in and zoom out in order to see the results. In fact, visually we have the same effect as before, but the advantage is that now every layer tagged as **city** will only become visible in the range we defined with zoom min and zoom max properties.

Now say that you want Philadelphia city to become visible at level 4. You can do it by adding **to the layer** an attribute called `_zoom_min` and giving the value 4 only to Philadelphia feature (and NULL to all other features). It works because feature properties are preferred over global properties.

**IMPORTANT**: if don't want to use a property name as function paramenter, it's ok to use numbers, like below:

`visibilityByZoomRange(5, 15)`

Always remember that most of our functions accepts a number OR a property name.

### Controlling visibility with percentiles

When you have hundred of features with labels, possibly overlapping each other, Qgis will hide some of them to make the map less crowded. But this is done without any criteria that helps user to understand the map. So we'll try to help Qgis in this matter by showing just a portion of feature at each zoom level: the higher the population of a city, the sooner it will be visible on the map.

To implement that strategy, go to **Show label** option set another function:

`visibilityByPercentilesIncrement('_zoom_min', '_zoom_max', 'population', 1, 10)`

![](/images/percentiles_increment_1.png)

Here is what this function does: at first zoom level available (= 5), 1% of the highest population cities will be visible. At the next zoom level, 1% + 10% of the highest population will be visible. From zoom level 15 onwards, 100% of the cities will be visible on the map. And if you have a list of predefined percentiles, you can use a similar function called controlVisibilityByPercentilesArray:

`visibilityByPercentilesArray('_zoom_min', '_zoom_max', 'population', array(1,20,50,100))`

Using the function above, at first zoom level 1% of cities will be visible; next, 1 + 20%...

### Controlling other styling parameters

It is sometimes useful to increase label size as the zoom level increases. This is because as the scale increases, the label becomes smaller and smaller relative to the area it represents. To automatically increase label size as the zoom level increases, go to the layer Properties -> Labels -> Text and add the following function to the Data Defined Override option of **Size** field:

`incrementPerZoom('_zoom_min', '_zoom_max', 1, 7, 15)`

The first number indicates an ammount of increment per zoom level. The second number is the minimum size, when zoom level = 5 (remeber we defined number 5 as the minimum zoom level). The third number is the maximum size. So, our labels begins at size = 7 and will growing up to size = 15, adding 1 at each level. You can use the alternative `incrementPerZoomOffset('_zoom_min', '_zoom_max', 1, 7, 8)`, where the third parameter means an offset from minimum size. Finally, you can use array, as we did in last section:

`arrayItemPerZoom('_zoom_min', '_zoom_max', array(7,8,9,10,11,12,13,14,15))`

Another function, if you don't care about how much the value will increase, is the following:

`normalizeZoomRange('_zoom_min', '_zoom_max', 7, 15)`

Basically, normalizeZoomRange performs a min-max normalization: transforms a zoom range into the specified value range (a different scale). Use this method to achieve a smooth size transition between zoom levels.

Now let's think about cities again. Obviously, there are cities more important than others in terms of population. It will be a good idea do give a bigger font size to bigger cities. So go to the layer Properties -> Labels -> Text and add the following function to the Data Defined Override option of **Size** field:

`normalizeZoomRangeOffset(scaleExponential('population', 50, 0.5, 3, 8), 7)`

Note that we are using normalizeZoomRangeOffset (MinMax normalization), so we don't care about the increase value per zoom level. Just two parameters are required: min size and offset from min size. And note that we are using another function as minSize parameter of normalizeZoomRangeOffset: the function `scaleExponential('population', 50, 0.5, 3, 8)`. It is telling us that the minimum size is variable in a exponential fashion: less populous cities begins at size = 3, while most populous cities begins at size = 8. It works just like `scale_exp`, provided by QGis, but here you don't need to know the exact value of the highest and lowest populations. About the second parameter: if you have cities with population much higher than others you may want to decrease this value to get better visual results. Finally, the second argument of `normalizeZoomRangeOffset` is the offset relative to minimum value: if minimum value is 3, then size will increase up to 7 + 3 = 10; if minimum value is 8, then size will increase up to 7 + 8 = 15.

![](/images/scale_exp_min_max_offset2.png)

Understand that you can use all the above functions not only for size field of a label. You can use it to transparency fields, color fields (in this case using arrays only) etc.

### Automate OSM download using `_osm_query` property

Whenever you add `_osm_query` to a tag, you are describing what vector layers need to be downloaded from OSM. Such tag is used in our OSM Downloader tool to download vector data of all tagged layers at once.

Go to ![](/images/settings.png) **Settings** and then create another tag called **road**. Right-click the new tag and then **Add property**. Select  `_osm_query`. You can add a list of items. In this case, list item must be in the format `<key>=<value>`. Add the following items to the list:

* highway=primary
* highway=primary_link
* highway=primary_trunk

Now add the property `_geometry_type` e choose the value `lines`. We are just telling OSM downloader the geometry type of roads (they are lines, of course).

![](/images/osm_road.png)

Apply and close the Settings dialog and click on ![](/images/osm.png) button. Choose a CRS and an extent. Field **Tags** will be by default initialized with all tags that have `_osm_query` and `_geometry_type` properties, as they are required to download data from OSM. Click Run to start downloading.

### Automate style application using `_style` property

The `_style` property tells what style should be applied to every layer of a same tag. Just add another property to one or all tags, selecting `_style` property and choosing a QML file. Every time you click the ![](/images/apply_style.png) icon, a style will be applied to each tagged layer.

### Re-arrange the layer tree

It is important to keep you layer tree organized and standardized across projects. If you got to ![](/images/settings.png) **Settings**  -> **Structure** and click **Update** button, the arrangement of your tagged layers will be recorded. Then every time you click ![](/images/apply_structure.png) **Apply Structre** button, all tagged layers will be organized using the recorded layers arrangement.   

### Using your own properties

Its possible to create your own properties and use, for example, as argument in one of our custom functions. For example, instead of:

`IncrementByZoomRange(5, 15, 1, 7, 15)`

You can can create property `label_size_min` and use it like this:

`IncrementByZoomRange(5, 15, 1, 'label_size_min', 15)`

(And remember that you can create an attribute called `label_size_min` and give a different value to a single feature.)

To create a property, go to ![](/images/settings.png) **Settings** -> **Properties** -> **Add new property**.

![](/images/add_property.png)

### Generating a Shaded Relief

**Using the tagging system is not required here**

Our shaded relief tool creates two layers, in the order they need to be: one above the other. It works like this because each layer uses a light source with a different azimuth and different blend modes. This brings more details to the final shaded relief.

In addition, both layers receive the Aerial Perspective effect: the higher the layer, the greater the contrast. This is good for cartography because usually the lower portions of a region contains more cities, highways etc and less contrast means easier to recognize all these elements. Here is a good article about Aerial Perspective: http://www.reliefshading.com/design/aerial-perspective/.

Click on ![](/images/relief_creator.png) button to generate a Shaded Relief. The option **Aerial Perspective Intensity**, always between 0 and 100, increase/decrease the contrast between higher and lower altitudes. And the option **Angle Between Light Sources** controls the angle between the light sources: a number between 30 - 70 is generally a good choice; values close to 180 usually gives an undesirable plastic effect.

Remember that layers are generated in the order they need to be, so its a good idea to rename them to something like "hillshade top" and "hillshade bottom". After these steps, put you colored DEM file below 'hillshade bottom' layer.

### Exporting settings

If you are going to replicate your map, it's important to export you Webmap Plugin Project. You can do that by just click ![](/images/settings.png) **Settings** -> **Export**. Everything will be included in a file wit `.wpc` extension, even the styles assigned to `_style` property.

### Import settings

To import settings just click ![](/images/settings.png) **Settings** -> **Import**. Because style files may be present in a .wpc file, you might be asked what to do with QML file: you may choose a folder to save them; or just use them as temporary files.

### Example Project

Now it's your time try it out. Download this wpc file to replicate a map similar to the map below:

![](/images/example_map.png)

Just follow these steps in order to create the map:

* Download a DEM file of the region of interest
* Reproject it to EPSG:3857
* ![](/images/relief_creator.png) Generate a Shaded Relief
* ![](/images/settings.png) Import settings (.wpc file we provided as example)
* ![](/images/osm.png) Download OSM data
* ![](/images/apply_structure.png) Re-arrange layers
* ![](/images/apply_style.png) Apply styles