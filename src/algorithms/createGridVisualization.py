"""
Model exported as python.
Name : model
Group : 
With QGIS : 32806
"""

from qgis.core import QgsProcessing, QgsProcessingOutputLayerDefinition, QgsProperty
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsField, edit, QgsFeatureRequest, QgsVectorLayer, QgsExpressionContext, QgsExpressionContextUtils

from qgis.PyQt.QtCore import QVariant

import processing
from .afterProcessingLayerRenamer import AfterProcessingLayerRenamer

class CreateGridVisualization(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterVectorLayer('VECTOR_LAYER', 'Vector Layer (points)', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('ID_ATTRIBUTE', 'ID attribute', type=QgsProcessingParameterField.Any, parentLayerParameterName='VECTOR_LAYER', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterExtent('EXTENT', 'Extent', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('GRID_SQUARE_LENGTH_METERS', 'Grid Square Length (meters)', type=QgsProcessingParameterNumber.Double, minValue=100, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('NUMBER_OF_ZOOMS', 'Number of zoom levels', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('NEW_ATTRIBUTE_NAME', 'Attribute name (that controls visibility)', multiLine=False, defaultValue='_visibility_offset'))
        self.addParameter(QgsProcessingParameterFeatureSink('OUTPUT', 'Grid View', type=QgsProcessing.SourceType.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        nSteps = parameters['NUMBER_OF_ZOOMS'] * 2 + 1
        currStep = 0
        feedback = QgsProcessingMultiStepFeedback(nSteps, model_feedback)
        toBeMerged = []
        results = {}
        outputs = {}

        squareSideSize = 2*parameters['GRID_SQUARE_LENGTH_METERS']
        newAttributeName = parameters['NEW_ATTRIBUTE_NAME']

        for nZoom in range(parameters['NUMBER_OF_ZOOMS']):
            squareSideSize = squareSideSize / 2
            
            feedback.pushInfo('Create grid')
            # Create grid
            alg_params = {
                'CRS': 'ProjectCrs',
                'EXTENT': parameters['EXTENT'],
                'HOVERLAY': 0,
                'HSPACING': squareSideSize,
                'TYPE': 0,  # Point
                'VOVERLAY': 0,
                'VSPACING': squareSideSize,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'CreateGrid{nZoom}'] = processing.run('native:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            currStep += 1
            feedback.setCurrentStep(currStep)
            if feedback.isCanceled():
                return {}

            feedback.pushInfo('Join attributes by nearest')
            # Join attributes by nearest
            alg_params = {
                'DISCARD_NONMATCHING': False,
                'FIELDS_TO_COPY': parameters['ID_ATTRIBUTE'],
                'INPUT': outputs[f'CreateGrid{nZoom}']['OUTPUT'],
                'INPUT_2': parameters['VECTOR_LAYER'],
                'MAX_DISTANCE': squareSideSize/2,
                'NEIGHBORS': 1,
                'PREFIX': '',
                'NON_MATCHING': QgsProcessing.TEMPORARY_OUTPUT,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'JoinAttributesByNearest{nZoom}'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            toBeMerged.append(outputs[f'JoinAttributesByNearest{nZoom}']['OUTPUT'])

            joinedLayer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(outputs[f'JoinAttributesByNearest{nZoom}']['OUTPUT'])
            joinedLayer.setName(str(nZoom))

            zOffsetField = QgsField(newAttributeName, QVariant.Type.Int)
            joinedLayer.dataProvider().addAttributes([zOffsetField])
            joinedLayer.updateFields()

            for feature in joinedLayer.getFeatures():
                with edit(joinedLayer):
                    feature[newAttributeName] = nZoom
                    joinedLayer.updateFeature(feature)

            currStep += 1
            feedback.setCurrentStep(currStep)
            if feedback.isCanceled():
                return {}

        feedback.pushInfo('Merge vector layers')
        # Merge vector layers
        alg_params = {
            'CRS': parameters['VECTOR_LAYER'],
            'LAYERS': toBeMerged,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
    
        currStep += 1
        feedback.setCurrentStep(currStep)
        if feedback.isCanceled():
            return {}
        
        feedback.pushInfo('Join attributes by field value')
        # Join attributes by field value
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': parameters['ID_ATTRIBUTE'],
            'FIELDS_TO_COPY': [newAttributeName],
            'FIELD_2': parameters['ID_ATTRIBUTE'],
            'INPUT': parameters['VECTOR_LAYER'],
            'INPUT_2': outputs['MergeVectorLayers']['OUTPUT'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREFIX': '',
            'NON_MATCHING': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByFieldValue'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        currStep += 1
        feedback.setCurrentStep(currStep)
        if feedback.isCanceled():
            return {}

        # Create spatial index
        alg_params = {
            'INPUT': outputs['JoinAttributesByFieldValue']['OUTPUT']
        }
        outputs['CreateSpatialIndexJoinSummary'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        currStep += 1
        feedback.setCurrentStep(currStep)
        if feedback.isCanceled():
            return {}

        feedback.pushInfo('Join by location (summary)')
        # Join by location (summary)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['VECTOR_LAYER'],
            'JOIN': outputs['CreateSpatialIndexJoinSummary']['OUTPUT'],
            'JOIN_FIELDS': [newAttributeName],
            'PREDICATE': [0,1,2,3,4],  # intersect,contain,equal,touch,overlap
            'SUMMARIES': [2],  # min
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['JoinAttributesByLocationSummary'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
    
        if parameters['OUTPUT'].sink.staticValue() == QgsProcessing.TEMPORARY_OUTPUT:
            finalLayer: QgsVectorLayer = context.temporaryLayerStore().mapLayer(outputs['JoinAttributesByLocationSummary']['OUTPUT'])
        else:
            finalLayer: QgsVectorLayer = QgsVectorLayer(outputs['JoinAttributesByLocationSummary']['OUTPUT'])

        request = QgsFeatureRequest()
        reqContext = QgsExpressionContext()
        reqContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(finalLayer))
        request.setExpressionContext(reqContext)
        request.setFilterExpression(f'"{newAttributeName}" IS NULL')
        
        with edit(finalLayer):
            idx = finalLayer.fields().indexFromName(f'{newAttributeName}_min')
            finalLayer.renameAttribute(idx, newAttributeName)

            for feature2 in finalLayer.getFeatures(request):
                feature2[newAttributeName] = parameters['NUMBER_OF_ZOOMS']
                finalLayer.updateFeature(feature2)

        results['OUTPUT'] = outputs['JoinAttributesByLocationSummary']['OUTPUT']

        global renamer
        renamer = AfterProcessingLayerRenamer('Grid View')
        context.layerToLoadOnCompletionDetails(results['OUTPUT']).setPostProcessor(renamer)

        return results

    def name(self):
        return 'Grid Visualization'

    def displayName(self):
        return 'Grid Visualization'

    def group(self):
        return 'Vector'

    def groupId(self):
        return 'Vector'

    def createInstance(self):
        return CreateGridVisualization()
    
    def shortHelpString(self):
        return """
            This algorithm creates a imaginary regular grid of points separated by a user-defined distance. Only the Feature closest to each point is displayed. At each new zoom a new grid is created (using a distance between points equal to half of the previous distance) and new Features are presented.
            <h2>Input parameters</h2>
            <h3>Vector Layer</h3>
            Point layer
            <h3>ID attribute</h3>
            Identifier attribute of each feature.
            <h3>Extent</h3>
            Target region where the imginary grid will be created.
            <h3>Distance between grid points (meters)</h3>
            Distance between grid points. Caution: Do not use very small distances for large regions.
            <h3>Number of zoom levels</h3>
            Number of zoom levels to apply this algorithm. After the last zoom level, all features become visible.
            <h3>Attribute name (that controls visibility)</h3>
            Name of the attribute to be created. This new attribute should be used together with the visibilitByOffset() function.
            <br />
        """