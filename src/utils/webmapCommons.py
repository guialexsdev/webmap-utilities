from qgis.core import QgsExpressionContextUtils, QgsExpressionContext, QgsProject, QgsMapLayer, NULL, QgsMapLayer
from ..model.settings import TAG_IDENTIFY_MODE, Settings
from ..database.settingsManager import SettingsManager
from ..model.variable import Variable

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
              
    def getCachedLayerTag(context: QgsExpressionContext):
        tagFound = context.cachedValue('webmap_current_tag')

        if tagFound is None:
            settingsManager = SettingsManager.loadFromProject(QgsProject.instance())
            settings = settingsManager.settings
            tags: list[str] = None

            if settings.tagIdentifyMode == TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH:
                name = context.variable('layer_name')
                tags = [tag for tag in settingsManager.settings.tags if name.startswith(tag)]
            else:
                layer: QgsMapLayer = Utils.getCurrentLayer(context)
                categories = layer.metadata().categories()
                tags = [tag for tag in settingsManager.settings.tags if tag in categories]

            tagFound = tags[0] if tags.__len__() > 0 else None

            if tagFound is not None:
                context.setCachedValue('webmap_current_tag', tagFound)

        return tagFound
    
    def getLayerTag(layer: QgsMapLayer, settings: Settings):
        tags: list[str] = None

        if settings.tagIdentifyMode == TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH:
            name = layer.name()
            tags = [tag for tag in settings.tags if name.startswith(tag)]
        else:
            categories = layer.metadata().categories()
            tags = [tag for tag in settings.tags if tag in categories]

        tagFound = tags[0] if tags.__len__() > 0 else None

        return tagFound
    
    def getCurrentLayer(context):
        id = context.variable('layer_id')
        return QgsProject.instance().mapLayer(id)
        
    def getVariable(key, prop, feature = None, default = None):
        value = None
        varName = Variable.formatVariableName(key,prop)

        if feature is not None:
            value = Utils.getAttribute(feature, prop)

        if value != NULL and value is not None:
            return ('attribute', str(value))
        else:
            value = QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(varName)

            if value != NULL and value is not None:
                return ('var', value)
            else:
                if default is None:
                    raise Exception(f"{prop} not found. Was this property added to your tag or layer attribute's table?")
                else:
                    return ('default', default)

    def strToArrayOfStrings(value: str, separator = ';'):
        return value.split(separator)

    def strToArrayOfNumbers(value: str, separator = ';'):
        return list(map(lambda x: float(x), Utils.strToArrayOfStrings(value, separator)))
    
    def normalizeMinMax(x, minx, maxx, minNormalized, maxNormalized):
        return minNormalized + ((x - minx) / (maxx - minx)) * (maxNormalized - minNormalized)

    def boundValue(value, min, max):
        if value >= min and value <= max:
            return value
        elif value < min:
            return min
        elif value > max:
            return max
        
    def scaleToZoomLevel(availableScales: list[float], scale: float):
        aproxScale = min(availableScales, key=lambda x:abs(x-scale))
        return availableScales.index(aproxScale)
    