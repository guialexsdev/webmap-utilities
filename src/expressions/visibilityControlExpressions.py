import numpy as np
import traceback
from qgis.core import qgsfunction, NULL, QgsExpressionContext, QgsFeature, QgsExpressionContextUtils, QgsProject
from ..utils.cache import Cache
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
    def work():
        scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
        key = Utils.getCachedLayerTag(context, scope)

        currentZoom = context.variable('zoom_level') + 1
        
        _minZoom = float(Utils.getVariable(key, minZoom, scope, feature)[1] if isinstance(minZoom, str) else minZoom)
        _maxZoom = float(Utils.getVariable(key, maxZoom, scope, feature)[1] if isinstance(maxZoom, str) else maxZoom)

        return 1 if currentZoom >= _minZoom and currentZoom <= _maxZoom else 0
    
    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{maxZoom}'
    return cache.cachedSection(resultCacheKey, work)

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByOffset(minZoom, offset, feature, parent, context):
    """
    visibilityByOffset(minZoom, offset)<br><br>
    Controls features visibility by minZoom and a offset value. Example: if minZoom = 5 and offset = 0 then the feature become visible
    for all zoom levels greater than ou equal 5. If minZoom = 5 and offset = 1 the the feature become visible for all zoom levels greater than
    or equal 6. This function is useful to control visibility of layers created by <b>Create Clustered View</b> and <b>Create Grid View</b> tools.
    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>offset</b>: offset from minZoom</li>
    </ul>

    </br>
    <h2>Example usage:</h2>
    visibilityByOffset(5, 2) -> feature will be visible for all zoom levels greater than ou equal 7 (5 + 2).
    """
    def work():
        scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
        key   = Utils.getCachedLayerTag(context, scope)

        currentZoom = context.variable('zoom_level') + 1

        _minZoom = float(Utils.getVariable(key, minZoom, scope, feature)[1] if isinstance(minZoom, str) else minZoom)
        _offset  = float(Utils.getVariable(key, offset, scope, feature)[1] if isinstance(offset, str) else offset)

        return 1 if currentZoom - _minZoom >= _offset else 0

    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{offset}'
    return cache.cachedSection(resultCacheKey, work)

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
    def work():
        scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
        key = Utils.getCachedLayerTag(context, scope)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = cache.cachedSection('_layer_all_attrs_values', lambda: [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()])

        currentZoom = float(context.variable('zoom_level')) + 1
        _minZoom = float(Utils.getVariable(key, minZoom, scope, feature)[1] if isinstance(minZoom, str) else minZoom)
        _maxZoom = float(Utils.getVariable(key, maxZoom, scope, feature)[1] if isinstance(maxZoom, str) else maxZoom)

        if currentZoom >= _minZoom and currentZoom <= _maxZoom:
            attrValue = Utils.getFloatAttribute(feature, attributeName)

            if currentZoom == _maxZoom and (attrValue == NULL or attrValue is None):
                return 1
            
            _percentiles = Utils.strToArrayOfNumbers(Utils.getVariable(key, percentiles, scope, feature)[1]) if isinstance(percentiles, str) else percentiles

            fromMinOffset = currentZoom - _minZoom
            percentileIndex = Utils.boundValue(fromMinOffset, 0, len(_percentiles) - 1)
            percentile = _percentiles[int(percentileIndex)]

            percentileResult = cache.cachedSection(f'_layer_percentile_{percentile}', lambda: np.percentile(allAttrValues, 100 - percentile))
            return 1 if attrValue >= percentileResult else 0
        else:
            return 0

    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{maxZoom}_{attributeName}_{str(percentiles)}'
    return cache.cachedSection(resultCacheKey, work)

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
    def work():
        scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
        key = Utils.getCachedLayerTag(context, scope)
        layer = Utils.getCurrentLayer(context)

        allAttrValues = context.cachedValue('_layer_all_attrs_values')

        if allAttrValues is None:            
            allAttrValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
            context.setCachedValue('_layer_all_attrs_values', allAttrValues)

        currentZoom = context.variable('zoom_level') + 1
        _minZoom = float(Utils.getVariable(key, minZoom, scope, feature)[1] if isinstance(minZoom, str) else minZoom)
        _maxZoom = float(Utils.getVariable(key, maxZoom, scope, feature)[1] if isinstance(maxZoom, str) else maxZoom)
        _increment = float(Utils.getVariable(key, increment, scope, feature)[1] if isinstance(increment, str) else increment)

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

    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{maxZoom}_{attributeName}_{increment}_{minPercentile}'
    return cache.cachedSection(resultCacheKey, work)

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByCluster(minZoom, initialNumberOfMembers, increment, clusterIdAttribute, selectionAttribute, selectionMethod, feature, parent, context):
    """
    visibilityByCluster(minZoom, initialNumberOfMembers, increment, clusterIdAttribute, selectionAttribute, selectionMethod)<br><br>
    This function controls features visibility by electing a cluster member to become to represent the cluster. At each zoom level, a new cluster
    member is elected (but previously elected member keeps visible). Clustered ID attribute must be previously calculated by user before using this 
    function (using DBSCAN algorithm, for example).
    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>initialNumberOfMembers</b>: initial number of members (to be elected at minZoom)</li>
      <li><b>increment</b>: increment to initialNumberOfMembers at each zoom level</li>
      <li><b>clusterIdAttribute</b>: attribute containing feature cluster id</li>
      <li><b>selectionAttribute</b>: attribute to be aggregated (used by selectionMethod)</li>
      <li><b>selectionMethod</b>: strategy to select a new visible member. Two options: 'min' and 'max'</li>
    </ul>
    """
    def work():
        scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
        key = Utils.getCachedLayerTag(context, scope)
        layer = Utils.getCurrentLayer(context)

        currentZoom = context.variable('zoom_level') + 1

        _minZoom = int(Utils.getVariable(key, minZoom, scope, feature)[1] if isinstance(minZoom, str) else minZoom)

        if (currentZoom < _minZoom):
            return 0
        
        clusterId = feature[clusterIdAttribute]
        value = Utils.getFloatAttribute(feature, selectionAttribute)

        _visiblePerCluster = int(Utils.getVariable(key, initialNumberOfMembers, scope, feature)[1] if isinstance(initialNumberOfMembers, str) else initialNumberOfMembers)
        _increment = int(Utils.getVariable(key, increment, scope, feature)[1] if isinstance(increment, str) else increment)

        cache = Cache(context)
        arrValues = cache.cachedSection(
            f'{clusterId}_arr', 
            lambda: sorted([Utils.getFloatAttribute(f, selectionAttribute) for f in layer.getFeatures() if f[clusterIdAttribute] == clusterId])
        )

        nRepr = int(_visiblePerCluster + (currentZoom - _minZoom)*_increment)

        if selectionMethod == 'min':
            toShow = arrValues[nRepr:].__contains__(value)
        elif selectionMethod == 'max':
            toShow = arrValues[-nRepr:].__contains__(value)

        return 1 if toShow else 0

    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{increment}'
    return cache.cachedSection(resultCacheKey, work)
