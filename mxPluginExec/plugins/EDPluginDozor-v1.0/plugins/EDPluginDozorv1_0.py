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

import os, time, shlex

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
        self.defaultPixelMean = -1
	self.defaultPixelMax = 64000
        self.ix_min = None
        self.iy_min = None
        self.ix_max = None
        self.iy_max = None
        # Default values for ESRF Pilatus6M
        self.ix_min_pilatus6m = 1 
        self.ix_max_pilatus6m = 1270
        self.iy_min_pilatus6m = 1190
        self.iy_max_pilatus6m = 1310
        # Default values for ESRF Pilatus2M
        self.ix_min_pilatus2m = 1 
        self.ix_max_pilatus2m = 840
        self.iy_min_pilatus2m = 776
        self.iy_max_pilatus2m = 852

    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginDozorv1_0.checkParameters")
        self.checkMandatoryParameters(self.dataInput, "Data Input is None")

    
    def preProcess(self, _edObject=None):
        self.setRequireCCP4(True) # GB: this sets dozor env from execProcessScriptSetupCCP4 config param
        EDPluginExecProcessScript.preProcess(self)
        self.DEBUG("EDPluginDozorv1_0.preProcess")
        xsDataInputDozor = self.getDataInput()
        # Retrieve config (if any)
        self.ix_min = self.config.get("ix_min")
        self.ix_max = self.config.get("ix_max")
        self.iy_min = self.config.get("iy_min")
        self.iy_max = self.config.get("iy_max")
        if self.ix_min is None or self.ix_max is None or self.iy_min is None or self.iy_max is None:
            # One configuration value is missing - use default values
            if xsDataInputDozor.detectorType.value == "pilatus2m":
                self.ix_min = self.ix_min_pilatus2m
                self.ix_max = self.ix_max_pilatus2m
                self.iy_min = self.iy_min_pilatus2m
                self.iy_max = self.iy_max_pilatus2m
            else:
                self.ix_min = self.ix_min_pilatus6m                
                self.ix_max = self.ix_max_pilatus6m
                self.iy_min = self.iy_min_pilatus6m
                self.iy_max = self.iy_max_pilatus6m
        self.setScriptCommandline(" dozor.dat")
        strCommands = self.generateCommands(xsDataInputDozor)
        #self.createImageLinks(xsDataInputDozor)
        EDUtilsFile.writeFile(os.path.join(self.getWorkingDirectory(), "dozor.dat"), strCommands)


    def postProcess(self, _edObject=None):
        EDPluginExecProcessScript.postProcess(self)
        self.DEBUG("EDPluginDozorv1_0.postProcess")
        self.dataOutput = self.parseOutput(os.path.join(self.getWorkingDirectory(),
                                                        self.getScriptLogFileName()))


    
    def generateCommands(self, _xsDataInputDozor):
        """
        This method creates the input file for dozor
        """
        self.DEBUG("EDPluginDozorv1_0.generateCommands")
        strCommandText = None
        if _xsDataInputDozor is not None:
            self.setProcessInfo("first image no %d" % _xsDataInputDozor.firstImageNumber.value)
            strCommandText = "job single\n"
            #strCommandText += "detector %s\n" % _xsDataInputDozor.detectorType.value
            #strCommandText += "exposure %.3f\n" % _xsDataInputDozor.exposureTime.value
            #strCommandText += "spot_size %d\n" % _xsDataInputDozor.spotSize.value
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

            if None in [ _xsDataInputDozor.ixMin, _xsDataInputDozor.ixMax, 
                         _xsDataInputDozor.iyMin, _xsDataInputDozor.iyMin] :
                strCommandText += "ix_min %d\n" % self.ix_min
                strCommandText += "ix_max %d\n" % self.ix_max
                strCommandText += "iy_min %d\n" % self.iy_min
                strCommandText += "iy_max %d\n" % self.iy_max
            else:
                strCommandText += "ix_min %d\n" % _xsDataInputDozor.ixMin.value
                strCommandText += "ix_max %d\n" % _xsDataInputDozor.ixMax.value
                strCommandText += "iy_min %d\n" % _xsDataInputDozor.iyMin.value
                strCommandText += "iy_max %d\n" % _xsDataInputDozor.iyMax.value

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
            
            strCommandText += "library //beamlines/bl13/controls/production/software/lib/xds-zcbf.so\n"
            strCommandText += "nx 2463\n"
            strCommandText += "ny 2527\n"
            strCommandText += "pixel 0.172\n"
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
        # Skip the four first lines
        self.DEBUG('***** Dozor raw output ***** ')
        self.DEBUG(strOutput)
        listOutput = strOutput.split("\n")[14:]
        for strLine in listOutput:
            xsDataImageDozor = XSDataImageDozor()
            # Remove "|" 
            listLine = shlex.split(strLine.replace("|", " "))
            #print listLine
            if listLine != [] and not listLine[0].startswith("-"):
                xsDataImageDozor.number = XSDataInteger(listLine[0])
                # Fix for xaloc-ALBA
                #if listLine[5].startswith("-") or len(listLine) < 11:
                if len(listLine) < 11:
                    xsDataImageDozor.spots_num_of = XSDataInteger(listLine[1])
                    xsDataImageDozor.spots_int_aver = self.parseDouble(listLine[2])
                    try:
                        xsDataImageDozor.spots_resolution = self.parseDouble(listLine[3])
                    except IndexError as e:
                        xsDataImageDozor.spots_resolution = XSDataDouble(0.0)
                    xsDataImageDozor.score = XSDataDouble(0.0) #self.parseDouble(listLine[4])
                else:
                    xsDataImageDozor.spots_num_of = XSDataInteger(listLine[1])
                    xsDataImageDozor.spots_int_aver = self.parseDouble(listLine[2])
                    xsDataImageDozor.spots_resolution = self.parseDouble(listLine[3])
                    xsDataImageDozor.powder_wilson_scale = self.parseDouble(listLine[4])
                    xsDataImageDozor.powder_wilson_bfactor = self.parseDouble(listLine[5])
                    xsDataImageDozor.powder_wilson_resolution = self.parseDouble(listLine[6])
                    xsDataImageDozor.powder_wilson_correlation = self.parseDouble(listLine[7])
                    xsDataImageDozor.powder_wilson_rfactor = self.parseDouble(listLine[8])
                    xsDataImageDozor.score = self.parseDouble(listLine[9])
#                print xsDataImageDozor.marshal()
                xsDataResultDozor.addImageDozor(xsDataImageDozor)
        return xsDataResultDozor
        
    def parseDouble(self, _strValue):
        returnValue = None
        try:
            returnValue = XSDataDouble(_strValue)
        except BaseException as ex:
            self.warning("Error when trying to parse '" + _strValue + "': %r" % ex)
        return returnValue
