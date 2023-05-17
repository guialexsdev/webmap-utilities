from qgis.core import QgsProcessing, QgsBrightnessContrastFilter, QgsBilinearRasterResampler, QgsProcessingContext, QgsRasterLayer, QgsMapLayer, QgsProject
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.PyQt.QtGui import QPainter
import processing

class ShadedReliefCreator(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('dem', 'dem', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('ap_intensity', 'Aerial Perspective Intensity', type=QgsProcessingParameterNumber.Integer, minValue=-255, maxValue=255, defaultValue=60))
        self.addParameter(QgsProcessingParameterNumber('angle_between_light_sources', 'Angle Between Light Sources', type=QgsProcessingParameterNumber.Double, minValue=10, maxValue=180, defaultValue=45))
        self.addParameter(QgsProcessingParameterNumber('z_factor', 'Z Factor', type=QgsProcessingParameterNumber.Double, defaultValue=1))
        self.addParameter(QgsProcessingParameterNumber('scale', 'Scale', type=QgsProcessingParameterNumber.Double, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterDestination('HillshadeLayerBottom', 'Bottom Hillshade', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('HillshadeLayerTop', 'Top Hillshade', createByDefault=True, defaultValue=None))

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
            'INPUT': parameters['dem']
        }
        outputs['DemStats'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        step = step + 1
        feedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}
        
        for idx in range(2):
            if idx == 0:
                azimuth = 360 - float(parameters['angle_between_light_sources'])/2
            else:
                azimuth = float(parameters['angle_between_light_sources'])/2

            # Hillshade
            alg_params = {
                'ALTITUDE': 45,
                'AZIMUTH': azimuth,
                'BAND': 1,
                'COMBINED': False,
                'COMPUTE_EDGES': False,
                'EXTRA': '',
                'INPUT': parameters['dem'],
                'MULTIDIRECTIONAL': False,
                'OPTIONS': '',
                'SCALE': parameters['scale'],
                'ZEVENBERGEN': False,
                'Z_FACTOR': parameters['z_factor'],
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
            
            contrastMin = -parameters['ap_intensity']
            contrastMax = parameters['ap_intensity']
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
                'INPUT_A': parameters['dem'],
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


            rasterName = f"HillshadeLayer{'Top' if idx == 1 else 'Bottom'}"

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
            
            layer: QgsMapLayer = QgsRasterLayer(outputs[f'RasterCalculator{idx}']['OUTPUT'])
            layer.setOpacity(0.5)
            resampleFilter = layer.resampleFilter()
            resampleFilter.setZoomedInResampler(QgsBilinearRasterResampler())
            resampleFilter.setZoomedOutResampler(QgsBilinearRasterResampler())
            layer.setName(rasterName)

            if idx == 0:
                contrastFilter = QgsBrightnessContrastFilter()
                contrastFilter.setContrast(-25)
                contrastFilter.setBrightness(40)
                layer.pipe().set(contrastFilter)
                layer.setBlendMode(QPainter.CompositionMode.CompositionMode_Multiply)
            else:
                contrastFilter = QgsBrightnessContrastFilter()
                contrastFilter.setContrast(-25)
                contrastFilter.setBrightness(-40)
                layer.pipe().set(contrastFilter)
                layer.setBlendMode(QPainter.CompositionMode.CompositionMode_Overlay)

            QgsProject.instance().addMapLayer(layer)

            results[rasterName] = outputs[f'RasterCalculator{idx}']['OUTPUT']

        return results
    
    def name(self):
        return 'Aerial Perspective'

    def displayName(self):
        return 'Aerial Perspective'

    def group(self):
        return 'Webmap Utilities'

    def groupId(self):
        return 'Webmap Utilities'

    def createInstance(self):
        return ShadedReliefCreator()
