"""
Model exported as python.
Name : clusterizer
Group : 
With QGIS : 32810
"""

import processing
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterNumber, QgsProcessingParameterString

class CreateClusterizationByDistance(QgsProcessingAlgorithm):
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('VECTOR_LAYER', 'Vector Layer', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('DISTANCE_BETWEEN_CLUSTER_MEMBERS_METERS', 'Distance between cluster members (meters)', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('ID_FIELD_NAME', 'Name for cluster id attribute', multiLine=False, defaultValue='CLUSTER_ID'))
        self.addParameter(QgsProcessingParameterString('SIZE_FIELD_NAME', 'Name for cluster size attribute', multiLine=False, defaultValue='CLUSTER_SIZE'))
        self.addParameter(QgsProcessingParameterFeatureSink('OUTPUT', 'Clusterized', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
        results = {}
        outputs = {}

        # Create spatial index (input)
        alg_params = {
            'INPUT': parameters['VECTOR_LAYER']
        }
        outputs['InputIndexed'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        bufferSize = parameters['DISTANCE_BETWEEN_CLUSTER_MEMBERS_METERS']
        feedback.pushInfo('Bufferizing... Buffer size = {}'.format(bufferSize))

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': bufferSize,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['InputIndexed']['OUTPUT'],#parameters['VECTOR_LAYER'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        feedback.pushInfo('Dissolving...')
        # Dissolve
        alg_params = {
            'FIELD': [''],
            'INPUT': outputs['Buffer']['OUTPUT'],
            'SEPARATE_DISJOINT': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        idAttributeName = parameters['ID_FIELD_NAME']
        feedback.pushInfo('Generating unique {} for each cluster...'.format(idAttributeName))

        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': idAttributeName,
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': '@id',
            'INPUT': outputs['Dissolve']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
        
        feedback.pushInfo('Creating spatial index...')

        # Create spatial index (field calculator)
        alg_params = {
            'INPUT': outputs['FieldCalculator']['OUTPUT']
        }
        outputs['CreateSpatialIndexFieldCalculator'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        feedback.pushInfo('Counting clusters size...')

        # Join attributes by location (summary)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['CreateSpatialIndexFieldCalculator']['OUTPUT'],
            'JOIN': outputs['InputIndexed']['OUTPUT'],#parameters['VECTOR_LAYER'],
            'JOIN_FIELDS': ['fid'],
            'PREDICATE': [1],  # contain
            'SUMMARIES': [0],  # count
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocationSummary'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}
        
        feedback.pushInfo('Creating spatial index...')

        # Create spatial index (join summary)
        alg_params = {
            'INPUT': outputs['JoinAttributesByLocationSummary']['OUTPUT']
        }
        outputs['CreateSpatialIndexJoinSummary'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}
        
        feedback.pushInfo('Transfering cluster id and cluster size to the input vector layer')

        # Join attributes by location
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['InputIndexed']['OUTPUT'],#parameters['VECTOR_LAYER'],
            'JOIN': outputs['CreateSpatialIndexJoinSummary']['OUTPUT'],
            'JOIN_FIELDS': [parameters['ID_FIELD_NAME'],'fid_count'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREDICATE': [5],  # are within
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocation'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        clusterSizeAttribute = parameters['SIZE_FIELD_NAME']
        feedback.pushInfo('Renaming attribute fid_count to {}'.format(clusterSizeAttribute))

        # Rename field
        alg_params = {
            'FIELD': 'fid_count',
            'INPUT': outputs['JoinAttributesByLocation']['OUTPUT'],
            'NEW_NAME': clusterSizeAttribute,
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['RenameField'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['RenameField']['OUTPUT']

        return results

    def name(self):
        return 'clusterization_by_distance'

    def displayName(self):
        return 'Clusterization by distance'

    def group(self):
        return 'Vector'

    def groupId(self):
        return 'Vector'

    def createInstance(self):
        return CreateClusterizationByDistance()
