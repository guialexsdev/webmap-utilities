from qgis.core import QgsProcessingProvider
from .createClusteredVisualization import CreateClusteredVisualization
from .createGridVisualization import CreateGridVisualization
from .shadedReliefCreator import ShadedReliefCreator
from .createAerialPerspective import CreateAerialPerspective
from .clusterizationByDistance import CreateClusterizationByDistance

class Provider(QgsProcessingProvider):
    """Processing Webmap Utilities provider."""

    def id(self, *args, **kwargs):
        """Return the id."""
        return 'webmap_utilities'

    def name(self, *args, **kwargs):
        """Return the name."""
        return 'Webmap Utilities'

    def icon(self):
        """Return the icon."""
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self, *args, **kwargs):
        """Load the algorithms"""
        self.addAlgorithm(CreateClusterizationByDistance())
        self.addAlgorithm(CreateClusteredVisualization())
        self.addAlgorithm(CreateGridVisualization())
        self.addAlgorithm(ShadedReliefCreator())
        self.addAlgorithm(CreateAerialPerspective())