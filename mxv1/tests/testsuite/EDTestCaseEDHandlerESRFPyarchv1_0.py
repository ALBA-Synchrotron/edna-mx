#
#    Project: EDNA MXv1
#             http://www.edna-site.org
#
#    Copyright (C) 2012      European Synchrotron Radiation Facility
#                            Grenoble, France
#
#    Principal authors:      Olof Svensson (svensson@esrf.fr)
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
__copyright__ = "Copyrigth (c) 2010 ESRF"

import os
import time
import shutil

from EDAssert import EDAssert
from EDVerbose import EDVerbose
from EDTestCasePluginUnit import EDTestCasePluginUnit
from EDHandlerESRFPyarchv1_0 import EDHandlerESRFPyarchv1_0
from EDUtilsPath import EDUtilsPath
from EDUtilsFile import EDUtilsFile

from XSDataCommon import XSDataInput
from XSDataMXv1 import XSDataCollection

class EDTestCaseEDHandlerESRFPyarchv1_0(EDTestCasePluginUnit):


    def __init__(self, _edStringTestName=None):
        EDTestCasePluginUnit.__init__(self, "EDHandlerESRFPyarchv1_0")


    def testCreatePyarchFilePath(self):
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/"), "/")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data"), "/data")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor"), "/data/visitor")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id14eh2"), "/data/visitor/mx415/id14eh2")
        EDAssert.equal("/data/pyarch/2010/id14eh2/mx415/20100212",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id14eh2/20100212"),
                       "/data/visitor/mx415/id14eh2/20100212")
        EDAssert.equal("/data/pyarch/2010/id14eh2/mx415/20100212/1",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id14eh2/20100212/1"),
                       "/data/visitor/mx415/id14eh2/20100212/1")
        EDAssert.equal("/data/pyarch/2010/id14eh2/mx415/20100212/1/2",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id14eh2/20100212/1/2"),
                       "/data/visitor/mx415/id14eh2/20100212/1/2")
        # Test with inhouse account...
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/"), "/")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data"), "/data")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2"), "/data/id23eh2")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2/inhouse"), "/data/id23eh2/inhouse")
        EDAssert.equal(None, EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2/inhouse/opid232"), "/data/id23eh2/inhouse/opid232")
        EDAssert.equal("/data/pyarch/2010/id23eh2/opid232/20100525",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2/inhouse/opid232/20100525"),
                       "/data/id23eh2/inhouse/opid232/20100525")
        EDAssert.equal("/data/pyarch/2010/id23eh2/opid232/20100525/1",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2/inhouse/opid232/20100525/1"),
                       "/data/id23eh2/inhouse/opid232/20100525/1")
        EDAssert.equal("/data/pyarch/2010/id23eh2/opid232/20100525/1/2",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id23eh2/inhouse/opid232/20100525/1/2"),
                       "/data/id23eh2/inhouse/opid232/20100525/1/2")
        EDAssert.equal("/data/pyarch/2014/id30a1/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id30a1/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles"),
                       "/data/id30a1/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles")
        # Visitor
        EDAssert.equal(None,
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id30a3"),
                       "/data/visitor/mx415/id30a3")
        EDAssert.equal("/data/pyarch/2010/id30a3/mx415/20100212",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id30a3/20100212"),
                       "/data/visitor/mx415/id30a3/20100212")
        EDAssert.equal("/data/pyarch/2010/id30a3/mx415/20100212/1",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id30a3/20100212/1"),
                       "/data/visitor/mx415/id30a3/20100212/1")
        EDAssert.equal("/data/pyarch/2010/id30a3/mx415/20100212/1/2",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/visitor/mx415/id30a3/20100212/1/2"),
                       "/data/visitor/mx415/id30a3/20100212/1/2")
        EDAssert.equal("/data/pyarch/2010/id30a3/opid232/20100525",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id30a3/inhouse/opid232/20100525"),
                       "/data/id30a3/inhouse/opid232/20100525")
        EDAssert.equal("/data/pyarch/2010/id30a3/opid232/20100525/1",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id30a3/inhouse/opid232/20100525/1"),
                       "/data/id30a3/inhouse/opid232/20100525/1")
        EDAssert.equal("/data/pyarch/2010/id30a3/opid232/20100525/1/2",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id30a3/inhouse/opid232/20100525/1/2"),
                       "/data/id30a3/inhouse/opid232/20100525/1/2")
        EDAssert.equal("/data/pyarch/2014/id30a3/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles",
                       EDHandlerESRFPyarchv1_0.createPyarchFilePath("/data/id30a3/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles"),
                       "/data/id30a3/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles")


    def testCreatePyarchReprocessDirectoryPath(self):
        beamline = "id30a2"
        pipelineName = "EDNA_proc"
        dataCollectionId = 123456
        pyarch_path = EDHandlerESRFPyarchv1_0.createPyarchReprocessDirectoryPath(beamline, pipelineName, dataCollectionId)
        EDAssert.equal(True, os.path.exists(pyarch_path))
        year = time.strftime("%Y", time.localtime(time.time()))
        EDAssert.equal(True, pyarch_path.startswith("/data/pyarch/{0}/id30a2/reprocess/EDNA_proc/123456".format(year)))
        shutil.rmtree(pyarch_path)



    def testCreatePyarchHtmlDirectoryPath(self):
        strTestDataDir = self.getPluginTestsDataHome()
        strTestFile = os.path.join(strTestDataDir, "EDHandlerESRFPyarchv1_0", "XSDataCollection_reference.xml")
        strXml = self.readAndParseFile(strTestFile)
        xsDataCollection = XSDataCollection.parseString(strXml)
        strPyarchHtmlDirectoryPath = EDHandlerESRFPyarchv1_0.createPyarchHtmlDirectoryPath(xsDataCollection)
        # print strPyarchHtmlDirectoryPath
        strReferencePath = "/data/pyarch/2016/id30b/opid30b/20161214/RAW_DATA/Magda/Test_x1_2_dnafiles"
        EDAssert.equal(strReferencePath, strPyarchHtmlDirectoryPath, "Correct pyarch path")



    def testCopyHTMLFilesAndDir(self):
        if not os.path.exists(EDUtilsPath.getEdnaUserTempFolder()):
            os.mkdir(EDUtilsPath.getEdnaUserTempFolder())
        strTestFromDir = os.path.join(EDUtilsPath.getEdnaUserTempFolder(), "TestFromDir")
        shutil.rmtree(strTestFromDir, ignore_errors=True)
        os.mkdir(strTestFromDir)
        strTestHtmlFilePath = os.path.join(strTestFromDir, "index.html")
        strTestHtmlDirPath = os.path.join(strTestFromDir, "index")
        EDUtilsFile.writeFile(strTestHtmlFilePath, "Test content")
        if not os.path.exists(strTestHtmlDirPath):
            os.mkdir(strTestHtmlDirPath)
        strTestHtmlDirFilePath = os.path.join(strTestHtmlDirPath, "test.txt")
        EDUtilsFile.writeFile(strTestHtmlDirFilePath, "Test content")
        #
        strTestToDir = os.path.join(EDUtilsPath.getEdnaUserTempFolder(), "TestToDir")
        shutil.rmtree(strTestToDir, ignore_errors=True)
        os.mkdir(strTestToDir)
        EDHandlerESRFPyarchv1_0.copyHTMLDir(strTestFromDir, strTestToDir)
        #
        # Check that files exist in strTestToDir:
        EDAssert.isFile(os.path.join(strTestToDir, "index", "index.html"))
        EDAssert.isFile(os.path.join(strTestToDir, "index", "index", "test.txt"))
        #
        shutil.rmtree(strTestFromDir, ignore_errors=True)
        shutil.rmtree(strTestToDir, ignore_errors=True)



    def process(self):
        self.addTestMethod(self.testCreatePyarchFilePath)
        self.addTestMethod(self.testCreatePyarchReprocessDirectoryPath)
        self.addTestMethod(self.testCreatePyarchHtmlDirectoryPath)
        self.addTestMethod(self.testCopyHTMLFilesAndDir)




if __name__ == '__main__':

    EDTestCaseEDHandlerESRFPyarchv1_0 = EDTestCaseEDHandlerESRFPyarchv1_0("EDTestCaseEDHandlerESRFPyarchv1_0")
    EDTestCaseEDHandlerESRFPyarchv1_0.execute()
