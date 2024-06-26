#
#    Project: EDNA MXv1
#             http://www.edna-site.org
#
#    File: "$Id$"
#
#    Copyright (C) 2008-2009 European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal author:       Marie-Francoise Incardona (incardon@esrf.fr)
#
#    Contributing author:    Olof Svensson (svensson@esrf.fr)
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


__authors__ = [ "Marie-Francoise Incardona", "Olof Svensson" ]
__contact__ = "svensson@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

from EDVerbose          import EDVerbose
from EDPluginControl    import EDPluginControl
from EDMessage          import EDMessage



class EDPluginControlInterfacev1_1(EDPluginControl):
    """
    This is the common class to all plugins managing user interfaces
    """

    def __init__ (self):
        EDPluginControl.__init__(self)
        self.__strPluginCharacterisationName = "EDPluginControlCharacterisationv1_1"
        self.__edPluginCharacterisation = None


    def configure(self):
        """
        Gets the configuration parameters (if any).
        """
        EDPluginControl.configure(self)
        self.DEBUG("EDPluginControlInterfacev1_1.configure")
        if self.getControlledPluginName("characterisationPlugin") is not None:
            self.__strPluginCharacterisationName = self.getControlledPluginName("characterisationPlugin")


    def preProcess(self, _edPlugin=None):
        """
        Gets the Configuration Parameters, if found, overrides default parameters
        """
        EDPluginControl.preProcess(self, _edPlugin)
        self.DEBUG("EDPluginControlInterfacev1_1.preProcess...")

        xsDataCollection = self.buildInput()

        self.__edPluginCharacterisation = self.loadPlugin(self.__strPluginCharacterisationName, "Characterisation")
        self.__edPluginCharacterisation.setDataInput(xsDataCollection)


    def checkParameters(self):
        """
        Checks the data input object
        """
        # Checks the mandatory parameters:
        self.checkMandatoryParameters(self.getDataInput(), "Data Input is None")


    def process(self, _edPlugin=None):
        """
        """
        EDPluginControl.process(self, _edPlugin)
        self.DEBUG("EDPluginControlInterfacev1_1.process...")

        if(self.__edPluginCharacterisation is not None):
            self.connectProcess(self.__edPluginCharacterisation.executeSynchronous)
            self.__edPluginCharacterisation.connectSUCCESS(self.doSuccessActionCharacterisation)
            self.__edPluginCharacterisation.connectFAILURE(self.doFailureActionCharacterisation)


    def buildInput(self, _edPlugin=None):
        """
        To be overridden by sub classes. This method should return an XSDataCollection object.
        """
        errorMessage = EDMessage.ERROR_ABSTRACT_METHOD_02 % (self.getPluginName(), 'buildInput')
        self.error(errorMessage)
        self.addErrorMessage(errorMessage)
        raise RuntimeError(errorMessage)


    def postProcess(self, _edPlugin=None):
        """
        """
        EDPluginControl.postProcess(self, _edPlugin)
        self.DEBUG("EDPluginControlInterfacev1_1.postProcess...")


    def doFailureActionCharacterisation(self, _edPlugin=None):
        """
        retrieve the potential warning messages
        retrieve the potential error messages
        """
        self.DEBUG("EDPluginControlInterfacev1_1.doFailureActionCharacterisation")
        self.generateExecutiveSummary(self)
        self.setFailure()


    def doSuccessActionCharacterisation(self, _edPlugin=None):
        """
        retrieve the potential warning messages
        """
        self.DEBUG("EDPluginControlInterfacev1_1.doSuccessActionCharacterisation")
        self.retrieveSuccessMessages(_edPlugin, "EDPluginControlInterfacev1_1.doSuccessActionCharacterisation")


    def generateExecutiveSummary(self, _edPlugin=None):
        """
        Prints the executive summary from the plugin
        """
        self.DEBUG("EDPluginControlInterfacev1_1.generateExecutiveSummary")
        self.addExecutiveSummaryLine("Summary of plugin %s:" % self.__strPluginCharacterisationName)
        if (self.__edPluginCharacterisation is not None):
            self.appendExecutiveSummary(self.__edPluginCharacterisation)
        self.verboseScreenExecutiveSummary()


    def getPluginCharacterisation(self):
        return self.__edPluginCharacterisation
