#
#    Project: EDNA MXv1
#             http://www.edna-site.org
#
#    File: "$Id: EDPluginControlISPyBv2_0.py 2150 2010-10-12 07:20:56Z svensson $"
#
#    Copyright (C) 2008-2010 European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal authors:      Olof Svensson (svensson@esrf.fr)
#                            Karl Levik (karl.levik@diamond.ac.uk)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__author__ = "Olof Svensson, Karl Levik"
__contact__ = "svensson@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

from EDVerbose          import EDVerbose
from EDPluginControl    import EDPluginControl
from EDMessage          import EDMessage
from XSDataMXv1         import XSDataInputControlISPyB
from XSDataMXv1         import XSDataResultControlISPyB
from XSDataCommon       import XSDataString

class EDPluginControlISPyBv2_0(EDPluginControl):
    """
    This plugin controls the ISPyB execution plugin.
    """

    def __init__ (self):
        """
        """
        EDPluginControl.__init__(self)
        self.setXSDataInputClass(XSDataInputControlISPyB)
        self.setXSDataInputClass(XSDataString, "shortComments")
        self.setXSDataInputClass(XSDataString, "comments")
        self.setXSDataInputClass(XSDataString, "statusMessage")
        self.m_edStringPluginExecISPyBName = "EDPluginISPyBv1_2"
        self.m_edPluginExecISPyB = None
        self.__strShortComments = None
        self.__strComments = None
        self.__strStatusMessage = None


    def checkParameters(self):
        """
        Checks the mandatory parameters
        """
        self.DEBUG("EDPluginControlISPyBv2_0.checkParameters")
        self.checkMandatoryParameters(self.getDataInput(), "Data Input is None")
        self.checkMandatoryParameters(self.getDataInput().getCharacterisationResult(), "characterisationResult")


    def preProcess(self, _edObject=None):
        """
        Loads the ISPyB execution plugin and prepares the input data
        """
        EDPluginControl.preProcess(self, _edObject)
        self.DEBUG("EDPluginControlISPyBv2_0.preProcess...")

        if (self.hasDataInput("shortComments")):
            self.__strShortComments = self.getDataInput("shortComments")[0].getValue()
        if (self.hasDataInput("comments")):
            self.__strComments = self.getDataInput("comments")[0].getValue()
        if (self.hasDataInput("statusMessage")):
            self.__strStatusMessage = self.getDataInput("statusMessage")[0].getValue()

        self.m_edPluginExecISPyB = self.loadPlugin(self.m_edStringPluginExecISPyBName)
        from EDHandlerXSDataISPyBv2_0 import EDHandlerXSDataISPyBv2_0
        xsDataInputISPyB = None
        xsDataISPyBImage = None
        #try:
        if 1==1:
            xsDataISPyBScreening = EDHandlerXSDataISPyBv2_0.generateXSDataISPyBScreening(self.getDataInput(), self.__strShortComments, self.__strComments)
            xsDataISPyBScreeningInput = EDHandlerXSDataISPyBv2_0.generateXSDataISPyBScreeningInput(self.getDataInput())
            xsDataISPyBScreeningOutputContainer = EDHandlerXSDataISPyBv2_0.generateXSDataISPyBScreeningOutputContainer(self.getDataInput(), self.__strStatusMessage)
            if (xsDataISPyBScreening.getDataCollectionId() is None):
                xsDataISPyBImage = EDHandlerXSDataISPyBv2_0.generateXSDataISPyBImage(self.getDataInput())

        if 1==0:
        #except Exception as error:
            # This exception handling needs to be rethought, see bug #43.
            errorMessage = EDMessage.ERROR_DATA_HANDLER_02 % ("EDPluginControlISPyBv2_0.preProcess: Unexpected error in ISPyB handler: ", error)
            self.error(errorMessage)
            self.addErrorMessage(errorMessage)
            raise RuntimeError(errorMessage)

        self.m_edPluginExecISPyB.setDataInput(xsDataISPyBScreening, "screening")
        self.m_edPluginExecISPyB.setDataInput(xsDataISPyBScreeningInput, "screeningInput")
        self.m_edPluginExecISPyB.setDataInput(xsDataISPyBScreeningOutputContainer, "screeningOutputContainer")
        if (xsDataISPyBScreening.getDataCollectionId() is None):
            self.m_edPluginExecISPyB.setDataInput(xsDataISPyBImage, "image")


    def process(self, _edObject=None):
        """
        Executes the ISPyB execution plugin
        """
        EDPluginControl.process(self, _edObject)
        self.DEBUG("EDPluginControlISPyBv2_0.process")
        if (self.m_edPluginExecISPyB is not None):
            self.m_edPluginExecISPyB.connectSUCCESS(self.doSuccessGeneratePrediction)
            self.m_edPluginExecISPyB.connectFAILURE(self.doFailureGeneratePrediction)
            self.m_edPluginExecISPyB.executeSynchronous()


    def doSuccessGeneratePrediction(self, _edPlugin=None):
        self.DEBUG("EDPluginControlISPyBv2_0.doSuccessGeneratePrediction")
        self.retrieveSuccessMessages(self.m_edPluginExecISPyB, "EDPluginControlISPyBv2_0.doSuccessGeneratePrediction")


    def doFailureGeneratePrediction(self, _edPlugin=None):
        self.DEBUG("EDPluginControlISPyBv2_0.doFailureGeneratePrediction")
        self.retrieveFailureMessages(_edPlugin, "EDPluginControlISPyBv2_0.doFailureGeneratePrediction")


    def postProcess(self, _edPlugin=None):
        self.DEBUG("EDPluginControlISPyBv2_0.postProcess")
        # For the moment just an empty result object
        xsDataResultControlISPyB = XSDataResultControlISPyB()
        self.setDataOutput(xsDataResultControlISPyB)


