import os

from qgis.core import QgsMessageLog
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtWidgets import QMessageBox, QLineEdit, QComboBox, QCheckBox, QListWidget, QPushButton, QListWidgetItem, QGroupBox
from ..database.settingsManager import SettingsManager
from ..model.property import Property

FORM_CLASS, _ = uic.loadUiType(os.path.join(
  os.path.dirname(__file__), '../../ui/webmap_add_property.ui'))

class SettingsAddPropertyDialog(QtWidgets.QDialog, FORM_CLASS):
  def __init__(self, settingsManager: SettingsManager, previousProperty: Property, callback, parent=None):
    super(SettingsAddPropertyDialog, self).__init__(parent)
    self.setupUi(self)

    self.settingsManager = settingsManager
    self.previousProperty = previousProperty
    self.callback = callback

    self.nameEditWidget: QLineEdit = self.nameEditWidget
    self.descrEditWidget: QLineEdit = self.descrEditWidget
    self.typeComboWidget: QComboBox = self.typeComboWidget
    self.listCheckWidget: QCheckBox = self.listCheckWidget
    self.validValuesGroup: QGroupBox = self.validValuesGroup
    self.validValuesListWidget: QListWidget = self.validValuesListWidget
    self.validValueEditWidget: QLineEdit = self.validValueEditWidget
    self.addBtnWidget: QPushButton = self.addBtnWidget
    self.delBtnWidget: QPushButton = self.delBtnWidget

    self.typeComboWidget.currentTextChanged.connect(self.onTypeComboWidgetChanged)

    self.addBtnWidget.clicked.connect(self.onAddButtonClicked)
    self.delBtnWidget.clicked.connect(self.onDelButtonClicked)
    self.okButtonWidget.clicked.connect(self.handleOkBtnEvent)
    self.cancelButtonWidget.clicked.connect(self.close)

    self.initialize()

  def initialize(self):
    comboBoxIndex = {
      'number': 0,
      'string': 1,
      'file': 2,
    }

    if self.previousProperty is not None:
      self.nameEditWidget.setText(self.previousProperty.name)
      self.descrEditWidget.setText(self.previousProperty.description)
      self.typeComboWidget.setCurrentIndex(comboBoxIndex[self.previousProperty.type])
      self.listCheckWidget.setChecked(self.previousProperty.isList)

      if self.previousProperty.validValues is not None:
        self.validValuesGroup.setChecked(True)

        for v in self.previousProperty.validValues:
          self.addListItem(v)
      else:
        self.validValuesGroup.setChecked(False)

      self.nameEditWidget.setEnabled(True)
      self.descrEditWidget.setEnabled(True)
      self.typeComboWidget.setEnabled(False)
      self.listCheckWidget.setEnabled(False)

  def addListItem(self, value):
    item = QListWidgetItem(self.validValuesListWidget)
    item.setText(value)
    self.validValuesListWidget.addItem(item)
    self.validValueEditWidget.setText('')

  def onTypeComboWidgetChanged(self, currentType):
    if currentType == 'number':
      self.validValueEditWidget.setValidator(QDoubleValidator(self.validValueEditWidget))
    else:
      self.validValueEditWidget.setValidator(None)

  def onAddButtonClicked(self):
    value = self.validValueEditWidget.text()

    if value is not None:
      self.addListItem(value)

  def onDelButtonClicked(self):
    for index in self.validValuesListWidget.selectedIndexes():
        self.validValuesListWidget.takeItem(index.row())

  def handleOkBtnEvent(self):
    name = self.nameEditWidget.text().strip()
    descr = self.descrEditWidget.text()
    type = self.typeComboWidget.currentText()
    isList = self.listCheckWidget.isChecked()
    validValues = None

    if self.validValuesGroup.isChecked():
      validValues = [str(self.validValuesListWidget.item(i).text()) for i in range(self.validValuesListWidget.count())]

    if name == '':
      QMessageBox.critical(self, "Error", "Name field is required.")
      return
    
    if name in self.settingsManager.settings.properties:
      if self.previousProperty is None or name != self.previousProperty.name:
        QMessageBox.critical(self, "Error", "Name already exists.")
        return

    if self.previousProperty is not None and name != self.previousProperty.name:
      self.settingsManager.renameProperty(self.previousProperty.name, name)

    property = Property(name, descr, type, isList, validValues)

    self.settingsManager.settings.addOrUpdateProperty(property)
    self.callback(property)
    self.close()
