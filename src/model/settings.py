
from .property import Property

class TAG_IDENTIFY_MODE:
	LAYER_NAME_STARTS_WITH: str = 'layer_name_starts_with'
	CATEGORY_METADATA_CONTAINS: str = 'category_metadata_contains'

class Settings:

	def __new__(cls, *args, **kwargs):
		return super().__new__(cls)

	def __init__(self, tags = [], properties = {}, structure = {}, tagIdentifyMode = TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH):
		self.tags: list[str] = tags
		self.properties = properties
		self.structure = structure
		self.tagIdentifyMode = tagIdentifyMode if tagIdentifyMode is not None else TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH

	def addOrUpdateTag(self, tag: str):
		self.tags.append(tag)

	def addOrUpdateTags(self, tags: list[str]):
		for tag in tags:
			self.addOrUpdateTag(tag)

	def addOrUpdateProperty(self, property: Property):
		self.properties[property.name] = property

	def addOrUpdateProperties(self, properties: list[Property]):
		for property in properties:
			self.addOrUpdateProperty(property)

	def removeTag(self, tag):
		self.tags.remove(tag)

	def removeTags(self, tags: list[str]):
		for tag in tags:
			self.tags.remove(tag)

	def removeProperty(self, propertyName):
		if propertyName in self.properties:
			del self.properties[propertyName]

	def removeProperties(self, propertyNames: list[str]):
		for property in propertyNames:
			self.removeProperty(property)
			
