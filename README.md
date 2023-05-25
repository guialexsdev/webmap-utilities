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

## Requirements and dependencies

- Minimum QGis version 3.28
- You need to install QuickOSM plugin before installing Webmap Utilities.

## Installing

In QGis, install Webmap Utilities through the menu **Plugins -> Manage and Install Plugins**. Search for 'Webmap Utilities' and install. It may be necessary, in the Settings tab in the plugin manager, to check the option **Show also Experimental Plugins**.

Acesse as ferramentas do plugin clicando com o botão direito do mouse em qualquer lugar na barra de ferramentas e selecionando **Webmap Utilities Toolbar**

![](/images/toolbar.png)

## Quick Tutorial

We built a tagging system to make it easy to replicate and standardize a map. Let's say you've made a map of a certain region and you liked the result. To replicate such  map for another region using Webmap Utilities it would take just a few clicks to: 

- Automatically download the OSM layers
- Automatically apply styles to all layers (vector or raster)
- Automatically organize the layer tree, in the right order

### Controlling visibility of a layer

Suppose we have a vector layer containing all cities of a certain region. Actually you don't need to suppose, click here to download all cities of Pensilvania State (EUA). Open it and give it a simple style showing labels only. One of the first problems when designing a webmap is to decide what will be shown at each zoom level or scale. Say that our cities has a visibility range that begins at level 5 and finishes at level 15. Of course you can do this by just setting the **Scale dependent visibility** option that Qgis already offer, but you need to memorize which scale corresponds to which zoom level. To avoid it you may use our **Set layer zoom level visibility** tool, that works with zoom levels instead of scales. Right-click a layer to get access to that option.

But what if you add another layer of cities to the project? You will certainly need to set visibility again, one more time for each extra layer you add. Not a big problem yet, but it will be, as soon as you have a map with many layers that need to be replicated to another area. And what if you need to show at level 4 only a single feature, an important feature? To resolve these and other problems we propose a tagging system: tags that identifies your layers and control them by default or user defined properties. So, let us define a tag and 2 properties to control the visibility of our layer.

Find and click ![](/images/settings.png) **Settings** button. The first screen is the one that manages all tags of a project. Click ![](/images/symbologyAdd.png) **Add new tag...** to insert a new tag. Give it meaningful name like **city**. And before proceed, make sure that our layer begins with the word **city**, that is how the plugin recognize that a layer belongs to a tag. Now right click the tag name and then **Add property**. Open the list of properties and select `_zoom_min`. In value field type the number 5. Every layer tagged with the word **city** will only be visbile at zoom level 5. Click OK and repeat the process to add the property `_zoom_max` with value 15. Exit Settings screen pressing OK to see the result. Now go to the labels properties of the layer and then to **Rendering** properties. Edit Data Defined Override of **Show label** option and type the following function:

`controlVisibility()`

Go back to the canvas and zoom in and zoom out in order to see the results. In fact, visually we have the same effect as before, but the advantage is that now every layer tagged as **city** will only become visible in the range we defined with zoom min and zoom max properties.

Now say that you want Philadelphia city to become visible at level 4. You can do it by adding to the layer an attribute called `_zoom_min` and giving the value 4 only to Philadelphia feature (and NULL to all other features). It works because feature properties are preferred over global properties.

### Controlling visibility with percentiles

When you have hundred of features with labels, possibly overlapping each other, Qgis will hide some of them to make the map less crowded. But this is done without any criteria that helps user to understand the map. So we'll try to help Qgis in this matter by showing just a portion of feature at each zoom level: the higher the population of a city, the sooner it will be visible on the map.

To implement that strategy, go to **Show label** option set another function:

`controlVisibilityByPercentilesIncrement('population', 1, 10)`

Here is what this function does: at first zoom level available (= 5), 1% of the highest population cities will be visible. At the next zoom level, 1% + 10% of the highest population will be visible. From zoom level 15 onwards, 100% of the cities will be visible on the map. And if you have a list of predefined percentiles, you can use a similar function called controlVisibilityByPercentilesArray:

`controlVisibilityByPercentilesArray('population', array(1,20,50,100))`

Using the function above, at first zoom level 1% of cities will be visible; next, 1 + 20%...

### Controlling other styling parameters

It is sometimes useful to increase label size as the zoom level increases. This is because as the scale increases, the label becomes smaller and smaller relative to the area it represents. To automatically increase label size as the zoom level increases, go to the layer Properties -> Labels -> Text and add the following function to the Data Defined Override option of **Size** field:

`controlByIncrement(1, 7, 15)`

The first number indicates an ammount of increment per zoom level. The second number is the minimum size, when zoom level = 5 (remeber we defined number 5 as the minimum zoom level). The third number is the maximum size. So, our labels begins at size = 7 and will growing up to size = 15, adding 1 at each level. You can use the alternative `controlByIncrementRelativeMax(1, 7, 8)`, where the third parameter means an offset from minimum size. Finally, you can use array, as we did in last section:

`controlByArray(array(7,8,9,10,11,12,13,14,15))`

Another function, if you don't care about how much the value will increase, is the following:

`controlByMinMaxNorm(7,15)`

Basically, min-max normalization will be applied to your value range (7-15) considering zoom min and zoo max previously defined. You will see labels size uniformly increasing as zoom goes up.

Now lets think about cities again. Obviously, there are cities more importante than others in terms of population. It will be a good idea do give a bigger font size to bigger cities. So go to the layer Properties -> Labels -> Text and add the following function to the Data Defined Override option of **Size** field:

`controlByMinMaxNormRelativeMax(scaleExponential('population', 50, 0.5, 3, 8), 7)`

Note that we are using MinMax normalization, so we don't care about the increase value per zoom level. Just two parameters are required: min size and max size. And note that the function `scaleExponential('population', 50, 0.5, 3, 8)` is telling us that the minimum size is variable in a exponential fashion: less populous cities begins at size = 3; most populous cities begins at size = 8. It works just like `scale_exp`, provided by QGis, but here you don't need to know the exact value of the highest and lowest populations. Another difference is the second parameter: if you have cities with population absurdly higher than other you may want to decrease this value. Finally, the second argument of `controlByMinMaxNormRelativeMax` is the offset relative to minimum value: if minimum value is 3, then size will increase up to 7 + 3 = 10; if minimum value is 8, then size will increase up to 7 + 8 = 15.

Understand that you can use all the above function not only for size field of a label. You can use it to transparency fields, color fields (in this case using arrays only) etc.

### Automate OSM download using `_osm_query` property

Whenever you add `_osm_query` to a tag, you are describing what vector layers need to be downloaded from OSM. Such tag is used in our OSM Downloader tool to download vector data of all tagged layers at once.

Go to ![](/images/settings.png) **Settings** and then create another tag called **road**. Right-click the new tag and then **Add property**. Select  `_osm_query`. You can add a list of items. In this case, list item must be in the format `<key>=<value>`. Add the following items to the list:

* highway=primary
* highway=primary_link
* highway=primary_trunk

Now add the property `_geometry_type` e choose the value `lines`. We are just telling OSM downloader the geometry type of roads (they are lines, of course).

Apply and close the Settings dialog and click on ![](/images/osm.png) button. Choose a CRS and an extent. Field **Tags** will be by default initialized with all tags that have `_osm_query` and `_geometry_type` properties, as they are required to download data from OSM. Click Run to start downloading.

### Automate style application using `_style`property

The `_style` property tells what style should be applied to every layer of a same tag. Just add another property to one or all tags, selecting `_style` property and choosing a QML file. Every time you click the ![](/images/apply_style.png) icon, a style will be applied to each tagged layer.

### Using your own properties

Its possible to create your own properties and use, for example, as argument in one of our custom functions. For example, instead of:

`controlByIncrement(1, 7, 15)`

You can can create property `label_size_min` and use it like this:

`controlByIncrement(1, 'label_size_min', 15)`

(And remember that you can create an attribute called `label_size_min` and give a different value to a single feature.)

To create a property, go to ![](/images/settings.png) **Settings** -> **Properties** -> **Add new property**.

### Generating a Shaded Relief

**Using the tagging system is not required here**

Our shaded relief tool creates two layers, in the order they need to be: one above the other. It works like this because each layer uses a light source with a different azimuth and different blend modes. This brings more details to the final shaded relief.

In addition, both layers receive the Aerial Perspective effect: the higher the layer, the greater the contrast. This is good for cartography because usually the lower portions of a region contains more cities, highways etc and less contrast means easier to recognize all these elements. Here is a good article about Aerial Perspective: http://www.reliefshading.com/design/aerial-perspective/.

Click on ![](/images/relief_creator.png) button to generate a Shaded Relief. The option **Aerial Perspective Intensity**, always between 0 and 100, increase/decrease the contrast between higher and lower altitudes. And the option **Angle Between Light Sources** controls the angle between the light sources: a number between 30 - 70 is generally a good choice; values close to 180 usually gives an undesirable plastic effect.

Remember that layers are generated in the order they need to be, so its a good idea to rename them to something like "hillshade top" and "hillshade bottom".

### Exporting settings

If you are going to replicate your map, it's important to export you Webmap Plugin Project. You can do that by just click ![](/images/settings.png) **Settings** -> **Export**. Everything will be included in a file wit `.wpc` extension, even the styles assigned to `_style` property.

### Import settings

To import settings just click ![](/images/settings.png) **Settings** -> **Import**. Because style may be present int a .wpc file, you might be asked what to do with QML file: you may choose a folder to save them; or just use them as temporary files.
