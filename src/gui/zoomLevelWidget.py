import math
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from qgis.core import QgsProject

class ZoomLevelWidget(QWidget):
    def __init__(self, iface, parent, *args, **kwargs):
        super(ZoomLevelWidget, self).__init__(*args, **kwargs)
        self.iface = iface
        self.combo = QComboBox(parent)
        #self.label = QLabel(parent)

        #self.label.setText("Zoom Level:")
        predefinedScales = QgsProject.instance().viewSettings().mapScales()
        for z in range(len(predefinedScales)):
            self.combo.addItem(str(z))

        layout = QHBoxLayout()
        #layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.setLayout(layout)

        iface.mapCanvas().scaleChanged.connect(self.updateZoomLevelWidget)
        self.combo.currentTextChanged.connect(self.updateScale)

    def updateZoomLevelWidget(self):
        predefinedScales = QgsProject.instance().viewSettings().mapScales()
        if len(predefinedScales) != 0:
            scale = int(math.floor(self.iface.mapCanvas().scale()))
            targetScale = min(predefinedScales, key=lambda x:abs(x-scale))
            zoomLevelComboIndex = predefinedScales.index(targetScale)
            self.combo.setCurrentIndex(zoomLevelComboIndex)

    def updateScale(self, index):
        predefinedScales = QgsProject.instance().viewSettings().mapScales()
        canvas = self.iface.mapCanvas()
        canvas.zoomScale(predefinedScales[int(index)])
