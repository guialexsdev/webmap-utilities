from qgis.core import QgsProject, QgsLayerTreeLayer, QgsLayerTreeNode, QgsLayerTreeGroup, QgsMapLayer, QgsLayerTree, QgsMapLayer, QgsMessageLog
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QMessageBox
from ..utils.webmapCommons import Utils
from ..database.settingsManager import SettingsManager

class LayerTreeOrganizer:
    def __init__(self, iface, settingsManager: SettingsManager):
        self.iface: QgisInterface = iface
        self.settingsManager = settingsManager

    def getTree(self, tags, tree, path: list[str], root: QgsLayerTreeNode):
        for c in root.children():
            if c.nodeType() == QgsLayerTree.NodeType.NodeGroup:
                self.getTree(tags, tree, f'{path}.{c.name()}', c)
            else:
                for tag in tags:
                    currentLayerTag = Utils.getLayerTag(c, self.settingsManager.settings)
                    if currentLayerTag ==tag:
                        if path in tree:
                            if tag not in tree[path]:
                                tree[path].append(tag)
                        else:
                            tree[path] = [tag]

    def moveLayersToGroup(self, layers: list[QgsMapLayer], group: QgsLayerTreeGroup):
        root = QgsProject.instance().layerTreeRoot()
        index = 0

        for layer in layers:
            treeLayer = root.findLayer(layer.id())
            treeLayerClone = treeLayer.clone()
            parent: QgsLayerTreeNode = treeLayer.parent()

            group.insertChildNode(index, treeLayerClone)
            parent.removeChildNode(treeLayer)
            index = index + 1

    def getGroupInside(self, group: QgsLayerTree, name: str):
        for g in group.children():
            if g.name() == name:
                return g
        return None

    def createPath(self, path: str):
        root = QgsProject.instance().layerTreeRoot()

        if path == 'root':
            return root
        
        groups = path.split('.')

        if groups[0] == 'root':
            groups.pop(0) #remove 'root'

        currentGroup = root
        for group in groups:
            foundGroup = self.getGroupInside(currentGroup, group)
            if foundGroup is None:
                currentGroup = currentGroup.addGroup(group)
            else:
                currentGroup = foundGroup

        return currentGroup
    
    def getTocLayers(self, arr, group, tags):
        settings = self.settingsManager.settings

        for child in group.children():
            tagMatched = False

            for tag in tags:
                if isinstance(child, QgsLayerTreeLayer) and Utils.getLayerTag(child.layer(), settings) == tag:
                    tagMatched = True

            if tagMatched:
                arr.append(child.layer())

    def getStructure(self):
        #selectedNodes = self.iface.layerTreeView().selectedLayerNodes()
        #root = selectedNodes[0] if selectedNodes.__len__() > 0 else QgsProject.instance().layerTreeRoot()
        #rootName = root.name() if root.name() is not None else 'root'

        tags = self.settingsManager.settings.tags

        tree = {}
        self.getTree(tags, tree, 'root', QgsProject.instance().layerTreeRoot())
        return tree

    def applyStructure(self, referenceTree):
        root = QgsProject.instance().layerTreeRoot()

        for path in referenceTree:
            createdGroup = self.createPath(path)
            layers = []
            self.getTocLayers(layers, root, referenceTree[path])
            self.moveLayersToGroup(layers, createdGroup)
