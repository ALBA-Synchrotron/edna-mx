#!/usr/bin/env python

#
# Generated Thu Jul 4 03:38::47 2019 by EDGenerateDS.
#

import os, sys
from xml.dom import minidom
from xml.dom import Node


strEdnaHome = os.environ.get("EDNA_HOME", None)

dictLocation = { \
 "XSDataCommon": "kernel/datamodel", \
 "XSDataCommon": "kernel/datamodel", \
 "XSDataCommon": "kernel/datamodel", \
 "XSDataCommon": "kernel/datamodel", \
 "XSDataCommon": "kernel/datamodel", \
 "XSDataCommon": "kernel/datamodel", \
}

try:
    from XSDataCommon import XSDataBoolean
    from XSDataCommon import XSDataFile
    from XSDataCommon import XSDataInput
    from XSDataCommon import XSDataInteger
    from XSDataCommon import XSDataResult
    from XSDataCommon import XSDataDouble
    from XSDataCommon import XSDataString
except ImportError as error:
    if strEdnaHome is not None:
        for strXsdName in dictLocation:
            strXsdModule = strXsdName + ".py"
            strRootdir = os.path.dirname(os.path.abspath(os.path.join(strEdnaHome, dictLocation[strXsdName])))
            for strRoot, listDirs, listFiles in os.walk(strRootdir):
                if strXsdModule in listFiles:
                    sys.path.append(strRoot)
    else:
        raise error
from XSDataCommon import XSDataBoolean
from XSDataCommon import XSDataFile
from XSDataCommon import XSDataInput
from XSDataCommon import XSDataInteger
from XSDataCommon import XSDataResult
from XSDataCommon import XSDataDouble
from XSDataCommon import XSDataString




#
# Support/utility functions.
#

# Compabiltity between Python 2 and 3:
if sys.version.startswith('3'):
    unicode = str
    from io import StringIO
else:
    from StringIO import StringIO


def showIndent(outfile, level):
    for idx in range(level):
        outfile.write(unicode('    '))


def warnEmptyAttribute(_strName, _strTypeName):
    pass
    #if not _strTypeName in ["float", "double", "string", "boolean", "integer"]:
    #    print("Warning! Non-optional attribute %s of type %s is None!" % (_strName, _strTypeName))

class MixedContainer(object):
    # Constants for category:
    CategoryNone = 0
    CategoryText = 1
    CategorySimple = 2
    CategoryComplex = 3
    # Constants for content_type:
    TypeNone = 0
    TypeText = 1
    TypeString = 2
    TypeInteger = 3
    TypeFloat = 4
    TypeDecimal = 5
    TypeDouble = 6
    TypeBoolean = 7
    def __init__(self, category, content_type, name, value):
        self.category = category
        self.content_type = content_type
        self.name = name
        self.value = value
    def getCategory(self):
        return self.category
    def getContenttype(self, content_type):
        return self.content_type
    def getValue(self):
        return self.value
    def getName(self):
        return self.name
    def export(self, outfile, level, name):
        if self.category == MixedContainer.CategoryText:
            outfile.write(self.value)
        elif self.category == MixedContainer.CategorySimple:
            self.exportSimple(outfile, level, name)
        else:     # category == MixedContainer.CategoryComplex
            self.value.export(outfile, level, name)
    def exportSimple(self, outfile, level, name):
        if self.content_type == MixedContainer.TypeString:
            outfile.write(unicode('<%s>%s</%s>' % (self.name, self.value, self.name)))
        elif self.content_type == MixedContainer.TypeInteger or \
                self.content_type == MixedContainer.TypeBoolean:
            outfile.write(unicode('<%s>%d</%s>' % (self.name, self.value, self.name)))
        elif self.content_type == MixedContainer.TypeFloat or \
                self.content_type == MixedContainer.TypeDecimal:
            outfile.write(unicode('<%s>%f</%s>' % (self.name, self.value, self.name)))
        elif self.content_type == MixedContainer.TypeDouble:
            outfile.write(unicode('<%s>%g</%s>' % (self.name, self.value, self.name)))

#
# Data representation classes.
#



class XSDataInputControlXia2DIALS(XSDataInput):
    def __init__(self, configuration=None, reprocess=None, endFrame=None, startFrame=None, unitCell=None, spaceGroup=None, smallMolecule3dii=None, doAnomAndNonanom=None, doAnom=None, processDirectory=None, dataCollectionId=None, cc_half=None, misigma=None, isigma=None, d_min=None, cc_ref=None):
        XSDataInput.__init__(self, configuration)
        if dataCollectionId is None:
            self._dataCollectionId = None
        elif dataCollectionId.__class__.__name__ == "XSDataInteger":
            self._dataCollectionId = dataCollectionId
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'dataCollectionId' is not XSDataInteger but %s" % self._dataCollectionId.__class__.__name__
            raise BaseException(strMessage)
        if processDirectory is None:
            self._processDirectory = None
        elif processDirectory.__class__.__name__ == "XSDataFile":
            self._processDirectory = processDirectory
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'processDirectory' is not XSDataFile but %s" % self._processDirectory.__class__.__name__
            raise BaseException(strMessage)
        if doAnom is None:
            self._doAnom = None
        elif doAnom.__class__.__name__ == "XSDataBoolean":
            self._doAnom = doAnom
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'doAnom' is not XSDataBoolean but %s" % self._doAnom.__class__.__name__
            raise BaseException(strMessage)
        if doAnomAndNonanom is None:
            self._doAnomAndNonanom = None
        elif doAnomAndNonanom.__class__.__name__ == "XSDataBoolean":
            self._doAnomAndNonanom = doAnomAndNonanom
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'doAnomAndNonanom' is not XSDataBoolean but %s" % self._doAnomAndNonanom.__class__.__name__
            raise BaseException(strMessage)
        if smallMolecule3dii is None:
            self._smallMolecule3dii = None
        elif smallMolecule3dii.__class__.__name__ == "XSDataBoolean":
            self._smallMolecule3dii = smallMolecule3dii
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'smallMolecule3dii' is not XSDataBoolean but %s" % self._smallMolecule3dii.__class__.__name__
            raise BaseException(strMessage)
        if spaceGroup is None:
            self._spaceGroup = None
        elif spaceGroup.__class__.__name__ == "XSDataString":
            self._spaceGroup = spaceGroup
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'spaceGroup' is not XSDataString but %s" % self._spaceGroup.__class__.__name__
            raise BaseException(strMessage)
        if unitCell is None:
            self._unitCell = None
        elif unitCell.__class__.__name__ == "XSDataString":
            self._unitCell = unitCell
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'unitCell' is not XSDataString but %s" % self._unitCell.__class__.__name__
            raise BaseException(strMessage)
        if startFrame is None:
            self._startFrame = None
        elif startFrame.__class__.__name__ == "XSDataInteger":
            self._startFrame = startFrame
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'startFrame' is not XSDataInteger but %s" % self._startFrame.__class__.__name__
            raise BaseException(strMessage)
        if endFrame is None:
            self._endFrame = None
        elif endFrame.__class__.__name__ == "XSDataInteger":
            self._endFrame = endFrame
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'endFrame' is not XSDataInteger but %s" % self._endFrame.__class__.__name__
            raise BaseException(strMessage)
        
        if cc_ref is None:
            self._cc_ref = None
        elif cc_ref.__class__.__name__ == "XSDataDouble":
            self._cc_ref = cc_ref
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'cc_ref' is not XSDataDouble but %s" % self._cc_ref.__class__.__name__
            raise BaseException(strMessage)

        if cc_half is None:
            self._cc_half = None
        elif cc_half.__class__.__name__ == "XSDataDouble":
            self._cc_half = cc_half
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'cc_half' is not XSDataDouble but %s" % self._cc_half.__class__.__name__
            raise BaseException(strMessage)
        
        if misigma is None:
            self._misigma = None
        elif misigma.__class__.__name__ == "XSDataDouble":
            self._misigma = misigma
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'misigma' is not XSDataDouble but %s" % self._misigma.__class__.__name__
            raise BaseException(strMessage)
        
        if isigma is None:
            self._isigma = None
        elif isigma.__class__.__name__ == "XSDataDouble":
            self._isigma = isigma
        else:
            strMessage = "ERROR! XSDataInputXiXSDataInputControlXia2DIALSa2DIALS constructor argument 'isigma' is not XSDataDouble but %s" % self._isigma.__class__.__name__
            raise BaseException(strMessage)
        
        if d_min is None:
            self._d_min = None
        elif isigma.__class__.__name__ == "XSDataDouble":
            self._d_min = d_min
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'd_min' is not XSDataDouble but %s" % self._d_min.__class__.__name__
            raise BaseException(strMessage)

        if reprocess is None:
            self._reprocess = None
        elif reprocess.__class__.__name__ == "XSDataBoolean":
            self._reprocess = reprocess
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS constructor argument 'reprocess' is not XSDataBoolean but %s" % self._reprocess.__class__.__name__
            raise BaseException(strMessage)
    # Methods and properties for the 'dataCollectionId' attribute
    def getDataCollectionId(self): return self._dataCollectionId
    def setDataCollectionId(self, dataCollectionId):
        if dataCollectionId is None:
            self._dataCollectionId = None
        elif dataCollectionId.__class__.__name__ == "XSDataInteger":
            self._dataCollectionId = dataCollectionId
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setDataCollectionId argument is not XSDataInteger but %s" % dataCollectionId.__class__.__name__
            raise BaseException(strMessage)
    def delDataCollectionId(self): self._dataCollectionId = None
    dataCollectionId = property(getDataCollectionId, setDataCollectionId, delDataCollectionId, "Property for dataCollectionId")
    # Methods and properties for the 'processDirectory' attribute
    def getProcessDirectory(self): return self._processDirectory
    def setProcessDirectory(self, processDirectory):
        if processDirectory is None:
            self._processDirectory = None
        elif processDirectory.__class__.__name__ == "XSDataFile":
            self._processDirectory = processDirectory
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setProcessDirectory argument is not XSDataFile but %s" % processDirectory.__class__.__name__
            raise BaseException(strMessage)
    def delProcessDirectory(self): self._processDirectory = None
    processDirectory = property(getProcessDirectory, setProcessDirectory, delProcessDirectory, "Property for processDirectory")
    # Methods and properties for the 'doAnom' attribute
    def getDoAnom(self): return self._doAnom
    def setDoAnom(self, doAnom):
        if doAnom is None:
            self._doAnom = None
        elif doAnom.__class__.__name__ == "XSDataBoolean":
            self._doAnom = doAnom
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setDoAnom argument is not XSDataBoolean but %s" % doAnom.__class__.__name__
            raise BaseException(strMessage)
    def delDoAnom(self): self._doAnom = None
    doAnom = property(getDoAnom, setDoAnom, delDoAnom, "Property for doAnom")
    # Methods and properties for the 'doAnomAndNonanom' attribute
    def getDoAnomAndNonanom(self): return self._doAnomAndNonanom
    def setDoAnomAndNonanom(self, doAnomAndNonanom):
        if doAnomAndNonanom is None:
            self._doAnomAndNonanom = None
        elif doAnomAndNonanom.__class__.__name__ == "XSDataBoolean":
            self._doAnomAndNonanom = doAnomAndNonanom
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setDoAnomAndNonanom argument is not XSDataBoolean but %s" % doAnomAndNonanom.__class__.__name__
            raise BaseException(strMessage)
    def delDoAnomAndNonanom(self): self._doAnomAndNonanom = None
    doAnomAndNonanom = property(getDoAnomAndNonanom, setDoAnomAndNonanom, delDoAnomAndNonanom, "Property for doAnomAndNonanom")
    # Methods and properties for the 'smallMolecule3dii' attribute
    def getSmallMolecule3dii(self): return self._smallMolecule3dii
    def setSmallMolecule3dii(self, smallMolecule3dii):
        if smallMolecule3dii is None:
            self._smallMolecule3dii = None
        elif smallMolecule3dii.__class__.__name__ == "XSDataBoolean":
            self._smallMolecule3dii = smallMolecule3dii
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setSmallMolecule3dii argument is not XSDataBoolean but %s" % smallMolecule3dii.__class__.__name__
            raise BaseException(strMessage)
    def delSmallMolecule3dii(self): self._doSmallMolecule3dii = None
    smallMolecule3dii = property(getSmallMolecule3dii, setSmallMolecule3dii, delSmallMolecule3dii, "Property for smallMolecule3dii")
    # Methods and properties for the 'spaceGroup' attribute
    def getSpaceGroup(self): return self._spaceGroup
    def setSpaceGroup(self, spaceGroup):
        if spaceGroup is None:
            self._spaceGroup = None
        elif spaceGroup.__class__.__name__ == "XSDataString":
            self._spaceGroup = spaceGroup
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setSpaceGroup argument is not XSDataString but %s" % spaceGroup.__class__.__name__
            raise BaseException(strMessage)
    def delSpaceGroup(self): self._spaceGroup = None
    spaceGroup = property(getSpaceGroup, setSpaceGroup, delSpaceGroup, "Property for spaceGroup")
    # Methods and properties for the 'unitCell' attribute
    def getUnitCell(self): return self._unitCell
    def setUnitCell(self, unitCell):
        if unitCell is None:
            self._unitCell = None
        elif unitCell.__class__.__name__ == "XSDataString":
            self._unitCell = unitCell
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setUnitCell argument is not XSDataString but %s" % unitCell.__class__.__name__
            raise BaseException(strMessage)
    def delUnitCell(self): self._unitCell = None
    unitCell = property(getUnitCell, setUnitCell, delUnitCell, "Property for unitCell")
    # Methods and properties for the 'startFrame' attribute
    def getStartFrame(self): return self._startFrame
    def setStartFrame(self, startFrame):
        if startFrame is None:
            self._startFrame = None
        elif startFrame.__class__.__name__ == "XSDataInteger":
            self._startFrame = startFrame
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setStartFrame argument is not XSDataInteger but %s" % startFrame.__class__.__name__
            raise BaseException(strMessage)
    def delStartFrame(self): self._startFrame = None
    startFrame = property(getStartFrame, setStartFrame, delStartFrame, "Property for startFrame")
    # Methods and properties for the 'endFrame' attribute
    def getEndFrame(self): return self._endFrame
    def setEndFrame(self, endFrame):
        if endFrame is None:
            self._endFrame = None
        elif endFrame.__class__.__name__ == "XSDataInteger":
            self._endFrame = endFrame
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setEndFrame argument is not XSDataInteger but %s" % endFrame.__class__.__name__
            raise BaseException(strMessage)
    def delEndFrame(self): self._endFrame = None
    endFrame = property(getEndFrame, setEndFrame, delEndFrame, "Property for endFrame")

    # Methods and properties for the 'cc_ref' attribute
    def getCcRef(self): return self._cc_ref
    def setCcRef(self, cc_ref):
        if cc_ref is None:
            self._cc_ref = None
        elif cc_ref.__class__.__name__ == "XSDataDouble":
            self._cc_ref = cc_ref
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setCcRef argument is not XSDataDouble but %s" % cc_ref.__class__.__name__
            raise BaseException(strMessage)
    def delCcRef(self): self._cc_ref = None
    cc_ref = property(getCcRef, setCcRef, delCcRef, "Property for cc_ref")
    
    # Methods and properties for the 'cc_half' attribute
    def getCcHalf(self): return self._cc_half
    def setCcHalf(self, cc_half):
        if cc_half is None:
            self._cc_half = None
        elif cc_half.__class__.__name__ == "XSDataDouble":
            self._cc_half = cc_half
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setCcHalf argument is not XSDataDouble but %s" % cc_half.__class__.__name__
            raise BaseException(strMessage)
    def delCcHalf(self): self._cc_half = None
    cc_half = property(getCcHalf, setCcHalf, delCcHalf, "Property for cc_half")

    # Methods and properties for the 'misigma' attribute
    def getMisigma(self): return self._misigma
    def setMisigma(self, misigma):
        if misigma is None:
            self._misigma = None
        elif misigma.__class__.__name__ == "XSDataDouble":
            self._misigma = misigma
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setMisigma argument is not XSDataDouble but %s" % misigma.__class__.__name__
            raise BaseException(strMessage)
    def delMisigma(self): self._misigma = None
    misigma = property(getMisigma, setMisigma, delMisigma, "Property for misigma")

    # Methods and properties for the 'isigma' attribute
    def getIsigma(self): return self._isigma
    def setIsigma(self, isigma):
        if isigma is None:
            self._isigma = None
        elif isigma.__class__.__name__ == "XSDataDouble":
            self._isigma = isigma
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setIsigma argument is not XSDataDouble but %s" % isigma.__class__.__name__
            raise BaseException(strMessage)
    def delIsigma(self): self._isigma = None
    isigma = property(getIsigma, setIsigma, delIsigma, "Property for isigma")

    # Methods and properties for the 'd_min' attribute
    def getDmin(self): return self._d_min
    def setDmin(self, d_min):
        if d_min is None:
            self._d_min = None
        elif d_min.__class__.__name__ == "XSDataDouble":
            self._d_min = d_min
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setDmin argument is not XSDataDouble but %s" % d_min.__class__.__name__
            raise BaseException(strMessage)
    def delDmin(self): self._d_min = None
    d_min = property(getDmin, setDmin, delDmin, "Property for d_min")



    # Methods and properties for the 'reprocess' attribute
    def getReprocess(self): return self._reprocess
    def setReprocess(self, reprocess):
        if reprocess is None:
            self._reprocess = None
        elif reprocess.__class__.__name__ == "XSDataBoolean":
            self._reprocess = reprocess
        else:
            strMessage = "ERROR! XSDataInputControlXia2DIALS.setReprocess argument is not XSDataBoolean but %s" % reprocess.__class__.__name__
            raise BaseException(strMessage)
    def delReprocess(self): self._reprocess = None
    reprocess = property(getReprocess, setReprocess, delReprocess, "Property for reprocess")
    def export(self, outfile, level, name_='XSDataInputControlXia2DIALS'):
        showIndent(outfile, level)
        outfile.write(unicode('<%s>\n' % name_))
        self.exportChildren(outfile, level + 1, name_)
        showIndent(outfile, level)
        outfile.write(unicode('</%s>\n' % name_))
    def exportChildren(self, outfile, level, name_='XSDataInputControlXia2DIALS'):
        XSDataInput.exportChildren(self, outfile, level, name_)
        if self._dataCollectionId is not None:
            self.dataCollectionId.export(outfile, level, name_='dataCollectionId')
        if self._processDirectory is not None:
            self.processDirectory.export(outfile, level, name_='processDirectory')
        if self._doAnom is not None:
            self.doAnom.export(outfile, level, name_='doAnom')
        if self._doAnomAndNonanom is not None:
            self.doAnomAndNonanom.export(outfile, level, name_='doAnomAndNonanom')
        if self._smallMolecule3dii is not None:
            self.smallMolecule3dii.export(outfile, level, name_='smallMolecule3dii')
        if self._spaceGroup is not None:
            self.spaceGroup.export(outfile, level, name_='spaceGroup')
        if self._unitCell is not None:
            self.unitCell.export(outfile, level, name_='unitCell')
        if self._startFrame is not None:
            self.startFrame.export(outfile, level, name_='startFrame')
        if self._endFrame is not None:
            self.endFrame.export(outfile, level, name_='endFrame')
        if self._cc_ref is not None:
            self.cc_ref.export(outfile, level, name_='cc_ref')
        if self._cc_half is not None:
            self.cc_half.export(outfile, level, name_='cc_half')
        if self._misigma is not None:
            self.misigma.export(outfile, level, name_='misigma')
        if self._isigma is not None:
            self.isigma.export(outfile, level, name_='isigma')
        if self._d_min is not None:
            self.d_min.export(outfile, level, name_='d_min')
        if self._reprocess is not None:
            self.reprocess.export(outfile, level, name_='reprocess')
    def build(self, node_):
        for child_ in node_.childNodes:
            nodeName_ = child_.nodeName.split(':')[-1]
            self.buildChildren(child_, nodeName_)
    def buildChildren(self, child_, nodeName_):
        if child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'dataCollectionId':
            obj_ = XSDataInteger()
            obj_.build(child_)
            self.setDataCollectionId(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'processDirectory':
            obj_ = XSDataFile()
            obj_.build(child_)
            self.setProcessDirectory(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'doAnom':
            obj_ = XSDataBoolean()
            obj_.build(child_)
            self.setDoAnom(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'doAnomAndNonanom':
            obj_ = XSDataBoolean()
            obj_.build(child_)
            self.setDoAnomAndNonanom(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'smallMolecule3dii':
            obj_ = XSDataBoolean()
            obj_.build(child_)
            self.setSmallMolecule3dii(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'spaceGroup':
            obj_ = XSDataString()
            obj_.build(child_)
            self.setSpaceGroup(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'unitCell':
            obj_ = XSDataString()
            obj_.build(child_)
            self.setUnitCell(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'startFrame':
            obj_ = XSDataInteger()
            obj_.build(child_)
            self.setStartFrame(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'endFrame':
            obj_ = XSDataInteger()
            obj_.build(child_)
            self.setEndFrame(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'cc_ref':
            obj_ = XSDataDouble()
            obj_.build(child_)
            self.setCcRef(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'cc_half':
            obj_ = XSDataDouble()
            obj_.build(child_)
            self.setCcHalf(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'misigma':
            obj_ = XSDataDouble()
            obj_.build(child_)
            self.setMisigma(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'isigma':
            obj_ = XSDataDouble()
            obj_.build(child_)
            self.setIsigma(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'd_min':
            obj_ = XSDataDouble()
            obj_.build(child_)
            self.setDmin(obj_)
        elif child_.nodeType == Node.ELEMENT_NODE and \
            nodeName_ == 'reprocess':
            obj_ = XSDataBoolean()
            obj_.build(child_)
            self.setReprocess(obj_)
        XSDataInput.buildChildren(self, child_, nodeName_)
    #Method for marshalling an object
    def marshal( self ):
        oStreamString = StringIO()
        oStreamString.write(unicode('<?xml version="1.0" ?>\n'))
        self.export( oStreamString, 0, name_="XSDataInputControlXia2DIALS" )
        oStringXML = oStreamString.getvalue()
        oStreamString.close()
        return oStringXML
    #Only to export the entire XML tree to a file stream on disk
    def exportToFile( self, _outfileName ):
        outfile = open( _outfileName, "w" )
        outfile.write(unicode('<?xml version=\"1.0\" ?>\n'))
        self.export( outfile, 0, name_='XSDataInputControlXia2DIALS' )
        outfile.close()
    #Deprecated method, replaced by exportToFile
    def outputFile( self, _outfileName ):
        print("WARNING: Method outputFile in class XSDataInputControlXia2DIALS is deprecated, please use instead exportToFile!")
        self.exportToFile(_outfileName)
    #Method for making a copy in a new instance
    def copy( self ):
        return XSDataInputControlXia2DIALS.parseString(self.marshal())
    #Static method for parsing a string
    def parseString( _inString ):
        doc = minidom.parseString(_inString)
        rootNode = doc.documentElement
        rootObj = XSDataInputControlXia2DIALS()
        rootObj.build(rootNode)
        # Check that all minOccurs are obeyed by marshalling the created object
        oStreamString = StringIO()
        rootObj.export( oStreamString, 0, name_="XSDataInputControlXia2DIALS" )
        oStreamString.close()
        return rootObj
    parseString = staticmethod( parseString )
    #Static method for parsing a file
    def parseFile( _inFilePath ):
        doc = minidom.parse(_inFilePath)
        rootNode = doc.documentElement
        rootObj = XSDataInputControlXia2DIALS()
        rootObj.build(rootNode)
        return rootObj
    parseFile = staticmethod( parseFile )
# end class XSDataInputControlXia2DIALS


class XSDataResultControlXia2DIALS(XSDataResult):
    def __init__(self, status=None):
        XSDataResult.__init__(self, status)
    def export(self, outfile, level, name_='XSDataResultControlXia2DIALS'):
        showIndent(outfile, level)
        outfile.write(unicode('<%s>\n' % name_))
        self.exportChildren(outfile, level + 1, name_)
        showIndent(outfile, level)
        outfile.write(unicode('</%s>\n' % name_))
    def exportChildren(self, outfile, level, name_='XSDataResultControlXia2DIALS'):
        XSDataResult.exportChildren(self, outfile, level, name_)
    def build(self, node_):
        for child_ in node_.childNodes:
            nodeName_ = child_.nodeName.split(':')[-1]
            self.buildChildren(child_, nodeName_)
    def buildChildren(self, child_, nodeName_):
        pass
        XSDataResult.buildChildren(self, child_, nodeName_)
    #Method for marshalling an object
    def marshal( self ):
        oStreamString = StringIO()
        oStreamString.write(unicode('<?xml version="1.0" ?>\n'))
        self.export( oStreamString, 0, name_="XSDataResultControlXia2DIALS" )
        oStringXML = oStreamString.getvalue()
        oStreamString.close()
        return oStringXML
    #Only to export the entire XML tree to a file stream on disk
    def exportToFile( self, _outfileName ):
        outfile = open( _outfileName, "w" )
        outfile.write(unicode('<?xml version=\"1.0\" ?>\n'))
        self.export( outfile, 0, name_='XSDataResultControlXia2DIALS' )
        outfile.close()
    #Deprecated method, replaced by exportToFile
    def outputFile( self, _outfileName ):
        print("WARNING: Method outputFile in class XSDataResultControlXia2DIALS is deprecated, please use instead exportToFile!")
        self.exportToFile(_outfileName)
    #Method for making a copy in a new instance
    def copy( self ):
        return XSDataResultControlXia2DIALS.parseString(self.marshal())
    #Static method for parsing a string
    def parseString( _inString ):
        doc = minidom.parseString(_inString)
        rootNode = doc.documentElement
        rootObj = XSDataResultControlXia2DIALS()
        rootObj.build(rootNode)
        # Check that all minOccurs are obeyed by marshalling the created object
        oStreamString = StringIO()
        rootObj.export( oStreamString, 0, name_="XSDataResultControlXia2DIALS" )
        oStreamString.close()
        return rootObj
    parseString = staticmethod( parseString )
    #Static method for parsing a file
    def parseFile( _inFilePath ):
        doc = minidom.parse(_inFilePath)
        rootNode = doc.documentElement
        rootObj = XSDataResultControlXia2DIALS()
        rootObj.build(rootNode)
        return rootObj
    parseFile = staticmethod( parseFile )
# end class XSDataResultControlXia2DIALS



# End of data representation classes.


