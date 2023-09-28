from qgis.core import qgsfunction
from ..utils.cache import Cache

@qgsfunction(args='auto', group='Webmap - Visibility')
def visibilityByOffset(minZoom, offset, feature, parent, context):
    """
    visibilityByOffset(minZoom, offset)<br><br>
    Controls the visibility of Features using an offset parameter. For example, if you choose minZoom = 5 and offset = 3, the layer will be visible only from zoom level 8 onwards.    <br>

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
        currentZoom = context.variable('zoom_level') + 1
        return 1 if currentZoom - minZoom >= offset else 0

    cache = Cache(context)
    resultCacheKey = f'{feature.id()}_{minZoom}_{offset}'
    return cache.cachedSection(resultCacheKey, work)
