from json import JSONEncoder

class PROPERTY_DATA_TYPE:
	NUMBER: str = 'number'
	STRING: str = 'string'
	FILE: str = 'file'

class Property:
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls)

  def __init__(self, name = None, description = None, type = None, isList = None, validValues = None, isDefault = False):
    self.name = name
    self.description = description
    self.type = type
    self.isList = isList
    self.validValues = validValues
    self.isDefault = isDefault

  def __repr__(self) -> str:
    return f'{self.name} = [{self.description},{self.type},{self.isList}]'
  
  def fromDict(dict):
    return Property(
      dict['name'],
      dict['description'],
      dict['type'],
      dict['isList'],
      dict['validValues'] if 'validValues' in dict else None,
      dict['isDefault'] if 'isDefault' in dict else False
    )

class PropertyEncoder(JSONEncoder):
  def default(self, o):
      return o.__dict__

