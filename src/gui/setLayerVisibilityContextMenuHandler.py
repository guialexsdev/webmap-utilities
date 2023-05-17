from qgis.core import QgsMapLayer, QgsProject
from qgis.PyQt.QtWidgets import QMenu
from .layerVisibilityDialog import LayerVisibilityDialog
from ..utils.webmapCommons import Utils

class SetLayerVisibilityContextMenuHandler:
    def __init__(self, iface, parent=None):
        self.iface = iface
        self.parent = parent

    def handle(self, menu: QMenu, selectedLayers: list[QgsMapLayer]):
        action = menu.addAction('Set Layer Zoom Level Visibility...')

        defaultZoomMin = None
        defaultZoomMax = None

        if selectedLayers.__len__() == 1:
            predefinedScales = QgsProject.instance().viewSettings().mapScales()
            defaultZoomMin = Utils.scaleToZoomLevel(predefinedScales, selectedLayers[0].minimumScale())
            defaultZoomMax = Utils.scaleToZoomLevel(predefinedScales, selectedLayers[0].maximumScale())

        action.triggered.connect(lambda: LayerVisibilityDialog(self.iface, selectedLayers, defaultZoomMin, defaultZoomMax, self.parent).exec_())
