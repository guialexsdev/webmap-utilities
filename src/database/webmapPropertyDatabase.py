from collections import namedtuple
from qgis.core import QgsProject, QgsExpressionContextUtils, NULL
from ..model.property import Property, WebmapPropertyEncoder
import json

class PropertiesDatabase:
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, project: QgsProject):
        self.project = project
        self.scope = QgsExpressionContextUtils.projectScope(project)

        propertiesFromProject = self.scope.variable('webmap_properties')

        if propertiesFromProject is not None and propertiesFromProject != NULL:
            self.properties = json.loads(propertiesFromProject, object_hook=WebmapPropertyDecoder().decoder)
        else:
            self.properties = self.defaultProperties()

    def commit(self):
        QgsExpressionContextUtils.setProjectVariable(self.project, 'webmap_properties', json.dumps(self.properties, cls=WebmapPropertyEncoder))

    def insert(self, property: Property):
        self.properties[property.name] = property

    def updateVisibilityByNames(self, names: list[str], visible: bool):
        for name in names:
            self.properties[name].tableVisibility = visible

    def updateVisibilityByName(self, name: str, visible: bool):
        self.properties[name].tableVisibility = visible

    def delete(self, name):
        if name in self.properties:
            del self.properties[name]

    def deleteAll(self, names: list[str]):
        for name in names:
            if name in self.properties:
                del self.properties[name]

    def getAll(self):
        return self.properties

    def getPropertyNamesByVisibility(self, visible: bool):
        return [k for k in self.properties if self.properties[k].tableVisibility == visible]

    def getAllPropertyNames(self):
        return [k for k in self.properties]

    def defaultProperties(self):
        return {
            '_zoom_min': Property('_zoom_min', 'Minimum zoom level', 'number', False),
            '_zoom_max': Property('_zoom_max', 'Maximum zoom level', 'number', False),

            '_label_zoom_min': Property('_label_zoom_min', 'Minimum zoom level for labels', 'number', False),
            '_label_size_min': Property('_label_size_min', 'Minimum label size', 'number', False),
            '_label_size_max': Property('_label_size_max', 'Maximum label size', 'number', False),
            '_label_size_increment': Property('_label_size_increment', 'Label size increment per zoom increment', 'number', False),

            '_symbol_zoom_min': Property('_symbol_zoom_min', 'Minimum zoom level for symbols', 'number', False),
            '_symbol_size_min': Property('_symbol_size_min', 'Minimum symbol size', 'number', False),
            '_symbol_size_max': Property('_symbol_size_max', 'Maximum symbol size', 'number', False),
            '_symbol_size_increment': Property('_symbol_size_increment', 'Symbol size increment per zoom increment', 'number', False)
        }

class WebmapPropertyDecoder:
  def __init__(self):
    self.objDict = {}

  def decoder(self, dict):
      if 'name' in dict:
        obj = Property(dict['name'],dict['description'],dict['type'],dict['isList'],dict['tableVisibility'])
        self.objDict[obj.name] = obj
        return obj
      else:
        return self.objDict