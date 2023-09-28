from qgis.core import QgsProcessingLayerPostProcessorInterface, QgsBrightnessContrastFilter, QgsBilinearRasterResampler

class CreateShadedReliefPostProcessing(QgsProcessingLayerPostProcessorInterface):
    def __init__(self, layer_name, blendMode, contrastFilter: QgsBrightnessContrastFilter):
        self.name = layer_name
        self.blendMode = blendMode
        self.contrastFilter = contrastFilter
        super().__init__()
        
    def postProcessLayer(self, layer, context, feedback):
        layer.setOpacity(0.5)
        resampleFilter = layer.resampleFilter()
        resampleFilter.setZoomedInResampler(QgsBilinearRasterResampler())
        resampleFilter.setZoomedOutResampler(QgsBilinearRasterResampler())
        layer.setName(self.name)
        layer.pipe().set(self.contrastFilter)
        layer.setBlendMode(self.blendMode)
