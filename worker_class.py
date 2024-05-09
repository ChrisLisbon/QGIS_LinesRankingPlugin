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
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import time
import os, string
from qgis.core import *
from .preparation import *
from .graph_processing import overall_call
import processing


TMP_DIRECTORY_NAME = 'lines_ranking_tmp_directory'

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

        self.base_dir = os.path.abspath('.')
        if 'C:' in self.base_dir:
            # Generate temporary folder not in C disk
            available_drives = ['%s:' % d for d in string.ascii_uppercase if
                                os.path.exists('%s:' % d)]
            if len(available_drives) >= 2:
                # There is an alternative:
                available_drives = list(filter(lambda x: 'C' not in x, available_drives))
                self.base_dir = os.path.join(available_drives[0], TMP_DIRECTORY_NAME)
                self.create_base_directory_if_required()

        self.attributes_file_path = os.path.join(self.base_dir, 'attributes_temp.csv')
        self.points_file_path = os.path.join(self.base_dir, 'points_temp.csv')
        self.original_file_path = os.path.join(self.base_dir, 'original_temp.csv')

        # Set temporary files with intermediate results
        # (needed in the case if input layer not in shp format)
        self.tmp_after_fixing_geometries = os.path.join(self.base_dir,
                                                        'tmp_lines_ranking_after_fixing_geometries.gpkg')
        self.tmp_after_vclean = os.path.join(self.base_dir, 'tmp_lines_ranking_after_vclean.gpkg')
        self.remove_tmp_files()

    def create_base_directory_if_required(self):
        if os.path.exists(self.base_dir) is False:
            os.mkdir(self.base_dir)

    def remove_base_directory(self):
        if len(os.listdir(self.base_dir)) < 1 and TMP_DIRECTORY_NAME in self.base_dir:
            # Remove directory after finishing
            os.rmdir(self.base_dir)

    def remove_tmp_files(self):
        if os.path.exists(self.tmp_after_fixing_geometries) is True:
            os.remove(self.tmp_after_fixing_geometries)
        if os.path.exists(self.tmp_after_vclean) is True:
            os.remove(self.tmp_after_vclean)

    def run(self):
        try:
            # By default - use intermediate layers
            answer = self._run_ranking(use_intermediate_layers=True)
            self.remove_tmp_files()
            self.remove_base_directory()
            return answer
        except Exception as ex:
            self.logText = 'Errors occurred. Re-run algorithm without saving intermediate layers'
            try:
                self.remove_tmp_files()
                self.remove_base_directory()
            except Exception as ex:
                pass

            answer = self._run_ranking(use_intermediate_layers=False)
            return answer

    def _fix_geometries_and_v_clean_with_temporary_files(self):
        self.logText = 'Fixing geometries'
        if os.path.exists(self.tmp_after_fixing_geometries) is True:
            os.remove(self.tmp_after_fixing_geometries)
        vl = fix_geometries(self.selectedLayer,
                            self.tmp_after_fixing_geometries)
        if self.isCanceled():
            return None, None
        else:
            if self.cleanTresholdValue.replace(' ', '') != '':
                self.setProgress(5)
                self.logText = 'Filling gaps (v.clean)'
                try:
                    cleaned_layer_path = clean_gaps(vl, self.cleanTresholdValue,
                                                    self.tmp_after_vclean)
                    cleaned_layer = QgsVectorLayer(cleaned_layer_path,
                                                   'v_clean')
                except Exception:
                    self.error_reason = 'grass'
                    self.logText = ''
                    return None, None
            else:
                vl = QgsVectorLayer(vl, 'fix')
                pr = vl.dataProvider()
                pr.addAttributes([QgsField("fid", QVariant.Int)])
                vl.updateFields()
                cleaned_layer = vl

        buffer_layer = createCleanedBuffer(cleaned_layer)
        buffer_layer.setProviderEncoding(u'UTF-8')
        buffer_layer.dataProvider().setEncoding(u'UTF-8')

        return cleaned_layer, buffer_layer

    def _fix_geometries_and_v_clean_in_memory(self):
        self.logText = 'Fixing geometries. Re-run'
        vl = fix_geometries(self.selectedLayer, 'memory:fixed_geometry')
        if self.isCanceled():
            return None, None
        else:
            if self.cleanTresholdValue.replace(' ', '') != '':
                self.setProgress(5)
                self.logText = 'Filling gaps (v.clean). Re-run'
                try:
                    cleaned_payer_path = clean_gaps(vl, self.cleanTresholdValue, 'TEMPORARY_OUTPUT')
                    cleaned_layer = QgsVectorLayer(cleaned_payer_path, 'v_clean')
                except Exception:
                    self.error_reason = 'grass'
                    self.logText = ''
                    return None, None
            else:
                pr = vl.dataProvider()
                pr.addAttributes([QgsField("fid", QVariant.Int)])
                vl.updateFields()
                cleaned_layer = vl
        buffer_layer = createCleanedBuffer(cleaned_layer)
        buffer_layer.setProviderEncoding(u'UTF-8')
        buffer_layer.dataProvider().setEncoding(u'UTF-8')

        return cleaned_layer, buffer_layer

    def _run_ranking(self, use_intermediate_layers: bool = False):
        self.create_base_directory_if_required()
        response = False
        cleaned_layer = None
        try:
            if use_intermediate_layers is True:
                cleaned_layer, buffer_layer = self._fix_geometries_and_v_clean_with_temporary_files()
            else:
                # All layers will be processed in memory
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
                QgsVectorFileWriter.writeAsVectorFormatV2(clip_output[1], self.attributes_file_path,
                                                          QgsCoordinateTransformContext(),
                                                          options)

            if self.isCanceled():
                return False
            else:
                clipped_vector_layer.startEditing()
                self.setProgress(25)
                self.logText = 'Creating "fid" attributes'
                all_f = clipped_vector_layer.featureCount()
                for feature in clipped_vector_layer.getFeatures():
                    progress = 25 + (int(feature.id())*10) / all_f

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
                QgsVectorFileWriter.writeAsVectorFormatV2(clipped_vector_layer,
                                                          self.original_file_path,
                                                          QgsCoordinateTransformContext(),
                                                          options)

            if self.isCanceled():
                return False
            else:
                intersect_point_layer = get_lines_intersections(clipped_vector_layer,
                                                                self.setProgress)
            if self.isCanceled():
                return False
            else:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "CSV"
                options.fileEncoding = "utf-8"
                QgsVectorFileWriter.writeAsVectorFormatV2(intersect_point_layer,
                                                          self.points_file_path,
                                                          QgsCoordinateTransformContext(),
                                                          options)

            if self.isCanceled():
                return False
            else:
                self.setProgress(47)
                self.logText = 'Get nearest segment id'
                start_segment_id = get_nearest_segmentId(clipped_vector_layer,
                                                         self.pt, self.setProgress)
            if self.isCanceled():
                return False
            else:
                self.setProgress(58)
                self.logText = 'Graph traversal ranking'
                out_dataset = overall_call(self.original_file_path,
                                           self.points_file_path,
                                           start_segment_id,
                                           self.attributes_file_path,
                                           self.setProgress)

                os.remove(self.points_file_path)
                os.remove(self.original_file_path)
                os.remove(self.attributes_file_path)
                clipped_vector_layer.selectAll()
                outLayer = processing.run("native:saveselectedfeatures",
                                          {'INPUT': clipped_vector_layer, 'OUTPUT': 'memory:rank_output'})['OUTPUT']
            if self.isCanceled():
                return False
            else:
                self.setProgress(89)
                self.logText = 'Creating attributes table'
                pr = outLayer.dataProvider()
                for field_name in self.fields_names:
                    pr.addAttributes([QgsField(field_name,  QVariant.Int)])
                outLayer.updateFields()
                outLayer.startEditing()

                all_f = outLayer.featureCount()
                for feature in outLayer.getFeatures():
                    progress = 89 + (int(feature.id())*10)/all_f
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
                    except Exception as e:
                        outLayer.deleteFeature(feature.id())

                outLayer.commitChanges()
                createSpatialIndex(outLayer)
                outLayerWithAttr = joinAttributes(outLayer, buffer_layer, self.fields_names)
                outLayerWithAttr.setProviderEncoding(u'UTF-8')
                outLayerWithAttr.dataProvider().setEncoding(u'UTF-8')

            if self.isCanceled():
                return False
            else:
                if self.outLineEdit.replace(' ', '') != '':
                    if self.outLineEdit[-5:] != '.gpkg':
                        self.outLineEdit = self.outLineEdit + '.gpkg'
                    try:
                        QgsVectorFileWriter.writeAsVectorFormat(layer=outLayerWithAttr,
                                                                fileName=self.outLineEdit,
                                                                fileEncoding="utf-8",
                                                                driverName="GPKG")
                        self.result = QgsVectorLayer(self.outLineEdit, self.outLineEdit.split('/')[-1][:-5], "ogr")
                    except Exception as e:
                        pass
                else:
                    self.result = outLayerWithAttr

            if self.isCanceled():
                if use_intermediate_layers is True:
                    del cleaned_layer
                    self.remove_tmp_files()
                    self.remove_base_directory()
                return False
            else:
                if use_intermediate_layers is False:
                    del cleaned_layer
                    self.remove_tmp_files()
                    self.remove_base_directory()
                return True
        except Exception as ex:
            del cleaned_layer
            self.remove_tmp_files()
            self.remove_base_directory()
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
                QMessageBox.critical(None, "Error", 'GRASS modules are not available. Activate GRASS or leave snapping threshold empty')
        if result is True:
            QMessageBox.information(None, "Success", 'Lines Ranking process is finished')


class Worker(QObject):
    def __init__(self, qapp, selectedLayer, pt, cleanTresholdValue, outLineEdit, QgsProject, prBar, logTxtLine, fields_names):
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
            # Current value must be integer
            progress = int(round(progress))

        self.progress.setValue(progress)

    def StartScriptTask(self):        
        self.task = StartScript('Lines Ranking processing', QgsTask.CanCancel,
                                 self.selectedLayer, self.pt, self.cleanTresholdValue,
                                 self.outLineEdit, self.QgsProject, self.fields_names)
        self.task.progressChanged.connect(lambda: self.progressSet(self.task.progress(), self.task.logText))
        self.task.taskCompleted.connect(lambda: self.setResult(self.task.result))
        self.qapp.taskManager().addTask(self.task)

    def cancelTask(self):
        self.task.cancel()
        QMessageBox.critical(None, "Terminating", 'Lines Ranking process was canceled')

