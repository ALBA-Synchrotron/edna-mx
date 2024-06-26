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

from XSDataCommon import XSDataInteger

from XSDataISPyBv1_4 import XSDataISPyBScreeningStrategy
from XSDataISPyBv1_4 import XSDataInputISPyBStoreScreening
from XSDataISPyBv1_4 import XSDataResultISPyBStoreScreening


class EDPluginISPyBStoreScreeningv1_4(EDPluginISPyBv1_4):
    """
    Plugin to store results in an ISPyB database using web services
    """

    def __init__(self):
        """
        Sets default values for dbserver parameters 
        """
        EDPluginISPyBv1_4.__init__(self)
        self.setXSDataInputClass(XSDataInputISPyBStoreScreening)
        self.iScreeningId = None
        self.iDataCollectionGroupId = None


    def configure(self):
        """
        Gets the web servise wdsl parameters from the config file and stores them in class member attributes.
        """
        EDPluginISPyBv1_4.configure(self,
                                    _bRequireToolsForCollectionWebServiceWsdl=True,
                                    _bRequireToolsForBLSampleWebServiceWsdl=True,
                                    _bRequireToolsForScreeningEDNAWebServiceWsdl=True,
                                    )


    def process(self, _edObject=None):
        """
        Stores the contents of the AutoProcContainer in ISPyB.
        """
        EDPluginISPyBv1_4.process(self)
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.process")
        xsDataInputISPyBStoreScreening = self.getDataInput()
        httpAuthenticatedToolsForAutoprocessingWebService1 = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
        clientToolsForBLSampleWebServiceWsdl = Client(self.strToolsForBLSampleWebServiceWsdl,
                                                      transport=httpAuthenticatedToolsForAutoprocessingWebService1,
                                                      cache=None)
        httpAuthenticatedToolsForAutoprocessingWebService2 = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
        clientToolsForScreeningEDNAWebServiceWsdl = Client(self.strToolsForScreeningEDNAWebServiceWsdl,
                                                           transport=httpAuthenticatedToolsForAutoprocessingWebService2,
                                                           cache=None)
        self.bContinue = True
        # Data collection Id
        if xsDataInputISPyBStoreScreening.screening.dataCollectionGroupId is None:
            xsDataISPyBImage = xsDataInputISPyBStoreScreening.image
            if xsDataISPyBImage is not None:
                httpAuthenticatedToolsForAutoprocessingWebService3 = HttpAuthenticated(username=self.strUserName, password=self.strPassWord)
                clientToolsForCollectionWebService = Client(self.strToolsForCollectionWebServiceWsdl,
                                                            transport=httpAuthenticatedToolsForAutoprocessingWebService3,
                                                            cache=None)
                self.iDataCollectionGroupId = self.findDataCollectionFromFileLocationAndFileName(clientToolsForCollectionWebService, xsDataISPyBImage.fileLocation.value, xsDataISPyBImage.fileName.value)
                if self.iDataCollectionGroupId is None:
                    self.ERROR("Couldn't obtain data collection id!")
                    self.setFailure()
                else:
                    xsDataInputISPyBStoreScreening.screening.dataCollectionGroupId = XSDataInteger(self.iDataCollectionGroupId)
        else:
            self.iDataCollectionGroupId = xsDataInputISPyBStoreScreening.screening.dataCollectionGroupId.value
        if not self.isFailure():
            # DiffractionPlan
            xsDataISPyBDiffractionPlan = xsDataInputISPyBStoreScreening.diffractionPlan
            iDiffractionPlanId = self.storeOrUpdateDiffractionPlan(clientToolsForBLSampleWebServiceWsdl, xsDataISPyBDiffractionPlan)
            if iDiffractionPlanId is None:
                self.ERROR("Couldn't create entry for diffraction plan in ISPyB!")
                self.setFailure()
                self.bContinue = False
            # Screening
            xsDataISPyBScreening = xsDataInputISPyBStoreScreening.screening
            self.iScreeningId = self.storeOrUpdateScreening(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreening, iDiffractionPlanId)
            if self.iScreeningId is None:
                self.ERROR("Couldn't create entry for screening in ISPyB!")
                self.setFailure()
                self.bContinue = False
            # Screening Output Container
            for xsDataISPyBScreeningOutputContainer in xsDataInputISPyBStoreScreening.screeningOutputContainer:
                xsDataISPyBScreeningOutput = xsDataISPyBScreeningOutputContainer.screeningOutput
                iScreeningOutputId = self.storeOrUpdateScreeningOutput(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreeningOutput, self.iScreeningId)
                if iScreeningOutputId is None:
                    self.ERROR("Couldn't create entry for screening in ISPyB!")
                    self.setFailure()
                    self.bContinue = False
                for xsDataISPyBScreeningOutputLattice in xsDataISPyBScreeningOutputContainer.screeningOutputLattice:
                    iScreeningOutputLatticeId = self.storeOrUpdateScreeningOutputLattice(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreeningOutputLattice, iScreeningOutputId)
                    if iScreeningOutputLatticeId is None:
                        self.ERROR("Couldn't create entry for screening lattice in ISPyB!")
                        self.setFailure()
                        self.bContinue = False
                for xsDataISPyBScreeningStrategyContainer in xsDataISPyBScreeningOutputContainer.screeningStrategyContainer:
                    # Create an empty object of type XSDataISPyBScreeningStrategy
                    xsDataISPyBScreeningStrategy = XSDataISPyBScreeningStrategy()
                    iScreeningStrategyId = self.storeOrUpdateScreeningStrategy(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreeningStrategy, iScreeningOutputId)
                    if iScreeningStrategyId is None:
                        self.ERROR("Couldn't create entry for screening strategy in ISPyB!")
                        self.setFailure()
                        self.bContinue = False
                    for xsDataISPyBScreeningStrategyWedgeContainer in xsDataISPyBScreeningStrategyContainer.screeningStrategyWedgeContainer:
                        xsDataISPyBScreeningStrategyWedge = xsDataISPyBScreeningStrategyWedgeContainer.screeningStrategyWedge
                        iScreeningStrategyWedgeId = self.storeOrUpdateScreeningStrategyWedge(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreeningStrategyWedge, iScreeningStrategyId)
                        if iScreeningStrategyWedgeId is None:
                            self.ERROR("Couldn't create entry for screening strategy in ISPyB!")
                            self.setFailure()
                            self.bContinue = False
                        for xsDataISPyBScreeningStrategySubWedge in xsDataISPyBScreeningStrategyWedgeContainer.screeningStrategySubWedge:
                            iScreeningStrategySubWedgeId = self.storeOrUpdateScreeningStrategySubWedge(clientToolsForScreeningEDNAWebServiceWsdl, xsDataISPyBScreeningStrategySubWedge, iScreeningStrategyWedgeId)
                            if iScreeningStrategySubWedgeId is None:
                                self.ERROR("Couldn't create entry for screening strategy in ISPyB!")
                                self.setFailure()
                                self.bContinue = False





    def finallyProcess(self, _edObject=None):
        EDPluginISPyBv1_4.finallyProcess(self)
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.finallyProcess")
        xsDataResultISPyBStoreScreening = XSDataResultISPyBStoreScreening()
        if self.iScreeningId is not None:
            xsDataResultISPyBStoreScreening.screeningId = XSDataInteger(self.iScreeningId)
        if self.iDataCollectionGroupId is not None:
            xsDataResultISPyBStoreScreening.dataCollectionGroupId = XSDataInteger(self.iDataCollectionGroupId)
        self.setDataOutput(xsDataResultISPyBStoreScreening)




    def findDataCollectionFromFileLocationAndFileName(self, _clientToolsForCollectionWebService, _strDirName, _strFileName):
        """Returns the data collection id for an image path"""
        if _strDirName.endswith(os.sep):
            strDirName = _strDirName[:-1]
        else:
            strDirName = _strDirName
        self.DEBUG("Looking for ISPyB data collection id for dir %s name %s" % (strDirName, _strFileName))
        dataCollectionWS3VO = _clientToolsForCollectionWebService.service.findDataCollectionFromFileLocationAndFileName(
                strDirName, \
                _strFileName, \
                )
        if dataCollectionWS3VO is None:
            iDataCollectionGroupId = None
            self.WARNING("Cannot find data collection id for dir %s name %s" % (strDirName, _strFileName))
        else:
            iDataCollectionGroupId = dataCollectionWS3VO.dataCollectionGroupId
            self.DEBUG("Data collection id for dir %s name %s is %d" % (strDirName, _strFileName, iDataCollectionGroupId))
        return iDataCollectionGroupId




    def storeOrUpdateDiffractionPlan(self, _clientToolsForBLSampleWebServiceWsdl, _xsDataISPyBDiffractionPlan):
        """Creates an entry in ISPyB for the DiffractionPlan table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeDiffractionPlan")
        iDiffractionPlanId = self.getXSValue(_xsDataISPyBDiffractionPlan.diffractionPlanId)
        strExperimentKind = self.getXSValue(_xsDataISPyBDiffractionPlan.experimentKind)
        fObservedResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.observedResolution)
        fMinimalResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.minimalResolution)
        fExposureTime = self.getXSValue(_xsDataISPyBDiffractionPlan.exposureTime)
        fOscillationRange = self.getXSValue(_xsDataISPyBDiffractionPlan.oscillationRange)
        fMaximalResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.maximalResolution)
        fScreeningResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.screeningResolution)
        fRadiationSensitivity = self.getXSValue(_xsDataISPyBDiffractionPlan.radiationSensitivity)
        strAnomalousScatterer = self.getXSValue(_xsDataISPyBDiffractionPlan.anomalousScatterer)
        fPreferredBeamSizeX = self.getXSValue(_xsDataISPyBDiffractionPlan.preferredBeamSizeX)
        fPreferredBeamSizeY = self.getXSValue(_xsDataISPyBDiffractionPlan.preferredBeamSizeY)
        fPreferredBeamDiameter = self.getXSValue(_xsDataISPyBDiffractionPlan.preferredBeamDiameter)
        strComments = self.getXSValue(_xsDataISPyBDiffractionPlan.comments)
        fAimedCompleteness = self.getXSValue(_xsDataISPyBDiffractionPlan.aimedCompleteness)
        fAimedIOverSigmaAtHighestResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.aimedIOverSigmaAtHighestResolution)
        fAimedMultiplicity = self.getXSValue(_xsDataISPyBDiffractionPlan.aimedMultiplicity)
        fAimedResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.aimedResolution)
        bAnomalousData = self.getXSValue(_xsDataISPyBDiffractionPlan.anomalousData, _oDefaultValue=False)
        strComplexity = self.getXSValue(_xsDataISPyBDiffractionPlan.complexity)
        bEstimateRadiationDamage = self.getXSValue(_xsDataISPyBDiffractionPlan.estimateRadiationDamage, _oDefaultValue=False)
        strForcedSpaceGroup = self.getXSValue(_xsDataISPyBDiffractionPlan.forcedSpaceGroup)
        fRequiredCompleteness = self.getXSValue(_xsDataISPyBDiffractionPlan.requiredCompleteness)
        fRequiredMultiplicity = self.getXSValue(_xsDataISPyBDiffractionPlan.requiredMultiplicity)
        fRequiredResolution = self.getXSValue(_xsDataISPyBDiffractionPlan.requiredResolution)
        strStrategyOption = self.getXSValue(_xsDataISPyBDiffractionPlan.strategyOption)
        strKappaStrategyOption = self.getXSValue(_xsDataISPyBDiffractionPlan.kappaStrategyOption)
        iNumberOfPositions = self.getXSValue(_xsDataISPyBDiffractionPlan.numberOfPositions)
        fMinOscWidth = self.getXSValue(_xsDataISPyBDiffractionPlan.minOscWidth)
        iDiffractionPlanId = _clientToolsForBLSampleWebServiceWsdl.service.storeOrUpdateDiffractionPlan(
            arg0=iDiffractionPlanId, \
            experimentKind=strExperimentKind, \
            observedResolution=fObservedResolution, \
            minimalResolution=fMinimalResolution, \
            exposureTime=fExposureTime, \
            oscillationRange=fOscillationRange, \
            maximalResolution=fMaximalResolution, \
            screeningResolution=fScreeningResolution, \
            radiationSensitivity=fRadiationSensitivity, \
            anomalousScatterer=strAnomalousScatterer, \
            preferredBeamSizeX=fPreferredBeamSizeX, \
            preferredBeamSizeY=fPreferredBeamSizeY, \
            preferredBeamDiameter=fPreferredBeamDiameter, \
            comments=strComments, \
            aimedCompleteness=fAimedCompleteness, \
            aimedIOverSigmaAtHighestRes=fAimedIOverSigmaAtHighestResolution, \
            aimedMultiplicity=fAimedMultiplicity, \
            aimedResolution=fAimedResolution, \
            anomalousData=bAnomalousData, \
            complexity=strComplexity, \
            estimateRadiationDamage=bEstimateRadiationDamage, \
            forcedSpaceGroup=strForcedSpaceGroup, \
            requiredCompleteness=fRequiredCompleteness, \
            requiredMultiplicity=fRequiredMultiplicity, \
            requiredResolution=fRequiredResolution, \
            strategyOption=strStrategyOption, \
            kappaStrategyOption=strKappaStrategyOption, \
            numberOfPositions=iNumberOfPositions, \
            minOscWidth=fMinOscWidth, \
            )
        self.DEBUG("DiffractionPlanId: %d" % iDiffractionPlanId)
        return iDiffractionPlanId


    def storeOrUpdateScreening(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreening, _iDiffractionPlanId):
        """Creates an entry in ISPyB for the Screening table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreening")
        iScreeningId = self.getXSValue(_xsDataISPyBScreening.screeningId)
        iDataCollectionGroupId = self.getXSValue(_xsDataISPyBScreening.dataCollectionGroupId)
        iDiffractionPlanId = _iDiffractionPlanId
        strTimeStamp = DateTime(datetime.datetime.now())
        strProgramVersion = self.getXSValue(_xsDataISPyBScreening.programVersion, _iMaxStringLength=45)
        strComments = self.getXSValue(_xsDataISPyBScreening.comments, _iMaxStringLength=255)
        strShortComments = self.getXSValue(_xsDataISPyBScreening.shortComments, _iMaxStringLength=20)
        strXmlSampleInformation = self.getXSValue(_xsDataISPyBScreening.xmlSampleInformation)
        iScreeningId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreening(
            arg0=iScreeningId, \
            dataCollectionGroupId=iDataCollectionGroupId, \
            diffractionPlanId=iDiffractionPlanId, \
            recordTimeStamp=strTimeStamp, \
            programVersion=strProgramVersion, \
            comments=strComments, \
            shortComments=strShortComments, \
            xmlSampleInformation=strXmlSampleInformation, \
            )
        self.DEBUG("ScreeningId: %d" % iScreeningId)
        return iScreeningId



    def storeOrUpdateScreeningOutput(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningOutput, _iScreeningId):
        """Creates an entry in ISPyB for the ScreeningOutput table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningOutput")
        iScreeningOutputId = self.getXSValue(_xsDataISPyBScreeningOutput.screeningOutputId)
        iScreeningId = _iScreeningId
        strStatusDescription = self.getXSValue(_xsDataISPyBScreeningOutput.statusDescription, _iMaxStringLength=1024)
        iRejectedReflections = self.getXSValue(_xsDataISPyBScreeningOutput.rejectedReflections)
        fResolutionObtained = self.getXSValue(_xsDataISPyBScreeningOutput.resolutionObtained)
        fSpotDeviationR = self.getXSValue(_xsDataISPyBScreeningOutput.spotDeviationR)
        fSpotDeviationTheta = self.getXSValue(_xsDataISPyBScreeningOutput.spotDeviationTheta)
        fBeamShiftX = self.getXSValue(_xsDataISPyBScreeningOutput.beamShiftX)
        fBeamShiftY = self.getXSValue(_xsDataISPyBScreeningOutput.beamShiftY)
        iNumSpotsFound = self.getXSValue(_xsDataISPyBScreeningOutput.numSpotsFound)
        iNumSpotsUsed = self.getXSValue(_xsDataISPyBScreeningOutput.numSpotsUsed)
        iNumSpotsRejected = self.getXSValue(_xsDataISPyBScreeningOutput.numSpotsRejected)
        fMosaicity = self.getXSValue(_xsDataISPyBScreeningOutput.mosaicity)
        fIOverSigma = self.getXSValue(_xsDataISPyBScreeningOutput.iOverSigma)
        bDiffractionRings = self.getXSValue(_xsDataISPyBScreeningOutput.diffractionRings, _oDefaultValue=False)
        bIndexingSuccess = self.getXSValue(_xsDataISPyBScreeningOutput.indexingSuccess, _oDefaultValue=False)
        bStrategySuccess = self.getXSValue(_xsDataISPyBScreeningOutput.strategySuccess, _oDefaultValue=False)
        bMosaicityEstimated = self.getXSValue(_xsDataISPyBScreeningOutput.mosaicityEstimated, _oDefaultValue=False)
        fRankingResolution = self.getXSValue(_xsDataISPyBScreeningOutput.rankingResolution)
        strProgram = self.getXSValue(_xsDataISPyBScreeningOutput.program, _iMaxStringLength=45)
        fDoseTotal = self.getXSValue(_xsDataISPyBScreeningOutput.doseTotal)
        fTotalExposureTime = self.getXSValue(_xsDataISPyBScreeningOutput.totalExposureTime)
        fTotalRotationRange = self.getXSValue(_xsDataISPyBScreeningOutput.totalRotationRange)
        fTotalNumberOfImages = self.getXSValue(_xsDataISPyBScreeningOutput.totalNumberOfImages)
        fRFriedel = self.getXSValue(_xsDataISPyBScreeningOutput.rFriedel)
        iScreeningOutputId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningOutput(
            iScreeningOutputId, \
            screeningId=iScreeningId, \
            statusDescription=strStatusDescription, \
            rejectedReflections=iRejectedReflections, \
            resolutionObtained=fResolutionObtained, \
            spotDeviationR=fSpotDeviationR, \
            spotDeviationTheta=fSpotDeviationTheta, \
            beamShiftX=fBeamShiftX, \
            beamShiftY=fBeamShiftY, \
            numSpotsFound=iNumSpotsFound, \
            numSpotsUsed=iNumSpotsUsed, \
            numSpotsRejected=iNumSpotsRejected, \
            mosaicity=fMosaicity, \
            ioverSigma=fIOverSigma, \
            diffractionRings=bDiffractionRings, \
            strategySuccess=bStrategySuccess, \
            indexingSuccess=bIndexingSuccess, \
            mosaicityEstimated=bMosaicityEstimated, \
            rankingResolution=fRankingResolution, \
            program=strProgram, \
            doseTotal=fDoseTotal, \
            totalExposureTime=fTotalExposureTime, \
            totalRotationRange=fTotalRotationRange, \
            totalNumberOfImages=fTotalNumberOfImages, \
            rFriedel=fRFriedel, \
            )
        self.DEBUG("ScreeningOutputId: %d" % iScreeningOutputId)
        return iScreeningOutputId

    def storeOrUpdateScreeningOutputLattice(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningOutputLattice, _iScreeningOutputId):
        """Creates an entry in ISPyB for the ScreeningOutputLattice table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningOutputLattice")
        iScreeningOutputLatticeId = self.getXSValue(_xsDataISPyBScreeningOutputLattice.screeningOutputLatticeId)
        iScreeningOutputId = _iScreeningOutputId
        strSpaceGroup = self.getXSValue(_xsDataISPyBScreeningOutputLattice.spaceGroup, _iMaxStringLength=45)
        strPointGroup = self.getXSValue(_xsDataISPyBScreeningOutputLattice.pointGroup, _iMaxStringLength=45)
        strBravaisLattice = self.getXSValue(_xsDataISPyBScreeningOutputLattice.bravaisLattice, _iMaxStringLength=45)
        fRawOrientationMatrix_a_x = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_a_x)
        fRawOrientationMatrix_a_y = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_a_y)
        fRawOrientationMatrix_a_z = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_a_z)
        fRawOrientationMatrix_b_x = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_b_x)
        fRawOrientationMatrix_b_y = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_b_y)
        fRawOrientationMatrix_b_z = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_b_z)
        fRawOrientationMatrix_c_x = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_c_x)
        fRawOrientationMatrix_c_y = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_c_y)
        fRawOrientationMatrix_c_z = self.getXSValue(_xsDataISPyBScreeningOutputLattice.rawOrientationMatrix_c_z)
        fUnitCell_a = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_a)
        fUnitCell_b = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_b)
        fUnitCell_c = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_c)
        fUnitCell_alpha = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_alpha)
        fUnitCell_beta = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_beta)
        fUnitCell_gamma = self.getXSValue(_xsDataISPyBScreeningOutputLattice.unitCell_gamma)
        strTimeStamp = DateTime(datetime.datetime.now())
        bLabelitIndexing = self.getXSValue(_xsDataISPyBScreeningOutputLattice.labelitIndexing, _oDefaultValue=False)
        iScreeningOutputLatticeId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningOutputLattice(
            iScreeningOutputLatticeId, \
            iScreeningOutputId, \
            strSpaceGroup, \
            strPointGroup, \
            strBravaisLattice, \
            fRawOrientationMatrix_a_x, \
            fRawOrientationMatrix_a_y, \
            fRawOrientationMatrix_a_z, \
            fRawOrientationMatrix_b_x, \
            fRawOrientationMatrix_b_y, \
            fRawOrientationMatrix_b_z, \
            fRawOrientationMatrix_c_x, \
            fRawOrientationMatrix_c_y, \
            fRawOrientationMatrix_c_z, \
            fUnitCell_a, \
            fUnitCell_b, \
            fUnitCell_c, \
            fUnitCell_alpha, \
            fUnitCell_beta, \
            fUnitCell_gamma, \
            strTimeStamp, \
            bLabelitIndexing, \
            )
        self.DEBUG("ScreeningOutputLatticeId: %d" % iScreeningOutputLatticeId)
        return iScreeningOutputLatticeId

    def storeOrUpdateScreeningStrategy(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningStrategy, _iScreeningOutputId):
        """Creates an entry in ISPyB for the ScreeningStrategy table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningStrategy")
        iScreeningStrategyId = self.getXSValue(_xsDataISPyBScreeningStrategy.screeningStrategyId)
        iScreeningOutputId = _iScreeningOutputId
        fPhiStart = self.getXSValue(_xsDataISPyBScreeningStrategy.phiStart)
        fPhiEnd = self.getXSValue(_xsDataISPyBScreeningStrategy.phiEnd)
        fRotation = self.getXSValue(_xsDataISPyBScreeningStrategy.rotation)
        fExposureTime = self.getXSValue(_xsDataISPyBScreeningStrategy.exposureTime)
        fResolution = self.getXSValue(_xsDataISPyBScreeningStrategy.resolution)
        fCompleteness = self.getXSValue(_xsDataISPyBScreeningStrategy.completeness)
        fMultiplicity = self.getXSValue(_xsDataISPyBScreeningStrategy.multiplicity)
        bAnomalous = self.getXSValue(_xsDataISPyBScreeningStrategy.anomalous, _oDefaultValue=False)
        strProgram = self.getXSValue(_xsDataISPyBScreeningStrategy.program, _iMaxStringLength=45)
        fRankingResolution = self.getXSValue(_xsDataISPyBScreeningStrategy.rankingResolution)
        fTransmission = self.getXSValue(_xsDataISPyBScreeningStrategy.transmission)
        iScreeningStrategyId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningStrategy(
            iScreeningStrategyId, \
            iScreeningOutputId, \
            fPhiStart, \
            fPhiEnd, \
            fRotation, \
            fExposureTime, \
            fResolution, \
            fCompleteness, \
            fMultiplicity, \
            bAnomalous, \
            strProgram, \
            fRankingResolution, \
            fTransmission, \
            )
        self.DEBUG("ScreeningStrategyId: %d" % iScreeningStrategyId)
        return iScreeningStrategyId

    def storeOrUpdateScreeningStrategyWedge(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningStrategyWedge, _iScreeningStrategyId):
        """Creates an entry in ISPyB for the ScreeningStrategyWedge table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningStrategyWedge")
        iScreeningStrategyWedgeId = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.screeningStrategyWedgeId)
        iScreeningStrategyId = _iScreeningStrategyId
        iWedgeNumber = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.wedgeNumber)
        fResolution = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.resolution)
        fCompleteness = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.completeness)
        fMultiplicity = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.multiplicity)
        fDoseTotal = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.doseTotal)
        iNumberOfImages = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.numberOfImages)
        fPhi = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.phi)
        fKappa = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.kappa)
        fChi = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.chi)
        strComments = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.comments, _iMaxStringLength=255)
        fWavelength = self.getXSValue(_xsDataISPyBScreeningStrategyWedge.wavelength)
        iScreeningStrategyWedgeId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningStrategyWedge(
            arg0=iScreeningStrategyWedgeId, \
            screeningStrategyId=iScreeningStrategyId, \
            wedgeNumber=iWedgeNumber, \
            resolution=fResolution, \
            completeness=fCompleteness, \
            multiplicity=fMultiplicity, \
            doseTotal=fDoseTotal, \
            numberOfImages=iNumberOfImages, \
            phi=fPhi, \
            kappa=fKappa, \
            chi=fChi, \
            comments=strComments, \
            wavelength=fWavelength, \
            )
        self.DEBUG("ScreeningStrategyWedgeId: %d" % iScreeningStrategyWedgeId)
        return iScreeningStrategyWedgeId

    def storeOrUpdateScreeningStrategySubWedge(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningStrategySubWedge, _iScreeningStrategyWedgeId):
        """Creates an entry in ISPyB for the ScreeningStrategySubWedge table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningStrategySubWedge")
        iScreeningStrategySubWedgeId = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.screeningStrategySubWedgeId)
        iScreeningStrategyWedgeId = _iScreeningStrategyWedgeId
        iSubWedgeNumber = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.subWedgeNumber)
        strRotationAxis = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.rotationAxis, _iMaxStringLength=45)
        fAxisStart = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.axisStart)
        fAxisEnd = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.axisEnd)
        fExposureTime = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.exposureTime)
        fTransmission = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.transmission)
        fOscillationRange = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.oscillationRange)
        fCompleteness = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.completeness)
        fMultiplicity = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.multiplicity)
        fDoseTotal = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.doseTotal)
        iNumberOfImages = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.numberOfImages)
        strComments = self.getXSValue(_xsDataISPyBScreeningStrategySubWedge.comments, _iMaxStringLength=255)
        iScreeningStrategySubWedgeId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningStrategySubWedge(
            iScreeningStrategySubWedgeId, \
            iScreeningStrategyWedgeId, \
            iSubWedgeNumber, \
            strRotationAxis, \
            fAxisStart, \
            fAxisEnd, \
            fExposureTime, \
            fTransmission, \
            fOscillationRange, \
            fCompleteness, \
            fMultiplicity, \
            fDoseTotal, \
            iNumberOfImages, \
            strComments, \
            )
        self.DEBUG("ScreeningStrategySubWedgeId: %d" % iScreeningStrategySubWedgeId)
        return iScreeningStrategySubWedgeId

    def storeOrUpdateScreeningInput(self, _clientToolsForScreeningEDNAWebServiceWsdl, _xsDataISPyBScreeningInput, _iScreeningId, _iDiffractionPlanId):
        """Creates an entry in ISPyB for the ScreeningInput table"""
        self.DEBUG("EDPluginISPyBStoreScreeningv1_4.storeScreeningInput")
        iScreeningInputId = self.getXSValue(_xsDataISPyBScreeningInput.screeningInputId)
        iScreeningId = _iScreeningId
        iDiffractionPlanId = _iDiffractionPlanId
        fBeamX = self.getXSValue(_xsDataISPyBScreeningInput.beamX)
        fBeamY = self.getXSValue(_xsDataISPyBScreeningInput.beamY)
        fRmsErrorLimits = self.getXSValue(_xsDataISPyBScreeningInput.rmsErrorLimits)
        fMinimumFractionIndexed = self.getXSValue(_xsDataISPyBScreeningInput.minimumFractionIndexed)
        fMaximumFractionRejected = self.getXSValue(_xsDataISPyBScreeningInput.maximumFractionRejected)
        fMinimumSignalToNoise = self.getXSValue(_xsDataISPyBScreeningInput.minimumSignalToNoise)
        strXmlSampleInformation = self.getXSValue(_xsDataISPyBScreeningInput.xmlSampleInformation)
        iScreeningInputId = _clientToolsForScreeningEDNAWebServiceWsdl.service.storeOrUpdateScreeningInput(
            iScreeningInputId, \
            iScreeningId, \
            iDiffractionPlanId, \
            fBeamX, \
            fBeamY, \
            fRmsErrorLimits, \
            fMinimumFractionIndexed, \
            fMaximumFractionRejected, \
            fMinimumSignalToNoise, \
            strXmlSampleInformation, \
            )
        self.DEBUG("ScreeningInputId: %d" % iScreeningInputId)
        return iScreeningInputId


