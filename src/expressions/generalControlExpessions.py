from qgis.core import qgsfunction
from ..utils.webmapCommons import Utils

@qgsfunction(args='auto', group='Webmap - General')
def zoomLevel(feature, parent, context):
    return context.variable('zoom_level') + 1

@qgsfunction(args='auto', group='Webmap - General')
def controlByIncrement(increment, minValue, maxValue, feature, parent, context):
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
    _minZoom   = float(Utils.getVariable(key, '_zoom_min', feature)[1])
    _minValue  = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue  = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)
    _increment = float(Utils.getVariable(key, increment, feature)[1] if isinstance(increment, str) else increment)

    _size = float(_minValue + (currentZoom - _minZoom) * _increment)

    return Utils.boundValue(_size, _minValue, _maxValue)

@qgsfunction(args='auto', group='Webmap - General')
def controlByArray(array, feature, parent, context):
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
    _minZoom = float(Utils.getVariable(key, '_zoom_min', feature)[1])
    _array   = Utils.strToArrayOfNumbers(Utils.getVariable(key, array, feature)[1]) if isinstance(array, str) else array

    return _array[int(Utils.boundValue(currentZoom - _minZoom, 0, _array.__len__() - 1))]

@qgsfunction(args='auto', group='Webmap - General')
def controlByMinMaxNormalization(minValue, maxValue, feature, parent, context):
    """
    controlByMinMaxNormalization(minValue, maxValue)<br><br>
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
    _minZoom  = float(Utils.getVariable(key, '_zoom_min', feature)[1])
    _maxZoom  = float(Utils.getVariable(key, '_zoom_max', feature)[1])
    _minValue = float(Utils.getVariable(key, minValue, feature)[1] if isinstance(minValue, str) else minValue)
    _maxValue = float(Utils.getVariable(key, maxValue, feature)[1] if isinstance(maxValue, str) else maxValue)
    _normalizedValue = Utils.normalizeMinMax(currentZoom, _minZoom, _maxZoom, _minValue, _maxValue)

    return Utils.boundValue(_normalizedValue, _minValue, _maxValue)
