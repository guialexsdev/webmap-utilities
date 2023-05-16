import os

from qgis.core import QgsMessageLog
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem, QAction, QInputDialog, QLineEdit
from ..utils.layerTreeOrganizer import LayerTreeOrganizer
from ..model.variable import Variable
from ..database.settingsManager import SettingsManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_structure_settings_page_widget.ui'))

class SettingsStructurePageWidget(QtWidgets.QWidget, FORM_CLASS):
    def __init__(self, iface, settingsManager: SettingsManager, parent=None):
        super(SettingsStructurePageWidget, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settingsManager = settingsManager
        self.organizer = LayerTreeOrganizer(iface, self.settingsManager)
        self.treeWidget: QTreeWidget = self.treeWidget

        #self.treeWidget.customContextMenuRequested.connect(self.onContextMenuRequested)
        self.updateBtnWidget.clicked.connect(self.onUpdateBtnClicked)

        self.initialize()

    def initialize(self):
        self.treeWidget.clear()
        structure = self.settingsManager.settings.structure

        for path in structure:
            item = None

            if path == 'root':
                for tag in structure[path]:
                    item = self.addTopLevelItem(f"Layers with '{tag}' tag", 'layer')

                continue
            
            groups = path.split('.')

            if groups[0] == 'root':
                groups.pop(0) #remove 'root'

            for index in range(groups.__len__()):
                if index == 0:
                    item = self.getTopLevelItem(groups[index])
                    if item is None:
                        item = self.addTopLevelItem(groups[index], 'folder')
                else:
                    previousItem = self.getChildItem(item, groups[index])
                    item = self.addSubItem(item, groups[index], 'folder') if previousItem is None else previousItem

            for tag in structure[path]:
                self.addSubItem(item, f"Layers with '{tag}' tag", 'layer')

    def getTopLevelItem(self, name):
        for index in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(index)
            if item.text(0) == name:
                return item

    def getChildItem(self, parent: QTreeWidgetItem, name):
        for index in range(parent.childCount()):
            item = parent.child(index)
            if item.text(0) == name:
                return item

    def addTopLevelItem(self, name: str, type: str):
        item = QTreeWidgetItem(self.treeWidget)
        item.setText(0, name)
        item.setData(0, Qt.ItemDataRole.UserRole, type)
        item.setExpanded(True)

        self.treeWidget.addTopLevelItem(item)
        return item

    def addSubItem(self, parent: QTreeWidgetItem, name: str, type: str):
        item = QTreeWidgetItem(parent)
        item.setText(0, name)
        item.setData(0, Qt.ItemDataRole.UserRole, type)
        item.setExpanded(True)
        return item

    def callAddTagLayerDialog(self, item):
        response = QInputDialog().getText(self, 'Add tag layer', 'Tag name:', QLineEdit.Normal)

        if response[1]:
            name = response[0]
            self.addSubItem(item, name, 'layer')

    def onContextMenuRequested(self, pos: QPoint):
        item = self.treeWidget.itemAt(pos)

        if item is None or item.data(0, Qt.ItemDataRole.UserRole) != 'folder':
            return

        for selItem in self.treeWidget.selectedItems():
            selItem.setSelected(True if selItem == item else False)

        itemName = item.text(0)
        menu = QMenu(self.treeWidget)

        addTagLayerAction = QAction(f'Add tag layer...', self.treeWidget)
        addTagLayerAction.triggered.connect(lambda: self.callAddTagLayerDialog(item))
        
        menu.setTitle(itemName)
        menu.addAction(addTagLayerAction)
        menu.exec(self.treeWidget.mapToGlobal(pos))

    def onUpdateBtnClicked(self):
        self.settingsManager.settings.structure = self.organizer.getStructure()
        self.initialize()
