import os

from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QInputDialog, QHeaderView, QMessageBox, QAction
from ..model.settings import TAG_IDENTIFY_MODE
from ..model.variable import Variable
from .settingsAddPropertyToTag import SettingAddPropertyToTag
from ..database.settingsManager import SettingsManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_tags_settings_page_widget.ui'))

class SettingsTagsPageWidget(QtWidgets.QWidget, FORM_CLASS):
    def __init__(self, iface, settingsManager: SettingsManager, parent=None):
        super(SettingsTagsPageWidget, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.settingsManager = settingsManager

        self.tagTreeWidget: QTreeWidget = self.tagTreeWidget
        self.filterEditWidget: QLineEdit = self.filterEditWidget
        self.identifyStrategyComboWidget: QComboBox = self.identifyStrategyComboWidget

        self.tagTreeWidget.itemDoubleClicked.connect(self.onDoubleClick)
        self.tagTreeWidget.customContextMenuRequested.connect(self.onContextMenuRequested)

        self.addTagBtnWidget.clicked.connect(self.onAddTagBtnClicked)
        self.delTagBtnWidget.clicked.connect(self.onDelTagBtnClicked)
        self.cloneTagBtnWidget.clicked.connect(self.onCloneTagBtnClicked)
        self.filterEditWidget.textChanged.connect(self.onFilterTextChanged)
        self.identifyStrategyComboWidget.currentIndexChanged.connect(self.onIdentifyStrategyComboChanged)

        self.initialize()

    def initialize(self):
        self.tagTreeWidget.clear()

        groupedVariables = self.settingsManager.variablesManager.groupByTag()

        for tag in self.settingsManager.settings.tags:
            tagItem = self.addTagTreeItem(tag)

            #A tag may be registered without properties.
            if tag in groupedVariables:
                for variable in groupedVariables[tag]:
                    self.addPropertyTreeItem(tagItem, variable.prop, variable.value)

        self.tagTreeWidget.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tagTreeWidget.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        if self.settingsManager.settings.tagIdentifyMode == TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH:
            self.identifyStrategyComboWidget.setCurrentIndex(0)
        else:
            self.identifyStrategyComboWidget.setCurrentIndex(1)

    def addTagTreeItem(self, tag: str):
        item = QTreeWidgetItem(self.tagTreeWidget)
        item.setText(0, tag)
        item.setExpanded(True)
        item.setSelected(True)
        self.tagTreeWidget.setCurrentItem(item)
        self.tagTreeWidget.scrollTo(self.tagTreeWidget.indexFromItem(item))
        self.tagTreeWidget.addTopLevelItem(item)

        return item
    
    def addPropertyTreeItem(self, parent: QTreeWidgetItem, propertyName: str, propertyValue: str):
        self.tagTreeWidget.clearSelection()

        item = QTreeWidgetItem(parent)
        item.setText(0, propertyName)
        item.setText(1, propertyValue)
        item.setIcon(2, QIcon(':/icons/symbologyRemove.png'))
        item.setSelected(True)
        self.tagTreeWidget.addTopLevelItem(item)

    def filterTreeItems(self, filters: list[str]):
        showAll = True if filters is None or filters.__len__() == 0 else False

        for index in range(self.tagTreeWidget.topLevelItemCount()):
            item = self.tagTreeWidget.topLevelItem(index)

            if showAll:
                item.setHidden(False)
            else:
                matched = [f for f in filters if item.text(0).startswith(f.strip())].__len__() > 0
                item.setHidden(not matched)

    def isTagTreeItem(self, item: QTreeWidgetItem):
        return item.parent() is None
    
    def isPropertyTreeItem(self, item: QTreeWidgetItem):
        #Property item always have a parent
        return not self.isTagTreeItem(item)

    def callAddOrUpdateTagDialog(self, previousItem: QTreeWidgetItem = None):
        if previousItem is None:
            response = QInputDialog().getText(self, 'New tag', 'Tag name:', QLineEdit.Normal)
        else:
            response = QInputDialog().getText(self, 'Rename tag', 'Rename to:', QLineEdit.Normal, previousItem.text(0))

        if response[1]:
            tag = response[0]

            if tag.strip() == '':
                QMessageBox.critical(self,"Error","Tag name cannot be empty.")
            elif tag.__contains__('[') or tag.__contains__(']'):
                QMessageBox.critical(self,"Error","Invalid tag name. Do not use brackets.")
            elif self.settingsManager.tagExists(tag):
                QMessageBox.critical(self,"Error","Tag already exists.")
            else:
                self.filterEditWidget.setText('')

                if previousItem:
                    self.settingsManager.renameTag(previousItem.text(0), tag)
                    previousItem.setText(0, tag)
                    return previousItem
                else:
                    self.settingsManager.settings.addOrUpdateTag(tag)
                    return self.addTagTreeItem(tag)

    def callDeleteTagDialog(self, items: list[QTreeWidgetItem]):
        ret = QMessageBox.question(
            self,
            "Delete confirmation",
            f'Do you really want to delete all the selected tags?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if ret == QMessageBox.No:
            return
        
        topLevelItems = list(filter(lambda x: self.isTagTreeItem(x), items))
        listOfTagName = list(map(lambda x: x.text(0), topLevelItems))
        self.settingsManager.deleteTags(listOfTagName)

        root = self.tagTreeWidget.invisibleRootItem()
        for item in self.tagTreeWidget.selectedItems():
            root.removeChild(item)

    def callAddPropertyDialog(self, item: QTreeWidgetItem):
        tag = item.text(0)
        callback = lambda property, value: self.addPropertyTreeItem(item, property, value)
        title = f'Add new property value to [{tag}] tag'
        previousVariable = None

        dlg = SettingAddPropertyToTag(tag, self.settingsManager, previousVariable, callback)
        dlg.setWindowTitle(title)
        dlg.exec_()

    def callUpdatePropertyDialog(self, item: QTreeWidgetItem):
        tag = item.parent().text(0)
        propertyName = item.text(0)
        value = item.text(1)
        callback = lambda _, value: item.setText(1, value)
        title = f'Update value of [{propertyName}] property'
        previousVariable = Variable(tag, propertyName, value)
    
        dlg = SettingAddPropertyToTag(tag, self.settingsManager, previousVariable, callback)
        dlg.setWindowTitle(title)
        dlg.exec_()

    def cloneTag(self, item: QTreeWidgetItem):
        newTagItem = self.callAddOrUpdateTagDialog()

        if newTagItem is not None:
            self.settingsManager.cloneTagProperties(item.text(0), newTagItem.text(0))

            for childIndex in range(item.childCount()):
                childItem = item.child(childIndex)
                newTagItem.addChild(childItem.clone())

    def deleteProperty(self, item: QTreeWidgetItem):
        propertyName = item.text(0)
        tag = item.parent().text(0)
        var = Variable.formatVariableName(tag, propertyName)
        self.settingsManager.variablesManager.removeByVariables([var])
        item.parent().removeChild(item)

    def onDoubleClick(self, item: QTreeWidgetItem, column):
        if self.isPropertyTreeItem(item) and column == 0:
            self.callUpdatePropertyDialog(item)

    def onAddTagBtnClicked(self):
        self.callAddOrUpdateTagDialog(None)

    def onContextMenuRequested(self, pos: QPoint):
        item = self.tagTreeWidget.itemAt(pos)

        if item is None:
            return

        for selItem in self.tagTreeWidget.selectedItems():
            selItem.setSelected(True if selItem == item else False)

        itemName = item.text(0)
        menu = QMenu(self.tagTreeWidget)

        if self.isTagTreeItem(item):
            addPropertyAction = QAction(f'Add property...', self.tagTreeWidget)
            addPropertyAction.triggered.connect(lambda: self.callAddPropertyDialog(item))

            editTagAction = QAction(f'Rename...', self.tagTreeWidget)
            editTagAction.triggered.connect(lambda: self.callAddOrUpdateTagDialog(item))

            cloneTagAction = QAction(f'Clone...', self.tagTreeWidget)
            cloneTagAction.triggered.connect(lambda: self.cloneTag(item))

            deleteTagAction = QAction(f'Delete', self.tagTreeWidget)
            deleteTagAction.triggered.connect(lambda: self.callDeleteTagDialog([item]))

            menu.setTitle(itemName)
            menu.addAction(addPropertyAction)
            menu.addAction(editTagAction)
            menu.addAction(cloneTagAction)
            menu.addAction(deleteTagAction)
        elif self.isPropertyTreeItem(item):
            editAction = QAction(f'Edit...', self.tagTreeWidget)
            editAction.triggered.connect(lambda: self.callUpdatePropertyDialog(item))
            deleteAction = QAction(f'Delete', self.tagTreeWidget)
            deleteAction.setObjectName('deleteAction')
            deleteAction.triggered.connect(lambda: self.deleteProperty(item))

            menu.setTitle(itemName)
            menu.addAction(editAction)
            menu.addAction(deleteAction)

        menu.exec(self.tagTreeWidget.mapToGlobal(pos))

    def onDelTagBtnClicked(self):
        selectedItems = self.tagTreeWidget.selectedItems()

        if selectedItems.__len__() > 0:
            self.callDeleteTagDialog(selectedItems)

    def onCloneTagBtnClicked(self):
        selectedItems = self.tagTreeWidget.selectedItems()

        if selectedItems.__len__() > 0 and self.isTagTreeItem(selectedItems[0]):
            selectedTagItem = selectedItems[0]
            selectedTagItem.setSelected(True)
            self.cloneTag(selectedTagItem)

    def onFilterTextChanged(self):
        input = self.filterEditWidget.text()

        if input.strip() != '':
            filters = list(filter(lambda x: x.strip() != '', input.split(',')))
            self.filterTreeItems(filters)
        else:
            self.filterTreeItems(None)
    
    def onIdentifyStrategyComboChanged(self, index):
        if index == 0:
            self.settingsManager.settings.tagIdentifyMode = TAG_IDENTIFY_MODE.LAYER_NAME_STARTS_WITH
        else:
            self.settingsManager.settings.tagIdentifyMode = TAG_IDENTIFY_MODE.CATEGORY_METADATA_CONTAINS