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
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsSpatialIndex,
)
import processing


def fix_geometries(layer, output='TEMPORARY_OUTPUT'):
    algorithm_output = processing.run(
        'native:fixgeometries',
        {
            "INPUT": layer,
            "OUTPUT": output,
        }
    )
    fixed_vector_layer = algorithm_output["OUTPUT"]
    return fixed_vector_layer


def clip_line_to_segment(layer):
    algorithm_output = processing.run(
        'qgis:splitwithlines',
        {
            "INPUT": layer,
            "LINES": layer,
            "OUTPUT": 'memory:split_no_attr',
        }
    )
    clipped_vector_layer = algorithm_output["OUTPUT"]

    algorithm_output = processing.run(
        'qgis:fieldcalculator',
        {
            'INPUT': clipped_vector_layer,
            'FIELD_NAME': 'id',
            'FIELD_TYPE': 1,
            'FIELD_LENGTH': 7,
            'FIELD_PRECISION': 1,
            'NEW_FIELD': True,
            'FORMULA': '$id',
            'OUTPUT': 'memory:with_id_attr',
        }
    )
    with_id_attr_layer = algorithm_output["OUTPUT"]

    algorithm_output = processing.run(
        'qgis:fieldcalculator',
        {
            'INPUT': with_id_attr_layer,
            'FIELD_NAME': 'length',
            'FIELD_TYPE': 1,
            'FIELD_LENGTH': 15,
            'FIELD_PRECISION': 1,
            'NEW_FIELD': True,
            'FORMULA': '$length',
            'OUTPUT': 'memory:split_with_attr',
        }
    )
    attr_clipped_vector_layer = algorithm_output["OUTPUT"]
    attr_clipped_vector_layer.commitChanges()

    return [clipped_vector_layer, attr_clipped_vector_layer]


def clean_gaps(layer, threshold, output='TEMPORARY_OUTPUT'):
    algorithm_output = processing.run(
        "grass7:v.clean",
        {
            '-b': False,
            '-c': False,
            'GRASS_MIN_AREA_PARAMETER': 0.0001,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_SNAP_TOLERANCE_PARAMETER': -1,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'error': 'memory:',
            'input': layer,
            'output': output,
            'threshold': threshold,
            'tool': [1],
            'type': [1],
        }
    )
    return algorithm_output['output']


def get_lines_intersections(layer, set_progress_funk):
    algorithm_output = processing.run(
        'qgis:lineintersections',
        {
            "INPUT": layer,
            "INTERSECT": layer,
            "OUTPUT": 'memory:intersection',
        }
    )
    intersect_point_layer = algorithm_output["OUTPUT"]

    provider = intersect_point_layer.dataProvider()
    provider.addAttributes([QgsField("geometry", QVariant.String)])
    intersect_point_layer.updateFields()
    intersect_point_layer.startEditing()

    all_features = intersect_point_layer.featureCount()
    for feature in intersect_point_layer.getFeatures():
        progress = 36 + (int(feature.id()) * 10) / all_features
        set_progress_funk(progress)
        feature['geometry'] = feature.geometry().asWkt()
        intersect_point_layer.updateFeature(feature)

    intersect_point_layer.commitChanges()
    return intersect_point_layer


def get_nearest_segmentId(layer, point_xy, set_progress_funk):
    spatial_index = QgsSpatialIndex()
    all_features = layer.featureCount()

    for feature in layer.getFeatures():
        progress = 47 + (int(feature.id()) * 10) / all_features
        set_progress_funk(progress)
        spatial_index.addFeature(feature)

    nearest_ids = spatial_index.nearestNeighbor(point_xy, 1)
    nearest_feature = layer.getFeatures(QgsFeatureRequest().setFilterFid(nearest_ids[0]))
    feature_result = QgsFeature()
    nearest_feature.nextFeature(feature_result)

    return feature_result["fid"]


def createSpatialIndex(layer):
    processing.run(
        'qgis:createspatialindex',
        {
            "INPUT": layer,
        }
    )


def createCleanedBuffer(layer):
    algorithm_output = processing.run(
        'native:buffer',
        {
            'DISSOLVE': False,
            'DISTANCE': 0.001,
            'END_CAP_STYLE': 0,
            'INPUT': layer,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'OUTPUT': 'memory:buffer_layer',
            'SEGMENTS': 5,
        }
    )
    buffer_layer = algorithm_output["OUTPUT"]
    return buffer_layer


def joinAttributes(outlayer, reallayer, user_fields_names):
    provider = reallayer.dataProvider()
    field_names = [field.name() for field in provider.fields()]

    for name in user_fields_names:
        if name in field_names:
            field_names.remove(name)

    algorithm_output = processing.run(
        'native:joinattributesbylocation',
        {
            'DISCARD_NONMATCHING': False,
            'INPUT': outlayer,
            'JOIN': reallayer,
            'JOIN_FIELDS': field_names,
            'METHOD': 0,
            'OUTPUT': 'memory:rank_attributes',
            'PREDICATE': [5],
            'PREFIX': '',
        }
    )
    outlayer_with_attributes = algorithm_output["OUTPUT"]
    return outlayer_with_attributes
