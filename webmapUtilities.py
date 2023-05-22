# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WebmapUtilities
                                 A QGIS plugin
 Widgets and python functions to help webmap creators.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-04-27
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Guilherme Alexsander Periera
        email                : guilhermealexs.pereira@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import math
import os.path

from qgis.core import QgsProject, QgsExpressionContextUtils, QgsMessageLog
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar, QComboBox, QLabel

from .resources import *
from .src.expressions.generalControlExpessions import *
from .src.expressions.visibilityControlExpressions import *
from .src.utils.layerTreeOrganizer import LayerTreeOrganizer
from .src.model.variable import Variable
from .src.database.settingsManager import SettingsManager
from .src.gui.settingsDialog import SettingsDialog
from .src.gui.eventListeners import EventListeners
from .src.algorithms.downloadOSMByTag import DownloadOsmByTag
from .src.algorithms.shadedReliefCreator import ShadedReliefCreator
import processing

class WebmapUtilities:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # Save reference to the QGIS interface
        self.tocSetPropertyActions = {}
        self.toolbar = None
        self.iface: QgisInterface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'WebmapUtilities_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = '&Webmap Utilities'
        self.tagRequiredActions: list[QAction] = []
        self.zoomLevelComboWidget = None

    def createToolbar(self, name):
        if self.toolbar is None:
            self.toolbar: QToolBar = self.iface.addToolBar(name)
            self.toolbar.setObjectName("WebmapToolbar")

    def addButtonToCustomToolbar(self, text, iconPath, enabled, callback):
        icon = QIcon(iconPath)
        action = QAction(icon, text, self.iface.mainWindow())
        action.setEnabled(enabled)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
        self.actions.append(action)
        return action
    
    def addWidgetToCustomToolbar(self, widget):
        self.actions.append(self.toolbar.addWidget(widget))

    def initGui(self):
        self.toolbar = None
        for toolbar in self.iface.mainWindow().findChildren(QToolBar):
            if toolbar.objectName() == 'WebmapToolbar':
                self.toolbar = toolbar

                actionsToRemove = self.toolbar.actions()
                for action in actionsToRemove:
                    self.toolbar.removeAction(action)

        if self.toolbar is None:
            self.createToolbar("Webmap Utilities Toolbar")

        isProjectInitialized = self.isProjectInitialized()
        QgsMessageLog.logMessage(str(isProjectInitialized), "Webmap Plugin Flow")

        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.addButtonToCustomToolbar(
            'Initialize Project',
            ':/icons/configure_project.png',
            True,
            self.runConfigureProject
        )

        tagRequiredAction = self.addButtonToCustomToolbar(
            'Settings',
            ':/icons/settings.png',
            isProjectInitialized,
            self.runSettingsDialog
        )
        self.tagRequiredActions.append(tagRequiredAction)

        tagRequiredAction = self.addButtonToCustomToolbar(
            'Apply Style',
            ':/icons/apply_style.png',
            isProjectInitialized,
            self.runApplyStyleDialog
        )
        self.tagRequiredActions.append(tagRequiredAction)

        tagRequiredAction = self.addButtonToCustomToolbar(
            'Apply Structure',
            ':/icons/apply_structure.png',
            isProjectInitialized,
            self.runApplyStructure
        )
        self.tagRequiredActions.append(tagRequiredAction)

        tagRequiredAction = self.addButtonToCustomToolbar(
            'OSM Downloader',
            ':/icons/osm.png',
            isProjectInitialized,
            self.runOSMDownloader
        )
        self.tagRequiredActions.append(tagRequiredAction)

        self.toolbar.addSeparator()

        self.addButtonToCustomToolbar(
            'Shaded Relief Creator',
            ':/icons/relief_creator.png',
            True,
            self.runShadedReliefCreator
        )

        self.toolbar.addSeparator()
        self.addZoomLevelWidget()

        QgsProject().instance().viewSettings().mapScalesChanged.connect(self.addZoomLevelWidget)

        self.iface.projectRead.connect(self.onProjectRead)
        self.iface.layerTreeView().contextMenuAboutToShow.connect(self.contextMenuAboutToShow)
        self.iface.currentLayerChanged.connect(self.currentLayerChanged)

    def unload(self):
        self.iface.layerTreeView().contextMenuAboutToShow.disconnect(self.contextMenuAboutToShow)
        self.iface.currentLayerChanged.disconnect(self.currentLayerChanged)

        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removeToolBarIcon(action)

    def isProjectInitialized(sef):
        return QgsExpressionContextUtils.projectScope(QgsProject.instance()).hasVariable('webmap_settings')
    
    def setRequiredActionsEnabled(self, enabled):
        for action in self.tagRequiredActions:
            action.setEnabled(enabled)

    def onProjectRead(self):
        self.setRequiredActionsEnabled(self.isProjectInitialized())

    def runConfigureProject(self):
        mercatorScales = [554678932,277339466,138669733,69334866,34667433,17333716,8666858,4333429,2166714,1083357,541678,270839,135419,67709,33854,16927,8463,4231,2115]
        viewSettings = QgsProject().instance().viewSettings()
        viewSettings.setMapScales(mercatorScales)
        viewSettings.setUseProjectScales(True)

        if not self.isProjectInitialized():
            project = QgsProject().instance()
            settingsManager = SettingsManager()
            settingsManager.persistToProject(project)

            self.setRequiredActionsEnabled(True)

    def runOSMDownloader(self):
        settingsManager = SettingsManager.loadFromProject(QgsProject().instance())

        if settingsManager is None:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Project not initialized. Click on the plug icon first to initialize the project.")
            return

        alg: DownloadOsmByTag = DownloadOsmByTag()
        processing.execAlgorithmDialog(alg)

    def runShadedReliefCreator(self):
        alg: ShadedReliefCreator = ShadedReliefCreator()
        processing.execAlgorithmDialog(alg)

    def runSettingsDialog(self):
        self.dlg = SettingsDialog(self.iface)
        self.dlg.show()

        result = self.dlg.exec_()
        if result:
            pass

    def runApplyStyleDialog(self):
        settingsManager = SettingsManager.loadFromProject(QgsProject().instance())

        if settingsManager is None:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Project not initialized. Click on the plug icon first to initialize the project.")
            return
    
        ret = QMessageBox.question(
            None,
            "Apply style confirmation",
            f'Do you really want to apply style to all tagged layers?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if ret == QMessageBox.No:
            return

        project = QgsProject.instance()
        settingsManager = SettingsManager.loadFromProject(project)

        tags = settingsManager.settings.tags

        for k, layer in QgsProject.instance().mapLayers().items():
            for tag in tags:
                currentLayerTag = Utils.getLayerTag(layer, settingsManager.settings)
                if currentLayerTag == tag:
                    value = QgsExpressionContextUtils.projectScope(project).variable(Variable.formatVariableName(tag, '_style'))
                    layer.loadNamedStyle(value)
        
        self.iface.mapCanvas().refreshAllLayers()

    def runApplyStructure(self):
        settingsManager = SettingsManager.loadFromProject(QgsProject().instance())

        if settingsManager is None:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Project not initialized. Click on the plug icon first to initialize the project.")
            return
    
        ret = QMessageBox.question(
            None,
            "Apply confirmation",
            f'The project default layer arrangement will be applied. Some layers will be moved and some groups may be created. Confirm?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if ret == QMessageBox.No:
            return
        
        settingsManager = SettingsManager.loadFromProject(QgsProject.instance())
        LayerTreeOrganizer(self.iface, settingsManager).applyStructure(settingsManager.settings.structure)
        self.iface.mapCanvas().refreshAllLayers()

    def contextMenuAboutToShow(self, menu):
        EventListeners.onContextMenuAboutToShow(self.iface, menu)
        
    def currentLayerChanged(self, layer):
        EventListeners.layerChangedUpdatesQuickInfo(self.iface, layer)

    #TODO move all the methods below to another class

    def updateZoomLevelWidget(self):
        predefinedScales = QgsProject.instance().viewSettings().mapScales()

        if len(predefinedScales) != 0:
            scale = int(math.floor(self.iface.mapCanvas().scale()))
            targetScale = min(predefinedScales, key=lambda x:abs(x-scale))
            zoomLevelComboIndex = predefinedScales.index(targetScale)
            self.zoomLevelComboWidget.setCurrentIndex(zoomLevelComboIndex)

    def updateScale(self, index):
        if index == None or index < 0:
            return
        
        predefinedScales = QgsProject.instance().viewSettings().mapScales()
        
        if (predefinedScales.__len__() == 0):
            return
        
        canvas = self.iface.mapCanvas()
        canvas.zoomScale(predefinedScales[int(index)])

    def initializeZoomLevelWidget(self):
        self.zoomLevelComboWidget.clear()

        predefinedScales = QgsProject.instance().viewSettings().mapScales()

        if (predefinedScales.__len__() == 0):
            return
    
        for z in range(len(predefinedScales)):
            self.zoomLevelComboWidget.addItem(str(z)) 

        self.updateScale(Utils.scaleToZoomLevel(predefinedScales, self.iface.mapCanvas().scale()))
        self.updateZoomLevelWidget()
    
    def addZoomLevelWidget(self):
        if self.zoomLevelComboWidget is not None:
            self.zoomLevelComboWidget.currentIndexChanged.disconnect(self.updateScale)
            self.iface.mapCanvas().scaleChanged.disconnect(self.updateZoomLevelWidget)
            self.initializeZoomLevelWidget()
            self.zoomLevelComboWidget.currentIndexChanged.connect(self.updateScale)
            self.iface.mapCanvas().scaleChanged.connect(self.updateZoomLevelWidget)
            return
    
        parent = self.iface.mainWindow()

        label = QLabel(parent)
        label.setText("Zoom Level:")

        self.zoomLevelComboWidget = QComboBox(parent)

        self.initializeZoomLevelWidget()
        self.zoomLevelComboWidget.currentIndexChanged.connect(self.updateScale)

        self.iface.mapCanvas().scaleChanged.connect(self.updateZoomLevelWidget)
            
        self.addWidgetToCustomToolbar(label)
        self.addWidgetToCustomToolbar(self.zoomLevelComboWidget)
