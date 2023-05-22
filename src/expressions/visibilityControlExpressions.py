from qgis.core import qgsfunction, NULL, QgsExpressionContext
from ..utils.webmapCommons import Utils
import numpy as np

@qgsfunction(args='auto', group='Webmap - Visibility', referenced_columns=['_zoom_min','_zoom_max'])
def controlVisibility(feature, parent, context):
    """
    controlVisibilityOffset(currentZoom)<br><br>
    Controls features visibility by _zoom_min and _zoom_max properties. If a feature don't have these properties or they are NULL, 
    then the TAG property will be used. Note that this function do not override the 'Scale Dependent Visibility' option of a layer.
    <br>
    <h2>Parameters</h2>
    <ul>
      <li><b>currentZoom</b>: current zoom level. Leave it with the value of @zoom_level variable.</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    controlVisibility(@zoom_level)
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    minZoom = int(Utils.getVariable(key, '_zoom_min', feature)[1])
    maxZoom = int(Utils.getVariable(key, '_zoom_max', feature)[1])

    return 1 if currentZoom >= minZoom and currentZoom <= maxZoom else 0

@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityOffset(minZoomOffset, maxZoomOffset, feature, parent, context):
    """
    controlVisibilityOffset(currentZoom, minZoomOffset, maxZoomOffset)<br><br>
    Controls features visibility by _zoom_min and _zoom_max properties. This function adds an offset value to the _zoom_min and _zoom_max values,
    only for the current style.If a feature don't have these properties or they are NULL, then the TAG property will be used.
    Note that this function do not override the 'Scale Dependent Visibility' option of a layer.
    <br>
    <h2>Parameters</h2>
    <ul>
      <li><b>currentZoom</b>: current zoom level. Leave it with the value of @zoom_level variable.</li>
      <li><b>minZoomOffset</b>: value to be added to _zoom_min property.</li>
      <li><b>maxZoomOffset</b>: value to be added to _zoom_max property.</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    The following example increases the visibility interval of a layer that is controlled by _zoom_min and _zoom_max properties.
    <br>
    controlVisibility(@zoom_level, -1, 1)
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    minZoom = int(Utils.getVariable(key, '_zoom_min', feature)[1]) + minZoomOffset
    maxZoom = int(Utils.getVariable(key, '_zoom_max', feature)[1]) + maxZoomOffset 

    return 1 if currentZoom >= minZoom and currentZoom <= maxZoom else 0

@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityByPercentilesArray(attribute, percentiles, feature, parent, context: QgsExpressionContext):
    """
    controlVisibilityByPercentilesArray(currentZoom, attribute, percentiles)<br><br>
    Controls features visibility by using an array of percentiles. For example, say you have a vector layer containing cities and its populations. 
    So using the array arr = [5,25,50,100] and considering _zoom_min = 10 and _zoom_max = 13, it will produce the following results:

    <ul>
      <li><b>zoom level less than 10</b>: 5% of the cities with highest population will be shown</li>
      <li><b>zoom level = 10</b>: 5% of the cities with highest population will be shown</li>
      <li><b>zoom level = 11</b>: 25% of the cities with highest population will be shown</li>
      <li><b>zoom level = 12</b>: 50% of the cities with highest population will be shown</li>
      <li><b>zoom level = 13</b>: 100% of the cities with highest population will be shown</li>
      <li><b>zoom level bigger than 13</b>: 100% of the cities with highest population will be shown</li>
    </ul>

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>currentZoom</b>: current zoom level. Leave it with the value of @zoom_level variable.</li>
      <li><b>attribute</b>: numeric attribute name that will be used for percentile calculations (field 'population' in the case above).</li>
      <li><b>percentiles</b>: array of percentiles OR a property name. Ex: array(5,25,5,100) ou '_cities_percentiles_array'</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    controlVisibilityByPercentilesArray(@zoom_level, array(5,25,50,100))
    controlVisibilityByPercentilesArray(@zoom_level, '_cities_percentiles_array')
    """
        
    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        maxAttrCacheVar = context.cachedValue('_layer_max')

        if maxAttrCacheVar is not None:
            maxAttr = maxAttrCacheVar
        else:
            idx = layer.fields().indexFromName(attribute)
            maxAttr = float(layer.maximumValue(idx))
            context.setCachedValue('_layer_max', maxAttr)

        currentZoom = context.variable('zoom_level') + 1
        minZoom = int(Utils.getVariable(key, '_zoom_min', feature)[1])
        maxZoom = int(Utils.getVariable(key, '_zoom_max', feature)[1])

        if currentZoom >= minZoom and currentZoom <= maxZoom:
            attrValue = float(feature[attribute])  
            attrCollection = []

            if currentZoom == maxZoom and (attrValue == NULL or attrValue is None):
                return 1
            
            _percentiles = Utils.strToArrayOfNumbers(Utils.getVariable(key, percentiles, feature)[1]) if isinstance(percentiles, str) else percentiles


            fromMinOffset = currentZoom - minZoom
            percentileIndex = Utils.boundValue(fromMinOffset, 0, len(_percentiles) - 1)
            percentile = _percentiles[percentileIndex]
            
            percentileVar = f'_layer_percentile_{percentile}'
            percentileResult = context.cachedValue(percentileVar)

            if percentileResult is not None:
                percentileResult = percentileResult
            else:
                for f in layer.getFeatures():
                    vAttr = f[attribute]
                    if (vAttr != NULL):
                        attrCollection.append(maxAttr - float(vAttr))

                percentileResult = np.percentile(attrCollection, percentile)
                context.setCachedValue(percentileVar, percentileResult)

            inverseAttr = maxAttr if attrValue == NULL else maxAttr - attrValue
            return 1 if inverseAttr <= percentileResult else 0
        else:
            return 0
    except Exception as e:
        return 0
    
@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityByPercentilesIncrement(attribute, minPercentile, increment, feature, parent, context):
    """
    controlVisibilityByPercentilesIncrement(currentZoom, attribute, minPercentile, increment)<br><br>
    Controls features visibility by using a minimum percentile value that will be automaticaly incremented. 
    For example, say you have a vector layer containing cities and its populations. So using minPercentile = 5, increment = 5 and 
    considering _zoom_min = 10 and _zoom_max = 13, it will produce the following results:

    <ul>
      <li><b>zoom level less than 10</b>: 5% of the cities with highest population will be shown</li>
      <li><b>zoom level = 10</b>: 5% of the cities with highest population will be shown</li>
      <li><b>zoom level = 11</b>: 10% of the cities with highest population will be shown</li>
      <li><b>zoom level = 12</b>: 15% of the cities with highest population will be shown</li>
      <li><b>zoom level = 13</b>: 20% of the cities with highest population will be shown</li>
      <li><b>zoom level bigger than 13</b>: 20% of the cities with highest population will be shown</li>
    </ul>

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>currentZoom</b>: current zoom level. Leave it with the value of @zoom_level variable.</li>
      <li><b>attribute</b>: numeric attribute name that will be used for percentile calculations (field 'population' in the case above).</li>
      <li><b>minPercentile</b>: minimum percentile number OR a property name. Ex: 5 ou '_cities_min_percentile'</li>
      <li><b>increment</b>: value to be added to minPercentile at each zoom level. Ex: 5 ou '_cities_increment_percentile'</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    controlVisibilityByPercentilesIncrement(@zoom_level, 5, 5)
    controlVisibilityByPercentilesIncrement(@zoom_level, '_cities_min_percentile', '_cities_increment_percentile')
    """

    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        maxAttrCacheVar = context.cachedValue('_layer_max')

        if maxAttrCacheVar is not None:
            maxAttr = maxAttrCacheVar
        else:
            idx = layer.fields().indexFromName(attribute)
            maxAttr = float(layer.maximumValue(idx))
            context.setCachedValue('_layer_max', maxAttr)

        currentZoom = context.variable('zoom_level') + 1
        minZoom = int(Utils.getVariable(key, '_zoom_min', feature)[1])
        maxZoom = int(Utils.getVariable(key, '_zoom_max', feature)[1])
        _increment = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

        if currentZoom >= minZoom and currentZoom <= maxZoom:
            attrValue = float(feature[attribute])
            attrCollection = []

            if currentZoom == maxZoom and (attrValue == NULL or attrValue is None):
                return 1
        
            fromMinOffset = currentZoom - minZoom if currentZoom >= minZoom else 0
            percentile = minPercentile + (_increment*fromMinOffset)
            percentileVar = f'_layer_percentile_{percentile}'
            percentileResult = context.cachedValue(percentileVar)

            if percentileResult is not None:
                percentileResult = percentileResult
            else:
                for f in layer.getFeatures():
                    vAttr = f[attribute]
                    if (vAttr != NULL):
                        attrCollection.append(maxAttr - float(vAttr))

                percentileResult = np.percentile(attrCollection, percentile)
                context.setCachedValue(percentileVar, percentileResult)

            inverseAttr = float(maxAttr) if attrValue == NULL else float(maxAttr) - float(attrValue)
            return 1 if inverseAttr <= percentileResult else 0
        else:
            return 0
    except Exception as e:
        return 0
