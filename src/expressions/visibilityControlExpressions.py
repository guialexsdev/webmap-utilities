from qgis.core import qgsfunction, NULL, QgsExpressionContext
from ..utils.logUtils import error
from ..utils.webmapCommons import Utils
import numpy as np
import traceback

@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibility(minZoom, maxZoom, feature, parent, context):
    """
    controlVisibilityOffset()<br><br>
    Controls features visibility by _zoom_min and _zoom_max properties. If a feature don't have these properties or they are NULL, 
    then the TAG property will be used. Note that this function do not override the 'Scale Dependent Visibility' option of a layer.
    <br>
    <h2>Example usage:</h2>
    controlVisibility()
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)

    return 1 if currentZoom >= _minZoom and currentZoom <= _maxZoom else 0

@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityOffset(minZoom, maxZoom, minZoomOffset, maxZoomOffset, feature, parent, context):
    """
    controlVisibilityOffset(minZoomOffset, maxZoomOffset)<br><br>
    Controls features visibility by _zoom_min and _zoom_max properties. This function adds an offset value to the _zoom_min and _zoom_max values,
    only for the current style.If a feature don't have these properties or they are NULL, then the TAG property will be used.
    Note that this function do not override the 'Scale Dependent Visibility' option of a layer.
    <br>
    <h2>Parameters</h2>
    <ul>
      <li><b>minZoomOffset</b>: value to be added to _zoom_min property.</li>
      <li><b>maxZoomOffset</b>: value to be added to _zoom_max property.</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    The following example increases the visibility interval of a layer that is controlled by _zoom_min and _zoom_max properties.
    <br>
    controlVisibility(-1, 1)
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom) + minZoomOffset
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom) + maxZoomOffset

    return 1 if currentZoom >= _minZoom and currentZoom <= _maxZoom else 0

@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityByPercentilesArray(minZoom, maxZoom, attributeName, percentiles, feature, parent, context: QgsExpressionContext):
    """
    controlVisibilityByPercentilesArray(attribute, percentiles)<br><br>
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
      <li><b>attribute</b>: numeric attribute name that will be used for percentile calculations (field 'population' in the case above).</li>
      <li><b>percentiles</b>: array of percentiles OR a property name. Ex: array(5,25,5,100) ou '_cities_percentiles_array'</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    controlVisibilityByPercentilesArray(array(5,25,50,100))
    controlVisibilityByPercentilesArray('_cities_percentiles_array')
    """
        
    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = context.cachedValue('_layer_all_attrs_values')

        if allAttrValues is None:            
            allAttrValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
            context.setCachedValue('_layer_all_attrs_values', allAttrValues)

        maxAttrCacheVar = context.cachedValue('_layer_max')

        if maxAttrCacheVar is not None:
            maxAttr = maxAttrCacheVar
        else:
            maxAttr = max(allAttrValues)
            context.setCachedValue('_layer_max', maxAttr)

        currentZoom = context.variable('zoom_level') + 1
        _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
        _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)

        if currentZoom >= _minZoom and currentZoom <= _maxZoom:
            attrValue = Utils.getFloatAttribute(feature, attributeName)

            if currentZoom == _maxZoom and (attrValue == NULL or attrValue is None):
                return 1
            
            _percentiles = Utils.strToArrayOfNumbers(Utils.getVariable(key, percentiles, feature)[1]) if isinstance(percentiles, str) else percentiles

            fromMinOffset = currentZoom - _minZoom
            percentileIndex = Utils.boundValue(fromMinOffset, 0, len(_percentiles) - 1)
            percentile = _percentiles[int(percentileIndex)]
            
            percentileVar = f'_layer_percentile_{percentile}'
            percentileResult = context.cachedValue(percentileVar)

            if percentileResult is None:
                percentileResult = np.percentile(allAttrValues, 100 - percentile)
                context.setCachedValue(percentileVar, percentileResult)

            return 1 if attrValue >= percentileResult else 0
        else:
            return 0
    except Exception as e:
        error(str(traceback.format_exc()))
        return 0
    
@qgsfunction(args='auto', group='Webmap - Visibility')
def controlVisibilityByPercentilesIncrement(minZoom, maxZoom, attributeName, minPercentile, increment, feature, parent, context):
    """
    controlVisibilityByPercentilesIncrement(attribute, minPercentile, increment)<br><br>
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
      <li><b>attribute</b>: numeric attribute name that will be used for percentile calculations (field 'population' in the case above).</li>
      <li><b>minPercentile</b>: minimum percentile number OR a property name. Ex: 5 ou '_cities_min_percentile'</li>
      <li><b>increment</b>: value to be added to minPercentile at each zoom level. Ex: 5 ou '_cities_increment_percentile'</li>
    </ul>
    <br>
    <h2>Example usage:</h2>
    controlVisibilityByPercentilesIncrement(5, 5)
    controlVisibilityByPercentilesIncrement('_cities_min_percentile', '_cities_increment_percentile')
    """

    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = context.cachedValue('_layer_all_attrs_values')

        if allAttrValues is None:            
            allAttrValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
            context.setCachedValue('_layer_all_attrs_values', allAttrValues)

        maxAttrCacheVar = context.cachedValue('_layer_max')

        if maxAttrCacheVar is not None:
            maxAttr = maxAttrCacheVar
        else:
            maxAttr = max(allAttrValues)
            context.setCachedValue('_layer_max', maxAttr)

        currentZoom = context.variable('zoom_level') + 1
        _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
        _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)
        _increment = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

        if currentZoom >= _minZoom and currentZoom <= _maxZoom:
            attrValue = Utils.getFloatAttribute(feature, attributeName)

            if currentZoom == _maxZoom and (attrValue == NULL or attrValue is None):
                return 1
        
            fromMinOffset = currentZoom - _minZoom if currentZoom >= _minZoom else 0
            percentile = Utils.boundValue(minPercentile + (_increment*fromMinOffset), minPercentile, 100)
            percentileVar = f'_layer_percentile_{percentile}'
            percentileResult = context.cachedValue(percentileVar)

            if percentileResult is not None:
                percentileResult = percentileResult
            else:
                percentileResult = np.percentile(allAttrValues, 100 - percentile)
                context.setCachedValue(percentileVar, percentileResult)

            return 1 if attrValue >= percentileResult else 0
        else:
            return 0
    except Exception as e:
        return 0
