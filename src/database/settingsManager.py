import os
from textwrap import dedent
import zipfile
import json
import tempfile
from pathlib import Path
from qgis.core import Qgis
from qgis.core import QgsProject, QgsExpressionContextUtils, QgsMessageLog
from ..model.variable import Variable
from ..database.variablesManager import VariablesManager
from ..model.property import PROPERTY_DATA_TYPE, Property
from ..model.settings import Settings

class SettingsManager:
    PROJECT_SETTINGS_VAR_KEY = 'webmap_settings'

    def __init__(self, settings: Settings = None, variablesManager: VariablesManager = None):
        if settings is None:
            self.settings = Settings()
            self.settings.addOrUpdateProperties(self.defaultProperties())
        else:
            self.settings = settings
            #A version update may create or even modify default properties, so we need to always bring updates from default properties.
            self.updateDefaultProperties()

        self.variablesManager = VariablesManager() if variablesManager is None else variablesManager
        
    def updateDefaultProperties(self):
        defaultProperties = self.defaultProperties()

        for defProp in defaultProperties:
            if defProp.name not in self.settings.properties:
                self.settings.properties[defProp.name] = defProp

        defaulPropertiesName = list(map(lambda x: x.name, defaultProperties))

        for propName in self.settings.properties:
            prop: Property = self.settings.properties[propName]
            if prop.isDefault and prop.name not in defaulPropertiesName:
                prop.isDefault = False

    def defaultProperties(self):
        geometryTypes = ['points','lines','multilinestrings','multipolygons','other']

        return [
            Property('_zoom_min', 'Minimum zoom level', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_zoom_max', 'Maximum zoom level', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_geometry_type', 'Geometry type', PROPERTY_DATA_TYPE.STRING, False, geometryTypes, True),
            Property('_label_zoom_min', 'Minimum zoom level for labels', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_label_size_min', 'Minimum label size', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_label_size_max', 'Maximum label size', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_label_size_increment', 'Label size increment per zoom increment', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_symbol_zoom_min', 'Minimum zoom level for symbols', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_symbol_size_min', 'Minimum symbol size', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_symbol_size_max', 'Maximum symbol size', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_symbol_size_increment', 'Symbol size increment per zoom increment', PROPERTY_DATA_TYPE.NUMBER, False, None, True),
            Property('_symbol_color_sequence', 'Symbol colors per zoom', PROPERTY_DATA_TYPE.STRING, True, None, True),
            Property('_style', 'Style (qml file) to be automatically applied', PROPERTY_DATA_TYPE.FILE, False, None, True),
            Property(
                '_osm_query', 
                dedent(
                    """
                    OSM query to download vector layer of tag. Only one key-value pair per list entry is permitted.
                    Format: <key>=<value>
                    Example: place=city
                    """
                ), 
                PROPERTY_DATA_TYPE.STRING, True, None, True
            )
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

    # Every plugin's data is stored in project variables environment.
    def persistToProject(self, project: QgsProject):
        jsonStr = json.dumps(self.settings, cls=DefaultEncoder)
        QgsExpressionContextUtils.setProjectVariable(project, SettingsManager.PROJECT_SETTINGS_VAR_KEY, jsonStr)
        self.variablesManager.persistToProject(project)

    # Loads plugin data from project environment.
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

    # Export to a file with extension .wpc (Webmap Plugin Configuration)
    def exportToFile(self, filepath: str):
        name = Path(filepath).name
        settingsFile = filepath.replace(name, 'settings.json')

        # Writing settings.json with all properties, tags etc.
        file = open(settingsFile, "w")
        dump = {
            'settings': self.settings,
            'variables': self.variablesManager.variables
        }
        file.write(json.dumps(dump, cls=DefaultEncoder))
        file.close()

        # Creating a list of files to compress later
        vars  = self.variablesManager.getByProperty('_style')
        files = list(map(lambda x: x.value, vars))
        files.append(settingsFile)
        
        # Now compressing...
        self.__compress(set(files), filepath)

        # Don't need settings file anymore... now everything is inside zip file.
        os.remove(settingsFile)

    # Import from a .wpc file. If some style property was found, onStylePropertyFound callback 
    # will be called to give us a path (where styles will be stored)
    def importFromFile(self, filepath: str, onStylePropertyFound):
        #Uncompress in a temp folder
        tmpFolder = tempfile.TemporaryDirectory().name
        self.__uncompress(filepath, tmpFolder)

        #Load setting.json at first
        settingsFile = f'{tmpFolder}\settings.json'
        file = open(settingsFile, 'r')
        jsonObj = json.loads(file.read())
        file.close()

        #Import settings.json (properties, variables etc)
        self.settings = Settings.fromDict(jsonObj['settings'])
        for varName in jsonObj['variables']:
            var = Variable.fromDict(jsonObj['variables'][varName])
            self.variablesManager.variables[varName] = var
        self.variablesManager.toDelete = []

        #All lines below handles QML files. Needs a refactoring!!
        extractedQmlFiles = [f for f in os.listdir(tmpFolder) if f.lower().endswith('.qml')]

        if extractedQmlFiles.__len__() > 0:
            stylesFolder = onStylePropertyFound()

            if stylesFolder is not None:
                #Yeah... a second terrible call to uncompress. TODO: remove it, please!
                self.__uncompress(filepath, stylesFolder)
                os.remove(f'{stylesFolder}\settings.json')
            else:
                stylesFolder = tmpFolder

            for varName in self.variablesManager.variables:
                var = self.variablesManager.variables[varName]

                if var.prop == '_style':
                    oldQmlName = Path(var.value).name
                    var.value = f'{stylesFolder}\{oldQmlName}' if oldQmlName in extractedQmlFiles else ''

    def __compress(self, files: list[str], zipName: str):
        compression = zipfile.ZIP_DEFLATED
        zf = zipfile.ZipFile(zipName, mode="w")

        try:
            for file in files:
                name = Path(file).name
                zf.write(file, name, compress_type=compression)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'Webmap Utilities Plugin', Qgis.MessageLevel.Critical)
        finally:
            zf.close()

    def __uncompress(self, zipFile: str, folder: str):
        try:
            with zipfile.ZipFile(zipFile, 'r') as zipRef:
                zipRef.extractall(folder)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'Webmap Utilities Plugin', Qgis.MessageLevel.Critical)

class DefaultEncoder(json.JSONEncoder):
  def default(self, o):
      return o.__dict__
