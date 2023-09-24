import math
from qgis.core import QgsProject, NULL, QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QMenu
from ..gui.setLayerVisibilityContextMenuHandler import SetLayerVisibilityContextMenuHandler
from ..gui.setPropertyContextMenuHandler import SetPropertyContextMenuHandler
from ..database.settingsManager import SettingsManager
from ..utils.webmapCommons import Utils
from ..model.variable import Variable

class EventListeners:
    def renderingCompleted():
        globalScope = QgsExpressionContextUtils.globalScope()
        for name in globalScope.variableNames():
            if name.startswith(Variable.TEMP_PREFIX):
                QgsExpressionContextUtils.removeGlobalVariable(name)

    def onContextMenuAboutToShow(iface, menu: QMenu):
        project = QgsProject.instance()
        selectedLayers = iface.layerTreeView().selectedLayersRecursive()

        if selectedLayers is not None:
            menu.addSeparator()
            scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
            settingsManager = SettingsManager.loadFromProject(scope)

            if settingsManager is not None:
                SetPropertyContextMenuHandler(iface, settingsManager, menu.parent()).handle(menu, selectedLayers)

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

            scope = QgsExpressionContextUtils.projectScope(QgsProject.instance())
            settingsManager = SettingsManager.loadFromProject(scope)

            if settingsManager is None:
                return

            tag = Utils.getLayerTag(layer, settingsManager.settings)
            minZoomFromVars = int(Utils.getVariable(tag, '_zoom_min', scope, None, minZoom)[1])
            maxZoomFromVars = int(Utils.getVariable(tag, '_zoom_max', scope, None, maxZoom)[1])

            if layer.hasScaleBasedVisibility():
                minScale = int(math.floor(layer.minimumScale()))
                maxScale = int(math.floor(layer.maximumScale()))

                targetMinScale = min(predefinedScales, key=lambda x:abs(x-minScale))
                targetMaxScale = min(predefinedScales, key=lambda x:abs(x-maxScale))

                minZoom = 0 if targetMinScale > minPredefinedScale else predefinedScales.index(targetMinScale)
                maxZoom = len(predefinedScales) - 1 if targetMaxScale < maxPredefinedScale else predefinedScales.index(targetMaxScale)

            if minZoomFromVars != NULL and minZoomFromVars is not None:
                minZoom = max(minZoom, int(minZoomFromVars))

            if maxZoomFromVars != NULL and minZoomFromVars is not None:
                maxZoom = min(maxZoom, int(maxZoomFromVars))

            iface.mainWindow().statusBar().showMessage(f'{layer.name()} visibility: {minZoom} - {maxZoom}')
