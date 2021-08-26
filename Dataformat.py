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
import silx
import glob
import re
import json
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
from silx.gui.widgets.TableWidget import TableWidget
from silx.io.nxdata import save_NXdata

class inputdialogdemo(qt.QDialog):
    def __init__(self, parent = None):
        super(inputdialogdemo, self).__init__(parent)

        self.datapath = []
        self.rownumber = []
        self.columnumber = []
        self.savefilename = []
        
        layout_main = qt.QVBoxLayout()
        self.setLayout(layout_main)

        layout_select_file = qt.QFormLayout()
        self.btn = qt.QPushButton("Choose from list")
        layout_select_file.addRow(qt.QLabel("Select data for the model structure"), self.btn)
        self.btn.clicked.connect(self.select_data)

        layout_main.addLayout(layout_select_file)

        layout_handling = qt.QHBoxLayout()
        self.treeview = silx.gui.hdf5.Hdf5TreeView(self)
        self.treeview.activated.connect(self.assignpath)
        layout_handling.addWidget(self.treeview)

        layout_button = qt.QVBoxLayout()
        self.extractbutton = qt.QPushButton("Extract")
        self.extractbutton.clicked.connect(self.extractpath)
        layout_button.addWidget(self.extractbutton)
        self.withdrawbutton = qt.QPushButton("Withdraw")
        self.withdrawbutton.clicked.connect(self.withdrawpath)
        layout_button.addWidget(self.withdrawbutton)

        layout_handling.addLayout(layout_button)

        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setRowCount(15)
        self.table.cellClicked.connect(self.getcell)
        self.init_table()
        layout_handling.addWidget(self.table)

        layout_save = qt.QHBoxLayout()
        layout_save.setAlignment(qt.Qt.AlignRight)
        
        self.btnreset = qt.QPushButton("Reset")
        self.btnreset.clicked.connect(lambda: self.init_table())
        self.btnedit = qt.QPushButton("Edit")
        self.btnedit.clicked.connect(lambda: self.editfile())
        self.btnsave = qt.QPushButton("Save")
        self.btnsave.clicked.connect(lambda: self.savefile())
        self.btnclose = qt.QPushButton("Close")
        self.btnclose.clicked.connect(lambda: self.close())

        layout_main.addLayout(layout_handling)

        layout_save.addWidget(self.btnreset)
        layout_save.addWidget(self.btnedit)
        layout_save.addWidget(self.btnsave)
        layout_save.addWidget(self.btnclose)
                
        layout_main.addLayout(layout_save)
        self.setWindowTitle("Add new Data format")
                
        self.exec_()
    
    def select_data(self):
        file = qt.QFileDialog.getOpenFileName(self, 'Choose Model Data Structure')

        if file != ('', ''):
            print(file[0])
            self.treeview.findHdf5TreeModel().appendFile(file[0])
            #self.ExtractDataformat(file[0])
    
    def init_table(self):
        format = {
            "saxs_det": "entry/data/data",
            "saxs_master": "",
            "waxs_det": "entry/data/data",
            "waxs_master":"",
            "I_0": "",
            "I_t": "",
            "dt": "",
            "Motor_x": "",
            "Motor_y": "",
            "Motor_z": "",
            "Rot": "",
            "T": ""
        }
        self.readdict(format)
        '''
        for count, dict in enumerate(zip(format.keys(), format.values())):
            key_name = qt.QTableWidgetItem(dict[0])
            path = qt.QTableWidgetItem(dict[1])
            self.table.setItem(count, 0, key_name)
            self.table.setItem(count, 1, path)
        '''
    
    def assignpath(self):
        selected = list(self.treeview.selectedH5Nodes())
        #print(selected[0])
        if len(selected) == 1:
            # Update the viewer for a single selection
            self.datapath = selected[0].data_url.data_path()[1:]

            print(self.datapath)

    def extractpath(self):
        try:
            setpath = qt.QTableWidgetItem(self.datapath)
            print(self.rownumber)
            self.table.setItem(self.rownumber, self.columnumber, setpath) 
        except:
            print("Assignment is failed!!")

    def withdrawpath(self):
        try:
            self.table.setItem(self.rownumber, self.columnumber, None) 
        except:
            print("withdraw is failed!!")
    
    def getcell(self):
        self.rownumber = self.table.currentRow()
        self.columnumber = self.table.currentColumn()

    def savefile(self):
        name = qt.QFileDialog.getSaveFileName(self, 'Save Data Format', 'Data format/', "txt files (*.txt)")
                
        data = self.convertdict()

        if name != ('', ''):
            with open(name[0],'w') as file:
                file.write(json.dumps(data))
            self.savefilename = name[0]
        else:
            self.savefilename = []

        print(self.savefilename)
            
    def convertdict(self):
        dict = {}
        n = 0
        while self.table.item(n, 0):
            dict.update({self.table.item(n, 0).text(): self.table.item(n, 1).text()})
            n += 1
        print(dict)
        return dict
    
    def editfile(self):
        file = qt.QFileDialog.getOpenFileName(self, 'Choose Model Data Structure', 'Data format/', "txt files (*.txt)")

        if file != ('', ''):
            with open(file[0],'r') as f:
                format = json.loads(f.read())
                self.readdict(format)
                    

    def readdict(self, format):
        for count, dict in enumerate(zip(format.keys(), format.values())):
            key_name = qt.QTableWidgetItem(dict[0])
            path = qt.QTableWidgetItem(dict[1])
            self.table.setItem(count, 0, key_name)
            self.table.setItem(count, 1, path)

    '''            
    def ExtractDataformat(self, obj):
        with h5py.File(obj,'r') as h5:
            full_file_keys = []
            Data_keys = []
            h5.visit(full_file_keys.append)
            for h5_key in full_file_keys:
                if isinstance(h5[h5_key], h5py.Dataset):
                #if isinstance(h5[h5_key], h5py.Group):
                    #tmp = np.array(h5obj[h5_key])[mask]
                    # There is no way to simply change the dataset because its
                    # shape is fixed, causing a broadcast error, so it is
                    # necessary to delete and then recreate it.
                    #del h5obj[h5_key]
                    #h5obj.create_dataset(h5_key, data=tmp)
                    Data_keys.append(h5_key)
            print(Data_keys)
            self.Data_keys = Data_keys
            del full_file_keys, Data_keys
                    #tmp = h5_key.split('/')
                    #print(tmp[-1])
    
    def ExtractDataformat(self, event):
        for obj in event:
            if obj.ntype == h5py.File:
                full_file_keys = []
                Data_keys = []
                h5 = obj.h5py_object
                h5.visit(full_file_keys.append)
                for h5_key in full_file_keys:
                    if isinstance(h5[h5_key], h5py.Dataset):
                    #if isinstance(h5[h5_key], h5py.Group):
                        #tmp = np.array(h5obj[h5_key])[mask]
                        # There is no way to simply change the dataset because its
                        # shape is fixed, causing a broadcast error, so it is
                        # necessary to delete and then recreate it.
                        #del h5obj[h5_key]
                        #h5obj.create_dataset(h5_key, data=tmp)
                        Data_keys.append(h5_key)
                print(Data_keys)
                self.Data_keys = Data_keys
                del full_file_keys, Data_keys
                        #tmp = h5_key.split('/')
                        #print(tmp[-1])
    '''

class D_format(qt.QComboBox):
    def __init__(self, parent=None):
        super(D_format, self).__init__(parent)
        #layout = qt.QHBoxLayout()
        #layout.addStretch(1)
        #self.dropbox = qt.QComboBox()
        self.loadfile()
        #layout.addWidget(qt.QLabel("File Format"))
        #layout.addWidget(self.dropbox)
        #self.setLayout(layout)
        self.dataformat = {
            "saxs_det": "",
            "saxs_master": "",
            "waxs_det": "",
            "waxs_master":"",
            "I_0": "",
            "I_t": "",
            "dt": "",
            "Motor_x": "",
            "Motor_y": "",
            "Motor_z": "",
            "Rot": "",
            "T": ""
        }
        self.setdata("MAX IV - CoSAXS")
        #self.dropbox.currentIndexChanged.connect(self.onchange)
        self.activated.connect(self.onchange)
    
    def setdata(self, filename):
        self.setCurrentText(filename)
        self.dataformat = self.readfile(self.currentText())
        print(self.currentText() + " is selected")
        '''
        if self.currentText() == "MAX IV - CoSAXS":
            self.dataformat = self.readfile(self.currentText())
            #print(self.dataformat)
            print(self.currentText() + " is selected")
            #self.output()
        else:
            self.onchange()
        '''
    def onchange(self):
        if self.currentText() != "User defined":
            self.dataformat = self.readfile(self.currentText())
            print(self.currentText() + " is selected")
            #self.output(self.dataformat)
            #print(self.dropbox.currentText())
            #print(self.dataformat)
        else:
            self.userdefine()

    def userdefine(self):
        print("you're in charge")
        inputfile = inputdialogdemo()
        self.clear()
        self.loadfile()
        if inputfile.savefilename != []:
            print(inputfile.savefilename)
            filename = os.path.splitext(os.path.basename(inputfile.savefilename))[0]
            print(filename)
            self.setdata(filename)
            #self.output(self.dataformat)


        
    
    def readfile(self, filename):
        with open('Data format/'+filename+'.txt') as f:
                #return dict(re.findall(r'(\S+)\s+(.+)', f.read()))
                #return dict(line.strip().split(1) for line in f)
                #return ast.literal_eval(f.read())
                return json.loads(f.read())
    
    def loadfile(self):
        for file in glob.glob("Data format/*"):
            fileName = os.path.splitext(os.path.basename(file))[0]
            self.addItem(fileName)
        self.addItem("User defined")

    def output(self, data):
        return data

            
    
    