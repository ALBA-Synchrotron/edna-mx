#!/usr/bin/env python
#
# This file has been modified to meet certain requirements for the EDNA project.
# Please see below the original copy right message for generateDS.py.
#

"""
1. Synopsis:

Generate Python classes from XML Schema definition.
Input is read from in_xsd_file or, if "-" (dash) arg, from stdin.
Output is written to files named in "-o" and "-s" options.
    
2. Usage:

python EDGenerateDS.py [ options ] <xsd_file>
python EDGenerateDS.py [ options ] -

3. Options:

-h, --help               Display this help information.
-o <outfilename>         Output file name for data representation classes
-s <subclassfilename>    Output file name for subclasses
-p <prefix>              Prefix string to be pre-pended to the class names
-f                       Force creation of output files.  Do not ask.
-a <namespaceabbrev>     Namespace abbreviation, e.g. "xsd:". Default = 'xs:'.                         
-b <behaviorfilename>    Input file name for behaviors added to subclasses
-m                       Generate properties for member variables
--subclass-suffix="XXX"  Append XXX to the generated subclass names. Default="Sub".                         
--root-element="XXX"     Assume XXX is root element of instance docs.Default is first element defined in schema.                         
--super="XXX"            Super module name in subclass module. Default="???"
--validator-bodies=path  Path to a directory containing files that provide bodies (implementations) of validator methods.                         
--use-old-getter-setter  Name getters and setters getVar() and setVar(), instead of get_var() and set_var().                         
--user-methods= <module>,
-u <module               Optional module containing user methods.  See section "User Methods" in the documentation.
                         
"""


## LICENSE

## Copyright (c) 2003 Dave Kuhlman

## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:

## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
## IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
## CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
## TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
## SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



#from __future__ import generators   # only needed for Python 2.2

import sys
import os.path
import time
import getopt
import urllib2
from xml.sax import handler, make_parser
import xml.sax.xmlreader
import logging
import keyword

# Default logger configuration
#logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s %(levelname)s %(message)s')

##from IPython.Shell import IPShellEmbed
##args = ''
##ipshell = IPShellEmbed(args,
##    banner = 'Dropping into IPython',
##    exit_msg = 'Leaving Interpreter, back to program.')

# Then use the following line where and when you want to drop into the
# IPython shell:
#    ipshell('<some message> -- Entering ipshell.\\nHit Ctrl-D to exit')


#
# Global variables etc.
#
GenerateProperties = 0
UseOldGetterSetter = 0
DelayedElements = []
DelayedElements_subclass = []
AlreadyGenerated = []
AlreadyGenerated_subclass = []
PostponedExtensions = []
ElementsForSubclasses = []
ElementDict = {}
SaxElementDict = {}
Force = 0

##NameTable = {
##    'class': 'klass',
##    'import': 'emport',
##    'type': 'ttype',
##    'pass': 'ppass',
##    }

NameTable = {
    'type': 'typexx',
    }
for kw in keyword.kwlist:
    NameTable[kw] = '%sxx' % kw


SubclassSuffix = 'Sub'
RootElement = None
AttributeGroups = {}
SubstitutionGroups = {}
#
# SubstitutionGroups can also include simple types that are
#   not (defined) elements.  Keep a list of these simple types.
#   These are simple types defined at top level.
SimpleElementDict = {}
SimpleTypeDict = {}
ValidatorBodiesBasePath = None
UserMethodsPath = None
UserMethodsModule = None
XsdNameSpace = ''

def set_type_constants(nameSpace):
    global StringType, TokenType, \
        IntegerType, DecimalType, \
        ShortType, LongType, \
        PositiveIntegerType, NegativeIntegerType, \
        NonPositiveIntegerType, NonNegativeIntegerType, \
        BooleanType, FloatType, DoubleType, \
        ElementType, ComplexTypeType, SequenceType, ChoiceType, \
        AttributeGroupType, AttributeType, SchemaType, \
        DateTimeType, DateType, \
        ComplexContentType, ExtensionType, \
        IDType, IDREFType, IDREFSType, IDTypes, \
        NameType, NCNameType, QNameType, NameTypes, \
        AnyAttributeType, SimpleTypeType, RestrictionType, \
        WhiteSpaceType, ListType, EnumerationType, UnionType, \
        OtherSimpleTypes
    AttributeGroupType = nameSpace + 'attributeGroup'
    AttributeType = nameSpace + 'attribute'
    BooleanType = nameSpace + 'boolean'
    ChoiceType = nameSpace + 'choice'
    ComplexContentType = nameSpace + 'complexContent'
    ComplexTypeType = nameSpace + 'complexType'
    SimpleTypeType = nameSpace + 'simpleType'
    RestrictionType = nameSpace + 'restriction'
    WhiteSpaceType = nameSpace + 'whiteSpace'
    AnyAttributeType = nameSpace + 'anyAttribute'
    DateTimeType = nameSpace + 'dateTime'
    DateType = nameSpace + 'date'
    IntegerType = (nameSpace + 'integer',
        nameSpace + 'unsignedShort',
        nameSpace + 'short',
        nameSpace + 'long',
        nameSpace + 'int',
        nameSpace + 'short',
        )
    #ShortType = nameSpace + 'short'
    #LongType = nameSpace + 'long'
    DecimalType = nameSpace + 'decimal'
    PositiveIntegerType = nameSpace + 'positiveInteger'
    NegativeIntegerType = nameSpace + 'negativeInteger'
    NonPositiveIntegerType = nameSpace + 'nonPositiveInteger'
    NonNegativeIntegerType = nameSpace + 'nonNegativeInteger'
    DoubleType = nameSpace + 'double'
    ElementType = nameSpace + 'element'
    ExtensionType = nameSpace + 'extension'
    FloatType = nameSpace + 'float'
    IDREFSType = nameSpace + 'IDREFS'
    IDREFType = nameSpace + 'IDREF'
    IDType = nameSpace + 'ID'
    IDTypes = (IDREFSType, IDREFType, IDType,)
    SchemaType = nameSpace + 'schema'
    SequenceType = nameSpace + 'sequence'
    StringType = (nameSpace + 'string',
        nameSpace + 'duration',
        nameSpace + 'anyURI',
        nameSpace + 'normalizedString',
        )
    TokenType = nameSpace + 'token'
    NameType = nameSpace + 'Name'
    NCNameType = nameSpace + 'NCName'
    QNameType = nameSpace + 'QName'
    NameTypes = (NameType, NCNameType, QNameType,)
    ListType = nameSpace + 'list'
    EnumerationType = nameSpace + 'enumeration'
    UnionType = nameSpace + 'union'
    OtherSimpleTypes = (
        nameSpace + 'ENTITIES',
        nameSpace + 'ENTITY',
        nameSpace + 'ID',
        nameSpace + 'IDREF',
        nameSpace + 'IDREFS',
        nameSpace + 'NCName',
        nameSpace + 'NMTOKEN',
        nameSpace + 'NMTOKENS',
        nameSpace + 'NOTATION',
        nameSpace + 'Name',
        nameSpace + 'QName',
        nameSpace + 'anyURI',
        nameSpace + 'base64Binary',
        nameSpace + 'boolean',
        nameSpace + 'byte',
        nameSpace + 'date',
        nameSpace + 'dateTime',
        nameSpace + 'decimal',
        nameSpace + 'double',
        nameSpace + 'duration',
        nameSpace + 'float',
        nameSpace + 'gDay',
        nameSpace + 'gMonth',
        nameSpace + 'gMonthDay',
        nameSpace + 'gYear',
        nameSpace + 'gYearMonth',
        nameSpace + 'hexBinary',
        nameSpace + 'int',
        nameSpace + 'integer',
        nameSpace + 'language',
        nameSpace + 'long',
        nameSpace + 'negativeInteger',
        nameSpace + 'nonNegativeInteger',
        nameSpace + 'nonPositiveInteger',
        nameSpace + 'normalizedString',
        nameSpace + 'positiveInteger',
        nameSpace + 'short',
        nameSpace + 'string',
        nameSpace + 'time',
        nameSpace + 'token',
        nameSpace + 'unsignedByte',
        nameSpace + 'unsignedInt',
        nameSpace + 'unsignedLong',
        nameSpace + 'unsignedShort',
    )



#
# For debugging.
#

# Print only if DEBUG is true.
DEBUG = 0
def dbgprint(level, msg):
    if DEBUG and level > 0:
        print(msg)

def pplist(lst):
    for count, item in enumerate(lst):
        print('%d. %s' % (count, item))



#
# Representation of element definition.
#

def showLevel(outfile, level):
    for idx in range(level):
        outfile.write('    ')


class XschemaElementBase:
    def __init__(self):
        pass


class SimpleTypeElement(XschemaElementBase):
    def __init__(self, name):
        XschemaElementBase.__init__(self)
        self.name = name
        self.base = None
        self.collapseWhiteSpace = 0
        # Attribute definitions for the current attributeGroup, if there is one.
        self.attributeGroup = None
        # Attribute definitions for the currect element.
        self.attributeDefs = {}
        self.complexType = 0
        # Enumeration values for the current element.
        self.values = list()
        # The other simple types this is a union of.
        self.unionOf = list()
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setBase(self, base): self.base = base
    def getBase(self): return self.base
    def setSimpleType(self, simpleType): self.simpleType = simpleType
    def getSimpleType(self): return self.simpleType
    def getAttributeGroups(self): return self.attributeGroups
    def setAttributeGroup(self, attributeGroup): self.attributeGroup = attributeGroup
    def getAttributeGroup(self): return self.attributeGroup
    def __str__(self):
        s1 = '<"%s" SimpleTypeElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1

    def __repr__(self):
        s1 = '<"%s" SimpleTypeElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1


class XschemaElement(XschemaElementBase):
    def __init__(self, attrs):
        XschemaElementBase.__init__(self)
        self.cleanName = ''
        self.attrs = dict(attrs)
        name_val = ''
        type_val = ''
        ref_val = ''
        if 'name' in self.attrs:
            name_val = strip_namespace(self.attrs['name'])
        if 'type' in self.attrs:
            if self.attrs['type'].startswith(XsdNameSpace):
                type_val = self.attrs['type']
            else:
                type_val = strip_namespace(self.attrs['type'])
        if 'ref' in self.attrs:
            ref_val = strip_namespace(self.attrs['ref'])
        if type_val and not name_val:
            name_val = type_val
        if ref_val and not name_val:
            name_val = ref_val
        if ref_val and not type_val:
            type_val = ref_val
        if name_val:
            self.attrs['name'] = name_val
        if type_val:
            self.attrs['type'] = type_val
        if ref_val:
            self.attrs['ref'] = ref_val
        self.name = name_val
        #import pdb; pdb.set_trace()
        self.children = []
        self.optional = False
        self.minOccurs = 1
        self.maxOccurs = 1
        self.complex = 0
        self.complexType = 0
        self.type = 'NoneType'
        self.mixed = 0
        self.base = None
        self.mixedExtensionError = 0
        self.collapseWhiteSpace = 0
        # Attribute definitions for the currect element.
        self.attributeDefs = {}
        # Attribute definitions for the current attributeGroup, if there is one.
        self.attributeGroup = None
        # List of names of attributes for this element.
        # We will add the attribute defintions in each of these groups
        #   to this element in annotate().
        self.attributeGroupNameList = []
        self.topLevel = 0
        # Does this element contain an anyAttribute?
        self.anyAttribute = 0
        self.explicit_define = 0
        self.simpleType = None
        # Enumeration values for the current element.
        self.values = list()
        # The parent choice for the current element.
        self.choice = None

    def addChild(self, element):
        self.children.append(element)
    def getChildren(self): return self.children
    def getName(self): return self.name
    def getCleanName(self): return self.cleanName
    def getUnmappedCleanName(self): return self.unmappedCleanName
    def setName(self, name): self.name = name
    def getAttrs(self): return self.attrs
    def setAttrs(self, attrs): self.attrs = attrs
    def getMinOccurs(self): return self.minOccurs
    def getMaxOccurs(self): return self.maxOccurs
    def getOptional(self): return self.optional
    def getRawType(self): return self.type
    def setExplicitDefine(self, explicit_define):
        self.explicit_define = explicit_define
    def isExplicitDefine(self): return self.explicit_define
    def getType(self):
        returnType = self.type
        if ElementDict.has_key(self.type):
            typeObj = ElementDict[self.type]
            typeObjType = typeObj.getRawType()
            if typeObjType in StringType or \
                typeObjType == TokenType or \
                typeObjType == DateTimeType or \
                typeObjType == DateType or \
                typeObjType in IntegerType or \
                typeObjType == DecimalType or \
                typeObjType == PositiveIntegerType or \
                typeObjType == NegativeIntegerType or \
                typeObjType == NonPositiveIntegerType or \
                typeObjType == NonNegativeIntegerType or \
                typeObjType == BooleanType or \
                typeObjType == FloatType or \
                typeObjType == DoubleType:
                returnType = typeObjType
        return returnType
    def isComplex(self): return self.complex
    def addAttributeDefs(self, attrs): self.attributeDefs.append(attrs)
    def getAttributeDefs(self): return self.attributeDefs
    def isMixed(self): return self.mixed
    def setMixed(self, mixed): self.mixed = mixed
    def setBase(self, base): self.base = base
    def getBase(self): return self.base
    def getMixedExtensionError(self): return self.mixedExtensionError
    def getAttributeGroups(self): return self.attributeGroups
    def addAttribute(self, name, attribute):
        self.attributeGroups[name] = attribute
    def setAttributeGroup(self, attributeGroup): self.attributeGroup = attributeGroup
    def getAttributeGroup(self): return self.attributeGroup
    def setTopLevel(self, topLevel): self.topLevel = topLevel
    def getTopLevel(self): return self.topLevel
    def setAnyAttribute(self, anyAttribute): self.anyAttribute = anyAttribute
    def getAnyAttribute(self): return self.anyAttribute
    def setSimpleType(self, simpleType): self.simpleType = simpleType
    def getSimpleType(self): return self.simpleType

    def show(self, outfile, level):
        showLevel(outfile, level)
        outfile.write('Name: %s  Type: %s\n' % (self.name, self.getType()))
        showLevel(outfile, level)
        outfile.write('  - Complex: %d  MaxOccurs: %d  MinOccurs: %d\n' % \
            (self.complex, self.maxOccurs, self.minOccurs))
        showLevel(outfile, level)
        outfile.write('  - Attrs: %s\n' % self.attrs)
        showLevel(outfile, level)
        outfile.write('  - AttributeDefs: %s\n' % self.attributeDefs)

        for attr in self.getAttributeDefs():
            key = attr['name']
            try:
                value = attr['value']
            except Exception:
                value = '<empty>'
            showLevel(outfile, level + 1)
            outfile.write('key: %s  value: %s\n' % \
                (key, value))
        for child in self.children:
            child.show(outfile, level + 1)

    def annotate(self):
        self.collect_element_dict()
        self.annotate_find_type()
        self.annotate_tree()
        self.fix_dup_names()
        self.coerce_attr_types()
        self.checkMixedBases()

    def collect_element_dict(self):
        base = self.getBase()
        if self.getTopLevel() or len(self.getChildren()) > 0 or \
            len(self.getAttributeDefs()) > 0 or base:
            ElementDict[self.name] = self
        for child in self.children:
            child.collect_element_dict()

    def element_is_complex(self):
        pass

    # If it is a mixed-content element and it is defined as
    #   an extension, then all of its bases (base, base of base, ...)
    #   must be mixed-content.  Mark it as an error, if not.
    def checkMixedBases(self):
        self.checkMixedBasesChain(self, self.mixed)
        for child in self.children:
            child.checkMixedBases()

    def checkMixedBasesChain(self, child, childMixed):
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            if childMixed != parent.isMixed():
                self.mixedExtensionError = 1
                return
            parent.checkMixedBasesChain(child, childMixed)

    def resolve_type(self):
        self.complex = 0
        # If it has any attributes, then it's complex.
        attrDefs = self.getAttributeDefs()
        if len(attrDefs) > 0:
            self.complex = 1
            # type_val = ''
        type_val = self.resolve_type_1()
        if type_val:
            if type_val in ElementDict:
                type_val1 = type_val
                # The following loop handles the case where an Element's 
                # reference element has no sub-elements and whose type is
                # another simpleType (potentially of the same name). Its
                # fundamental function is to avoid the incorrect 
                # categorization of "complex" to Elements which are not and 
                # correctly resolve the Element's type. It also handles cases 
                # where the Element's "simpleType" is so-called "top level" 
                # and is only available through the global SimpleTypeDict.
                i = 0
                while True:
                    element = ElementDict[type_val1]
                    t = element.resolve_type_1()
                    # If the type is available in the SimpleTypeDict, we
                    # know we've gone far enough in the Element hierarchy
                    # and can return the correct base type.
                    if t in SimpleTypeDict:
                        type_val1 = SimpleTypeDict[t].getBase()
                        break
                    # If the type name is the same as the previous type name
                    # then we know we've fully resolved the Element hierarchy
                    # and the Element is well and truely "complex". There is
                    # also a need to handle cases where the Element name and
                    # its type name are the same (ie. this is our first time
                    # through the loop). For example:
                    #   <xsd:element name="ReallyCool" type="ReallyCool"/>
                    #   <xsd:simpleType name="ReallyCool">
                    #     <xsd:restriction base="xsd:string">
                    #       <xsd:enumeration value="MyThing"/>
                    #     </xsd:restriction>
                    #   </xsd:simpleType>
                    if t == type_val1 and i != 0:
                        break
                    if t not in ElementDict:
                        type_val1 = t
                        break
                    type_val1 = t
                    i += 1
                if type_val1 in StringType or \
                    type_val1 == TokenType or \
                    type_val1 == DateTimeType or \
                    type_val1 == DateType or \
                    type_val1 in IntegerType or \
                    type_val1 == DecimalType or \
                    type_val1 == PositiveIntegerType or \
                    type_val1 == NonPositiveIntegerType or \
                    type_val1 == NegativeIntegerType or \
                    type_val1 == NonNegativeIntegerType or \
                    type_val1 == BooleanType or \
                    type_val1 == FloatType or \
                    type_val1 == DoubleType:
                    type_val = type_val1
                else:
                    self.complex = 1
            else:
                if type_val in StringType or \
                    type_val == TokenType or \
                    type_val == DateTimeType or \
                    type_val == DateType or \
                    type_val in IntegerType or \
                    type_val == DecimalType or \
                    type_val == PositiveIntegerType or \
                    type_val == NonPositiveIntegerType or \
                    type_val == NegativeIntegerType or \
                    type_val == NonNegativeIntegerType or \
                    type_val == BooleanType or \
                    type_val == FloatType or \
                    type_val == DoubleType:
                    pass
                else:
                    type_val = StringType[0]
        else:
            type_val = StringType[0]
        return type_val

    def resolve_type_1(self):
        type_val = ''
        if 'type' in self.attrs:
            # fix
            #type_val = strip_namespace(self.attrs['type'])
            type_val = self.attrs['type']
            if type_val in SimpleTypeDict:
                self.simpleType = type_val
        elif 'ref' in self.attrs:
            # fix
            type_val = strip_namespace(self.attrs['ref'])
            #type_val = self.attrs['ref']
        elif 'name' in self.attrs:
            # fix
            type_val = strip_namespace(self.attrs['name'])
            #type_val = self.attrs['name']
        return type_val

    def annotate_find_type(self):
        type_val = self.resolve_type()
        self.attrs['type'] = type_val
        self.type = type_val
        if not self.complex:
            SimpleElementDict[self.name] = self.name
        for child in self.children:
            child.annotate_find_type()

    def annotate_tree(self):
        # If there is a namespace, replace it with an underscore.
        if self.base:
            self.base = strip_namespace(self.base)
        self.unmappedCleanName = cleanupName(self.name)
        self.cleanName = mapName(self.unmappedCleanName)
        SaxElementDict[self.cleanName] = self
        self.replace_attributeGroup_names()

        # Resolve "maxOccurs" attribute
        if 'maxOccurs' in self.attrs.keys():
            maxOccurs = self.attrs['maxOccurs']
        elif self.choice and 'maxOccurs' in self.choice.attrs.keys():
            maxOccurs = self.choice.attrs['maxOccurs']
        else:
            maxOccurs = 1

        # Resolve "minOccurs" attribute
        if 'minOccurs' in self.attrs.keys():
            minOccurs = self.attrs['minOccurs']
        elif self.choice and 'minOccurs' in self.choice.attrs.keys():
            minOccurs = self.choice.attrs['minOccurs']
        else:
            minOccurs = 1

        # Cleanup "minOccurs" and "maxOccurs" attributes
        try:
            minOccurs = int(minOccurs)
            if minOccurs == 0:
                self.optional = True
        except ValueError:
            sys.stderr.write('*** %s  minOccurs must be integer.' % \
                self.getName())
            sys.exit(-1)
        try:
            if maxOccurs == 'unbounded':
                maxOccurs = 99999
            else:
                maxOccurs = int(maxOccurs)
        except ValueError:
            sys.stderr.write('*** %s  maxOccurs must be integer or "unbounded".' % \
                self.getName())
            sys.exit(-1)
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs

        # If it does not have a type, then make the type the same as the name.
        if self.type == 'NoneType' and self.name:
            self.type = self.name
        # Is it a mixed-content element definition?
        if 'mixed' in self.attrs.keys():
            mixed = self.attrs['mixed'].strip()
            if mixed == '1' or mixed.lower() == 'true':
                self.mixed = 1
        # If this element has a base and the base is a simple type and
        #   the simple type is collapseWhiteSpace, then mark this
        #   element as collapseWhiteSpace.
        base = self.getBase()
        if base and base in SimpleTypeDict:
            parent = SimpleTypeDict[base]
            if isinstance(parent, SimpleTypeElement) and \
                parent.collapseWhiteSpace:
                self.collapseWhiteSpace = 1
                #ipshell('Annotating collapseWhiteSpace -- Entering ipshell.\\nHit Ctrl-D to exit')
        # Do it recursively for all descendents.
        for child in self.children:
            child.annotate_tree()

    #
    # For each name in the attributeGroupNameList for this element,
    #   add the attributes defined for that name in the global
    #   attributeGroup dictionary.
    def replace_attributeGroup_names(self):
        for groupName in self.attributeGroupNameList:
            if AttributeGroups.has_key(groupName):
                attrGroup = AttributeGroups[groupName]
                for name in attrGroup.getKeys():
                    attr = attrGroup.get(name)
                    self.attributeDefs[name] = attr
            else:
                print('*** Error. attributeGroup %s not defined.' % groupName)

    def __str__(self):
        s1 = '<"%s" XschemaElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1

    def __repr__(self):
        s1 = '<"%s" XschemaElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1

    def fix_dup_names(self):
        # Patch-up names that are used for both a child element and an attribute.
        #
        attrDefs = self.getAttributeDefs()
        # Collect a list of child element names.
        #   Must do this for base (extension) elements also.
        elementNames = []
        self.collectElementNames(elementNames)
        replaced = []
        # Create the needed new attributes.
        keys = attrDefs.keys()
        for key in keys:
            attr = attrDefs[key]
            name = attr.getName()
            if name in elementNames:
                newName = name + '_attr'
                newAttr = XschemaAttribute(newName)
                attrDefs[newName] = newAttr
                replaced.append(name)
        # Remove the old (replaced) attributes.
        for name in replaced:
            del attrDefs[name]
        for child in self.children:
            child.fix_dup_names()

    def collectElementNames(self, elementNames):
        for child in self.children:
            elementNames.append(cleanupName(child.cleanName))
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            parent.collectElementNames(elementNames)

    def coerce_attr_types(self):
        replacements = []
        attrDefs = self.getAttributeDefs()
        for idx, name in enumerate(attrDefs):
            attr = attrDefs[name]
            attrType = attr.getData_type()
            if attrType == IDType or \
                attrType == IDREFType or \
                attrType == IDREFSType:
                attr.setData_type(StringType[0])
        for child in self.children:
            child.coerce_attr_types()
# end class XschemaElement


class XschemaAttributeGroup:
    def __init__(self, name='', group=None):
        self.name = name
        if group:
            self.group = group
        else:
            self.group = {}
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setGroup(self, group): self.group = group
    def getGroup(self): return self.group
    def get(self, name, default=None):
        if self.group.has_key(name):
            return self.group[name]
        else:
            return default
    def getKeys(self):
        return self.group.keys()
    def add(self, name, attr):
        self.group[name] = attr
    def delete(self, name):
        if has_key(self.group, name):
            del self.group[name]
            return 1
        else:
            return 0
# end class XschemaAttributeGroup

class XschemaAttribute:
    def __init__(self, name, data_type='xs:string', use='optional'):
        self.name = name
        self.data_type = data_type
        self.use = use
        # Enumeration values for the attribute.
        self.values = list()
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setData_type(self, data_type): self.data_type = data_type
    def getData_type(self): return self.data_type
    def setUse(self, use): self.use = use
    def getUse(self): return self.use
# end class XschemaAttribute


#
# SAX handler
#
class XschemaHandler(handler.ContentHandler):
    def __init__(self):
        handler.ContentHandler.__init__(self)
        self.stack = []
        self.root = None
        self.inElement = 0
        self.inComplexType = 0
        self.inNonanonymousComplexType = 0
        self.inSequence = 0
        self.inChoice = 1
        self.inAttribute = 0
        self.inAttributeGroup = 0
        self.inSimpleType = 0
        # The last attribute we processed.
        self.lastAttribute = None
        # Simple types that exist in the global context and may be used to
        # qualify the type of many elements and/or attributes.
        self.topLevelSimpleTypes = list()
        # The current choice type we're in
        self.currentChoice = None
##        self.dbgcount = 1
##        self.dbgnames = []

    def getRoot(self):
        return self.root

    def showError(self, msg):
        print(msg)
        sys.exit(-1)

    def startElement(self, name, attrs):
        logging.debug("Start element: %s %s" % (name, repr(attrs.items())))

        if name == SchemaType:
            self.inSchema = 1
            element = XschemaElement(attrs)
            if len(self.stack) == 1:
                element.setTopLevel(1)
            self.stack.append(element)
            # If there is an attribute "xmlns" and its value is
            #   "http://www.w3.org/2001/XMLSchema", then remember and
            #   use that namespace prefix.
            for name, value in attrs.items():
                if name[:6] == 'xmlns:' and \
                        value == 'http://www.w3.org/2001/XMLSchema':
                    nameSpace = name[6:] + ':'
                    set_type_constants(nameSpace)
        elif name == ElementType or ((name == ComplexTypeType) and (len(self.stack) == 1)):
            self.inElement = 1
            self.inNonanonymousComplexType = 1
            element = XschemaElement(attrs)
            if not 'type' in attrs.keys() and not 'ref' in attrs.keys():
                element.setExplicitDefine(1)
            if len(self.stack) == 1:
                element.setTopLevel(1)
            if 'substitutionGroup' in attrs.keys() and 'name' in attrs.keys():
                substituteName = attrs['name']
                headName = attrs['substitutionGroup']
                if headName not in SubstitutionGroups:
                    SubstitutionGroups[headName] = []
                SubstitutionGroups[headName].append(substituteName)
            if name == ComplexTypeType:
                element.complexType = 1
            if self.inChoice and self.currentChoice:
                element.choice = self.currentChoice
            self.stack.append(element)
        elif name == ComplexTypeType:
            # If it have any attributes and there is something on the stack,
            #   then copy the attributes to the item on top of the stack.
            if len(self.stack) > 1 and len(attrs) > 0:
                parentDict = self.stack[-1].getAttrs()
                for key in attrs.keys():
                    parentDict[key] = attrs[key]
            self.inComplexType = 1
        elif name == SequenceType:
            self.inSequence = 1
        elif name == ChoiceType:
            self.currentChoice = XschemaElement(attrs)
            self.inChoice = 1
        elif name == AttributeType:
            self.inAttribute = 1
            if 'name' in attrs.keys():
                name = attrs['name']
            elif 'ref' in attrs.keys():
                name = strip_namespace(attrs['ref'])
            else:
                name = 'no_attribute_name'
            if 'type' in attrs.keys():
                data_type = attrs['type']
            else:
                data_type = StringType[0]
            if 'use' in attrs.keys():
                use = attrs['use']
            else:
                use = 'optional'
            if self.stack[-1].attributeGroup:
                # Add this attribute to a current attributeGroup.
                attribute = XschemaAttribute(name, data_type, use)
                self.stack[-1].attributeGroup.add(name, attribute)
            else:
                # Add this attribute to the element/complexType.
                attribute = XschemaAttribute(name, data_type, use)
                self.stack[-1].attributeDefs[name] = attribute
            self.lastAttribute = attribute
        elif name == AttributeGroupType:
            self.inAttributeGroup = 1
            # If it has attribute 'name', then it's a definition.
            #   Prepare to save it as an attributeGroup.
            if 'name' in attrs.keys():
                name = strip_namespace(attrs['name'])
                attributeGroup = XschemaAttributeGroup(name)
                element = XschemaElement(attrs)
                if len(self.stack) == 1:
                    element.setTopLevel(1)
                element.setAttributeGroup(attributeGroup)
                self.stack.append(element)
            # If it has attribute 'ref', add it to the list of
            #   attributeGroups for this element/complexType.
            if 'ref' in attrs.keys():
                self.stack[-1].attributeGroupNameList.append(attrs['ref'])
        elif name == ComplexContentType:
            pass
        elif name == ExtensionType:
            if 'base' in attrs.keys() and len(self.stack) > 0:
                extensionBase = attrs['base']
                if extensionBase in StringType or \
                    extensionBase in IDTypes or \
                    extensionBase in NameTypes or \
                    extensionBase == TokenType or \
                    extensionBase == DateTimeType or \
                    extensionBase == DateType or \
                    extensionBase in IntegerType or \
                    extensionBase == DecimalType or \
                    extensionBase == PositiveIntegerType or \
                    extensionBase == NegativeIntegerType or \
                    extensionBase == NonPositiveIntegerType or \
                    extensionBase == NonNegativeIntegerType or \
                    extensionBase == BooleanType or \
                    extensionBase == FloatType or \
                    extensionBase == DoubleType or \
                    extensionBase in OtherSimpleTypes:
                    pass
                else:
                    self.stack[-1].setBase(extensionBase)
        elif name == AnyAttributeType:
            # Mark the current element as containing anyAttribute.
            self.stack[-1].setAnyAttribute(1)
        elif name == SimpleTypeType:
            # Save the name of the simpleType, but ignore everything
            #   else about it (for now).
            if 'name' in attrs.keys():
                stName = cleanupName(attrs['name'])
            else:
                stName = None
            # If the parent is an element, mark it as a simpleType.
            if len(self.stack) > 0:
                self.stack[-1].setSimpleType(1)
            element = SimpleTypeElement(stName)
            SimpleTypeDict[stName] = element
            self.stack.append(element)
            self.inSimpleType = 1
        elif name == RestrictionType:
            # If we are in a simpleType, capture the name of
            #   the restriction base.
            if self.inSimpleType and 'base' in attrs.keys():
                self.stack[-1].setBase(attrs['base'])
            self.inRestrictionType = 1
        elif name == EnumerationType:
            if self.inAttribute and attrs.has_key('value'):
                # We know that the restriction is on an attribute and the
                # attributes of the current element are un-ordered so the
                # instance variable "lastAttribute" will have our attribute.
                self.lastAttribute.values.append(attrs['value'])
            elif self.inElement and attrs.has_key('value'):
                # We're not in an attribute so the restriction must have
                # been placed on an element and that element will still be
                # in the stack. We search backwards through the stack to
                # find the last element.
                element = None
                for entry in list(stack).reverse():
                    if type(entry) == XschemaElement:
                        element = entry
                if element is None:
                    sys.stderr.write(
                        'Cannot find element to attach enumeration: %s' % \
                            value)
                    sys.exit(-1)
                element.values.append(attrs['value'])
            elif self.inSimpleType and attrs.has_key('value'):
                # We've been defined as a simpleType on our own.
                self.stack[-1].values.append(attrs['value'])
        elif name == UnionType:
            # Union types are only used with a parent simpleType and we want
            # the parent to know what it's a union of.
            if attrs.has_key('memberTypes'):
                for member in attrs['memberTypes'].split(" "):
                    self.stack[-1].unionOf.append(member)
        elif name == WhiteSpaceType and self.inRestrictionType:
            if attrs.has_key('value'):
                if attrs.getValue('value') == 'collapse':
                    self.stack[-1].collapseWhiteSpace = 1
        elif name == ListType:
            self.inListType = 1
            #ipshell('Parsing simpleType -- Entering ipshell.\nHit Ctrl-D to exit')
            #import pdb; pdb.set_trace()
        logging.debug("Start element stack: %d" % len(self.stack))

    def endElement(self, name):
        logging.debug("End element: %s" % (name))
        logging.debug("End element stack: %d" % (len(self.stack)))
        if name == SimpleTypeType and self.inSimpleType:
            self.inSimpleType = 0
            # If the simpleType is directly off the root, it may be used to 
            # qualify the type of many elements and/or attributes so we 
            # don't want to loose it entirely.
            simpleType = self.stack.pop()
            if len(self.stack) == 1:
                self.topLevelSimpleTypes.append(simpleType)
        elif name == RestrictionType and self.inRestrictionType:
            self.inRestrictionType = 0
        elif name == ElementType or (name == ComplexTypeType and self.stack[-1].complexType):
            self.inElement = 0
            self.inNonanonymousComplexType = 0
            element = self.stack.pop()
            self.stack[-1].addChild(element)
        elif name == ComplexTypeType:
            self.inComplexType = 0
        elif name == SequenceType:
            self.inSequence = 0
        elif name == ChoiceType:
            self.currentChoice = None
            self.inChoice = 0
        elif name == AttributeType:
            self.inAttribute = 0
        elif name == AttributeGroupType:
            self.inAttributeGroup = 0
            if self.stack[-1].attributeGroup:
                # The top of the stack contains an XschemaElement which
                #   contains the definition of an attributeGroup.
                #   Save this attributeGroup in the
                #   global AttributeGroup dictionary.
                attributeGroup = self.stack[-1].attributeGroup
                name = attributeGroup.getName()
                AttributeGroups[name] = attributeGroup
                self.stack[-1].attributeGroup = None
                self.stack.pop()
            else:
                # This is a reference to an attributeGroup.
                # We have already added it to the list of attributeGroup names.
                # Leave it.  We'll fill it in during annotate.
                pass
        elif name == SchemaType:
            self.inSchema = 0
            if len(self.stack) != 1:
                print('*** error stack.  len(self.stack): %d' % len(self.stack))
                sys.exit(-1)
            logging.debug("Previous root:", self.root)
            self.root = self.stack[0]
            logging.debug("New root:", self.root)
        elif name == ComplexContentType:
            pass
        elif name == ExtensionType:
            pass
        elif name == ListType:
            # List types are only used with a parent simpleType and can have a
            # simpleType child. So, if we're in a list type we have to be
            # careful to reset the inSimpleType flag otherwise the handler's
            # internal stack will not be unrolled correctly.
            self.inSimpleType = 1
            self.inListType = 0

    def characters(self, chrs):
        if self.inElement:
            pass
        elif self.inComplexType:
            pass
        elif self.inSequence:
            pass
        elif self.inChoice:
            pass


#
# Code generation
#

def generateExportFn_1(outfile, child, name, fill):
    cleanName = cleanupName(name)
    mappedName = mapName(cleanName)
    if child.getType() in StringType or \
        child.getType() == TokenType or \
        child.getType() == DateTimeType or \
        child.getType() == DateType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%s</%s>\\n' %% quote_xml(self.get%s()))\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() in IntegerType or \
        child.getType() == BooleanType or \
        child.getType() == PositiveIntegerType or \
        child.getType() == NonPositiveIntegerType or \
        child.getType() == NegativeIntegerType or \
        child.getType() == NonNegativeIntegerType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%d</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() == FloatType or \
        child.getType() == DecimalType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%f</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() == DoubleType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%e</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    else:
        s1 = "%s        if self.%s:\n" % (fill, mappedName)
        outfile.write(s1)
        if name == child.getType():
            s1 = "%s            self.%s.export(outfile, level)\n" % \
                (fill, mappedName)
        else:
            s1 = "%s            self.%s.export(outfile, level, name_='%s')\n" % \
                (fill, mappedName, name)
        outfile.write(s1)


def generateExportFn_2(outfile, child, name, fill):
    cleanName = cleanupName(name)
    mappedName = mapName(cleanName)
    s1 = "%s    for %s_ in self.get%s():\n" % (fill, cleanName, make_gs_name(cleanName))
    outfile.write(s1)
    if child.getType() in StringType or \
        child.getType() == TokenType or \
        child.getType() == DateTimeType or \
        child.getType() == DateType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%s</%s>\\n' %% quote_xml(%s_))\n" % \
            (fill, name, name, cleanName,)
        outfile.write(s1)
    elif child.getType() in IntegerType or \
        child.getType() == BooleanType or \
        child.getType() == PositiveIntegerType or \
        child.getType() == NonPositiveIntegerType or \
        child.getType() == NegativeIntegerType or \
        child.getType() == NonNegativeIntegerType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%d</%s>\\n' %% %s_)\n" % \
            (fill, name, name, cleanName,)
        outfile.write(s1)
    elif child.getType() == FloatType or \
        child.getType() == DecimalType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%f</%s>\\n' %% %s_)\n" % \
            (fill, name, name, cleanName,)
        outfile.write(s1)
    elif child.getType() == DoubleType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('<%s>%%e</%s>\\n' %% %s_)\n" % \
            (fill, name, name, cleanName)
        outfile.write(s1)
    else:
        if name == child.getType():
            s1 = "%s        %s_.export(outfile, level)\n" % (fill, mappedName)
        else:
            s1 = "%s        %s_.export(outfile, level, name_='%s')\n" % \
                (fill, mappedName, cleanName,)
        outfile.write(s1)


def generateExportFn_3(outfile, child, name, fill):
    cleanName = cleanupName(name)
    mappedName = mapName(cleanName)
    s1 = "%s        if self.get%s() != None :\n" % (
        fill, make_gs_name(cleanName))
    outfile.write(s1)
    if child.getType() in StringType or \
        child.getType() == TokenType or \
        child.getType() == DateTimeType or \
        child.getType() == DateType:
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('<%s>%%s</%s>\\n' %% quote_xml(self.get%s()))\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() in IntegerType or \
        child.getType() == BooleanType or \
        child.getType() == PositiveIntegerType or \
        child.getType() == NonPositiveIntegerType or \
        child.getType() == NegativeIntegerType or \
        child.getType() == NonNegativeIntegerType:
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('<%s>%%d</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() == FloatType or \
        child.getType() == DecimalType:
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('<%s>%%f</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    elif child.getType() == DoubleType:
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('<%s>%%e</%s>\\n' %% self.get%s())\n" % \
            (fill, name, name, make_gs_name(cleanName))
        outfile.write(s1)
    else:
        s1 = "%s            if self.%s:\n" % (fill, mappedName)
        outfile.write(s1)
        if name == child.getType():
            s1 = "%s                self.%s.export(outfile, level)\n" % \
                (fill, mappedName)
        else:
            s1 = "%s                self.%s.export(outfile, level, name_='%s')\n" % \
                (fill, mappedName, name)
        outfile.write(s1)


def generateExportAttributes(outfile, element, hasAttributes):
    if len(element.getAttributeDefs()) > 0:
        hasAttributes += 1
        attrDefs = element.getAttributeDefs()
        for key in attrDefs.keys():
            attrDef = attrDefs[key]
            name = attrDef.getName()
            cleanName = cleanupName(name)
            capName = make_gs_name(cleanName)
            if attrDef.getUse() == 'optional':
                s1 = "        if self.get%s() is not None:\n" % (capName,)
                outfile.write(s1)
                s1 = "            outfile.write(' %s=\"%%s\"' %% (self.get%s(), ))\n" % \
                    (name, capName,)
                outfile.write(s1)
            else:
                s1 = "        outfile.write(' %s=\"%%s\"' %% (self.get%s(), ))\n" % \
                    (name, capName,)
                outfile.write(s1)
    if element.getAnyAttribute():
        s1 = '        for name, value in self.anyAttributes_.items():\n'
        outfile.write(s1)
        s1 = "            outfile.write(' %s=\"%s\"' % (name, value, ))\n"
        outfile.write(s1)
    return hasAttributes


def generateExportChildren(outfile, element, hasChildren):
    if len(element.getChildren()) > 0:
        hasChildren += 1
        if element.isMixed():
            s1 = "        for item_ in self.content_:\n"
            outfile.write(s1)
            s1 = "            item_.export(outfile, level, name_)\n"
            outfile.write(s1)
        else:
            for child in element.getChildren():
                name = child.getName()
                if child.getMaxOccurs() > 1:
                    generateExportFn_2(outfile, child, name, '    ')
                else:
                    if (child.getOptional()):
                        generateExportFn_3(outfile, child, name, '')
                    else:
                        generateExportFn_1(outfile, child, name, '')
##    base = element.getBase()
##    if base and base in ElementDict:
##        parent = ElementDict[base]
##        hasAttributes = generateExportChildren(outfile, parent, hasChildren)
    return hasChildren


def countChildren(element, count):
    count += len(element.getChildren())
    base = element.getBase()
    if base and base in ElementDict:
        parent = ElementDict[base]
        count = countChildren(parent, count)
    return count


def generateExportFn(outfile, prefix, element):
    childCount = countChildren(element, 0)
    base = element.getBase()
    s1 = "    def export(self, outfile, level, name_='%s'):\n" % \
        element.getName()
    outfile.write(s1)
    s1 = '        showIndent(outfile, level)\n'
    outfile.write(s1)
    if len(element.getAttributeDefs()) > 0 or element.getAnyAttribute():
        s1 = "        outfile.write('<%s' % (name_, ))\n"
        outfile.write(s1)

        s1 = "        self.exportAttributes(outfile, level, name_='%s')\n" % \
            element.getName()
        outfile.write(s1)
        if element.isMixed() or childCount == 0:
            s1 = "        outfile.write('>')\n"
        else:
            s1 = "        outfile.write('>\\n')\n"
        outfile.write(s1)
    else:
        if element.isMixed() or childCount == 0:
            s1 = "        outfile.write('<%s>' % name_)\n"
        else:
            s1 = "        outfile.write('<%s>\\n' % name_)\n"
        outfile.write(s1)

    s1 = "        self.exportChildren(outfile, level + 1, name_)\n"
    outfile.write(s1)
    if element.isMixed() or childCount == 0:
        s1 = "        outfile.write('</%s>\\n' % name_)\n"
        outfile.write(s1)
    else:
        s1 = '        showIndent(outfile, level)\n'
        outfile.write(s1)
        s1 = "        outfile.write('</%s>\\n' % name_)\n"
        outfile.write(s1)
    s1 = "    def exportAttributes(self, outfile, level, name_='%s'):\n" % \
        element.getName()
    outfile.write(s1)
    hasAttributes = 0
    hasAttributes = generateExportAttributes(outfile, element, hasAttributes)
    if base and base not in SimpleTypeDict:
        hasAttributes += 1
        s1 = "        %s.exportAttributes(self, outfile, level, name_='%s')\n" % \
            (base, element.getName(),)
        outfile.write(s1)
    if hasAttributes == 0:
        s1 = "        pass\n"
        outfile.write(s1)
##    if len(element.getChildren()) > 0 and not element.isMixed():
##        s1 = '        showIndent(outfile, level)\n'
##        outfile.write(s1)
    s1 = "    def exportChildren(self, outfile, level, name_='%s'):\n" % \
        element.getName()
    outfile.write(s1)
    hasChildren = 0
    hasChildren = generateExportChildren(outfile, element, hasChildren)
    if base and base not in SimpleTypeDict:
        hasChildren += 1
        s1 = "        %s.exportChildren(self, outfile, level, name_)\n" % (base,)
        outfile.write(s1)
    if childCount == 0:
        s1 = "        outfile.write(self.valueOf_)\n"
        outfile.write(s1)
# end generateExportFn

# Modified by EDNA
def generateExportFnXML(outfile, prefix, element):
    s1 = "    #Only to export the entire XML tree to a file stream on disk\n"
    s2 = "    def outputFile( self, _outfileName ):\n"
    outfile.write("\n")
    outfile.write(s1)
    outfile.write(s2)
    outfile.write('        outfile = open( _outfileName, "w" )\n')
    outfile.write('        outfile.write(\"<?xml version=\\"1.0\\" ?>\\n\")\n')
    outfile.write('        self.export( outfile, 0, name_=\'%s\' )\n' % element.getName())
    outfile.write('        outfile.close()\n')
    outfile.write("\n")

def generateStaticParseString(outfile, prefix, element):
    s1 = "    #Static method for parsing a string\n"
    s2 = "    def parseString( _inString ):\n"
    outfile.write("\n")
    outfile.write(s1)
    outfile.write(s2)
    outfile.write('        doc = minidom.parseString(_inString)\n')
    outfile.write('        rootNode = doc.documentElement\n')
    outfile.write('        rootObj = %s.factory()\n' % element.getName())
    outfile.write('        rootObj.build(rootNode)\n')
    outfile.write('        return rootObj\n')
    outfile.write('    parseString = staticmethod( parseString ) \n')
    outfile.write("\n")

def generateStaticParseFile(outfile, prefix, element):
    s1 = "    #Static method for parsing a file\n"
    s2 = "    def parseFile( _inFilePath ):\n"
    outfile.write("\n")
    outfile.write(s1)
    outfile.write(s2)
    outfile.write('        doc = minidom.parse(_inFilePath)\n')
    outfile.write('        rootNode = doc.documentElement\n')
    outfile.write('        rootObj = %s.factory()\n' % element.getName())
    outfile.write('        rootObj.build(rootNode)\n')
    outfile.write('        return rootObj\n')
    outfile.write('    parseFile = staticmethod( parseFile ) \n')
    outfile.write("\n")

def generateMarshal(outfile, prefix, element):
    s1 = "    #Method for marshalling an object\n"
    s2 = "    def marshal( self ):\n"
    outfile.write("\n")
    outfile.write(s1)
    outfile.write(s2)
    outfile.write('        oStreamString = StringIO.StringIO()\n')
    outfile.write('        oStreamString.write(\'<?xml version="1.0" ?>\\n\')\n')
    outfile.write('        self.export( oStreamString, 0, name_="%s" )\n' % element.getName())
    outfile.write('        oStringXML = oStreamString.getvalue()\n')
    outfile.write('        oStreamString.close()\n')
    outfile.write('        return oStringXML\n')
    outfile.write("\n")

#
# Generate exportLiteral method.
#

def generateExportLiteralFn_1(outfile, child, name, fill):
    cleanName = cleanupName(name)
    mappedName = mapName(cleanName)
    if child.getType() in StringType or \
        child.getType() == TokenType or \
        child.getType() == DateTimeType or \
        child.getType() == DateType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%s=%%s,\\n' %% quote_python(self.get%s()))\n" % \
            (fill, mappedName, make_gs_name(name))
        outfile.write(s1)
    elif child.getType() in IntegerType or \
        child.getType() == BooleanType or \
        child.getType() == PositiveIntegerType or \
        child.getType() == NonPositiveIntegerType or \
        child.getType() == NegativeIntegerType or \
        child.getType() == NonNegativeIntegerType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%s=%%d,\\n' %% self.get%s())\n" % \
            (fill, mappedName, make_gs_name(name))
        outfile.write(s1)
    elif child.getType() == FloatType or \
        child.getType() == DecimalType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%s=%%f,\\n' %% self.get%s())\n" % \
            (fill, mappedName, make_gs_name(name))
        outfile.write(s1)
    elif child.getType() == DoubleType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%s=%%e,\\n' %% self.get%s())\n" % \
            (fill, name, make_gs_name(name))
        outfile.write(s1)
    else:
        s1 = "%s        if self.%s:\n" % (fill, mappedName)
        outfile.write(s1)
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('%s=%s(\\n')\n" % \
            (fill, mappedName, mapName(cleanupName(child.getType())))
        outfile.write(s1)
        if name == child.getType():
            s1 = "%s            self.%s.exportLiteral(outfile, level)\n" % \
                (fill, mappedName)
        else:
            s1 = "%s            self.%s.exportLiteral(outfile, level, name_='%s')\n" % \
                (fill, mappedName, name)
        outfile.write(s1)
        s1 = '%s            showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s            outfile.write('),\\n')\n" % (fill,)
        outfile.write(s1)


def generateExportLiteralFn_2(outfile, child, name, fill):
    if child.getType() in StringType or \
        child.getType() == TokenType or \
        child.getType() == DateTimeType or \
        child.getType() == DateType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%%s,\\n' %% quote_python(%s))\n" % \
            (fill, name)
        outfile.write(s1)
    elif child.getType() in IntegerType or \
        child.getType() == BooleanType or \
        child.getType() == PositiveIntegerType or \
        child.getType() == NonPositiveIntegerType or \
        child.getType() == NegativeIntegerType or \
        child.getType() == NonNegativeIntegerType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%%d,\\n' %% %s)\n" % \
            (fill, name)
        outfile.write(s1)
    elif child.getType() == FloatType or \
        child.getType() == DecimalType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%%f,\\n' %% %s)\n" % \
            (fill, name)
        outfile.write(s1)
    elif child.getType() == DoubleType:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%%e,\\n' %% %s)\n" % \
            (fill, name)
        outfile.write(s1)
    else:
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('%s(\\n')\n" % \
            (fill, cleanupName(child.getType()))
        outfile.write(s1)
        if name == child.getType():
            s1 = "%s        %s.exportLiteral(outfile, level)\n" % (fill, child.getType())
        else:
            s1 = "%s        %s.exportLiteral(outfile, level, name_='%s')\n" % \
                (fill, name, name)
        outfile.write(s1)
        s1 = '%s        showIndent(outfile, level)\n' % fill
        outfile.write(s1)
        s1 = "%s        outfile.write('),\\n')\n" % (fill,)
        outfile.write(s1)


def generateExportLiteralFn(outfile, prefix, element):
    base = element.getBase()
    s1 = "    def exportLiteral(self, outfile, level, name_='%s'):\n" % element.getName()
    outfile.write(s1)
    s1 = "        level += 1\n"
    outfile.write(s1)
    s1 = "        self.exportLiteralAttributes(outfile, level, name_)\n"
    outfile.write(s1)
    s1 = "        self.exportLiteralChildren(outfile, level, name_)\n"
    outfile.write(s1)
    s1 = "    def exportLiteralAttributes(self, outfile, level, name_):\n"
    outfile.write(s1)
    count = 0
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        count += 1
        name = attrDef.getName()
        cleanName = cleanupName(name)
        capName = make_gs_name(cleanName)
        mappedName = mapName(cleanName)
        s1 = "        showIndent(outfile, level)\n"
        outfile.write(s1)
        stringType = 0
        data_type = attrDef.getData_type()
        if data_type.find('string') >= 0:
            stringType = 1
        else:
            stringType = 1
        if stringType:
            s1 = "        outfile.write('%s = \"%%s\",\\n' %% (self.get%s(),))\n" % \
                (mappedName, capName,)
        else:
            s1 = "        outfile.write('%s = %%s,\\n' %% (self.get%s(),))\n" % \
                (mappedName, capName,)
        outfile.write(s1)
    if element.getAnyAttribute():
        count += 1
        s1 = '        for name, value in self.anyAttributes_.items():\n'
        outfile.write(s1)
        s1 = '            showIndent(outfile, level)\n'
        outfile.write(s1)
        s1 = "            outfile.write('%s = \"%s\",\\n' % (name, value,))\n"
        outfile.write(s1)
    if count == 0:
        s1 = "        pass\n"
        outfile.write(s1)
    if base and base not in SimpleTypeDict:
        s1 = "        %s.exportLiteralAttributes(self, outfile, level, name_)\n" % \
            (base,)
        outfile.write(s1)
    s1 = "    def exportLiteralChildren(self, outfile, level, name_):\n"
    outfile.write(s1)
    for child in element.getChildren():
        name = child.getName()
        name = cleanupName(name)
        #unmappedName = child.getUnmappedCleanName()
        #cleanName = cleanupName(name)
        #mappedName = mapName(cleanName)
        if element.isMixed():
            s1 = "        showIndent(outfile, level)\n"
            outfile.write(s1)
            s1 = "        outfile.write('content_ = [\\n')\n"
            outfile.write(s1)
            s1 = '        for item_ in self.content_:\n'
            outfile.write(s1)
            s1 = '            item_.exportLiteral(outfile, level, name_)\n'
            outfile.write(s1)
            s1 = "        showIndent(outfile, level)\n"
            outfile.write(s1)
            s1 = "        outfile.write('],\\n')\n"
            outfile.write(s1)
        else:
            if child.getMaxOccurs() > 1:
                s1 = "        showIndent(outfile, level)\n"
                outfile.write(s1)
                s1 = "        outfile.write('%s=[\\n')\n" % name
                outfile.write(s1)
                s1 = "        level += 1\n"
                outfile.write(s1)
                s1 = "        for %s in self.%s:\n" % (name, name)
                outfile.write(s1)
                generateExportLiteralFn_2(outfile, child, name, '    ')
                s1 = "        level -= 1\n"
                outfile.write(s1)
                s1 = "        showIndent(outfile, level)\n"
                outfile.write(s1)
                s1 = "        outfile.write('],\\n')\n"
                outfile.write(s1)
            else:
                generateExportLiteralFn_1(outfile, child, name, '')
    if len(element.getChildren()) == 0:
        s1 = "        showIndent(outfile, level)\n"
        outfile.write(s1)
        s1 = "        outfile.write('valueOf_ = \"%s\",\\n' % (self.valueOf_,))\n"
        outfile.write(s1)
    if base and base not in SimpleTypeDict:
        s1 = "        %s.exportLiteralChildren(self, outfile, level, name_)\n" % \
            (base,)
        outfile.write(s1)
    #s1 = "        level -= 1\n"
    #outfile.write(s1)
# end generateExportLiteralFn

#
# Generate build method.
#

def generateBuildAttributes(outfile, element, hasAttributes):
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        hasAttributes += 1
        name = attrDef.getName()
        cleanName = cleanupName(name)
        mappedName = mapName(cleanName)
        atype = attrDef.getData_type()
        if atype in IntegerType or \
            atype == PositiveIntegerType or \
            atype == NonPositiveIntegerType or \
            atype == NegativeIntegerType or \
            atype == NonNegativeIntegerType:
            s1 = "        if attrs.get('%s'):\n" % name
            outfile.write(s1)
            s1 = '            try:\n'
            outfile.write(s1)
            s1 = "                self.%s = int(attrs.get('%s').value)\n" % \
                (mappedName, name)
            outfile.write(s1)
            s1 = '            except ValueError:\n'
            outfile.write(s1)
            s1 = "                raise ValueError('Bad integer attribute (%s)')\n" % \
                (name,)
            outfile.write(s1)
            if atype == PositiveIntegerType:
                s1 = '            if self.%s <= 0:\n' % mappedName
                outfile.write(s1)
                s1 = "                raise ValueError('Invalid PositiveInteger (%s)')\n" % name
                outfile.write(s1)
            elif atype == NonPositiveIntegerType:
                s1 = '            if self.%s > 0:\n' % mappedName
                outfile.write(s1)
                s1 = "                raise ValueError('Invalid NonPositiveInteger (%s)')\n" % name
                outfile.write(s1)
            elif atype == NegativeIntegerType:
                s1 = '            if self.%s >= 0:\n' % mappedName
                outfile.write(s1)
                s1 = "                raise ValueError('Invalid NegativeInteger (%s)')\n" % name
                outfile.write(s1)
            elif atype == NonNegativeIntegerType:
                s1 = '            if self.%s < 0:\n' % mappedName
                outfile.write(s1)
                s1 = "                raise ValueError('Invalid NonNegativeInteger (%s)')\n" % name
                outfile.write(s1)
        elif atype == BooleanType:
            s1 = "        if attrs.get('%s'):\n" % (name,)
            outfile.write(s1)
            s1 = "            if attrs.get('%s').value in ('true', '1'):\n" % \
                (name,)
            outfile.write(s1)
            s1 = "                self.%s = 1\n" % (mappedName,)
            outfile.write(s1)
            s1 = "            elif attrs.get('%s').value in ('false', '0'):\n" % \
                (name,)
            outfile.write(s1)
            s1 = "                self.%s = 0\n" % (mappedName,)
            outfile.write(s1)
            s1 = '            else:\n'
            outfile.write(s1)
            s1 = "                raise ValueError('Bad boolean attribute (%s)')\n" % \
                (name,)
            outfile.write(s1)
        elif atype == FloatType or atype == DoubleType or atype == DecimalType:
            s1 = "        if attrs.get('%s'):\n" % (name,)
            outfile.write(s1)
            s1 = '            try:\n'
            outfile.write(s1)
            s1 = "                self.%s = float(attrs.get('%s').value)\n" % \
                (mappedName, name,)
            outfile.write(s1)
            s1 = '            except Exception:\n'
            outfile.write(s1)
            s1 = "                raise ValueError('Bad float/double attribute (%s)')\n" % \
                (name,)
            outfile.write(s1)
        elif atype == TokenType:
            s1 = "        if attrs.get('%s'):\n" % (name,)
            outfile.write(s1)
            s1 = "            self.%s = attrs.get('%s').value\n" % \
                (mappedName, name,)
            outfile.write(s1)
            s1 = "            self.%s = ' '.join(self.%s.split())\n" % \
                (mappedName, mappedName,)
            outfile.write(s1)
        else:
            # Assume attr['type'] in StringType or attr['type'] == DateTimeType:
            s1 = "        if attrs.get('%s'):\n" % (name,)
            outfile.write(s1)
            s1 = "            self.%s = attrs.get('%s').value\n" % \
                (mappedName, name,)
            outfile.write(s1)
    if element.getAnyAttribute():
        hasAttributes += 1
        s1 = '        self.anyAttributes_ = {}\n'
        outfile.write(s1)
        s1 = '        for name, value in attrs.items():\n'
        outfile.write(s1)
        if len(attrDefs) > 0:
            s1List = ['            if']
            firstTime = 1
            for key in attrDefs:
                if firstTime:
                    s1List.append(' name != "%s"' % key)
                    firstTime = 0
                else:
                    s1List.append(' and name != "%s"' % key)
            s1List.append(':\n')
            s1 = ''.join(s1List)
            outfile.write(s1)
            s1 = '                self.anyAttributes_[name] = value\n'
            outfile.write(s1)
        else:
            s1 = '            self.anyAttributes_[name] = value\n'
            outfile.write(s1)
    return hasAttributes


def generateBuildMixed_1(outfile, prefix, child, headChild, keyword, delayed):
    global DelayedElements, DelayedElements_subclass
    nestedElements = 1
    origName = child.getName()
    name = child.getCleanName()
    headName = cleanupName(headChild.getName())
    childType = child.getType()
    if childType in StringType or \
        childType == TokenType or \
        childType == DateTimeType or \
        childType == DateType:
        s1 = '        %s child_.nodeType == Node.ELEMENT_NODE and \\\n' % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            value_ = []\n"
        outfile.write(s1)
        s1 = "            for text_ in child_.childNodes:\n"
        outfile.write(s1)
        s1 = "                value_.append(text_.nodeValue)\n"
        outfile.write(s1)
        s1 = "            valuestr_ = ''.join(value_)\n"
        outfile.write(s1)
        if childType == TokenType:
            s1 = "            valuestr_ = ' '.join(valuestr_.split())\n"
            outfile.write(s1)
        s1 = "            obj_ = self.mixedclass_(MixedContainer.CategorySimple,\n"
        outfile.write(s1)
        s1 = "                MixedContainer.TypeString, '%s', valuestr_)\n" % \
            origName
        outfile.write(s1)
        s1 = "            self.content_.append(obj_)\n"
        outfile.write(s1)
    elif childType in IntegerType or \
        childType == PositiveIntegerType or \
        childType == NonPositiveIntegerType or \
        childType == NegativeIntegerType or \
        childType == NonNegativeIntegerType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                try:\n"
        outfile.write(s1)
        s1 = "                    ival_ = int(sval_)\n"
        outfile.write(s1)
        s1 = "                except ValueError:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires integer -- %s' % child_.toxml())\n"
        outfile.write(s1)
        if childType == PositiveIntegerType:
            s1 = "                if ival_ <= 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('Invalid positiveInteger (%s)' % child_.toxml()))\n"
            outfile.write(s1)
        if childType == NonPositiveIntegerType:
            s1 = "                if ival_ > 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('Invalid nonPositiveInteger (%s)' % child_.toxml()))\n"
            outfile.write(s1)
        if childType == NegativeIntegerType:
            s1 = "                if ival_ >= 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('Invalid negativeInteger (%s)' % child_.toxml()))\n"
            outfile.write(s1)
        if childType == NonNegativeIntegerType:
            s1 = "                if ival_ < 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('Invalid nonNegativeInteger (%s)' % child_.toxml()))\n"
            outfile.write(s1)
        s1 = "            else:\n"
        outfile.write(s1)
        s1 = "                ival_ = -1\n"
        outfile.write(s1)
        s1 = "            obj_ = self.mixedclass_(MixedContainer.CategorySimple,\n"
        outfile.write(s1)
        s1 = "                MixedContainer.TypeInteger, '%s', ival_)\n" % \
            origName
        outfile.write(s1)
        s1 = "            self.content_.append(obj_)\n"
        outfile.write(s1)
    elif childType == BooleanType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                if sval_ in ('true', '1'):\n"
        outfile.write(s1)
        s1 = "                    ival_ = 1\n"
        outfile.write(s1)
        s1 = "                elif sval_ in ('false', '0'):\n"
        outfile.write(s1)
        s1 = "                    ival_ = 0\n"
        outfile.write(s1)
        s1 = "                else:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires boolean -- %s' % child_.toxml())\n"
        outfile.write(s1)
        s1 = "            obj_ = self.mixedclass_(MixedContainer.CategorySimple,\n"
        outfile.write(s1)
        s1 = "                MixedContainer.TypeInteger, '%s', ival_)\n" % \
            origName
        outfile.write(s1)
        s1 = "            self.content_.append(obj_)\n"
        outfile.write(s1)
    elif childType == FloatType or \
        childType == DoubleType or \
        childType == DecimalType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                try:\n"
        outfile.write(s1)
        s1 = "                    fval_ = float(sval_)\n"
        outfile.write(s1)
        s1 = "                except ValueError:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires float (or double) -- %s' % child_.toxml())\n"
        outfile.write(s1)
        s1 = "            obj_ = self.mixedclass_(MixedContainer.CategorySimple,\n"
        outfile.write(s1)
        s1 = "                MixedContainer.TypeFloat, '%s', fval_)\n" % \
            origName
        outfile.write(s1)
        s1 = "            self.content_.append(obj_)\n"
        outfile.write(s1)
    else:
        # Perhaps it's a complexType that is defined right here.
        # Generate (later) a class for the nested types.
        if not delayed and not child in DelayedElements:
            DelayedElements.append(child)
            DelayedElements_subclass.append(child)
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            childobj_ = %s%s.factory()\n" % \
            (prefix, cleanupName(mapName(childType)))
        outfile.write(s1)
        s1 = "            childobj_.build(child_)\n"
        outfile.write(s1)
        s1 = "            obj_ = self.mixedclass_(MixedContainer.CategoryComplex,\n"
        outfile.write(s1)
        s1 = "                MixedContainer.TypeNone, '%s', childobj_)\n" % \
            origName
        outfile.write(s1)
        s1 = "            self.content_.append(obj_)\n"
        outfile.write(s1)


def generateBuildMixed(outfile, prefix, element, keyword, delayed, hasChildren):
    for child in element.getChildren():
        generateBuildMixed_1(outfile, prefix, child, child, keyword, delayed)
        hasChildren += 1
        keyword = 'elif'
        # Does this element have a substitutionGroup?
        #   If so generate a clause for each element in the substitutionGroup.
        if child.getName() in SubstitutionGroups:
            for memberName in SubstitutionGroups[child.getName()]:
                if memberName in ElementDict:
                    member = ElementDict[memberName]
                    generateBuildMixed_1(outfile, prefix, member, child,
                        keyword, delayed)
    s1 = "        %s child_.nodeType == Node.TEXT_NODE:\n" % keyword
    outfile.write(s1)
    s1 = "            obj_ = self.mixedclass_(MixedContainer.CategoryText,\n"
    outfile.write(s1)
    s1 = "                MixedContainer.TypeNone, '', child_.nodeValue)\n"
    outfile.write(s1)
    s1 = "            self.content_.append(obj_)\n"
    outfile.write(s1)
##    base = element.getBase()
##    if base and base in ElementDict:
##        parent = ElementDict[base]
##        hasChildren = generateBuildMixed(outfile, prefix, parent, keyword, delayed, hasChildren)
    return hasChildren


def generateBuildStandard_1(outfile, prefix, child, headChild, keyword, delayed):
    global DelayedElements, DelayedElements_subclass
    origName = child.getName()
    name = cleanupName(child.getName())
    mappedName = mapName(name)
    headName = cleanupName(headChild.getName())
    attrCount = len(child.getAttributeDefs())
    childType = child.getType()
    if attrCount == 0 and \
        (childType in StringType or \
            childType == TokenType or \
            childType == DateTimeType or \
            childType == DateType \
        ):
        s1 = '        %s child_.nodeType == Node.ELEMENT_NODE and \\\n' % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            %s_ = ''\n" % name
        outfile.write(s1)
        s1 = "            for text__content_ in child_.childNodes:\n"
        outfile.write(s1)
        s1 = "                %s_ += text__content_.nodeValue\n" % name
        outfile.write(s1)
        if childType == TokenType:
            s1 = "            %s_ = ' '.join(%s_.split())\n" % (name, name,)
            outfile.write(s1)
        if child.getMaxOccurs() > 1:
            s1 = "            self.%s.append(%s_)\n" % (mappedName, name,)
            outfile.write(s1)
        else:
            s1 = "            self.%s = %s_\n" % (mappedName, name,)
            outfile.write(s1)
    elif childType in IntegerType or \
        childType == PositiveIntegerType or \
        childType == NonPositiveIntegerType or \
        childType == NegativeIntegerType or \
        childType == NonNegativeIntegerType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                try:\n"
        outfile.write(s1)
        s1 = "                    ival_ = int(sval_)\n"
        outfile.write(s1)
        s1 = "                except ValueError:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires integer -- %s' % child_.toxml())\n"
        outfile.write(s1)
        if childType == PositiveIntegerType:
            s1 = "                if ival_ <= 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('requires positiveInteger -- %s' % child_.toxml())\n"
            outfile.write(s1)
        elif childType == NonPositiveIntegerType:
            s1 = "                if ival_ > 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('requires nonPositiveInteger -- %s' % child_.toxml())\n"
            outfile.write(s1)
        elif childType == NegativeIntegerType:
            s1 = "                if ival_ >= 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('requires negativeInteger -- %s' % child_.toxml())\n"
            outfile.write(s1)
        elif childType == NonNegativeIntegerType:
            s1 = "                if ival_ < 0:\n"
            outfile.write(s1)
            s1 = "                    raise ValueError('requires nonNegativeInteger -- %s' % child_.toxml())\n"
            outfile.write(s1)
        if child.getMaxOccurs() > 1:
            s1 = "                self.%s.append(ival_)\n" % (mappedName,)
            outfile.write(s1)
        else:
            s1 = "                self.%s = ival_\n" % (mappedName,)
            outfile.write(s1)
    elif childType == BooleanType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                if sval_ in ('true', '1'):\n"
        outfile.write(s1)
        s1 = "                    ival_ = 1\n"
        outfile.write(s1)
        s1 = "                elif sval_ in ('false', '0'):\n"
        outfile.write(s1)
        s1 = "                    ival_ = 0\n"
        outfile.write(s1)
        s1 = "                else:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires boolean -- %s' % child_.toxml())\n"
        outfile.write(s1)
        if child.getMaxOccurs() > 1:
            s1 = "                self.%s.append(ival_)\n" % (mappedName,)
            outfile.write(s1)
        else:
            s1 = "                self.%s = ival_\n" % (mappedName,)
            outfile.write(s1)
    elif childType == FloatType or \
        childType == DoubleType or \
        childType == DecimalType:
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            if child_.firstChild:\n"
        outfile.write(s1)
        s1 = "                sval_ = child_.firstChild.nodeValue\n"
        outfile.write(s1)
        s1 = "                try:\n"
        outfile.write(s1)
        s1 = "                    fval_ = float(sval_)\n"
        outfile.write(s1)
        s1 = "                except ValueError:\n"
        outfile.write(s1)
        s1 = "                    raise ValueError('requires float (or double) -- %s' % child_.toxml())\n"
        outfile.write(s1)
        if child.getMaxOccurs() > 1:
            s1 = "                self.%s.append(fval_)\n" % (mappedName,)
            outfile.write(s1)
        else:
            s1 = "                self.%s = fval_\n" % (mappedName,)
            outfile.write(s1)
    else:
        # Perhaps it's a complexType that is defined right here.
        # Generate (later) a class for the nested types.
        if not delayed and not child in DelayedElements:
            DelayedElements.append(child)
            DelayedElements_subclass.append(child)
        s1 = "        %s child_.nodeType == Node.ELEMENT_NODE and \\\n" % \
             keyword
        outfile.write(s1)
        s1 = "            nodeName_ == '%s':\n" % origName
        outfile.write(s1)
        s1 = "            obj_ = %s%s.factory()\n" % \
            (prefix, cleanupName(mapName(childType)))
        outfile.write(s1)
        s1 = "            obj_.build(child_)\n"
        outfile.write(s1)
        if headChild.getMaxOccurs() > 1:
            s1 = "            self.%s.append(obj_)\n" % headName
            outfile.write(s1)
        else:
            s1 = "            self.set%s(obj_)\n" % make_gs_name(headName)
            outfile.write(s1)
    #
    # If this child is defined in a simpleType, then generate
    #   a validator method.
    typeName = None
    if child.getSimpleType():
        typeName = child.getSimpleType()
    elif (childType in ElementDict and
        ElementDict[childType].getSimpleType()):
        typeName = ElementDict[childType].getType()
    if typeName:
        s1 = "            self.validate_%s(self.%s)    # validate type %s\n" % (
            typeName, mappedName, typeName,)
        outfile.write(s1)


def generateBuildStandard(outfile, prefix, element, keyword, delayed, hasChildren):
    for child in element.getChildren():
        generateBuildStandard_1(outfile, prefix, child, child, keyword, delayed)
        hasChildren += 1
        keyword = 'elif'
        # Does this element have a substitutionGroup?
        #   If so generate a clause for each element in the substitutionGroup.
        childName = child.getName()
        if childName in SubstitutionGroups:
            for memberName in SubstitutionGroups[childName]:
                memberName = cleanupName(memberName)
                if memberName in ElementDict:
                    member = ElementDict[memberName]
                    generateBuildStandard_1(outfile, prefix, member, child,
                        keyword, delayed)
    return hasChildren


def generateBuildFn(outfile, prefix, element, delayed):
    base = element.getBase()
    outfile.write('    def build(self, node_):\n')
    outfile.write('        attrs = node_.attributes\n')
    outfile.write('        self.buildAttributes(attrs)\n')
##    if len(element.getChildren()) > 0:
    childCount = countChildren(element, 0)
    if childCount == 0:
        s1 = "        self.valueOf_ = ''\n"
        outfile.write(s1)
    outfile.write('        for child_ in node_.childNodes:\n')
    outfile.write("            nodeName_ = child_.nodeName.split(':')[-1]\n")
    outfile.write("            self.buildChildren(child_, nodeName_)\n")
    outfile.write('    def buildAttributes(self, attrs):\n')
    hasAttributes = generateBuildAttributes(outfile, element, 0)
    if base and base not in SimpleTypeDict:
        hasAttributes += 1
        s1 = '        %s.buildAttributes(self, attrs)\n' % (base,)
        outfile.write(s1)
    if hasAttributes == 0:
        outfile.write('        pass\n')
    outfile.write('    def buildChildren(self, child_, nodeName_):\n')
    keyword = 'if'
    hasChildren = 0
    if element.isMixed():
        hasChildren = generateBuildMixed(outfile, prefix, element, keyword,
            delayed, hasChildren)
    else:      # not element.isMixed()
        hasChildren = generateBuildStandard(outfile, prefix, element, keyword,
            delayed, hasChildren)
    if hasChildren == 0:
##        s1 = "        self.valueOf_ = ''\n"
##        outfile.write(s1)
##        s1 = "        for child in child_.childNodes:\n"
##        outfile.write(s1)
##        s1 = "            if child.nodeType == Node.TEXT_NODE:\n"
##        outfile.write(s1)
##        s1 = "                self.valueOf_ += child.nodeValue\n"
##        outfile.write(s1)
        s1 = "        if child_.nodeType == Node.TEXT_NODE:\n"
        outfile.write(s1)
        s1 = "            self.valueOf_ += child_.nodeValue\n"
        outfile.write(s1)
    if base and base in ElementDict and base not in SimpleTypeDict:
        parent = ElementDict[base]
        if len(parent.getChildren()) > 0:
            s1 = "        %s.buildChildren(self, child_, nodeName_)\n" % (base,)
            outfile.write(s1)
# end generateBuildFn


def countElementChildren(element, count):
    count += len(element.getChildren())
    base = element.getBase()
    if base and base in ElementDict:
        parent = ElementDict[base]
        countElementChildren(parent, count)
    return count


def buildCtorArgs_multilevel(element):
    content = []
    addedArgs = {}
    add = content.append
    buildCtorArgs_multilevel_aux(addedArgs, add, element)
    count = countElementChildren(element, 0)
    if count == 0:
        add(", valueOf_=''")
    if element.isMixed():
        add(', mixedclass_=None')
        add(', content_=None')
    s1 = ''.join(content)
    return s1


def buildCtorArgs_multilevel_aux(addedArgs, add, element):
    base = element.getBase()
    if base and base in ElementDict:
        parent = ElementDict[base]
        buildCtorArgs_multilevel_aux(addedArgs, add, parent)
    buildCtorArgs_aux(addedArgs, add, element)


def buildCtorArgs_aux(addedArgs, add, element):
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        name = attrDef.getName()
        if name in addedArgs:
            continue
        addedArgs[name] = 1
        mappedName = name.replace(':', '_')
        mappedName = cleanupName(mapName(mappedName))
        try:
            atype = attrDef.getData_type()
        except KeyError:
            atype = StringType
        if atype in StringType or \
            atype == TokenType or \
            atype == DateTimeType or \
            atype == DateType:
            add(', %s=\'\'' % mappedName)
        elif atype in IntegerType:
            add(', %s=-1' % mappedName)
        elif atype == PositiveIntegerType:
            add(', %s=1' % mappedName)
        elif atype == NonPositiveIntegerType:
            add(', %s=0' % mappedName)
        elif atype == NegativeIntegerType:
            add(', %s=-1' % mappedName)
        elif atype == NonNegativeIntegerType:
            add(', %s=0' % mappedName)
        elif atype == BooleanType:
            add(', %s=0' % mappedName)
        elif atype == FloatType or atype == DoubleType or atype == DecimalType:
            add(', %s=0.0' % mappedName)
        else:
            add(', %s=None' % mappedName)
    nestedElements = 0
    for child in element.getChildren():
        cleanName = child.getCleanName()
        if cleanName in addedArgs:
            continue
        addedArgs[cleanName] = 1
        nestedElements = 1
        if child.getMaxOccurs() > 1:
            add(', %s=None' % cleanName)
        else:
            childType = child.getType()
            if childType in StringType or \
                childType == TokenType or \
                childType == DateTimeType or \
                childType == DateType:
                add(', %s=\'\'' % cleanName)
            elif childType in IntegerType:
                add(', %s=-1' % cleanName)
            elif childType == PositiveIntegerType:
                add(', %s=1' % cleanName)
            elif childType == NonPositiveIntegerType:
                add(', %s=0' % cleanName)
            elif childType == NegativeIntegerType:
                add(', %s=-1' % cleanName)
            elif childType == NonNegativeIntegerType:
                add(', %s=0' % cleanName)
            elif childType == BooleanType:
                add(', %s=0' % cleanName)
            elif childType == FloatType or \
                childType == DoubleType or \
                childType == DecimalType:
                add(', %s=0.0' % cleanName)
            else:
                add(', %s=None' % cleanName)
# end buildCtorArgs_aux


MixedCtorInitializers = '''\
        if mixedclass_ is None:
            self.mixedclass_ = MixedContainer
        else:
            self.mixedclass_ = mixedclass_
        if content_ is None:
            self.content_ = []
        else:
            self.content_ = content_
'''


def generateCtor(outfile, element):
    s2 = buildCtorArgs_multilevel(element)
    s1 = '    def __init__(self%s):\n' % s2
    outfile.write(s1)
    base = element.getBase()
    if base and base in ElementDict:
        parent = ElementDict[base]
        s2 = buildCtorParams(parent)
        s1 = '        %s.__init__(self%s)\n' % (base, s2,)
        outfile.write(s1)
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        mappedName = cleanupName(attrDef.getName())
        mappedName = mapName(mappedName)
        logging.debug("Constructor attribute: %s" % mappedName)
        s1 = '        self.%s = %s\n' % (mappedName, mappedName)
        outfile.write(s1)
        member = 1
    # Generate member initializers in ctor.
    if element.isMixed():
        outfile.write(MixedCtorInitializers)
    else:
        member = 0
        nestedElements = 0
        for child in element.getChildren():
            name = cleanupName(child.getCleanName())
            logging.debug("Constructor child: %s" % name)
            logging.debug("Dump: %s" % child.__dict__)
            if child.getMaxOccurs() > 1:
                s1 = '        if %s is None:\n' % (name,)
                outfile.write(s1)
                s1 = '            self.%s = []\n' % (name,)
                outfile.write(s1)
                s1 = '        else:\n'
                outfile.write(s1)
                s1 = '            self.%s = %s\n' % \
                    (name, name)
                outfile.write(s1)
            else:
                s1 = '        self.%s = %s\n' % \
                    (name, name)
                outfile.write(s1)
            member = 1
            nestedElements = 1
        if not nestedElements:
            s1 = '        self.valueOf_ = valueOf_\n'
            outfile.write(s1)
            member = 1
        if element.getAnyAttribute():
            s1 = '        self.anyAttributes_ = {}\n'
            outfile.write(s1)
            member = 1
        if not member:
            outfile.write('        pass\n')
# end generateCtor

#
# Attempt to retrieve the body (implementation) of a validator
#   from a directory containing one file for each simpleType.
#   The name of the file should be the same as the name of the
#   simpleType with and optional ".py" extension.
def getValidatorBody(stName):
    retrieved = 0
    if ValidatorBodiesBasePath:
        found = 0
        path = '%s%s%s.py' % (ValidatorBodiesBasePath, os.sep, stName,)
        if os.path.exists(path):
            found = 1
        else:
            path = '%s%s%s' % (ValidatorBodiesBasePath, os.sep, stName,)
            if os.path.exists(path):
                found = 1
        if found:
            infile = open(path, 'r')
            lines = infile.readlines()
            infile.close()
            lines1 = []
            for line in lines:
                if not line.startswith('##'):
                    lines1.append(line)
            s1 = ''.join(lines1)
            retrieved = 1
    if not retrieved:
        s1 = '        pass\n'
    return s1


# Generate get/set/add member functions.
def generateGettersAndSetters(outfile, element):
    nestedElements = 0
    generatedSimpleTypes = []
    for child in element.getChildren():
        name = cleanupName(child.getCleanName())
        unmappedName = cleanupName(child.getName())
        capName = make_gs_name(unmappedName)
        getMaxOccurs = child.getMaxOccurs()
        nestedElements = 1
        childType = child.getType()
        s1 = '    def get%s(self): return self.%s\n' % \
            (capName, name)
        outfile.write(s1)
        s1 = '    def set%s(self, %s): self.%s = %s\n' % \
            (capName, name, name, name)
        outfile.write(s1)
        if child.getMaxOccurs() > 1:
            s1 = '    def add%s(self, value): self.%s.append(value)\n' % \
                (capName, name)
            outfile.write(s1)
            s1 = '    def insert%s(self, index, value): self.%s[index] = value\n' % \
                (capName, name)
            outfile.write(s1)
        if GenerateProperties:
            s1 = '    %sProp = property(get%s, set%s)\n' % \
                (unmappedName, capName, capName)
            outfile.write(s1)
        #
        # If this child is defined in a simpleType, then generate
        #   a validator method.
        typeName = None
        if child.getSimpleType():
            typeName = child.getSimpleType()
        elif (childType in ElementDict and
            ElementDict[childType].getSimpleType()):
            typeName = ElementDict[childType].getType()
        if typeName:
            generatedSimpleTypes.append(typeName)
            #s1 = '    def validate_%s(self, value):\n' % (capName, )
            s1 = '    def validate_%s(self, value):\n' % (typeName,)
            outfile.write(s1)
            if typeName in SimpleTypeDict:
                stObj = SimpleTypeDict[typeName]
                s1 = '        # Validate type %s, a restriction on %s.\n' % (
                    typeName, stObj.getBase(),)
                outfile.write(s1)
            else:
                s1 = '        # validate type %s\n' % (typeName,)
                outfile.write(s1)
            s1 = getValidatorBody(typeName)
            outfile.write(s1)
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        name = cleanupName(attrDef.getName().replace(':', '_'))
        mappedName = mapName(name)
        capName = make_gs_name(mappedName)
        s1 = '    def get%s(self): return self.%s\n' % \
            (make_gs_name(name), mappedName)
        outfile.write(s1)
        #
        # What?  An attribute cannot occur multiple times on the same
        #   element.  No attribute is a list of values.  Right?
##        if element.getMaxOccurs() > 1:
##            s1 = '    def add%s(self, %s): self.%s.append(%s)\n' % \
##                (capName, mappedName, mappedName, mappedName)
##            outfile.write(s1)
##            s1 = '    def set%s(self, %s, index): self.%s[index] = %s\n' % \
##                (make_gs_name(name), mappedName, mappedName, mappedName)
##            outfile.write(s1)
##        else:
        s1 = '    def set%s(self, %s): self.%s = %s\n' % \
            (make_gs_name(name), mappedName, mappedName, mappedName)
        outfile.write(s1)
        if GenerateProperties:
            s1 = '    %sProp = property(get%s, set%s)\n' % \
                (mappedName, capName, capName)
            outfile.write(s1)
    if not nestedElements:
        s1 = '    def getValueOf_(self): return self.valueOf_\n'
        outfile.write(s1)
        s1 = '    def setValueOf_(self, valueOf_): self.valueOf_ = valueOf_\n'
        outfile.write(s1)
    if element.getAnyAttribute():
        s1 = '    def getAnyAttributes_(self): return self.anyAttributes_\n'
        outfile.write(s1)
        s1 = '    def setAnyAttributes_(self, anyAttributes_): self.anyAttributes_ = anyAttributes_\n'
        outfile.write(s1)
# end generateGettersAndSetters


#
# Generate a class variable whose value is a list of tuples, one
#   tuple for each member data item of the class.
#   Each tuble has 3 elements: (1) member name, (2) member data type,
#   (3) container/list or not (maxoccurs > 1).
def generateMemberSpec(outfile, element):
    content = ['    _member_data_items = [']
    add = content.append
    for child in element.getChildren():
        name = cleanupName(child.getCleanName())
        item1 = name
        item2 = child.getType()
        if child.getMaxOccurs() > 1:
            item3 = 1
        else:
            item3 = 0
        #item = "        ('%s', '%s', %d)," % (item1, item2, item3, )
        item = "        _MemberSpec('%s', '%s', %d)," % (item1, item2, item3,)
        add(item)
    add('        ]')
    s1 = '\n'.join(content)
    outfile.write(s1)
    outfile.write('\n')


def generateUserMethods(outfile, element):
    if not UserMethodsModule:
        return
    specs = UserMethodsModule.METHOD_SPECS
    name = cleanupName(element.getCleanName())
    values_dict = {'class_name': name, }
    for spec in specs:
        if spec.match_name(name):
            source = spec.get_interpolated_source(values_dict)
            outfile.write(source)


def generateClasses(outfile, prefix, element, delayed):
    logging.debug("Generating class for: %s" % element)
    base = element.getBase()
    logging.debug("Element base: %s" % base)
    wrt = outfile.write
##    if (not element.getChildren()) and (not element.getAttributeDefs()):
##        return
    if not element.isExplicitDefine():
        logging.debug("Not an explicit define, returning.")
        return
    # If this element is an extension (has a base) and the base has
    #   not been generated, then postpone it.
    if base and base in ElementDict:
        parent = ElementDict[base]
        parentName = parent.getName()
        if (parentName not in AlreadyGenerated and
            parentName not in SimpleTypeDict.keys()):
            PostponedExtensions.append(element)
            return
    if element.getName() in AlreadyGenerated:
        return
    AlreadyGenerated.append(element.getName())
    if element.getMixedExtensionError():
        print('*** Element %s extension chain contains mixed and non-mixed content.  Not generated.' % \
            (element.getName(),))
        return
    ElementsForSubclasses.append(element)
    name = element.getCleanName()
    if GenerateProperties:
        if base and base not in SimpleTypeDict:
            s1 = 'class %s%s(object, %s):\n' % (prefix, name, base)
        else:
            s1 = 'class %s%s(object):\n' % (prefix, name)
    else:
        if base and base not in SimpleTypeDict:
            s1 = 'class %s%s(%s):\n' % (prefix, name, base)
        else:
            s1 = 'class %s%s:\n' % (prefix, name)
    wrt(s1)
    if UserMethodsModule:
        generateMemberSpec(outfile, element)
    wrt('    subclass = None\n')
    generateCtor(outfile, element)
    wrt('    def factory(*args_, **kwargs_):\n')
    wrt('        if %s%s.subclass:\n' % (prefix, name))
    wrt('            return %s%s.subclass(*args_, **kwargs_)\n' % (prefix, name))
    wrt('        else:\n')
    wrt('            return %s%s(*args_, **kwargs_)\n' % (prefix, name))
    wrt('    factory = staticmethod(factory)\n')
    generateGettersAndSetters(outfile, element)
    generateExportFn(outfile, prefix, element)
    generateExportFnXML(outfile, prefix, element)
    generateStaticParseString(outfile, prefix, element)
    generateStaticParseFile(outfile, prefix, element)
    generateMarshal(outfile, prefix, element)
    generateExportLiteralFn(outfile, prefix, element)
    generateBuildFn(outfile, prefix, element, delayed)
    generateUserMethods(outfile, element)
    wrt('# end class %s\n' % name)
    wrt('\n\n')
# end generateClasses


#
# Generate the SAX handler class for SAX parsing.
#

SAX_STARTELEMENT_1 = """\
    def startElement(self, name, attrs):
        done = 0
        if name == '%s':
            obj = %s.factory()
            stackObj = SaxStackElement('%s', obj)
            self.stack.append(stackObj)
            done = 1
"""

SAX_STARTELEMENT_2 = """\
            stackObj = SaxStackElement('%s', obj)
            self.stack.append(stackObj)
            done = 1
"""

SAX_STARTELEMENT_3 = """\
            stackObj = SaxStackElement('%s', None)
            self.stack.append(stackObj)
            done = 1
"""

SAX_STARTELEMENT_4 = """\
        if not done:
            self.reportError('"%s" element not allowed here.' % name)
"""

SAX_ATTR_INTEGER = """\
            val = attrs.get('%s', None)
            if val is not None:
                try:
                    obj.set%s(int(val))
                except Exception:
                    self.reportError('"%s" attribute must be integer')
"""

SAX_ATTR_BOOLEAN = """\
            val = attrs.get('%s', None)
            if val is not None:
                if val in ('true', '1'):
                    obj.set%s(1)
                elif val in ('false', '0'):
                    obj.set%s(0)
                else:
                    self.reportError('"%s" attribute must be boolean ("true", "1", "false", "0")')
"""

SAX_ATTR_FLOAT = """\
            val = attrs.get('%s', None)
            if val is not None:
                try:
                    obj.set%s(float(val))
                except Exception:
                    self.reportError('"%s" attribute must be float')
"""

SAX_ATTR_STRING = """\
            val = attrs.get('%s', None)
            if val is not None:
                obj.set%s(val)
"""

def getClassName(element):
    name = element.getCleanName()
    return name

def generateSaxAttributes(wrt, element):
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        name = attrDef.getName()
        atype = attrDef.getData_type()
        if atype in IntegerType:
            s1 = SAX_ATTR_INTEGER % (name, make_gs_name(name), name)
            wrt(s1)
##             s1 = "            if attrs.get('%s'):\n" % name
##             wrt(s1)
##             s1 = '                try:\n'
##             wrt(s1)
##             s1 = "                    self.%s = int(attrs.get('%s').value)\n" % \
##                 (name, name)
##             wrt(s1)
##             s1 = '                except ValueError:\n'
##             wrt(s1)
##             s1 = "                    raise ValueError('Bad integer')\n"
##             wrt(s1)
        elif atype == BooleanType:
            s1 = SAX_ATTR_BOOLEAN % (name, make_gs_name(name), \
                make_gs_name(name), name)
            wrt(s1)
##             wrt(s1)
##             s1 = "            if attrs.get('%s'):\n" % name
##             wrt(s1)
##             s1 = "                if attrs.get('%s').value in ('true', '1'):\n" % \
##                 name
##             wrt(s1)
##             s1 = "                    self.%s = 1\n" % \
##                 name
##             wrt(s1)
##             s1 = "                elif attrs.get('%s').value in ('false', '0'):\n" % \
##                 name
##             wrt(s1)
##             s1 = "                    self.%s = 0\n" % \
##                 name
##             wrt(s1)
##             s1 = '            else:\n'
##             wrt(s1)
##             s1 = "                raise ValueError('Bad boolean')\n"
##             wrt(s1)
        elif atype == FloatType or atype == DoubleType or atype == DecimalType:
            s1 = SAX_ATTR_FLOAT % (name, make_gs_name(name), name)
            wrt(s1)
##             s1 = "            if attrs.get('%s'):\n" % name
##             wrt(s1)
##             s1 = '                try:\n'
##             wrt(s1)
##             s1 = "                    self.%s = float(attrs.get('%s').value)\n" % \
##                 (name, name)
##             wrt(s1)
##             s1 = '                except Exception:\n'
##             wrt(s1)
##             s1 = "                    raise ValueError('Bad float/double')\n"
##             wrt(s1)
        else:
            # Assume attr['type'] in StringType or attr['type'] == DateTimeType:
            s1 = SAX_ATTR_STRING % (name, make_gs_name(name))
            wrt(s1)
##             s1 = "            if attrs.get('%s'):\n" % name
##             wrt(s1)
##             s1 = "                self.%s = attrs.get('%s').value\n" % (name, name)
##             wrt(s1)


def generateSAXStartElement_1(wrt, element):
    origName = element.getName()
    typeName = cleanupName(mapName(element.getRawType()))
    className = element.getCleanName()
    s1 = "        elif name == '%s':\n" % origName
    wrt(s1)
    if element.isComplex():
        s1 = "            obj = %s.factory()\n" % cleanupName(typeName)
        wrt(s1)
    element1 = SaxElementDict[element.getCleanName()]
    generateSaxAttributes(wrt, element1)
    if element.isComplex():
        s1 = SAX_STARTELEMENT_2 % className
    else:
        s1 = SAX_STARTELEMENT_3 % className
    wrt(s1)

def generateSAXStartElement(outfile, root, elementList):
    wrt = outfile.write
    name = root.getChildren()[0].getName()
    s1 = SAX_STARTELEMENT_1 % (name, name, name)
    wrt(s1)
    for element, parent in elementList:
        generateSAXStartElement_1(wrt, element)
    s1 = SAX_STARTELEMENT_4
    wrt(s1)
    wrt('\n')


SAX_ENDELEMENT_1 = """\
        if name == '%s':
            if len(self.stack) == 1:
                self.root = self.stack[-1].obj
                self.stack.pop()
                done = 1
"""

SAX_ENDELEMENT_2 = """\
        elif name == '%s':
            if len(self.stack) >= 2:
                self.stack[-2].obj.%s%s(self.stack[-1].obj)
                self.stack.pop()
                done = 1
"""

SAX_ENDELEMENT_3 = """\
        elif name == '%s':
            if len(self.stack) >= 2:
                content = self.stack[-1].content
%s                self.stack[-2].obj.%s%s(content)
                self.stack.pop()
                done = 1
"""

SAX_ENDELEMENT_INT = """\
                if content:
                    try:
                        content = int(content)
                    except Exception:
                        self.reportError('"%s" must be integer -- content: %%s' %% content)
                else:
                    content = -1
"""

SAX_ENDELEMENT_FLOAT = """\
                if content:
                    try:
                        content = float(content)
                    except Exception:
                        self.reportError('"%s" must be float -- content: %%s' %% content)
                else:
                    content = -1
"""

SAX_ENDELEMENT_BOOLEAN = """\
                if content and content in ('true', '1'):
                    content = 1
                else:
                    content = 0
"""

SAX_ENDELEMENT_4 = """\
        if not done:
            self.reportError('"%s" element not allowed here.' % name)
"""

def generateParentCheck(parent):
    s1 = "self.stack[-2].name == '%s'" % getClassName(parent)
    return s1
##     strList = []
##     for parent in parentList:
##         strList.append("self.stack[-2].name == '%s'" % \
##             parent.getName())
##     s1 = ' or '.join(strList)
##     if len(parentList) > 1:
##         s1 = '(%s)' % s1
##     return s1

def generateSAXEndElement(outfile, root, elementList):
    wrt = outfile.write
    s1 = "    def endElement(self, name):\n"
    wrt(s1)
    s1 = "        done = 0\n"
    wrt(s1)
    name = root.getChildren()[0].getName()
    s1 = SAX_ENDELEMENT_1 % (name,)
    wrt(s1)
    for element, parent in elementList:
        #s2 = generateParentCheck(parent)
        name = element.getName()
        capName = make_gs_name(element.getUnmappedCleanName())
        if element.isComplex():
            if element.getMaxOccurs() > 1:
                s1 = SAX_ENDELEMENT_2 % (name, 'add', capName)
            else:
                s1 = SAX_ENDELEMENT_2 % (name, 'set', capName)
        else:
            etype = element.getType()
            if etype in IntegerType:
                s3 = SAX_ENDELEMENT_INT % name
            elif etype == FloatType or etype == DoubleType or etype == DecimalType:
                s3 = SAX_ENDELEMENT_FLOAT % name
            elif etype == BooleanType:
                s3 = SAX_ENDELEMENT_BOOLEAN
            else:
                s3 = ''
            if element.getMaxOccurs() > 1:
                s1 = SAX_ENDELEMENT_3 % (name, s3, 'add', capName)
            else:
                s1 = SAX_ENDELEMENT_3 % (name, s3, 'set', capName)
        wrt(s1)
    s1 = SAX_ENDELEMENT_4
    wrt(s1)
    wrt('\n')


SAX_HEADER = """\
from xml.sax import handler, make_parser

class SaxStackElement:
    def __init__(self, name='', obj=None):
        self.name = name
        self.obj = obj
        self.content = ''

#
# SAX handler
#
class Sax%sHandler(handler.ContentHandler):
    def __init__(self):
        self.stack = []
        self.root = None

    def getRoot(self):
        return self.root

    def setDocumentLocator(self, locator):
        self.locator = locator
    
    def showError(self, msg):
        print('*** (showError):', msg)
        sys.exit(-1)

"""

SAX_FOOTER = """\
    def characters(self, chrs, start, end):
        if len(self.stack) > 0:
            self.stack[-1].content += chrs[start:end]

    def reportError(self, mesg):
        locator = self.locator
        sys.stderr.write('Doc: %s  Line: %d  Column: %d\\n' % \\
            (locator.getSystemId(), locator.getLineNumber(), 
            locator.getColumnNumber() + 1))
        sys.stderr.write(mesg)
        sys.stderr.write('\\n')
        sys.exit(-1)
        #raise RuntimeError

"""


##def produceAllElements(element, parent):
##     if element.getType() in StringType or \
##         element.getType() in IntegerType or \
##         element.getType() == DecimalType or \
##         element.getType() == FloatType or \
##         element.getType() == DoubleType or \
##         element.getType() == BooleanType or \
##         len(element.getChildren()) != 0:
##    yield (element, parent)
##    for child in element.getChildren():
##        for element1, parent1 in produceAllElements(child, element):
##            yield (element1, parent1)


#
# This version of produceAllElements does not use 'yield' and is,
#   therefore, usable with older versions of Python.
def produceAllElements_nogen(element, parent, collection):
    collection.append((element, parent))
    for child in element.getChildren():
        produceAllElements_nogen(child, element, collection)


def generateSAXHndlr(outfile, root):
    firstElement = root.getChildren()[0]
    name = firstElement.getName()
    s1 = SAX_HEADER % cleanupName(make_gs_name(name))
    outfile.write(s1)
    elementList = []
    collection = []
    produceAllElements_nogen(root, None, collection)
    for element, parent in collection:
        if element == root:
            continue
        elementList.append((element, parent))
##         print '(gsh) element: %s/%s/%d  parent: %s/%s/%d' % \
##             (element.getUnmappedCleanName(), element.getType(), id(element), 
##             #(element.getName(), element.getType(), id(element), 
##             parent.getName(), parent.getType(), id(parent))
##         if parent.getName() == 'booster':
##             ipshell('at booster -- Entering ipshell.\\nHit Ctrl-D to exit')
##         if element in elementDict:
##             elementDict[element].append(parent)
##         else:
##             elementDict[element] = [parent]
    elementList1 = []
    alreadySeen = []
    for element, parent in elementList:
        if parent == root:
            continue
        if element.getName() in alreadySeen:
            continue
        alreadySeen.append(element.getName())
        elementList1.append((element, parent))
##     print '+' * 20
##     for element, parent in elementList1:
##         print '(gsh) element: %s/%s/%d  parent: %s/%s/%d' % \
##             (element.getUnmappedCleanName(), element.getType(), id(element), 
##             #(element.getName(), element.getType(), id(element), 
##             parent.getName(), parent.getType(), id(parent))
    generateSAXStartElement(outfile, root, elementList1)
    generateSAXEndElement(outfile, root, elementList1)
    s1 = SAX_FOOTER
    outfile.write(s1)


def collect(element, elements):
    if element.getName() != 'root':
        elements.append(element)
    for child in element.getChildren():
        collect(child, elements)


TEMPLATE_HEADER = """\
#!/usr/bin/env python

#
# Generated %s by EDGenerateDS.py.
#

import sys
import getopt
import StringIO
from xml.dom import minidom
from xml.dom import Node

#
# If you have installed IPython you can uncomment and use the following.
# IPython is available from http://ipython.scipy.org/.
#

## from IPython.Shell import IPShellEmbed
## args = ''
## ipshell = IPShellEmbed(args,
##     banner = 'Dropping into IPython',
##     exit_msg = 'Leaving Interpreter, back to program.')

# Then use the following line where and when you want to drop into the
# IPython shell:
#    ipshell('<some message> -- Entering ipshell.\\nHit Ctrl-D to exit')

#
# Support/utility functions.
#

def showIndent(outfile, level):
    for idx in range(level):
        outfile.write('    ')

def quote_xml(inStr):
    s1 = inStr
    s1 = s1.replace('&', '&amp;')
    s1 = s1.replace('<', '&lt;')
    s1 = s1.replace('"', '&quot;')
    return s1

def quote_python(inStr):
    s1 = inStr
    if s1.find("'") == -1:
        if s1.find('\\n') == -1:
            return "'%%s'" %% s1
        else:
            return "'''%%s'''" %% s1
    else:
        if s1.find('"') != -1:
            s1 = s1.replace('"', '\\\\"')
        if s1.find('\\n') == -1:
            return '"%%s"' %% s1
        else:
            return '\"\"\"%%s\"\"\"' %% s1


class MixedContainer:
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
        else:    # category == MixedContainer.CategoryComplex
            self.value.export(outfile, level, name)
    def exportSimple(self, outfile, level, name):
        if self.content_type == MixedContainer.TypeString:
            outfile.write('<%%s>%%s</%%s>' %% (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeInteger or \\
                self.content_type == MixedContainer.TypeBoolean:
            outfile.write('<%%s>%%d</%%s>' %% (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeFloat or \\
                self.content_type == MixedContainer.TypeDecimal:
            outfile.write('<%%s>%%f</%%s>' %% (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeDouble:
            outfile.write('<%%s>%%g</%%s>' %% (self.name, self.value, self.name))
    def exportLiteral(self, outfile, level, name):
        if self.category == MixedContainer.CategoryText:
            showIndent(outfile, level)
            outfile.write('MixedContainer(%%d, %%d, "%%s", "%%s"),\\n' %% \\
                (self.category, self.content_type, self.name, self.value))
        elif self.category == MixedContainer.CategorySimple:
            showIndent(outfile, level)
            outfile.write('MixedContainer(%%d, %%d, "%%s", "%%s"),\\n' %% \\
                (self.category, self.content_type, self.name, self.value))
        else:    # category == MixedContainer.CategoryComplex
            showIndent(outfile, level)
            outfile.write('MixedContainer(%%d, %%d, "%%s",\\n' %% \\
                (self.category, self.content_type, self.name,))
            self.value.exportLiteral(outfile, level + 1)
            showIndent(outfile, level)
            outfile.write(')\\n')


class _MemberSpec(object):
    def __init__(self, name='', data_type='', container=0):
        self.name = name
        self.data_type = data_type
        self.container = container
    def set_name(self, name): self.name = name
    def get_name(self): return self.name
    def set_data_type(self, data_type): self.data_type = data_type
    def get_data_type(self): return self.data_type
    def set_container(self, container): self.container = container
    def get_container(self): return self.container


#
# Data representation classes.
#

"""

# Fool (and straighten out) the syntax highlighting.
# DUMMY = '''

def generateHeader(outfile, prefix):
    s1 = TEMPLATE_HEADER % time.ctime()
    outfile.write(s1)


TEMPLATE_MAIN = """\
USAGE_TEXT = \"\"\"
Usage: python <%(prefix)sParser>.py [ -s ] <in_xml_file>
Options:
    -s        Use the SAX parser, not the minidom parser.
\"\"\"

def usage():
    print(USAGE_TEXT)
    sys.exit(-1)


#
# SAX handler used to determine the top level element.
#
class SaxSelectorHandler(handler.ContentHandler):
    def __init__(self):
        self.topElementName = None
    def getTopElementName(self):
        return self.topElementName
    def startElement(self, name, attrs):
        self.topElementName = name
        raise StopIteration


def parseSelect(inFileName):
    infile = file(inFileName, 'r')
    topElementName = None
    parser = make_parser()
    documentHandler = SaxSelectorHandler()
    parser.setContentHandler(documentHandler)
    try:
        try:
            parser.parse(infile)
        except StopIteration:
            topElementName = documentHandler.getTopElementName()
        if topElementName is None:
            raise RuntimeError('no top level element')
        topElementName = topElementName.replace('-', '_').replace(':', '_')
        if topElementName not in globals():
            raise RuntimeError('no class for top element: %%s' %% topElementName)
        topElement = globals()[topElementName]
        infile.seek(0)
        doc = minidom.parse(infile)
    finally:
        infile.close()
    rootNode = doc.childNodes[0]
    rootObj = topElement.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0)
    return rootObj


def saxParse(inFileName):
    parser = make_parser()
    documentHandler = Sax%(cap_name)sHandler()
    parser.setDocumentHandler(documentHandler)
    parser.parse('file:%%s' %% inFileName)
    root = documentHandler.getRoot()
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    root.export(sys.stdout, 0)
    return root


def saxParseString(inString):
    parser = make_parser()
    documentHandler = Sax%(cap_name)sHandler()
    parser.setDocumentHandler(documentHandler)
    parser.feed(inString)
    parser.close()
    rootObj = documentHandler.getRoot()
    #sys.stdout.write('<?xml version="1.0" ?>\\n')
    #rootObj.export(sys.stdout, 0)
    return rootObj


def parse(inFileName):
    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement
    rootObj = %(prefix)s%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0, name_="%(name)s")
    return rootObj


def parseString(inString):
    doc = minidom.parseString(inString)
    rootNode = doc.documentElement
    rootObj = %(prefix)s%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0, name_="%(name)s")
    return rootObj


def parseLiteral(inFileName):
    doc = minidom.parse(inFileName)
    rootNode = doc.documentElement
    rootObj = %(prefix)s%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('from %(module_name)s import *\\n\\n')
    sys.stdout.write('rootObj = %(name)s(\\n')
    rootObj.exportLiteral(sys.stdout, 0, name_="%(name)s")
    sys.stdout.write(')\\n')
    return rootObj

class %(module_name)s:
    pass


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-s':
        saxParse(args[1])
    elif len(args) == 1:
        parse(args[0])
    else:
        usage()


if __name__ == '__main__':
    main()
    #import pdb
    #pdb.run('main()')

"""


# Fool (and straighten out) the syntax highlighting.
# DUMMY = '''


def generateMain(outfile, prefix, root):
    name = root.getChildren()[0].getName()
    elType = cleanupName(root.getChildren()[0].getType())
    if RootElement:
        rootElement = RootElement
    else:
        rootElement = elType
    params = {
        'prefix': prefix,
        'cap_name': cleanupName(make_gs_name(name)),
        'name': cleanupName(name),
        'module_name': os.path.splitext(os.path.basename(outfile.name))[0],
        'root': rootElement,
        }
    s1 = TEMPLATE_MAIN % params
    outfile.write(s1)


def buildCtorParams(element):
    content = []
    add = content.append
    if element.isMixed():
        add(', mixedclass_')
        add(', content_')
    else:
        buildCtorParams_aux(add, element)
    s1 = ''.join(content)
    return s1


def buildCtorParams_aux(add, element):
    base = element.getBase()
    if base and base in ElementDict:
        parent = ElementDict[base]
        buildCtorParams_aux(add, parent)
    attrDefs = element.getAttributeDefs()
    for key in attrDefs:
        attrDef = attrDefs[key]
        name = attrDef.getName()
        cleanName = cleanupName(mapName(name))
        add(', %s' % cleanName)
    for child in element.getChildren():
        add(', %s' % child.getCleanName())


def get_class_behavior_args(classBehavior):
    argList = []
    args = classBehavior.getArgs()
    args = args.getArg()
    #print '(get_class_behavior_args) args:', args
    for arg in args:
        argList.append(arg.getName())
    argString = ', '.join(argList)
    return argString


#
# Retrieve the implementation body via an HTTP request to a
#   URL formed from the concatenation of the baseImplUrl and the
#   implUrl.
# An alternative implementation of get_impl_body() that also
#   looks in the local file system is commented out below.
#
def get_impl_body(classBehavior, baseImplUrl, implUrl):
    impl = '        pass\n'
    if implUrl:
        if baseImplUrl:
            implUrl = '%s%s' % (baseImplUrl, implUrl)
        try:
            implFile = urllib2.urlopen(implUrl)
            impl = implFile.read()
            implFile.close()
        except urllib2.HTTPError:
            print('*** Implementation at %s not found.' % implUrl)
        except urllib2.URLError:
            print('*** Connection refused for URL: %s' % implUrl)
    return impl

###
### This alternative implementation of get_impl_body() tries the URL
###   via http first, then, if that fails, looks in a directory on
###   the local file system (baseImplUrl) for a file (implUrl)
###   containing the implementation body.
###
##def get_impl_body(classBehavior, baseImplUrl, implUrl):
##    impl = '        pass\n'
##    if implUrl:
##        trylocal = 0
##        if baseImplUrl:
##            implUrl = '%s%s' % (baseImplUrl, implUrl)
##        try:
##            implFile = urllib2.urlopen(implUrl)
##            impl = implFile.read()
##            implFile.close()
##        except Exception:
##            trylocal = 1
##        if trylocal:
##            try:
##                implFile = file(implUrl)
##                impl = implFile.read()
##                implFile.close()
##            except Exception:
##                print '*** Implementation at %s not found.' % implUrl
##    return impl


def generateClassBehaviors(wrt, classBehaviors, baseImplUrl):
    for classBehavior in classBehaviors:
        behaviorName = classBehavior.getName()
        #
        # Generate the core behavior.
        argString = get_class_behavior_args(classBehavior)
        if argString:
            wrt('    def %s(self, %s, *args):\n' % (behaviorName, argString))
        else:
            wrt('    def %s(self, *args):\n' % (behaviorName,))
        implUrl = classBehavior.getImpl_url()
        impl = get_impl_body(classBehavior, baseImplUrl, implUrl)
        wrt(impl)
        wrt('\n')
        #
        # Generate the ancillaries for this behavior.
        ancillaries = classBehavior.getAncillaries()
        if ancillaries:
            ancillaries = ancillaries.getAncillary()
        if ancillaries:
            for ancillary in ancillaries:
                argString = get_class_behavior_args(ancillary)
                if argString:
                    wrt('    def %s(self, %s, *args):\n' % (ancillary.getName(), argString))
                else:
                    wrt('    def %s(self, *args):\n' % (ancillary.getName(),))
                implUrl = ancillary.getImpl_url()
                impl = get_impl_body(classBehavior, baseImplUrl, implUrl)
                wrt(impl)
                wrt('\n')
        #
        # Generate the wrapper method that calls the ancillaries and
        #   the core behavior.
        argString = get_class_behavior_args(classBehavior)
        if argString:
            wrt('    def %s_wrapper(self, %s, *args):\n' % (behaviorName, argString))
        else:
            wrt('    def %s_wrapper(self, *args):\n' % (behaviorName,))
        if ancillaries:
            for ancillary in ancillaries:
                role = ancillary.getRole()
                if role == 'DBC-precondition':
                    wrt('        if not self.%s(*args)\n' % (ancillary.getName(),))
                    wrt('            return False\n')
        if argString:
            wrt('        result = self.%s(%s, *args)\n' % (behaviorName, argString))
        else:
            wrt('        result = self.%s(*args)\n' % (behaviorName,))
        if ancillaries:
            for ancillary in ancillaries:
                role = ancillary.getRole()
                if role == 'DBC-postcondition':
                    wrt('        if not self.%s(*args)\n' % (ancillary.getName(),))
                    wrt('            return False\n')
        wrt('        return result\n')
        wrt('\n')


def generateSubclass(outfile, element, prefix, xmlbehavior, behaviors, baseUrl):
    wrt = outfile.write
    if not element.isComplex():
        return
    if (not element.getChildren()) and (not element.getAttributeDefs()):
        return
    if element.getName() in AlreadyGenerated_subclass:
        return
    AlreadyGenerated_subclass.append(element.getName())
    name = element.getCleanName()
    wrt('class %s%s%s(supermod.%s):\n' % (prefix, name, SubclassSuffix, name))
    s1 = buildCtorArgs_multilevel(element)
    wrt('    def __init__(self%s):\n' % s1)
    s1 = buildCtorParams(element)
    wrt('        supermod.%s%s.__init__(self%s)\n' % (prefix, name, s1))
    if xmlbehavior and behaviors:
        wrt('\n')
        wrt('    #\n')
        wrt('    # XMLBehaviors\n')
        wrt('    #\n')
        # Get a list of behaviors for this class/subclass.
        classDictionary = behaviors.get_class_dictionary()
        if name in classDictionary:
            classBehaviors = classDictionary[name]
        else:
            classBehaviors = None
        if classBehaviors:
            generateClassBehaviors(wrt, classBehaviors, baseUrl)
    wrt('supermod.%s.subclass = %s%s\n' % (name, name, SubclassSuffix))
    wrt('# end class %s%s%s\n' % (prefix, name, SubclassSuffix))
    wrt('\n\n')


TEMPLATE_SUBCLASS_HEADER = """\
#!/usr/bin/env python

#
# Generated %s by EDGenerateDS.py.
#

import sys
from xml.dom import minidom
from xml.sax import handler, make_parser

import %s as supermod

"""

TEMPLATE_SUBCLASS_FOOTER = """\

#
# SAX handler used to determine the top level element.
#
class SaxSelectorHandler(handler.ContentHandler):
    def __init__(self):
        self.topElementName = None
    def getTopElementName(self):
        return self.topElementName
    def startElement(self, name, attrs):
        self.topElementName = name
        raise StopIteration


def parseSelect(inFileName):
    infile = file(inFileName, 'r')
    topElementName = None
    parser = make_parser()
    documentHandler = SaxSelectorHandler()
    parser.setContentHandler(documentHandler)
    try:
        try:
            parser.parse(infile)
        except StopIteration:
            topElementName = documentHandler.getTopElementName()
        if topElementName is None:
            raise RuntimeError('no top level element')
        topElementName = topElementName.replace('-', '_').replace(':', '_')
        if topElementName not in supermod.__dict__:
            raise RuntimeError('no class for top element: %%s' %% topElementName)
        topElement = supermod.__dict__[topElementName]
        infile.seek(0)
        doc = minidom.parse(infile)
    finally:
        infile.close()
    rootNode = doc.childNodes[0]
    rootObj = topElement.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0)
    return rootObj


def saxParse(inFileName):
    parser = make_parser()
    documentHandler = supermod.Sax%(cap_name)sHandler()
    parser.setDocumentHandler(documentHandler)
    parser.parse('file:%%s' %% inFileName)
    rootObj = documentHandler.getRoot()
    #sys.stdout.write('<?xml version="1.0" ?>\\n')
    #rootObj.export(sys.stdout, 0)
    return rootObj


def saxParseString(inString):
    parser = make_parser()
    documentHandler = supermod.SaxContentHandler()
    parser.setDocumentHandler(documentHandler)
    parser.feed(inString)
    parser.close()
    rootObj = documentHandler.getRoot()
    #sys.stdout.write('<?xml version="1.0" ?>\\n')
    #rootObj.export(sys.stdout, 0)
    return rootObj


def parse(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0, name_="%(name)s")
    doc = None
    return rootObj


def parseString(inString):
    doc = minidom.parseString(inString)
    rootNode = doc.documentElement
    rootObj = supermod.%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\\n')
    rootObj.export(sys.stdout, 0, name_="%(name)s")
    return rootObj


def parseLiteral(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.%(root)s.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('from %(super)s import *\\n\\n')
    sys.stdout.write('rootObj = %(name)s(\\n')
    rootObj.exportLiteral(sys.stdout, 0, name_="%(name)s")
    sys.stdout.write(')\\n')
    return rootObj


USAGE_TEXT = \"\"\"
Usage: python ???.py <infilename>
\"\"\"

def usage():
    print(USAGE_TEXT)
    sys.exit(-1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    main()
    #import pdb
    #pdb.run('main()')


"""

##def isMember(item, lst):
##    for item1 in lst:
##        if item == item1:
##            print '(isMember) found name: %s' % item
##            return True
##    print '(isMember) did not find name: %s' % item
##    return False


def generateSubclasses(root, subclassFilename, behaviorFilename,
        prefix, superModule='xxx'):
    name = root.getChildren()[0].getName()
    subclassFile = makeFile(subclassFilename)
    if subclassFile:
        # Read in the XMLBehavior file.
        xmlbehavior = None
        behaviors = None
        baseUrl = None
        if behaviorFilename:
            try:
                # Add the currect working directory to the path so that
                #   we use the user/developers local copy.
                sys.path.insert(0, '.')
                import xmlbehavior_sub as xmlbehavior
            except ImportError:
                print('*** You have requested generation of extended methods.')
                print('*** But, no xmlbehavior module is available.')
                print('*** Generation of extended behavior methods is omitted.')
            if xmlbehavior:
                behaviors = xmlbehavior.parse(behaviorFilename)
                behaviors.make_class_dictionary(cleanupName)
                baseUrl = behaviors.getBase_impl_url()
        wrt = subclassFile.write
        wrt(TEMPLATE_SUBCLASS_HEADER % (time.ctime(), superModule))
        for element in ElementsForSubclasses:
            generateSubclass(subclassFile, element, prefix, xmlbehavior, behaviors, baseUrl)
##        processed = []
##        for element in root.getChildren():
##            name = element.getCleanName()
##            if name not in processed:
##                processed.append(name)
##                generateSubclass(subclassFile, element, prefix, xmlbehavior, behaviors, baseUrl)
##        while 1:
##            if len(DelayedElements_subclass) <= 0:
##                break
##            element = DelayedElements_subclass.pop()
##            name = element.getCleanName()
##            if name not in processed:
##                processed.append(name)
##                generateSubclass(subclassFile, element, prefix, xmlbehavior, behaviors, baseUrl)
        name = root.getChildren()[0].getName()
        elType = cleanupName(root.getChildren()[0].getType())
        if RootElement:
            rootElement = RootElement
        else:
            rootElement = elType
        params = {
            'cap_name': make_gs_name(cleanupName(name)),
            'name': cleanupName(name),
            'module_name': os.path.splitext(os.path.basename(subclassFilename))[0],
            'root': rootElement,
            'super': superModule,
            }
        wrt(TEMPLATE_SUBCLASS_FOOTER % params)
        subclassFile.close()


def generateFromTree(outfile, prefix, elements, processed):
    for element in elements:
        name = element.getCleanName()
        if 1:     # if name not in processed:
            processed.append(name)
            generateClasses(outfile, prefix, element, 0)
            children = element.getChildren()
            if children:
                generateFromTree(outfile, prefix, element.getChildren(), processed)


def generate(outfileName, subclassFilename, behaviorFilename,
        prefix, root, superModule):
    global DelayedElements, DelayedElements_subclass
    # Create an output file.
    # Note that even if the user does not request an output file,
    #   we still need to go through the process of generating classes
    #   because it produces data structures needed during generation of
    #   subclasses.
    outfile = None
    if outfileName:
        outfile = makeFile(outfileName)
    if not outfile:
        outfile = os.tmpfile()
    processed = []
    generateHeader(outfile, prefix)
    DelayedElements = []
    DelayedElements_subclass = []
    elements = root.getChildren()
    generateFromTree(outfile, prefix, elements, processed)
    while 1:
        if len(DelayedElements) <= 0:
            break
        element = DelayedElements.pop()
        name = element.getCleanName()
        if name not in processed:
            processed.append(name)
            generateClasses(outfile, prefix, element, 1)
    #
    # Generate the elements that were postponed because we had not
    #   yet generated their base class.
    while 1:
        if len(PostponedExtensions) <= 0:
            break
        element = PostponedExtensions.pop()
        base = element.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            parentName = parent.getName()
            if (parentName in AlreadyGenerated or
                parentName in SimpleTypeDict.keys()):
                generateClasses(outfile, prefix, element, 1)
            else:
                PostponedExtensions.insert(0, element)
    #
    # Disable the generation of SAX handler/parser.
    # It failed when we stopped putting simple types into ElementDict.
    # When there are duplicate names, the SAX parser probably does
    #   not work anyway.
    generateSAXHndlr(outfile, root)
    generateMain(outfile, prefix, root)
    outfile.close()
    if subclassFilename:
        generateSubclasses(root, subclassFilename, behaviorFilename,
            prefix, superModule)


def makeFile(outFileName):
    global Force
    outFile = None
    if (not Force) and os.path.exists(outFileName):
        reply = raw_input('File %s exists.  Overwrite? (y/n): ' % outFileName)
        if reply == 'y':
            outFile = file(outFileName, 'w')
    else:
        outFile = file(outFileName, 'w')
    return outFile


def mapName(oldName):
    global NameTable
    newName = oldName
    if NameTable:
        if oldName in NameTable:
            newName = NameTable[oldName]
    return newName

def cleanupName(oldName):
    newName = oldName.replace(':', '_')
    newName = newName.replace('-', '_')
    newName = newName.replace('.', '_')
    return newName

def make_gs_name(oldName):
    if UseOldGetterSetter:
        #newName = oldName.capitalize()
        newName = oldName[0].capitalize()
        if len(oldName) > 1:
            newName += oldName[1:]
    else:
        newName = '_%s' % oldName
    return newName

## def mapName(oldName):
##     return '_X_%s' % oldName


def strip_namespace(val):
    return val.split(':')[-1]


def parseAndGenerate(outfileName, subclassFilename, prefix, \
        xschemaFileName, behaviorFilename, superModule='???'):
    global DelayedElements, DelayedElements_subclass, AlreadyGenerated, SaxDelayedElements, \
        AlreadyGenerated_subclass, UserMethodsPath, UserMethodsModule
    DelayedElements = []
    DelayedElements_subclass = []
    AlreadyGenerated = []
    AlreadyGenerated_subclass = []
    if UserMethodsPath:
        UserMethodsModule = __import__(UserMethodsPath)
##    parser = saxexts.make_parser("xml.sax.drivers2.drv_pyexpat")
    parser = make_parser()
##    print 'dir(parser):', dir(parser)
##    print "Parser: %s" % parser
    dh = XschemaHandler()
##    parser.setDocumentHandler(dh)
    parser.setContentHandler(dh)
    if xschemaFileName == '-':
        parser.parse(sys.stdin)
    else:
        parser.parse(xschemaFileName)
    root = dh.getRoot()
    root.annotate()
##    print 'ElementDict:', ElementDict
##    for name, obj in ElementDict.iteritems():
##        print '    ', name, obj.getName(), obj.type
##    print '=' * 50
##    root.show(sys.stdout, 0)
##    print '=' * 50
##    response = raw_input('Press Enter')
##    root.show(sys.stdout, 0)
##    print '=' * 50
##    print ']]] root: ', root, '[[['
    generate(outfileName, subclassFilename, behaviorFilename,
        prefix, root, superModule)



USAGE_TEXT = __doc__

def usage():
    print(USAGE_TEXT)
    sys.exit(-1)


def main():
    global Force, GenerateProperties, SubclassSuffix, RootElement, \
        ValidatorBodiesBasePath, UseOldGetterSetter, \
        UserMethodsPath, XsdNameSpace
    args = sys.argv[1:]
    options, args = getopt.getopt(args, 'hfyo:s:p:a:b:mu:',
        ['help', 'subclass-suffix=', 'root-element=', 'super=',
        'validator-bodies=', 'use-old-getter-setter',
        'user-methods=',
        ])
    prefix = ''
    outFilename = None
    subclassFilename = None
    behaviorFilename = None
    nameSpace = 'xs:'
    superModule = '???'
    for option in options:
        if option[0] == '-h' or option[0] == '--help':
            usage()
        elif option[0] == '-p':
            prefix = option[1]
        elif option[0] == '-o':
            outFilename = option[1]
        elif option[0] == '-s':
            subclassFilename = option[1]
        elif option[0] == '-f':
            Force = 1
        elif option[0] == '-a':
            nameSpace = option[1]
        elif option[0] == '-b':
            behaviorFilename = option[1]
        elif option[0] == '-m':
            GenerateProperties = 1
        elif option[0] == '--subclass-suffix':
            SubclassSuffix = option[1]
        elif option[0] == '--root-element':
            RootElement = option[1]
        elif option[0] == '--super':
            superModule = option[1]
        elif option[0] == '--validator-bodies':
            ValidatorBodiesBasePath = option[1]
        elif option[0] == '--use-old-getter-setter':
            UseOldGetterSetter = 1
        elif option[0] in ('-u', '--user-methods'):
            UserMethodsPath = option[1]
    XsdNameSpace = nameSpace
    set_type_constants(nameSpace)
    if behaviorFilename and not subclassFilename:
        print('\n*** Error.  -b requires -s')
        usage()
    if len(args) != 1:
        usage()
    xschemaFileName = args[0]
    parseAndGenerate(outFilename, subclassFilename, prefix, \
        xschemaFileName, behaviorFilename, superModule=superModule)


if __name__ == '__main__':
    main()
##    import pdb
##    pdb.run('main()')


