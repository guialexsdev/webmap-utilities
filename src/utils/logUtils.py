from qgis.core import QgsMessageLog, Qgis

def info(msg, tabName = 'WMU'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Info)

def warning(msg, tabName = 'WMU'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Warning)

def error(msg, tabName = 'WMU'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Critical)