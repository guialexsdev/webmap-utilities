import processing
from qgis.core import QgsProcessing, QgsBrightnessContrastFilter, QgsProcessingContext
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.PyQt.QtGui import QPainter
from .createShadedReliefPostProcessing import CreateShadedReliefPostProcessing

class ShadedReliefCreator(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('DEM', 'DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('AP_INTENSITY', 'Aerial Perspective Intensity', type=QgsProcessingParameterNumber.Integer, minValue=-255, maxValue=255, defaultValue=60))
        self.addParameter(QgsProcessingParameterNumber('ANGLE_BETWEEN_LIGHT_SOURCES', 'Angle Between Light Sources', type=QgsProcessingParameterNumber.Double, minValue=10, maxValue=180, defaultValue=45))
        self.addParameter(QgsProcessingParameterNumber('Z_FACTOR', 'Z Factor', type=QgsProcessingParameterNumber.Double, defaultValue=1))
        self.addParameter(QgsProcessingParameterNumber('SCALE', 'Scale', type=QgsProcessingParameterNumber.Double, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterDestination('HILLSHADE_LAYER_BOTTOM', 'Bottom Hillshade', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('HILLSHADE_LAYER_TOP', 'Top Hillshade', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context: QgsProcessingContext, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}
        step = 0

        # DEM Stats
        alg_params = {
            'BAND': 1,
            'INPUT': parameters['DEM']
        }
        outputs['DemStats'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        step = step + 1
        feedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}
        
        for idx in range(2):
            if idx == 0:
                azimuth = 360 - float(parameters['ANGLE_BETWEEN_LIGHT_SOURCES'])/2
            else:
                azimuth = float(parameters['ANGLE_BETWEEN_LIGHT_SOURCES'])/2

            # Hillshade
            alg_params = {
                'ALTITUDE': 45,
                'AZIMUTH': azimuth,
                'BAND': 1,
                'COMBINED': False,
                'COMPUTE_EDGES': False,
                'EXTRA': '',
                'INPUT': parameters['DEM'],
                'MULTIDIRECTIONAL': False,
                'OPTIONS': '',
                'SCALE': parameters['SCALE'],
                'ZEVENBERGEN': False,
                'Z_FACTOR': parameters['Z_FACTOR'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'Hillshade{idx}'] = processing.run('gdal:hillshade', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Translate (convert format)
            alg_params = {
                'COPY_SUBDATASETS': False,
                'DATA_TYPE': 6,  # Float32
                'EXTRA': '',
                'INPUT': outputs[f'Hillshade{idx}']['OUTPUT'],
                'NODATA': None,
                'OPTIONS': '',
                'TARGET_CRS': None,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'HillshadeFloat{idx}'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Hillshade Stats
            alg_params = {
                'BAND': 1,
                'INPUT': outputs[f'HillshadeFloat{idx}']['OUTPUT']
            }
            outputs[f'HillshadeStats{idx}'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            demMin = outputs['DemStats']['MIN']
            demMax = outputs['DemStats']['MAX']
            
            contrastMin = -parameters['AP_INTENSITY']
            contrastMax = parameters['AP_INTENSITY']
            contrast = f'({contrastMax} - {contrastMin})*((A - {demMin}) / ({demMax} - {demMin})) + {contrastMin}'
            contrastFactor = f'(259*(({contrast}) + 255)) / (255*(259 - ({contrast})))'
            
            apDenorm = f'({contrastFactor})*(B - 128) + 128'
            feedback.pushInfo(apDenorm)
            
            # AP Denorm
            alg_params = {
                'BAND_A': 1,
                'BAND_B': None,
                'BAND_C': None,
                'BAND_D': None,
                'BAND_E': None,
                'BAND_F': None,
                'EXTRA': '',
                'FORMULA': apDenorm,
                'INPUT_A': parameters['DEM'],
                'INPUT_B': outputs[f'HillshadeFloat{idx}']['OUTPUT'],
                'INPUT_C': None,
                'INPUT_D': None,
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 5,  # Float32
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'ApDenorm{idx}'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # Ap Denorm Stats
            alg_params = {
                'BAND': 1,
                'INPUT': outputs[f'ApDenorm{idx}']['OUTPUT']
            }
            outputs[f'ApDenormStats{idx}'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            step = step + 1
            feedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            apDenormMin = outputs[f'ApDenormStats{idx}']['MIN']
            apDenormMax = outputs[f'ApDenormStats{idx}']['MAX']
            apNorm = f'255*((A - {apDenormMin}) / ({apDenormMax} - {apDenormMin}))'

            rasterName = f"HILLSHADE_LAYER_{'TOP' if idx == 1 else 'BOTTOM'}"

            # Raster calculator
            alg_params = {
                'BAND_A': 1,
                'BAND_B': None,
                'BAND_C': None,
                'BAND_D': None,
                'BAND_E': None,
                'BAND_F': None,
                'EXTRA': '',
                'FORMULA': apNorm,
                'INPUT_A': outputs[f'ApDenorm{idx}']['OUTPUT'],
                'INPUT_B': None,
                'INPUT_C': None,
                'INPUT_D': None,
                'INPUT_E': None,
                'INPUT_F': None,
                'NO_DATA': None,
                'OPTIONS': '',
                'RTYPE': 2,  # Byte
                'OUTPUT': parameters[rasterName]
            }

            outputs[f'RasterCalculator{idx}'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results[rasterName] = outputs[f'RasterCalculator{idx}']['OUTPUT']

        bottomContrastFilter = QgsBrightnessContrastFilter()
        bottomContrastFilter.setContrast(-25)
        bottomContrastFilter.setBrightness(40)
        bottomBlendMode = QPainter.CompositionMode.CompositionMode_Multiply

        global renamer
        renamer = CreateShadedReliefPostProcessing('Hillshade (Bottom)', bottomBlendMode, bottomContrastFilter)
        context.layerToLoadOnCompletionDetails(results['HILLSHADE_LAYER_BOTTOM']).setPostProcessor(renamer)

        topContrastFilter = QgsBrightnessContrastFilter()
        topContrastFilter.setContrast(-25)
        topContrastFilter.setBrightness(-40)
        topBlendMode = QPainter.CompositionMode.CompositionMode_Overlay

        global renamer2
        renamer2 = CreateShadedReliefPostProcessing('Hillshade (Top)', topBlendMode, topContrastFilter)
        context.layerToLoadOnCompletionDetails(results['HILLSHADE_LAYER_TOP']).setPostProcessor(renamer2)

        return results
    
    def name(self):
        return 'shaded_relief'

    def displayName(self):
        return 'Create Shaded Relief w/ Aerial Perspective'
    
    def group(self):
        return 'Raster'

    def groupId(self):
        return 'Raster'

    def createInstance(self):
        return ShadedReliefCreator()

    def shortHelpString(self):
        return """
        Create 2 shaded reliefs using two light sources and Aerial Perspective (higher areas receives more contrast than lower areas).
        <h2>Input parameters</h2>
        <h3>Aerial Perspective Intensity</h3>
        Increase/decrease the contrast between higher and lower altitudes. Small values decrease the effect of Aerial Perspective.
        <h3>Angle Between Light Sources</h3>
        Angle between the two light sources. Valid values: 0 - 180. Avoid extreme values, you should stay between 30 - 70 for better results.
        <h3>Z factor</h3>
        Vertical exaggeration. This parameter is useful when the Z units differ from the X and Y units, for example feet and meters. You can use this parameter to adjust for this. Increasing the value of this parameter will exaggerate the final result (making it look more “hilly”). The default is 1 (no exaggeration).
        <h3>Scale</h3>
        Ratio of vertical units to horizontal
        <h2>Outputs</h2>
        <h3>Hillshade Top and Bottom</h3>
        <p>Two raster layers will be created. Hillshade (top) must always be above the Hillshade (bottom). Manually change the order of these layers if they were created in a different order.</p>
        <br />
        """