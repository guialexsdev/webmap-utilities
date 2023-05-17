from qgis.core import QgsProject, QgsMapLayer
from qgis.PyQt.QtWidgets import QMenu
from ..utils.webmapCommons import Utils
from .settingsAddPropertyToTag import SettingAddPropertyToTag
from ..database.settingsManager import SettingsManager

class SetPropertyContextMenuHandler:
    def __init__(self, iface, settingsManager: SettingsManager, parent=None):
        self.iface = iface
        self.parent = parent
        self.settingsManager = settingsManager

    def callUpdatePropertyDialog(self, var):
        project = QgsProject.instance()
        title = f'Update value of {var.tag}[{var.prop}] property'
        callback = lambda prop,value: self.settingsManager.persistToProject(project)

        dlg = SettingAddPropertyToTag(var.tag, self.settingsManager, var, callback)
        dlg.setWindowTitle(title)
        dlg.exec_()
        self.iface.mapCanvas().refreshAllLayers()

    def callAddPropertyDialog(self, tag):
        project = QgsProject.instance()
        title = f'Add property to {tag} tag'
        callback = lambda prop,value: self.settingsManager.persistToProject(project)

        dlg = SettingAddPropertyToTag(tag, self.settingsManager, None, callback)
        dlg.setWindowTitle(title)
        dlg.exec_()
        self.iface.mapCanvas().refreshAllLayers()

    def handle(self, menu: QMenu, selectedLayers: list[QgsMapLayer]):
        if selectedLayers.__len__() != 1:
            return

        selectedLayer = selectedLayers[0]
   
        subMenu = None
        selectedTag = None
        propertyWasFound = False

        tag = Utils.getLayerTag(selectedLayer, self.settingsManager.settings)

        if tag is not None:
            subMenu = menu.addMenu('Set tag property...')
            vars = self.settingsManager.variablesManager.getByTag(tag)
            vars.sort(key=lambda x: x.prop)

            for var in vars:
                def addAction(var):
                    action = subMenu.addAction(var.prop)
                    action.triggered.connect(lambda: self.callUpdatePropertyDialog(var))
                addAction(var)
                propertyWasFound = True

            selectedTag = tag    

        if not propertyWasFound and selectedTag:
            action = subMenu.addAction('No property set')
            action.setEnabled(False)

        if selectedTag is not None:
            subMenu.addSeparator()
            action = subMenu.addAction('Add property...')
            action.triggered.connect(lambda: self.callAddPropertyDialog(selectedTag))
