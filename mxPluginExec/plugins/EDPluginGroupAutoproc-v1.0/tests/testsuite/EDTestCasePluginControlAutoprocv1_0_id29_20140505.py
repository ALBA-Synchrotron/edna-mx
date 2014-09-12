# coding: utf8
#
#    Project: <projectName>
#             http://www.edna-site.org
#
#    File: "$Id$"
#
#    Copyright (C) <copyright>
#
#    Principal author:       <author>
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

__author__="<author>"
__license__ = "GPLv3+"
__copyright__ = "<copyright>"

import os, shutil

from EDVerbose                           import EDVerbose
from EDAssert                            import EDAssert
from EDTestCasePluginExecute             import EDTestCasePluginExecute


class EDTestCasePluginControlAutoprocv1_0_id29_20140505(EDTestCasePluginExecute):
    """
    Those are all execution tests for the EDNA Exec plugin SolveContent
    """

    def __init__(self, _strTestName = None):
        """
        """
        EDTestCasePluginExecute.__init__(self, "EDPluginControlAutoprocv1_0")
#        self.setConfigurationFile(os.path.join(self.getPluginTestsDataHome(),
#                                               "XSConfiguration_SolveContent.xml"))
        self.strTestDir = os.path.join(self.getPluginTestsDataHome(), "id29_20140505")
        self.setDataInputFile(os.path.join(self.strTestDir,
                                           "edna-autoproc-input.xml"))
#        self.setReferenceDataOutputFile(os.path.join(self.getPluginTestsDataHome(), \
#                                                     "XSDataAutoproc_reference.xml"))


    def preProcess(self, _edPlugin=None):
        EDTestCasePluginExecute.preProcess(self)
        # Remove files from previous runs
        if os.path.exists(os.path.join(self.strTestDir, "results")):
            shutil.rmtree(os.path.join(self.strTestDir, "results"))
        if os.path.exists(os.path.join(self.strTestDir, "stats.json")):
            os.remove(os.path.join(self.strTestDir, "stats.json"))

    def testExecute(self):
        self.run()
        # Remove files from this run
        if os.path.exists(os.path.join(self.strTestDir, "results")):
            shutil.rmtree(os.path.join(self.strTestDir, "results"))
        if os.path.exists(os.path.join(self.strTestDir, "stats.json")):
            os.remove(os.path.join(self.strTestDir, "stats.json"))

    def process(self):
        self.addTestMethod(self.testExecute)
