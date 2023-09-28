"""in'
Model exported as python.
Name : model
Group : 
With QGIS : 32207
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
import processing

class CreateAerialPerspective(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('DEM', 'DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('HILLSHADE', 'HILLSHADE', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('CONTRAST_MIN', 'Minimum constrast', type=QgsProcessingParameterNumber.Integer, minValue=-255, maxValue=255, defaultValue=-20))
        self.addParameter(QgsProcessingParameterNumber('CONTRAST_MAX', 'Maximum constrast', type=QgsProcessingParameterNumber.Integer, minValue=-255, maxValue=255, defaultValue=50))
        self.addParameter(QgsProcessingParameterRasterDestination('AerialPerspective', 'Aerial Perspective', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # DEM Stats
        alg_params = {
            'BAND': 1,
            'INPUT': parameters['DEM']
        }
        outputs['DemStats'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Translate (convert format)
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 6,  # Float32
            'EXTRA': '',
            'INPUT': parameters['HILLSHADE'],
            'NODATA': None,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['HillshadeFloat'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
		
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        demMin = outputs['DemStats']['MIN']
        demMax = outputs['DemStats']['MAX']
        
        contrastMin = parameters['CONTRAST_MIN']
        contrastMax = parameters['CONTRAST_MAX']
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
            'INPUT_B': outputs['HillshadeFloat']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ApDenorm'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Ap Denorm Stats
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ApDenorm']['OUTPUT']
        }
        outputs['ApDenormStats'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        
        apDenormMin = outputs['ApDenormStats']['MIN']
        apDenormMax = outputs['ApDenormStats']['MAX']
        apNorm = f'255*((A - {apDenormMin}) / ({apDenormMax} - {apDenormMin}))'

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
            'INPUT_A': outputs['ApDenorm']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 2,  # Byte
            'OUTPUT': parameters['AerialPerspective']
        }
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['RasterCalculator']['OUTPUT']
        return results

    def name(self):
        return 'aerial_perspective'

    def displayName(self):
        return 'Aerial Perspective'
    
    def group(self):
        return 'Raster'

    def groupId(self):
        return 'Raster'

    def createInstance(self):
        return CreateAerialPerspective()
    
    def shortHelpString(self):
        return """
        This algorithm creates a new hillshade, applying the Aerial Perspective effect to it. This effect consists of decreasing the contrast in lower regions and increasing it in higher regions.        
        <h2>Input parameters</h2>
        <h3>DEM</h3>
        DEM raster used to generate Hillshade.
        <h3>Hilshade</h3>
        Hillshade generated by the specified DEM raster.
        <h3>Minimum constrast</h3>
        Contrast applied in the lower regions.
        <h3>Maximum constrast</h3>
        Contrast applied in the higher regions.
        <br />
        """