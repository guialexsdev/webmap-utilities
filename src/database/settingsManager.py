from ..model.variable import Variable
from ..database.variablesManager import VariablesManager
from ..model.property import PROPERTY_DATA_TYPE, Property
from ..model.settings import Settings
from qgis.core import QgsProject, QgsExpressionContextUtils
import json

class SettingsManager:
    PROJECT_SETTINGS_VAR_KEY = 'webmap_settings'

    def __init__(self, settings: Settings = None, variablesManager: VariablesManager = None):
        if settings is None:
            self.settings = Settings()
            self.settings.addOrUpdateProperties(self.defaultProperties())
        else:
            self.settings = settings

        self.variablesManager = VariablesManager() if variablesManager is None else variablesManager
        
    def defaultProperties(self):
        return [
            Property('_zoom_min',              'Minimum zoom level',                           PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_zoom_max',              'Maximum zoom level',                           PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_label_zoom_min',        'Minimum zoom level for labels',                PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_label_size_min',        'Minimum label size',                           PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_label_size_max',        'Maximum label size',                           PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_label_size_increment',  'Label size increment per zoom increment',      PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_symbol_zoom_min',       'Minimum zoom level for symbols',               PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_symbol_size_min',       'Minimum symbol size',                          PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_symbol_size_max',       'Maximum symbol size',                          PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_symbol_size_increment', 'Symbol size increment per zoom increment',     PROPERTY_DATA_TYPE.NUMBER, False),
            Property('_symbol_color_sequence', 'Symbol colors per zoom',                       PROPERTY_DATA_TYPE.STRING, True),
            Property('_style',                 'Style (qml file) to be automatically applied', PROPERTY_DATA_TYPE.FILE,   False)
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

    def loadFromProject(project: QgsProject):
        scope = QgsExpressionContextUtils.projectScope(project)

        if scope.hasVariable(SettingsManager.PROJECT_SETTINGS_VAR_KEY):
            propertiesFromProject = scope.variable(SettingsManager.PROJECT_SETTINGS_VAR_KEY)
            jsonObj = json.loads(propertiesFromProject)
            settings = Settings.fromDict(jsonObj)
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

        self.settings = Settings.fromDict(jsonObj['settings'])
        self.variablesManager.variables = [Variable.fromDict(jsonObj[varName]) for varName in jsonObj['variables']]
        self.variablesManager.toDelete = []
        file.close()

    def persistToProject(self, project: QgsProject):
        jsonStr = json.dumps(self.settings, cls=DefaultEncoder)
        QgsExpressionContextUtils.setProjectVariable(project, SettingsManager.PROJECT_SETTINGS_VAR_KEY, jsonStr)
        self.variablesManager.persistToProject(project)

class DefaultEncoder(json.JSONEncoder):
  def default(self, o):
      return o.__dict__
