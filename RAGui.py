# -*- coding: utf-8 -*-
#######################################
# newer layout of gen-SAXS GUI
#######################################

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
#import Reduction
import Reduction_modified
#import Analysis
import Plot
import hdf5plugin
#from pyFAI.app import calib2

logging.basicConfig()
_logger = logging.getLogger("RAGui")

from silx.gui import qt
import silx.gui.hdf5
from silx.gui.data.DataViewerFrame import DataViewerFrame
from silx.gui.data.DataViewer import DataViewer
from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot.PlotWindow import PlotWindow
from silx.gui.widgets.ThreadPoolPushButton import ThreadPoolPushButton
from silx.gui.hdf5.Hdf5TreeModel import Hdf5TreeModel
from silx.io.nxdata import save_NXdata

class RAGui(qt.QMainWindow):
    def __init__(self, filenames=None):
        qt.QMainWindow.__init__(self)
        
        self.setWindowTitle("Reduce and Analysis GUI")

        self.statusBar()
        mainmenu = self.menuBar()
        fileMenu = mainmenu.addMenu('&File')
        viewMenu = mainmenu.addMenu('&Setting')

        set_path = qt.QAction('Saving Path', self)
        set_path.triggered.connect(self.path_set)
        viewMenu.addAction(set_path)

        pyFAI_cali = qt.QAction('Calibration', self)
        pyFAI_cali.triggered.connect(self.cali_trigger)
        viewMenu.addAction(pyFAI_cali)
        
        helpMenu = mainmenu.addMenu('&Help')
        help_wiki = qt.QAction('Help wiki', self)
        help_wiki.triggered.connect(self.wiki_open)
        helpMenu.addAction(help_wiki) 
        about = qt.QAction("About", self)
        about.triggered.connect(self.about_open)
        helpMenu.addAction(about)        
        
        open_file = qt.QAction('Raw Data', self)
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.file_open)

        exitAct = qt.QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qt.qApp.quit)
        
        fileMenu.addAction(open_file)
        fileMenu.addAction(exitAct)

        #self.InitWindow()


    #def InitWindow(self):
        Tabmenu = qt.QTabWidget()
        Tabmenu.setTabPosition(2)
        Tabmenu.setStyleSheet(
            "QTabWidget::pane {border-top: 2px solid #C2C7CB;}"
            "QTabWidget::tab  {border: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; font: Arial}"
            "QTabBar::tab:selected {background-color: #4169E1; color:#ffffff;}")
        self.setCentralWidget(Tabmenu)
        #self.tab_red = Reduction.Reduction()
        self.tab_red = Reduction_modified.Reduction()
        #self.tab_fit = Analysis.Analysis() 
        self.tab_plot = Plot.Plot()

        Tabmenu.addTab(self.tab_red, "Reduction")
        Tabmenu.addTab(self.tab_plot, "Profile Plot")
        #Tabmenu.addTab(self.tab_fit, "Fitting")
    
    def file_open(self):

        #names = qt.QFileDialog.getOpenFileNames(self, 'Open File')
        names = qt.QFileDialog.getExistingDirectory(self, "Raw Data path")

        if names != ('', ''):
            #self.tab_red.File_open(names)
            self.tab_red.File_open(names)

    def path_set(self):
        saving_path = qt.QFileDialog.getExistingDirectory(self, "set saving path")

        if saving_path != ('',''):
            self.tab_red.Path_set(saving_path)
            self.tab_plot.Path_set(saving_path)

    def cali_trigger(self):
        #self.message("Executing calibration process.")
        self.p = qt.QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #self.p.start("python3", ['dummy_script.py'])
        self.p.start("pyfai-calib2")
    
    def wiki_open(self):
        self.wiki = qt.QDesktopServices()
        self.wiki.openUrl(qt.QUrl("https://www.maxiv.lu.se/accelerators-beamlines/beamlines/cosaxs/sampleenvironment/software/"))

    def about_open(self):
        msgBox = qt.QMessageBox()
        msgBox.setIcon(qt.QMessageBox.Information)
        msgBox.setText('''The Reduction and Analysis GUI is develped by Dr. Shun Yu (RISE Research Institue of Sweden) and tested by Dr. Nils Håkansson (MAX IV).
        The software is based on \"silx\" package developed by European Synchrotron Radiation Facility (ESRF) and serves the reduction and quick plotting of data aquired at CoSAXS beamline, MAX IV''')
        msgBox.setWindowTitle("About")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)

        returnValue = msgBox.exec()
        #if returnValue == qt.QMessageBox.Ok:
        #    print('OK clicked')


def main():
    """
    :param filenames: list of file paths
    """
    app = qt.QApplication([])
    #app.setStyle('Fusion')
    #print(qt.QStyleFactory.keys())
    sys.excepthook = qt.exceptionHandler
    window = RAGui()
    window.show()
    result = app.exec_()
    # remove ending warnings relative to QTimer
    app.deleteLater()
    sys.exit(result)


if __name__ == "__main__":
    main()