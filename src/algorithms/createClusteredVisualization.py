import processing
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
from qgis.PyQt.QtCore import QVariant

from .layer.vectorLayerManager import VectorLayerManager
from .afterProcessingLayerRenamer import AfterProcessingLayerRenamer

class CreateClusteredVisualization(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.step = 0

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
        nSteps = parameters['NUMBER_OF_ZOOM_LEVELS'] * 4
        feedback = QgsProcessingMultiStepFeedback(nSteps, model_feedback)

        currMaxClustedDistance = 2*parameters['INITIAL_MAX_CLUSTER_MEMBER_DISTANCE']
        visibilityAttribute = parameters['NEW_ATTRIBUTE_NAME']
        lastZoomLevel = parameters['NUMBER_OF_ZOOM_LEVELS'] - 1

        results = {}
        outputs = {}

        for nZoom in range(parameters['NUMBER_OF_ZOOM_LEVELS']):
            currMaxClustedDistance = currMaxClustedDistance / 2

            # Clusterization by distance
            alg_params = {
                'VECTOR_LAYER': parameters['VECTOR_LAYER'] if nZoom == 0 else outputs[f'DbscanClustering{nZoom - 1}']['OUTPUT'],
                'DISTANCE_BETWEEN_CLUSTER_MEMBERS_METERS': currMaxClustedDistance,
                'ID_FIELD_NAME': f'_cluster_id{nZoom}',
                'SIZE_FIELD_NAME': f'_cluster_size{nZoom}',
                'OUTPUT': parameters['OUTPUT'] if nZoom == lastZoomLevel else QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'DbscanClustering{nZoom}'] = processing.run(
                'webmap_utilities:clusterization_by_distance', 
                alg_params, 
                context=context, 
                feedback=feedback, 
                is_child_algorithm=True
            )

            layer = VectorLayerManager(
                outputs[f'DbscanClustering{nZoom}']['OUTPUT'],
                feedback,
                context,
                parameters['OUTPUT']
            )

            #Create attribute that controls visibility
            layer.createField(visibilityAttribute, QVariant.Type.Int)

            if parameters['ISOLATED_FEATURES_ALWAYS_VISIBLE'] == True:
                query = f'"_cluster_size{nZoom}" < 2 and "{visibilityAttribute}" IS NULL'
                layer.setAttributeValueByExpression(parameters['NEW_ATTRIBUTE_NAME'], query, nZoom)

            self.updateProgress(feedback)
            
            #Show cluster members
            electionAttr = parameters['ELECTION_ATTRIBUTE']
            orderBy = 'True' if parameters['ELECTION_METHOD'] == 1 else 'False'
            query = f'array_contains(array_slice(array_sort(array_agg(to_real("{electionAttr}"), group_by:="_cluster_id{nZoom}", filter:="{visibilityAttribute}" IS NULL and "_cluster_size{nZoom}" > 1), {orderBy}),0,0), to_real("{electionAttr}"))'
            layer.setAttributeValueByExpression(parameters['NEW_ATTRIBUTE_NAME'], query, nZoom)

            #Show remaining features
            if nZoom == parameters['NUMBER_OF_ZOOM_LEVELS'] - 1:
                value = nZoom if parameters['SHOW_ALL_AT_LAST_ZOOM_LEVEL'] == True else nZoom + 1
                layer.setValueOfNullAttributes(visibilityAttribute, value)
            
            layer.deleteAttribute(f'_cluster_id{nZoom}')
            layer.deleteAttribute(f'_cluster_size{nZoom}')

            self.updateProgress(feedback)

        results['OUTPUT'] = outputs[f"DbscanClustering{lastZoomLevel}"]['OUTPUT']

        global renamer
        renamer = AfterProcessingLayerRenamer('Clustered View')
        context.layerToLoadOnCompletionDetails(results['OUTPUT']).setPostProcessor(renamer)

        return results

    def updateProgress(self, feedback):
        self.step += 1
        feedback.setCurrentStep(self.step)
        if feedback.isCanceled():
            return {}

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
            Visit <a href="https://github.com/guialexsdev/webmap-utilities">https://github.com/guialexsdev/webmap-utilities</a> to learn more!
        """