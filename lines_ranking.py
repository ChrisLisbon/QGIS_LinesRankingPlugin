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

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant, QUrl, QObject, pyqtSignal, QTimer
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialog, QProgressDialog, QProgressBar
from qgis.core import QgsProject, QgsMapLayer, QgsWkbTypes, Qgis, QgsApplication, QgsFeature, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSpatialIndex, QgsFeatureRequest, QgsPointXY,  QgsTask
from qgis.gui import QgsMapToolEmitPoint

from .lines_ranking_dialog import LinesRankingDialog
import os.path


class LinesRanking:

    def __init__(self, iface):
        self.iface = iface
        self.map_canvas=self.iface.mapCanvas()
        self.tool_clickPoint = QgsMapToolEmitPoint(self.map_canvas)
        self.m=None
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LinesRanking_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.actions = []
        self.menu = self.tr(u'&Lines Ranking')
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('LinesRanking', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/lines_ranking/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Lines Ranking'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr(u'&Lines Ranking'), action)
            self.iface.removeToolBarIcon(action)

######################################################################################
####                        User - Interface communication                         ###
######################################################################################

    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.gpkg')
        self.dlg.lineEdit.setText(filename)

    def select_input_point_file(self):
        filename, _filter = QFileDialog.getOpenFileName(self.dlg, "Select input file ","", '*')
        if filename!='':
            self.dlg.comboBox_2.addItems([filename])
            allItems = [self.dlg.comboBox_2.itemText(i) for i in range(self.dlg.comboBox_2.count())]
            self.dlg.comboBox_2.setCurrentIndex(allItems.index(filename))

    def select_input_lines_file(self):
        filename, _filter = QFileDialog.getOpenFileName(self.dlg, "Select input file ","", '*')
        if filename!='':
            self.dlg.comboBox.addItems([filename])
            allItems = [self.dlg.comboBox.itemText(i) for i in range(self.dlg.comboBox_2.count())]
            self.dlg.comboBox.setCurrentIndex(allItems.index(filename))
    
    def set_point_coordinates(self, point, button):
        coordinates_string=point.asWkt()[6:-2].replace(' ', ',')
        self.dlg.lineEdit_2.setText(coordinates_string)

    def select_point_from_map(self):  
        self.map_canvas.setMapTool(self.tool_clickPoint)  
        self.tool_clickPoint.canvasClicked.connect(self.set_point_coordinates)

    ### Task aborting if "cancel" clicked, dialog closing ###
    def exit_dialog(self):
        if self.m!=None:
            try:
                self.m.cancelTask()
            except Exception:
                pass
            self.m=None
        else:
            self.dlg.close()        

    def get_point_coordinates(self):
        ### Use map canvas for start point set ###
        if self.dlg.radioButton.isChecked():
            try:                
                x=float(self.dlg.lineEdit_2.text().split(',')[0])
                y=float(self.dlg.lineEdit_2.text().split(',')[1])
                pt = QgsPointXY(x, y)
                return pt
            except Exception:
                QMessageBox.critical(None, "Error", 'Invalid start point coordinates')
                return None

        ### Use file for start point set ###        
        if self.dlg.radioButton_2.isChecked():
            try:
                selectedPointLayerIndex = self.dlg.comboBox_2.currentIndex()
                if selectedPointLayerIndex==0:
                    QMessageBox.critical(None, "Error", 'Start point file is invalid')
                    return None
                if selectedPointLayerIndex>len(self.point_layers):
                    vlayer=QgsVectorLayer(self.dlg.comboBox_2.currentText(), self.dlg.comboBox_2.currentText().split('/')[-1].split('.')[0], "ogr")
                if selectedPointLayerIndex<=len(self.point_layers):
                    vlayer=self.point_layers[selectedPointLayerIndex-1].layer()
            except Exception as e:
                QMessageBox.critical(None, "Error", 'Start point file is invalid')
                return None
            
            for feature in vlayer.getFeatures():
                if feature.geometry().wkbType()!=QgsWkbTypes.MultiPoint and feature.geometry().wkbType()!=QgsWkbTypes.Point:
                    QMessageBox.critical(None, "Error", 'Start point file is invalid')
                    return None
            if vlayer.featureCount()!=1:
                QMessageBox.critical(None, "Error", 'Start point file contains multiple points, single needs')
                return None
            for feature in vlayer.getFeatures():
                return feature.geometry().asPoint()
            
    def radio1_clicked(self, enabled):
        if enabled:
            self.dlg.comboBox_2.setDisabled(True)
            self.dlg.pushButton_5.setDisabled(True)
            self.dlg.lineEdit_2.setDisabled(False)
            self.dlg.pushButton_2.setDisabled(False)

    def radio2_clicked(self, enabled):
        if enabled:
            self.dlg.lineEdit_2.setDisabled(True)
            self.dlg.pushButton_2.setDisabled(True)
            self.dlg.comboBox_2.setDisabled(False)
            self.dlg.pushButton_5.setDisabled(False)

    def checkbox_clicked(self):
        if self.dlg.checkBox.isChecked():
            self.dlg.lineEdit_4.setDisabled(False)
            self.dlg.lineEdit_5.setDisabled(False)
            self.dlg.lineEdit_6.setDisabled(False)
            self.dlg.lineEdit_7.setDisabled(False)
        else:
            self.dlg.lineEdit_4.setDisabled(True)
            self.dlg.lineEdit_5.setDisabled(True)
            self.dlg.lineEdit_6.setDisabled(True)
            self.dlg.lineEdit_7.setDisabled(False)

    def link(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))
    
    def run(self):        
        try:
            from .worker_class import Worker
            self.Worker = Worker
        except ModuleNotFoundError:
            QMessageBox.critical(None, "Error", 'Required dependencies are not met. You should install python libraries networkx and pandas, see docs for details.')
            return None

        if self.first_start is True:
            self.first_start = False            
            self.dlg = LinesRankingDialog(self.iface.mainWindow())
            self.dlg.lineEdit.setPlaceholderText("[Save to temporary layer]")
            self.dlg.progressBar.setValue(0)
            self.dlg.comboBox_2.setDisabled(True)
            self.dlg.pushButton_5.setDisabled(True)
            self.dlg.label_8.linkActivated.connect(self.link)
            self.dlg.label_8.setText('<a href="https://github.com/ChrisLisbon/QGIS_LinesRankingPlugin">Source code page</a>')
            self.dlg.pushButton.clicked.connect(self.select_output_file)
            self.dlg.pushButton_2.clicked.connect(self.select_point_from_map)
            self.dlg.pushButton_5.clicked.connect(self.select_input_point_file)
            self.dlg.pushButton_6.clicked.connect(self.select_input_lines_file)
            self.dlg.pushButton_3.clicked.connect(self.add_task)
            self.dlg.pushButton_4.clicked.connect(self.exit_dialog)
            self.dlg.radioButton.toggled.connect(self.radio1_clicked)
            self.dlg.radioButton_2.toggled.connect(self.radio2_clicked)
            self.dlg.checkBox.toggled.connect(self.checkbox_clicked)
            self.dlg.lineEdit_4.setDisabled(True)
            self.dlg.lineEdit_5.setDisabled(True)
            self.dlg.lineEdit_6.setDisabled(True)
            self.dlg.lineEdit_7.setDisabled(True)
            
        layers = QgsProject.instance().layerTreeRoot().children()
        self.filtered_layers=[]
        self.point_layers=[]
        for layer in layers:
            if layer.layer().type()==QgsMapLayer.VectorLayer:
                valid_line=False
                valid_point=False
                for feature in layer.layer().getFeatures():
                    if feature.geometry().wkbType()==QgsWkbTypes.LineString or feature.geometry().wkbType()==QgsWkbTypes.MultiLineString or feature.geometry().wkbType()==QgsWkbTypes.Unknown:
                        valid_line=True
                    if feature.geometry().wkbType()==QgsWkbTypes.Point or feature.geometry().wkbType()==QgsWkbTypes.MultiPoint:
                        valid_point=True
                if valid_line==True:
                    self.filtered_layers.append(layer)
                if valid_point==True:
                    self.point_layers.append(layer)
                    
        self.dlg.comboBox.clear()
        self.dlg.comboBox_2.clear()
        self.dlg.comboBox.addItems([layer.name() for layer in self.filtered_layers])
        self.point_names=['',]
        for layer in self.point_layers:
            self.point_names.append(layer.name())
        self.dlg.comboBox_2.addItems(self.point_names)   
        self.dlg.show()
        result = self.dlg.exec_()
        close=self.dlg.close()
        if close:
            self.first_start = True
            if self.m!=None:
                try:
                    self.m.cancelTask()
                except Exception:
                    pass
                self.m=None

    ### Start processing function ###
    def add_task(self):
        selectedLayer=None
        selectedLayerIndex = self.dlg.comboBox.currentIndex()
        cleanTresholdValue = self.dlg.lineEdit_3.text()
        outLineEdit=self.dlg.lineEdit.text()
        prBar=self.dlg.progressBar
        logTxtLine=self.dlg.label_9
        if selectedLayerIndex<=len(self.filtered_layers)-1:
            selectedLayer = self.filtered_layers[selectedLayerIndex].layer()
        if selectedLayerIndex>len(self.filtered_layers)-1: 
            selectedLayer =  QgsVectorLayer(self.dlg.comboBox.currentText(), self.dlg.comboBox.currentText().split('/')[-1].split('.')[0], "ogr")        
        if selectedLayer!=None:
            selectedLayer.setProviderEncoding(u'UTF-8')
            selectedLayer.dataProvider().setEncoding(u'UTF-8')
            pt = self.get_point_coordinates()
            if self.dlg.checkBox.isChecked():
                fields_names = []
                fields_names.append(self.dlg.lineEdit_4.text().replace(' ', ''))
                fields_names.append(self.dlg.lineEdit_5.text().replace(' ', ''))
                fields_names.append(self.dlg.lineEdit_6.text().replace(' ', ''))
                fields_names.append(self.dlg.lineEdit_7.text().replace(' ', ''))
            else:
                fields_names = ['Rank', 'ValueShreve', 'ValueStrahler', 'Distance']
            if fields_names[0] != '' and fields_names[1] != '' and fields_names[2] != '':
                if pt is not None:
                    ### QgsTask class call ### 
                    self.m = self.Worker(QgsApplication, selectedLayer, pt,
                                         cleanTresholdValue, outLineEdit,
                                         QgsProject, prBar, logTxtLine,
                                         fields_names)
                    self.m.StartScriptTask()            

                
