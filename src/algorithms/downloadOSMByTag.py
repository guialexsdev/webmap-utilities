"""
Model exported as python.
Name : Download OSM by Tag
Group : Webmap Utilities
With QGIS : 32806
"""

from qgis.core import QgsProcessingContext, QgsProcessing, QgsProject, QgsExpressionContextUtils
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterExtent
import processing

from ..database.settingsManager import SettingsManager
from ..model.variable import Variable

class DownloadOsmByTag(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterCrs('crs', 'CRS', defaultValue=QgsProject.instance().crs().authid()))
        self.addParameter(QgsProcessingParameterExtent('extent', 'Extent', defaultValue=None))

    def processAlgorithm(self, parameters, context: QgsProcessingContext, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        project         = QgsProject.instance()
        projectScope    = QgsExpressionContextUtils.projectScope(project)
        settingsManager = SettingsManager.loadFromProject(QgsProject.instance())
        settings        = settingsManager.settings

        queries = []

        for tag in settings.tags:
            keyVar    = Variable.formatVariableName(tag, '_osm_key')
            valuesVar = Variable.formatVariableName(tag, '_osm_values')
            typeVar   = Variable.formatVariableName(tag, '_osm_type')

            if projectScope.hasVariable(keyVar) and projectScope.hasVariable(typeVar):
                keys   = str(projectScope.variable(keyVar)).split(';')
                values = str(projectScope.variable(valuesVar)).split(';')
                type   = str(projectScope.variable(typeVar))

                for index in range(keys.__len__()):
                    queries.append((tag, keys[index], values[index], type))

        feedback = QgsProcessingMultiStepFeedback(5*queries.__len__(), model_feedback)
        results = {}
        context.setDefaultEncoding('utf8')

        step = 0
        for query in queries:
            outputs   = {}
            tag       = query[0]
            osmKey    = query[1]
            osmValue  = query[2]
            osmType   = query[3].lower()

            # Build query inside an extent
            alg_params = {
                'EXTENT': parameters['extent'],
                'KEY': osmKey,
                'SERVER': 'https://overpass-api.de/api/interpreter',
                'TIMEOUT': 25,
                'VALUE': osmValue
            }
            outputs['BuildQueryInsideAnExtent'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Download file
            alg_params = {
                'DATA': '',
                'METHOD': 0,  # GET
                'URL': outputs['BuildQueryInsideAnExtent']['OUTPUT_URL'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['DownloadFile'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            alg_params = {
                'FILE': outputs['DownloadFile']['OUTPUT']
            }
            outputs['ReadFile'] = processing.run('quickosm:openosmfile', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            if osmType.lower() == 'points':
                outputType = 'OUTPUT_POINTS'
            elif osmType == 'lines':
                outputType = 'OUTPUT_LINES'
            elif osmType == 'multilinestrings':
                outputType = 'OUTPUT_MULTILINESTRINGS'
            elif osmType == 'multipolygons':
                outputType = 'OUTPUT_MULTIPOLYGONS'
            elif osmType == 'other_relations':
                outputType = 'OUTPUT_OTHER_RELATIONS'

            buildingLyr = outputs['ReadFile'][outputType]
            layer = context.temporaryLayerStore().mapLayer(buildingLyr)
            layer.setProviderEncoding('utf8')
            layer.dataProvider().setEncoding('utf8')

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            alg_params = {
                 'EXPECTED_FIELDS': '',
                 'FIELD': 'other_tags',
                 'INPUT': layer,
                 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
             }
            
            outputs['ExplodeHstoreField'] = processing.run('native:explodehstorefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
 
            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Reproject layer
            alg_params = {
                'INPUT': outputs['ExplodeHstoreField']['OUTPUT'],
                'OPERATION': '',
                'TARGET_CRS': parameters['crs'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ReprojectLayer'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
            finalLayer = context.temporaryLayerStore().mapLayer(outputs['ReprojectLayer']['OUTPUT'])
            finalLayer.setName(tag)
            QgsProject.instance().addMapLayer(finalLayer)

        return results

    def name(self):
        return 'Download OSM by Tag'

    def displayName(self):
        return 'Download OSM by Tag'

    def group(self):
        return 'Webmap Utilities'

    def groupId(self):
        return 'Webmap Utilities'

    def createInstance(self):
        return DownloadOsmByTag()
