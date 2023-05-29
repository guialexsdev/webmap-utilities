from qgis.core import qgsfunction, NULL, QgsExpression
from ..utils.webmapCommons import Utils

@qgsfunction(args='auto', group='Webmap - General')
def zoomLevel(feature, parent, context):
    return context.variable('zoom_level') + 1

@qgsfunction(args='auto', group='Webmap - General')
def incrementPerZoom(minZoom, increment, minValue, maxValue, feature, parent, context):
    """
    incrementPerZoom(minZoom, increment, minValue, maxValue)<br><br>
    Increments a value from <b>minValue</b> to <b>maxValue</b>. At each zoom level, <b>increment</b> is added
    to the current value. If current zoom level is less than <b>minZoom</b>, <b>minValue</b> will be used. 
    If current calculated vale is bigger than <b>maxValue</b>, <b>maxValue</b> will be used.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom at which increment starts  (inclusive)</li>
      <li><b>increment</b>: increment added to the current value at each zoom level</li>
      <li><b>minValue</b>: minimum value (inclusive)</li>
      <li><b>maxValue</b>: maximum value (inclusive)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    incrementPerZoom(5, 1, 1, 10) -> starting at level 5, add 1 to the starting value until reaching 10.
    incrementPerZoom('_symbol_size_increment', '_symbol_size_min', '_symbol_size_max') -> the same as before, but using properties instead of
    numbers.
    """

    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom   = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _minValue  = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue  = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)
    _increment = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

    _size = float(_minValue + (currentZoom - _minZoom) * _increment)

    return Utils.boundValue(_size, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def incrementPerZoomOffset(minZoom, increment, minValue, fromMinOffset, feature, parent, context):
    """
    incrementPerZoomOffset(minZoom, increment, minValue, fromMinOffset)<br><br>
    Increments a value from <b>minValue</b> to <b>minValue + fromMinOffset</b>. At each zoom level, <b>increment</b> is added
    to the current value. Useful when <b>minValue</b> is variable. If current zoom level is less than <b>minZoom</b>, <b>minValue</b> 
    will be used. If current calculated vale is bigger than <b>minValue + fromMinOffset</b>, <b>minValue + fromMinOffset</b> will be used.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom at which increment starts (inclusive)</li>
      <li><b>increment</b>: increment added to the current value at each zoom level</li>
      <li><b>minValue</b>: minimum value (inclusive)</li>
      <li><b>fromMinOffset</b>: value to be added to minimum value (inclusive)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    incrementPerZoomOffset(5, 1, 1, 9) -> starting at level 5, add 1 to the starting value 9 times.
    incrementPerZoomOffset('_symbol_size_increment', '_symbol_size_min', '_symbol_size_n_increments') -> the same as before, but using properties instead of
    numbers.
    """

    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom    = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _minValue   = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue   = _minValue + fromMinOffset
    _increment  = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

    _size = float(_minValue + (currentZoom - _minZoom) * _increment)

    return Utils.boundValue(_size, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def arrayItemPerZoom(minZoom, array, feature, parent, context):
    """
    arrayItemPerZoom(minZoom, array)<br><br>
    Use the value in the given array at each zoom level. For example, consider minZoom = 5: if current zoom = 5 then first element of 
    array will be returned; if current zoom = 6 then second element of array will be returned etc. 
    
    If the value falls outside the range of the array, the closest array item will is used (first or last element). 

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>array</b>: array of values</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    arrayItemPerZoom(5, array(2,5,10)) -> at zoom level 5 the first array item (2) is returned; at zoom level 6 the second array item (5) 
    is returned etc.
    arrayItemPerZoom('_zoom_min', '_my_array') -> the same as before, but using properties.
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom   = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _array   = Utils.strToArrayOfNumbers(Utils.getVariable(key, array, feature)[1]) if isinstance(array, str) else array

    return _array[int(Utils.boundValue(currentZoom - _minZoom, 0, _array.__len__() - 1))]

@qgsfunction(args='auto', group='Webmap - General')
def normalizeZoomRange(minZoom, maxZoom, minValue, maxValue, feature, parent, context):
    """
    normalizeToZoomRange(minZoom, maxZoom, minValue, maxValue)<br><br>
    Normalize minZoom - maxZoom range to minValue - maxValue using Min-Max approach. Use this function if you don't care about
    how much your value will be increased at each zoom level. The result is often smoother than functions where the increment 
    value is explicit.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>maxZoom</b>: maximum zoom (inclusive)</li>
      <li><b>minValue</b>: minimum value (inclusive)</li>
      <li><b>maxValue</b>: maximum value (inclusive)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    normalizeZoomRange(5, 10, 1, 8) -> between zoom level 5 and 10, value should be increased from 1 to 8.
    normalizeZoomRange('_zoom_min', '_zoom_max', '_label_min_size', '_label_max_size') -> the same as before, but using properties.
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)
    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)
    _normalizedValue = Utils.normalizeMinMax(currentZoom, _minZoom, _maxZoom, _minValue, _maxValue)

    return Utils.boundValue(_normalizedValue, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def normalizeZoomRangeOffset(minZoom, maxZoom, minValue, fromMinOffset, feature, parent, context):
    """
    normalizeZoomRangeOffset(minZoom, maxZoom, minValue, fromMinOffset)<br><br>
    Normalize minZoom - maxZoom range to minValue - (minValue + fromMinOffset) using Min-Max approach. Use this function if you don't care 
    about how much your value will be increased at each zoom level. The result is often smoother than functions where the increment 
    value is explicit.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minZoom</b>: minimum zoom (inclusive)</li>
      <li><b>maxZoom</b>: maximum zoom (inclusive)</li>
      <li><b>minValue</b>: minimum value (inclusive)</li>
      <li><b>fromMinOffset</b>: value to be added to minValue (so obtaining the maximum value)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    normalizeZoomRangeOffset(5, 10, 1, 7) -> between zoom level 5 and 10, value should be increased from 1 to 8 (1 + 7).
    normalizeZoomRangeOffset('_zoom_min', '_zoom_max', '_label_min_size', '_label_offset_size') -> the same as before, but using properties.
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)
    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = _minValue + fromMinOffset
    _normalizedValue = Utils.normalizeMinMax(currentZoom, _minZoom, _maxZoom, _minValue, _maxValue)

    return _normalizedValue#Utils.boundValue(_normalizedValue, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def normalizeAttribute(attributeName, minValue, maxValue, feature, parent, context):
    """
    normalizeAttribute(attributeName, minValue, minValue, fromMinOffset)<br><br>
    Algorithm will get minimum and maximum values of the given attribute and trasnform it to range to <b>minValue</b> - <b>maxValue</b> 
    using Min-Max approach. Parameter <b>attributeName</b> can't be replaced by a property.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>attributeName</b>: name of the attribute</li>
      <li><b>minValue</b>: minimum value (inclusive)</li>
      <li><b>maxValue</b>: maximum value (inclusive)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    normalizeAttribute('population', 1, 7) -> returns a valeu between 1 and 7, according to 'population' attribute.
    normalizeAttribute('population', '_my_min_size', '_my_max_size') -> the same as before, but using properties. Remember that 
    parameter <b>attributeName</b> can't be replaced by a property.
    """
    key = Utils.getCachedLayerTag(context)
    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)

    layer = Utils.getCurrentLayer(context)
    minAttr = context.cachedValue('_layer_min')
    maxAttr = context.cachedValue('_layer_max')

    if minAttr is None or maxAttr is None:
        allAttrsValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
        minAttr = min(allAttrsValues)
        maxAttr = max(allAttrsValues)
        context.setCachedValue('_layer_min', minAttr)
        context.setCachedValue('_layer_max', maxAttr)

    attrValue = Utils.getFloatAttribute(feature, attributeName)
    return Utils.normalizeMinMax(attrValue, minAttr, maxAttr, _minValue, _maxValue)
    
@qgsfunction(args='auto', group='Webmap - General')
def scaleExponential(attributeName, outlierEffect, exponent, minValue, maxValue, feature, parent, context):
    """
    scaleExponential(attributeName, outlierEffect, exponent, minValue, maxValue)<br><br>
    Similar to the native function scale_exp(...). Parameter <b>attributeName</b> can't be replaced by a property.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>attributeName</b>: attribute name to be scaled.</li>
      <li><b>outlierEffect</b>: percentage of the maximum value. If the chosen attribute has very high values - outlier - decrease this number.</li>
      <li><b>exponent</b>: A positive value (greater than 0), which dictates the way input values are mapped to the output range. 
      Large exponents will cause the output values to 'ease in', starting slowly before accelerating as the input values approach the domain maximum. 
      Smaller exponents (less than 1) will cause output values to 'ease out', where the mapping starts quickly but slows as it approaches the 
      domain maximum.</li>
      <li><b>minValue</b>: Specifies the minimum value in the output range, the smallest value which should be output by the function  (inclusive)</li>
      <li><b>maxValue</b>: Specifies the maximum value in the output range, the largest value which should be output by the function (inclusive)</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    scaleExponential('population', 50, 0.5, 3, 8)
    """
    key = Utils.getCachedLayerTag(context)

    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)

    layer = Utils.getCurrentLayer(context)
    minAttr = context.cachedValue('_layer_min')
    maxAttr = context.cachedValue('_layer_max')

    if minAttr is None or maxAttr is None:
        allAttrsValues = [Utils.getFloatAttribute(f, attributeName) for f in layer.getFeatures()]
        minAttr = min(allAttrsValues)
        maxAttr = max(allAttrsValues)
        context.setCachedValue('_layer_min', minAttr)
        context.setCachedValue('_layer_max', maxAttr)

    attrValue = Utils.getFloatAttribute(feature, attributeName)
    return QgsExpression(f'coalesce(scale_exp({attrValue}, {minAttr}, {maxAttr*(outlierEffect/100)}, {_minValue}, {_maxValue}, {exponent}),  {_minValue})').evaluate()
