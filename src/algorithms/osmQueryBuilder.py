import re
from textwrap import dedent
from qgis.core import QgsRectangle, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsMessageLog
import urllib.parse

class OSMQueryBuilder:
    def __init__(self, id = None, geomType = str):
        self.id = id
        self.items = []
        self.bbox = None
        self.geomType = geomType
        
    def setBBox(self, rawBbox: str):
        res = re.findall(r'\[.*?\]', rawBbox)
        epsg = res[0][1:-1]
        rectRaw = rawBbox.replace(res[0], '')
        rectCoords = rectRaw.split(',') #0: xmin / 1: xmax / 2: ymin / 3: ymax
        rect = QgsRectangle(float(rectCoords[0]),float(rectCoords[2]),float(rectCoords[1]),float(rectCoords[3]))

        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(epsg),
            QgsCoordinateReferenceSystem("EPSG:4326"), 
            QgsProject.instance()
        )

        transfomedRect = transform.transformBoundingBox(rect)
        self.bbox = "%f,%f,%f,%f" %(transfomedRect.yMinimum(), transfomedRect.xMinimum(), transfomedRect.yMaximum(), transfomedRect.xMaximum())

    def addQueryItem(self, key, value):
        self.items.append((key,value))
    
    def toQueryString(self):
        oqlNodeItems     = []
        oqlWayItems      = []
        oqlRelationItems = []

        for item in self.items:
            key = item[0]
            value = item[1]
            oqlNodeItems.append(f'node["{key}"="{value}"]({self.bbox});\n')
            oqlWayItems.append(f'way["{key}"="{value}"]({self.bbox});\n')
            oqlRelationItems.append(f'relation["{key}"="{value}"]({self.bbox});\n')

        allOqlItems = []
        allOqlItems.extend(oqlNodeItems)
        allOqlItems.extend(oqlWayItems)
        allOqlItems.extend(oqlRelationItems)
        
        return dedent(f"""
        [out:xml][timeout:25];
        (
        {''.join(allOqlItems)});
        (._;>;);
        out body;
        """)
