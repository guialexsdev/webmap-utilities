from qgis.core import QgsProject, QgsExpressionContextUtils, NULL
from ..model.settings import Settings
from ..model.variable import Variable

class VariablesManager:
    def __new__(cls, *args, **kwargs):
      return super().__new__(cls)

    def __init__(self, variables = {}):
      self.variables = variables
      self.toDelete = []
    
    def addVariable(self, variable: Variable):
      self.variables[variable.getVariableName()] = variable

    def addVariables(self, variables: list[Variable]):
      for variable in variables:
        self.addVariable(variable)

    def renameVariablesByTag(self, oldTag, newTag):
      deleteList = []
      addList = []

      for varName in self.variables:
        var = self.variables[varName]

        if var.tag == oldTag:
          deleteList.append(varName)
          var.tag = newTag
          addList.append(var)

      self.removeByVariables(deleteList)
      self.addVariables(addList)

    def renameVariablesByProperty(self, oldName, newName):
      deleteList = []
      addList = []

      for varName in self.variables:
        var = self.variables[varName]

        if var.prop == oldName:
          deleteList.append(varName)
          var.prop = newName
          addList.append(var)

      self.removeByVariables(deleteList)
      self.addVariables(addList)

    def getByTag(self, tag: str) -> list[Variable]:
      found = []

      for varName in self.variables:
        var = self.variables[varName]
        if var.tag == tag:
          found.append(var)
      
      return found

    def getByProperty(self, prop: str) -> list[Variable]:
      found = []

      for varName in self.variables:
        var = self.variables[varName]
        if var.prop == prop:
          found.append(var)
      
      return found

    def tagHasProperties(self, tag, properties: list[str]) -> bool:
      vars = self.getByTag(tag)
      varsProperties = list(map(lambda x: x.prop, vars))
      
      for prop in properties:
        if prop not in varsProperties:
          return False
      
      return True

    def removeByVariables(self, varNames: list[str]):
      for name in varNames:
        self.toDelete.append(name)
        del self.variables[name]

    def removeByTags(self, tags: list[str]):
      deleteList = []
      for variable in self.variables:
        if self.variables[variable].tag in tags:
           deleteList.append(variable)

      self.removeByVariables(deleteList)

    def removeByProperties(self, propertiesName: list[str]):
      deleteList = []
      for variable in self.variables:
        if self.variables[variable].prop in propertiesName:
           deleteList.append(variable)

      self.removeByVariables(deleteList)

    def groupByTag(self):
      groupedByTag = {}
      for varName in self.variables:
          variable = self.variables[varName]
          if variable.tag in groupedByTag:
              groupedByTag[variable.tag].append(variable)
          else:
              groupedByTag[variable.tag] = [variable]

      return groupedByTag
    
    def loadFromProject(settings: Settings, project: QgsProject):
      scope = QgsExpressionContextUtils.projectScope(project)
      allProjectVarNames = scope.variableNames()

      vars = {}
      for varName in allProjectVarNames:
          value = scope.variable(varName)
          var = Variable.fromVariableNameAndValue(varName, value)

          if var is not None and var.prop in settings.properties and var.tag in settings.tags:
              vars[var.getVariableName()] = var

      return VariablesManager(vars) if vars.__len__() > 0 else None

    def persistToProject(self, project: QgsProject):
      for varName in self.toDelete:
         QgsExpressionContextUtils.removeProjectVariable(project, varName)

      for varName in self.variables:
         variable: Variable = self.variables[varName]
         QgsExpressionContextUtils.setProjectVariable(project, variable.getVariableName(), variable.value)

      self.toDelete = []
