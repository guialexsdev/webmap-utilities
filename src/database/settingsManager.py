#from ..model.property import Property
from ..model.variable import Variable
from ..database.variablesManager import VariablesManager
from ..model.property import Property
from ..model.settings import Settings
from qgis.core import QgsProject, QgsExpressionContextUtils, QgsMessageLog
import json

class SettingsManager:
    def __init__(self, settings: Settings = None, variablesManager: VariablesManager = None):
        if settings is None:
            self.settings = Settings()
            self.settings.addOrUpdateProperties(self.defaultProperties())
        else:
            self.settings = settings

        if variablesManager is None:
            self.variablesManager = VariablesManager()
        else:
            self.variablesManager = variablesManager
        
    def defaultProperties(self):
        return [
            Property('_zoom_min', 'Minimum zoom level', 'number', False),
            Property('_zoom_max', 'Maximum zoom level', 'number', False),
            Property('_label_zoom_min', 'Minimum zoom level for labels', 'number', False),
            Property('_label_size_min', 'Minimum label size', 'number', False),
            Property('_label_size_max', 'Maximum label size', 'number', False),
            Property('_label_size_increment', 'Label size increment per zoom increment', 'number', False),
            Property('_symbol_zoom_min', 'Minimum zoom level for symbols', 'number', False),
            Property('_symbol_size_min', 'Minimum symbol size', 'number', False),
            Property('_symbol_size_max', 'Maximum symbol size', 'number', False),
            Property('_symbol_size_increment', 'Symbol size increment per zoom increment', 'number', False),
            Property('_symbol_color_sequence', 'Symbol colors per zoom', 'string', True),
            Property('_style', 'Style (qml file) to be automatically applied', 'file', False)
        ]

    def cloneTagProperties(self, tagToBeCloned, newTag):
        varsToBeCloned = self.variablesManager.getByTag(tagToBeCloned)
        for var in varsToBeCloned:
            newVar = Variable(newTag, var.prop, var.value)
            self.variablesManager.addVariable(newVar)
    
    def tagExists(self, tag):
        return self.settings.tags.__contains__(tag)
    
    def deleteProperty(self, propertiesName: list[str]):
        self.settings.removeProperties(propertiesName)
        self.variablesManager.removeByProperties(propertiesName)

    def deleteTags(self, tags: list[str]):
        self.variablesManager.removeByTags(tags)
        self.settings.removeTags(tags)

    def renameTag(self, oldName, newName):
        self.variablesManager.renameVariablesByTag(oldName, newName)
        self.settings.removeTags([oldName])
        self.settings.addOrUpdateTag(newName)

    def renameProperty(self, oldName, newName):
        self.variablesManager.renameVariablesByProperty(oldName, newName)
        oldPropertyObj = self.settings.properties[oldName]
        newPropertyObk = Property(newName, oldPropertyObj.description, oldPropertyObj.type, oldPropertyObj.isList)
        self.settings.removeProperties([oldName])
        self.settings.addOrUpdateProperty(newPropertyObk)

    def removeProperties(self, properties: list[str]):
        self.settings.removeProperties(properties)
        self.variablesManager.removeByProperties(properties)

    def settingsJsonToObj(jsonObj):
        propertiesJsonObj = jsonObj['properties']
        convertedPropertiesObj = {}

        for prop in propertiesJsonObj:
            convertedPropertiesObj[prop] = Property(
                propertiesJsonObj[prop]['name'],
                propertiesJsonObj[prop]['description'],
                propertiesJsonObj[prop]['type'],
                propertiesJsonObj[prop]['isList'],
                propertiesJsonObj[prop]['validValues'] if 'validValues' in propertiesJsonObj[prop] else None
            )

        tags = jsonObj['tags'] if 'tags' in jsonObj else {}
        structure = jsonObj['structure'] if 'structure' in jsonObj else {}
        tagIdentifyMode = jsonObj['tagIdentifyMode'] if 'tagIdentifyMode' in jsonObj else None

        return Settings(tags, convertedPropertiesObj, structure, tagIdentifyMode)

    def loadFromProject(project: QgsProject):
        scope = QgsExpressionContextUtils.projectScope(project)

        if scope.hasVariable('webmap_settings'):
            propertiesFromProject = scope.variable('webmap_settings')
            jsonObj = json.loads(propertiesFromProject)
            settings = SettingsManager.settingsJsonToObj(jsonObj)
            variablesManager = VariablesManager.loadFromProject(settings, project)
            return SettingsManager(settings, variablesManager)
        else:
            return None

    def exportToFile(self, filepath: str):
        file = open(filepath, "w")
        dump = {
            'settings': self.settings,
            'variables': self.variablesManager.variables
        }
        
        file.write(json.dumps(dump, cls=DefaultEncoder))
        file.close()

    def importFromFile(self, filepath: str):
        file = open(filepath, "r")
        jsonObj = json.loads(file.read())
        self.settings = SettingsManager.settingsJsonToObj(jsonObj['settings'])
        self.variablesManager.variables = VariablesManager.variablesJsonToObj(jsonObj['variables'])
        self.variablesManager.toDelete = []
        file.close()

    def persistToProject(self, project: QgsProject):
        QgsExpressionContextUtils.setProjectVariable(project, 'webmap_settings', json.dumps(self.settings, cls=DefaultEncoder))
        self.variablesManager.persistToProject(project)

class DefaultEncoder(json.JSONEncoder):
  def default(self, o):
      return o.__dict__
