import Ol from 'ol'
import Map from 'ol/Map.js';
import View from 'ol/View.js';
import GeoJSON from 'ol/format/GeoJSON.js';
import MultiPoint from 'ol/geom/MultiPoint.js';
import VectorLayer from 'ol/layer/Vector.js';
import VectorSource from 'ol/source/Vector.js';
import Select from 'ol/interaction/Select.js';
import {click, pointerMove, altKeyOnly} from 'ol/events/condition.js';
import {  Circle as CircleStyle,  Fill,  Stroke,  Style} from 'ol/style.js';
import Text from 'ol/style/Text';
import {  transform } from 'ol/proj.js';
import Circle from 'ol/geom/Circle';
import Feature from 'ol/Feature.js';
import {Tile as TileLayer,  VectorL} from 'ol/layer.js';
import {OSM,Vector} from 'ol/source.js';
import Overlay from 'ol/Overlay';
import {  defaults as defaultControls,  OverviewMap,  LayerSwitcher, FullScreen} from 'ol/control.js';


//import data

import clusterData from './cluster.geojson'
import clusterBoundaryData from './cluster_boundary.geojson'
import edgeyData from './edges.geojson'
import nodeData from './nodes.geojson'

var clusterStyleFunction = function(feature, resolution) {
  var clusterStyle = new Style({
    stroke: new Stroke({  color:  feature.get("stroke"),  width: 1  }),
    fill: new Fill({ color: feature.get("fill")      })
  });
  return clusterStyle; };

var clusterBoundaryStyleFunction = function(feature, resolution) {
  var clusterStyle = new Style({  stroke: new Stroke({  color: feature.get("stroke"),  width: 1    }),
    fill: new Fill({  color: feature.get("fill")  })
  });
  return clusterStyle; };

var edgeStyleFunction = function(feature, resolution) {
  var l=feature.get("level")
  var edgeStyle = new Style({  stroke: new Stroke({      color: feature.get("stroke"),    width: 10/ resolution })  });
  var empytStyle=new Style({});
  var stlye=empytStyle;

  if (resolution> 30) return new Style({});


  return edgeStyle;
  };



var nodeStyleFunction = function(feature, resolution) {
  var nodestyle = new Style({
  image:  new CircleStyle({
            radius: 20 / (resolution/2),
            fill: new Fill({color: '#666666'}),
            stroke: new Stroke({color: '#666666', width: 1})
          }),
      });
    global.nodestyle=nodestyle
if (resolution < 1.7)
nodestyle.setText(createTextStyle(feature.get("label"), 20 ,resolution))

if (resolution> 30) return new Style({});
  return nodestyle;
};

var selectStyleFunctionForNode=function(feature, resolution) {

  var style=nodeStyleFunction(feature, resolution);
  style.setImage( new CircleStyle({
            radius: 20 / (resolution/2),
            fill: new Fill({color: 'red'}),
            stroke: new Stroke({color: 'red', width: 1})
          }))


  return style;

};



function getVisible(l,resolution)
{
  var visiable=false
  if (l == 1 && resolution< 30)  visiable= true;
  if (l == 2 && resolution< 20) visiable= true;
  if (l == 3 && resolution< 15)  visiable= true;
  if (l == 4 && resolution< 10)   visiable= true;
  if (l == 5 && resolution< 8)  visiable= true;
  if (l == 6 && resolution< 6)  visiable= true;
  if (l == 7 && resolution< 5)  visiable= true;
  if (l == 8 && resolution< 4)  visiable= true;
  return visiable
}



var createTextStyle = function(lbl, fontsize, resolution) {
  var fsize=  parseFloat(fontsize) ///resolution;
  var nodetext=
     new Text({  font:  fsize + 'px arial',  text: lbl,
      fill: new Fill({      color: 'rgba(0,0,0,0.5)'    }),
      stroke: new Stroke({  color: 'rgba(0,0,0,0.5)', width: 1  }),
      offsetX: 0,
      offsetY: 0,//boxheight/2,
    });
    return nodetext;
  };




var clusterSource = new Vector({  url: clusterData,  format: new GeoJSON() });
var clusterLayer = new VectorLayer({  source: clusterSource,  style: clusterStyleFunction });

var clusterBoundaySource = new Vector({ url: clusterBoundaryData, format: new GeoJSON() });
var clusterBoundayLayer = new VectorLayer({   source: clusterBoundaySource,   style: clusterBoundaryStyleFunction });

var edgeSource = new Vector({  url: edgeyData,  format: new GeoJSON() });
var edgesLayer = new VectorLayer({  source: edgeSource,  style: edgeStyleFunction});

var nodeSource = new Vector({  url: nodeData,  format: new GeoJSON()});
var nodesLayer = new VectorLayer({  source: nodeSource,  style: nodeStyleFunction});


//var geolayer = new TileLayer({  source: new OSM()});
// clusterLayer,clusterBoundayLayer,
var map = new Map({
  controls: defaultControls().extend([new OverviewMap()]),
  layers: [ clusterLayer,clusterBoundayLayer,edgesLayer, nodesLayer],
  target: 'map',
  view: new View({center:  [17759.391499406964, -10439.758404798833],
      zoom: 17,//12, //17
      maxZoom: 18,
      minZoom: 5  })
});

global.map = map

var popup = new Overlay({  element: document.getElementById('popup') });
map.addOverlay(popup);


global.popup =popup

var edgeSelectPointerMove = new Select({
  condition: pointerMove,
  layers: [edgesLayer]
  });


  var nodeSelectPointerMove = new Select({
    condition: pointerMove,
    layers: [nodesLayer],
       style: selectStyleFunctionForNode
    });

map.addInteraction(edgeSelectPointerMove);
map.addInteraction(nodeSelectPointerMove);




map.on('click', function(evt) {
  var element = popup.getElement();
  $(element).popover('destroy');
  var feature = map.forEachFeatureAtPixel(evt.pixel,
      function(feature, layer) {      return feature;  });
      if (feature) {
          var element = popup.getElement();
        var geometry = feature.getGeometry();
        var fid=feature.getId()
        var ftype = feature.getGeometry().getType()
        if ( fid &&  fid.search("cluster")>-1 ) return 0;

        $(element)[0].title =feature.get('label')
        var pmid=  feature.get('label')
         var content
          if ( fid &&  fid.search("node")>-1 )  {
         content =  '<a target="_blank" href="https://www.ncbi.nlm.nih.gov/pubmed/'+pmid+'/">' + pmid  + "</a>  " ;
        }

        if ( fid &&  fid.search("edge")>-1 )  {
            console.log(pmid)
            var e1=pmid.split(" -- ")[0]
            var e2=pmid.split(" -- ")[1]
       content =  '<a target="_blank" href="https://www.ncbi.nlm.nih.gov/pubmed/'+e1+'/">' + e1  + "</a> <br> "       ;
       content =  content+  '<a target="_blank" href="https://www.ncbi.nlm.nih.gov/pubmed/'+e2+'/">' + e2  + "</a> <br>  "     ;

      }


        $(element).popover('destroy');
        popup.setPosition(evt.coordinate);
        $(element).popover({ placement: 'top',  animation: false,  html: true,  content: content,    });
        $(element).popover('show');
  }
});
