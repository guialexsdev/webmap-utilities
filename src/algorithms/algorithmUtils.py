from qgis.core import edit, QgsFeatureRequest, QgsVectorLayer, QgsExpressionContext, QgsExpressionContextUtils, QgsProcessing

class AlgorithmUtils:
  def outputToLayer(parameterFeatureSink, ouput, context):
    if parameterFeatureSink.sink.staticValue() != QgsProcessing.TEMPORARY_OUTPUT:
        clusterLayer: QgsVectorLayer = QgsVectorLayer(ouput)
    else:
        clusterLayer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(ouput)
    
    return clusterLayer
  
  def setAttributeValueByExpression(attrName, expression, value, layer: QgsVectorLayer):
    request = QgsFeatureRequest()
    reqContext = QgsExpressionContext()
    reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    request.setExpressionContext(reqContext)
    request.setFilterExpression(expression)

    with edit(layer):
        for feature in layer.getFeatures(request):
            feature[attrName] = value
            layer.updateFeature(feature)
  
  def setNullAttributes(attrName, value, layer: QgsVectorLayer):
    request = QgsFeatureRequest()
    reqContext = QgsExpressionContext()
    reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    request.setExpressionContext(reqContext)
    request.setFilterExpression(f'"{attrName}" IS NULL')

    with edit(layer):
        for feature in layer.getFeatures(request):
            feature[attrName] = value
            layer.updateFeature(feature)

  def deleteAttribute(layer, name):
    with edit(layer):
        attrIdx = layer.fields().indexFromName(name)
        if attrIdx != -1:
            deleted = layer.dataProvider().deleteAttributes([attrIdx])
            layer.updateFields()
            return deleted
