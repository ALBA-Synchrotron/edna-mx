#
#    Project: mxPluginExec
#             http://www.edna-site.org
#
#    Copyright (C) 2011-2013 European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal authors:      Olof Svensson (svensson@esrf.fr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    and the GNU Lesser General Public License  along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#


__author__ = "Olof Svensson"
__contact__ = "svensson@esrf.fr"
__license__ = "LGPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "20161109"
__status__ = "production"

import os

from EDFactoryPluginStatic import EDFactoryPluginStatic

from EDPluginISPyBv1_4 import EDPluginISPyBv1_4

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.sax.date import DateTime

from XSDataCommon import XSDataInteger

from XSDataISPyBv1_4 import XSDataInputISPyBSetBestWilsonPlotPath
from XSDataISPyBv1_4 import XSDataResultISPyBSetBestWilsonPlotPath


class EDPluginISPyBSetBestWilsonPlotPathv1_4(EDPluginISPyBv1_4):
    """
    Plugin to store motor positions (for grid scans)
    """

    def __init__(self):
        """
        Sets default values for dbserver parameters 
        """
        EDPluginISPyBv1_4.__init__(self)
        self.setXSDataInputClass(XSDataInputISPyBSetBestWilsonPlotPath)
        self.dataCollectionId = None


    def configure(self):
        """
        Gets the web servise wdsl parameters from the config file and stores them in class member attributes.
        """
        EDPluginISPyBv1_4.configure(self, _bRequireToolsForCollectionWebServiceWsdl=True)


    def process(self, _edObject=None):
        """
        Uses ToolsForCollectionWebService 
        """
        EDPluginISPyBv1_4.process(self)
        self.DEBUG("EDPluginISPyBSetBestWilsonPlotPathv1_4.process")
        httpAuthenticatedToolsForCollectionWebService = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
        clientToolsForCollectionWebService = Client(self.strToolsForCollectionWebServiceWsdl,
                                                    transport=httpAuthenticatedToolsForCollectionWebService,
                                                    cache=None)
        # Loop over all positions
        xsDataInputISPyBSetBestWilsonPlotPath = self.getDataInput()
        iDataCollectionId = self.getXSValue(xsDataInputISPyBSetBestWilsonPlotPath.dataCollectionId)
        strBestWilsonPlotPath = self.getXSValue(xsDataInputISPyBSetBestWilsonPlotPath.bestWilsonPlotPath)
        self.dataCollectionId = clientToolsForCollectionWebService.service.setBestWilsonPlotPath(
                                    arg0=iDataCollectionId, \
                                    bestWilsonPlotPath=strBestWilsonPlotPath, \
                                    )
        self.DEBUG("EDPluginISPyBSetBestWilsonPlotPathv1_4.process: dataCollectionId=%r" % self.dataCollectionId)





    def finallyProcess(self, _edObject=None):
        EDPluginISPyBv1_4.finallyProcess(self)
        self.DEBUG("EDPluginISPyBSetBestWilsonPlotPathv1_4.finallyProcess")
        xsDataResultISPyBSetBestWilsonPlotPath = XSDataResultISPyBSetBestWilsonPlotPath()
        xsDataResultISPyBSetBestWilsonPlotPath.dataCollectionId = XSDataInteger(self.dataCollectionId)
        self.setDataOutput(xsDataResultISPyBSetBestWilsonPlotPath)


    def createMotorPosition3VO(self, _clientToolsForCollectionWebService, _xsDataPosition):
        position3VO = _clientToolsForCollectionWebService.factory.create('motorPosition3VO')
        if _xsDataPosition.gridIndexY is not None:
            position3VO.gridIndexY = _xsDataPosition.gridIndexY.value
        if _xsDataPosition.gridIndexZ is not None:
            position3VO.gridIndexZ = _xsDataPosition.gridIndexZ.value
        position3VO.kappa = _xsDataPosition.kappa.value
        position3VO.omega = _xsDataPosition.omega.value
        position3VO.phi = _xsDataPosition.phi.value
        position3VO.phiX = _xsDataPosition.phiX.value
        position3VO.phiY = _xsDataPosition.phiY.value
        position3VO.phiZ = _xsDataPosition.phiZ.value
        position3VO.sampX = _xsDataPosition.sampX.value
        position3VO.sampY = _xsDataPosition.sampY.value
        return position3VO
