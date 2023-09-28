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
from .afterProcessingLayerRenamer import AfterProcessingLayerRenamer

class CreateClusteredVisualization(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('VECTOR_LAYER', 'Vector layer (points)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('ELECTION_ATTRIBUTE', 'Attribute used to select cluster members', type=QgsProcessingParameterField.Any, parentLayerParameterName='VECTOR_LAYER', allowMultiple=False, defaultValue=None))
        self.addParameter(
            QgsProcessingParameterEnum(
                'ELECTION_METHOD', 
                'Election method',
                options=['max','min'], 
                allowMultiple=False, 
                usesStaticStrings=False, 
                defaultValue=[0]
            )
        )
        self.addParameter(QgsProcessingParameterNumber('MIN_CLUSTER_SIZE', 'Minimum cluster size', type=QgsProcessingParameterNumber.Integer, defaultValue=2))
        self.addParameter(QgsProcessingParameterNumber('INITIAL_MAX_CLUSTER_MEMBER_DISTANCE', 'Initial max. cluster member distance', type=QgsProcessingParameterNumber.Double, minValue=100, defaultValue=20000))
        self.addParameter(QgsProcessingParameterNumber('NUMBER_OF_ZOOM_LEVELS', 'Number of zoom levels', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=3))
        self.addParameter(QgsProcessingParameterBoolean('SHOW_ALL_AT_LAST_ZOOM_LEVEL', 'Show all feature at last zoom level', defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean('ISOLATED_FEATURES_ALWAYS_VISIBLE', 'Always show isolated features', defaultValue=False))
        self.addParameter(QgsProcessingParameterString('NEW_ATTRIBUTE_NAME', 'Attribute name (that controls visibility)', multiLine=False, defaultValue='_visibility_offset'))
        self.addParameter(QgsProcessingParameterFeatureSink('OUTPUT', 'Clustered View', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        nSteps = parameters['NUMBER_OF_ZOOM_LEVELS'] * 2
        currStep = 0
        feedback = QgsProcessingMultiStepFeedback(nSteps, model_feedback)
        results = {}
        outputs = {}
        currMaxClustedDistance = 2*parameters['INITIAL_MAX_CLUSTER_MEMBER_DISTANCE']
        visibilityOffsetFieldAdded = False
        visibilityAttribute = parameters['NEW_ATTRIBUTE_NAME']

        for nZoom in range(parameters['NUMBER_OF_ZOOM_LEVELS']):
            currMaxClustedDistance = currMaxClustedDistance / 2

            # Clusterization by distance
            alg_params = {
                'VECTOR_LAYER': parameters['VECTOR_LAYER'] if nZoom == 0 else outputs[f'DbscanClustering{nZoom - 1}']['OUTPUT'],
                'DISTANCE_BETWEEN_CLUSTER_MEMBERS_METERS': currMaxClustedDistance,
                'ID_FIELD_NAME': f'_cluster_id{nZoom}',
                'SIZE_FIELD_NAME': f'_cluster_size{nZoom}',
                'OUTPUT': parameters['OUTPUT'] if nZoom == parameters['NUMBER_OF_ZOOM_LEVELS'] - 1 else QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'DbscanClustering{nZoom}'] = processing.run('webmap_utilities:clusterization_by_distance', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            if nZoom == parameters['NUMBER_OF_ZOOM_LEVELS'] - 1 and parameters['OUTPUT'].sink.staticValue() != QgsProcessing.TEMPORARY_OUTPUT:
                clusterLayer: QgsVectorLayer = QgsVectorLayer(outputs[f'DbscanClustering{nZoom}']['OUTPUT'])
            else:
                clusterLayer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(outputs[f'DbscanClustering{nZoom}']['OUTPUT'])

            #Create attribute that controls visibility
            if not visibilityOffsetFieldAdded:
                visibilityOffsetFieldAdded = True
                vOffsetField = QgsField(visibilityAttribute, QVariant.Type.Int)
                clusterLayer.dataProvider().addAttributes([vOffsetField])
                clusterLayer.updateFields()

            if parameters['ISOLATED_FEATURES_ALWAYS_VISIBLE'] == True:
                self.showIsolatedFeatures(nZoom, clusterLayer, parameters)

            #Show cluster members
            self.showClusteredFeaturesByAttribute(nZoom, clusterLayer, parameters)

            #Show remaining features
            if nZoom == parameters['NUMBER_OF_ZOOM_LEVELS'] - 1:
                self.showRemainingFeatures(nZoom, clusterLayer, parameters)
            
            self.deleteAttribute(clusterLayer, f'_cluster_id{nZoom}')
            self.deleteAttribute(clusterLayer, f'_cluster_size{nZoom}')

            currStep += 1
            feedback.setCurrentStep(currStep)
            if feedback.isCanceled():
                return {}

        results['OUTPUT'] = outputs[f"DbscanClustering{parameters['NUMBER_OF_ZOOM_LEVELS'] - 1}"]['OUTPUT']

        global renamer
        renamer = AfterProcessingLayerRenamer('Clustered View')
        context.layerToLoadOnCompletionDetails(results['OUTPUT']).setPostProcessor(renamer)

        return results

    def showIsolatedFeatures(self, currentZoom: int, layer: QgsVectorLayer, parameters):
        visibilityAttribute = parameters['NEW_ATTRIBUTE_NAME']
        request = QgsFeatureRequest()
        reqContext = QgsExpressionContext()
        reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        request.setExpressionContext(reqContext)
        request.setFilterExpression(f'"_cluster_size{currentZoom}" < 2 and "{visibilityAttribute}" IS NULL')

        with edit(layer):
            for feature in layer.getFeatures(request):
                feature[visibilityAttribute] = currentZoom
                layer.updateFeature(feature)

    def showClusteredFeaturesByAttribute(self, currentZoom: int, layer: QgsVectorLayer, parameters):
        electionAttribute = parameters['ELECTION_ATTRIBUTE']
        visibilityAttribute = parameters['NEW_ATTRIBUTE_NAME']
        orderBy = 'True' if parameters['ELECTION_METHOD'] == 1 else 'False'
        query = f'array_contains(array_slice(array_sort(array_agg(to_real("{electionAttribute}"), group_by:="_cluster_id{currentZoom}", filter:="{visibilityAttribute}" IS NULL and "_cluster_size{currentZoom}" > 1), {orderBy}),0,0), to_real("{electionAttribute}"))'

        request = QgsFeatureRequest()
        reqContext = QgsExpressionContext()
        reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        request.setExpressionContext(reqContext)
        request.setFilterExpression(query)

        with edit(layer):
            for feature in layer.getFeatures(request):
                feature[visibilityAttribute] = currentZoom
                layer.updateFeature(feature)

    def showRemainingFeatures(self, currentZoom: int, layer: QgsVectorLayer, parameters):
        visibilityAttribute = parameters['NEW_ATTRIBUTE_NAME']

        request = QgsFeatureRequest()
        reqContext = QgsExpressionContext()
        reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        request.setExpressionContext(reqContext)
        request.setFilterExpression(f'"{visibilityAttribute}" IS NULL')

        with edit(layer):
            for feature in layer.getFeatures(request):
                feature[visibilityAttribute] = currentZoom if parameters['SHOW_ALL_AT_LAST_ZOOM_LEVEL'] == True else currentZoom + 1
                layer.updateFeature(feature)

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
        return 'Vector'

    def groupId(self):
        return 'Vector'

    def createInstance(self):
        return CreateClusteredVisualization()

    def shortHelpString(self):
        return """
            This algorithm divides a vector layer into clusters and only one feature of each cluster is chosen to be visible.
            This selection depends on the strategy (min or max) and the attribute chosen by the user. At each new zoom the initial distance defined by the user is divided by 2 and process of Clusterization and election of feature is done again.
            <h2>Input parameters</h2>
            <h3>Vector Layer (points)</h3>
            Point layer
            <h3>Attribute used to select cluster members</h3>
            The attribute that is used to select new visible features.
            <h3>Election method</h3>
            Strategy used to select new visible features.
            <h3>Minimum cluster size</h3>
            Minimum number of features to be considered a cluster
            <h3>Initial max. cluster member distance</h3>
            Minimum initial distance between members of a cluster.
            <h3>Number of zoom levels</h3>
            Number of zoom levels to apply this algorithm. After the last zoom level, all features become visible.
            <h3>Show allfeatures at last zoom level</h3>
            Indicates whether all features should be visible at the last zoom level.
            <h3>Always show isolated features</h3>
            Indicates whether isolated features (outside a cluster) will always be visible.
            <h3>Attribute name (that controls visibility)</h3>
            Name of the attribute to be created. This new attribute should be used together with the visibilitByOffset() function.
            <br />
        """