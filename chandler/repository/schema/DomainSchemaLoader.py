""" Support SAX2 Parsing of DomainSchema XML format for repository.

    @@@ Known Issues
    + Assumes all elements are in the appropriate namespace, should ignore
      elements from other namespaces.
    + Does not handle default values for our attributes
    + Many datatypes are interpreted as strings, not dealing with
      int or float types.
    + Doesn't deal with DTDs or XSDs.

"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax
import xml.sax.handler

from model.schema.Kind import Kind
from model.schema.AttrDef import AttrDef
from model.schema import Types

from model.item.Item import Item

# XML format tag is the key, Repository expected kind is the value

ITEM_TAGS = {'Kind' : 'Kind',
             'AttributeDefinition' : 'AttrDef',
             'Alias': 'Alias',
             'Type' : 'Type'}


# XML format tag is the key, Repository expected attribute is the value

ATTRIBUTE_TEXT_TAGS = {'label': 'DisplayName',
                       'comment': 'comment',
                       'example': 'example',
                       'issue' : 'issue',
                       'version' : 'version',
                       'default' : 'Default',
                       'derivation' : 'derivation',
                       'cardinality': 'Cardinality',
                       'relationshipType': 'relationshipType',
                       'pythonClass' : 'Class'}

ATTRIBUTE_REF_TAGS = {'superKind' : 'SuperKind',
                      'superAttribute': 'SuperAttrDef',
                      'attribute': 'AttrDefs',
                      'type': 'Type',
                      'displayAttribute':'displayAttribute',
                      'equivalentKind':'equivalentKind',
                      'equivalentAttribute':'equivalentAttribute',
                      'inverseAttribute':'OtherName',
                      'aliasFor':'aliasFor'}

ATTRIBUTE_BOOL_TAGS = {'hidden' : 'hidden',
                       'abstract' : 'abstract',
                       'unidirectional' : 'unidirectional',
                       'required' : 'Required'}

class DomainSchemaLoader(object):
    """ Load items defined in the schema file into the repository,
        using a SAX2 parser.
    """

    def __init__(self, repository):
        self.repository = repository
        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 1)
        self.parser.setContentHandler(DomainSchemaHandler(self.repository))
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
        if currentTag in ATTRIBUTE_TEXT_TAGS:
            self.currentAttributes[currentTag] = content

    def startElementNS(self, (uri, local), qname, attrs):

        # Add the tag to our stack
        self.tags.append(local)

        # Create the domainSchema item now
        if local == 'DomainSchema':
            self.schemaAttributes = {}
            self.currentAttributes = self.schemaAttributes
            
            idString = attrs.getValue((None, 'id'))
            rootName = attrs.getValue((None, 'root'))
            self.domainSchema = self.createDomainSchema(idString, rootName)

        # Create the item
        if local in ITEM_TAGS:
            self.currentAttributes = {}
            self.currentAttributes['attribute'] = []
            idString = attrs.getValue((None, 'id'))
            if local == 'Kind':
                self.currentItem = self.createKind(idString)
            elif local == 'AttributeDefinition':
                self.currentItem = self.createAttributeDefinition(idString)

        # Add an attribute to the current item
        elif local in ATTRIBUTE_REF_TAGS:
            refValue = attrs.getValue((None, 'itemref'))
            if local == 'attribute':
                self.currentAttributes[local].append(refValue)
            else:
                self.currentAttributes[local] = refValue
        elif local in ATTRIBUTE_BOOL_TAGS:
            self.currentAttributes[local] = True

        # Create a mapping from a prefix to the repository path
        if local == 'containmentPath':
            prefix = attrs.getValue((None, 'prefix'))
            path = attrs.getValue((None, 'path'))
            self.mapping[prefix] = path

    def endElementNS(self, (uri, local), qname):

        # Create the item in the repository
        if local in ITEM_TAGS:
            # self.addAttributes(self.currentItem, self.currentAttributes)
            self.todo.append((self.currentItem, self.currentAttributes))
            self.currentAttributes = self.schemaAttributes
            self.currentItem = None

        if local == 'DomainSchema':
            self.addAttributes(self.domainSchema, self.currentAttributes)

        # Remove the tag from the stack
        self.tags.pop()

    def findItem(self, reference):
        """Given a reference with a namespace prefix,
           find the item in the repository. Look up the prefix
           using the mapping defined by the containmentPath tag.
        """
        [prefix, local] = reference.split(':')
        path = self.mapping[prefix] + local
        item = self.repository.find(path)
        return item

    def createDomainSchema(self, idString, rootName):
        """Create a DomainSchema with the given id."""
        [prefix, name] = idString.split(':')
        kind = self.repository.find('//Schema/Model/Item')
        item = Item(name, self.parent, kind)
        root = Item(rootName, self.repository, kind)
        return item

    def createKind(self, idString):
        """Create a Kind item with the given id."""
        [prefix, name] = idString.split(':')
        kind = self.repository.find('//Schema/Model/Kind')
        item = Kind(name, self.domainSchema, kind)
        return item

    def createAttributeDefinition(self, idString):
        """Create an AttributeDefinition item with the given id."""
        [prefix, name] = idString.split(':')
        kind = self.repository.find('//Schema/Model/AttrDef')
        item = AttrDef(name, self.domainSchema, kind)
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

            # For references, find the item to set the attribute
            if key in ATTRIBUTE_REF_TAGS:

                # Special case for 'attribute', our only multivalued attribute
                if key == 'attribute':
                    for attr in attributeDictionary[key]:
                        ref = self.findItem(attr)
                        item.attach(ATTRIBUTE_REF_TAGS[key], ref)

                # Special case for 'OtherName'
                elif key == 'inverseAttribute':
                    ref = self.findItem(attributeDictionary[key])
                    item.setAttribute(ATTRIBUTE_REF_TAGS[key], ref.getName())
                                        
                else:
                    ref = self.findItem(attributeDictionary[key])
                    item.setAttribute(ATTRIBUTE_REF_TAGS[key], ref)
                    
            # For booleans or text, look up the value in the dictionary
            elif key in ATTRIBUTE_TEXT_TAGS:
                value = attributeDictionary[key]
                item.setAttribute(ATTRIBUTE_TEXT_TAGS[key], value)
            elif key in ATTRIBUTE_BOOL_TAGS:
                value = attributeDictionary[key]
                item.setAttribute(ATTRIBUTE_BOOL_TAGS[key], value)


