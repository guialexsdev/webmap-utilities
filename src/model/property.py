from json import JSONEncoder
from qgis.core import QgsMessageLog

class Property:
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls)

  def __init__(self, name = None, description = None, type = None, isList = None, validValues = None):
    self.name = name
    self.description = description
    self.type = type
    self.isList = isList
    self.validValues = validValues

  def __repr__(self) -> str:
    return f'{self.name} = [{self.description},{self.type},{self.isList}]'

class PropertyEncoder(JSONEncoder):
  def default(self, o):
      return o.__dict__

