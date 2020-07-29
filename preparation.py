# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Lines Ranking
                                 A QGIS plugin
                              -------------------
        begin                : 2020-07-07
        copyright            : (C) 2020 by Julia Borisova, Mikhail Sarafanov 
        email                : yulashka.htm@yandex.ru, mik_sar@mail.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsEllipsoidUtils, QgsProject, QgsMapLayer, QgsWkbTypes, Qgis, QgsApplication, QgsFeature, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSpatialIndex, QgsFeatureRequest, QgsPointXY, QgsDistanceArea, QgsUnitTypes
import processing

def fix_geometries(layer):
    algorithmOutput = processing.run(
        'native:fixgeometries',
        {
            "INPUT": layer,
            "OUTPUT": 'memory:fixed_geometry'
        }
    )
    fixedVectorLayer=algorithmOutput["OUTPUT"]
    return fixedVectorLayer

def clip_line_to_segment(layer):
    algorithmOutput = processing.run(
        'qgis:splitwithlines',
        {
            "INPUT": layer,
            "LINES":layer,
            "OUTPUT": 'memory:split_no_attr'
        }
    )
    clipedVectorLayer=algorithmOutput["OUTPUT"]
    
    #Setting id field for split layer
    algorithmOutput=processing.run(
        'qgis:fieldcalculator',
        {
            'INPUT': clipedVectorLayer,
            'FIELD_NAME': 'id',
            'FIELD_TYPE':1,
            'FIELD_LENGTH':7,
            'FIELD_PRECISION':1,
            'NEW_FIELD':True,
            'FORMULA':'$id',
            'OUTPUT': 'memory:with_id_attr'
        }
    )
    with_id_attr_layer=algorithmOutput["OUTPUT"]
    algorithmOutput=processing.run(
        'qgis:fieldcalculator',
        {
            'INPUT': with_id_attr_layer,
            'FIELD_NAME': 'length',
            'FIELD_TYPE':1,
            'FIELD_LENGTH':15,
            'FIELD_PRECISION':1,
            'NEW_FIELD':True,
            'FORMULA':'$length',
            'OUTPUT': 'memory:split_with_attr'
        }
    )
    attrClipedVectorLayer=algorithmOutput["OUTPUT"]
    attrClipedVectorLayer.commitChanges()
    return [clipedVectorLayer, attrClipedVectorLayer]

def clean_gaps(layer, treshold):
    algorithmOutput = processing.run(
            "grass7:v.clean",
            { '-b' : False,
              '-c' : False, 
              'GRASS_MIN_AREA_PARAMETER' : 0.0001, 
              'GRASS_OUTPUT_TYPE_PARAMETER' : 0, 
              'GRASS_REGION_PARAMETER' : None, 
              'GRASS_SNAP_TOLERANCE_PARAMETER' : -1, 
              'GRASS_VECTOR_DSCO' : '', 
              'GRASS_VECTOR_EXPORT_NOCAT' : False, 
              'GRASS_VECTOR_LCO' : '', 
              'error' : 'memory:', 
              'input' : layer, 
              'output' : 'TEMPORARY_OUTPUT', 
              'threshold' : treshold, 
              'tool' : [1], 
              'type' : [1] })
    return algorithmOutput['output']

def get_lines_intersections(layer, set_progress_funk):
    algorithmOutput = processing.run(
        'qgis:lineintersections',
        {
            "INPUT": layer,
            "INTERSECT":layer,
            "OUTPUT": 'memory:intersection'
        }
    )
    intersectPointLayer=algorithmOutput["OUTPUT"]             

    pr = intersectPointLayer.dataProvider() 
    pr.addAttributes([QgsField("geometry",  QVariant.String)]) 
    intersectPointLayer.updateFields()
    intersectPointLayer.startEditing()

    all_f=intersectPointLayer.featureCount()
    for feature in intersectPointLayer.getFeatures():
        progress=36+(int(feature.id())*10)/all_f 
        set_progress_funk(progress)
        feature['geometry']=feature.geometry().asWkt()
        intersectPointLayer.updateFeature(feature)
    intersectPointLayer.commitChanges()
    return intersectPointLayer

def get_nearest_segmentId(layer, QgsPointXY, set_progress_funk):
    spIndex = QgsSpatialIndex()
    all_f=layer.featureCount()
    for feature in layer.getFeatures():
        progress=47+(int(feature.id())*10)/all_f 
        set_progress_funk(progress)
        spIndex.addFeature(feature)
    nearestIds = spIndex.nearestNeighbor(QgsPointXY,1)
    nearest_feature = layer.getFeatures(QgsFeatureRequest().setFilterFid(nearestIds[0]))
    ftr = QgsFeature()
    nearest_feature.nextFeature(ftr)
    return ftr["fid"]

def createSpatialIndex(layer):
    processing.run(
        'qgis:createspatialindex',
        {
            "INPUT": layer
        }
    )

def createCleanedBuffer(layer):
    algorithmOutput = processing.run(
        'native:buffer',
        {
            'DISSOLVE' : False, 
            'DISTANCE' : 0.001, 
            'END_CAP_STYLE' : 0, 
            'INPUT' : layer, 
            'JOIN_STYLE' : 0, 
            'MITER_LIMIT' : 2, 
            'OUTPUT' : 'memory:buffer_layer', 
            'SEGMENTS' : 5 
        }
    )
    buffer_layer=algorithmOutput["OUTPUT"]
    return buffer_layer

def joinAttributes(outlayer, reallayer, user_fields_names):
    prov = reallayer.dataProvider()
    field_names = [field.name() for field in prov.fields()]
    for name in user_fields_names:
        if name in field_names:
            field_names.remove(name)
    algorithmOutput = processing.run(
        'native:joinattributesbylocation',
        {
            'DISCARD_NONMATCHING' : False, 
            'INPUT' : outlayer, 
            'JOIN' : reallayer, 
            'JOIN_FIELDS' : field_names, 
            'METHOD' : 0, 
            'OUTPUT' : 'memory:rank_attributes', 
            'PREDICATE' : [5], 
            'PREFIX' : '' 
        }
    )
    outlayerWithAttributes=algorithmOutput["OUTPUT"]
    return outlayerWithAttributes