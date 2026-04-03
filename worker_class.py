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

from qgis.gui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
import tempfile
import os
from qgis.core import *
from .preparation import *
from .graph_processing import overall_call
import processing


class StartScript(QgsTask):
    def __init__(self, desc, flags, selectedLayer, pt, cleanTresholdValue,
                 outLineEdit, QgsProject, fields_names):
        QgsTask.__init__(self, desc, flags)
        self.selectedLayer = selectedLayer
        self.pt = pt
        self.cleanTresholdValue = cleanTresholdValue
        self.outLineEdit = outLineEdit
        self.QgsProject = QgsProject
        self.result = None
        self.logText = ''
        self.fields_names = fields_names
        self.error_reason = ''

        self.base_dir = tempfile.gettempdir()
        self.attributes_file_path = os.path.join(self.base_dir, 'attributes_temp.csv')
        self.points_file_path = os.path.join(self.base_dir, 'points_temp.csv')
        self.original_file_path = os.path.join(self.base_dir, 'original_temp.csv')

    def run(self):
        try:
            return self._run_ranking()
        except Exception as ex:
            self.logText = 'Errors occurred'
            raise ex

    def _ensure_vector_layer(self, layer_or_source, layer_name):
        if isinstance(layer_or_source, QgsVectorLayer):
            return layer_or_source

        if layer_or_source is None:
            return None

        layer = QgsVectorLayer(layer_or_source, layer_name, 'ogr')
        if layer.isValid():
            return layer

        layer = QgsVectorLayer(layer_or_source, layer_name, 'memory')
        if layer.isValid():
            return layer

        return None

    def _fix_geometries_and_v_clean_in_memory(self):
        self.logText = 'Fixing geometries'
        vl = fix_geometries(self.selectedLayer, 'TEMPORARY_OUTPUT')
        vl = self._ensure_vector_layer(vl, 'fix')

        if vl is None:
            raise Exception('Failed to create fixed geometry layer')

        if self.isCanceled():
            return None, None

        if self.cleanTresholdValue.replace(' ', '') != '':
            self.setProgress(5)
            self.logText = 'Filling gaps (v.clean)'

            try:
                cleaned_layer = clean_gaps(vl, self.cleanTresholdValue, 'TEMPORARY_OUTPUT')
                cleaned_layer = self._ensure_vector_layer(cleaned_layer, 'v_clean')

                if cleaned_layer is None:
                    raise Exception('Failed to create cleaned layer')
            except Exception:
                self.error_reason = 'grass'
                self.logText = ''
                return None, None
        else:
            if vl.fields().indexFromName('fid') == -1:
                pr = vl.dataProvider()
                pr.addAttributes([QgsField("fid", QVariant.Int)])
                vl.updateFields()

            cleaned_layer = vl

        buffer_layer = createCleanedBuffer(cleaned_layer)
        buffer_layer.setProviderEncoding(u'UTF-8')
        buffer_layer.dataProvider().setEncoding(u'UTF-8')

        return cleaned_layer, buffer_layer

    def _run_ranking(self):
        cleaned_layer = None

        try:
            cleaned_layer, buffer_layer = self._fix_geometries_and_v_clean_in_memory()

            if cleaned_layer is None:
                return False

            if self.isCanceled():
                return False
            else:
                self.setProgress(15)
                self.logText = 'Clear attribute fields'
                cleaned_layer.startEditing()

                count = 0
                del_list = []
                for field in cleaned_layer.dataProvider().fields():
                    if field.name() != 'fid':
                        del_list.append(count)
                    count += 1

                cleaned_layer.dataProvider().deleteAttributes(del_list)
                cleaned_layer.updateFields()
                cleaned_layer.commitChanges()

            if self.isCanceled():
                return False
            else:
                self.setProgress(20)
                self.logText = 'Create lines segments'
                clip_output = clip_line_to_segment(cleaned_layer)
                clipped_vector_layer = clip_output[0]

            if self.isCanceled():
                return False
            else:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "CSV"
                options.fileEncoding = "utf-8"
                QgsVectorFileWriter.writeAsVectorFormatV2(
                    clip_output[1],
                    self.attributes_file_path,
                    QgsCoordinateTransformContext(),
                    options,
                )

            if self.isCanceled():
                return False
            else:
                clipped_vector_layer.startEditing()
                self.setProgress(25)
                self.logText = 'Creating "fid" attributes'
                all_f = clipped_vector_layer.featureCount()

                for feature in clipped_vector_layer.getFeatures():
                    progress = 25 + (int(feature.id()) * 10) / all_f
                    self.setProgress(progress)

                    if self.isCanceled():
                        break
                    else:
                        if feature.geometry().wkbType() == 0:
                            clipped_vector_layer.deleteFeature(feature.id())
                        else:
                            feature['fid'] = feature.id()
                            clipped_vector_layer.updateFeature(feature)

                clipped_vector_layer.commitChanges()
                self.setProgress(36)
                self.logText = 'Calculating lines intersections'

            if self.isCanceled():
                return False
            else:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "CSV"
                options.fileEncoding = "utf-8"
                QgsVectorFileWriter.writeAsVectorFormatV2(
                    clipped_vector_layer,
                    self.original_file_path,
                    QgsCoordinateTransformContext(),
                    options,
                )

            if self.isCanceled():
                return False
            else:
                intersect_point_layer = get_lines_intersections(
                    clipped_vector_layer,
                    self.setProgress,
                )

            if self.isCanceled():
                return False
            else:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "CSV"
                options.fileEncoding = "utf-8"
                QgsVectorFileWriter.writeAsVectorFormatV2(
                    intersect_point_layer,
                    self.points_file_path,
                    QgsCoordinateTransformContext(),
                    options,
                )

            if self.isCanceled():
                return False
            else:
                self.setProgress(47)
                self.logText = 'Get nearest segment id'
                start_segment_id = get_nearest_segmentId(
                    clipped_vector_layer,
                    self.pt,
                    self.setProgress,
                )

            if self.isCanceled():
                return False
            else:
                self.setProgress(58)
                self.logText = 'Graph traversal ranking'
                out_dataset = overall_call(
                    self.original_file_path,
                    self.points_file_path,
                    start_segment_id,
                    self.attributes_file_path,
                    self.setProgress,
                )

                os.remove(self.points_file_path)
                os.remove(self.original_file_path)
                os.remove(self.attributes_file_path)

                clipped_vector_layer.selectAll()
                outLayer = processing.run(
                    "native:saveselectedfeatures",
                    {
                        'INPUT': clipped_vector_layer,
                        'OUTPUT': 'memory:rank_output',
                    }
                )['OUTPUT']

            if self.isCanceled():
                return False
            else:
                self.setProgress(89)
                self.logText = 'Creating attributes table'
                pr = outLayer.dataProvider()

                for field_name in self.fields_names:
                    pr.addAttributes([QgsField(field_name, QVariant.Int)])

                outLayer.updateFields()
                outLayer.startEditing()

                all_f = outLayer.featureCount()
                for feature in outLayer.getFeatures():
                    progress = 89 + (int(feature.id()) * 10) / all_f
                    self.setProgress(progress)

                    try:
                        if self.isCanceled():
                            break
                        else:
                            f_id = feature['fid']
                            rank = out_dataset[f_id][0]
                            value_shreve = out_dataset[f_id][1]
                            value_strahler = out_dataset[f_id][2]
                            distance = out_dataset[f_id][3]

                            try:
                                feature[self.fields_names[0]] = rank
                            except Exception:
                                pass

                            try:
                                feature[self.fields_names[1]] = value_shreve
                            except Exception:
                                pass

                            try:
                                feature[self.fields_names[2]] = value_strahler
                            except Exception:
                                pass

                            try:
                                feature[self.fields_names[3]] = distance
                            except Exception:
                                pass

                            outLayer.updateFeature(feature)
                    except Exception:
                        outLayer.deleteFeature(feature.id())

                outLayer.commitChanges()
                createSpatialIndex(outLayer)
                outLayerWithAttr = joinAttributes(outLayer, buffer_layer, self.fields_names)
                outLayerWithAttr.setProviderEncoding(u'UTF-8')
                outLayerWithAttr.dataProvider().setEncoding(u'UTF-8')

            if self.isCanceled():
                del cleaned_layer
                return False
            else:
                if self.outLineEdit.replace(' ', '') != '':
                    if self.outLineEdit[-5:] != '.gpkg':
                        self.outLineEdit = self.outLineEdit + '.gpkg'
                    try:
                        QgsVectorFileWriter.writeAsVectorFormat(
                            layer=outLayerWithAttr,
                            fileName=self.outLineEdit,
                            fileEncoding="utf-8",
                            driverName="GPKG",
                        )
                        self.result = QgsVectorLayer(
                            self.outLineEdit,
                            self.outLineEdit.split('/')[-1][:-5],
                            "ogr",
                        )
                    except Exception:
                        pass
                else:
                    self.result = outLayerWithAttr

            if self.isCanceled():
                del cleaned_layer
                return False
            else:
                del cleaned_layer
                return True

        except Exception as ex:
            del cleaned_layer
            raise ex

    def cancel(self):
        super().cancel()

    def finished(self, result):
        self.setProgress(0)
        self.logText = ''

        if result is False:
            try:
                os.remove(self.points_file_path)
                os.remove(self.original_file_path)
                os.remove(self.attributes_file_path)
            except Exception:
                pass

            if self.error_reason == 'grass':
                QMessageBox.critical(
                    None,
                    "Error",
                    'GRASS modules are not available. Activate GRASS or leave snapping threshold empty',
                )

        if result is True:
            QMessageBox.information(None, "Success", 'Lines Ranking process is finished')


class Worker(QObject):
    def __init__(self, qapp, selectedLayer, pt, cleanTresholdValue, outLineEdit,
                 QgsProject, prBar, logTxtLine, fields_names):
        self.qapp = qapp
        self.selectedLayer = selectedLayer
        self.pt = pt
        self.cleanTresholdValue = cleanTresholdValue
        self.outLineEdit = outLineEdit
        self.QgsProject = QgsProject
        self.result = None
        self.progress = prBar
        self.logTxtLine = logTxtLine
        self.fields_names = fields_names

    def setResult(self, r):
        QgsProject.instance().addMapLayer(r)
        self.progress = 0

    def progressSet(self, progress, logText):
        self.logTxtLine.setText(logText)
        if isinstance(progress, float):
            progress = int(round(progress))

        self.progress.setValue(progress)

    def StartScriptTask(self):
        self.task = StartScript(
            'Lines Ranking processing',
            QgsTask.CanCancel,
            self.selectedLayer,
            self.pt,
            self.cleanTresholdValue,
            self.outLineEdit,
            self.QgsProject,
            self.fields_names,
        )
        self.task.progressChanged.connect(
            lambda: self.progressSet(self.task.progress(), self.task.logText)
        )
        self.task.taskCompleted.connect(lambda: self.setResult(self.task.result))
        self.qapp.taskManager().addTask(self.task)

    def cancelTask(self):
        self.task.cancel()
        QMessageBox.critical(None, "Terminating", 'Lines Ranking process was canceled')
