# coding: utf8
#
#    Project: MX Plugin Exec
#             http://www.edna-site.org
#
#    Copyright (C) ESRF
#
#    Principal author:       Olof Svensson
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

__author__ = "Olof Svensson"
__license__ = "GPLv3+"
__copyright__ = "ESRF"

import os
import time
import shlex
import distro
import pprint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


from EDPluginExecProcessScript import EDPluginExecProcessScript
from EDUtilsTable              import EDUtilsTable
from EDFactoryPluginStatic import EDFactoryPluginStatic
from EDUtilsFile import EDUtilsFile

EDFactoryPluginStatic.loadModule("markupv1_10")
import markupv1_10

from XSDataCommon import XSDataDouble
from XSDataCommon import XSDataString
from XSDataCommon import XSDataFile

from XSDataDnaTables import dna_tables

from XSDataCommon import XSDataInteger
from XSDataCommon import XSDataDouble
from XSDataCommon import XSDataString
from XSDataCommon import XSDataAngle

from XSDataDozorv1_0 import XSDataInputDozor
from XSDataDozorv1_0 import XSDataResultDozor
from XSDataDozorv1_0 import XSDataImageDozor

class EDPluginDozorv1_0(EDPluginExecProcessScript):
    """
    This plugin runs the Dozor program written by Sasha Popov
    """
    

    def __init__(self):
        EDPluginExecProcessScript.__init__(self)
        self.setXSDataInputClass(XSDataInputDozor)
        self.setDataOutput(XSDataResultDozor())
        self.strImageLinkSubDirectory = "img"
        self.defaultFractionPolarization = 0.99
        self.defaultImageStep = 1
        self.startingAngle = 0.0
		### From previous ALBA "production" branch, not in latest Olof version (24-11-2021)
		# self.defaultPixelMean = -1
		# self.defaultPixelMax = 64000
        ###
        self.firstImageNumber = None
        self.oscillationRange = None
        self.overlap = 0.0
        self.ixMin = None
        self.iyMin = None
        self.ixMax = None
        self.iyMax = None
        # Default values for ESRF Pilatus6M id30b: 1,1230; 1228,1298
        # self.ixMinPilatus6m = 1
        # self.ixMaxPilatus6m = 1270
        # self.iyMinPilatus6m = 1190
        # self.iyMaxPilatus6m = 1310
        # Readjusted by rboer and acastellvi for bl13-Xaloc at ALBA
        self.ixMinPilatus6m = 1
        self.ixMaxPilatus6m = 1380
        self.iyMinPilatus6m = 1170
        self.iyMaxPilatus6m = 1410
        
        # Default values for ESRF Pilatus2M : ID30a1: 1,776; 826,894
        self.ixMinPilatus2m = 1 
        self.ixMaxPilatus2m = 840
        self.iyMinPilatus2m = 776
        self.iyMaxPilatus2m = 852
        # Default values for ESRF Eiger4M : ID30a3: 1,1120; 1025,1140
        self.ixMinEiger4m = 1
        self.ixMaxEiger4m = 1120
        self.iyMinEiger4m = 1025
        self.iyMaxEiger4m = 1140
        # Default values for ESRF Eiger16M : ID23eh1: 1, 2159, 2087, 2312
        self.ixMinEiger16m = 1
        self.ixMaxEiger16m = 2159
        self.iyMinEiger16m = 2087
        self.iyMaxEiger16m = 2312
        # Bad zones
        self.strBad_zona = None


    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginDozorv1_0.checkParameters")
        self.checkMandatoryParameters(self.dataInput, "Data Input is None")


    def getLibraryName(self, libraryType, doSubmit=False):
        libraryName = 'library_' + libraryType
        idName, version, codename = distro.linux_distribution()
        #self.screen(f"idName={idName}, version={version}, codename={codename}")
        if 'Debian' in idName:
            libraryName += '_debian_'
        elif idName == 'Ubuntu':
            libraryName += '_ubuntu_'
        elif 'CentOS' in idName:
            libraryName += '_centos_'
        else:
            self.DEBUG('ExecDozor: unknown os name {0}'.format(idName))
            # raise RuntimeError('ExecDozor: unknown os name {0}'.format(idName))
        libraryName += version
        return libraryName

    def configure(self):
        EDPluginExecProcessScript.configure(self)
        self.DEBUG("EDPluginXOalignv1_0.configure")
        self.ixMin = self.config.get("ix_min", None)
        self.iyMin = self.config.get("iy_min", None)
        self.ixMax = self.config.get("ix_max", None)
        self.iyMax = self.config.get("iy_max", None)
        # Eventual bad zones
        self.strBad_zona = self.config.get("bad_zona", None)
        #self.library_cbf = self.config.get(self.getLibraryName("cbf"))
        #self.library_h5 = self.config.get(self.getLibraryName("h5"))
        # ALBA workaround
        self.library_cbf = self.getLibraryName("cbf")
        self.library_h5 = self.getLibraryName("h5")

    def preProcess(self, _edObject=None):
        self.setRequireCCP4(True) # GB: this sets dozor env from execProcessScriptSetupCCP4 config param
        EDPluginExecProcessScript.preProcess(self)
        self.DEBUG("EDPluginDozorv1_0.preProcess")
        xsDataInputDozor = self.getDataInput()
        # First image number and osc range for output angle calculations
        self.firstImageNumber = xsDataInputDozor.firstImageNumber.value
        self.oscillationRange = xsDataInputDozor.oscillationRange.value
        if xsDataInputDozor.overlap is not None:
            self.overlap = xsDataInputDozor.overlap.value
        if xsDataInputDozor.radiationDamage is not None and xsDataInputDozor.radiationDamage.value:
            self.setScriptCommandline(" -pall -rd dozor.dat")
        else:
            self.setScriptCommandline(" -pall -p dozor.dat")
        #self.setScriptCommandline(" dozor.dat")
        strCommands = self.generateCommands(xsDataInputDozor, _library_cbf=self.library_cbf, _library_h5=self.library_h5)
        EDUtilsFile.writeFile(os.path.join(self.getWorkingDirectory(), "dozor.dat"), strCommands)

    def postProcess(self, _edObject=None):
        EDPluginExecProcessScript.postProcess(self)
        self.DEBUG("EDPluginDozorv1_0.postProcess")
        self.dataOutput = self.parseOutput(os.path.join(self.getWorkingDirectory(),
                                                        self.getScriptLogFileName()))



    def generateCommands(self, _xsDataInputDozor, _library_cbf=None, _library_h5=None):
        """
        This method creates the input file for dozor
        """
        self.DEBUG("EDPluginDozorv1_0.generateCommands")
        strCommandText = None
        library = _library_cbf
        if _xsDataInputDozor.detectorType.value == "pilatus2m":
            library = _library_cbf
            nx = 1475
            ny = 1679
            pixel = 0.172
            if self.ixMin is None or self.ixMax is None or self.iyMin is None or self.iyMax is None:
                self.ixMin = self.ixMinPilatus2m
                self.ixMax = self.ixMaxPilatus2m
                self.iyMin = self.iyMinPilatus2m
                self.iyMax = self.iyMaxPilatus2m
        elif _xsDataInputDozor.detectorType.value == "pilatus6m":
            library = _library_cbf
            nx = 2463
            ny = 2527
            pixel = 0.172
            if self.ixMin is None or self.ixMax is None or self.iyMin is None or self.iyMax is None:
                self.ixMin = self.ixMinPilatus6m
                self.ixMax = self.ixMaxPilatus6m
                self.iyMin = self.iyMinPilatus6m
                self.iyMax = self.iyMaxPilatus6m
        elif _xsDataInputDozor.detectorType.value == "eiger4m":
            library = _library_cbf
            nx = 2070
            ny = 2167
            pixel = 0.075
            if self.ixMin is None or self.ixMax is None or self.iyMin is None or self.iyMax is None:
                self.ixMin = self.ixMinEiger4m
                self.ixMax = self.ixMaxEiger4m
                self.iyMin = self.iyMinEiger4m
                self.iyMax = self.iyMaxEiger4m
        elif _xsDataInputDozor.detectorType.value == "eiger16m":
            library = _library_cbf
            nx = 4150
            ny = 4371
            pixel = 0.075
            if self.ixMin is None or self.ixMax is None or self.iyMin is None or self.iyMax is None:
                self.ixMin = self.ixMinEiger16m
                self.ixMax = self.ixMaxEiger16m
                self.iyMin = self.iyMinEiger16m
                self.iyMax = self.iyMaxEiger16m
        elif _xsDataInputDozor.detectorType.value == "eiger2_16m":
            library = _library_cbf
            nx = 4148
            ny = 4362
            pixel = 0.075
            if self.ixMin is None or self.ixMax is None or self.iyMin is None or self.iyMax is None:
                self.ixMin = self.ixMinEiger16m
                self.ixMax = self.ixMaxEiger16m
                self.iyMin = self.iyMinEiger16m
                self.iyMax = self.iyMaxEiger16m
        else:
            raise RuntimeError("Detector type not recognised: {0}".format(_xsDataInputDozor.detectorType.value))
        if _xsDataInputDozor is not None:
            self.setProcessInfo("name template: %s, first image no: %d, no images: %d" % (
                os.path.basename(_xsDataInputDozor.nameTemplateImage.value),
                _xsDataInputDozor.firstImageNumber.value,
                _xsDataInputDozor.numberImages.value))
            #strCommandText = "!\n"
            strCommandText = "job single\n"
            strCommandText += "detector %s\n" % _xsDataInputDozor.detectorType.value
            #strCommandText += "library %s\n" % library
            # ALBA workaround
            #strCommandText += "library /beamlines/bl13/controls/production/software/lib/xds-zcbf.so\n"
            if '_centos_' in library:
                strCommandText += "library /beamlines/bl13/sdm/production/libs/xds-zcbf/centos7/build/xds-zcbf.so\n"
            else: # we assume debian 9, like in ctbl1301
                strCommandText += "library /beamlines/bl13/controls/production/software/lib/xds-zcbf.so\n"
            strCommandText += "nx %d\n" % nx
            strCommandText += "ny %d\n" % ny
            strCommandText += "pixel %f\n" % pixel
            strCommandText += "exposure %.3f\n" % _xsDataInputDozor.exposureTime.value
            strCommandText += "spot_size %d\n" % _xsDataInputDozor.spotSize.value
            strCommandText += "detector_distance %.3f\n" % _xsDataInputDozor.detectorDistance.value
            strCommandText += "X-ray_wavelength %.3f\n" % _xsDataInputDozor.wavelength.value

            #if _xsDataInputDozor.fractionPolarization is None:
            #    fractionPolarization = self.defaultFractionPolarization
            #else:
            #    fractionPolarization = _xsDataInputDozor.fractionPolarization.value
            #strCommandText += "fraction_polarization %.3f\n" % fractionPolarization

            #if _xsDataInputDozor.pixelMin is None:
            #    pixelMin = self.defaultPixelMin
            #else:
            #    pixelMin = _xsDataInputDozor.pixelMin.value
            ##strCommandText += "pixel_min %d\n"%pixelMin
            #strCommandText += "pixel_min 0\n"

            #if _xsDataInputDozor.pixelMax is None:
            #    pixelMax = self.defaultPixelMax
            #else:
            #    pixelMax = _xsDataInputDozor.pixelMax.value
            #strCommandText += "pixel_max %d\n"%pixelMax

            #if None in [ _xsDataInputDozor.ixMin, _xsDataInputDozor.ixMax, 
            #             _xsDataInputDozor.iyMin, _xsDataInputDozor.iyMin] :
            #    strCommandText += "ix_min %d\n" % self.ix_min
            #    strCommandText += "ix_max %d\n" % self.ix_max
            #    strCommandText += "iy_min %d\n" % self.iy_min
            #    strCommandText += "iy_max %d\n" % self.iy_max
            #else:
            #    strCommandText += "ix_min %d\n" % _xsDataInputDozor.ixMin.value
            #    strCommandText += "ix_max %d\n" % _xsDataInputDozor.ixMax.value
            #    strCommandText += "iy_min %d\n" % _xsDataInputDozor.iyMin.value
            #    strCommandText += "iy_max %d\n" % _xsDataInputDozor.iyMax.value
            if self.ixMin is not None:
                strCommandText += "ix_min %d\n" % self.ixMin
                strCommandText += "ix_max %d\n" % self.ixMax
                strCommandText += "iy_min %d\n" % self.iyMin
                strCommandText += "iy_max %d\n" % self.iyMax
            if self.strBad_zona is not None:
                strCommandText += "bad_zona %s\n" % self.strBad_zona

            strCommandText += "orgx %.1f\n" % _xsDataInputDozor.orgx.value
            strCommandText += "orgy %.1f\n" % _xsDataInputDozor.orgy.value
            #strCommandText += "oscillation_range %.3f\n" % _xsDataInputDozor.oscillationRange.value
            #if _xsDataInputDozor.imageStep is None:
            #    imageStep = self.defaultImageStep
            #else:
            #    imageStep = _xsDataInputDozor.imageStep.value
            #strCommandText += "image_step %.3f\n" % imageStep
            #if _xsDataInputDozor.startingAngle is None:
            #    startingAngle = self.defaultStartingAngle
            #else:
            #    startingAngle = _xsDataInputDozor.startingAngle.value
            #strCommandText += "starting_angle %.3f\n" % startingAngle
            strCommandText += "first_image_number %d\n" % _xsDataInputDozor.firstImageNumber.value
            strCommandText += "number_images %d\n" % _xsDataInputDozor.numberImages.value
            ##strCommandText += "name_template_image %s\n" % os.path.join(self.strImageLinkSubDirectory,
            ##                                                            os.path.basename(_xsDataInputDozor.nameTemplateImage.value))
            strCommandText += "name_template_image %s\n" % _xsDataInputDozor.nameTemplateImage.value
            #strCommandText += "end\n"
            
            #strCommandText += "library /beamlines/bl13/controls/production/software/lib/xds-zcbf.so\n"
            #strCommandText += "nx 2463\n"
            #strCommandText += "ny 2527\n"
            #strCommandText += "pixel 0.172\n"
            self.DEBUG("strCommandText: " + strCommandText)
        return strCommandText
    

    def createImageLinks(self, _xsDataInputDozor):
        self.addListCommandPreExecution("rm -rf %s" % (self.strImageLinkSubDirectory))
        self.addListCommandPreExecution("mkdir -p %s" % (self.strImageLinkSubDirectory))
        strTemplate = os.path.basename(_xsDataInputDozor.nameTemplateImage.value)
        strTemplatePrefix, strTemplateSuffix = strTemplate.split("????")
        for index in range(_xsDataInputDozor.numberImages.value):
            iImageNo = _xsDataInputDozor.firstImageNumber.value + index
            strImageName = strTemplatePrefix + "%04d" % iImageNo + strTemplateSuffix
            strSourcePath = os.path.join(os.path.dirname(_xsDataInputDozor.nameTemplateImage.value),
                                           strImageName)
            strTargetPath = os.path.join(self.strImageLinkSubDirectory,
                                       strImageName)
            self.addListCommandPreExecution("ln -s %s %s" % (strSourcePath, strTargetPath))

        
        
  
        
    def parseOutput(self, _strFileName):
        """
        This method parses the output of dozor
        """
        xsDataResultDozor = XSDataResultDozor()
        strOutput = EDUtilsFile.readFile(_strFileName)
        strWorkingDir = os.path.dirname(_strFileName)
        # Skip the four first lines
        self.DEBUG('***** Dozor raw output ***** ')
        self.DEBUG(strOutput)
        listOutput = strOutput.split("\n")[14:]
        for strLine in listOutput:
            xsDataImageDozor = XSDataImageDozor()
            # Remove "|" 
            listLine = shlex.split(strLine.replace("|", " "))
 
### From previous ALBA "production" branch, not in latest Olof version (24-11-2021)
#            #print listLine
#            if listLine != [] and not listLine[0].startswith("-"):
#                xsDataImageDozor.number = XSDataInteger(listLine[0])
#                # Fix for xaloc-ALBA
#                #if listLine[5].startswith("-") or len(listLine) < 11:
#                if len(listLine) < 11:
#                    xsDataImageDozor.spots_num_of = XSDataInteger(listLine[1])
#                    xsDataImageDozor.spots_int_aver = self.parseDouble(listLine[2])
#                    try:
#                        xsDataImageDozor.spots_resolution = self.parseDouble(listLine[3])
#                    except IndexError as e:
#                        xsDataImageDozor.spots_resolution = XSDataDouble(0.0)
#                    xsDataImageDozor.score = XSDataDouble(0.0) #self.parseDouble(listLine[4])
#                else:
#                    xsDataImageDozor.spots_num_of = XSDataInteger(listLine[1])
#                    xsDataImageDozor.spots_int_aver = self.parseDouble(listLine[2])
#                    xsDataImageDozor.spots_resolution = self.parseDouble(listLine[3])
#                    xsDataImageDozor.powder_wilson_scale = self.parseDouble(listLine[4])
#                    xsDataImageDozor.powder_wilson_bfactor = self.parseDouble(listLine[5])
#                    xsDataImageDozor.powder_wilson_resolution = self.parseDouble(listLine[6])
#                    xsDataImageDozor.powder_wilson_correlation = self.parseDouble(listLine[7])
#                    xsDataImageDozor.powder_wilson_rfactor = self.parseDouble(listLine[8])
#                    xsDataImageDozor.score = self.parseDouble(listLine[9])
##                print xsDataImageDozor.marshal()
###
            if len(listLine) > 0 and listLine[0].isdigit():
                xsDataImageDozor = XSDataImageDozor()
                imageNumber = int(listLine[0])
                angle = self.startingAngle + (imageNumber - self.firstImageNumber) * (self.oscillationRange - self.overlap) + self.oscillationRange / 2.0
                xsDataImageDozor.number = XSDataInteger(imageNumber)
                xsDataImageDozor.angle = XSDataAngle(angle)

                xsDataImageDozor.spotsNumOf = XSDataInteger(0)
                xsDataImageDozor.spotsIntAver = XSDataDouble(0)
                xsDataImageDozor.spotsResolution = XSDataDouble(0)
                xsDataImageDozor.mainScore = XSDataDouble(0)
                xsDataImageDozor.spotScore = XSDataDouble(0)
                xsDataImageDozor.visibleResolution = XSDataDouble(40)
                try:
                    # This commented line comes from ALBA production branch, as a fix for the XALOC beamline at ALBA
                    #if len(listLine) < 11:
                    if listLine[5].startswith("-") or len(listLine) < 11:
                        xsDataImageDozor.spotsNumOf = XSDataInteger(listLine[1])
                        xsDataImageDozor.spotsIntAver = self.parseDouble(listLine[2])
                        xsDataImageDozor.spotsRfactor = self.parseDouble(listLine[3])
                        xsDataImageDozor.spotsResolution = self.parseDouble(listLine[4])
                        xsDataImageDozor.mainScore = self.parseDouble(listLine[8])
                        xsDataImageDozor.spotScore = self.parseDouble(listLine[9])
                        xsDataImageDozor.visibleResolution = self.parseDouble(listLine[10])
                    else:
                        xsDataImageDozor.spotsNumOf = XSDataInteger(listLine[1])
                        xsDataImageDozor.spotsIntAver = self.parseDouble(listLine[2])
                        xsDataImageDozor.spotsRfactor = self.parseDouble(listLine[3])
                        xsDataImageDozor.spotsResolution = self.parseDouble(listLine[4])
                        xsDataImageDozor.powderWilsonScale = self.parseDouble(listLine[5])
                        xsDataImageDozor.powderWilsonBfactor = self.parseDouble(listLine[6])
                        xsDataImageDozor.powderWilsonResolution = self.parseDouble(listLine[7])
                        xsDataImageDozor.powderWilsonCorrelation = self.parseDouble(listLine[8])
                        xsDataImageDozor.powderWilsonRfactor = self.parseDouble(listLine[9])
                        xsDataImageDozor.mainScore = self.parseDouble(listLine[10])
                        xsDataImageDozor.spotScore = self.parseDouble(listLine[11])
                        xsDataImageDozor.visibleResolution = self.parseDouble(listLine[12])
                except:
                    pass
                # Dozor spot file
                if strWorkingDir is not None:
                    strSpotFile = os.path.join(strWorkingDir, "%05d.spot" % xsDataImageDozor.number.value)
                    if os.path.exists(strSpotFile):
                        xsDataImageDozor.spotFile = XSDataFile(XSDataString(strSpotFile))
#                #print xsDataImageDozor.marshal()
                xsDataResultDozor.addImageDozor(xsDataImageDozor)
            elif strLine.startswith("h"):
                xsDataResultDozor.halfDoseTime = XSDataDouble(strLine.split("=")[1].split()[0])
        
        # Check if mtv plot file exists
        mtvFileName = "dozor_rd.mtv"
        mtvFilePath = os.path.join(strWorkingDir, mtvFileName)
        if os.path.exists(mtvFilePath):
            xsDataResultDozor.plotmtvFile = XSDataFile(XSDataString(mtvFilePath))
            xsDataResultDozor.pngPlots = self.generatePngPlots(mtvFilePath, strWorkingDir)

        return xsDataResultDozor
        
    def parseDouble(self, _strValue):
        returnValue = None
        try:
            returnValue = XSDataDouble(_strValue)
        except BaseException as ex:
            self.warning("Error when trying to parse '" + _strValue + "': %r" % ex)
        return returnValue
    
    def generatePngPlots(self, _plotmtvFile, _workingDir):
        listXSFile = []
        # Create plot dictionary
        with open(_plotmtvFile) as f:
            listLines = f.readlines()
        dictPlot = None
        plotData = None
        listPlots = []
        index = 0
        while index < len(listLines):
            # print("0" + listLines[index])
            if listLines[index].startswith("$"):
                dictPlot = {}
                dictPlotList = []
                listPlots.append(dictPlot)
                dictPlot["plotList"] = dictPlotList
                index += 1
                dictPlot["name"] = listLines[index].split("'")[1]
                index += 1
                # print(listLines[index])
                while listLines[index].startswith("%"):
                    listLine = listLines[index].split("=")
                    # print(listLine)
                    label = listLine[0][1:].strip()
                    # print("label: " + str([label]))
                    if "'" in listLine[1]:
                        value = listLine[1].split("'")[1]
                    else:
                        value = listLine[1]
                    value = value.replace("\n", "").strip()
                    # print("value: " + str([value]))
                    dictPlot[label] = value
                    index += 1
                    # print(listLines[index])
            elif listLines[index].startswith("#"):
                dictSubPlot = {}
                dictPlotList.append(dictSubPlot)
                plotName = listLines[index].split("#")[1].replace("\n", "").strip()
                dictSubPlot["name"] = plotName
                index += 1
                # print("1" + listLines[index])
                while listLines[index].startswith("%"):
                    listLine = listLines[index].split("=")
                    # print(listLine)
                    label = listLine[0][1:].strip()
                    # print("label: " + str([label]))
                    if "'" in listLine[1]:
                        value = listLine[1].split("'")[1]
                    else:
                        value = listLine[1]
                    value = value.replace("\n", "").strip()
                    # print("value: " + str([value]))
                    dictSubPlot[label] = value
                    index += 1
                    # print(listLines[index])
                dictSubPlot["xValues"] = []
                dictSubPlot["yValues"] = []
            else:
                listData = listLines[index].replace("\n", "").split()
                dictSubPlot["xValues"].append(float(listData[0]))
                dictSubPlot["yValues"].append(float(listData[1]))
                index += 1
        # pprint.pprint(listPlots)
        # Generate the plots
        for mtvplot in listPlots:
            listLegend = []
            xmin = None
            xmax = None
            ymin = None
            ymax = None
            for subPlot in mtvplot["plotList"]:
                xmin1 = min(subPlot["xValues"])
                if xmin is None or xmin > xmin1:
                    xmin = xmin1
                xmax1 = max(subPlot["xValues"])
                if xmax is None or xmax < xmax1:
                    xmax = xmax1
                ymin1 = min(subPlot["yValues"])
                if ymin is None or ymin > ymin1:
                    ymin = ymin1
                ymax1 = max(subPlot["yValues"])
                if ymax is None or ymax < ymax1:
                    ymax = ymax1
            if "xmin" in mtvplot:
                xmin = float(mtvplot["xmin"])
            if "ymin" in mtvplot:
                ymin = float(mtvplot["ymin"])
            plt.xlim(xmin, xmax)
            plt.ylim(ymin, ymax)
            plt.xlabel(mtvplot["xlabel"])
            plt.ylabel(mtvplot["ylabel"])
            plt.title(mtvplot["name"])
            for subPlot in mtvplot["plotList"]:
                if "markercolor" in subPlot:
                    style = "bs-."
                else:
                    style = "r"
                plt.plot(subPlot["xValues"], subPlot["yValues"], style, linewidth=2)
                listLegend.append(subPlot["linelabel"])
            plt.legend(listLegend, loc='lower right')
            plotPath = os.path.join(_workingDir, mtvplot["name"].replace(" ", "").replace(".", "_") + ".png")
            plt.savefig(plotPath, bbox_inches='tight', dpi=75)
            plt.close()
            listXSFile.append(XSDataFile(XSDataString(plotPath)))
        return listXSFile
