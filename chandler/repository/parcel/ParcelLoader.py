""" Support SAX2 parsing of XML format for repository items

    @@@ Known Issues (most require resolving data model and repository issues)
    (1) Special case for attributes (set the alias)
    (2) Special case for inverseAttribute and displayAttribute
    (3) Empty list, None types not handled properly
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax
import xml.sax.handler
import logging

from repository.parcel.Util import PrintItem
from repository.parcel.Parcel import Parcel
from repository.util.ClassLoader import ClassLoader
from repository.util.Path import Path


class ParcelLoader(object):
    """ Load items defined in the XML file into the repository,
        using a SAX2 parser.
    """

    def __init__(self, repository, callback, callbackArg):
        self.repository = repository
        self.callback = callback
        self.callbackArg = callbackArg
        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, True)
        self.parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        self.parser.setContentHandler(ItemHandler(self.repository,
                                                  callback, callbackArg))

    def load(self, file, uri):
        # Before loading a parcel, load its parent
        parentUri = uri[:uri.rfind('/')]
        parcelParent = self.repository.findPath(parentUri)
        if not parcelParent:
            self.callback(self.repository, parentUri, self.callbackArg)

        if self.repository.findPath(uri):
            # this parcel is already loaded
            return

        contentHandler = self.parser.getContentHandler()
        contentHandler.uri = uri

        self.parser.parse(file)


class ItemHandler(xml.sax.ContentHandler):
    """ A SAX2 ContentHandler responsible for loading items into a
        repository namespace.
    """
    _DELAYED_REFERENCE = 0
    _DELAYED_LITERAL   = 1

    def __init__(self, repository, callback, callbackArg):
        self.repository = repository
        self.callback = callback
        self.callbackArg = callbackArg
        self.log = logging.getLogger('repository.schema')

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
        self.parcelParent = self.repository.findPath(parentUri)
        assert self.parcelParent, "Parcel parent has not been loaded."

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
            if attrs.has_key((None, 'type')):
                # Store the full path to the type item
                self.currentType = "%s/%s" % self.getNamespaceName(
                 attrs.getValue((None, 'type')))
            else:
                self.currentType = None
            self.currentValue = ''
            
        else:
            # Otherwise, assume its a literal attribute
            element = 'Attribute'
            if attrs.has_key((None, 'type')):
                # Store the full path to the type item
                self.currentType = "%s/%s" % self.getNamespaceName(
                 attrs.getValue((None, 'type')))
            else:
                self.currentType = None
            self.currentValue = ''
            
        # Add the tag to our context stack
        self.tags.append((uri, local, element,
                          self.currentItem, self.currentReferences))

    def endElementNS(self, (uri, local), qname):
        """SAX2 callback for the end of a tag"""
        elementUri = uri
        elementLocal = local
        
        (uri, local, element, currentItem, currentReferences) = self.tags[-1]

        # Is the current item part of the core schema?
        isSchemaItem = (currentItem.itsKind.itsRoot.itsName == 'Schema')

        # If we have a reference, delay loading
        if element == 'Reference':
            (namespace, name) = self.getNamespaceName(self.currentValue)
            self.currentReferences.append((self._DELAYED_REFERENCE, local,
             namespace, name, None, self.locator.getLineNumber()))
            
        # If we have a literal attribute, but delay assignment until the 
        # end of the document because superKinds are not yet linked up and 
        # therefore attribute assignments could fail.
        elif element == 'Attribute':
            if isSchemaItem:
                if elementLocal == "defaultValue" or \
                   elementLocal == "initialValue":
                    # The type and cardinality of the default value we're going
                    # to make should be that of the attribute so that the
                    # parcel author doesn't have to re-specify the type here.
                    # However, the attribute's type may not have been hooked up
                    # yet, so for now we need the type specified in the
                    # initialValue/defaultValue element. 
                    # TODO:  Delay this addValue until after we've had a chance
                    # to hook up the attribute's type.
                    if currentItem.cardinality == "single":
                        value = self.makeValue(currentItem, elementLocal, self.currentType, self.currentValue, self.locator.getLineNumber())
                        currentItem.addValue(elementLocal, value)
                    elif currentItem.cardinality == "dict":
                        currentItem.addValue(elementLocal, {})
                    else:
                        # Cardinality is list
                        # For the moment ignore any value/type and set to empty
                        # list.
                        # TODO: support assignment of a non-empty list to
                        # initialValue?
                        currentItem.addValue(elementLocal, [])
                else:
                    value = self.makeValue(currentItem, elementLocal, self.currentType, self.currentValue, self.locator.getLineNumber())
                    currentItem.addValue(elementLocal, value)
            else: # Delay
                self.currentReferences.append((self._DELAYED_LITERAL, local,
                 self.currentType, self.currentValue, None, self.locator.getLineNumber()))
                
        # We have a dictionary, similar to attribute, but we have a key
        elif element == 'Dictionary':
            if isSchemaItem:
                value = self.makeValue(currentItem, elementLocal, self.currentType, self.currentValue, self.locator.getLineNumber())
                currentItem.setValue(elementLocal, value, self.currentKey)
            else: # Delay
                self.currentReferences.append((self._DELAYED_LITERAL, local,
                 self.currentType, self.currentValue, self.currentKey, self.locator.getLineNumber()))

            
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

        # Save the prefix mapping, for use by itemref attributes,
        # and also used to determine which dependent parcels to load
        # later on.
        self.mapping[prefix] = uri

    def endPrefixMapping(self, prefix):
        """ SAX2 callback for namespace prefixes """

        # If we define a prefix mapping, it means we depend on
        # the parcel. Load the uri, if it does not match the uri
        # for this file.
        uri = self.mapping[prefix]
        if uri != self.uri:
            self.callback(self.repository, uri, self.callbackArg)

        self.mapping[prefix] = None


    def makeValue(self, item, attributeName, attributeTypePath, value, line):
        """ Creates a value from a string, based on the type
            of the attribute.
        """
        if attributeTypePath:
            attributeType = self.repository.findPath(attributeTypePath)
            value = attributeType.makeValue(value)
        else:
            assert item, \
                   "No parent item at %s:%s" % (self.locator.getSystemId(),
                                               line)

            kindItem = item.itsKind
            attributeItem = kindItem.getAttribute(attributeName)

            assert attributeItem, \
                   "No Attribute %s at %s:%s" % (attributeName,
                                                 self.locator.getSystemId(),
                                              line)
        
            value = attributeItem.type.makeValue(value)

        return value

    def findItem(self, namespace, name, line):
        """ Find the item with the namespace indicated by prefix,
            and with the given name.  If it isn't yet in the repository
            the try loading the parcel it's supposed to be in.
        """

        path = Path(namespace, name)
        item = self.repository.find(path)

        # If the item doesn't yet exist, load the parcel it's supposed
        # to be in and try again
        if not item:
            self.callback(self.repository, namespace, self.callbackArg)
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

        # If the item already exists, use the existing item
        item = parent.getItemChild(name)
        if item:
            self.log.debug("Reloading item %s" % item.itsPath) 
            return item

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
            cls = ClassLoader.loadClass(className)
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

        for (type, attributeName, namespace, name, key, line) in attributes:

            if type == self._DELAYED_REFERENCE:
                if namespace == "//Schema/Core" and name == "None":
                    reference = None
                else:
                    reference = self.findItem(namespace, name, line)

                # @@@ Special cases to resolve
                if attributeName == 'inverseAttribute':
                    item.addValue('otherName', reference.itsName)
                elif attributeName == 'displayAttribute':
                    item.addValue('displayAttribute', reference.itsName)
                elif attributeName == 'attributes':
                    item.addValue('attributes', reference,
                                  alias=reference.itsName)
                else:
                    item.addValue(attributeName, reference)

            elif type == self._DELAYED_LITERAL:

                # In the case of a literal, "namespace" specifies the path
                # of the type item, and "name" contains the value.  If "key"
                # is not None then use is as a dict key.

                attributeTypePath = namespace


                value = self.makeValue(item, attributeName, attributeTypePath,
                 name, line)
                if key:
                    item.setValue(attributeName, value, key)
                else:
                    item.addValue(attributeName, value)
