#
#    Project: mxPluginExec
#             http://www.edna-site.org
#
#    Copyright (C) 2011-2012 European Synchrotron Radiation Facility
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
import datetime

from EDFactoryPluginStatic import EDFactoryPluginStatic

from EDPluginISPyBv1_4 import EDPluginISPyBv1_4

from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.sax.date import DateTime
import json
import subprocess
import sys
import re

from XSDataCommon import XSDataInteger

from XSDataISPyBv1_4 import XSDataInputStoreAutoProc
from XSDataISPyBv1_4 import XSDataResultStoreAutoProc


class EDPluginISPyBStoreAutoProcv1_4(EDPluginISPyBv1_4):
    """
    Plugin to store results in an ISPyB database using web services
    """

    def __init__(self):
        """
        Sets default values for dbserver parameters 
        """
        EDPluginISPyBv1_4.__init__(self)
        self.setXSDataInputClass(XSDataInputStoreAutoProc)
        self.strUserName = None
        self.strPassWord = None
        self.strToolsForAutoprocessingWebServiceWsdl = None
        self.iAutoProcId = None
        self.iAutoProcProgramId = None
        self.iAutoProcIntegrationId = None
        self.iAutoProcScalingId = None
        self.bContinue = True
        self.iAutoProcScalingHasIntId = None


    def configure(self):
        """
        Gets the web servise wdsl parameters from the config file and stores them in class member attributes.
        """
        EDPluginISPyBv1_4.configure(self,
                                    _bRequireToolsForAutoprocessingWebServiceWsdl=True)


    def process(self, _edObject=None):
        """
        Stores the contents of the AutoProcContainer in ISPyB.
        """
        EDPluginISPyBv1_4.process(self)
        self.DEBUG("EDPluginISPyBStoreAutoProcv1_4.process")
        xsDataInputStoreAutoProc = self.getDataInput()
        xsDataAutoProcContainer = xsDataInputStoreAutoProc.getAutoProcContainer()
        httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
        clientToolsForAutoprocessingWebService = Client(self.strToolsForAutoprocessingWebServiceWsdl,
                                                        transport=httpAuthenticatedToolsForAutoprocessingWebService,
                                                        cache=None)
        xsDataAutoProcScalingContainer = xsDataAutoProcContainer.getAutoProcScalingContainer()
        xsDataAutoProcProgram = xsDataAutoProcContainer.getAutoProcProgramContainer().getAutoProcProgram()
        # AutoProcProgram
        self.iAutoProcProgramId = self.storeOrUpdateAutoProcProgram(clientToolsForAutoprocessingWebService, xsDataAutoProcProgram)
        if self.iAutoProcProgramId is None:
            self.ERROR("Couldn't create entry for AutoProcProgram in ISPyB!")
            self.setFailure()
            self.bContinue = False
        else:
            listAutoProcProgramAttachment = xsDataAutoProcContainer.getAutoProcProgramContainer().getAutoProcProgramAttachment()
            for xsDataAutoProcProgramAttachment in listAutoProcProgramAttachment:
                self.storeOrUpdateAutoProcProgramAttachment(clientToolsForAutoprocessingWebService, xsDataAutoProcProgramAttachment)
            if xsDataAutoProcScalingContainer is None:
                self.bContinue = False
        if self.bContinue:
            # AutoProcIntegration
            xsDataAutoProcIntegrationContainer = xsDataAutoProcScalingContainer.getAutoProcIntegrationContainer()
            self.iAutoProcIntegrationId = self.storeOrUpdateAutoProcIntegration(clientToolsForAutoprocessingWebService, xsDataAutoProcIntegrationContainer)
            if self.iAutoProcIntegrationId is None:
                self.WARNING("Couldn't create entry for AutoProcIntegration in ISPyB!")
            if xsDataAutoProcProgram.getProcessingStatus() == "FAILED":
                self.bContinue = False
        if self.bContinue:
            # AutoProc
            xsDataAutoProc = xsDataAutoProcContainer.getAutoProc()
            if xsDataAutoProc is not None:
                self.iAutoProcId = self.storeOrUpdateAutoProc(clientToolsForAutoprocessingWebService, xsDataAutoProc)
            if self.iAutoProcId is None:
                self.DEBUG("Couldn't create entry for AutoProc in ISPyB. Stopping here.")
                self.bContinue = False
        if self.bContinue:
            # AutoProcScaling
            xsDataAutoProcScaling = xsDataAutoProcScalingContainer.getAutoProcScaling()
            self.iAutoProcScalingId = self.storeOrUpdateAutoProcScaling(clientToolsForAutoprocessingWebService, xsDataAutoProcScaling)
            if self.iAutoProcScalingId is None:
                self.ERROR("Couldn't create entry for AutoProcScaling in ISPyB!")
                self.setFailure()
                self.bContinue = False
        if self.bContinue:
            # AutoProcScalingHasIntId
            self.iAutoProcScalingHasIntId = self.storeOrUpdateAutoProcScalingHasIntId(clientToolsForAutoprocessingWebService)
            if self.iAutoProcScalingHasIntId is None:
                self.ERROR("Couldn't create entry for AutoProcScalingHasIntId in ISPyB!")
                self.setFailure()
                self.bContinue = False
        if self.bContinue:
            # AutoProcScalingStatistics
            for xsDataAutoProcScalingStatistics in xsDataAutoProcScalingContainer.getAutoProcScalingStatistics():
                iAutoProcScalingStatisticsId = self.storeOrUpdateAutoProcScalingStatistics(clientToolsForAutoprocessingWebService, xsDataAutoProcScalingStatistics)
                if iAutoProcScalingStatisticsId is None:
                    self.ERROR("Couldn't create entry for AutoProcScalingStatistics in ISPyB!")
                    self.setFailure()
                    self.bContinue = False



    def finallyProcess(self, _edObject=None):
        EDPluginISPyBv1_4.finallyProcess(self)
        self.DEBUG("EDPluginISPyBStoreAutoProcv1_4.finallyProcess")
        xsDataResultStoreAutoProc = XSDataResultStoreAutoProc()
        if self.iAutoProcId is not None:
            xsDataResultStoreAutoProc.setAutoProcId(XSDataInteger(self.iAutoProcId))
        if self.iAutoProcIntegrationId is not None:
            xsDataResultStoreAutoProc.setAutoProcIntegrationId(XSDataInteger(self.iAutoProcIntegrationId))
        if self.iAutoProcScalingId is not None:
            xsDataResultStoreAutoProc.setAutoProcScalingId(XSDataInteger(self.iAutoProcScalingId))
        if self.iAutoProcProgramId is not None:
            xsDataResultStoreAutoProc.setAutoProcProgramId(XSDataInteger(self.iAutoProcProgramId))
        self.setDataOutput(xsDataResultStoreAutoProc)



    def storeOrUpdateAutoProcProgram(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProcProgram):
        """Creates an entry in the ISPyB AutoProcProgram table"""
        self.DEBUG("EDPluginISPyBStoreAutoProcv1_4.storeOrUpdateAutoProcProgram")
        iAutoProcProgramId = self.getXSValue(_xsDataAutoProcProgram.getAutoProcProgramId())
        strProcessingCommandLine = self.getXSValue(_xsDataAutoProcProgram.getProcessingCommandLine())
        strProcessingPrograms = self.getXSValue(_xsDataAutoProcProgram.getProcessingPrograms())
        strProcessingStatus = self.getXSValue(_xsDataAutoProcProgram.getProcessingStatus(), "SUCCESS")
        if strProcessingStatus == "true" or strProcessingStatus == "1":
            strProcessingStatus = "SUCCESS"
        elif strProcessingStatus == "false" or strProcessingStatus == "0":
            strProcessingStatus = "FAILED"
        strProcessingMessage = self.getXSValue(_xsDataAutoProcProgram.getProcessingMessage())
        processingStartTime = self.getDateValue(_xsDataAutoProcProgram.getProcessingStartTime(), "%a %b %d %H:%M:%S %Y", DateTime(datetime.datetime.now()))
        processingEndTime = self.getDateValue(_xsDataAutoProcProgram.getProcessingEndTime(), "%a %b %d %H:%M:%S %Y", DateTime(datetime.datetime.now()))
        strProcessingEnvironment = self.getXSValue(_xsDataAutoProcProgram.getProcessingEnvironment())
        recordTimeStamp = self.getDateValue(None, "%a %b %d %H:%M:%S %Y", DateTime(datetime.datetime.now()))
        iAutoProcProgramId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcProgram(
                arg0=iAutoProcProgramId,
                processingCommandLine=strProcessingCommandLine,
                processingPrograms=strProcessingPrograms,
                processingStatus=strProcessingStatus,
                processingMessage=strProcessingMessage,
                processingStartTime=processingStartTime,
                processingEndTime=processingEndTime,
                processingEnvironment=strProcessingEnvironment,
                recordTimeStamp=recordTimeStamp
                )
        self.DEBUG("AutoProcProgramId: %r" % iAutoProcProgramId)
        return iAutoProcProgramId


    def storeOrUpdateAutoProcProgramAttachment(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProcProgramAttachment):
        """Creates an entry in the ISPyB AutoProcProgramAttachment table"""
        iAutoProcProgramAttachmentId = self.getXSValue(_xsDataAutoProcProgramAttachment.getAutoProcProgramAttachmentId())
        strFileType = self.getXSValue(_xsDataAutoProcProgramAttachment.getFileType())
        strFileName = self.getXSValue(_xsDataAutoProcProgramAttachment.getFileName())
        strFilePath = self.getXSValue(_xsDataAutoProcProgramAttachment.getFilePath())
        recordTimeStamp = DateTime(datetime.datetime.now())
        iAutoProcProgramId = self.iAutoProcProgramId
        iAutoProcProgramAttachmentId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcProgramAttachment(
                arg0=iAutoProcProgramAttachmentId,
                fileType=strFileType,
                fileName=strFileName,
                filePath=strFilePath,
                recordTimeStamp=recordTimeStamp,
                autoProcProgramId=iAutoProcProgramId
                )
        self.DEBUG("AutoProcProgramAttachmentId: %r" % iAutoProcProgramAttachmentId)
        return iAutoProcProgramAttachmentId


    def storeOrUpdateAutoProcIntegration(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProcIntegrationContainer):
        """Creates an entry in the ISPyB AutoProcIntegration table"""
        xsDataProcIntegration = _xsDataAutoProcIntegrationContainer.getAutoProcIntegration()
        iAutoProcIntegrationId = self.getXSValue(xsDataProcIntegration.getAutoProcIntegrationId())
        iAutoProcProgramId = self.iAutoProcProgramId
        iStartImageNumber = self.getXSValue(xsDataProcIntegration.getStartImageNumber())
        iEndImageNumber = self.getXSValue(xsDataProcIntegration.getEndImageNumber())
        fRefinedDetectorDistance = self.getXSValue(xsDataProcIntegration.getRefinedDetectorDistance())
        fRefinedXbeam = self.getXSValue(xsDataProcIntegration.getRefinedXbeam())
        fRefinedYbeam = self.getXSValue(xsDataProcIntegration.getRefinedYbeam())
        fRotationAxisX = self.getXSValue(xsDataProcIntegration.getRotationAxisX())
        fRotationAxisY = self.getXSValue(xsDataProcIntegration.getRotationAxisY())
        fRotationAxisZ = self.getXSValue(xsDataProcIntegration.getRotationAxisZ())
        fBeamVectorX = self.getXSValue(xsDataProcIntegration.getBeamVectorX())
        fBeamVectorY = self.getXSValue(xsDataProcIntegration.getBeamVectorY())
        fBeamVectorZ = self.getXSValue(xsDataProcIntegration.getBeamVectorZ())
        fCellA = self.getXSValue(xsDataProcIntegration.getCell_a())
        fCellB = self.getXSValue(xsDataProcIntegration.getCell_b())
        fCellC = self.getXSValue(xsDataProcIntegration.getCell_c())
        fCellAlpha = self.getXSValue(xsDataProcIntegration.getCell_alpha())
        fCellBeta = self.getXSValue(xsDataProcIntegration.getCell_beta())
        fCellGamma = self.getXSValue(xsDataProcIntegration.getCell_gamma())
        bAnomalous = self.getXSValue(xsDataProcIntegration.getAnomalous(), False)
        iDataCollectionId = _xsDataAutoProcIntegrationContainer.getImage().getDataCollectionId()
        recordTimeStamp = DateTime(datetime.datetime.now())
        iAutoProcIntegrationId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcIntegration(
                arg0=iAutoProcIntegrationId,
                autoProcProgramId=iAutoProcProgramId,
                startImageNumber=iStartImageNumber,
                endImageNumber=iEndImageNumber,
                refinedDetectorDistance=fRefinedDetectorDistance,
                refinedXbeam=fRefinedXbeam,
                refinedYbeam=fRefinedYbeam,
                rotationAxisX=fRotationAxisX,
                rotationAxisY=fRotationAxisY,
                rotationAxisZ=fRotationAxisZ,
                beamVectorX=fBeamVectorX,
                beamVectorY=fBeamVectorY,
                beamVectorZ=fBeamVectorZ,
                cellA=fCellA,
                cellB=fCellB,
                cellC=fCellC,
                cellAlpha=fCellAlpha,
                cellBeta=fCellBeta,
                cellGamma=fCellGamma,
                recordTimeStamp=recordTimeStamp,
                anomalous=bAnomalous,
                dataCollectionId=iDataCollectionId
                )
        self.DEBUG("AutoProcProgramIntegrationId: %r" % iAutoProcIntegrationId)
        return iAutoProcIntegrationId


    def storeOrUpdateAutoProc(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProc):
        """Creates an entry in the ISPyB AutoProc table"""
        iAutoProcId = self.getXSValue(_xsDataAutoProc.getAutoProcId())
        iAutoProcProgramId = self.iAutoProcProgramId
        strSpaceGroup = self.getXSValue(_xsDataAutoProc.getSpaceGroup())
        fRefinedCellA = self.getXSValue(_xsDataAutoProc.getRefinedCell_a())
        fRefinedCellB = self.getXSValue(_xsDataAutoProc.getRefinedCell_b())
        fRefinedCellC = self.getXSValue(_xsDataAutoProc.getRefinedCell_c())
        fRefinedCellAlpha = self.getXSValue(_xsDataAutoProc.getRefinedCell_alpha())
        fRefinedCellBeta = self.getXSValue(_xsDataAutoProc.getRefinedCell_beta())
        fRefinedCellGamma = self.getXSValue(_xsDataAutoProc.getRefinedCell_gamma())
        recordTimeStamp = DateTime(datetime.datetime.now())
        iAutoProcId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProc(
                arg0=iAutoProcId,
                autoProcProgramId=iAutoProcProgramId,
                spaceGroup=strSpaceGroup,
                refinedCellA=fRefinedCellA,
                refinedCellB=fRefinedCellB,
                refinedCellC=fRefinedCellC,
                refinedCellAlpha=fRefinedCellAlpha,
                refinedCellBeta=fRefinedCellBeta,
                refinedCellGamma=fRefinedCellGamma,
                recordTimeStamp=recordTimeStamp
                )
        self.DEBUG("AutoProcId: %r" % iAutoProcId)
        return iAutoProcId


    def storeOrUpdateAutoProcScaling(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProcScaling):
        """Creates an entry in the ISPyB AutoProcScaling table"""
        iAutoProcScalingId = self.getXSValue(_xsDataAutoProcScaling.getAutoProcScalingId())
        iAutoProcId = self.iAutoProcId
        recordTimeStamp = self.getDateValue(_xsDataAutoProcScaling.getRecordTimeStamp(), "%Y-%m-%d %H:%M:%S", DateTime(datetime.datetime.now()))
        if _xsDataAutoProcScaling.StaranisoEllipsoid is not None:
            StaranisoEllipsoidRotationMatrix = _xsDataAutoProcScaling.StaranisoEllipsoid.StaranisoEllipsoidRotationMatrix
            iResolutionEllipsoidAxis11 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix11)
            iResolutionEllipsoidAxis12 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix12)
            iResolutionEllipsoidAxis13 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix13)
            iResolutionEllipsoidAxis21 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix21)
            iResolutionEllipsoidAxis22 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix22)
            iResolutionEllipsoidAxis23 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix23)
            iResolutionEllipsoidAxis31 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix31)
            iResolutionEllipsoidAxis32 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix32)
            iResolutionEllipsoidAxis33 = self.getXSValue(StaranisoEllipsoidRotationMatrix.StaranisoEllipsoidRotationMatrix33)
            StaranisoEllipsoidEigenvalues = _xsDataAutoProcScaling.StaranisoEllipsoid.StaranisoEllipsoidEigenvalues
            iResolutionEllipsoidValue1 = self.getXSValue(StaranisoEllipsoidEigenvalues.StaranisoEllipsoidEigenvalue1)
            iResolutionEllipsoidValue2 = self.getXSValue(StaranisoEllipsoidEigenvalues.StaranisoEllipsoidEigenvalue2)
            iResolutionEllipsoidValue3 = self.getXSValue(StaranisoEllipsoidEigenvalues.StaranisoEllipsoidEigenvalue3)
        else:
            iResolutionEllipsoidAxis11 = None
            iResolutionEllipsoidAxis12 = None
            iResolutionEllipsoidAxis13 = None
            iResolutionEllipsoidAxis21 = None
            iResolutionEllipsoidAxis22 = None
            iResolutionEllipsoidAxis23 = None
            iResolutionEllipsoidAxis31 = None
            iResolutionEllipsoidAxis32 = None
            iResolutionEllipsoidAxis33 = None
            iResolutionEllipsoidValue1 = None
            iResolutionEllipsoidValue2 = None
            iResolutionEllipsoidValue3 = None
        iAutoProcScalingId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcScaling(
                arg0=iAutoProcScalingId,
                autoProcId=iAutoProcId,
                recordTimeStamp=recordTimeStamp,
                resolutionEllipsoidAxis11=iResolutionEllipsoidAxis11,
                resolutionEllipsoidAxis12=iResolutionEllipsoidAxis12,
                resolutionEllipsoidAxis13=iResolutionEllipsoidAxis13,
                resolutionEllipsoidAxis21=iResolutionEllipsoidAxis21,
                resolutionEllipsoidAxis22=iResolutionEllipsoidAxis22,
                resolutionEllipsoidAxis23=iResolutionEllipsoidAxis23,
                resolutionEllipsoidAxis31=iResolutionEllipsoidAxis31,
                resolutionEllipsoidAxis32=iResolutionEllipsoidAxis32,
                resolutionEllipsoidAxis33=iResolutionEllipsoidAxis33,
                resolutionEllipsoidValue1=iResolutionEllipsoidValue1,
                resolutionEllipsoidValue2=iResolutionEllipsoidValue2,
                resolutionEllipsoidValue3=iResolutionEllipsoidValue3,
                )
        self.DEBUG("AutoProcScalingId: %r" % iAutoProcScalingId)
        return iAutoProcScalingId



    def storeOrUpdateAutoProcScalingStatistics(self, _clientToolsForAutoprocessingWebService, _xsDataAutoProcScalingStatistics):
        """Creates an entry in the ISPyB AutoProcScalingStatistics table"""
        iAutoProcScalingStatisticsId = self.getXSValue(_xsDataAutoProcScalingStatistics.getAutoProcScalingStatisticsId())
        strScalingStatisticsType = self.getXSValue(_xsDataAutoProcScalingStatistics.getScalingStatisticsType())
        strComments = self.getXSValue(_xsDataAutoProcScalingStatistics.getComments())
        fResolutionLimitLow = self.getXSValue(_xsDataAutoProcScalingStatistics.getResolutionLimitLow())
        fResolutionLimitHigh = self.getXSValue(_xsDataAutoProcScalingStatistics.getResolutionLimitHigh())
        fRmerge = self.getXSValue(_xsDataAutoProcScalingStatistics.getRMerge())
        fRmeasWithinIplusIminus = self.getXSValue(_xsDataAutoProcScalingStatistics.getRMeasWithinIPlusIMinus())
        fRmeasAllIplusIminus = self.getXSValue(_xsDataAutoProcScalingStatistics.getRMeasAllIPlusIMinus())
        fRpimWithinIplusIminus = self.getXSValue(_xsDataAutoProcScalingStatistics.getRPimWithinIPlusIMinus())
        fRpimAllIplusIminus = self.getXSValue(_xsDataAutoProcScalingStatistics.getRPimAllIPlusIMinus())
        fFractionalPartialBias = self.getXSValue(_xsDataAutoProcScalingStatistics.getFractionalPartialBias())
        iNtotalObservations = self.getXSValue(_xsDataAutoProcScalingStatistics.getNTotalObservations())
        iNtotalUniqueObservations = self.getXSValue(_xsDataAutoProcScalingStatistics.getNtotalUniqueObservations())
        fMeanIoverSigI = self.getXSValue(_xsDataAutoProcScalingStatistics.getMeanIOverSigI())
        fCompleteness = self.getXSValue(_xsDataAutoProcScalingStatistics.getCompleteness())
        fMultiplicity = self.getXSValue(_xsDataAutoProcScalingStatistics.getMultiplicity())
        fAnomalousCompleteness = self.getXSValue(_xsDataAutoProcScalingStatistics.getAnomalousCompleteness())
        fAnomalousMultiplicity = self.getXSValue(_xsDataAutoProcScalingStatistics.getAnomalousMultiplicity())
        recordTimeStamp = DateTime(datetime.datetime.now())
        bAnomalous = self.getXSValue(_xsDataAutoProcScalingStatistics.getAnomalous(), False)
        iAutoProcScalingId = self.iAutoProcScalingId
        fCcHalf = self.getXSValue(_xsDataAutoProcScalingStatistics.getCcHalf())
        fCcAno = self.getXSValue(_xsDataAutoProcScalingStatistics.getCcAno())
        fSigAno = self.getXSValue(_xsDataAutoProcScalingStatistics.getSigAno())
        fIsa = self.getXSValue(_xsDataAutoProcScalingStatistics.getIsa())
        fCompletenessSpherical = self.getXSValue(_xsDataAutoProcScalingStatistics.getCompletenessSpherical())
        fAnomalousCompletenessSpherical = self.getXSValue(_xsDataAutoProcScalingStatistics.getAnomalousCompletenessSpherical())
        fCompletenessEllipsoidal = self.getXSValue(_xsDataAutoProcScalingStatistics.getCompletenessEllipsoidal())
        fAnomalousCompletenessEllipsoidal = self.getXSValue(_xsDataAutoProcScalingStatistics.getAnomalousCompletenessEllipsoidal())
        iAutoProcScalingStatisticsId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcScalingStatistics(
                arg0=iAutoProcScalingStatisticsId,
                scalingStatisticsType=strScalingStatisticsType,
                comments=strComments,
                resolutionLimitLow=fResolutionLimitLow,
                resolutionLimitHigh=fResolutionLimitHigh,
                rmerge=fRmerge,
                rmeasWithinIplusIminus=fRmeasWithinIplusIminus,
                rmeasAllIplusIminus=fRmeasAllIplusIminus,
                rpimWithinIplusIminus=fRpimWithinIplusIminus,
                rpimAllIplusIminus=fRpimAllIplusIminus,
                fractionalPartialBias=fFractionalPartialBias,
                nTotalObservations=iNtotalObservations,
                nTotalUniqueObservations=iNtotalUniqueObservations,
                meanIoverSigI=fMeanIoverSigI,
                completeness=fCompleteness,
                multiplicity=fMultiplicity,
                anomalousCompleteness=fAnomalousCompleteness,
                anomalousMultiplicity=fAnomalousMultiplicity,
                recordTimeStamp=recordTimeStamp,
                anomalous=bAnomalous,
                autoProcScalingId=iAutoProcScalingId,
                ccHalf=fCcHalf,
                ccAno=fCcAno,
                sigAno=fSigAno,
                isa=fIsa,
                completenessSpherical=fCompletenessSpherical,
                anomalousCompletenessSpherical=fAnomalousCompletenessSpherical,
                completenessEllipsoidal=fCompletenessEllipsoidal,
                anomalousCompletenessEllipsoidal=fAnomalousCompletenessEllipsoidal,
                )
        self.DEBUG("AutoProcScalingStatisticsId: %r" % iAutoProcScalingStatisticsId)
        return iAutoProcScalingStatisticsId


    def storeOrUpdateAutoProcScalingHasIntId(self, _clientToolsForAutoprocessingWebService):
        """Creates an entry in the ISPyB storeOrUpdateAutoProcScalingHasIntId table"""
        iAutoProcIntegrationId = self.iAutoProcIntegrationId
        iAutoProcScalingId = self.iAutoProcScalingId
        recordTimeStamp = DateTime(datetime.datetime.now())
        iAutoProcScalingHasIntId = _clientToolsForAutoprocessingWebService.service.storeOrUpdateAutoProcScalingHasInt(
                arg0=None,
                autoProcIntegrationId=iAutoProcIntegrationId,
                autoProcScalingId=iAutoProcScalingId,
                recordTimeStamp=recordTimeStamp
                )
        self.DEBUG("AutoProcScalingHasIntId: %r" % iAutoProcScalingHasIntId)
        return iAutoProcScalingHasIntId


    def storeOrUpdateAutoProcPhasingStep(self, mrMtzPath, mrPdbPath, scalingId, structureGroupName, inputPDB, phasingPrograms):
        """Creates an entry in the ISPyB Phasing step"""
        
        #EDPluginISPyBv1_4.process(self)
        self.DEBUG("EDPluginISPyBStoreAutoProcv1_4.storeOrUpdateAutoProcPhasingStep")
        # self.screen("self.strUserName = {0}".format(self.strUserName) )
        # self.screen("self.strPassWord = {0}".format(self.strPassWord) )
        # self.screen("self.strToolsForAutoprocessingWebServiceWsdl = {0}".format(self.strToolsForAutoprocessingWebServiceWsdl) )
        httpAuthenticatedToolsForAutoprocessingWebService = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
        clientToolsForAutoprocessingWebService = Client(self.strToolsForAutoprocessingWebServiceWsdl,
                                                        transport=httpAuthenticatedToolsForAutoprocessingWebService,
                                                        cache=None)
        
        dictPhasingStep = {"scalingId": scalingId}
        
        mrSubDir = os.path.dirname(mrMtzPath)
        
        if not os.path.exists(mrPdbPath):
            self.screen("ERROR: MR.pdb path {0} does not exist!".format(mrPdbPath))
        elif not os.path.exists(mrPdbPath):
            self.screen("ERROR: MR.mtz path {0} does not exist!".format(mrMtzPath))
        else:
            out_log, out_err = self.run_cmd(str('mtzdmp ' + mrMtzPath))
            mtzdmp_data = self.parse_mtzdmp(out_log)
            
            
            dictPhasingStep["lowRes"] = mtzdmp_data['min_resolution']
            dictPhasingStep["highRes"] = mtzdmp_data['min_resolution']
            spaceGroupName = mtzdmp_data['space_group']
            spaceGroupShortName = spaceGroupName.replace(" ", "")
            dictPhasingStep["spaceGroupShortName"] = spaceGroupShortName
            
            # Create PhasingStep entry
            phasingStep = {
                "previousPhasingStepId": None,
                "autoProcScalingId": scalingId,
                "phasingStepType": "PHASING",
                "method": 'MR',
                "solventContent": None,
                "enantiomorph": None,
                "lowRes": dictPhasingStep["lowRes"],
                "highRes": dictPhasingStep["highRes"],
                "groupName": structureGroupName,
            }
            spaceGroup = {
                "spaceGroupShortName": spaceGroupShortName,
            }
            run = {
                "phasingCommandLine": None,
                "phasingPrograms": phasingPrograms,
                "phasingStatus": None,
                "phasingMessage": None,
                "phasingStartTime": None,
                "phasingEndTime": None,
                "phasingEnvironment": None,
                "phasingDirectory": mrSubDir,
            }
            attachments = [
                {
                    "fileType": "PDB",
                    "fileName": os.path.basename(mrPdbPath),
                    "filePath": mrPdbPath,
                    "recordTimeStamp": None,
                }, {
                    "fileType": "Map",
                    "fileName": os.path.basename(mrMtzPath),
                    "filePath": mrMtzPath,
                    "recordTimeStamp": None,
                }
            ]

            dictInputPDB = {
                "fileType": "PDB",
                "fileName": os.path.basename(inputPDB),
                "filePath": inputPDB,
                "recordTimeStamp": None,
                "input": 1,
            }
            attachments.append(dictInputPDB)

            statistics = []

            self.screen("storePhasingAnalysis phasingStep: {0}".format(json.dumps(phasingStep, indent=4)))
            self.screen("storePhasingAnalysis spaceGroup: {0}".format(json.dumps(spaceGroup, indent=4)))
            self.screen("storePhasingAnalysis run: {0}".format(json.dumps(run, indent=4)))
            self.screen("storePhasingAnalysis attachments: {0}".format(json.dumps(attachments, indent=4)))
            self.screen("storePhasingAnalysis statistics: {0}".format(json.dumps(statistics, indent=4)))
            
            
            storePhasingAnalysisResponse = clientToolsForAutoprocessingWebService.service.storePhasingAnalysis(
                                                                            json.dumps(phasingStep),
                                                                            json.dumps(spaceGroup),
                                                                            json.dumps(run),
                                                                            json.dumps(attachments),
                                                                            json.dumps(statistics))
            phasingStepId = json.loads(storePhasingAnalysisResponse)["phasingStepId"]
            
            return phasingStepId

    def run_cmd(self, command_line: str, run_dir: str = ".") -> tuple:
        """
        It moves to the run_dir directory (cd run_dir) and then it executes the command line
        :param command_line: The command line to execute
        :param run_dir: Path where the command_line will be executed from
        :return: A tuple containing 2 strings: the stdout and the stderr
        """
        proc = subprocess.Popen(
            ["cd " + run_dir + ";" + command_line],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout = proc.stdout.read().decode().rstrip("\n\r") if proc.stdout else ""
        stderr = proc.stderr.read().decode().rstrip("\n\r") if proc.stderr else ""
        return stdout, stderr
        


    def parse_mtzdmp(self, mtz_output: str) -> dict:
        mtz_data = {}
        
        # * Space group = 'P 43 21 2' (number     96)
        sg_match = re.search(r"\*\sSpace\sgroup\s=\s\'(P.+)\'.+", mtz_output)
        if sg_match:
            sg = sg_match.group(1)
            sg_short = sg.replace(" ", "")
            mtz_data['space_group'] = sg_short 
        else:
            self.screen("ERROR: Space groupt not found in mtzdmp output!")
            
        
        #*  Resolution Range :
        #
        #0.00032    0.75996     (     56.017 -      1.147 A )
        resolution_match = re.search(r"\*\s+Resolution\sRange\s*:\n\s*\n\s*(\d+\.?\d+)\s+(\d+\.?\d+)\s+\(\s+(\d+\.?\d+)\s+\-\s+(\d+\.?\d+)\s+A\s*\).*", mtz_output)
        if sg_match:
            
            print(f"resolution_match = {resolution_match}")
            # Reciprocal space
            reciproc_min = resolution_match.group(1)
            reciproc_max = resolution_match.group(2)
            
            # Real space
            directe_min = resolution_match.group(3)
            directe_max = resolution_match.group(4)
            mtz_data['reciprocal_min_resolution'] = reciproc_min
            mtz_data['reciprocal_max_resolution'] = reciproc_max    
            mtz_data['min_resolution'] = directe_min
            mtz_data['max_resolution'] = directe_max
            
        else:
            print("ERROR: Space groupt not found in mtzdmp output!")
        
        sg_match = re.search(r"\*\sSpace\sgroup\s=\s\'(P.+)\'.+", mtz_output)
        if sg_match:
            sg = sg_match.group(1)
            sg_short = sg.replace(" ", "")
            mtz_data['space_group'] = sg_short 
        else:
            self.screen("ERROR: Space groupt not found in mtzdmp output!")

        
        return mtz_data
