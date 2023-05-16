import os

from qgis.core import QgsProject, QgsMessageLog
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtGui import QFont, QIcon
from qgis.PyQt.QtWidgets import QMenu, QTableWidget, QTableWidgetItem, QTextBrowser, QInputDialog, QHeaderView, QMessageBox, QAction, QAbstractItemView
from .settingsAddPropertyDialog import SettingsAddPropertyDialog
from ..model.property import Property
from ..model.variable import Variable
from .settingsAddPropertyToTag import SettingAddPropertyToTag
from ..database.settingsManager import SettingsManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_properties_settings_page_widget2.ui'))

class SettingsPropertiesPageWidget(QtWidgets.QWidget, FORM_CLASS):
    def __init__(self, settingsManager: SettingsManager, changesCallback, parent=None):
        super(SettingsPropertiesPageWidget, self).__init__(parent)
        self.setupUi(self)

        self.changesCallback = changesCallback
        self.settingsManager = settingsManager

        self.propertiesTableWidget: QTableWidget = self.propertiesTableWidget
        self.helpBrowser: QTextBrowser = self.helpBrowser

        self.propertiesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.propertiesTableWidget.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.propertiesTableWidget.itemDoubleClicked.connect(self.onDoubleClick)
        self.propertiesTableWidget.customContextMenuRequested.connect(self.onContextMenuRequested)

        self.addPropertyBtnWidget.clicked.connect(self.onAddBtnClicked)
        self.delPropertyBtnWidget.clicked.connect(self.onDelBtnClicked)

        self.initialize()

    def initialize(self):
        self.propertiesTableWidget.clear()
        self.propertiesTableWidget.clearContents()            
        self.propertiesTableWidget.clearSelection()
        self.helpBrowser.clear()

        row = self.propertiesTableWidget.rowCount()

        for propertyName in self.settingsManager.settings.properties:
            property = self.settingsManager.settings.properties[propertyName]
            self.addPropertyTableItem(property, row)
            row = row + 1

        self.propertiesTableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.propertiesTableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.propertiesTableWidget.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)

        if row > 0:
            self.propertiesTableWidget.clearSelection()
            self.helpBrowser.clear()

    def addPropertyTableItem(self, property: Property, row = None):
        self.propertiesTableWidget.setSortingEnabled(False)
        currentRow = row if row is not None else self.propertiesTableWidget.rowCount()
        self.propertiesTableWidget.insertRow(currentRow)

        itemName = QTableWidgetItem()
        itemName.setFlags(itemName.flags() ^ QtCore.Qt.ItemIsEditable)
        itemName.setData(QtCore.Qt.DisplayRole, property.name)

        itemType = QTableWidgetItem()
        itemType.setFlags(itemType.flags() ^ QtCore.Qt.ItemIsEditable)
        itemType.setData(QtCore.Qt.DisplayRole, property.type)

        itemIsList = QTableWidgetItem()
        itemIsList.setFlags(itemIsList.flags() ^ QtCore.Qt.ItemIsEditable)
        itemIsList.setData(QtCore.Qt.DisplayRole, property.isList)

        self.propertiesTableWidget.setItem(currentRow, 0, itemName)
        self.propertiesTableWidget.setItem(currentRow, 1, itemType)
        self.propertiesTableWidget.setItem(currentRow, 2, itemIsList)
        self.propertiesTableWidget.selectRow(currentRow)

        self.helpBrowser.setText(property.description)
        self.propertiesTableWidget.setSortingEnabled(True)
        self.propertiesTableWidget.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def editPropertyTableItem(self, property: Property, row):
        itemName = self.propertiesTableWidget.item(row, 0)
        itemName.setData(QtCore.Qt.DisplayRole, property.name)

        itemType = self.propertiesTableWidget.item(row, 1)
        itemType.setData(QtCore.Qt.DisplayRole, property.type)

        itemIsList = self.propertiesTableWidget.item(row, 2)
        itemIsList.setData(QtCore.Qt.DisplayRole, property.isList)

        self.helpBrowser.setText(property.description)

    def rowToProperty(self, row: int):
        name = self.propertiesTableWidget.item(row, 0).text()
        return self.settingsManager.settings.properties[name]

    def callAddDialog(self):
        def callback(property: Property):
            self.addPropertyTableItem(property)

        dlg = SettingsAddPropertyDialog(self.settingsManager, None, callback)
        dlg.setWindowTitle(f'Add property')
        dlg.exec_()

    def callUpdateDialog(self, row: int):
        oldProperty: Property = self.rowToProperty(row)

        def callback(property: Property):
            if property.description != oldProperty.description:
                self.helpBrowser.setText(property.description)

            if property.name != oldProperty.name:
                self.editPropertyTableItem(property, row)

        dlg = SettingsAddPropertyDialog(self.settingsManager, oldProperty, callback)
        dlg.setWindowTitle(f'Update {oldProperty.name}')
        dlg.exec_()

        self.changesCallback()

    def callDeleteDialog(self, rows: list[int]):
        self.propertiesTableWidget.itemSelectionChanged.disconnect(self.itemSelectionChanged)

        ret = QMessageBox.question(
            self,
            "Delete confirmation",
            f'Do you really want to delete all the selected properties?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if ret == QMessageBox.No:
            return

        listOfPropertyNames = list(map(lambda row: self.propertiesTableWidget.item(row, 0).text(), rows))
        self.settingsManager.removeProperties(listOfPropertyNames)

        for row in rows:
           self.propertiesTableWidget.removeRow(row)

        self.propertiesTableWidget.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.helpBrowser.clear()
        self.changesCallback()

    def itemSelectionChanged(self):
        selectedItems = self.propertiesTableWidget.selectedItems()

        if selectedItems.__len__() > 0:
            selectedItem = selectedItems[0]
            row = selectedItem.row()
            nameItem = self.propertiesTableWidget.item(row,0)
            property = self.settingsManager.settings.properties[nameItem.text()]
            self.helpBrowser.setText(property.description)

    def onDoubleClick(self, item: QTableWidgetItem):
        self.callUpdateDialog(item.row())

    def onAddBtnClicked(self):
        self.callAddDialog()

    def onDelBtnClicked(self):
        selectedItems = self.propertiesTableWidget.selectedItems()
        rows = set(map(lambda x: x.row(), selectedItems))
        self.callDeleteDialog(rows)

    def onContextMenuRequested(self, pos: QPoint):
        pass
