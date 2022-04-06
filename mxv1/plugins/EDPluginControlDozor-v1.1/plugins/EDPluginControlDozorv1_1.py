# coding: utf8
#
#    Project: MXv1
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
#import xmlrpclib
from xmlrpc import client

import socket
import sys

from EDPluginControl import EDPluginControl
from EDUtilsImage import EDUtilsImage

from XSDataCommon import XSDataInteger
from XSDataCommon import XSDataDouble
from XSDataCommon import XSDataString
from XSDataCommon import XSDataFile
from XSDataCommon import XSDataTime

from EDFactoryPluginStatic import EDFactoryPluginStatic
EDFactoryPluginStatic.loadModule("XSDataDozorv1_0")
from XSDataDozorv1_0 import XSDataInputDozor

from XSDataMXv1 import XSDataInputReadImageHeader

EDFactoryPluginStatic.loadModule("XSDataMXWaitFilev1_1")
from XSDataMXWaitFilev1_1 import XSDataInputMXWaitFile

from XSDataControlDozorv1_1 import XSDataInputControlDozor
from XSDataControlDozorv1_1 import XSDataResultControlDozor
from XSDataControlDozorv1_1 import XSDataControlImageDozor

class EDPluginControlDozorv1_1(EDPluginControl):
    """
    This plugin runs the Dozor program written by Sasha Popov
    """
    

    def __init__(self):
        EDPluginControl.__init__(self)
        self.setXSDataInputClass(XSDataInputControlDozor)
        self.setDataOutput(XSDataResultControlDozor())
        self.strEDPluginControlReadImageHeaderName = "EDPluginControlReadImageHeaderv10"
        self.strPluginMXWaitFile = "EDPluginMXWaitFilev1_1"
        self.edPluginControlReadImageHeader = None
        self.strEDPluginDozorName = "EDPluginDozorv1_0"
        self.edPluginDozor = None
        self._strMxCuBE_URI = None
        self._oServerProxy = None
        self.setTimeOut(9999)

    def checkParameters(self):
        """
        Checks the mandatory parameters.
        """
        self.DEBUG("EDPluginControlDozorv1_1.checkParameters")
        self.checkMandatoryParameters(self.dataInput, "Data Input is None")

        self._strMxCuBE_URI = self.config.get("mxCuBE_URI", None)
        print(self.config)
        if self._strMxCuBE_URI is not None:
            self.DEBUG("Enabling sending messages to mxCuBE via URI {0}".format(self._strMxCuBE_URI))
            #self._oServerProxy = xmlrpclib.ServerProxy(self._strMxCuBE_URI, allow_none=True)
            self._oServerProxy = client.ServerProxy(self._strMxCuBE_URI, allow_none=True)
            self.get_image_num = self._oServerProxy.get_image_num 
    
    def preProcess(self, _edObject=None):
        EDPluginControl.preProcess(self)
        self.DEBUG("EDPluginControlDozorv1_1.preProcess")
        #self.edPluginControlReadImageHeader = self.loadPlugin(self.strEDPluginControlReadImageHeaderName, "SubWedgeAssemble")
        #self.edPluginDozor = self.loadPlugin(self.strEDPluginDozorName, "Dozor")

    def process(self, _edObject=None):
        EDPluginControl.process(self)
        self.DEBUG("EDPluginControlDozorv1_1.process") 
        msg = "EDPluginControlDozorXmlRpcv1_0 started..."
        self.sendMessageToMXCuBE("Processing started...", "info")
        xsDataResultControlDozor = XSDataResultControlDozor()

        firstFileName = self.dataInput.template.value % (self.dataInput.first_run_number.value,
                                                         self.dataInput.first_image_number.value)
       
        fWaitFileTimeout = 180 #sec

        self.waitFileFirst = self.loadPlugin("EDPluginMXWaitFilev1_1", "MXWaitFileFirst")
        xsDataInputMXWaitFileFirst = XSDataInputMXWaitFile()
        xsDataInputMXWaitFileFirst.file = XSDataFile(XSDataString(firstFileName))
        xsDataInputMXWaitFileFirst.timeOut = XSDataTime(fWaitFileTimeout)

         
        self.waitFileFirst.size = XSDataInteger(1000000)
        self.waitFileFirst.dataInput = xsDataInputMXWaitFileFirst
        self.waitFileFirst.executeSynchronous()
        if self.waitFileFirst.dataOutput.timedOut.value:
            strWarningMessage = "Timeout after %d seconds waiting for the first image %s!" % (fWaitFileTimeout, firstFileName)
            #self.addWarningMessage(strWarningMessage)
            #self.WARNING(strWarningMessage)
            #self.sendMessageToMXCuBE(strWarningMessage, "error")

        edPluginControlReadImageHeader = self.loadPlugin(self.strEDPluginControlReadImageHeaderName)
        xsDataInputReadImageHeader = XSDataInputReadImageHeader()
        xsDataInputReadImageHeader.image = XSDataFile(XSDataString(firstFileName))

        edPluginControlReadImageHeader.dataInput = xsDataInputReadImageHeader
        edPluginControlReadImageHeader.executeSynchronous()
        subWedge = edPluginControlReadImageHeader.dataOutput.subWedge

        xsDataInputDozor = XSDataInputDozor()
        beam = subWedge.experimentalCondition.beam
        detector = subWedge.experimentalCondition.detector
        goniostat = subWedge.experimentalCondition.goniostat
        xsDataInputDozor.detectorType = detector.type
        xsDataInputDozor.exposureTime = XSDataDouble(beam.exposureTime.value)
        #xsDataInputDozor.spotSize = XSDataDouble(3.0)
        xsDataInputDozor.spotSize = XSDataInteger(3)
        xsDataInputDozor.detectorDistance = XSDataDouble(detector.distance.value)
        xsDataInputDozor.wavelength = XSDataDouble(beam.wavelength.value)
        orgx = detector.beamPositionY.value / detector.pixelSizeY.value
        orgy = detector.beamPositionX.value / detector.pixelSizeX.value
        xsDataInputDozor.orgx = XSDataDouble(orgx)
        xsDataInputDozor.orgy = XSDataDouble(orgy)

        # GB: the 50 might need tunig to CPU speed and number of. 2000 is a current limit of Dozor.  
        self.maxChunkSize = 4000 #a min (150 * 2527 * 2463 /detector.numberPixelX.value / detector.numberPixelY.value, 2000)

        _beamstop = self.beamstop(detector)
        if _beamstop is not None:
            #self.WARNING("Setting beamstop shadow: %s"%_beamstop)
            xsDataInputDozor.ixMin = XSDataInteger(_beamstop['ix_min'])
            xsDataInputDozor.iyMin = XSDataInteger(_beamstop['iy_min'])
            xsDataInputDozor.ixMax = XSDataInteger(_beamstop['ix_max'])
            xsDataInputDozor.iyMax = XSDataInteger(_beamstop['iy_max'])
          
        if self.dataInput.pixelMin is not None:
            xsDataInputDozor.pixelMin = self.dataInput.pixelMin
          
        if self.dataInput.pixelMax is not None:
            xsDataInputDozor.pixelMax = self.dataInput.pixelMax
         
        _serial = 0
        _startTime = time.time() 
        chunk_list = self.schedule(goniostat.rotationAxisStart.value,goniostat.oscillationWidth.value) 

        for chunk in chunk_list:

            if not self.poll_file(self.dataInput.template.value%(chunk['run_number'],chunk['first']+chunk['number_of']-1), (beam.exposureTime.value+0.003) * chunk['number_of'] + 30 ):
                self.sendMessageToMXCuBE("Timeout waiting for frame: %d"%(chunk['first']+chunk['number_of']), level="error")
                return

            xsDataInputDozor.oscillationRange = XSDataDouble(chunk['rotation_range'])
            xsDataInputDozor.startingAngle = XSDataDouble(chunk['rotation_start'])
            xsDataInputDozor.firstImageNumber = XSDataInteger(chunk['first'])
            xsDataInputDozor.numberImages = XSDataInteger(chunk['number_of'])

            strFileName = self.dataInput.template.value%(chunk['run_number'],chunk['first'])
            strXDSTemplate = EDUtilsImage.getTemplate(strFileName,'?')
            xsDataInputDozor.nameTemplateImage = XSDataString(os.path.join(os.path.dirname(strFileName), strXDSTemplate))

            edPluginDozor = self.loadPlugin(self.strEDPluginDozorName,"Dozor")
            edPluginDozor.dataInput = xsDataInputDozor
            
            edPluginDozor.executeSynchronous()
                      
            xsDataChunkResultControlImageDozor = XSDataResultControlDozor()            

            dozor_batch_list = []#[[1,4,3,8,6],
                                #[2, 5, 3, 3, 7],[1, 3, 12, 11, 4],[4, 2, 3, 5, 7]]
            #ozor_image_dict = {}
            diff_image_count = 0

            xsDataControlImageDozor = XSDataControlImageDozor()            
 
            for xsDataResultDozor in edPluginDozor.dataOutput.imageDozor: 
                xsDataControlImageDozor = XSDataControlImageDozor()

                xsDataControlImageDozor.number = xsDataResultDozor.number
                strFileName = self.dataInput.template.value%(chunk['run_number'],xsDataControlImageDozor.number.value)           
                xsDataControlImageDozor.image = XSDataFile(XSDataString(strFileName))

                xsDataControlImageDozor.spots_num_of = xsDataResultDozor.spotsNumOf
                xsDataControlImageDozor.spots_int_aver = xsDataResultDozor.spotsIntAver
                xsDataControlImageDozor.spots_resolution = xsDataResultDozor.spotsResolution
                xsDataControlImageDozor.powder_wilson_scale = xsDataResultDozor.powderWilsonScale
                xsDataControlImageDozor.powder_wilson_bfactor = xsDataResultDozor.powderWilsonBfactor
                xsDataControlImageDozor.powder_wilson_resolution = xsDataResultDozor.powderWilsonResolution
                xsDataControlImageDozor.powder_wilson_correlation = xsDataResultDozor.powderWilsonCorrelation
                xsDataControlImageDozor.powder_wilson_rfactor = xsDataResultDozor.powderWilsonRfactor
                xsDataControlImageDozor.score = xsDataResultDozor.mainScore
                xsDataResultControlDozor.addImageDozor(xsDataControlImageDozor)           

                dozor_batch_list.append((xsDataControlImageDozor.number.getValue(),
                                         xsDataControlImageDozor.spots_num_of.getValue(),
                                         xsDataControlImageDozor.spots_int_aver.getValue(),
                                         xsDataControlImageDozor.spots_resolution.getValue(),
                                         xsDataControlImageDozor.score.getValue()))
                if xsDataControlImageDozor.spots_num_of.getValue() > 0:
                    diff_image_count += 1
                xsDataChunkResultControlImageDozor.addImageDozor(xsDataControlImageDozor)
            
            xsDataChunkResultControlImageDozor.exportToFile("ResultControlDozor_Chunk_%06d.xml"%_serial)

            self.sendResultToMXCuBE(dozor_batch_list)

            _serial += 1
            self.screen("Chunk %d/%d done in %.3f seconds" % \
                 (_serial, len(chunk_list), time.time()-_startTime))
            self.sendMessageToMXCuBE("Chunk %d/%d done in %.2f sec., num diffr. frames: %d/%d" % \
                                     (_serial,
                                      len(chunk_list),
                                      time.time() - _startTime,
                                      diff_image_count,
                                      len(dozor_batch_list)
                                     )
                                    )
            
            _startTime=time.time()

        #self.dataOutput = xsDataResultControlDozor   
  
    def poll_file(self,_strFile,_timeOut):
        _startTime = time.time()
        _waitTime = 0
        while _waitTime <= _timeOut : 
            if os.path.exists(_strFile):
                return True
            if _waitTime == 0:
                self.screen("Start waiting for %s"%_strFile)
            #TODO check this timeout
            time.sleep(0.2)
            _waitTime = time.time() - _startTime 
        self.WARNING("Time out while waiting for file %s"%_strFile)
        return False

    def beamstop(self,_xsDetector):
        if None in [self.dataInput.beamstopDirection, 
                    self.dataInput.beamstopSize,
                    self.dataInput.beamstopDistance] : 
           return None
        mmDelta = 0.5 * self.dataInput.beamstopSize.value * _xsDetector.distance.value / self.dataInput.beamstopDistance.value
        # GB: This is dirty !!!
        # _xsDetector.beamPositionX and _xsDetector.beamPositionY are swapped, in the same way as in the process() method! 
        # but _xsDetector.numberPixelX.value and _xsDetector.numberPixelY.value are in the "correct" order!
        #
        if self.dataInput.beamstopDirection.value.upper() == '-X' :
           return {'ix_min' : 1,
                   'iy_min' : int (( _xsDetector.beamPositionX.value - mmDelta ) / _xsDetector.pixelSizeX.value),
                   'ix_max' : int (_xsDetector.beamPositionY.value / _xsDetector.pixelSizeX.value ),
                   'iy_max' : int (( _xsDetector.beamPositionX.value + mmDelta ) / _xsDetector.pixelSizeX.value)}

        elif self.dataInput.beamstopDirection.value.upper() == 'X' :
           return {'ix_min' : int(_xsDetector.beamPositionY.value / _xsDetector.pixelSizeY.value ),
                   'iy_min' : int((_xsDetector.beamPositionX.value - mmDelta ) / _xsDetector.pixelSizeX.value),
                   'ix_max' : _xsDetector.numberPixelX.value,
                   'iy_max' : int((_xsDetector.beamPositionX.value + mmDelta) / _xsDetector.pixelSizeX.value)}

        elif self.dataInput.beamstopDirection.value.upper() == 'Y' :
           return {'ix_min' : int(( _xsDetector.beamPositionY.value - mmDelta) / _xsDetector.pixelSizeY.value),
                   'iy_min' : int(_xsDetector.beamPositionX.value / _xsDetector.pixelSizeX.value),
                   'ix_max' : int(( _xsDetector.beamPositionY.value + mmDelta ) / _xsDetector.pixelSizeY.value),
                   'iy_max' : _xsDetector.numberPixelY.value }

        elif self.dataInput.beamstopDirection.value.upper() == '-Y' :
           return {'ix_min' : int(( _xsDetector.beamPositionY.value - mmDelta) / _xsDetector.pixelSizeY.value),
                   'iy_min' : 1 ,
                   'ix_max' : int(( _xsDetector.beamPositionY.value + mmDelta ) / _xsDetector.pixelSizeY.value),
                   'iy_max' : int(_xsDetector.beamPositionX.value / _xsDetector.pixelSizeX.value) }
                    

    def schedule(self,rotation_start, rotation_range):

        first_image_number = self.dataInput.first_image_number.value
        last_image_number = self.dataInput.last_image_number.value         
        first_run_number = self.dataInput.first_run_number.value
        last_run_number = self.dataInput.last_run_number.value
        line_number_of = self.dataInput.line_number_of.value

        if line_number_of == 1:
            line_number_of = last_image_number / 60

        reversing_rotation = self.dataInput.reversing_rotation.value
 
        total_images = (last_image_number - first_image_number + 1 ) * (last_run_number - first_run_number + 1)
        images_per_line = total_images / line_number_of
        #if images_per_line * line_number_of != total_images:
        #   print "image/run/line numbers mismatch"
        chunk = 1000000
        chunks = 0
        while chunk > self.maxChunkSize:
            chunks = chunks + 1
            chunk = images_per_line / chunks
            run_number = first_run_number
            last_frame = 0
            res = []
            for line in range(line_number_of):
               if reversing_rotation and line%2 :
                  line_rotation_start = rotation_start + images_per_line * rotation_range
                  line_rotation_range = -rotation_range
               else:
                  line_rotation_start = rotation_start
                  line_rotation_range = rotation_range
               for x in range(chunks):
                   first_frame = last_frame + 1
                   if x == chunks-1:
                      if first_run_number != last_run_number:
                         last_frame = last_image_number
                      else:
                         last_frame = first_image_number + (line + 1) * images_per_line - 1
                   else:
                      last_frame = first_frame + chunk - 1
                   chunk_rotation_start = line_rotation_start + x * line_rotation_range * chunk
                   res.append({'run_number': run_number,
                               'first' : first_frame,
                               'number_of' : last_frame - first_frame + 1,
                               'rotation_start' : chunk_rotation_start,
                               'rotation_range' : line_rotation_range })
               if first_run_number != last_run_number:
                  run_number = run_number + 1
                  last_frame = 0
               else:
                   last_last_frame = x * chunk + 1
        return res

    def postProcess(self, _edObject=None):
        EDPluginControl.postProcess(self)
        #if self.failed:
        #    self.sendMessageToMXCuBE("Processing failed!", "error")
        #    self.setStatusToMXCuBE("Failed")
        #else:
        self.sendMessageToMXCuBE("Processing finished", "info")
        self.setStatusToMXCuBE("Success")

    def sendMessageToMXCuBE(self, _strMessage, level = "info"):
        self.DEBUG("Sending message to mxCuBE: {0}".format(_strMessage))
        try:
            for strMessage in _strMessage.split("\n"):
                if strMessage != "":
                    self._oServerProxy.log_message("EDNA | Dozor: " + _strMessage, level)
        except AttributeError:
            self.WARNING("Cannot send message to MXCuBE, proxy not configured")
        except Exception as ex:
            self.ERROR("Sending dozor batch data to mxCuBE failed! %s" % str(ex))

    def sendResultToMXCuBE(self, _batchData):
        self.DEBUG("Sending dozor batch data to mxCuBE %s" % _batchData)
        try:
            self._oServerProxy.dozor_batch_processed(_batchData)
        except AttributeError:
            self.WARNING("Cannot send results to MXCuBE, proxy not configured")
        except Exception as ex:
            self.ERROR("Sending dozor batch data to mxCuBE failed! %s" % str(ex))

    def setStatusToMXCuBE(self, status):
        self.DEBUG("Sending dozor status %s to mxCuBE" % status)
        try:
            self._oServerProxy.dozor_status_changed(status)
        except AttributeError:
            self.WARNING("Cannot set status to MXCuBE, proxy not configured")
        except Exception as ex:
            self.ERROR("Sending dozor status to mxCuBE failed! %s" % str(ex))
