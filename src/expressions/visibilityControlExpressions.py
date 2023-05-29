import numpy as np
import traceback
from qgis.core import qgsfunction, NULL, QgsExpressionContext, QgsFeature
from ..utils.logUtils import error, info
from ..utils.webmapCommons import Utils

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByZoomRange(minZoom, maxZoom, feature, parent, context):
    """
    visibilityByZoomRange()<br><br>
    Controls features visibility by minZoom and maxZoom range. If current zoom level is outside the given range, feature won't be visible.
    Note that this function do not override the 'Scale Dependent Visibility' option of a layer.
    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>maxZoom</b>: maximum zoom (inclusive)</li>
    </ul>

    </br>
    <h2>Example usage:</h2>
    visibilityByZoomRange(5, 10) -> feature will be visible between zoom level 5 (inclusive) and 10 (inclusive).
    visibilityByZoomRange('_zoom_min', '_zoom_max') -> same as before, but using properties.
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)

    return 1 if currentZoom >= _minZoom and currentZoom <= _maxZoom else 0

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByPercentilesArray(minZoom, maxZoom, attributeName, percentiles, feature: QgsFeature, parent, context: QgsExpressionContext):
    """
    visibilityByPercentilesArray(minZoom, maxZoom, attributeName, percentiles)<br><br>
    Controls features visibility by using an array of percentiles. For example, say you have a vector layer containing cities and its populations. 
    So using the array arr = [5,25,50,100] and considering minZoom = 10 and maxZoom = 13, it will produce the following results:

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
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>maxZoom</b>: maximum zoom (inclusive)</li>
      <li><b>attributeName</b>: name of attribute (must be numeric OR string containing only numbers) that will be used for percentile calculations.</li>
      <li><b>percentiles</b>: array of percentiles OR a property name. Ex: array(5,25,5,100)</li>
    </ul>

    <br>
    <h2>Example usage:</h2>
    visibilityByPercentilesArray(5, 10, array(5,25,50,100)) -> using percentiles 5%, 25%, 50% and 100% at each zoom level between zoom 5 and 10.
    visibilityByPercentilesArray('_zoom_min', '_zoom_max', '_cities_percentiles_array') -> same as before, but using properties.
    """
    result = None
    masterCache = f'{feature.id()}_{minZoom}_{maxZoom}_{attributeName}_{str(percentiles)}'

    if context.hasCachedValue(masterCache):
        return context.cachedValue(masterCache)

    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = context.cachedValue('_layer_all_attrs_values')
        if allAttrValues is None:            
            allAttrValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
            context.setCachedValue('_layer_all_attrs_values', allAttrValues)

        maxAttr = context.cachedValue('_layer_max')
        if maxAttr is None:
            maxAttr = max(allAttrValues)
            context.setCachedValue('_layer_max', maxAttr)

        currentZoom = float(context.variable('zoom_level')) + 1
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

            result = 1 if attrValue >= percentileResult else 0
        else:
            result = 0
    except Exception as e:
        error(str(traceback.format_exc()))
        result = 0
    
    context.setCachedValue(masterCache, result)
    return result

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByPercentilesIncrement(minZoom, maxZoom, attributeName, increment, minPercentile, feature, parent, context):
    """
    visibilityByPercentilesIncrement(minZoom, maxZoom, attribute, minPercentile, increment)<br><br>
    Controls features visibility by using a minimum percentile value that will be incremented a each zoom level.
    For example, say you have a vector layer containing cities and its populations. So using minPercentile = 5, increment = 5 and 
    considering minZoom = 10 and maxZoom = 13, it will produce the following results:

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
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>maxZoom</b>: maximum zoom (inclusive)</li>
      <li><b>attributeName</b>: name of attribute (must be numeric OR string containing only numbers) that will be used for percentile calculations.</li>
      <li><b>increment</b>: increment that be added at each zoom level to the current percentile (starting from minPercentile)</li>
      <li><b>minPercentile</b>: minimum percentile</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    visibilityByPercentilesIncrement(5, 10, 2, 5) -> from zoom 5 to 10, starting from percentile 5% and incrementing 2% eat each zoom level.
    visibilityByPercentilesIncrement('_zoom_min', '_zoom_max', '_cities_increment_percentile', '_cities_min_percentile') -> same as before, but using properties.
    """

    result = None
    masterCache = f'{feature.id()}_{minZoom}_{maxZoom}_{attributeName}_{increment}_{minPercentile}'

    if context.hasCachedValue(masterCache):
        return context.cachedValue(masterCache)
    
    try:
        key = Utils.getCachedLayerTag(context)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = context.cachedValue('_layer_all_attrs_values')

        if allAttrValues is None:            
            allAttrValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
            context.setCachedValue('_layer_all_attrs_values', allAttrValues)

        maxAttr = context.cachedValue('_layer_max')

        if maxAttr is None:
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

            result = 1 if attrValue >= percentileResult else 0
        else:
            result = 0
    except Exception as e:
        result = 0
        
    context.setCachedValue(masterCache, result)
    return result