import os

from qgis.core import QgsProject, QgsMapLayer
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtWidgets import QComboBox, QGroupBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../ui/webmap_layer_visibility_dialog.ui'))

class LayerVisibilityDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, layers: list[QgsMapLayer], defaultZoomMin: float, defaultZoomMax: float, parent=None):
        super(LayerVisibilityDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface
        self.layers: list[QgsMapLayer] = layers
        self.visibilityBoxWidget: QGroupBox = self.visibilityBoxWidget
        self.minZoomLevelCombo: QComboBox = self.minZoomLevelCombo
        self.maxZoomLevelCombo: QComboBox = self.maxZoomLevelCombo

        if layers.__len__() == 1:
            self.visibilityBoxWidget.setChecked(layers[0].hasScaleBasedVisibility())
        else:
            self.visibilityBoxWidget.setChecked(False)

        predefinedScales = QgsProject.instance().viewSettings().mapScales()

        for z in range(len(predefinedScales)):
            self.minZoomLevelCombo.addItem(str(z))
            self.maxZoomLevelCombo.addItem(str(z))

        if defaultZoomMin is not None and defaultZoomMax is not None:
            self.minZoomLevelCombo.setCurrentIndex(defaultZoomMin)
            self.maxZoomLevelCombo.setCurrentIndex(defaultZoomMax)

        self.buttons.accepted.connect(self.onApply)
        self.buttons.rejected.connect(self.close)

    def onApply(self):
        predefinedScales = QgsProject.instance().viewSettings().mapScales()
        for layer in self.layers:
            layer.setScaleBasedVisibility(self.visibilityBoxWidget.isChecked())
            
            if self.visibilityBoxWidget.isChecked():
                indexMin = int(self.minZoomLevelCombo.currentText())
                indexMax = int(self.maxZoomLevelCombo.currentText())

                # These steps are necessary because QGis use min (exclusive), be here we use min (inclusive)
                # If user selected zoom level > 0, than subtract 1 because we use inclusive range. 
                # If zoom = 0, we just subtract a small number to make 0 included.
                minScale = predefinedScales[indexMin - 1] if indexMin > 0 else predefinedScales[0] - 100
                maxScale = predefinedScales[indexMax]

                layer.setMinimumScale(minScale)
                layer.setMaximumScale(maxScale)

        self.iface.mapCanvas().refreshAllLayers()

        self.close()
