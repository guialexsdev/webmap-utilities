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
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsMapLayer, QgsField, QgsDefaultValue, edit
from qgis.PyQt.QtCore import QVariant

import processing

class CreateGridVisualization(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterVectorLayer('vector_layer', 'Vector Layer', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('id_attribute', 'ID attribute', type=QgsProcessingParameterField.Any, parentLayerParameterName='vector_layer', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterExtent('extent', 'Extent', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('grid_square_length_meters', 'Grid Square Length (meters)', type=QgsProcessingParameterNumber.Double, minValue=100, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('number_of_zooms', 'Number of zooms', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('GridView', 'Grid View', type=QgsProcessing.SourceType.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        nSteps = parameters['number_of_zooms'] * 2 + 1
        currStep = 0
        feedback = QgsProcessingMultiStepFeedback(nSteps, model_feedback)
        toBeMerged = []
        results = {}
        outputs = {}

        squareSideSize = 2*parameters['grid_square_length_meters']
        maxNearestDistance = parameters['grid_square_length_meters']

        for nZoom in range(parameters['number_of_zooms']):
            squareSideSize = squareSideSize / 2
            
            # Create grid
            alg_params = {
                'CRS': 'ProjectCrs',
                'EXTENT': parameters['extent'],
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

            # Join attributes by nearest
            alg_params = {
                'DISCARD_NONMATCHING': False,
                'FIELDS_TO_COPY': parameters['id_attribute'],
                'INPUT': outputs[f'CreateGrid{nZoom}']['OUTPUT'],
                'INPUT_2': parameters['vector_layer'],
                'MAX_DISTANCE': squareSideSize/2,
                'NEIGHBORS': 1,
                'PREFIX': '',
                'NON_MATCHING': QgsProcessing.TEMPORARY_OUTPUT,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'JoinAttributesByNearest{nZoom}'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            toBeMerged.append(outputs[f'JoinAttributesByNearest{nZoom}']['OUTPUT'])

            joinedLayer = context.temporaryLayerStore().mapLayer(outputs[f'JoinAttributesByNearest{nZoom}']['OUTPUT'])
            joinedLayer.setName(str(nZoom))

            zOffsetField = QgsField('_grid_zoom_offset', QVariant.Type.Int)
            joinedLayer.dataProvider().addAttributes([zOffsetField])
            joinedLayer.updateFields()

            for feature in joinedLayer.getFeatures():
                    with edit(joinedLayer):
                        feature['_grid_zoom_offset'] = nZoom
                        joinedLayer.updateFeature(feature)

            currStep += 1
            feedback.setCurrentStep(currStep)
            if feedback.isCanceled():
                return {}

        # Merge vector layers
        alg_params = {
            'CRS': parameters['vector_layer'],
            'LAYERS': toBeMerged,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
    
        currStep += 1
        feedback.setCurrentStep(currStep)
        if feedback.isCanceled():
            return {}
        
        # Join attributes by field value
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': parameters['id_attribute'],
            'FIELDS_TO_COPY': ['_grid_zoom_offset'],
            'FIELD_2': parameters['id_attribute'],
            'INPUT': parameters['vector_layer'],
            'INPUT_2': outputs['MergeVectorLayers']['OUTPUT'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByFieldValue'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        currStep += 1
        feedback.setCurrentStep(currStep)
        if feedback.isCanceled():
            return {}

        # Join by location (summary)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['vector_layer'],
            'JOIN': outputs['JoinAttributesByFieldValue']['OUTPUT'],
            'JOIN_FIELDS': ['_grid_zoom_offset'],
            'PREDICATE': [0,1,2,3,4],  # intersect,contain,equal,touch,overlap
            'SUMMARIES': [2],  # min
            'OUTPUT': parameters['GridView']
        }
        outputs['JoinAttributesByLocationSummary'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['GridView'] = outputs['JoinAttributesByLocationSummary']['OUTPUT']

        return results

    def name(self):
        return 'Grid Visualization'

    def displayName(self):
        return 'Grid Visualization'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return CreateGridVisualization()
