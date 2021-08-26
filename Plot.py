# -*- coding: utf-8 -*-
##################################
# Reduction panel
##################################

__authors__ = ["Shun Yu"]
__license__ = "MIT"
__date__ = "23/04/2020"

import logging
import sys
import tempfile
import numpy
import h5py
import os
import fabio
import pyFAI
#import Analysis
import silx
import time
import NewNxdataCurve
import glob
#from pathlib import Path
#from watchdog.observers import Observer
#from watchdog.events import PatternMatchingEventHandler
#from pyFAI.app import calib2

logging.basicConfig()
_logger = logging.getLogger("customHdf5TreeModel")
"""Module logger"""

from silx.gui import qt
from silx.gui import icons
import silx.gui.hdf5
from silx.gui.data.DataViewerFrame import DataViewerFrame
from silx.gui.data.DataViewer import DataViewer, DataViews
#from silx.gui.data import DataViews
from silx.gui.plot.StackView import StackView
from silx.gui.plot.PlotWindow import PlotWindow, Plot1D, Plot2D, ProfileToolBar
from silx.gui.data import NXdataWidgets
from silx.gui.widgets.ThreadPoolPushButton import ThreadPoolPushButton
from silx.gui.hdf5.Hdf5TreeModel import Hdf5TreeModel
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.io.nxdata import save_NXdata
from silx.gui.fit import FitWidget
from silx.gui.hdf5 import Hdf5TreeView
from silx.gui.widgets.TableWidget import TableWidget
from silx.io.utils import save1D
  
'''
class plot_panel(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.stackview = Plot1D()
        #self.stackview.setDisplayMode(DataViews.NXDATA_CURVE_MODE)
        #self.stackview.addTabbedDockWidget(self.stackview.getLegendsDockWidget())
        #self.plot1D = Plot1D()
        #toolbar = ProfileToolBar(plot=self.stackview, profileWindow=self.plot1D)
        #self.stackview.addToolBar(toolbar)
        layout = qt.QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.stackview)
        #layout.addWidget(self.plot1D)
        #self.AxesSelector = NumpyAxesSelector()
        #self.AxesSelector.setNamedAxesSelectorVisibility(True)
        #self.AxesSelector.show()
    def creatwidget(self, selected):
        if  self.stackview is not None:
            pass

    
    def setdata(self, selected):
        #print(selected.ntype)
        self.stackview.clear()
        data = numpy.array(selected)
        if data.shape[1] == 1:
            sequence = 0
            for curve in data:
                self.stackview.addCurve(selected.local_file['entry/scale/q_1d'], curve[0,:], legend=str(sequence))
                sequence += 1
        else:
            pass
        #if isinstance(selected, h5py.Dataset):
        #    print("pass")
    
    def setdata(self, stack, parameter):
        if stack.shape[1] == 1:
            sequence = 0
            for curve in stack:
                #print (curve[0,:])
                self.stackview.addCurve(parameter, curve[0,:], legend=str(sequence))
                sequence += 1
'''
        #if stack.shape[1] == 1:
        #    self.stackview.setLabels(labels=['Frame Number','', 'Q [nm-1]'])
        #else:
        #    self.stackview.setLabels(labels=['Frame Number', 'Azimuthal Angle', 'Q [nm-1]'])
                

class Plot(qt.QWidget):
    def __init__(self):
        super().__init__()

        self.databrowser = silx.gui.hdf5.Hdf5TreeView(self)
        self.databrowser.setSortingEnabled(True)
        self.databrowser.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)

        self.__savingpath = os.path.abspath('processed data/')

        self.file_layout= qt.QGroupBox("File handling")
        self.file_layout.setLayout(qt.QHBoxLayout())
        self.refresh = qt.QPushButton("Refresh")
        self.refresh.setIcon(icons.getQIcon('view-refresh'))
        self.refresh.clicked.connect(lambda: self.refresh_file())
        self.file_layout.layout().addWidget(self.refresh)
        self.loadfile = qt.QPushButton("Load")
        self.loadfile.setIcon(icons.getQIcon('document-open'))
        self.loadfile.clicked.connect(self.Load_file)
        self.file_layout.layout().addWidget(self.loadfile)
        self.deletefile = qt.QPushButton("Remove")
        self.deletefile.setIcon(icons.getQIcon('remove'))
        self.deletefile.clicked.connect(lambda: self.delete_file(self.databrowser.selectedH5Nodes()))
        self.file_layout.layout().addWidget(self.deletefile)
        self.clearview = qt.QPushButton("Clear")
        self.clearview.setIcon(icons.getQIcon('close'))
        self.clearview.clicked.connect(self.clear_view)
        self.file_layout.layout().addWidget(self.clearview)
        self.savefile = qt.QPushButton("Save As")
        self.savefile.setIcon(icons.getQIcon('document-save'))
        self.savefile.clicked.connect(self.save_file)
        self.file_layout.layout().addWidget(self.savefile)
        

        dataplotpara = qt.QGroupBox("Plotting selection")
        #dataplotpara.setCheckable(True)
        dataplotpara.setLayout(qt.QGridLayout())

        self.q_azi_selection = qt.QButtonGroup()
        self.q_plot = qt.QRadioButton("Q Plot")
        self.q_plot.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.q_plot.setChecked(True)
        self.q_azi_selection.addButton(self.q_plot, 1)
        dataplotpara.layout().addWidget(self.q_plot, 0, 0, 1, 1)
        self.azi_plot = qt.QRadioButton("Azimuthal Plot")
        self.azi_plot.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.q_azi_selection.addButton(self.azi_plot, 2)
        dataplotpara.layout().addWidget(self.azi_plot, 0, 2, 1, 1)

        L_q_start = qt.QLabel(r"Q<sub>low</sub> (nm<sup>-1</sup>)")
        L_q_start.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #q_azi_start.setMaximumWidth(80)
        dataplotpara.layout().addWidget(L_q_start, 1, 0, 1, 1)
        L_q_end = qt.QLabel(r"Q<sub>high</sub> (nm<sup>-1</sup>)")
        L_q_end.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #q_azi_end.setMaximumWidth(80)
        dataplotpara.layout().addWidget(L_q_end, 1, 1, 1, 1)

        self.q_low = qt.QLineEdit("0.1000")
        self.q_low.setValidator(qt.QDoubleValidator(0.0001, 50.0000, 4))
        dataplotpara.layout().addWidget(self.q_low, 2, 0, 1, 1)
        self.q_high = qt.QLineEdit("0.5000")
        self.q_high.setValidator(qt.QDoubleValidator(0.0001, 50.0000, 4))
        dataplotpara.layout().addWidget(self.q_high, 2, 1, 1, 1)
        #self.q_azi_step = qt.QLineEdit("1")
        #dataplotpara.layout().addWidget(self.q_azi_step, 2, 2, 1, 1)

        L_azi_start = qt.QLabel("\u03c6<sub>start</sub> (\xB0)")
        L_azi_start.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #q_azi_start.setMaximumWidth(80)
        dataplotpara.layout().addWidget(L_azi_start, 1, 2, 1, 1)
        L_azi_end = qt.QLabel("\u03c6<sub>stop</sub> (\xB0)")
        L_azi_end.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #q_azi_end.setMaximumWidth(80)
        dataplotpara.layout().addWidget(L_azi_end, 1, 3, 1, 1)

        self.azi_start = qt.QLineEdit("-180.0")
        self.azi_start.setValidator(qt.QDoubleValidator(-361.0000, 361.0000, 4))
        dataplotpara.layout().addWidget(self.azi_start, 2, 2, 1, 1)
        self.azi_stop = qt.QLineEdit("180.0")
        self.azi_stop.setValidator(qt.QDoubleValidator(-361.0000, 361.0000, 4))
        dataplotpara.layout().addWidget(self.azi_stop, 2, 3, 1, 1)

        self.plot_selection = qt.QButtonGroup()
        self.sin_plot = qt.QRadioButton("Single Plot")
        self.sin_plot.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.sin_plot.setChecked(True)
        self.plot_selection.addButton(self.sin_plot, 1)
        dataplotpara.layout().addWidget(self.sin_plot, 3, 0, 1, 1)
        self.mult_plot= qt.QRadioButton("Multiple Plot")
        self.mult_plot.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.plot_selection.addButton(self.mult_plot, 2)
        dataplotpara.layout().addWidget(self.mult_plot, 3, 1, 1, 1)
        self.waterfall_plot = qt.QRadioButton("Waterfall (Log)")
        self.waterfall_plot.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.plot_selection.addButton(self.waterfall_plot, 3)
        dataplotpara.layout().addWidget(self.waterfall_plot, 3, 2, 1, 1)
        self.waterfall_linear = qt.QRadioButton("Waterfall (Linear)")
        self.waterfall_linear.setStyleSheet('QRadioButton{font: Bold 10pt Helvetica MS;}')
        self.plot_selection.addButton(self.waterfall_linear, 3)
        dataplotpara.layout().addWidget(self.waterfall_linear, 3, 3, 1, 1)
        
        z_start = qt.QLabel("Sequence Start (int)")
        z_start.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #z_start.setMaximumWidth(80)
        dataplotpara.layout().addWidget(z_start, 4, 0, 1, 1)
        z_end = qt.QLabel("Sequence End (int)")
        z_end.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #z_end.setMaximumWidth(80)
        dataplotpara.layout().addWidget(z_end, 4, 1, 1, 1)
        z_step = qt.QLabel("Sequence Step (int)")
        z_step.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        #z_step.setMaximumWidth(80)
        dataplotpara.layout().addWidget(z_step, 4, 2, 1, 1)
        z_factor = qt.QLabel("Shift factor (float)")
        z_factor.setFont(qt.QFont("Arial", 9, qt.QFont.Bold))
        dataplotpara.layout().addWidget(z_factor, 4, 3, 1, 1)

        self.seq_start = qt.QLineEdit("0")
        self.seq_start.setValidator(qt.QIntValidator())
        dataplotpara.layout().addWidget(self.seq_start, 5, 0, 1, 1)
        self.seq_end = qt.QLineEdit("2")
        self.seq_end.setValidator(qt.QIntValidator())
        dataplotpara.layout().addWidget(self.seq_end, 5, 1, 1, 1)
        self.seq_step = qt.QLineEdit("1")
        self.seq_step.setValidator(qt.QIntValidator())
        dataplotpara.layout().addWidget(self.seq_step, 5, 2, 1, 1)
        self.seq_factor = qt.QLineEdit("1.5")
        self.seq_step.setValidator(qt.QDoubleValidator(0.0001, 50.0000, 4))
        dataplotpara.layout().addWidget(self.seq_factor, 5, 3, 1, 1)    

        dataselect = qt.QSplitter(qt.Qt.Vertical)
        dataselect.addWidget(self.file_layout)
        dataselect.addWidget(self.databrowser)
        dataselect.addWidget(dataplotpara)
        #dataselect.addWidget(self.datatable)
        
        #dataselect.setSizes([15, 1])
        dataselect.setStretchFactor(1, 10)

        #self.plotpanel = PlotWindow()
        self.plot_tabmenu = qt.QTabWidget()
        self.plotpanel = NewNxdataCurve.ArrayCurvePlot()
        self.plotpanel2d = NewNxdataCurve.ArrayImagePlot()
        self.plot_tabmenu.addTab(self.plotpanel, "1D plot")
        self.plot_tabmenu.addTab(self.plotpanel2d, "2D Plot")
        #self.plotpanel = NewNxdataCurve.ArrayImagePlot()
        #self.plotpanel = plot_panel()


        #datadisplay = qt.QSplitter(qt.Qt.Vertical)
        #datadisplay.addWidget(self.plotpanel)

        #self.Analysis_panel = Analysis.Analysis()

        layout = qt.QHBoxLayout()
        layout.addWidget(dataselect, 5)
        layout.addWidget(self.plot_tabmenu, 10)
        #layout.addWidget(self.plotpanel,10)
        #layout.addWidget(datadisplay, 6)
        #layout.addWidget(self.Analysis_panel, 4)

        self.databrowser.activated.connect(self.plot_data)
        #layout.setStretchFactor()
        

        self.setLayout(layout)

    def Path_set(self, path):
        self.__savingpath = path
        #for name in names[0]:
        #    self.__treeview.findHdf5TreeModel().appendFile(name)
    
   
    def plot_data(self):
        """Called to update the dataviewer with the selected data.
        """
        selected = list(self.databrowser.selectedH5Nodes())
        #h5 = selected.h5py_object
        #print(selected[0])
        if len(selected) == 1:
            #print(selected[0].ntype)
            # Update the viewer for a single selection
            if self.plot_tabmenu.currentWidget() is self.plotpanel:
                print("1D panel is active")
                title = os.path.basename(selected[0].local_filename[:-3])
                
                data = selected[0].h5py_object
                #print(q_1d)
                #print(data.shape[1])
                # data is a hdf5.H5Node object
                # data.h5py_object is a Group/Dataset object (from h5py, spech5, fabioh5)
                # The dataviewer can display both

                head_tail = os.path.split(selected[0].data_url.data_path())
                print(head_tail[0])

                try:
                    q_1d = selected[0].local_file[head_tail[0]+'/q'][:]
                except:
                    q_1d = selected[0].local_file[head_tail[0]+'/q_1d'][:]
                try:
                    azi_1d = selected[0].local_file[head_tail[0]+'/Azimuthal'][:]
                    azi_index_start = (numpy.abs(float(self.azi_start.text())-azi_1d)).argmin()
                    azi_index_stop = (numpy.abs(float(self.azi_stop.text())-azi_1d)).argmin()
                    self.qselector = (azi_index_start, azi_index_stop)
                except:
                    self.qselector = None
                    print("Azimuthal is found found! Pass!")
                    pass
                    #azi_1d = selected[0].local_file[head_tail[0]+'/Azimuthal'][:]
                
                q_index_low = (numpy.abs(float(self.q_low.text())-q_1d)).argmin()
                q_index_high = (numpy.abs(float(self.q_high.text())-q_1d)).argmin()
                
                if data.ndim ==1:
                    self.plotpanel.setCurvesData(data, x=data, xlabel=r"axis", title=title, legend="data", plotmode=1)
                else:
                    if self.q_plot.isChecked():
                        #data = selected[0]
                        #data = numpy.array(selected[0])
                        #if data.ndim == 2:
                        #    data = data.reshape(data.shape[0], 1, data.shape[1])
                    
                        if self.sin_plot.isChecked():
                            print("single plot is checked")
                            self.plotpanel.setCurvesData(data, x=q_1d, xlabel=r"q ($nm^{-1}$)", title=title, legend="data", plotmode=1)
                        elif self.mult_plot.isChecked():
                            print("multiple plot is checked") 
                            self.plotpanel.setCurvesData(data, x=q_1d, xlabel=r"q ($nm^{-1}$)", title=title, legend=title, plotmode=2)
                        elif self.waterfall_plot.isChecked():
                            print("waterfall plot is checked") 
                            self.selector = (int(self.seq_start.text()), int(self.seq_end.text())+1, int(self.seq_step.text()))
                            #self.qselector = (azi_index_start, azi_index_stop)
                            if data.ndim == 2:
                                self.plotpanel.Setwaterfall(data, x=q_1d, xlabel="q ($nm^{-1}$)", title=title, legend=title, 
                                                            selector=self.selector, factor=float(self.seq_factor.text()), plotmode=3)
                            else:
                                self.plotpanel.Setwaterfall(data, x=q_1d, xlabel="q ($nm^{-1}$)", title=title, legend=title, 
                                                            selector=self.selector, qselector=self.qselector, factor=float(self.seq_factor.text()), plotmode=3)
                        elif self.waterfall_linear.isChecked():
                            print("waterfall plot is checked") 
                            self.selector = (int(self.seq_start.text()), int(self.seq_end.text())+1, int(self.seq_step.text()))
                            #self.qselector = (azi_index_start, azi_index_stop)
                            if data.ndim == 2: 
                                self.plotpanel.Setwaterfall(data, x=q_1d, xlabel="q ($nm^{-1}$)", title=title, legend=title, 
                                                            selector=self.selector, factor=float(self.seq_factor.text()), plotmode=4)
                            else:
                                self.plotpanel.Setwaterfall(data, x=q_1d, xlabel="q ($nm^{-1}$)", title=title, legend=title, 
                                                            selector=self.selector, qselector=self.qselector, factor=float(self.seq_factor.text()), plotmode=4)
                    elif self.azi_plot.isChecked():
                        data = numpy.moveaxis(numpy.array(selected[0]), -1, 1)
                        try:
                            #azi_1d = selected[0].local_file['entry/scale/Azimuthal']
                            azi_1d = selected[0].local_file[head_tail[0]+'/Azimuthal']
                        except:
                            #azi_1d = selected[0].local_file['entry/data/2D_data/Azimuthal'][:]
                            azi_1d = len(data)
                        if self.sin_plot.isChecked():
                            print("single plot is checked")
                            self.aziselector = (q_index_low, q_index_high)
                            self.plotpanel.setCurvesData(data, x=azi_1d, xlabel=r"Azimuthal", aziselector=self.aziselector, title=title, legend="data", plotmode=1)
                        elif self.mult_plot.isChecked():
                            print("multiple plot is checked") 
                            self.aziselector = (q_index_low, q_index_high)
                            self.plotpanel.setCurvesData(data, x=azi_1d, xlabel=r"Azimuthal", aziselector=self.aziselector, title=title, legend=title, plotmode=2)
                        elif self.waterfall_plot.isChecked():
                            print("waterfall plot is checked") 
                            self.selector = (int(self.seq_start.text()), int(self.seq_end.text())+1, int(self.seq_step.text()))
                            self.aziselector = (q_index_low, q_index_high)
                            self.plotpanel.Setwaterfall(data, x=azi_1d, xlabel=r"Azimuthal", title=title, legend=title, 
                                                            selector=self.selector, aziselector=self.aziselector, factor=float(self.seq_factor.text()), plotmode=3)
                        elif self.waterfall_linear.isChecked():
                            print("waterfall plot is checked") 
                            self.selector = (int(self.seq_start.text()), int(self.seq_end.text())+1, int(self.seq_step.text()))
                            self.aziselector = (q_index_low, q_index_high)
                            self.plotpanel.Setwaterfall(data, x=azi_1d, xlabel=r"Azimuthal", title=title, legend=title, 
                                                            selector=self.selector, aziselector=self.aziselector, factor=float(self.seq_factor.text()), plotmode=4)                           
            else:
                print("2D panel is active")  
                
                head_tail = os.path.split(selected[0].data_url.data_path())
                print(head_tail[0])

                try:
                    q_1d = selected[0].local_file[head_tail[0]+'/q'][:]
                except:
                    q_1d = selected[0].local_file[head_tail[0]+'/q_1d'][:]
                
                try:
                    azi_angle = selected[0].local_file[head_tail[0]+'/Azimuthal'][:]
                except:
                    azi_angle = []
                    print("azi_angle is not found")
                    pass
                
                title = os.path.basename(selected[0].local_filename[:-3])
                
                data = selected[0].h5py_object

                if azi_angle == []:
                    if data.ndim == 2:
                        data = numpy.array(data)
                        data = data.reshape((1, data.shape[0], data.shape[1]))
                        self.plotpanel2d.setImageData(data, x_axis=q_1d, y_axis=None, signals_names=["Dynamics"], xlabel="q ($nm^{-1}$)", ylabel="Frame Number")
                    elif data.ndim >= 3:
                        #data = data.reshape((1, data.shape[0], data.shape[1]))
                        self.plotpanel2d.setImageData(data, x_axis=q_1d, y_axis=None, signals_names=range(len(data)), xlabel="q ($nm^{-1}$)", ylabel="Frame Number")
                else:
                    if data.ndim == 2:
                        data = numpy.array(data)
                        data = data.reshape((1, data.shape[0], data.shape[1]))
                        self.plotpanel2d.setImageData(data, x_axis=q_1d, y_axis=azi_angle, signals_names=["Dynamics"], xlabel="q ($nm^{-1}$)", ylabel="Frame Number")
                    elif data.ndim >=3:
                        self.plotpanel2d.setImageData(data, x_axis=q_1d, y_axis=azi_angle, signals_names=range(len(data)), xlabel="q ($nm^{-1}$)", ylabel="Azimuthal angle")
                  
            #self.__dataViewer2.addImage(data)
        #else:
        #    for sig in selected:
        #        data = numpy.array(sig[0])
        #        title = os.path.basename(sig[0].local_filename[:-3])
        #        q_1d = sig[0].local_file['entry/scale/q_1d']
        #        self.plotpanel.setCurvesData(data, x=q_1d, xlabel=r"q\(nm^{-1}\)", legend=title)


    def Load_file(self):
        files = qt.QFileDialog.getOpenFileNames(self, 'Choose Mask')
        
        if files != ('', ''):
            for name in files[0]:
                self.databrowser.findHdf5TreeModel().appendFile(name)

    def refresh_file(self):
        #files = qt.QFileDialog.getOpenFileNames(self, 'Choose Mask')
        #for file in self.file_layout
        self.databrowser.findHdf5TreeModel().clear()
        path = self.__savingpath + "/**/*AI*.h5"
        print(path)
        for files in glob.glob(path, recursive=True):
            self.databrowser.findHdf5TreeModel().appendFile(files)
        
    def save_file(self):
        
        selected = list(self.databrowser.selectedH5Nodes())

        if len(selected) == 1:
            try:
                head_tail = os.path.split(selected[0].data_url.data_path())
                print(head_tail[0])

                data = selected[0].h5py_object

                try:
                    q_1d = selected[0].local_file[head_tail[0]+'/q'][:]
                    print("q_1d found")
                except:
                    q_1d = numpy.arange(data.shape[-1])
                    print("q_1d assgined")
                try:
                    azi_angle = selected[0].local_file[head_tail[0]+'/Azimuthal'][:]
                    print("azi_angle found")
                except:
                    azi_angle = numpy.arange(data.shape[-2])
                    print("azi_angle assgined")

                name = qt.QFileDialog.getSaveFileName(self, 'Save As', self.__savingpath, "txt files (*.txt)")
                #print(obj.h5py_object)

                if name != ('', ''):
                    print(name[0])
                    if data.ndim <= 2:
                        print(data.ndim)
                        save1D(name[0], q_1d, data, xlabel="q", comments="#{}".format(azi_angle), header="Data exported from {}\n".format(selected[0].local_filename))
                        print("file is saved as {}".format(name[0]))
                    else:
                        print("{} is larger than 2".format(data.ndim))
                        ind = numpy.indices(data.shape[:-2])
                        ind_list = numpy.ravel_multi_index(ind, data.shape[:-2])
                        #for counter, subdata in data[...,:,:,:]:
                        for frame, counter in numpy.ndenumerate(ind_list):
                            subname = os.path.splitext(name[0])[0] + "_{}.txt".format(counter)
                            save1D(subname, q_1d, data[frame], xlabel="q", comments="#{}".format(azi_angle), header="Data frame at {}\nexported from {}\n".format(frame, selected[0].local_filename))
                            print("file is saved as {}".format(subname))
            except:
                print("file is not saved!")




    def delete_file(self, selectedObjects):
        #selectedObjects = event.source().selectedH5Nodes()
        #menu = event.menu()

        #if not menu.isEmpty():
        #    menu.addSeparator()
        
        for obj in selectedObjects:
            if obj.ntype is h5py.File:
                print("yes, it is h5py.file")
                #print(obj.h5py_object)
                self.databrowser.findHdf5TreeModel().removeH5pyObject(obj.h5py_object)
            else:
                print("no, it is not selected properly")
                self.databrowser.findHdf5TreeModel().removeH5pyObject(obj.local_file)
            #action = qt.QAction("Remove %s" % obj.local_filename, event.source())
            #action.triggered.connect(lambda: self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.local_file))
            #menu.addAction(action)
    
    def clear_view(self):
        self.databrowser.findHdf5TreeModel().clear()