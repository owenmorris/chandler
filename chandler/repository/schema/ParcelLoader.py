""" Support SAX2 parsing of XML format for repository items

    @@@ Known Issues (most require resolving data model and repository issues)
    (1) Special case for attributes (set the alias)
    (2) Special case for inverseAttribute and displayAttribute
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax
import xml.sax.handler

from repository.item.Item import Item
from repository.schema.Kind import Kind
from repository.schema.Attribute import Attribute
from repository.schema.Parcel import Parcel
import repository.schema.Types

class ParcelLoader(object):
    """ Load items defined in the XML file into the repository,
        using a SAX2 parser.
    """

    def __init__(self, repository, callback, callbackArg):
        self.repository = repository
        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, True)
        self.parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        self.parser.setContentHandler(ItemHandler(self.repository,
                                                  callback, callbackArg))

    def load(self, file, uri):
        contentHandler = self.parser.getContentHandler()
        contentHandler.uri = uri

        self.parser.parse(file)


class ItemHandler(xml.sax.ContentHandler):
    """ A SAX2 ContentHandler responsible for loading items into a
        repository namespace.
    """

    def __init__(self, repository, callback, callbackArg):
        self.repository = repository
        self.callback = callback
        self.callbackArg = callbackArg

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
        self.delayedReferences = []

        self.currentItem = None

        # Get the parcel's parent
        parentUri = self.uri[:self.uri.rfind('/')]
        self.parcelParent = self.repository.find(parentUri)
        assert parentUri, "Parcel parent has not been loaded."

    def endDocument(self):
        """SAX2 callback at the end of the document"""

        # We've delayed loading the references until the end of the file.
        # Wire up attribute/reference pairs to the items.
        for (item, attributes) in self.delayedReferences:
            self.addReferences(item, attributes)

    def characters(self, content):
        """SAX2 callback for character content within the tag"""

        (uri, local, element, item, references) = self.tags[-1]

        if element == 'Attribute' or element == 'Dictionary':
            self.currentValue += content

    def startElementNS(self, (uri, local), qname, attrs):
        """SAX2 callback for the beginning of a tag"""

        if attrs.has_key((None, 'itemName')):
            # If it has an item name, its an item
            element = 'Item'
            
            nameString = attrs.getValue((None, 'itemName'))
            if attrs.has_key((None, 'itemClass')):
                classString = attrs.getValue((None, 'itemClass'))
            else:
                classString = None
            self.currentItem = self.createItem(uri, local,
                                               nameString, classString)
            self.currentReferences = []
            
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
        self.tags.append((uri, local, element,
                          self.currentItem, self.currentReferences))


    def endElementNS(self, (uri, local), qname):
        """SAX2 callback for the end of a tag"""
        
        (uri, local, element, currentItem, currentReferences) = self.tags[-1]

        # If we have a reference, delay loading
        if element == 'Reference':
            (namespace, name) = self.getNamespaceName(self.currentValue)
            
            self.currentReferences.append((local, namespace, name,
                                           self.locator.getLineNumber()))
            
        # We have an attribute, append to the current item
        elif element == 'Attribute':

            value = self.makeValue(uri, local)
            self.currentItem.addValue(local, value)
                
        # We have a dictionary, similar to attribute, but we have a key
        elif element == 'Dictionary':

            value = self.makeValue(uri, local)
            self.currentItem.setValue(local, value, self.currentKey)
            
        # We have an item, add the collected attributes to the list
        elif element == 'Item':
            self.delayedReferences.append((self.currentItem,
                                           self.currentReferences))
            
            # Look at the tags stack for the parent item, and the
            # parent references
            if len(self.tags) >= 2:
                self.currentItem = self.tags[-2][3]
                self.currentReferences = self.tags[-2][4]
            
        self.tags.pop()

    def startPrefixMapping(self, prefix, uri):
        """ SAX2 callback for namespace prefixes """

        # If we define a prefix mapping, it means we depend on
        # the parcel. Load the uri, if it does not match the uri
        # for this file.
        if uri != self.uri:
            self.callback(self.repository, uri, self.callbackArg)

        # Save the prefix mapping, for use by itemref attributes
        self.mapping[prefix] = uri

    def endPrefixMapping(self, prefix):
        """ SAX2 callback for namespace prefixes """
        self.mapping[prefix] = None

    def makeValue(self, uri, local):
        """ Creates a value from a string, based on the type
            of the attribute.
        """
        assert self.currentItem, \
               "No parent item at %s:%s" % (self.locator.getSystemId(),
                                            self.locator.getLineNumber())

        kindItem = self.currentItem.kind
        attributeItem = kindItem.getAttribute(local)

        assert attributeItem, \
               "Attribute not found at %s:%s" % (self.locator.getSystemId(),
                                                 self.locator.getLineNumber())
        
        value = attributeItem.type.makeValue(self.currentValue)
        return value

    def findItem(self, namespace, name, line):
        """ Find the item with the namespace indicated by prefix,
            and with the given name.
        """

        path = "%s/%s" % (namespace, name)
        item = self.repository.find(path)

        assert item, \
               "No item (%s) at %s:%s" % (path,
                                          self.locator.getSystemId(),
                                          line)
        return item

    def getNamespaceName(self, nameString):
        """ Given a nameString, parse out the namespace prefix and look
            it up in the dictionary of namespace mappings.
            'core:String' => ('//Schema/Core', String)

            If there's no prefix, use the default namespace set by xmlns=
            'String' => ('//Schema/Core', String)
        """
        
        hasPrefix = nameString.count(':')

        assert (0 <= hasPrefix <= 1), \
               "Bad itemref: %s at %s:%s" % (nameString,
                                             self.locator.getSystemId(),
                                             self.locator.getLineNumber())
        
        # If there's no prefix, then use the default set by xmlns=
        if hasPrefix == 0:
            prefix = None
            name = nameString
        else:
            (prefix, name) = nameString.split(':')
            
        namespace = self.mapping.get(prefix, None)

        assert namespace, \
               "No namespace: %s at %s:%s" % (prefix,
                                              self.locator.getSystemId(),
                                              self.locator.getLineNumber())
        
        return (namespace, name)

    def createItem(self, uri, local, name, className):
        """ Create a new item, with the kind defined by the tag.
            The new item's namespace is derived from nameString.
            The new item's kind is derived from (uri, local).
        """

        # If we have the document root, use the parcel parent.
        # Otherwise, the currentItem is the parent.
        if len(self.tags) > 0:
            parent = self.currentItem
        else:
            parent = self.parcelParent

        # Find the kind represented by the tag (uri, local). The
        # parser has already mapped the prefix to the namespace (uri).
        kind = self.findItem(uri, local,
                             self.locator.getLineNumber())
            
        assert kind, \
               "No kind (%s/%s) at %s:%s" % (uri, local,
                                             self.locator.getSystemId(),
                                             self.locator.getLineNumber())

        if className:
            # Use the given class to instantiate the item
            cls = Item.loadClass(className)
            item = cls(name, parent, kind)
        else:
            # The kind knows how to instantiate an instance of the item
            item = kind.newItem(name, parent)

        assert item, \
               "Item not created at %s:%s" % (self.locator.getSystemId(),
                                              self.locator.getLineNumber())

        return item

    def addReferences(self, item, attributes):
        """ Add all of the references in the list to the item """

        for (attributeName, namespace, name, line) in attributes:
            reference = self.findItem(namespace, name, line)
            
            # @@@ Special cases to resolve
            if attributeName == 'inverseAttribute':
                item.addValue('otherName', reference.getItemName())
            elif attributeName == 'displayAttribute':
                item.addValue('displayAttribute', reference.getItemName())
            elif attributeName == 'attributes':
                item.addValue('attributes', reference,
                              alias=reference.getItemName())
            else:
                item.addValue(attributeName, reference)

        
        
