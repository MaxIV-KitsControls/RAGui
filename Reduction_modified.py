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
from h5py._hl import dataset
import numpy
import h5py
import os
import fabio
import pyFAI
from pyFAI.method_registry import IntegrationMethod
import silx
import glob
import re
from Dataformat import D_format
#from tqdm import tqdm
#from pathlib import Path, PureWindowsPath
#from pyFAI.app import calib2

logging.basicConfig()
_logger = logging.getLogger("customHdf5TreeModel")
"""Module logger"""

from silx.gui import qt
from silx.gui import icons
import silx.gui.hdf5
from silx.gui.data.DataViewerFrame import DataViewerFrame
from silx.gui.data.DataViewer import DataViewer
from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot.PlotWindow import PlotWindow
from silx.gui.widgets.ThreadPoolPushButton import ThreadPoolPushButton
from silx.gui.widgets.WaitingPushButton import WaitingPushButton
from silx.gui.hdf5.Hdf5TreeModel import Hdf5TreeModel
from silx.io.nxdata import save_NXdata
from silx.gui.dialog.ImageFileDialog import ImageFileDialog

detector_file_pattern = re.compile(r'scan_(...)_data*')

class int_para(qt.QWidget):
    def __init__(self):
        super().__init__()
        layout = qt.QGridLayout()
        layout.setColumnStretch(1, 4)
        layout.setColumnStretch(2, 4)

        start = qt.QLabel("Start")
        start.setMaximumWidth(60)
        end = qt.QLabel("End")
        end.setMaximumWidth(60)
        bins = qt.QLabel("Bins")
        bins.setMaximumWidth(60)
        azi = qt.QLabel("Azimuthal")
        azi.setMaximumWidth(60)
        q = qt.QLabel("Q")
        q.setMaximumWidth(60)
        self.azi_start = qt.QLineEdit("-180")
        self.azi_start.setValidator(qt.QIntValidator())
        self.azi_start.setMaximumWidth(60)
        self.azi_end = qt.QLineEdit("180")
        self.azi_end.setValidator(qt.QIntValidator())
        self.azi_end.setMaximumWidth(60)
        self.azi_bins = qt.QLineEdit("360")
        self.azi_bins.setValidator(qt.QIntValidator())
        self.azi_bins.setMaximumWidth(60)
        #self.q_start = qt.QDoubleSpinBox(0.001)
        #self.q_start.setRange(0.0000, 50.0000)
        self.q_start = qt.QLineEdit("0")
        self.q_start.setValidator(qt.QDoubleValidator(0.0001, 50.0000, 4))
        self.q_start.setMaximumWidth(60)
        self.q_end = qt.QLineEdit("inf")
        self.q_end.setValidator(qt.QDoubleValidator(0.1000, 100.0000, 4))
        self.q_end.setMaximumWidth(60)
        self.q_bins = qt.QLineEdit("800")
        self.q_bins.setValidator(qt.QIntValidator())
        self.q_bins.setMaximumWidth(60)
                
        layout.addWidget(start, 1, 0)
        layout.addWidget(end, 2, 0)
        layout.addWidget(bins, 3, 0)
        layout.addWidget(azi, 0, 1)
        layout.addWidget(self.azi_start, 1, 1)
        layout.addWidget(self.azi_end, 2, 1)
        layout.addWidget(self.azi_bins, 3, 1)
        layout.addWidget(q, 0, 2)
        layout.addWidget(self.q_start, 1, 2)
        layout.addWidget(self.q_end, 2, 2)
        layout.addWidget(self.q_bins, 3, 2)

        #self.azi_start = azi_start
        #self.azi_end = azi_end
        #self.azi_bin = azi_bins
        #self.q_start = q_start
        #self.q_end = q_end
        #self.

        self.setLayout(layout)
    
    def get_int_para(self):
        print(self.q_start.text(), self.q_end.text(), self.q_bins.text(), self.azi_start.text(), self.azi_end.text(), self.azi_bins.text())

        para = (float(self.q_start.text()), float(self.q_end.text()), int(self.q_bins.text()), float(self.azi_start.text()), float(self.azi_end.text()), int(self.azi_bins.text()))
        
        return para

class Reduction(qt.QWidget):
    """
    This window show an example of use of a Hdf5TreeView.

    The tree is initialized with a list of filenames. A panel allow to play
    with internal property configuration of the widget, and a text screen
    allow to display events.
    """

    def __init__(self, filenames=None):
        """
        :param files_: List of HDF5 or Spec files (pathes or
            :class:`silx.io.spech5.SpecH5` or :class:`h5py.File`
            instances)
        """
        #qt.QMainWindow.__init__(self)
        #self.setWindowTitle("Silx HDF5 Datapipeline")

        #self.statusBar()
        super().__init__()
        self.filenames = filenames
        self.__rawdata_path = os.path.abspath('test data/')

        self.__savingpath = os.path.abspath('processed data/')
        self.background = []
        self.ai = pyFAI.load('calibration file/calib_default.poni')
        self.Data_keys = []
        #self.maskfile = fabio.open('mask files/mask.edf').data
        self.maskfile = []
        self.__asyncload = False
        self.masterfile_list = []

        
        self.__treeview = silx.gui.hdf5.Hdf5TreeView(self)
        self.__treeview.setSortingEnabled(True)
        self.__treeview.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        
        """Silx HDF5 TreeView"""

        self.__sourceModel = self.__treeview.model()
        """Store the source model"""

        #self.__text = qt.QTextEdit(self)
        """Widget displaying information"""

        self.__dataViewer = DataViewerFrame(self)
        self.__dataViewer.setVisible(True)

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
        self.deletefile.clicked.connect(lambda: self.delete_file(self.__treeview.selectedH5Nodes()))
        self.file_layout.layout().addWidget(self.deletefile)
        self.clearview = qt.QPushButton("Clear")
        self.clearview.setIcon(icons.getQIcon('close'))
        self.clearview.clicked.connect(self.clear_view)
        self.file_layout.layout().addWidget(self.clearview)
        
        spliter = qt.QSplitter(qt.Qt.Vertical)
        spliter.addWidget(self.file_layout)
        spliter.addWidget(self.__treeview)
        spliter.setStretchFactor(1, 10)

        layout_dataformat = qt.QGroupBox()
        layout_dataformat.setStyleSheet("QGroupBox {font: bold; background-color: #B0E0E6}")
        layout_dataformat.setLayout(qt.QFormLayout())
        self.filestructure = D_format()
        self.__dataformat = self.filestructure.dataformat
        print(self.__dataformat, "self__dataformt is printed")
        self.filestructure.activated.connect(lambda: self.loaddataformat(self.filestructure))
        #self.filestructure.activated.connect(lambda: self.__dataformat = self.filestructure.onchange())
        layout_dataformat.layout().addRow(qt.QLabel("Data Format"), self.filestructure)

        layout = qt.QHBoxLayout()
        layout.addWidget(spliter, 4)
        layout.addWidget(self.__dataViewer, 6)
        DataReductionlayout = qt.QVBoxLayout()
        DataReductionlayout.addWidget(layout_dataformat, 0)
        DataReductionlayout.addWidget(self.DataReductionConfigurationPanel(self, self.__treeview))
        #layout.addWidget(self.DataReductionConfigurationPanel(self, self.__treeview), 1)
        layout.addLayout(DataReductionlayout)
        
        self.setLayout(layout)
        #main_panel.layout().addStretch(1)

        #self.setCentralWidget(main_panel)

        self.addfile(self.filenames)
        self.__treeview.activated.connect(self.displayData)
        self.__store_lambda = lambda event: self.closeAndSyncCustomContextMenu(event)
        self.__treeview.addContextMenuCallback(self.__store_lambda)

        # append all files to the tree

    def addfile(self, filenames):
        if filenames is not None:
            for file_name in filenames:
                self.__treeview.findHdf5TreeModel().appendFile(file_name)
            #print(file_name)
    
    def DataReductionConfigurationPanel(self, parent, treeview):
        """Create a configuration panel to allow to play with widget states"""
        panel = qt.QWidget(parent)
        panel.setLayout(qt.QVBoxLayout())
        #panel.setStyleSheet("background-color: red")

        DatatypeGB = qt.QGroupBox("Data", panel)
        #Integration.setStyleSheet("QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d4d5d6, stop: 0.8 #e6e6e6, stop: 1 transparent)}")
        DatatypeGB.setStyleSheet("QGroupBox {font: bold; background-color:  #e6e6e6}")
        #DatatypeGB.setCheckable(True)
        #DatatypeGB.setChecked(True)
        DatatypeGB.setLayout(qt.QFormLayout())
        panel.layout().addWidget(DatatypeGB)

        DataType = qt.QComboBox()
        DataType.addItems(["SAXS", "WAXS"])
        DatatypeGB.layout().addRow(qt.QLabel(u"Data Type"), DataType)

        process = qt.QGroupBox("Normalization", panel)
        #process.setStyleSheet("QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d4d5d6, stop: 0.8 #e6e6e6, stop: 1 transparent)}")
        process.setStyleSheet("QGroupBox {font: bold; background-color:  #e6e6e6}")
        process.setCheckable(True)
        process.setChecked(True)
        process.setLayout(qt.QFormLayout())
        panel.layout().addWidget(process)
        
        '''
        FileFormat = qt.QPushButton("Choose")
        FileFormat.clicked.connect(lambda: self.Dataformat(self.__treeview.selectedH5Nodes()))
        process.layout().addRow(qt.QLabel("File Format"), FileFormat)
        '''
        
        Master_file = qt.QPushButton("Choose")
        Master_file.clicked.connect(self.masterfile_load)
        process.layout().addRow(qt.QLabel("Master File"), Master_file)

        Norm_Method = qt.QComboBox()
        Norm_Method.addItems(["All","Aquisition time", "Transmission", "Flux", "Transmittance"])
        process.layout().addRow(qt.QLabel("Methods"), Norm_Method)
        #Dataset = qt.QComboBox()
        #process.layout().addRow(qt.QLabel("Dataset"), Dataset)

        #Norm_value = qt.QComboBox()
        #process.layout().addRow(qt.QLabel("Normalizing Factor"), Norm_value)

        button = WaitingPushButton("Execute")
        button.clicked.connect(lambda: self.Transnormal(self.__treeview.selectedH5Nodes(), DataType.currentText(), method=str(Norm_Method.currentText())))
        process.layout().addRow(qt.QLabel("Nomarlization"), button)

        #process.layout().addStretch(1)

        Background_remove = qt.QGroupBox("Remove Background", panel)
        #Background_remove.setStyleSheet("QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d4d5d6, stop: 0.8 #e6e6e6, stop: 1 transparent)}")
        Background_remove.setStyleSheet("QGroupBox {font: bold; background-color:  #e6e6e6}")
        Background_remove.setCheckable(True)
        Background_remove.setChecked(True)
        BG_layout = qt.QFormLayout()
        #Background_remove.setLayout(qt.QVBoxLayout())
        Background_remove.setLayout(BG_layout)
        panel.layout().addWidget(Background_remove)

        BG_selection = qt.QPushButton("Choose")
        BG_selection.clicked.connect(self.background_open)
        #Background_remove.layout().addWidget(BG_selection)
        BG_layout.addRow(qt.QLabel("Background"), BG_selection)

        #BG_factor = qt.QWidget()
        #BG_factor_layout = qt.QFormLayout()
        BG_factor_input = qt.QLineEdit("1.00")
        #BG_factor_input.setMaxLength(1)
        BG_factor_input.setValidator(qt.QDoubleValidator(0.00, 2.00, 2))
        #BG_factor_input.resize(10, 5)
        BG_layout.addRow(qt.QLabel("Factor"), BG_factor_input)
        #BG_factor.setLayout(BG_factor_layout)
        #Background_remove.layout().addWidget(BG_factor)
        
        subtraction = WaitingPushButton("Execute")
        subtraction.clicked.connect(lambda: self.subtraction(self.__treeview.selectedH5Nodes(), DataType.currentText(), float(BG_factor_input.text())))
        #Background_remove.layout().addWidget(subtraction)
        BG_layout.addRow(qt.QLabel("Remove Background"), subtraction)
        #Background_remove.layout().addStretch(1)
        
        Integration = qt.QGroupBox("Integration", panel)
        #Integration.setStyleSheet("QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d4d5d6, stop: 0.8 #e6e6e6, stop: 1 transparent)}")
        Integration.setStyleSheet("QGroupBox {font: bold; background-color:  #e6e6e6}")
        Integration.setCheckable(True)
        Integration.setChecked(True)
        Integration.setLayout(qt.QFormLayout())
        panel.layout().addWidget(Integration)

        Calibrant_poni = qt.QPushButton("Choose")
        Calibrant_poni.clicked.connect(self.calibration_open)
        Integration.layout().addRow(qt.QLabel(u"Calibration File"), Calibrant_poni)

        Mask_file = qt.QPushButton("Choose")
        Mask_file.clicked.connect(self.Mask_select)
        Integration.layout().addRow(qt.QLabel(u"Mask File"), Mask_file)

        IntegMethods = qt.QComboBox()
        IntegMethods.addItems(["BBox", "numpy", "cython", "splitpixel", "lut", "csr", "lut_ocl"])
        Integration.layout().addRow(qt.QLabel(u"Integration Methods"), IntegMethods)

        Integ_parameter = int_para()
        Integration.layout().addRow(Integ_parameter)

        Integer = WaitingPushButton("Execute")
        Integer.clicked.connect(lambda: self.AIntegrator(self.__treeview.selectedH5Nodes(), DataType.currentText(), IntegMethods.currentText(), Integ_parameter.get_int_para()))
        Integration.layout().addRow(qt.QLabel("2D integration"), Integer)

        combo_button = qt.QGroupBox("Combo")
        combo_button.setStyleSheet("QGroupBox {font: bold; background-color: #eff5d3}")
        combo_button.setLayout(qt.QFormLayout())
        panel.layout().addWidget(combo_button)
        
        File_prefix = qt.QLineEdit("None")
        combo_button.layout().addRow(qt.QLabel("File prefix"), File_prefix)
        
        combination_button = WaitingPushButton("Execute")
        combination_button.clicked.connect(lambda: self.Combineprocess(self.__treeview.selectedH5Nodes(), 
                                                                        normalcheck=process.isChecked(), 
                                                                        normalmethod=Norm_Method.currentText(),
                                                                        subtractioncheck=Background_remove.isChecked(), 
                                                                        datatype=DataType.currentText(),
                                                                        AIntegcheck=Integration.isChecked(),
                                                                        IntegrationMethods=IntegMethods.currentText(),
                                                                        subfactor=float(BG_factor_input.text()),
                                                                        intefactor= Integ_parameter.get_int_para(),
                                                                        file_prefix = File_prefix.text()))
        combo_button.layout().addRow(qt.QLabel("Combined Processing"), combination_button)

        #Integration.layout().addStretch(1)

        self.file_progress = qt.QLabel("The Progress of The Data Processing")
        panel.layout().addWidget(self.file_progress)
        
        self.pro_progress = qt.QProgressBar(self, textVisible=True)
        self.pro_progress.setStyleSheet(
            "QProgressBar {text-align: center; font-size: 12px; border: 1px solid #2196F3; border-radius: 2px;}")
        self.pro_progress.setMaximum(100)
        panel.layout().addWidget(self.pro_progress)
        

        panel.layout().addStretch(1)
        return panel
    
    def File_open(self, names):
        self.__rawdata_path = names
            
        #for name in names[0]:
        #    self.__treeview.findHdf5TreeModel().appendFile(name)
           
    def background_open(self):
        '''
        names = qt.QFileDialog.getOpenFileNames(self, 'Open Background')

        if names != ('',''):
            for name in names[0]:
                with h5py.File(name, 'r') as background:
                    try:
                        self.background = numpy.mean(background[self.__dataformat['saxs_master']], axis=0)
                    except:
                        self.background = numpy.mean(background[self.__dataformat['saxs_det']], axis=0, dtype=numpy.float)
            #self.__treeview.findHdf5TreeModel().appendFile(names[0])
        '''
        names = ImageFileDialog()
        names.exec_()
        self.background = names.selectedImage()
        #url = names.selectedDataUrl()
        #with h5py.File(url.file_path(), mode="r") as h5:
        #    self.background = h5[url.data_path()]

    def calibration_open(self):
        names = qt.QFileDialog.getOpenFileNames(self, 'Open Calibration')

        if names != ('', ''):
            for name in names[0]:
                self.ai = pyFAI.load(name) 
    
    def Mask_select(self):
        mask = qt.QFileDialog.getOpenFileNames(self, 'Choose Mask')

        if mask != ('', ''):
            for name in mask[0]:
                try:
                    self.maskfile = fabio.open(name).data
                    print("the mask file {} is updated!".format(name))
                except:
                    print("the mask file {} in not loaded properly!".format(name))
    
    def Path_set(self, path):
        #saving_path = qt.QFileDialog.getExistingDirectory(self, "set saving path")

        #if saving_path != ('',''):
        self.__savingpath = path

    def loaddataformat(self, obj):
        try:
            self.__dataformat = obj.dataformat
            print(self.__dataformat)
        except:
            print("dataformat is not updated!!")

    def Transnormal(self, event, type, method = None):
        if not self.__savingpath:
            raise Exception("\n Saving path is not defined! \n")
        #selected = len(list(event))
        #print(selected)
        #filecounter = 1
        
        for obj in event:
            h5 = obj.local_file
            norm_filename = os.path.splitext(os.path.basename(obj.local_filename))[0]
            #print("here")
            
            #self.file_progress.setText("Progress of file {}/{}".format(filecounter, selected))
            #print("pass")
            if type == "SAXS":
                try:
                    data = h5[self.__dataformat['saxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['saxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception(u"Data structure in {} is not found".format(self.__dataformat['saxs_master']))
            elif type == "WAXS":
                try:
                    data = h5[self.__dataformat['waxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['waxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception(u"Data structure in {} is not found".format(self.__dataformat['waxs_master']))

            ind = numpy.indices(data.shape[:-2])
            ind_list = numpy.ravel_multi_index(ind, data.shape[:-2])
            n_ind = ind_list.max()+1

            self.pro_progress.setRange(0, n_ind-1)

            if status == "detector_file":

                if self.masterfile_list == []:
                    print("The master file list is empty! \n meta data is set as one")
                    meta = numpy.ones(data.shape[:-2])
                else:
                    #print(self.masterfile_list)
                    masterfile = [s for s in self.masterfile_list if norm_filename[6:-10] in s]
                    #print("{masterfile} is found!")
                    
                    if masterfile:
                        print("find masterfile as {masterfile}")
                        metaentry = h5py.File(masterfile[0], 'r')
                        meta = self.extract_meta(metaentry, method) * numpy.ones(data.shape[:-2])
                    else:
                        print("Meta data is not found, meta is set as one")
                        meta = numpy.ones(data.shape[:-2])

            elif status == "master_file":    
                meta = self.extract_meta(h5, method) * numpy.ones(data.shape[:-2])

            savefilename = self.save_name_check(self.__savingpath, norm_filename, "None", "N")

            try:
                with h5py.File(savefilename, "w") as savefile:
                    savefile.attrs[u"NX_class"] = u"NXroot"

                    nxentry = savefile.create_group(u"entry")
                    nxentry.attrs[u"NX_class"] = u"NXentry"

                    nxnorm = nxentry.create_group(u"data")
                    nxnorm.attrs[u"NX_class"] = u"NXdata"

                    nxdata = nxnorm.create_dataset(u"data", shape = (data.shape), dtype=numpy.float32, shuffle=True)
                    nxdata.attrs[u"NX_class"] = u"NXdata"

                    for frame, counter in numpy.ndenumerate(ind_list):
                        nxdata[frame] = data[frame]/meta[frame]
                        self.pro_progress.setValue(counter)
                print("file is created as: \n {}".format(savefilename))
            except:
                if os.path.exists(savefilename):
                    os.remove(savefilename)
                    print("no file is created!")
            #if filecounter < selected:
            #    filecounter += 1
            del ind, n_ind, data, meta, status, norm_filename, savefilename

    def subtraction(self, selected, type, factor):
        
        if not self.__savingpath:
            raise Exception("\n\nSorry, The saving path is not defined!!!\n\nPlease select the saving path in Setting\n")
        if not isinstance(self.background, numpy.ndarray):
            raise Exception("\n\nPlease select the background first\n")
        for obj in selected:
            h5 = obj.local_file
            norm_filename = os.path.splitext(os.path.basename(obj.local_filename))[0]

            if type == "SAXS":
                try:
                    data = h5[self.__dataformat['saxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['saxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception(u"Data structure in {} is not found".format(self.__dataformat['saxs_master']))
            elif type == "WAXS":
                try:
                    data = h5[self.__dataformat['waxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['waxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception(u"Data structure in {} is not found".format(self.__dataformat['waxs_master']))

            ind = numpy.indices(data.shape[:-2])
            ind_list = numpy.ravel_multi_index(ind, data.shape[:-2])
            n_ind = ind_list.max()+1

            self.pro_progress.setRange(0, n_ind-1)

            savefilename = self.save_name_check(self.__savingpath, norm_filename, "None", "BG")
            try:
                with h5py.File(savefilename, "w") as savefile:
                    savefile.attrs[u"NX_class"] = u"NXroot"

                    nxentry = savefile.create_group(u"entry")
                    nxentry.attrs[u"NX_class"] = u"NXentry"

                    nxnorm = nxentry.create_group(u"data")
                    nxnorm.attrs[u"NX_class"] = u"NXdata"

                    nxdata = nxnorm.create_dataset(u"data", shape = (data.shape), dtype = numpy.float32, shuffle=True)
                    nxdata.attrs[u"NX_class"] = u"NXdata"

                    for frame, counter in numpy.ndenumerate(ind_list):
                        nxdata[frame] = data[frame] - factor * self.background
                        self.pro_progress.setValue(counter)
                print("file is created as: \n {}".format(savefilename))
            except:
                if os.path.exists(savefilename):
                    os.remove(savefilename)
                    print("no file is created!")

            del ind, n_ind, data, norm_filename, savefilename

    def AIntegrator(self, selected, type, methods, factor):
        if not self.__savingpath:
            raise Exception("\n\nSorry, The saving path is not defined!!!\n\nPlease select the saving path in Setting\n")
        if self.ai == []:
            raise Exception("\n\nPlease choose Calibration file first\n")

        for obj in selected:
            h5 = obj.local_file
            norm_filename = os.path.splitext(os.path.basename(obj.local_filename))[0]

            if type == "SAXS":
                try:
                    data = h5[self.__dataformat['saxs_master']]
                except: 
                    try:
                        data = h5[self.__dataformat['saxs_det']]
                    except:
                        raise Exception("Data structure in {} is not found".format(self.__dataformat['saxs_master']))
            elif type == "WAXS":
                try:
                    data = h5[self.__dataformat['waxs_master']]
                except: 
                    try:
                        data = h5[self.__dataformat['waxs_det']]
                    except:
                        raise Exception("Data structure in {} is not found".format(self.__dataformat['waxs_master']))
            #norm = numpy.zeros((factor[5], factor[2]))
            #Int = numpy.zeros(factor[2])
            ind = numpy.indices(data.shape[:-2])
            ind_list = numpy.ravel_multi_index(ind, data.shape[:-2])
            n_ind = ind_list.max()+1

            self.pro_progress.setRange(0, n_ind-1)

            try:
                savefilename = self.save_name_check(self.__savingpath, norm_filename, "None", "AI")
                print("pass name check")

                with h5py.File(savefilename, "w") as savefile:
                    
                    savefile.attrs[u"NX_class"] = u"NXroot"

                    nxentry = savefile.create_group(u"entry")
                    nxentry.attrs[u"NX_class"] = u"NXentry"

                    nxnorm = nxentry.create_group(u"data")
                    nxnorm.attrs[u"NX_class"] = u"NXdata"

                    if type == "SAXS" or type == "WAXS":
                        
                        nxdata2d = nxnorm.create_group(type+u"_2D_data")
                        nxdata2d.attrs[u"NX_class"] = u"NXdata"

                        nxdata1d = nxnorm.create_group(type+u"_1D_data")
                        nxdata1d.attrs[u"NX_class"] = u"NXdata"

                    #nxdata_2d = nxdata2d.create_dataset(u"data", data = numpy.moveaxis(data_2d, -1, 0), shuffle=True)
                    nxdata_2d = nxdata2d.create_dataset(u"data", data.shape[:-2]+(factor[5], factor[2]), dtype = numpy.float32, shuffle=True)
                    nxdata_2d.attrs[u"NX_class"] = u"NXdata"                    

                    #nxdata_1d = nxdata1d.create_dataset(u"data", data = numpy.moveaxis(data_1d, -1, 0), shuffle=True)
                    nxdata_1d = nxdata1d.create_dataset(u"data", data.shape[:-2]+(factor[2],), dtype = numpy.float32, shuffle=True)
                    nxdata_1d.attrs[u"NX_class"] = u"NXdata"

                    if self.maskfile == []:
                        if factor[0] == 0 and factor[1] == numpy.inf: 
                            print("call function 1")
                            for frame, counter in numpy.ndenumerate(ind_list):
                                I2d, q_2d, azi = self.ai.integrate2d(data[frame], factor[2], factor[5], azimuth_range=(factor[3], factor[4]), method=methods, unit="q_nm^-1")
                                q_1d, I_1d = self.ai.integrate1d(data[frame], factor[2], azimuth_range=(factor[3], factor[4]), unit="q_nm^-1")
                                self.pro_progress.setValue(counter)
                                #self.pro_progress.setValue(frame/(len(data)-1)*100)
                                nxdata_2d[frame] = I2d
                                nxdata_1d[frame] = I_1d
                        else:
                            print("call function 2")
                            #for imag in data:
                            for frame, counter in numpy.ndenumerate(ind_list):
                                I2d, q_2d, azi = self.ai.integrate2d(data[frame], factor[2], factor[5], radial_range=(factor[0], factor[1]), method=methods, azimuth_range=(factor[3], factor[4]), unit="q_nm^-1")
                                #norm = numpy.dstack((norm, I2d))
                                q_1d, I_1d = self.ai.integrate1d(data[frame], factor[2], radial_range=(factor[0], factor[1]), azimuth_range=(factor[3], factor[4]), unit="q_nm^-1")
                                #Int = numpy.dstack((Int, I_1d))
                                self.pro_progress.setValue(counter)
                                #self.pro_progress.setValue(frame/(len(data)-1)*100)
                                nxdata_2d[frame] = I2d
                                nxdata_1d[frame] = I_1d

                    else:
                        if factor[0] == 0 and factor[1] == numpy.inf:  
                            print("call function 3")
                            #for imag in data:
                            for frame, counter in numpy.ndenumerate(ind_list):
                                I2d, q_2d, azi = self.ai.integrate2d(data[frame], factor[2], factor[5], azimuth_range=(factor[3], factor[4]), unit="q_nm^-1", method=methods, mask=self.maskfile)
                                q_1d, I_1d = self.ai.integrate1d(data[frame], factor[2], azimuth_range=(factor[3], factor[4]), unit="q_nm^-1", mask=self.maskfile)
                                self.pro_progress.setValue(counter)
                                nxdata_2d[frame] = I2d
                                nxdata_1d[frame] = I_1d

                        else:   
                            print("call function 4")
                            #for imag in data:
                            for frame, counter in numpy.ndenumerate(ind_list):
                                I2d, q_2d, azi = self.ai.integrate2d(data[frame], factor[2], factor[5], radial_range=(factor[0], factor[1]), azimuth_range=(factor[3], factor[4]), unit="q_nm^-1", method=methods, mask=self.maskfile)
                                #norm = numpy.dstack((norm, I2d))
                                q_1d, I_1d = self.ai.integrate1d(data[frame], factor[2], radial_range=(factor[0], factor[1]), azimuth_range=(factor[3], factor[4]), unit="q_nm^-1", mask=self.maskfile)
                                #Int = numpy.dstack((Int, I_1d))
                                self.pro_progress.setValue(counter)
                                #self.pro_progress.setValue(frame/(len(data)-1)*100)
                                nxdata_2d[frame] = I2d
                                nxdata_1d[frame] = I_1d                        

                    nxdata_2q = nxdata2d.create_dataset(u"q", data=q_2d)
                    nxdata_2q.attrs[u"NX_class"] = u"NXdata"
                    nxdata_2q.make_scale('q')

                    nxdata_2a = nxdata2d.create_dataset(u"Azimuthal", data=azi)
                    nxdata_2a.attrs[u"NX_class"] = u"NXdata"
                    nxdata_2a.make_scale('Azimuthal')

                    nxdata_1q = nxdata1d.create_dataset(u"q", data=q_1d)
                    nxdata_1q.attrs[u"NX_class"] = u"NXdata"
                    nxdata_1q.make_scale('q')

                    nxdata_1d.dims[1].attach_scale(nxdata_1q)
                    nxdata_2d.dims[2].attach_scale(nxdata_2q)
                    nxdata_2d.dims[1].attach_scale(nxdata_2a)

                #if self.pro_progress.value >= 99:
                #    self.pro_progress.setValue(0)
                print("file is created as: \n {}".format(savefilename))
                del data, I2d, q_1d, I_1d, q_2d, azi, savefilename, norm_filename, ind, n_ind, ind_list
            except:
                if os.path.exists(savefilename):
                    os.remove(savefilename)
                    print("no file is created!")
            
    def Combineprocess(self, selected, normalcheck=False, normalmethod=None, subtractioncheck=False, datatype = None, AIntegcheck=False, IntegrationMethods=None, subfactor=None, intefactor=None, file_prefix="None"):

        if not self.__savingpath:
            raise Exception("\n\nSorry, The saving path is not defined!!!\n\nPlease select the saving path in Setting\n")
        if subtractioncheck and not isinstance(self.background, numpy.ndarray):
            print("Background remove panel is checked")
            raise Exception("\n\nPlease select the background in \"Remove Background\" Panel \n")
        if AIntegcheck and self.ai == []:
            raise Exception("\n\nPlease choose Calibration file in \"Integration\" Panel\n")

        for obj in selected:
            h5 = obj.local_file
            norm_filename = os.path.splitext(os.path.basename(obj.local_filename))[0]

            if datatype == "SAXS":                        
                try:
                    data = h5[self.__dataformat['saxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['saxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception("Data structures in {} or {} is not found".format(self.__dataformat['saxs_master'], self.__dataformat['saxs_det']))
            elif datatype == "WAXS":
                try:
                    data = h5[self.__dataformat['waxs_master']]
                    status = "master_file"
                except: 
                    try:
                        data = h5[self.__dataformat['waxs_det']]
                        status = "detector_file"
                    except:
                        raise Exception("Data structures in {} or {} is not found".format(self.__dataformat['waxs_master'], self.__dataformat['waxs_det']))

            ind = numpy.indices(data.shape[:-2])
            ind_list = numpy.ravel_multi_index(ind, data.shape[:-2])
            n_ind = ind_list.max()+1
            
            self.pro_progress.setRange(0, n_ind-1)

            if normalcheck:
                if status == "detector_file":

                    if self.masterfile_list == []:
                        print("The master file list is empty! \n meta data is 1")
                        meta = numpy.ones(data.shape[:-2])
                    else:
                        masterfile = [s for s in self.masterfile_list if norm_filename in s]
                        #for masterfile in self.masterfile_list:
                        if masterfile:
                            print("The masterfile is found")
                            metaentry = h5py.File(masterfile[0], 'r')
                            meta = self.extract_meta(metaentry, normalmethod) * numpy.ones(data.shape[:-2])
                        else:
                            print("Meta data is not found")
                            meta = numpy.ones(data.shape[:-2])

                elif status =="master_file":
                    meta = self.extract_meta(h5, normalmethod) * numpy.ones(data.shape[:-2])
                print("meta data is:\n{}".format(meta))
            else:
                meta = numpy.ones(data.shape[:-2])
                    
            if AIntegcheck:
                print("Azimuthal Integration is done!")
                if subtractioncheck:
                    if self.background is not []:
                        background = self.background
                        print("background is seleted")
                    else:
                        background = 0
                        print("background is empty and set as zero.")
                else:
                    background = 0
                    print("background is empty and set as zero.")
                try:
                    savefilename = self.save_name_check(self.__savingpath, norm_filename, file_prefix, "AI")
                    print("pass name check")

                    with h5py.File(savefilename, "w") as savefile:
                        
                        savefile.attrs[u"NX_class"] = u"NXroot"

                        nxentry = savefile.create_group(u"entry")
                        nxentry.attrs[u"NX_class"] = u"NXentry"

                        nxnorm = nxentry.create_group(u"data")
                        nxnorm.attrs[u"NX_class"] = u"NXdata"

                        if datatype == "SAXS" or datatype == "WAXS":

                            nxdata2d = nxnorm.create_group(datatype+u"_2D_data")
                            nxdata2d.attrs[u"NX_class"] = u"NXdata"

                            nxdata1d = nxnorm.create_group(datatype+u"_1D_data")
                            nxdata1d.attrs[u"NX_class"] = u"NXdata"

                        nxdata_2d = nxdata2d.create_dataset(u"data", data.shape[:-2]+ (intefactor[5], intefactor[2]), dtype = numpy.float32, shuffle=True)
                        nxdata_2d.attrs[u"NX_class"] = u"NXdata"

                        nxdata_1d = nxdata1d.create_dataset(u"data", data.shape[:-2] + (intefactor[2],), dtype = numpy.float32, shuffle=True)
                        nxdata_1d.attrs[u"NX_class"] = u"NXdata"
                        
                        if self.maskfile == []:
                            if intefactor[0] == 0 and intefactor[1] == numpy.inf: 
                                print("call function 1")
                                for frame, counter in numpy.ndenumerate(ind_list):
                                    I2d, q_2d, azi = self.ai.integrate2d(data[frame]/meta[frame]-subfactor * background, intefactor[2], intefactor[5], azimuth_range=(intefactor[3], intefactor[4]), method=IntegrationMethods, unit="q_nm^-1")
                                    q_1d, I_1d = self.ai.integrate1d(data[frame]/meta[frame]-subfactor * background, intefactor[2], azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1")
                                    self.pro_progress.setValue(counter)
                                    nxdata_2d[frame] = I2d
                                    nxdata_1d[frame] = I_1d         

                            else:
                                print("call function 2")
                                for frame, counter in numpy.ndenumerate(ind_list):
                                    I2d, q_2d, azi = self.ai.integrate2d(data[frame]/meta[frame]-subfactor * background, intefactor[2], intefactor[5], radial_range=(intefactor[0], intefactor[1]), azimuth_range=(intefactor[3], intefactor[4]), method=IntegrationMethods, unit="q_nm^-1")
                                    q_1d, I_1d = self.ai.integrate1d(data[frame]/meta[frame]-subfactor * background, intefactor[2], radial_range=(intefactor[0], intefactor[1]), azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1")
                                    self.pro_progress.setValue(counter)
                                    nxdata_2d[frame] = I2d
                                    nxdata_1d[frame] = I_1d    
                        else:
                            if intefactor[0] == 0 and intefactor[1] == numpy.inf:  
                                print("call function 3")
                                for frame, counter in numpy.ndenumerate(ind_list):
                                    I2d, q_2d, azi = self.ai.integrate2d(data[frame]/meta[frame]-subfactor * background, intefactor[2], intefactor[5], azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1", method=IntegrationMethods, mask=self.maskfile)
                                    q_1d, I_1d = self.ai.integrate1d(data[frame]/meta[frame]-subfactor * background, intefactor[2], azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1", mask=self.maskfile)
                                    self.pro_progress.setValue(counter)
                                    nxdata_2d[frame] = I2d
                                    nxdata_1d[frame] = I_1d   
                            else:
                                print("call function 4")
                                for frame, counter in numpy.ndenumerate(ind_list):
                                    I2d, q_2d, azi = self.ai.integrate2d(data[frame]/meta[frame]- subfactor *background, intefactor[2], intefactor[5], radial_range=(intefactor[0], intefactor[1]), azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1", method=IntegrationMethods, mask=self.maskfile)
                                    q_1d, I_1d = self.ai.integrate1d(data[frame]/meta[frame]- subfactor *background, intefactor[2], radial_range=(intefactor[0], intefactor[1]), azimuth_range=(intefactor[3], intefactor[4]), unit="q_nm^-1", mask=self.maskfile)
                                    self.pro_progress.setValue(counter)
                                    nxdata_2d[frame] = I2d
                                    nxdata_1d[frame] = I_1d 

                        nxdata_2q = nxdata2d.create_dataset(u"q", data=q_2d)
                        nxdata_2q.attrs[u"NX_class"] = u"NXdata"
                        nxdata_2q.make_scale('q')

                        nxdata_2a = nxdata2d.create_dataset(u"Azimuthal", data=azi)
                        nxdata_2a.attrs[u"NX_class"] = u"NXdata"
                        nxdata_2a.make_scale('Azimuthal')

                        nxdata_1q = nxdata1d.create_dataset(u"q", data=q_1d)
                        nxdata_1q.attrs[u"NX_class"] = u"NXdata"
                        nxdata_1q.make_scale('q')

                        nxdata_1d.dims[1].attach_scale(nxdata_1q)
                        nxdata_2d.dims[2].attach_scale(nxdata_2q)
                        nxdata_2d.dims[1].attach_scale(nxdata_2a)
                    
                    print("file is created as: \n {}".format(savefilename))
                    del meta, data, I2d, q_1d, I_1d, q_2d, azi, savefilename, norm_filename, ind, n_ind, ind_list
                except:
                    if os.path.exists(savefilename):
                        os.remove(savefilename)
                        print("no file is created!")
                

            elif not AIntegcheck and subtractioncheck:
                print("Azimuthal integration is NOT done but background is substracted")
                #BG_remove_writer(self.__savingpath, data, norm_filename, file_prefix)
                try:
                    savefilename = self.save_name_check(self.__savingpath, norm_filename, file_prefix, "AI")
                    print("pass name check")
                    with h5py.File(savefilename, "w") as savefile:
                        savefile.attrs[u"NX_class"] = u"NXroot"

                        nxentry = savefile.create_group(u"entry")
                        nxentry.attrs[u"NX_class"] = u"NXentry"

                        nxnorm = nxentry.create_group(u"data")
                        nxnorm.attrs[u"NX_class"] = u"NXdata"

                        nxdata = nxnorm.create_dataset(u"data", shape = data.shape, shuffle=True)
                        nxdata.attrs[u"NX_class"] = u"NXdata"

                        for frame, counter in numpy.ndenumerate(ind_list):
                            self.pro_progress.setValue(counter)
                            nxdata[frame] = data[frame] - subfactor * self.background

                    del data, norm_filename
                except:
                    if os.path.exists(savefilename):
                        os.remove(savefilename)
                        print("no file is created!")
                        del savefilename

    def closeAndSyncCustomContextMenu(self, event):
        """Called to populate the context menu

        :param silx.gui.hdf5.Hdf5ContextMenuEvent event: Event
            containing expected information to populate the context menu
        """
        selectedObjects = event.source().selectedH5Nodes()
        menu = event.menu()

        if not menu.isEmpty():
            menu.addSeparator()

        for obj in selectedObjects:
            if obj.ntype is h5py.File:
                action = qt.QAction("Remove %s" % obj.local_filename, event.source())
                action.triggered.connect(lambda: self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.h5py_object))
                menu.addAction(action)
            elif obj.ntype is h5py.Dataset:
                action = qt.QAction("Remove %s" % obj.local_filename, event.source())
                action.triggered.connect(lambda: self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.local_file))
                menu.addAction(action)
            elif obj.ntype is h5py.Group:
                action = qt.QAction("Remove %s" % obj.local_filename, event.source())
                action.triggered.connect(lambda: self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.local_file))
                menu.addAction(action)

    def displayData(self):
        """Called to update the dataviewer with the selected data.
        """
        selected = list(self.__treeview.selectedH5Nodes())
        #print(selected[0])
        if len(selected) == 1:
            # Update the viewer for a single selection
            data = selected[0]
            # data is a hdf5.H5Node object
            # data.h5py_object is a Group/Dataset object (from h5py, spech5, fabioh5)
            # The dataviewer can display both
            self.__dataViewer.setData(data)
            #self.__dataViewer2.addImage(data)

    def masterfile_load(self):
        files = qt.QFileDialog.getOpenFileNames(self, 'Choose Master File')

        if files != ('', ''):
            for name in files[0]:
                if name not in self.masterfile_list:
                    self.masterfile_list.append(name)
            print(self.masterfile_list)

    def Load_file(self):
        files = qt.QFileDialog.getOpenFileNames(self, 'Choose Mask')
        
        if files != ('', ''):
            for name in files[0]:
                self.__treeview.findHdf5TreeModel().appendFile(name)

    def refresh_file(self):
        #files = qt.QFileDialog.getOpenFileNames(self, 'Choose Mask')
        #for file in self.file_layout
        self.__treeview.findHdf5TreeModel().clear()
        if self.__rawdata_path:
            #windows_path = PureWindowsPath(self.__rawdata_path + "\\**\\*.*5")
            #path= Path(windows_path)
            path = self.__rawdata_path + "/**/*.*5"
            print(path)
            for files in glob.glob(path, recursive=True):
                self.__treeview.findHdf5TreeModel().appendFile(files)
        else:
            raise Exception("\nThe Raw data path is not defined!!!\n")
    
    def delete_file(self, selectedObjects):
        #selectedObjects = event.source().selectedH5Nodes()
        #menu = event.menu()

        #if not menu.isEmpty():
        #    menu.addSeparator()
        
        for obj in selectedObjects:
            if obj.ntype is h5py.File:
                print("yes, it is h5py.file")
                #print(obj.h5py_object)
                self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.h5py_object)
            else:
                print("no, it is not selected properly")
                self.__treeview.findHdf5TreeModel().removeH5pyObject(obj.local_file)

    def clear_view(self):
        self.__treeview.findHdf5TreeModel().clear()

    def save_name_check(self, path, name, prefix, tag):

        if os.path.isdir(path):
            if prefix=="None" or prefix =="none":
                processed_name = os.path.join(path, tag+"_"+name + "_000.h5")
            else:
                processed_name = os.path.join(path, prefix+"_"+tag+"_"+name + "_000.h5")            
            
            sequence = 1
            while os.path.isfile(processed_name):
                processed_name = processed_name[:-6]+"{:03d}.h5".format(sequence)
                sequence += 1
        del sequence
        return processed_name
    
    def extract_meta(self, h5, method = 'All'):
        if method == "Aquisition time":
            try:
                meta = h5[self.__dataformat['dt']][...]
                print("exposure time is found", meta)
            except:
                try:
                    meta = numpy.ones((len(h5['entry/leftover/Pt_No'])))
                    command_run = str(h5['entry/leftover/command_run'][...])
                    meta = float(re.findall(r"[-+]?\d*\.?\d+|[-+]?\d+", command_run)[-1])*meta
                    print("exposure time is calculated")
                except:
                    raise Exception("meta data is not found")
        elif method == "Transmission":
            try:
                meta = h5[self.__dataformat['I_t']][:]
                print("I_t is found")
            except:
                try:
                    meta = h5['entry/measurement/adlink_ch0']
                    print("I_t is found")
                except:
                    raise Exception("meta data is not found")
        elif method == "Flux":
            try:
                meta = h5[self.__dataformat['I_0']][:]
                print("I_0 is found")
            except:
                try:
                    meta = h5['entry/measurement/albaem02_ch2']
                    print("I_0 is found")
                except:
                    raise Exception("meta data is not found")
        elif method == "Transmittance":
            try:
                meta = h5[self.__dataformat['I_t']][:]/h5[self.__dataformat['I_0']][:]
                print("I_t/I_0 is calculated")
            except:
                try:
                    meta = h5['entry/measurement/adlink_ch0'][:]/h5['entry/measurement/albaem02_ch2'][:]
                    print("I_t/I_0 is calculated")
                except:
                    raise Exception("meta data is not found")
        elif method == "All":
            try:
                meta = h5[self.__dataformat['dt']]*h5[self.__dataformat['I_t']][:]*h5[self.__dataformat['I_0']][:]
                print("data will be normalized to dt*I_t*I_0")
            except:
                try:
                    meta = numpy.ones((len(h5['entry/leftover/Pt_No'])))
                    command_run = str(h5['entry/leftover/command_run'][...])
                    meta = float(re.findall(r"[-+]?\d*\.?\d+|[-+]?\d+", command_run)[-1])*meta
                    meta = meta*h5['entry/measurement/adlink_ch0']*h5['entry/measurement/albaem02_ch2']
                    #print(meta)
                    print("data will be normalized to dt*I_t*I_0")
                except:
                    raise Exception("meta data is not found")
        return meta
