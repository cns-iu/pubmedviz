import xml.etree.ElementTree as ET
import numpy as np
import json
import networkx as nx
import pygraphviz as pgv
import pandas as pd

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

mappath="map.svg"
input_graph="k-neighbor_10000.dot"
papermeshfile="papermeshname.csv"
papermesh=pd.read_csv(papermeshfile)
#papermesh=papermesh[papermesh["is_major_topic"]=='Y'].reset_index()
G=nx.Graph(pgv.AGraph(input_graph))

clusteroutput="../map/map-data/cluster.geojson"
polylineoutput="../map/map-data/cluster_boundary.geojson"
edgesoutput="../map/map-data/edges.geojson"
nodesoutput="../map/map-data/nodes.geojson"

root = ET.parse(mappath).getroot()

bounds = {
  "minx": -102944.7969, 
  "miny": -100931.5781, 
  "maxx": 100477.6328, 
  "maxy": 98229.6641
}

dist = {"minx": 1000000, "miny": 1000000, "maxx": -1000000, "maxy": -1000000}
def MapPoint(x, y):
    dist["minx"] = min(dist["minx"], x)
    dist["miny"] = min(dist["miny"], y)
    dist["maxx"] = max(dist["maxx"], x)
    dist["maxy"] = max(dist["maxy"], y)
    
    """Translate x/y into fake lon/lat values"""
    lon = ((x - bounds['minx']) / (bounds['maxx'] - bounds['minx'])) * 120 - 60
    lat = ((y - bounds['miny']) / (bounds['maxy'] - bounds['miny'])) * 120 - 60
    return lon, lat

def MapPoints(coords):
    return [ MapPoint(x,y) for x,y in coords ]

def Feature():
    n={}
    n["type"]="Feature"
    n["geometry"]={}
    n["geometry"]["type"]=""
    n["geometry"]["coordinates"]={}
    n["properties"]={}
    return n


def FeatureCollection(features):
    return {
        "type": "FeatureCollection",
        # "crs": {
        #     "type": "name",
        #     "properties": {
        #         "name": "EPSG:3857"
        #     }
        # },
        "features": features
    }

n2point = {}
for n in G.nodes():
    x1=float(G.node[n]["pos"].split(",")[0])
    y1=float(G.node[n]["pos"].split(",")[1])
    x1, y1 = MapPoint(x1, y1)
    n2point[n] = Point(x1, y1)

def getClusterName(points):
    meshcount={}
    nodesincluste=0
    for n in G.nodes():
        point = n2point[n]
        polygon = Polygon(points)
        if polygon.contains(point):
            nodesincluste=nodesincluste+1
            m=papermesh[papermesh['pmid']==int(n)].reset_index()
            #import pdb; pdb.set_trace()
            for i in range(0, len(m)):
                meshname=papermesh['mesh_name'][i]
                if  meshname in meshcount:
                    meshcount[meshname]=meshcount[meshname] +1
                else:
                    meshcount[meshname]= 1
    #print(nodesincluste, len(meshcount))
    if nodesincluste > 10 and len(meshcount)>3:
        #import pdb; pdb.set_trace()
        o=sorted(meshcount.items(), key=lambda x: x[1], reverse=True)
        #print(o)
        txt=o[0][0]  + ", " + o[1][0]+ ", " + o[2][0]
        print(txt)
        return txt
    else:
        return ""


def polygon_area(points):
    """Returns the area of the polygon whose vertices are given by the
    sequence points.
    """
    area = 0
    q = points[-1]
    for p in points:
        area += p[0] * q[1] - p[1] * q[0]
        q = p
    return abs( area / 2)


def process_polygon(xml,id):
    polygon=Feature()
    polygon["geometry"]["type"]="Polygon"
    polygon["id"]="cluster" + str(id)
    points=xml.attrib.pop('points')
    points_array = [ (float(p.split(",")[0]), float(p.split(",")[1])) for p in points.split(" ") ]
    points_array = MapPoints(points_array)
    area=int(polygon_area(points_array))
    polygon["properties"]=xml.attrib
    polygon["properties"]["label"]= str(area) + getClusterName(points_array)
    polygon["geometry"]["coordinates"]=[points_array]
    polygon["properties"]["area"]=area

    return polygon


def process_polyline(xml):
    polygon=Feature()
    polygon["geometry"]["type"]="LineString"
    points=xml.attrib.pop('points')
    #import pdb; pdb.set_trace()
    points_array = [ (float(p.split(",")[0]), float(p.split(",")[1])) for p in points.strip().split(" ") ]
    points_array = MapPoints(points_array)
    polygon["properties"]=xml.attrib
    polygon["properties"]["label"]=""
    polygon["geometry"]["coordinates"]=points_array
    polygon["properties"]["area"]=int(polygon_area(points_array))
    return polygon


def process_edge(xml,G,c):
    #import pdb; pdb.set_trace()
    edge=Feature()
    edge["id"]="edge" + str(c)
    edge["geometry"]["type"]="LineString"
    points=xml[1].attrib.pop('d')
    points=points.replace("M"," ").replace("D"," ").replace("C"," ")
    #import pdb; pdb.set_trace()
    points_array = [ (float(p.split(",")[0]), float(p.split(",")[1])) for p in points.strip().split(" ") ]
    points_array = MapPoints(points_array)
    edge["properties"]=xml[1].attrib
    n1=xml[0].text.split("--")[0]
    n2=xml[0].text.split("--")[1]
    edge["properties"]["src"]=n1
    edge["properties"]["dest"]=n2
    edge["properties"]["label"]=G.node[n1]["label"] + " -- " +  G.node[n2]["label"]
    edge["properties"]["weight"]=""
    edge["geometry"]["coordinates"]=points_array
    edge["properties"]["level"]="1"

    return edge


def process_node(xml,G):
    #import pdb; pdb.set_trace()
    node_g=xml[0].text
    node=Feature()
    node["geometry"]["type"]="Point" #"Point"
    node["id"]="node" + node_g
    node["properties"]=G.node[node_g]
    x=float(xml[1].attrib.pop('x'))
    y=float(xml[1].attrib.pop('y'))
    x,y = MapPoint(x, y)
    #h= float(node["properties"]["height"]) * 1.10 * 72  # inch to pixel conversion
    #w=float(node["properties"]["width"]) * 1.10 * 72 # inch to pixel conversion
    #points_array=[[x-w/2,y-h/2], [x+w/2,y-h/2], [x+w/2,y+h/2], [x-w/2,y+h/2], [x-w/2,y-h/2]]

    node["properties"]["height"]="h"
    node["properties"]["width"]= "w"

    node["geometry"]["coordinates"]= [x,y] #[points_array] #//
    return node


def write_to_file(features,file):
    with open(file,"w") as f:
        data=json.dumps(FeatureCollection(features), indent=2)
        f.write(data)


polygons=[]
polylines=[]
edges=[]
nodes=[]
for child in root.findall('*[@id="graph0"]/*'):
    if "polygon" in child.tag:
        polygons.append(process_polygon(child,len(polygons)))
    if "polyline" in child.tag:
        polylines.append(process_polyline(child))
    if "{http://www.w3.org/2000/svg}g"==child.tag:
        if child.attrib["class"]=="node":
            #print (child[0].text)
            #print(child[1].attrib)
            nodes.append(process_node(child, G))
        if child.attrib["class"]=="edge":
            edges.append(process_edge(child,G,len(edges)))

polygons = polygons[1:] # scrap first rectangle
print(len(polygons), len(polylines), len(nodes), len(edges))

write_to_file(polygons,clusteroutput)
write_to_file(polylines,polylineoutput)
write_to_file(edges,edgesoutput)
write_to_file(nodes,nodesoutput)


print(json.dumps(dist, indent=2))

'''
<g id="node2830" class="node">
<title>3506</title>
<text text-anchor="middle" x="23888.5" y="-6861.22" font-family="Helvetica,sans-Serif" font-weight="bold" font-size="15.00">block copolymers</text>
</g>
'''

'''

<g id="edge5238" class="edge">
<title>3324&#45;&#45;971</title>
<path fill="none" stroke="grey" d="M7023.05,-6911.53C7021.39,-6919.29 7019.08,-6930.12 7017.69,-6936.64"/>
</g>
'''