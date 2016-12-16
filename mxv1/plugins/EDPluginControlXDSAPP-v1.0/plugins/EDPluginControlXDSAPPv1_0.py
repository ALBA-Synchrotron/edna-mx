# coding: utf8
#
#    Project: autoPROC
#             http://www.edna-site.org
#
#    Copyright (C) ESRF
#
#    Principal authors: Thomas Boeglin and Olof Svensson
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
__license__ = "GPLv2+"
__copyright__ = "ESRF"

import os
import sys
import gzip
import time
import shutil
import socket
import subprocess

from EDPluginControl import EDPluginControl
from EDHandlerESRFPyarchv1_0 import EDHandlerESRFPyarchv1_0
from EDUtilsPath import EDUtilsPath
from EDUtilsFile import EDUtilsFile

from EDFactoryPlugin import edFactoryPlugin

from XSDataCommon import XSDataFile
from XSDataCommon import XSDataBoolean
from XSDataCommon import XSDataString
from XSDataCommon import XSDataInteger
from XSDataCommon import XSDataTime
from XSDataCommon import XSDataDouble

from XSDataControlXDSAPPv1_0 import XSDataInputControlXDSAPP
from XSDataControlXDSAPPv1_0 import XSDataResultControlXDSAPP

edFactoryPlugin.loadModule('XSDataXDSAPPv1_0')

from XSDataXDSAPPv1_0 import XSDataInputXDSAPP

edFactoryPlugin.loadModule('XSDataISPyBv1_4')
# plugin input/output
from XSDataISPyBv1_4 import AutoProc
from XSDataISPyBv1_4 import Image
from XSDataISPyBv1_4 import AutoProcProgram
from XSDataISPyBv1_4 import AutoProcContainer
from XSDataISPyBv1_4 import AutoProcIntegration
from XSDataISPyBv1_4 import AutoProcScaling
from XSDataISPyBv1_4 import AutoProcScalingContainer
from XSDataISPyBv1_4 import AutoProcScalingStatistics
from XSDataISPyBv1_4 import AutoProcIntegrationContainer
from XSDataISPyBv1_4 import AutoProcProgramContainer
from XSDataISPyBv1_4 import AutoProcProgramAttachment
from XSDataISPyBv1_4 import XSDataInputRetrieveDataCollection
from XSDataISPyBv1_4 import XSDataInputStoreAutoProc
from XSDataISPyBv1_4 import XSDataResultStoreAutoProc


edFactoryPlugin.loadModule("XSDataMXWaitFilev1_1")
from XSDataMXWaitFilev1_1 import XSDataInputMXWaitFile

edFactoryPlugin.loadModule("XSDataHTML2PDFv1_0")
from XSDataHTML2PDFv1_0 import XSDataInputHTML2PDF

class EDPluginControlXDSAPPv1_0(EDPluginControl):
    """
    Control plugin for xia2 -dials
    """


    def __init__(self):
        EDPluginControl.__init__(self)
        self.setXSDataInputClass(XSDataInputControlXDSAPP)
        self.dataOutput = XSDataResultStoreAutoProc()
        self.doAnomAndNonanom = True
        self.pyarchPrefix = None
        self.resultsDirectory = None
        self.pyarchDirectory = None

    def configure(self):
        EDPluginControl.configure(self)

    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginControlXDSAPPv1_0.checkParameters")
        self.checkMandatoryParameters(self.dataInput, "Data Input is None")
        self.checkMandatoryParameters(self.dataInput.dataCollectionId, "No data collection id")


    def preProcess(self, _edObject=None):
        EDPluginControl.preProcess(self)
        self.DEBUG("EDPluginControlXDSAPPv1_0.preProcess")
        self.screen("XDSAPP processing started")

        if self.dataInput.doAnomAndNonanom is not None:
            if self.dataInput.doAnomAndNonanom.value:
                self.doAnomAndNonanom = True
            else:
                self.doAnomAndNonanom = False

        self.strHost = socket.gethostname()
        self.screen("Running on {0}".format(self.strHost))
        try:
            strLoad = os.getloadavg()
            self.screen("System load avg: {0}".format(strLoad))
        except OSError:
            pass

        self.edPluginWaitFileFirst = self.loadPlugin("EDPluginMXWaitFilev1_1", "MXWaitFileFirst")
        self.edPluginWaitFileLast = self.loadPlugin("EDPluginMXWaitFilev1_1", "MXWaitFileLast")

        self.edPluginRetrieveDataCollection = self.loadPlugin("EDPluginISPyBRetrieveDataCollectionv1_4")
        self.edPluginExecXDSAPPAnom = self.loadPlugin("EDPluginExecXDSAPPv1_0", "EDPluginExecXDSAPPv1_0_anom")
        if self.doAnomAndNonanom:
            self.edPluginExecXDSAPPNoanom = self.loadPlugin("EDPluginExecXDSAPPv1_0", "EDPluginExecXDSAPPv1_0_noanom")


    def process(self, _edObject=None):
        EDPluginControl.process(self)
        self.DEBUG('EDPluginControlXDSAPPv1_0.process starting')

        directory = None
        template = None
        imageNoStart = None
        imageNoEnd = None
        pathToStartImage = None
        pathToEndImage = None
        userName = os.environ["USER"]
        beamline = "unknown"
        proposal = "unknown"

        # If we have a data collection id, use it
        if self.dataInput.dataCollectionId is not None:
            # Recover the data collection from ISPyB
            xsDataInputRetrieveDataCollection = XSDataInputRetrieveDataCollection()
            identifier = str(self.dataInput.dataCollectionId.value)
            xsDataInputRetrieveDataCollection.dataCollectionId = self.dataInput.dataCollectionId
            self.edPluginRetrieveDataCollection.dataInput = xsDataInputRetrieveDataCollection
            self.edPluginRetrieveDataCollection.executeSynchronous()
            ispybDataCollection = self.edPluginRetrieveDataCollection.dataOutput.dataCollection
            directory = ispybDataCollection.imageDirectory
            template = ispybDataCollection.fileTemplate.replace("%04d", "####")
            imageNoStart = ispybDataCollection.startImageNumber
            imageNoEnd = imageNoStart + ispybDataCollection.numberOfImages - 1

#            # DEBUG we set the end image to 20 in order to speed up things
#            self.warning("End image set to 20 (was {0})".format(imageNoEnd))
#            imageNoEnd = 20
            pathToStartImage = os.path.join(directory, ispybDataCollection.fileTemplate % imageNoStart)
            pathToEndImage = os.path.join(directory, ispybDataCollection.fileTemplate % imageNoEnd)
        else:
            identifier = str(int(time.time()))
            directory = self.dataInput.dirN.value
            template = self.dataInput.templateN.value
            imageNoStart = self.dataInput.fromN.value
            imageNoEnd = self.dataInput.toN.value
            fileTemplate = template.replace("####", "%04d")
            pathToStartImage = os.path.join(directory, fileTemplate % imageNoStart)
            pathToEndImage = os.path.join(directory, fileTemplate % imageNoEnd)

        # Try to get proposal from path
        if EDUtilsPath.isESRF():
            listDirectory = directory.split(os.sep)
            try:
                if listDirectory[1] == "data":
                    if listDirectory[2] == "visitor":
                        beamline = listDirectory[4]
                        proposal = listDirectory[3]
                    else:
                        beamline = listDirectory[2]
                        proposal = listDirectory[4]
            except:
                beamline = "unknown"
                proposal = userName


        if imageNoEnd - imageNoStart < 8:
            error_message = "There are fewer than 8 images, aborting"
            self.addErrorMessage(error_message)
            self.ERROR(error_message)
            self.setFailure()
            return

        # Process directory
        if self.dataInput.processDirectory is not None:
            processDirectory = self.dataInput.processDirectory.path.value
        else:
            processDirectory = directory.replace("RAW_DATA", "PROCESSED_DATA")

        isH5 = False
        if any(beamline in pathToStartImage for beamline in ["id23eh1", "id29"]):
            minSizeFirst = 6000000
            minSizeLast = 6000000
        elif any(beamline in pathToStartImage for beamline in ["id23eh2", "id30a1"]):
            minSizeFirst = 2000000
            minSizeLast = 2000000
        elif any(beamline in pathToStartImage for beamline in ["id30a3"]):
            minSizeFirst = 100000
            minSizeLast = 100000
            pathToStartImage = os.path.join(directory,
                                            self.eiger_template_to_image(template, imageNoStart))
            pathToEndImage = os.path.join(directory,
                                          self.eiger_template_to_image(template, imageNoEnd))
            isH5 = True
        else:
            minSizeFirst = 1000000
            minSizeLast = 1000000

        fWaitFileTimeout = 3600  # s

        xsDataInputMXWaitFileFirst = XSDataInputMXWaitFile()
        xsDataInputMXWaitFileFirst.file = XSDataFile(XSDataString(pathToStartImage))
        xsDataInputMXWaitFileFirst.timeOut = XSDataTime(fWaitFileTimeout)
        self.edPluginWaitFileFirst.size = XSDataInteger(minSizeFirst)
        self.edPluginWaitFileFirst.dataInput = xsDataInputMXWaitFileFirst
        self.edPluginWaitFileFirst.executeSynchronous()
        if self.edPluginWaitFileFirst.dataOutput.timedOut.value:
            strWarningMessage = "Timeout after %d seconds waiting for the first image %s!" % (fWaitFileTimeout, pathToStartImage)
            self.addWarningMessage(strWarningMessage)
            self.WARNING(strWarningMessage)

        xsDataInputMXWaitFileLast = XSDataInputMXWaitFile()
        xsDataInputMXWaitFileLast.file = XSDataFile(XSDataString(pathToEndImage))
        xsDataInputMXWaitFileLast.timeOut = XSDataTime(fWaitFileTimeout)
        self.edPluginWaitFileLast.size = XSDataInteger(minSizeLast)
        self.edPluginWaitFileLast.dataInput = xsDataInputMXWaitFileLast
        self.edPluginWaitFileLast.executeSynchronous()
        if self.edPluginWaitFileLast.dataOutput.timedOut.value:
            strErrorMessage = "Timeout after %d seconds waiting for the last image %s!" % (fWaitFileTimeout, pathToEndImage)
            self.addErrorMessage(strErrorMessage)
            self.ERROR(strErrorMessage)
            self.setFailure()



        # Prepare input to execution plugin
        xsDataInputXDSAPPAnom = XSDataInputXDSAPP()
        xsDataInputXDSAPPAnom.anomalous = XSDataBoolean(False)
        xsDataInputXDSAPPAnom.image = XSDataFile(XSDataString(pathToStartImage))
        if self.doAnomAndNonanom:
            xsDataInputXDSAPPNoanom = XSDataInputXDSAPP()
            xsDataInputXDSAPPNoanom.anomalous = XSDataBoolean(True)
            xsDataInputXDSAPPNoanom.image = XSDataFile(XSDataString(pathToStartImage))
#        if isH5:
#            masterFilePath = os.path.join(directory,
#                                          self.eiger_template_to_master(template))
#            xsDataInputXDSAPPAnom.addImage(XSDataFile(XSDataString(masterFilePath)))
#            if self.doAnomAndNonanom:
#                xsDataInputXDSAPPNoanom.addImage(XSDataFile(XSDataString(masterFilePath)))
#        else:
#            xsDataInputXDSAPPAnom.addImage(XSDataFile(XSDataString(pathToStartImage)))
#            if self.doAnomAndNonanom:
#                xsDataInputXDSAPPNoanom.addImage(XSDataFile(XSDataString(pathToStartImage)))
        timeStart = time.localtime()
        self.edPluginExecXDSAPPAnom.dataInput = xsDataInputXDSAPPAnom
        self.edPluginExecXDSAPPAnom.execute()
        if self.doAnomAndNonanom:
            self.edPluginExecXDSAPPNoanom.dataInput = xsDataInputXDSAPPNoanom
            self.edPluginExecXDSAPPNoanom.execute()
        self.edPluginExecXDSAPPAnom.synchronize()
        strPathXscaleLpAnom = self.runXscale(self.edPluginExecXDSAPPAnom.getWorkingDirectory(), anom=True, merged=True)
        xsDataResultXDSAPPAnom = self.edPluginExecXDSAPPAnom.dataOutput
        if self.doAnomAndNonanom:
            self.edPluginExecXDSAPPNoanom.synchronize()
            strPathXscaleLpNoanom = self.runXscale(self.edPluginExecXDSAPPNoanom.getWorkingDirectory(), anom=False, merged=True)
            xsDataResultXDSAPPNoanom = self.edPluginExecXDSAPPNoanom.dataOutput
        timeEnd = time.localtime()

        # Upload to ISPyB
        if self.dataInput.dataCollectionId is not None:
            self.uploadToISPyB(xsDataResultXDSAPPAnom, processDirectory, template,
                               strPathXscaleLpAnom, True, proposal, timeStart, timeEnd,
                               self.dataInput.dataCollectionId.value)
            if self.doAnomAndNonanom:
                self.uploadToISPyB(xsDataResultXDSAPPNoanom, processDirectory, template,
                                   strPathXscaleLpNoanom, False, proposal, timeStart, timeEnd,
                                   self.dataInput.dataCollectionId.value)


    def uploadToISPyB(self, xsDataResultXDSAPP, processDirectory, template,
                      strPathXscaleLp, isAnom, proposal, timeStart, timeEnd, dataCollectionId):

        # Parse log file
        dictLog = self.parseLogFile(xsDataResultXDSAPP.logFile.path.value)
        dictXscale = self.parseXscaleLp(strPathXscaleLp)

        # Make results directory
        resultsDirectory = os.path.join(processDirectory, "results")
        if not os.path.exists(resultsDirectory):
            os.makedirs(resultsDirectory, 0o755)

        # Create path to pyarch
        self.pyarchDirectory = EDHandlerESRFPyarchv1_0.createPyarchFilePath(resultsDirectory)
        self.pyarchDirectory = self.pyarchDirectory.replace('PROCESSED_DATA', 'RAW_DATA')
        if self.pyarchDirectory is not None and not os.path.exists(self.pyarchDirectory):
            os.makedirs(self.pyarchDirectory, 0o755)

        # Determine pyarch prefix
        listPrefix = template.split("_")
        self.pyarchPrefix = "xa_{0}_run{1}".format(listPrefix[-3], listPrefix[-2])

        # Result file directory
        self.strResultPath = os.path.join(processDirectory, "results")
        if not os.path.exists(self.strResultPath):
            os.makedirs(self.strResultPath, 0o755)


        xsDataInputStoreAutoProc = XSDataInputStoreAutoProc()
        autoProcContainer = AutoProcContainer()


        # AutoProc
        autoProc = AutoProc()
        autoProc.spaceGroup = dictLog["spaceGroup"]
        autoProc.refinedCell_a = dictLog["cellA"]
        autoProc.refinedCell_b = dictLog["cellB"]
        autoProc.refinedCell_c = dictLog["cellC"]
        autoProc.refinedCell_alpha = dictLog["cellAlpha"]
        autoProc.refinedCell_beta = dictLog["cellBeta"]
        autoProc.refinedCell_gamma = dictLog["cellGamma"]
        autoProcContainer.AutoProc = autoProc

        # AutoProcIntegrationContainer
        autoProcIntegrationContainer = AutoProcIntegrationContainer()
        autoProcIntegration = AutoProcIntegration()
        autoProcIntegration.cell_a = dictLog["cellA"]
        autoProcIntegration.cell_b = dictLog["cellB"]
        autoProcIntegration.cell_c = dictLog["cellC"]
        autoProcIntegration.cell_alpha = dictLog["cellAlpha"]
        autoProcIntegration.cell_beta = dictLog["cellBeta"]
        autoProcIntegration.cell_gamma = dictLog["cellGamma"]
        autoProcIntegration.anomalous = isAnom

        image = Image()
        image.dataCollectionId = dataCollectionId
        autoProcIntegrationContainer.AutoProcIntegration = autoProcIntegration
        autoProcIntegrationContainer.Image = image


        # Scaling container
        autoProcScalingContainer = AutoProcScalingContainer()
        autoProcScaling = AutoProcScaling()
        autoProcScaling.recordTimeStamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        autoProcScalingContainer.AutoProcScaling = autoProcScaling
        for scalingStatisticsType in dictXscale:
            autoProcScalingStatistics = AutoProcScalingStatistics()
            autoProcScalingStatistics.scalingStatisticsType = scalingStatisticsType
            autoProcScalingStatistics.anomalous = isAnom
            for scalingStatisticsAttribute in dictXscale[scalingStatisticsType]:
                setattr(autoProcScalingStatistics, scalingStatisticsAttribute, dictXscale[scalingStatisticsType][scalingStatisticsAttribute])
            autoProcScalingContainer.addAutoProcScalingStatistics(autoProcScalingStatistics)
        autoProcScalingContainer.AutoProcIntegrationContainer = autoProcIntegrationContainer
        autoProcContainer.AutoProcScalingContainer = autoProcScalingContainer

        # Program
        autoProcProgramContainer = AutoProcProgramContainer()
        autoProcProgram = AutoProcProgram()
        autoProcProgram.processingCommandLine = ' '.join(sys.argv)
        autoProcProgram.processingPrograms = "XDSAPP"
        autoProcProgram.processingStatus = "true"
        autoProcProgram.processingStartTime = time.strftime("%a %b %d %H:%M:%S %Y", timeStart)
        autoProcProgram.processingEndTime = time.strftime("%a %b %d %H:%M:%S %Y", timeEnd)
        autoProcProgramContainer.AutoProcProgram = autoProcProgram

        # Attached files
        pyarchPath = EDHandlerESRFPyarchv1_0.createPyarchFilePath(processDirectory)
        pyarchResultPath = os.path.join(pyarchPath, "results")
        if not os.path.exists(pyarchResultPath):
            os.makedirs(pyarchResultPath, 0o755)

        # XDSAPP log and result files
        if xsDataResultXDSAPP.logFile is not None:
            self.addAttachment(autoProcProgramContainer, xsDataResultXDSAPP.logFile.path.value,
                               "xdsapp", "log", isAnom, attachmentType="Log")
        if xsDataResultXDSAPP.pointlessLog is not None:
            self.addAttachment(autoProcProgramContainer, xsDataResultXDSAPP.pointlessLog.path.value,
                               "pointless", "log", isAnom, attachmentType="Log")
        if xsDataResultXDSAPP.phenixXtriageLog is not None:
            self.addAttachment(autoProcProgramContainer, xsDataResultXDSAPP.phenixXtriageLog.path.value,
                               "xtriage", "log", isAnom, attachmentType="Log")
        if xsDataResultXDSAPP.XDS_ASCII_HKL is not None:
            self.addAttachment(autoProcProgramContainer, xsDataResultXDSAPP.XDS_ASCII_HKL.path.value,
                               "XDS_ASCII", "HKL", isAnom, attachmentType="Result", doGzip=True)
        for mtz_F in xsDataResultXDSAPP.mtz_F:
            basenameMtz_F = os.path.splitext(os.path.basename(mtz_F.path.value))[0]
            self.addAttachment(autoProcProgramContainer, mtz_F.path.value,
                               basenameMtz_F, "mtz", isAnom, attachmentType="Result")
        for mtz_F_plus_F_minus in xsDataResultXDSAPP.mtz_F_plus_F_minus:
            basenameMtz_F_plus_F_minus = os.path.splitext(os.path.basename(mtz_F_plus_F_minus.path.value))[0]
            self.addAttachment(autoProcProgramContainer, mtz_F_plus_F_minus.path.value,
                               basenameMtz_F_plus_F_minus, "mtz", isAnom, attachmentType="Result")
#        for mtz_I in xsDataResultXDSAPP.mtz_I:
#            basenameMtz_I = os.path.splitext(os.path.basename(mtz_I.path.value))[0]
#            self.addAttachment(autoProcProgramContainer, mtz_I.path.value,
#                               basenameMtz_I, "mtz", isAnom, attachmentType="Result")
#        for hkl in xsDataResultXDSAPP.hkl:
#            basenameHkl = os.path.splitext(os.path.basename(hkl.path.value))[0]
#            self.addAttachment(autoProcProgramContainer, hkl.path.value,
#                               basenameHkl, "hkl", isAnom, attachmentType="Result", doGzip=True)
#        for cv in xsDataResultXDSAPP.cv:
#            basenameCv = os.path.splitext(os.path.basename(cv.path.value))[0]
#            self.addAttachment(autoProcProgramContainer, cv.path.value,
#                               basenameCv, "cv", isAnom, attachmentType="Result", doGzip=True)

        if os.path.exists(strPathXscaleLp):
            self.addAttachment(autoProcProgramContainer, strPathXscaleLp,
                               "XSCALE", "LP", isAnom, isMerged=True, attachmentType="Result")
        autoProcContainer.AutoProcProgramContainer = autoProcProgramContainer
        xsDataInputStoreAutoProc.AutoProcContainer = autoProcContainer
        if isAnom:
            anomString = "anom"
        else:
            anomString = "noanom"
        edPluginStoreAutoproc = self.loadPlugin("EDPluginISPyBStoreAutoProcv1_4", "EDPluginISPyBStoreAutoProcv1_4_{0}".format(anomString))
        edPluginStoreAutoproc.dataInput = xsDataInputStoreAutoProc
        edPluginStoreAutoproc.executeSynchronous()


    def addAttachment(self, autoProcProgramContainer, strPath, name, suffix, isAnom=True,
                      isMerged=None, attachmentType="Log", doGzip=False):
        if isAnom:
            anomString = "_anom"
        else:
            anomString = "_noanom"
        if isMerged is not None:
            if isMerged:
                mergeString = "_merged"
            else:
                mergeString = "_unmerged"
        else:
            mergeString = ""
        pyarchFileName = self.pyarchPrefix + mergeString + anomString + "_{0}.{1}".format(name, suffix)
        shutil.copy(strPath, os.path.join(self.strResultPath, pyarchFileName))
        if doGzip:
            pyarchFileName += ".gz"
            f_in = open(strPath)
            f_out = gzip.open(os.path.join(self.pyarchDirectory, pyarchFileName), "wb")
            f_out.writelines(f_in)
            f_out.close()
            f_in.close()
        else:
            shutil.copy(strPath, os.path.join(self.pyarchDirectory, pyarchFileName))
        autoProcProgramAttachment = AutoProcProgramAttachment()
        autoProcProgramAttachment.fileName = pyarchFileName
        autoProcProgramAttachment.filePath = self.pyarchDirectory
        autoProcProgramAttachment.fileType = attachmentType
        autoProcProgramContainer.addAutoProcProgramAttachment(autoProcProgramAttachment)


    def eiger_template_to_image(self, fmt, num):
        fileNumber = int(num / 100)
        if fileNumber == 0:
            fileNumber = 1
        fmt_string = fmt.replace("####", "1_data_%06d" % fileNumber)
        return fmt_string.format(num)


    def eiger_template_to_master(self, fmt):
        fmt_string = fmt.replace("####", "1_master")
        return fmt_string


    def parseLogFile(self, _logFile):
        dictLog = {}
        strLog = EDUtilsFile.readFile(_logFile)
        for strLine in strLog.split("\n"):
            if "Selected space group" in strLine and not "spaceGroup" in dictLog:
                listLine = strLine.split()
                dictLog["spaceGroup"] = " ".join(listLine[3:-1])
                dictLog["spaceGroupNumber"] = int(listLine[-1].replace("(", "").replace(")", ""))
            elif "Unit cell parameters" in strLine:
                listLine = strLine.split()
                dictLog["cellA"] = float(listLine[4])
                dictLog["cellB"] = float(listLine[5])
                dictLog["cellC"] = float(listLine[6])
                dictLog["cellAlpha"] = float(listLine[7])
                dictLog["cellBeta"] = float(listLine[8])
                dictLog["cellGamma"] = float(listLine[9])
        return dictLog


    def runXscale(self, _workingDirectory, merged=False, anom=False):
        strPathXscaleLp = None
        if os.path.exists(os.path.join(_workingDirectory, "XDS_ASCII.HKL")):
            if merged:
                strMerged = "merged"
            else:
                strMerged = "unmerged"
            if anom:
                strAnom = "anom"
            else:
                strAnom = "noanom"
            strXscaleInp = "OUTPUT_FILE= {0}_{1}_XSCALE.hkl\n".format(strMerged, strAnom)
            strXscaleInp += "INPUT_FILE= XDS_ASCII.HKL\n"
            strXscaleInp += "MERGE= {0}\n".format(str(merged).upper())
            strXscaleInp += "FRIEDEL'S_LAW= {0}\n".format(str(not anom).upper())
            EDUtilsFile.writeFile(os.path.join(_workingDirectory, "XSCALE.INP"), strXscaleInp)
            xscaleLog = os.path.join(_workingDirectory, "xscale.log")
            pipe1 = subprocess.Popen("/opt/pxsoft/bin/xscale",
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     close_fds=True,
                                     cwd=_workingDirectory)
            xdsInp = pipe1.communicate()[0]
            with open(xscaleLog, "w") as f:
                f.write(str(xdsInp))
            # Find path to XSCALE.LP file
            strPathXscaleLp = os.path.join(_workingDirectory, "XSCALE.LP")
        return strPathXscaleLp


    def parseXscaleLp(self, _strPathXscaleLp):
        dictXscale = {}
        strXscaleLp = EDUtilsFile.readFile(_strPathXscaleLp)
        isTable = False
        hasDoneInnerShell = False
        tableParsed = False
        listXscaleLp = strXscaleLp.split("\n")
        index = 0
        while not tableParsed and index < len(listXscaleLp):
            strLine = listXscaleLp[index]
            if "SUBSET OF INTENSITY DATA WITH SIGNAL/NOISE" in strLine:
                index += 3
                isTable = True
            elif isTable:
                listLine = strLine.split()
                if not hasDoneInnerShell:
                    dictXscale["innerShell"] = self.parseXscaleLine(listLine)
                    dictXscale["innerShell"]["resolutionLimitLow"] = 100
                    hasDoneInnerShell = True
                if listLine[0] == "total":
                    dictXscale["outerShell"] = self.parseXscaleLine(listXscaleLp[index - 1].split())
                    dictXscale["outerShell"]["resolutionLimitLow"] = float(listXscaleLp[index - 2].split()[0])
                    dictXscale["overall"] = self.parseXscaleLine(listLine)
                    tableParsed = True
            index += 1
        # Fix resolution ranges
        dictXscale["overall"]["resolutionLimitLow"] = dictXscale["innerShell"]["resolutionLimitHigh"]
        dictXscale["overall"]["resolutionLimitHigh"] = dictXscale["outerShell"]["resolutionLimitHigh"]
        return dictXscale


    def parseXscaleLine(self, listLine):
        dictLine = {}
        try:
            for index in range(len(listLine)):
                if listLine[index] != "total":
                    if "%" in listLine[index]:
                        listLine[index] = listLine[index].split("%")[0]
                    elif "*" in listLine[index]:
                        listLine[index] = listLine[index].split("*")[0]
                    listLine[index] = float(listLine[index])
            dictLine["resolutionLimitLow"] = listLine[0]
            dictLine["resolutionLimitHigh"] = listLine[0]
            dictLine["nTotalObservations"] = int(listLine[1])
            dictLine["ntotalUniqueObservations"] = int(listLine[2])
            dictLine["multiplicity"] = round(listLine[1] / listLine[3], 2)
            dictLine["completeness"] = listLine[4]
            dictLine["rMerge"] = listLine[5]
            dictLine["meanIOverSigI"] = listLine[8]
            dictLine["CCHalf"] = listLine[10]
            dictLine["ccAno"] = listLine[11]
            dictLine["sigAno"] = listLine[12]
        except Exception as e:
            self.error(e)
            self.error("Couldn't parse line: {0}".format(listLine))
        return dictLine
