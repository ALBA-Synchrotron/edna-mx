#
#    Project: EDNA MXv1
#             http://www.edna-site.org
#
#    Copyright (C) 2008-2014 European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal authors:      Marie-Francoise Incardona (incardon@esrf.fr)
#                            Olof Svensson (svensson@esrf.fr) 
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

__authors__ = [ "Olof Svensson", "Marie-Francoise Incardona", "Michael Hellmig" ]
__contact__ = "svensson@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os
import sys
import struct

from EDVerbose      import EDVerbose
from EDMessage      import EDMessage
from EDUtilsImage   import EDUtilsImage

from EDPluginExec import EDPluginExec

from XSDataCommon import XSDataWavelength
from XSDataCommon import XSDataImage
from XSDataCommon import XSDataAngle
from XSDataCommon import XSDataLength
from XSDataCommon import XSDataTime
from XSDataCommon import XSDataString
from XSDataCommon import XSDataInteger

from XSDataMXv1 import XSDataExperimentalCondition
from XSDataMXv1 import XSDataSubWedge
from XSDataMXv1 import XSDataDetector
from XSDataMXv1 import XSDataBeam
from XSDataMXv1 import XSDataGoniostat
from XSDataMXv1 import XSDataInputReadImageHeader
from XSDataMXv1 import XSDataResultReadImageHeader



class EDPluginExecReadImageHeaderPilatus6Mv10(EDPluginExec):


    def __init__(self):
        """
        """
        EDPluginExec.__init__(self)
        self.setXSDataInputClass(XSDataInputReadImageHeader)
        self.__xsDataResultReadImageHeader = None


    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginExecReadImageHeaderPilatus6Mv10.checkParameters")
        self.checkMandatoryParameters(self.getDataInput(), "Data Input is None")


    def process(self, _edObject=None):
        EDPluginExec.process(self)
        self.DEBUG("EDPluginExecReadImageHeaderPilatus6Mv10.process")
        xsDataInputReadImageHeader = self.getDataInput()
        xsDataFile = xsDataInputReadImageHeader.getImage()
        strPath = xsDataFile.getPath().getValue()
        dictPilatus6MHeader = self.readHeaderPilatus6M(strPath)
        if (dictPilatus6MHeader is None):
            strErrorMessage = "EDPluginExecReadImageHeaderPilatus6Mv10.process : Cannot read header : %s" % strPath
            self.error(strErrorMessage)
            self.addErrorMessage(strErrorMessage)
            self.setFailure()
        else:
            xsDataExperimentalCondition = XSDataExperimentalCondition()
            xsDataDetector = XSDataDetector()

            iNoPixelsX = 2463
            iNoPixelsY = 2527
            xsDataDetector.setNumberPixelX(XSDataInteger(iNoPixelsX))
            xsDataDetector.setNumberPixelY(XSDataInteger(iNoPixelsY))
            # Pixel size
            listPixelSizeXY = dictPilatus6MHeader[ "Pixel_size"   ].split(" ")
            fPixelSizeX = float(listPixelSizeXY[0]) * 1000
            xsDataDetector.setPixelSizeX(XSDataLength(fPixelSizeX))
            fPixelSizeY = float(listPixelSizeXY[3]) * 1000
            xsDataDetector.setPixelSizeY(XSDataLength(fPixelSizeY))
            # Beam position
            listBeamPosition = dictPilatus6MHeader["Beam_xy"].replace("(", " ").replace(")", " ").replace(",", " ").split()
            fBeamPositionX = float(listBeamPosition[1]) * fPixelSizeX
            fBeamPositionY = float(listBeamPosition[0]) * fPixelSizeY
            xsDataDetector.setBeamPositionX(XSDataLength(fBeamPositionX))
            xsDataDetector.setBeamPositionY(XSDataLength(fBeamPositionY))
            fDistance = float(dictPilatus6MHeader[ "Detector_distance" ].split(" ")[0]) * 1000
            xsDataDetector.setDistance(XSDataLength(fDistance))
#            xsDataDetector.setNumberBytesInHeader(XSDataInteger(float(dictPilatus6MHeader[ "header_size"   ])))
            xsDataDetector.setSerialNumber(XSDataString(dictPilatus6MHeader[ "Detector:"   ]))
#            #xsDataDetector.setBin(                 XSDataString(   dictPilatus6MHeader[ "BIN" ] ) ) )
#            #xsDataDetector.setDataType(            XSDataString(   dictPilatus6MHeader[ "TYPE" ] ) ) )
#            #xsDataDetector.setByteOrder(           XSDataString(   dictPilatus6MHeader[ "BYTE_ORDER" ] ) ) )
#            xsDataDetector.setImageSaturation(XSDataInteger(int(dictPilatus6MHeader[ "saturation_level" ])))
            #xsDataDetector.setName(XSDataString("PILATUS 6M"))
            xsDataDetector.setName(XSDataString("PILATUS3X 6M"))
            xsDataDetector.setType(XSDataString("pilatus6m"))
            xsDataExperimentalCondition.setDetector(xsDataDetector)

            # Beam object

            xsDataBeam = XSDataBeam()
            xsDataBeam.setWavelength(XSDataWavelength(float(dictPilatus6MHeader[ "Wavelength" ].split(" ")[0])))
            xsDataBeam.setExposureTime(XSDataTime(float(dictPilatus6MHeader[ "Exposure_time" ].split(" ")[0])))
            xsDataExperimentalCondition.setBeam(xsDataBeam)

            # Goniostat object
            xsDataGoniostat = XSDataGoniostat()
            fRotationAxisStart = float(dictPilatus6MHeader[ "Start_angle" ].split(" ")[0])
            fOscillationWidth = float(dictPilatus6MHeader[ "Angle_increment" ].split(" ")[0])
            if "Kappa" in dictPilatus6MHeader.keys():
                fKappa = float(dictPilatus6MHeader[ "Kappa" ].split(" ")[0])
                xsDataGoniostat.setKappa(XSDataAngle(fKappa))
            if "Phi" in dictPilatus6MHeader.keys():
                fPhi = float(dictPilatus6MHeader[ "Phi" ].split(" ")[0])
                xsDataGoniostat.setPhi(XSDataAngle(fPhi))
            xsDataGoniostat.setRotationAxisStart(XSDataAngle(fRotationAxisStart))
            xsDataGoniostat.setRotationAxisEnd(XSDataAngle(fRotationAxisStart + fOscillationWidth))
            xsDataGoniostat.setOscillationWidth(XSDataAngle(fOscillationWidth))
            xsDataExperimentalCondition.setGoniostat(xsDataGoniostat)
#
            # Create the image object
            xsDataImage = XSDataImage()
            xsDataImage.setPath(XSDataString(strPath))
            if "DateTime" in dictPilatus6MHeader:
                strTimeStamp = dictPilatus6MHeader[ "DateTime" ]
                xsDataImage.setDate(XSDataString(strTimeStamp))
            iImageNumber = EDUtilsImage.getImageNumber(strPath)
            xsDataImage.setNumber(XSDataInteger(iImageNumber))

            xsDataSubWedge = XSDataSubWedge()
            xsDataSubWedge.setExperimentalCondition(xsDataExperimentalCondition)
            xsDataSubWedge.addImage(xsDataImage)

            self.__xsDataResultReadImageHeader = XSDataResultReadImageHeader()
            self.__xsDataResultReadImageHeader.setSubWedge(xsDataSubWedge)


    def postProcess(self, _edObject=None):
        EDPluginExec.postProcess(self)
        self.DEBUG("EDPluginExecReadImageHeaderPilatus6Mv10.postProcess")
        if (self.__xsDataResultReadImageHeader is not None):
            self.setDataOutput(self.__xsDataResultReadImageHeader)


    def readHeaderPilatus6M(self, _strImageFileName):
        """
        Returns an dictionary with the contents of a Pilatus 6M CBF image header.
        """
        dictPilatus6M = None
        pyFile = None
        try:
            if sys.version.startswith('3'):
                pyFile = open(_strImageFileName, "r", encoding = "ISO-8859-1")
            else:
                pyFile = open(_strImageFileName, "r")
        except:
            self.ERROR("EDPluginExecReadImageHeaderPilatus6Mv10.readHeaderPilauts6M: couldn't open file: " + _strImageFileName)
            self.setFailure()
        if (pyFile != None):
            self.DEBUG("EDPluginExecReadImageHeaderPilatus6Mv10.readHeaderPilauts6M: Reading header from image " + _strImageFileName)
            pyFile.seek(0, 0)
            bContinue = True
            iMax = 60
            iIndex = 0
            while bContinue:
                strLine = pyFile.readline()
                iIndex += 1
                if (strLine.find("_array_data.header_contents") != -1):
                    dictPilatus6M = {}
                if (strLine.find("_array_data.data") != -1) or iIndex > iMax:
                    bContinue = False
                if (dictPilatus6M != None) and (strLine[0] == "#"):
                    # Check for date
                    strTmp = strLine[2:].replace("\r\n", "")
                    if strLine[6] == "/" and strLine[10] == "/":
                        dictPilatus6M["DateTime"] = strTmp
                    elif strLine[6] == "-" and strLine[9] == "-":
                        # At ALBA, we have the Pilatus 6M writing in the header                                                
                        # the date and time with the following format:                                                         
                        # '%Y-%m-%dT%H:%M:%S.%f'
                        # 2021-12-11T22:18:30.697
                        import datetime
                        dt = datetime.datetime.strptime(strTmp.strip(), '%Y-%m-%dT%H:%M:%S.%f')
                        dictPilatus6M["DateTime"] = dt.strftime('%Y/%b/%d %H:%M:%S.%f')#[:-3]
                    else:
                        strKey = strTmp.split(" ")[0]
                        strValue = strTmp.replace(strKey, "")[1:]
                        dictPilatus6M[strKey] = strValue
            pyFile.close()
        return dictPilatus6M

