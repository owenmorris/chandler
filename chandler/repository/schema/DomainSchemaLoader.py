""" Support SAX2 Parsing of DomainSchema XML format for repository.

    @@@ Known Issues
    + Assumes all elements are in the appropriate namespace, should ignore
      elements from other namespaces.
    + Does not handle default values for our attributes
    + Many datatypes are interpreted as strings, not dealing with
      int or float types.
    + Doesn't deal with DTDs or XSDs.
    + Only treats 'attribute' as a multivalued attribute, treats it as a
      special case
    + Treats otherName/inverseAttribute as a special case

"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax
import xml.sax.handler

from model.item.Item import Item
from model.schema.Kind import Kind
from model.schema.Attribute import Attribute
from model.schema import Types


# XML format tag is the key, Repository expected kind is the value

ITEM_TAGS = {'Kind' : 'Kind',
             'Attribute' : 'Attribute',
             'Alias': 'Alias',
             'Type' : 'Type'}

# XML format tag is the key, Repository expected attribute is the value

ATTRIBUTE_TEXT_TAGS = {'displayName': 'displayName',
                       'description': 'description',
                       'version' : 'version',
                       'defaultValue' : 'defaultValue',
                       'cardinality': 'cardinality',
                       'referencePolicy': 'referencePolicy'}

ATTRIBUTES_TEXT_TAGS = {'examples': 'examples',
                        'issues' : 'issues'}

ATTRIBUTE_REF_TAGS = {'superAttribute': 'superAttribute',
                      'type': 'type',
                      'inverseAttribute':'otherName',
                      'displayAttribute':'displayAttribute',
                      'inheritFrom' : 'inheritFrom'}

ATTRIBUTES_REF_TAGS = {'superKinds' : 'superKinds',
                       'attributes': 'attributes',
                       'equivalentKinds':'equivalentKinds',
                       'equivalentAttributes':'equivalentAttributes',
                       'aliasFor':'aliasFor'}

ATTRIBUTE_BOOL_TAGS = {'hidden' : 'hidden',
                       'abstract' : 'abstract',
                       'unidirectional' : 'unidirectional',
                       'required' : 'required'}

NAME_REF_TAGS = ['inverseAttribute', 'displayAttribute']

BOOTSTRAP_IGNORE = ['DaylightSavingTimezone', 'FixedTimezone', 'EnumKind', 'Item']

BOOTSTRAP = {'Boolean' : '//Schema/Model/Types/Boolean',
             'Number' : '//Schema/Model/Types/Integer',
             'SimpleString' : '//Schema/Model/Types/String',
             'PolyglotText' : '//Schema/Model/Types/String',
             'RigidDatetime' : '//Schema/Model/Types/DateTime',
             'RelationshipTypeEnum' : '//Schema/Model/Types/String',
             'RepositoryContainmentPath' : '//Schema/Model/Types/String',
             'Anything' : '//Schema/Model/Types/String'}

class DomainSchemaLoader(object):
    """ Load items defined in the schema file into the repository,
        using a SAX2 parser.
    """

    def __init__(self, repository, verbose=False):
        self.repository = repository
        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 1)
        self.parser.setContentHandler(DomainSchemaHandler(self.repository, verbose))
        self.parser.setErrorHandler(xml.sax.handler.ErrorHandler())
        
    def load(self, file, parent=None):
        self.parser.parse(file)

class DomainSchemaHandler(xml.sax.ContentHandler):
    """A SAX ContentHandler responsible for loading DomainSchemas.
    """

    def __init__(self, repository, verbose=False):

        self.repository = repository
        self.verbose = verbose

    def startDocument(self):

        # Keep a stack of tags, to know where we are during processing
        self.tags = []

        # Keep track of the prefix/path mappings, to be used when
        # creating references to other items.
        self.mapping = {}

        self.bootstrap = False

        self.parent = self.repository.find("//Schema")

        # save a list of items and attributes, wire them up later
        # to be able to handle forward references
        self.todo = []

    def endDocument(self):
        for (item, attributes) in self.todo:
            self.addAttributes(item, attributes)
    
    def characters(self, content):

        # Look up the current tag, to know the context
        currentTag = self.tags[-1]

        # Add the text as the value of the current attribute
        if (currentTag in ATTRIBUTE_TEXT_TAGS):
            self.currentAttributes[currentTag] = content
        elif (currentTag in ATTRIBUTES_TEXT_TAGS):
            if not self.currentAttributes.has_key(currentTag):
                self.currentAttributes[currentTag] = []
            self.currentAttributes[currentTag].append(content)


    def startElementNS(self, (uri, local), qname, attrs):

        # Add the tag to our stack
        self.tags.append(local)

        # Create the domainSchema item now
        if local == 'DomainSchema':
            self.schemaAttributes = {}
            self.currentAttributes = self.schemaAttributes
            
            idString = attrs.getValue((None, 'itemName'))
            rootName = attrs.getValue((None, 'root'))
            bootstrap = attrs.get((None, 'bootstrap'), 'False')
            self.bootstrap = (bootstrap == 'True')
            self.domainSchema = self.createDomainSchema(idString, rootName)

        # Create the item
        elif local in ITEM_TAGS:
            self.currentAttributes = {}
            idString = attrs.getValue((None, 'itemName'))
            [prefix, name] = idString.split(':')

            bootstrap = attrs.get((None, 'bootstrap'), "False")
            if bootstrap == 'True':
                if local == 'Attribute':
                    BOOTSTRAP[name] = '//Schema/Model/Attributes/' + name
                elif local == 'Kind':
                    BOOTSTRAP[name] = '//Schema/Model/' + name
                elif local == 'Type' or local == 'Alias':
                    BOOTSTRAP[name] = '//Schema/Model/Types/' + name
                if self.verbose:
                    print "Already loaded boostrap: %s" % idString

            elif local == 'Kind':
                self.currentItem = self.createKind(prefix, name)
            elif local == 'Attribute':
                self.currentItem = self.createAttribute(prefix, name)
            else:
                self.currentItem = None

        # Ignore the odd item
        elif local in BOOTSTRAP_IGNORE:
            self.currentAttributes = {}
            self.currentItem = None

        # Add an attribute to the current item
        elif local in ATTRIBUTE_REF_TAGS:
            refValue = attrs.getValue((None, 'itemref'))
            self.currentAttributes[local] = refValue
        elif local in ATTRIBUTES_REF_TAGS:
            refValue = attrs.getValue((None, 'itemref'))
            if not self.currentAttributes.has_key(local):
                self.currentAttributes[local] = []
            self.currentAttributes[local].append(refValue)
        elif local in ATTRIBUTE_BOOL_TAGS:
            self.currentAttributes[local] = True

        # Create a mapping from a prefix to the repository path
        elif local == 'itemPathMapping':
            prefix = attrs.getValue((None, 'prefix'))
            path = attrs.getValue((None, 'path'))
            self.mapping[prefix] = path

    def endElementNS(self, (uri, local), qname):

        # Create the item in the repository
        if (local in ITEM_TAGS):
            if self.currentItem:
                self.todo.append((self.currentItem, self.currentAttributes))
            self.currentAttributes = self.schemaAttributes
            self.currentItem = None

        elif (local in BOOTSTRAP_IGNORE):
            self.currentItem = None
            self.currentAttributes = self.schemaAttributes

        elif local == 'DomainSchema':
            self.addAttributes(self.domainSchema, self.currentAttributes)

        # Remove the tag from the stack
        self.tags.pop()

    def findItem(self, reference):
        """Given a reference with a namespace prefix,
           find the item in the repository. Look up the prefix
           using the mapping defined by the itemPathMapping tag.
        """
        [prefix, local] = reference.split(':')

        if self.bootstrap and (local in BOOTSTRAP):
            path = BOOTSTRAP[local]
        else:
            path = self.mapping[prefix] + local
        item = self.repository.find(path)

        # Warning
        if item == None:
            print "Warning while parsing %s: reference (%s) with path (%s) was not found" % (self.domainSchemaName, reference, path)

        return item

    def createDomainSchema(self, idString, rootName):
        """Create a DomainSchema with the given id."""
        [prefix, name] = idString.split(':')
        kind = self.repository.find('//Schema/Model/Item')

        self.domainSchemaName = name

        if self.bootstrap:
            parent = self.repository.find('//Schema/Model')
            item = Item('Proposed', parent, kind)
        else:
            item = Item(name, self.parent, kind)

        self.root = Item(rootName, self.repository, kind)

        return item

    def createKind(self, prefix, name):
        """Create a Kind item with the given id."""
        kind = self.repository.find('//Schema/Model/Kind')
        if self.verbose:
            print "Creating Kind: (%s, %s)" % (self.domainSchema.getItemPath(), name)
        item = Kind(name, self.domainSchema, kind)
        return item

    def createAttribute(self, prefix, name):
        """Create an Attribute item with the given id."""
        kind = self.repository.find('//Schema/Model/Attribute')
        if self.verbose:
            print "Creating Attribute: (%s, %s)" % (self.domainSchema.getItemPath(), name)
        item = Attribute(name, self.domainSchema, kind)
        return item

    def createItem(self, prefix, name):
        """Create a generic item, for types, aliases, etc."""
        kind = self.repository.find('//Schema/Model/Item')
        item = Item(name, self.domainSchema, kind)
        return item

    def createAlias(self, idString):
        """Create an Alias item with the given id."""
        # @@@ not yet implemented
        pass

    def createType(self, idString):
        """Create a Type item with the given id."""
        # @@@ not yet implemented
        pass

    def addAttributes(self, item, attributeDictionary):
        """Add the attributes in attributeDictionary to the given item.
        """

        for key in attributeDictionary.keys():

            # Special cases first

            # Store class mapping in a dictionary
            if key == 'classes':
                value = attributeDictionary[key]
                item.setValue('classes', value, 'python')

            # Special case for tags that currently give an item
            # reference, but we need the name of the item
            elif key in NAME_REF_TAGS:
                ref = self.findItem(attributeDictionary[key])
                item.setAttributeValue(ATTRIBUTE_REF_TAGS[key],
                                       ref.getItemName())

            # For references, find the item to set the attribute
            elif key in ATTRIBUTE_REF_TAGS:
                ref = self.findItem(attributeDictionary[key])
                item.setAttributeValue(ATTRIBUTE_REF_TAGS[key], ref)

            # Multivalued references
            elif key in ATTRIBUTES_REF_TAGS:
                for attr in attributeDictionary[key]:
                    ref = self.findItem(attr)
                    item.attach(ATTRIBUTES_REF_TAGS[key], ref)
                                        
            # Text, look up attribute in the dictionary
            elif (key in ATTRIBUTE_TEXT_TAGS):
                value = attributeDictionary[key]
                item.setAttributeValue(ATTRIBUTE_TEXT_TAGS[key], value)
                
            # Multivalued text, look up attribute in the dictionary
            elif (key in ATTRIBUTES_TEXT_TAGS):
                value = attributeDictionary[key]
                item.setAttributeValue(ATTRIBUTES_TEXT_TAGS[key], value)

            # Booleans, look up the value in the dictionary
            elif key in ATTRIBUTE_BOOL_TAGS:
                value = attributeDictionary[key]
                item.setAttributeValue(ATTRIBUTE_BOOL_TAGS[key], value)


