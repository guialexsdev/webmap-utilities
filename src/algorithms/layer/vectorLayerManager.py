from qgis.core import edit, QgsProcessingMultiStepFeedback, QgsFeatureRequest, QgsVectorLayer, QgsExpressionContext, QgsExpressionContextUtils, QgsProcessing, QgsField

class VectorLayerManager:
  
  def __init__(self, ouput, feedback: QgsProcessingMultiStepFeedback, context, parameterFeatureSink = None):
    self.feedback = feedback

    if parameterFeatureSink != None and parameterFeatureSink.sink.staticValue() != QgsProcessing.TEMPORARY_OUTPUT:
        self.layer: QgsVectorLayer = QgsVectorLayer(ouput)
    else:
        self.layer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(ouput)
  
  def setName(self, name):
     self.layer.setName(name)

  def createField(self, name, type):
    fieldExists = self.layer.fields().indexFromName(name)

    if fieldExists == -1:
      vOffsetField = QgsField(name, type)
      self.layer.dataProvider().addAttributes([vOffsetField])
      self.layer.updateFields()

  def renameField(self, currName, newName):
    with edit(self.layer):
      idx = self.layer.fields().indexFromName(currName)
      self.layer.renameAttribute(idx, newName)

  def setValueOfAllAttributes(self, attrName, value):
    for feature in self.layer.getFeatures():
        with edit(self.layer):
            feature[attrName] = value
            self.layer.updateFeature(feature)

  def setAttributeValueByExpression(self, attrName, expression, value):
    request = QgsFeatureRequest()
    reqContext = QgsExpressionContext()
    reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(self.layer))
    request.setExpressionContext(reqContext)
    request.setFilterExpression(expression)

    with edit(self.layer):
        for feature in self.layer.getFeatures(request):
            feature[attrName] = value
            self.layer.updateFeature(feature)
  
  def setValueOfNullAttributes(self, attrName, value):
    request = QgsFeatureRequest()
    reqContext = QgsExpressionContext()
    reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(self.layer))
    request.setExpressionContext(reqContext)
    request.setFilterExpression(f'"{attrName}" IS NULL')

    with edit(self.layer):
        for feature in self.layer.getFeatures(request):
            feature[attrName] = value
            self.layer.updateFeature(feature)

  def deleteAttribute(self, name):
    with edit(self.layer):
        attrIdx = self.layer.fields().indexFromName(name)
        if attrIdx != -1:
            deleted = self.layer.dataProvider().deleteAttributes([attrIdx])
            self.layer.updateFields()
            return deleted
