from qgis.core import qgsfunction, NULL, QgsExpression
from ..utils.webmapCommons import Utils

@qgsfunction(args='auto', group='Webmap - General')
def zoomLevel(feature, parent, context):
    return context.variable('zoom_level') + 1

@qgsfunction(args='auto', group='Webmap - General')
def controlByIncrement(minZoom, increment, minValue, maxValue, feature, parent, context):
    """
    controlByIncrement(increment, minValue, maxValue)<br><br>
    Controls any numeric property of features by incrementing a value from minValue up to maxValue. For example,
    you can use this function to increase the size of a symbol ou label.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>increment</b>: increment added to minValue at each zoom level OR a property name.</li>
      <li><b>minValue</b>: minimum value OR a property name</li>
      <li><b>maxValue</b>: maximum value OR a property name</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    controlByIncrement(1, 1, 10)
    controlByIncrement('_symbol_size_increment', '_symbol_size_min', '_symbol_size_max')
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
def controlByIncrementOffset(minZoom, increment, minValue, fromMinOffset, feature, parent, context):
    """
    controlByIncrement(increment, minValue, maxValue)<br><br>
    Controls any numeric property of features by incrementing a value from minValue up to maxValue. For example,
    you can use this function to increase the size of a symbol ou label.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>increment</b>: increment added to minValue at each zoom level OR a property name.</li>
      <li><b>minValue</b>: minimum value OR a property name</li>
      <li><b>maxValue</b>: maximum value OR a property name</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    controlByIncrement(1, 1, 10)
    controlByIncrement('_symbol_size_increment', '_symbol_size_min', '_symbol_size_max')
    """

    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom   = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _minValue  = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue  = _minValue + fromMinOffset
    _increment = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

    _size = float(_minValue + (currentZoom - _minZoom) * _increment)

    return Utils.boundValue(_size, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def controlByArray(minZoom, array, feature, parent, context):
    """
    controlByArray(array)<br><br>
    Controls any numeric property of features by using values of a fixed array. For example,
    you can use this function to increase the size of a symbol ou label.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>array</b>: array of values OR a property name.</li>
      <li><b>minValue</b>: minimum value OR a property name</li>
      <li><b>maxValue</b>: maximum value OR a property name</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    controlByArray(array(1,2,3))
    controlByArray('_symbol_size_increment_arr')
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom   = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _array   = Utils.strToArrayOfNumbers(Utils.getVariable(key, array, feature)[1]) if isinstance(array, str) else array

    return _array[int(Utils.boundValue(currentZoom - _minZoom, 0, _array.__len__() - 1))]

@qgsfunction(args='auto', group='Webmap - General')
def controlByMinMax(minZoom, maxZoom, minValue, maxValue, feature, parent, context):
    """
    controlByMinMaxNorm(minValue, maxValue)<br><br>
    Controls any numeric property of features by using min-max normalization. You just need to choose a minValue
    and a maxValue and the function will find an appropriate increment value.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minValue</b>: minimum value OR a property name</li>
      <li><b>maxValue</b>: maximum value OR a property name</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    controlByMinMaxNormalization(array(1,2,3))
    controlByMinMaxNormalization('_symbol_size_min', '_symbol_size_max')
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
def controlByMinMaxOffset(minZoom, maxZoom, minValue, fromMinOffset, feature, parent, context):
    """
    controlByMinMaxNormOffset(minValue, fromMinOffset)<br><br>
    Controls any numeric property of features by using min-max normalization. You just need to choose a minValue
    and a maxValue and the function will find an appropriate increment value.

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>minValue</b>: minimum value OR a property name</li>
    </ul>

    <br>

    <h2>Example usage:</h2>
    controlByMinMaxNormalization(array(1,2,3))
    controlByMinMaxNormalization('_symbol_size_min', '_symbol_size_max')
    """
    key = Utils.getCachedLayerTag(context)

    currentZoom = context.variable('zoom_level') + 1
    _minZoom = float(Utils.getVariable(key, minZoom, feature)[1] if isinstance(minZoom, str) else minZoom)
    _maxZoom = float(Utils.getVariable(key, maxZoom, feature)[1] if isinstance(maxZoom, str) else maxZoom)
    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = _minValue + fromMinOffset
    _normalizedValue = Utils.normalizeMinMax(currentZoom, _minZoom, _maxZoom, _minValue, _maxValue)

    return Utils.boundValue(_normalizedValue, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def scaleMinMax(attributeName, minValue, maxValue, feature, parent, context):
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
    Similar to the native function scale_exp(...).

    <br>

    <h2>Parameters</h2>
    <ul>
      <li><b>attributeName</b>: attribute name to be scaled.</li>
      <li><b>outlierEffect</b>: percentage of the maximum value. If the chosen attribute has very high values - outlier - decrease this number.</li>
      <li><b>exponent</b>: A positive value (greater than 0), which dictates the way input values are mapped to the output range. 
      Large exponents will cause the output values to 'ease in', starting slowly before accelerating as the input values approach the domain maximum. 
      Smaller exponents (less than 1) will cause output values to 'ease out', where the mapping starts quickly but slows as it approaches the 
      domain maximum.</li>
      <li><b>minValue</b>: Specifies the minimum value in the output range, the smallest value which should be output by the function.</li>
      <li><b>maxValue</b>: Specifies the maximum value in the output range, the largest value which should be output by the function.</li>
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
