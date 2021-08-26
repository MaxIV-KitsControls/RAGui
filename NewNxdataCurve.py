# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2017-2020 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""This module defines widgets used by _NXdataView.
"""
__authors__ = ["P. Knobel, Shun Yu"]
__license__ = "MIT"
__date__ = "12/11/2018"

import logging
import numpy

from silx.gui import qt, icons
from silx.gui.plot.actions import PlotAction
from silx.gui.data.NumpyAxesSelector import NumpyAxesSelector
from silx.gui.plot import PlotWindow, Plot1D, Plot2D, StackView, ScatterView
from silx.gui.plot.ComplexImageView import ComplexImageView
from silx.gui.colors import Colormap
from silx.gui.widgets.FrameBrowser import HorizontalSliderWithBrowser

from silx.math.calibration import ArrayCalibration, NoCalibration, LinearCalibration


_logger = logging.getLogger(__name__)

class ArrayCurvePlot(qt.QWidget):
    """
    Widget for plotting a curve from a multi-dimensional signal array
    and a 1D axis array.
    The signal array can have an arbitrary number of dimensions, the only
    limitation being that the last dimension must have the same length as
    the axis array.
    The widget provides sliders to select indices on the first (n - 1)
    dimensions of the signal array, and buttons to add/replace selected
    curves to the plot.
    This widget also handles simple 2D or 3D scatter plots (third dimension
    displayed as colour of points).
    """
    def __init__(self, parent=None):
        """
        :param parent: Parent QWidget
        """
        super(ArrayCurvePlot, self).__init__(parent)

        self.__signals = None
        self.__signals_names = None
        self.__signal_errors = None
        self.__axis = None
        self.__axis_name = None
        self.__x_axis_errors = None
        self.__values = None
        self.__old_plotmode = None
        self.__waterfallfactor = 1

        self._plot = Plot1D()

        self._selector = NumpyAxesSelector(self)
        self._selector.setNamedAxesSelectorVisibility(True)
        self._selector.show()
        self.__selector_is_connected = False

        self._plot.sigActiveCurveChanged.connect(self._setYLabelFromActiveLegend)

        layout = qt.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)
        layout.addWidget(self._selector)

        self.setLayout(layout)

    def getPlot(self):
        """Returns the plot used for the display
        :rtype: Plot1D
        """
        return self._plot

    def setCurvesData(self, ys, x=None,
                      yerror=None, xerror=None,
                      ylabels=None, xlabel=None, title=None,
                      xscale=None, yscale=None, aziselector=None, legend=None, plotmode=1):
        """
        :param List[ndarray] ys: List of arrays to be represented by the y (vertical) axis.
            It can be multiple n-D array whose last dimension must
            have the same length as x (and values must be None)
        :param ndarray x: 1-D dataset used as the curve's x values. If provided,
            its lengths must be equal to the length of the last dimension of
            ``y`` (and equal to the length of ``value``, for a scatter plot).
        :param ndarray yerror: Single array of errors for y (same shape), or None.
            There can only be one array, and it applies to the first/main y
            (no y errors for auxiliary_signals curves).
        :param ndarray xerror: 1-D dataset of errors for x, or None
        :param str ylabels: Labels for each curve's Y axis
        :param str xlabel: Label for X axis
        :param str title: Graph title
        :param str xscale: Scale of X axis in (None, 'linear', 'log')
        :param str yscale: Scale of Y axis in (None, 'linear', 'log')
        """
        self.__signals = ys
        #print(ys.shape)
        self.__signals_names = ylabels or (["Y"] * len(ys))
        self.__signal_errors = yerror
        self.__axis = x
        self.__axis_name = xlabel
        self.__x_axis_errors = xerror
        self.__title = title
        self.__legend = legend
        self.__plotmode = plotmode
        self.aziselector = aziselector
        

        if self.__selector_is_connected:
            try:
                self._selector.selectionChanged.disconnect(self._updateCurve)
            except:
                self._selector.selectionChanged.disconnect(self._updatewaterfall)
            self.__selector_is_connected = False
        #self._selector.setSelection([])
        #if self.__plotmode != 3:
        if self.aziselector == None :
            if ys.ndim == 1:
                self._selector.setData(ys)
            elif ys.ndim == 2:
                self._selector.setData(ys[slice(0, None, 1), slice(None,None,None)])
                #self._selector.setAxisNames(["Y"])
            else:
                self._selector.setData(ys[slice(0, None, 1), slice(0, None, 1), slice(None,None,None)])
                #self._selector.setAxisNames(["Y"])
        else:
            #ys = numpy.moveaxis(ys, -1, 1)
            ys = numpy.sum(ys[:,self.aziselector[0]:self.aziselector[1],:], axis=1)
            self._selector.setData(ys)
            #self._selector.setAxisNames(["Y"])
        #self._selector.setSelection([(slice(0, -1, 1), slice(0,-1,1), slice(None))])
        if self._selector.data() is not None:
            print("Data is assigned")
        else:
            print("Data is empty")
        self._selector.setAxisNames(["Y"])
        #self._selector.setCustomAxis(["sequence", "azimuthal", "Intensity"])
        
        #if len(ys[0].shape) < 3:
        #    self._selector.hide()
        #else:
        #    self._selector.show()

        self._plot.setGraphTitle(title or "")
        if xscale is not None:
            self._plot.getXAxis().setScale(
                'log' if xscale == 'log' else 'linear')
        if yscale is not None:
            self._plot.getYAxis().setScale(
                'log' if yscale == 'log' else 'linear')
        self._updateCurve()

        if not self.__selector_is_connected:
            self._selector.selectionChanged.connect(self._updateCurve)
            self.__selector_is_connected = True

    def _updateCurve(self):
        #print(self.__old_plotmode)
        if self.__plotmode == 1:
            self._plot.remove(kind="curve")
            Curve = self._plot.getActiveCurve()
            data = self._selector.selectedData()
            Curve = self._plot.addCurve(self.__axis, data, legend=self.__legend, 
                xerror=self.__x_axis_errors,
                yerror=None, xlabel=self.__axis_name)
            Curve        
            self._plot.resetZoom()
            self.__old_plotmode = 1
        
        elif self.__plotmode == 2:
            if self.__old_plotmode == 1:
                self._plot.remove("data", kind="curve")
            elif self.__old_plotmode == 3 or self.__old_plotmode == 4:
                self._plot.remove(kind="curve")
            #Curve = self._plot.getActiveCurve()
            data = self._selector.selectedData()
            Curve = self._plot.addCurve(self.__axis, data, legend=self.__legend,
                xerror=self.__x_axis_errors,
                yerror=None, xlabel=self.__axis_name)
            Curve        
            self._plot.resetZoom()
            self.__old_plotmode = 2
        #print(self.__old_plotmode)

    def Setwaterfall(self, ys, x=None,
                      yerror=None, xerror=None,
                      ylabels=None, xlabel=None, title=None,
                      xscale=None, yscale=None, legend=None, selector = None, qselector = None, aziselector=None, factor = 1, plotmode=3):
        self._plot.remove(kind="curve")
        #print(self.__old_plotmode)
        self.__signals_names = ylabels or (["Y"] * len(ys))
        self.__signal_errors = yerror
        self.__axis = x
        self.__axis_name = xlabel
        self.__x_axis_errors = xerror
        self.__title = title
        self.__legend = legend
        self.__plotmode = plotmode
        self.__waterfallfactor = factor
        self.arrayselector = selector

        if self.__selector_is_connected:
            try:
                self._selector.selectionChanged.disconnect(self._updateCurve)
            except:
                self._selector.selectionChanged.disconnect(self._updatewaterfall)
            self.__selector_is_connected = False

       
        if aziselector is None:
            if ys.ndim == 2:
                self.__signals = ys[slice(selector[0], selector[1], selector[2]),:]
            else:
                if qselector is None:
                    self.__signals = ys[...,slice(selector[0], selector[1], selector[2]), :]

                else:
                    self.__signals = numpy.sum(ys[...,slice(selector[0], selector[1], selector[2]), qselector[0]:qselector[1], :], axis = -2)

        else:
            self.__signals = numpy.sum(ys[..., slice(selector[0], selector[1], selector[2]), aziselector[0]:aziselector[1], :], axis= -2)

        ind = numpy.indices(self.__signals.shape[:-2])

        self._selector.setData(ind)

        if len(self.__signals.shape) <= 2:
            self._selector.hide()
        else:
            self._selector.show()

        self._updatewaterfall()
                
        if not self.__selector_is_connected:
            self._selector.selectionChanged.connect(self._updatewaterfall)
            self.__selector_is_connected = True
        
        #self._selector.clear()
    def _updatewaterfall(self):
        selection = self._selector.selection()


        if self.__plotmode == 3:
            sequence = 0
            for curve in self.__signals[selection]:
            #for curve in images:
                self._plot.addCurve(self.__axis, curve*self.__waterfallfactor**sequence, legend=self.__legend+'_'+str(self.arrayselector[0]+sequence*self.arrayselector[2]))
                sequence += 1
            self.__old_plotmode = 3
        
        if self.__plotmode == 4:
            sequence = 0
            for curve in self.__signals[selection]:
            #for curve in images:
                self._plot.addCurve(self.__axis, curve+self.__waterfallfactor*sequence, legend=self.__legend+'_'+str(self.arrayselector[0]+sequence*self.arrayselector[2]))
                sequence += 1
            self.__old_plotmode = 4

        #selection = self._selector.selection()
        #s = self._selector.selectedData()
        #print(selection)

        #print(ys)
    '''
    def _updateCurve(self):
        selection = self._selector.selection()
        print(selection)
        #ys = [sig[selection] for sig in self.__signals]
        ys = self.__signals[selection]
        y0 = ys[0,0]
        len_y = len(y0)
        x = self.__axis
        if x is None:
            x = numpy.arange(len_y)
        elif numpy.isscalar(x) or len(x) == 1:
            # constant axis
            x = x * numpy.ones_like(y0)
        elif len(x) == 2 and len_y != 2:
            # linear calibration a + b * x
            x = x[0] + x[1] * numpy.arange(len_y)

        self._plot.remove(kind=("curve",))

        for i in range(len(self.__signals)):
            legend = self.__signals_names[i]

            # errors only supported for primary signal in NXdata
            y_errors = None
            if i == 0 and self.__signal_errors is not None:
                y_errors = self.__signal_errors[self._selector.selection()]
            self._plot.addCurve(x, ys[i], legend=legend,
                                xerror=self.__x_axis_errors,
                                yerror=y_errors)
            if i == 0:
                self._plot.setActiveCurve(legend)

        self._plot.resetZoom()
        self._plot.getXAxis().setLabel(self.__axis_name)
        self._plot.getYAxis().setLabel(self.__signals_names[0])
    '''

    def _setYLabelFromActiveLegend(self, previous_legend, new_legend):
        for ylabel in self.__signals_names:
            if new_legend is not None and new_legend == ylabel:
                self._plot.getYAxis().setLabel(ylabel)
                break

    def clear(self):
        old = self._selector.blockSignals(True)
        self._selector.clear()
        self._selector.blockSignals(old)
        self._plot.clear()

class ArrayImagePlot(qt.QWidget):
    """
    Widget for plotting an image from a multi-dimensional signal array
    and two 1D axes array.
    The signal array can have an arbitrary number of dimensions, the only
    limitation being that the last two dimensions must have the same length as
    the axes arrays.
    Sliders are provided to select indices on the first (n - 2) dimensions of
    the signal array, and the plot is updated to show the image corresponding
    to the selection.
    If one or both of the axes does not have regularly spaced values, the
    the image is plotted as a coloured scatter plot.
    """
    def __init__(self, parent=None):
        """
        :param parent: Parent QWidget
        """
        super(ArrayImagePlot, self).__init__(parent)

        self.__signals = None
        self.__signals_names = None
        self.__x_axis = None
        self.__x_axis_name = None
        self.__y_axis = None
        self.__y_axis_name = None

        self._plot = Plot2D(self)
        self._plot.setDefaultColormap(Colormap(name="viridis",
                                               vmin=None, vmax=None,
                                               normalization=Colormap.LOGARITHM))
        self._plot.getIntensityHistogramAction().setVisible(True)
        self._plot.setKeepDataAspectRatio(False)

        # not closable
        self._selector = NumpyAxesSelector(self)
        self._selector.setNamedAxesSelectorVisibility(False)
        self._selector.selectionChanged.connect(self._updateImage)

        self._auxSigSlider = HorizontalSliderWithBrowser(parent=self)
        self._auxSigSlider.setMinimum(0)
        self._auxSigSlider.setValue(0)
        self._auxSigSlider.valueChanged[int].connect(self._sliderIdxChanged)
        self._auxSigSlider.setToolTip("Select auxiliary signals")

        layout = qt.QVBoxLayout()
        layout.addWidget(self._plot)
        layout.addWidget(self._selector)
        layout.addWidget(self._auxSigSlider)

        self.setLayout(layout)

    def _sliderIdxChanged(self, value):
        self._updateImage()

    def getPlot(self):
        """Returns the plot used for the display
        :rtype: Plot2D
        """
        return self._plot

    def setImageData(self, signals,
                     x_axis=None, y_axis=None,
                     signals_names=None,
                     xlabel=None, ylabel=None,
                     title=None, isRgba=False,
                     xscale=None, yscale=None):
        """
        :param signals: list of n-D datasets, whose last 2 dimensions are used as the
            image's values, or list of 3D datasets interpreted as RGBA image.
        :param x_axis: 1-D dataset used as the image's x coordinates. If
            provided, its lengths must be equal to the length of the last
            dimension of ``signal``.
        :param y_axis: 1-D dataset used as the image's y. If provided,
            its lengths must be equal to the length of the 2nd to last
            dimension of ``signal``.
        :param signals_names: Names for each image, used as subtitle and legend.
        :param xlabel: Label for X axis
        :param ylabel: Label for Y axis
        :param title: Graph title
        :param isRgba: True if data is a 3D RGBA image
        :param str xscale: Scale of X axis in (None, 'linear', 'log')
        :param str yscale: Scale of Y axis in (None, 'linear', 'log')
        """
        self._selector.selectionChanged.disconnect(self._updateImage)
        self._auxSigSlider.valueChanged.disconnect(self._sliderIdxChanged)

        self.__signals = signals
        self.__signals_names = signals_names
        self.__x_axis = x_axis
        self.__x_axis_name = xlabel
        self.__y_axis = y_axis
        self.__y_axis_name = ylabel
        self.__title = title

        self._selector.clear()
        if not isRgba:
            self._selector.setAxisNames(["Y", "X"])
            img_ndim = 2
        else:
            self._selector.setAxisNames(["Y", "X", "RGB(A) channel"])
            img_ndim = 3
        self._selector.setData(signals[0])

        if len(signals[0].shape) <= img_ndim:
            self._selector.hide()
        else:
            self._selector.show()

        self._auxSigSlider.setMaximum(len(signals)-1)
        if len(signals) > 1:
            self._auxSigSlider.show()
            self._auxSigSlider.setValue(1)
        else:
            self._auxSigSlider.hide()
            self._auxSigSlider.setValue(0)

        self._axis_scales = xscale, yscale
        self._updateImage()
        self._plot.resetZoom()

        self._selector.selectionChanged.connect(self._updateImage)
        self._auxSigSlider.valueChanged.connect(self._sliderIdxChanged)

    def _updateImage(self):
        selection = self._selector.selection()
        auxSigIdx = self._auxSigSlider.value()

        legend = self.__signals_names[auxSigIdx]

        images = [img[selection] for img in self.__signals]
        image = images[auxSigIdx]

        x_axis = self.__x_axis
        y_axis = self.__y_axis

        if x_axis is None and y_axis is None:
            xcalib = NoCalibration()
            ycalib = NoCalibration()
        else:
            if x_axis is None:
                # no calibration
                x_axis = numpy.arange(image.shape[1])
            elif numpy.isscalar(x_axis) or len(x_axis) == 1:
                # constant axis
                x_axis = x_axis * numpy.ones((image.shape[1], ))
            elif len(x_axis) == 2:
                # linear calibration
                x_axis = x_axis[0] * numpy.arange(image.shape[1]) + x_axis[1]

            if y_axis is None:
                y_axis = numpy.arange(image.shape[0])
            elif numpy.isscalar(y_axis) or len(y_axis) == 1:
                y_axis = y_axis * numpy.ones((image.shape[0], ))
            elif len(y_axis) == 2:
                y_axis = y_axis[0] * numpy.arange(image.shape[0]) + y_axis[1]

            xcalib = ArrayCalibration(x_axis)
            ycalib = ArrayCalibration(y_axis)

        self._plot.remove(kind=("scatter", "image",))
        if xcalib.is_affine() and ycalib.is_affine():
            # regular image
            xorigin, xscale = xcalib(0), xcalib.get_slope()
            yorigin, yscale = ycalib(0), ycalib.get_slope()
            origin = (xorigin, yorigin)
            scale = (xscale, yscale)

            self._plot.getXAxis().setScale('linear')
            self._plot.getYAxis().setScale('linear')
            self._plot.addImage(image, legend=legend,
                                origin=origin, scale=scale,
                                replace=True, resetzoom=False)
        else:
            xaxisscale, yaxisscale = self._axis_scales

            if xaxisscale is not None:
                self._plot.getXAxis().setScale(
                    'log' if xaxisscale == 'log' else 'linear')
            if yaxisscale is not None:
                self._plot.getYAxis().setScale(
                    'log' if yaxisscale == 'log' else 'linear')

            scatterx, scattery = numpy.meshgrid(x_axis, y_axis)
            # fixme: i don't think this can handle "irregular" RGBA images
            self._plot.addScatter(numpy.ravel(scatterx),
                                  numpy.ravel(scattery),
                                  numpy.ravel(image),
                                  legend=legend)

        if self.__title:
            title = self.__title
            if len(self.__signals_names) > 1:
                # Append dataset name only when there is many datasets
                title += '\n' + self.__signals_names[auxSigIdx]
        else:
            title = self.__signals_names[auxSigIdx]
        self._plot.setGraphTitle(title)
        self._plot.getXAxis().setLabel(self.__x_axis_name)
        self._plot.getYAxis().setLabel(self.__y_axis_name)

    def clear(self):
        old = self._selector.blockSignals(True)
        self._selector.clear()
        self._selector.blockSignals(old)
        self._plot.clear()
