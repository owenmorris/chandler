""" Support SAX2 parsing of XML format for repository items

    @@@ Known Issues (most require resolving data model and repository issues)
    (1) Special case for the 'root' element, aka where do we put odd items?
    (2) Special case for 'Domain' items, creating a 'FlatDomain' class
    (3) Special case for inverseAttribute and displayAttribute
    (4) Plumbing is available for better error handling, not all there yet
    (5) Types not all handled (assumes strings)
    (6) Special case for classes attribute, to load a python class
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
from model.schema.Namespace import Domain
import model.schema.Types

class ItemLoader(object):
    """ Load items defined in the XML file into the repository,
        using a SAX2 parser.
    """

    def __init__(self, repository, verbose=False):
        self.repository = repository
        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, True)
        self.parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        self.parser.setContentHandler(ItemHandler(self.repository,
                                                  verbose))
        self.parser.setErrorHandler(xml.sax.handler.ErrorHandler())

    def load(self, file, parent=None):
        self.parser.parse(file)

class ItemHandler(xml.sax.ContentHandler):
    """ A SAX2 ContentHandler responsible for loading items into a
        repository namespace.
    """

    def __init__(self, repository, verbose=False):
        self.repository = repository
        self.verbose = verbose

    def setDocumentLocator(self, locator):
        """SAX2 callback to set the locator, useful for error handling"""
        self.locator = locator

    def startDocument(self):
        """SAX2 callback at the start of the document"""

        # Keep a stack of tags, to know where we are during processing
        self.tags = []

        # Keep track of namespace prefixes
        self.mapping = {}

        # Save a list of items and attributes, wire them up later
        # to be able to handle forward references
        self.todo = []

    def endDocument(self):
        """SAX2 callback at the end of the document"""

        # Wire up items and attributes after parsing everything
        for (item, attributes) in self.todo:
            self.addReferences(item, attributes)

    def characters(self, content):
        """SAX2 callback for character content within the tag"""

        (uri, local, element) = self.tags[-1]

        if element == 'Attribute' or element == 'Dictionary':
            self.currentValue = self.currentValue + content

    def startElementNS(self, (uri, local), qname, attrs):

        if attrs.has_key((None, 'itemName')):
            # If it has an item name, its an item
            element = 'Item'

            nameString = attrs.getValue((None, 'itemName'))
            self.currentItem = self.createItem(uri, local, nameString)
            self.currentAttributes = []

        elif attrs.has_key((None, 'itemref')):
            # If it has an itemref, assume its a reference attribute
            element = 'Reference'
            self.currentValue = attrs.getValue((None, 'itemref'))
            
        elif attrs.has_key((None, 'key')):
            # If it has a key, assume its a dictionary of literals
            element = 'Dictionary'
            self.currentKey = attrs.getValue((None, 'key'))
            self.currentValue = ''
            
        else:
            # Otherwise, assume its a literal attribute
            element = 'Attribute'
            self.currentValue = ''

        # Add the tag to our context stack
        self.tags.append((uri, local, element))


    def endElementNS(self, (uri, local), qname):
        (uri, local, element) = self.tags[-1]

        # If we have a reference, delay loading
        if element == 'Reference':
            self.currentAttributes.append((local,
                                           self.currentValue,
                                           self.locator.getLineNumber()))

        # We have an attribute, append to the current item
        elif element == 'Attribute':

            # If the element is empty, treat the value as a boolean
            if self.currentValue == '':
                self.currentItem.addValue(local, True)

            # Otherwise, add the value as a string
            else:
                self.currentItem.addValue(local, self.currentValue)

        # We have a dictionary
        elif element == 'Dictionary':

            # @@@ (6) Special case, we know we're loading a class
            if local == 'classes':
                self.currentValue = Item.loadClass(self.currentValue)
                
            self.currentItem.setValue(local,
                                      self.currentValue,
                                      self.currentKey)
            
        # We have an item, add the collected attributes to the list
        elif element == 'Item':
            if self.currentItem:
                self.todo.append((self.currentItem, self.currentAttributes))
                self.currentItem = None
                self.currentAttributes = None
            
        self.tags.pop()

    def startPrefixMapping(self, prefix, uri):
        """ SAX2 callback for namespace prefixes """

        # Save the prefix mapping, for use by itemref attributes
        self.mapping[prefix] = uri

    def endPrefixMapping(self, prefix):
        """ SAX2 callback for namespace prefixes """
        # self.mapping[prefix] = None

    def findItem(self, namespace, name):
        """ Find the item with the namespace indicated by prefix,
            and with the given name.
        """

        # @@@ (4) error condition if namespace is not found
        # @@@ (4) error condition if item is not found
        path = "%s/%s" % (namespace, name)
        item = self.repository.find(path)

        if item == None:
            print "Item not found: %s, %s" % (path,
                                              self.locator.getLineNumber())

        return item

    def createItem(self, uri, local, nameString):

        # Find the item represented by the tag, schema information
        schemaItem = self.findItem(uri, local)

        (prefix, name) = nameString.split(':') 
        namespace = self.mapping[prefix]

        # @@@ (1) Hack for the root
        if namespace == '//':
            parent = self.repository
        else:
            parent = self.repository.find(namespace)

        # @@@ (2) Hack for Domain
        if local == 'Domain':
            item = FlatDomain(name, parent, schemaItem)
        else:
            item = schemaItem.newItem(name, parent)

        return item

    def addReferences(self, item, attributes):
        """ Add all of the references in the list to the item """
        for (attributeName, value, line) in attributes:

            (prefix, name) = value.split(':')

            namespace = self.mapping[prefix]
            reference = self.findItem(namespace, name)

            # @@@ (3) Special cases to resolve
            if attributeName == 'inverseAttribute':
                item.addValue('otherName', reference.getItemName())
            elif attributeName == 'displayAttribute':
                item.addValue('displayAttribute', reference.getItemName())
            else:
                item.addValue(attributeName, reference)

class FlatDomain(Domain):
    def getNamespace(self, name):
        return self
            
    
