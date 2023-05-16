import os

from qgis.core import QgsProject, QgsMessageLog
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtWidgets import QStackedWidget, QMessageBox, QComboBox, QLineEdit, QTextBrowser, QPushButton, QListWidget, QListWidgetItem, QFileDialog
from ..model.variable import Variable
from ..model.property import Property
from ..database.settingsManager import SettingsManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_tags_settings_set_property_dialog.ui'))

class SettingAddPropertyToTag(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, tag: str, settingsManager: SettingsManager, selectedVariable: Variable, callback=None, parent=None):
        super(SettingAddPropertyToTag, self).__init__(parent)
        self.setupUi(self)
        
        self.tag = tag
        self.selectedProperty = None
        self.callback = callback
        self.settingsManager = settingsManager

        self.propertyComboWidget: QComboBox = self.propertyComboWidget
        self.helpTextBrowser: QTextBrowser = self.helpTextBrowser
 
        self.valueEditWidget: QLineEdit = self.valueEditWidget
        self.valueComboBoxWidget: QComboBox = self.valueComboBoxWidget
        self.openFileBtnWidget: QPushButton = self.openFileBtnWidget
        self.listWidget: QListWidget = self.listWidget
        self.addToListBtnWidget: QPushButton = self.addToListBtnWidget
        self.delFromListBtnWidget: QPushButton = self.delFromListBtnWidget

        self.okButtonWidget: QPushButton = self.okButtonWidget
        self.cancelButtonWidget: QPushButton = self.cancelButtonWidget
        self.okButtonWidget.setDefault(True)

        self.propertyComboWidget.currentTextChanged.connect(self.onCurrentPropertyChanged)
        self.openFileBtnWidget.clicked.connect(self.onOpenFileClicked)
        self.addToListBtnWidget.clicked.connect(self.onAddButtonClicked)
        self.delFromListBtnWidget.clicked.connect(self.onDeleteButtonClicked)

        self.okButtonWidget.clicked.connect(self.handleOkBtnEvent)
        self.cancelButtonWidget.clicked.connect(self.handleCancelBtnEvent)

        self.initialize(selectedVariable)

    def initialize(self, selectedVariable: Variable):
        if selectedVariable is None:
            for property in self.settingsManager.settings.properties:
                self.propertyComboWidget.addItem(property)
                
            self.selectedProperty = self.settingsManager.settings.properties[self.propertyComboWidget.currentText()]
        else:
            self.propertyComboWidget.addItem(selectedVariable.prop)
            self.propertyComboWidget.setDisabled(True)
            self.selectedProperty = self.settingsManager.settings.properties[self.propertyComboWidget.currentText()]

            if self.selectedProperty.isList:
                for value in selectedVariable.value.split(';'):
                    self.addListItem(value)
            else:
                self.valueEditWidget.setText(selectedVariable.value) 

        if self.selectedProperty.type == 'number':
            self.valueEditWidget.setValidator(QDoubleValidator(self.valueEditWidget))

        self.setListWidgetsVisible(self.selectedProperty.isList)
        self.decideTypeOfValueWidget()
        self.decideIfShowFileButton()

    def setListWidgetsVisible(self, visible: bool):
        self.listWidget.setVisible(visible)
        self.addToListBtnWidget.setVisible(visible)
        self.delFromListBtnWidget.setVisible(visible)
        self.addToListBtnWidget.setDefault(visible)
        self.okButtonWidget.setDefault(not visible)

    def decideTypeOfValueWidget(self):
        if self.selectedProperty.validValues is not None:
            self.valueEditWidget.setHidden(True)
            self.valueComboBoxWidget.setHidden(False)
        else:
            self.valueEditWidget.setHidden(False)
            self.valueComboBoxWidget.setHidden(True)

    def decideIfShowFileButton(self):
        if self.selectedProperty.type == 'file' is not None:
            self.openFileBtnWidget.setHidden(False)
        else:
            self.openFileBtnWidget.setHidden(True)

    def getAndValidateValue(self):
        if self.valueEditWidget.isHidden():
            value = self.valueComboBoxWidget.currentText()
        else:
            value = self.valueEditWidget.text()

        if value.strip() == '':
            QMessageBox.critical(self, "Error", "Value cannot be empty.")
            return None
        elif value.__contains__(';'):
            QMessageBox.critical(self, "Error", "Don't use ;. It's a reserved character.")
            return None

        return value

    def addListItem(self, value):
        item = QListWidgetItem(self.listWidget)
        item.setText(value)
        self.listWidget.addItem(item)
        self.valueEditWidget.setText('')

    def onOpenFileClicked(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', QgsProject.instance().homePath())

        if file:
            self.valueEditWidget.setText(file)

    def onAddButtonClicked(self):
        value = self.getAndValidateValue()

        if value is not None:
            self.addListItem(value)

    def onDeleteButtonClicked(self):
        for index in self.listWidget.selectedIndexes():
            self.listWidget.takeItem(index.row())

    def onCurrentPropertyChanged(self, currentProperty):
        self.selectedProperty = self.settingsManager.settings.properties[currentProperty]

        type = f'List of {self.selectedProperty.type}s' if self.selectedProperty.isList else self.selectedProperty.type
        description = f"""
        <div><b>Description</b>: {self.selectedProperty.description}</div>
        <div><b>Type</b>: {type}</div>
        """

        self.valueEditWidget.setText('')

        if self.selectedProperty.type == 'number':
            self.valueEditWidget.setValidator(QDoubleValidator(self.valueEditWidget))
        else:            
            self.valueEditWidget.setValidator(None)

        self.valueComboBoxWidget.clear()

        if self.selectedProperty.validValues is not None:
            self.valueComboBoxWidget.addItems(self.selectedProperty.validValues)

        self.decideTypeOfValueWidget()
        self.decideIfShowFileButton()
        self.setListWidgetsVisible(self.selectedProperty.isList)
        self.helpTextBrowser.setHtml(description)

    def handleOkBtnEvent(self):
        tag = self.tag
        property = self.propertyComboWidget.currentText()

        if self.selectedProperty.isList:
            value = ';'.join([str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())])
        else:
            value = self.getAndValidateValue()

            if value is None:
                return

        self.settingsManager.variablesManager.addVariable(Variable(tag, property, value))

        if self.callback is not None:
            self.callback(property, value)

        self.close()

    def handleCancelBtnEvent(self):
        self.close()
        pass
