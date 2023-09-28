import math
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QMenu
from ..gui.setLayerVisibilityContextMenuHandler import SetLayerVisibilityContextMenuHandler

class EventListeners:
    def onContextMenuAboutToShow(iface, menu: QMenu):
        selectedLayers = iface.layerTreeView().selectedLayersRecursive()

        if selectedLayers is not None:
            menu.addSeparator()

            if QgsProject.instance().viewSettings().mapScales().__len__() > 0:
                SetLayerVisibilityContextMenuHandler(iface, menu.parent()).handle(menu, selectedLayers)

    def layerChangedUpdatesQuickInfo(iface, layer):
        if layer is not None:
            project = QgsProject.instance()
            predefinedScales = project.viewSettings().mapScales()

            if predefinedScales is None or predefinedScales.__len__() == 0:
                return

            minPredefinedScale = predefinedScales[0]
            maxPredefinedScale = predefinedScales[len(predefinedScales) - 1]

            minZoom = 0
            maxZoom = len(predefinedScales) - 1

            if layer.hasScaleBasedVisibility():
                minScale = int(math.floor(layer.minimumScale()))
                maxScale = int(math.floor(layer.maximumScale()))

                targetMinScale = min(predefinedScales, key=lambda x:abs(x-minScale))
                targetMaxScale = min(predefinedScales, key=lambda x:abs(x-maxScale))

                minZoom = 0 if targetMinScale > minPredefinedScale else predefinedScales.index(targetMinScale)
                maxZoom = len(predefinedScales) - 1 if targetMaxScale < maxPredefinedScale else predefinedScales.index(targetMaxScale)

            iface.mainWindow().statusBar().showMessage(f'{layer.name()} visibility: {minZoom} - {maxZoom}')
