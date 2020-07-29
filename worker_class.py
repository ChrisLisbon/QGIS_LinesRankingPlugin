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
import os
from qgis.core import *
from .preparation import *
from .graph_processing import overall_call
import processing

class StartScript(QgsTask):
    def __init__(self, desc, flags, selectedLayer, pt, cleanTresholdValue, outLineEdit, QgsProject, fields_names):
        QgsTask.__init__(self, desc, flags)
        self.selectedLayer=selectedLayer
        self.pt=pt
        self.cleanTresholdValue=cleanTresholdValue
        self.outLineEdit=outLineEdit
        self.QgsProject=QgsProject
        self.result=None
        self.logText=''
        self.fields_names=fields_names
        self.error_reason=''
    
    def run(self):
        self.logText='Fixing feometries'
        vl=fix_geometries(self.selectedLayer)
        if self.isCanceled():
            return False
        else:
            if self.cleanTresholdValue.replace(' ', '')!='':
                self.setProgress(5)
                self.logText='Filling gaps (v.clean)'  
                try:         
                    cleanedLayerPath=clean_gaps(vl, self.cleanTresholdValue) 
                    cleanedLayer=QgsVectorLayer(cleanedLayerPath, 'v_clean')
                except Exception:
                    self.error_reason='grass'                      
                    self.logText=''
                    return False      
            else:
                pr = vl.dataProvider() 
                pr.addAttributes([QgsField("fid",  QVariant.Int)])
                vl.updateFields()                    
                cleanedLayer=vl
        buffer_layer=createCleanedBuffer(cleanedLayer)
        buffer_layer.setProviderEncoding(u'UTF-8')
        buffer_layer.dataProvider().setEncoding(u'UTF-8')

        if self.isCanceled():
            return False
        else:
            self.setProgress(15)
            self.logText='Clear attribute fields'
            cleanedLayer.startEditing()
            count = 0
            del_list=[]
            for field in cleanedLayer.dataProvider().fields():
                if field.name() != 'fid':
                    del_list.append(count)                        
                count+=1 
            cleanedLayer.dataProvider().deleteAttributes(del_list)
            cleanedLayer.updateFields()               
            cleanedLayer.commitChanges()
        if self.isCanceled():
            return False
        else:
            self.setProgress(20)
            self.logText='Create lines segments'
            clipOutput=clip_line_to_segment(cleanedLayer)
            clipedVectorLayer=clipOutput[0]
        if self.isCanceled():
            return False
        else:
            self.attributes_file_path=os.path.join(os.getcwd(), 'attributes_temp.csv')
            QgsVectorFileWriter.writeAsVectorFormat(layer=clipOutput[1], 
                                                    fileName=self.attributes_file_path, 
                                                    fileEncoding="utf-8", 
                                                    driverName="CSV")
        if self.isCanceled():
            return False
        else:    
            clipedVectorLayer.startEditing()               
            self.setProgress(25)
            self.logText='Creatng "fid" attributes'
            all_f=clipedVectorLayer.featureCount()    
            for feature in clipedVectorLayer.getFeatures():
                progress=25+(int(feature.id())*10)/all_f 
                self.setProgress(progress)               
                if self.isCanceled():
                    break
                    return False
                else:
                    geom=feature.geometry()
                    if feature.geometry().wkbType()==0:
                        clipedVectorLayer.deleteFeature(feature.id())
                    else:
                        feature['fid']=feature.id()
                        clipedVectorLayer.updateFeature(feature)                
            clipedVectorLayer.commitChanges()
            
            self.setProgress(36)
            self.logText='Calculating lines intersections'        
        if self.isCanceled():
            return False
        else:
            self.original_file_path=os.path.join(os.getcwd(), 'original_temp.csv')
            QgsVectorFileWriter.writeAsVectorFormat(layer=clipedVectorLayer, 
                                                    fileName=self.original_file_path, 
                                                    fileEncoding="utf-8", 
                                                    driverName="CSV")                        
        if self.isCanceled():
            return False
        else:
            intersectPointLayer=get_lines_intersections(clipedVectorLayer, self.setProgress)
        if self.isCanceled():
            return False
        else:
            self.points_file_path=os.path.join(os.getcwd(), 'pionts_temp.csv')
            QgsVectorFileWriter.writeAsVectorFormat(layer=intersectPointLayer, 
                                                    fileName=self.points_file_path, 
                                                    fileEncoding="utf-8", 
                                                    driverName="CSV")                   
        if self.isCanceled():
            return False
        else: 
            self.setProgress(47)
            self.logText='Get nearest segment id'   
            start_segment_id=get_nearest_segmentId(clipedVectorLayer, self.pt, self.setProgress)
        if self.isCanceled():
            return False
        else:
            self.setProgress(58)
            self.logText='Graph traversal ranking'
            out_dataset=overall_call(self.original_file_path, self.points_file_path, start_segment_id, self.attributes_file_path, self.setProgress)
            os.remove(self.points_file_path)
            os.remove(self.original_file_path)
            os.remove(self.attributes_file_path)
            clipedVectorLayer.selectAll()
            outLayer = processing.run("native:saveselectedfeatures", {'INPUT': clipedVectorLayer, 'OUTPUT': 'memory:rank_output'})['OUTPUT']
        if self.isCanceled():
            return False
        else:
            self.setProgress(89)
            self.logText='Creating attributes table'
            pr = outLayer.dataProvider() 
            for field_name in self.fields_names:  
                pr.addAttributes([QgsField(field_name,  QVariant.Int)]) 
            outLayer.updateFields()
            outLayer.startEditing()

            all_f=outLayer.featureCount()
            for feature in outLayer.getFeatures():
                progress=89+(int(feature.id())*10)/all_f 
                self.setProgress(progress)
                try:
                    if self.isCanceled():
                        break
                        return False
                    else:
                        f_id=feature['fid']                   
                        rank=out_dataset[f_id][0]
                        value=out_dataset[f_id][1]
                        distance=out_dataset[f_id][2]
                        try:
                            feature[self.fields_names[0]]=rank
                        except Exception:
                            pass
                        try:
                            feature[self.fields_names[1]]=value
                        except Exception:
                            pass
                        try:
                            feature[self.fields_names[2]]=distance
                        except Exception:
                            pass

                        outLayer.updateFeature(feature)
                except Exception as e:
                    outLayer.deleteFeature(feature.id())
                    pass
            outLayer.commitChanges()
            createSpatialIndex(outLayer)
            outLayerWithAttr=joinAttributes(outLayer, buffer_layer, self.fields_names)            
            outLayerWithAttr.setProviderEncoding(u'UTF-8')
            outLayerWithAttr.dataProvider().setEncoding(u'UTF-8')

        if self.isCanceled():
            return False
        else:
            if self.outLineEdit.replace(' ', '')!='':
                if self.outLineEdit[-5:]!='.gpkg':
                    self.outLineEdit=self.outLineEdit+'.gpkg'
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
            return False
        else:
            return True

        def cancel(self):
            super().cancel()

    def finished(self, result):
        self.setProgress(0)
        self.logText=''
        if result is False:
            try:
                os.remove(self.points_file_path)
                os.remove(self.original_file_path)
                os.remove(self.attributes_file_path)
            except Exception:
                pass
            if self.error_reason=='grass':
                QMessageBox.critical(None, "Error", 'GRASS pakage is not accessible')
        if result is True:
            QMessageBox.information(None, "Success", 'Lines Ranking process is finished')

class Worker(QObject):
    def __init__(self, qapp, selectedLayer, pt, cleanTresholdValue, outLineEdit, QgsProject, prBar, logTxtLine, fields_names):
        self.qapp=qapp
        self.selectedLayer=selectedLayer
        self.pt=pt
        self.cleanTresholdValue=cleanTresholdValue
        self.outLineEdit=outLineEdit
        self.QgsProject=QgsProject
        self.result=None
        self.progress=prBar
        self.logTxtLine=logTxtLine
        self.fields_names=fields_names

    def setResult(self, r):
        QgsProject.instance().addMapLayer(r)
        self.progress=0
    
    def progressSet(self, progress, logText):
        self.logTxtLine.setText(logText)
        self.progress.setValue(progress)

    def StartScriptTask(self):        
        self.task1 = StartScript('LinesRanking processing', QgsTask.CanCancel, self.selectedLayer, self.pt, self.cleanTresholdValue, self.outLineEdit, self.QgsProject, self.fields_names)
        self.task1.progressChanged.connect(lambda: self.progressSet(self.task1.progress(), self.task1.logText))
        self.task1.taskCompleted.connect(lambda: self.setResult(self.task1.result))
        self.qapp.taskManager().addTask(self.task1)
    def cancelTask(self):
        self.task1.cancel()
        QMessageBox.critical(None, "Treminating", 'Lines Ranking process was canceled')

        

    