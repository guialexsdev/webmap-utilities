"""
Model exported as python.
Name : Download OSM by Tag
Group : Webmap Utilities
With QGIS : 32806
"""

from qgis.core import QgsProcessingContext, QgsProcessing, QgsProject, QgsExpressionContextUtils, QgsMessageLog
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterEnum
import processing

from ..algorithms.osmQueryBuilder import OSMQueryBuilder
from ..database.settingsManager import SettingsManager
from ..model.variable import Variable

class DownloadOsmByTag(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

        settingsManager = SettingsManager.loadFromProject(QgsProject.instance())
        self.variablesManager = settingsManager.variablesManager
        self.settings = settingsManager.settings
        self.tagsToDownload = []

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterCrs('crs', 'CRS', defaultValue=QgsProject.instance().crs().authid()))
        self.addParameter(QgsProcessingParameterExtent('extent', 'Extent', defaultValue=None))

        for tag in self.settings.tags:
            if self.variablesManager.tagHasProperties(tag, ['_osm_query','_geometry_type']):
                self.tagsToDownload.append(tag)

        self.addParameter(
            QgsProcessingParameterEnum(
                'tags', 
                'Tags',
                options=self.tagsToDownload, 
                allowMultiple=True, 
                usesStaticStrings=False, 
                defaultValue=list(range(self.tagsToDownload.__len__()))
            )
        )

    def processAlgorithm(self, parameters, context: QgsProcessingContext, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback     = QgsProcessingMultiStepFeedback(5*self.tagsToDownload.__len__(), model_feedback)
        project      = QgsProject.instance()
        projectScope = QgsExpressionContextUtils.projectScope(project)
        queryBuilders: list[OSMQueryBuilder] = []

        for index in parameters['tags']:
            tag = self.tagsToDownload[index]
            osmQueryVar = Variable.formatVariableName(tag, '_osm_query')
            geomTypeVar = Variable.formatVariableName(tag, '_geometry_type')

            if projectScope.hasVariable(osmQueryVar):
                if projectScope.hasVariable(geomTypeVar):
                    queriesRaw = str(projectScope.variable(osmQueryVar)).split(';')
                    geomType = str(projectScope.variable(geomTypeVar))

                    builder = OSMQueryBuilder(tag, geomType)
                    builder.setBBox(str(parameters['extent']))

                    for q in queriesRaw:
                        parts = q.split('=')

                        if parts.__len__() != 2:
                            model_feedback.pushWarning(f"Invalid query: {q}. Not in format <key>=<value>. Skipping...")
                            continue

                        builder.addQueryItem(parts[0].lower().strip(), parts[1].lower().strip())

                    if builder.items.__len__() > 0:
                        queryBuilders.append(builder)
                else:
                    feedback.pushWarning(f"Tag {tag} doesn't have property [_osm_query] and will not be downloaded.")
            else:
                feedback.pushWarning(f"Tag {tag} doesn't have property [_geometry_type] and will not be downloaded.")

        results  = {}
        context.setDefaultEncoding('utf8')

        if queryBuilders.__len__() == 0:
            feedback.pushWarning('Nothing to download')
            return {}

        step = 0
        for query in queryBuilders:
            outputs   = {}
            tag       = query.id

            # Download file
            alg_params = {
                'DATA': query.toQueryString(),
                'METHOD': 1, # POST
                'URL': 'http://overpass-api.de/api/interpreter',
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

            if query.geomType == 'points':
                outputType = 'OUTPUT_POINTS'
            elif query.geomType == 'lines':
                outputType = 'OUTPUT_LINES'
            elif query.geomType == 'multilinestrings':
                outputType = 'OUTPUT_MULTILINESTRINGS'
            elif query.geomType == 'multipolygons':
                outputType = 'OUTPUT_MULTIPOLYGONS'
            elif query.geomType == 'other':
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
           
            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Create spatial index
            alg_params = {
                'INPUT': outputs['ReprojectLayer']['OUTPUT']
            }
            outputs['CreateSpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}
            
            alg_params = {
                'CLIP': True,
                'EXTENT': parameters['extent'],
                'INPUT': outputs['CreateSpatialIndex']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExtractclipByExtent'] = processing.run('native:extractbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            
            finalLayer = context.temporaryLayerStore().mapLayer(outputs['ExtractclipByExtent']['OUTPUT'])
            finalLayer.setName(tag)
            QgsProject.instance().addMapLayer(finalLayer)

            results[tag] = outputs['ExtractclipByExtent']['OUTPUT']

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
    
    def shortHelpString(self):
        return """
Download OSM data of all tagged layers. Tagged layers must contain "_osm_query" and "_geometry_type" properties!
        <h2>Input parameters</h2>
        <h3>CRS</h3>
Output CRS of downloaded layers.
        <h3>Extent</h3>
Extent of downloaded layers
        <h3>Tags</h3>
List of tags available for download. All tags checked as default.
        <h2>Outputs</h2>
        <h3>Vector layer per tag</h3>
        <p>Multiple temporary layers will be added to the project, each one representing a tag.</p>
        <br />
        <p align="right">Algorithm author: Guilherme Alexsander Pereira (guilhermealexs.dev@gmail.com)</p>
        """