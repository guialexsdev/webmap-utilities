from qgis.core import NULL

class Utils:
    def getAttribute(feature, prop):
        try:
            return feature[prop]
        except:
            return NULL

    def getFloatAttribute(feature, prop):
        try:
            rawValue = feature[prop] 
            return float(rawValue) if rawValue != 'NULL' and rawValue != NULL else 0
        except:
            return None

    def scaleToZoomLevel(availableScales: list[float], scale: float):
        aproxScale = min(availableScales, key=lambda x:abs(x-scale))
        return availableScales.index(aproxScale)
    