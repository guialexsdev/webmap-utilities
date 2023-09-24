"""
Model exported as python.
Name : model
Group : 
With QGIS : 32806
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsField, edit, QgsFeatureRequest, QgsVectorLayer, QgsExpressionContext, QgsExpressionContextUtils
from qgis.PyQt.QtCore import QVariant

import processing
from ..utils.logUtils import info

class CreateClusteredVisualization(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('vector_layer_points', 'Vector layer (points)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('election_attribute', 'Attribute used to elect visible members', type=QgsProcessingParameterField.Any, parentLayerParameterName='vector_layer_points', allowMultiple=False, defaultValue=None))
        self.addParameter(
            QgsProcessingParameterEnum(
                'selection_method', 
                'Election method',
                options=['max','min'], 
                allowMultiple=False, 
                usesStaticStrings=False, 
                defaultValue=[0]
            )
        )
        self.addParameter(QgsProcessingParameterNumber('initial_min_cluster_size', 'Initial min. cluster size', type=QgsProcessingParameterNumber.Integer, defaultValue=5))
        self.addParameter(QgsProcessingParameterNumber('initial_max_cluster_member_distance', 'Initial max. cluster member distance', type=QgsProcessingParameterNumber.Double, defaultValue=50000))
        self.addParameter(QgsProcessingParameterNumber('number_of_zoom_levels', 'Number of zoom levels', type=QgsProcessingParameterNumber.Integer, defaultValue=3))
        self.addParameter(QgsProcessingParameterBoolean('isolated_feature_always_visible', 'Isolated feature always visible', defaultValue=False))
        self.addParameter(QgsProcessingParameterFeatureSink('ClusteredView', 'Clustered View', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('new_attribute_name', 'Attribute name (that controls visibility)', multiLine=False, defaultValue='_visibility_offset'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        nSteps = parameters['number_of_zoom_levels'] * 2
        currStep = 0
        feedback = QgsProcessingMultiStepFeedback(nSteps, model_feedback)
        results = {}
        outputs = {}
        currMaxClustedDistance = 2*parameters['initial_max_cluster_member_distance']
        visibilityOffsetFieldAdded = False
        newAttributeName = parameters['new_attribute_name']
        attributeName = parameters['election_attribute']
        orderBy = 'True' if parameters['selection_method'] == 1 else 'False'
        
        for nZoom in range(parameters['number_of_zoom_levels']):
            currMaxClustedDistance = currMaxClustedDistance / 2

            # DBSCAN clustering
            alg_params = {
                'DBSCAN*': False,
                'EPS': currMaxClustedDistance,
                'FIELD_NAME': f'_cluster_id{nZoom}',
                'INPUT': parameters['vector_layer_points'] if nZoom == 0 else outputs[f'DbscanClustering{nZoom - 1}']['OUTPUT'],
                'MIN_SIZE': parameters['initial_min_cluster_size'],
                'SIZE_FIELD_NAME': f'_cluster_size{nZoom}',
                'OUTPUT': parameters['ClusteredView'] if nZoom == parameters['number_of_zoom_levels'] - 1 else QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'DbscanClustering{nZoom}'] = processing.run('native:dbscanclustering', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            clusterLayer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(outputs[f'DbscanClustering{nZoom}']['OUTPUT'])

            #Create attribute that controls visibility
            if not visibilityOffsetFieldAdded:
                visibilityOffsetFieldAdded = True
                vOffsetField = QgsField(newAttributeName, QVariant.Type.Int)
                clusterLayer.dataProvider().addAttributes([vOffsetField])
                clusterLayer.updateFields()

            query = f'array_contains(array_slice(array_sort(array_agg(to_real("{attributeName}"), group_by:="_cluster_id{nZoom}", filter:="{newAttributeName}" IS NULL), {orderBy}),0,0), to_real("{attributeName}"))'

            request = QgsFeatureRequest()
            reqContext = QgsExpressionContext()
            reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(clusterLayer))
            request.setExpressionContext(reqContext)
            request.setFilterExpression(query)

            with edit(clusterLayer):
                for feature in clusterLayer.getFeatures(request):
                    feature[newAttributeName] = nZoom
                    clusterLayer.updateFeature(feature)

            if nZoom == parameters['number_of_zoom_levels'] - 1:
                request = QgsFeatureRequest()
                reqContext = QgsExpressionContext()
                reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(clusterLayer))
                request.setExpressionContext(reqContext)
                request.setFilterExpression(f'"{newAttributeName}" IS NULL')

                with edit(clusterLayer):
                    for feature in clusterLayer.getFeatures(request):
                        feature[newAttributeName] = 0 if parameters['isolated_feature_always_visible'] == True else nZoom + 1
                        clusterLayer.updateFeature(feature)
            
            self.deleteAttribute(clusterLayer, f'_cluster_id{nZoom}')
            self.deleteAttribute(clusterLayer, f'_cluster_size{nZoom}')

            currStep += 1
            feedback.setCurrentStep(currStep)
            if feedback.isCanceled():
                return {}

        results['ClusteredView'] = outputs[f"DbscanClustering{parameters['number_of_zoom_levels'] - 1}"]['OUTPUT']
        return results

    def deleteAttribute(self, layer, name):
        with edit(layer):
            attrIdx = layer.fields().indexFromName(name)
            if attrIdx != -1:
                deleted = layer.dataProvider().deleteAttributes([attrIdx])
                layer.updateFields()
                return deleted

    def name(self):
        return 'Clustered Visualization'

    def displayName(self):
        return 'Clustered Visualization'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return CreateClusteredVisualization()
