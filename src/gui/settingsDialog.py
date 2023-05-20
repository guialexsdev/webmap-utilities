import os
import tempfile
import traceback

from qgis.core import QgsProject, QgsMessageLog
from qgis.core import Qgis
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtWidgets import QStackedWidget, QDialogButtonBox, QListWidget, QPushButton, QFileDialog, QMessageBox
from ..gui.settingsStructurePageWidget import SettingsStructurePageWidget
from ..database.settingsManager import SettingsManager
from .settingsTagsPageWidget import SettingsTagsPageWidget
from .settingsPropertiesPageWidget import SettingsPropertiesPageWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_settings_dialog.ui'))

class SettingsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.project = QgsProject.instance()
        self.settingsManager = SettingsManager.loadFromProject(QgsProject.instance())

        if self.settingsManager is None:
            self.settingsManager = SettingsManager()
            QgsMessageLog.logMessage('No previous settings found. Using default settings.', 'Webmap Plugin')

        self.mainMenuListWidget: QListWidget = self.mainMenuListWidget
        self.stackedWidget: QStackedWidget = self.stackedWidget
        self.importBtnWidget: QPushButton = self.importBtnWidget
        self.exportBtnWidget: QPushButton = self.exportBtnWidget
        self.buttonBox: QDialogButtonBox = self.buttonBox
        
        self.tagsPage = SettingsTagsPageWidget(iface, self.settingsManager)
        self.propertiesPage = SettingsPropertiesPageWidget(self.settingsManager, self.onPropertiesSettingsChanged)
        self.structurePage = SettingsStructurePageWidget(iface, self.settingsManager)

        self.stackedWidget.insertWidget(0, self.tagsPage) #TODO insert tags page
        self.stackedWidget.insertWidget(1, self.propertiesPage) #TODO insert properties page
        self.stackedWidget.insertWidget(2, self.structurePage) #TODO insert structure page

        self.mainMenuListWidget.item(0).setSelected(True)
        
        self.importBtnWidget.clicked.connect(self.onImportButtonClicked)
        self.exportBtnWidget.clicked.connect(self.onExportButtonClicked)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.handleApplyBtnEvent)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.handleOkBtnEvent)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.handleCancelBtnEvent)

    def onPropertiesSettingsChanged(self):
        self.tagsPage.initialize()

    def onImportButtonClicked(self):
        homePath = self.project.homePath()
        filepath, _ = QFileDialog.getOpenFileName(self, 'Import configuration file', homePath, '*.wpc')

        if filepath:
            ret = QMessageBox.question(
                self,
                "Import confirmation",
                f'All tags, properties and layers arrangement structure will be replaced. Confirm?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if ret == QMessageBox.No:
                return

            def onStylePropertyFound():
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Question)
                msgBox.setWindowTitle('Import confirmation')
                msgBox.setText('The import file contains style properties. You can choose a folder to store the style files or use a temporary one. How to proceed?')
                msgBox.addButton(QPushButton('Choose folder...'), QMessageBox.ButtonRole.YesRole)
                msgBox.addButton(QPushButton('Use a temporary folder'), QMessageBox.ButtonRole.YesRole)
                ret = msgBox.exec_()

                if ret == 0:
                    choosenFolder = QFileDialog.getExistingDirectory(self, 'Folder to save styles', homePath)
                    if choosenFolder is not None:
                        return choosenFolder

                return tempfile.TemporaryDirectory().name

            try:
                self.settingsManager.importFromFile(filepath, onStylePropertyFound)
                self.tagsPage.initialize()
                self.propertiesPage.initialize()
                self.structurePage.initialize()
            except Exception as e:
                QgsMessageLog.logMessage(str(traceback.format_exc()), 'Webmap Utilities Plugin', Qgis.MessageLevel.Critical)
                QMessageBox.critical(self, "Error", "Import failed. File content seems invalid.")

    def onExportButtonClicked(self):
        homePath = self.project.homePath()
        filepath, _ = QFileDialog.getSaveFileName(self, 'Export configuration file...', homePath, '*.wpc')

        if filepath:
            self.settingsManager.exportToFile(filepath)
            QMessageBox.information(self, "Save", "Configuration file successfully exported.")

    def handleApplyBtnEvent(self):
        self.settingsManager.persistToProject(self.project)
        self.iface.mapCanvas().refreshAllLayers()
        pass

    def handleOkBtnEvent(self):
        self.handleApplyBtnEvent()
        self.close()
        pass

    def handleCancelBtnEvent(self):
        self.close()
        pass
