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
import sys

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
from .src.gui.layerVisibilityDialog import LayerVisibilityDialog
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

        self.zoomLevelComboWidget = None

    def createToolbar(self, name):
        if self.toolbar is None:
            self.toolbar: QToolBar = self.iface.addToolBar(name)
            self.toolbar.setObjectName("WebmapToolbar")

    def addButtonToCustomToolbar(self, text, iconPath, callback):
        icon = QIcon(iconPath)
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
        self.actions.append(action)

    def addWidgetToCustomToolbar(self, widget):
        self.actions.append(self.toolbar.addWidget(widget))

    def addAction(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

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

        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.addButtonToCustomToolbar(
            'Settings',
            ':/icons/settings.png',
            self.runSettingsDialog
        )

        self.addButtonToCustomToolbar(
            'Apply Style',
            ':/icons/apply_style.png',
            self.runApplyStyleDialog
        )

        self.addButtonToCustomToolbar(
            'Apply Structure',
            ':/icons/apply_structure.png',
            self.runApplyStructure
        )
        
        self.addButtonToCustomToolbar(
            'OSM Downloader',
            ':/icons/osm.png',
            self.runOSMDownloader
        )

        self.addButtonToCustomToolbar(
            'Shaded Relief Creator',
            ':/icons/relief_creator.png',
            self.runShadedReliefCreator
        )

        
        QgsMessageLog.logMessage("SUBSCRIBING mapScalesChanged","debugao")
        QgsProject().instance().viewSettings().mapScalesChanged.connect(self.addOrUpdateZoomLevelWidget)
        self.iface.layerTreeView().contextMenuAboutToShow.connect(self.contextMenuAboutToShow)
        self.iface.currentLayerChanged.connect(self.currentLayerChanged)

    def unload(self):
        self.iface.layerTreeView().contextMenuAboutToShow.disconnect(self.contextMenuAboutToShow)
        self.iface.currentLayerChanged.disconnect(self.currentLayerChanged)

        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removeToolBarIcon(action)

    def runOSMDownloader(self):
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

    def runLayerVisibilityDialog(self):
        self.dlg = LayerVisibilityDialog(self.iface)
        self.dlg.show()

        result = self.dlg.exec_()
        if result:
            pass

    def runApplyStyleDialog(self):
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

    def runApplyStructure(self):
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

    def contextMenuAboutToShow(self, menu):
        EventListeners.onContextMenuAboutToShow(self.iface, menu)
        
    def currentLayerChanged(self, layer):
        EventListeners.layerChangedUpdatesQuickInfo(self.iface, layer)

    def updateZoomLevelWidget(self):
        predefinedScales = QgsProject.instance().viewSettings().mapScales()

        if len(predefinedScales) != 0:
            scale = int(math.floor(self.iface.mapCanvas().scale()))
            targetScale = min(predefinedScales, key=lambda x:abs(x-scale))
            zoomLevelComboIndex = predefinedScales.index(targetScale)
            self.zoomLevelComboWidget.setCurrentIndex(zoomLevelComboIndex)

    def updateScale(self, index):
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
        self.updateZoomLevelWidget()
        
    def addOrUpdateZoomLevelWidget(self):
        if self.zoomLevelComboWidget is not None:
           QgsMessageLog.logMessage("self.zoomLevelComboWidget IS NOT None","debugao")
           self.initializeZoomLevelWidget()
           return
    
        QgsMessageLog.logMessage("self.zoomLevelComboWidget IS None","debugao")
        parent = self.iface.mainWindow()
        label = QLabel(parent)
        self.zoomLevelComboWidget = QComboBox(parent)

        label.setText("Zoom Level:")
        self.initializeZoomLevelWidget()

        def afterProjectLoaded():
            self.initializeZoomLevelWidget()
            self.iface.projectRead.disconnect(afterProjectLoaded)
            self.iface.mapCanvas().scaleChanged.connect(self.updateZoomLevelWidget)
            self.zoomLevelComboWidget.currentTextChanged.connect(self.updateScale)

        if QgsProject.instance().fileName().strip() == '':
            self.iface.projectRead.connect(afterProjectLoaded)
        else:
            self.initializeZoomLevelWidget()
            self.iface.mapCanvas().scaleChanged.connect(self.updateZoomLevelWidget)
            self.zoomLevelComboWidget.currentTextChanged.connect(self.updateScale)
            
        self.addWidgetToCustomToolbar(label)
        self.addWidgetToCustomToolbar(self.zoomLevelComboWidget)
