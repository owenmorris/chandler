"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import os, sys, string, logging, time
import mx.DateTime as DateTime
import xml.sax
import xml.sax.handler

import application.Globals as Globals
import repository
from repository.item.Item import Item
from repository.item.Query import KindQuery
from repository.schema.Kind import Kind
from repository.util.ClassLoader import ClassLoader
from repository.util.Path import Path

NS_ROOT = "http://osafoundation.org/parcels"
CORE = "%s/core" % NS_ROOT
CPIA = "%s/osaf/framework/blocks" % NS_ROOT

class Manager(Item):
    """
    The Parcel Manager, responsible for loading items from XML files into
    the repository and providing a namespace --> item mapping function.

    To use the parcel manager, retrieve a (singleton) instance of it by
    using the class method getManager()::

        import application
        mgr = application.Parcel.Manager.getManager(repository=rep, path=parcelSearchPath)
        mgr.loadParcels()

    By default, the manager will use Globals.repository if the "repository"
    parameter is not passed in; similarly if "path" is not passed in, it
    will use os.path.join(Globals.chandlerDirectory, "parcels").
    """

    __instanceUUID = None            # Stores UUID of the parcel manager object
    __repository = None              # Stores the repository object

    def getManager(cls, repository=None, path=None):
        """
        Class method for getting an instance of the parcel manager.

        If there is an instance already, that will be returned.  Otherwise
        one will be retrieved from the repository (or created there if not
        found), and its "wakeup" method will be called.

        @param repository: The repository object to load items into.  If
        no repository is passed in, "Globals.repository" will be used.
        @type repository: L{repository.persistence.XMLRepository}
        @param path: The search path for finding parcels.  This is a list
        of absolute directory paths; when loading parcels, each directory
        in the search path will be used as a starting point for recursively
        finding parcel.xml files.
        @type path: list
        @return: parcel manager object
        """

        # Use the repository that was passed in, the previously passed in
        # repository, or a default one (from Globals)
        if repository:
            cls.__repository = repository
        elif not cls.__repository:
            cls.__repository = Globals.repository

        if cls.__instanceUUID:
            # We already have an instance; find it via UUID
            instance = cls.__repository.findUUID(cls.__instanceUUID)
            if not instance:
                # This case can happen when the repository gets swapped
                # out from below us (during unit test runs, for example)
                # so let's bootstrap another manager
                cls.__instanceUUID = None

        if not cls.__instanceUUID:
            # Ensure that //parcels is sufficiently bootstrapped
            instance = cls.__bootstrap(cls.__repository)

            # Wake up the parcel manager (set any non-persistent data)
            instance.__wakeUp(cls.__repository)

            # Store the UUID in case someone calls getManager() again
            cls.__instanceUUID = instance.itsUUID

        if path:
            # Passing a path in overrides default or previous path
            instance.path = path
        elif not instance.path:
            # If no path has been set, assign to default ("chandler/parcels")
            instance.path = \
             [os.path.join(Globals.chandlerDirectory, "parcels")]

        return instance

    getManager = classmethod(getManager)


    def __bootstrap(cls, repo):
        """
        Make sure that various the //parcels and //parcels/manager items
        are created
        """
        parcelKind = repo.findPath("//Schema/Core/Parcel")

        parcelRoot = repo.findPath("//parcels")
        if not parcelRoot:
            parcelRoot = parcelKind.newItem("parcels", repo)
            parcelRoot.namespace = NS_ROOT

        manager = parcelRoot.findPath("manager")
        if not manager:
            managerKind = repo.findPath("//Schema/Core/ParcelManager")
            manager = managerKind.newItem("manager", parcelRoot)

        return manager

    __bootstrap = classmethod(__bootstrap)



    def __wakeUp(self, repository):
        """
        Method to be called by start() once per application session in order
        to set up non-persisted things like logging.
        """

        # Set up the parcel manager logger
        self.log = logging.getLogger("parcel")
        logHandler = logging.FileHandler("parcel.log")
        logHandler.setFormatter(
         logging.Formatter('%(asctime)s %(levelname)s %(message)s',
          "%m/%d %H:%M:%S")
        )
        self.log.addHandler(logHandler)
        self.log.setLevel(logging.INFO)
        self.log.info("= = = = = Parcel Manager initialization = = = = =")

        # Initialize any attributes that aren't persisted:
        self.repo = repository
        self.lastError = None


    def lookup(self, namespace, name=None):
        """
        Lookup a name in a namespace.

        Each parcel has a namespace (either
        explicitly defined in its parcel.xml or implicitly calculated based
        on its parent); calling loadParcels( ) populates a registry of these
        namespaces in the parcel manager so that a parcel can be found via
        its namespace.  If the "name" parameter is not provided, the parcel
        item is returned.

        In addition to retrieving parcels, items within
        parcels can be accessed by providing the optional "name" parameter;
        the parcel item's child matching that name will be returned.
        If a parcel has defined "alias" for a name (via a <namespaceMap>
        element in parcel.xml) then the item the alias refers to
        is returned.  Defining a namespace map allows you to provide a "flat"
        XML namespace for your parcel's hierarchy of items.

        There is a special alias a parcel may define:  the name "" (empty
        string).  If this alias is defined, then the item it refers to is
        considered the virtual root of the parcel -- child items searches
        via the "name" parameter will be relative to that virtual root instead
        of the parcel's real item.  This allows us to create a parcel which
        acts on behalf of the core schema; this parcel registers the namespace
        CORE (http://osafoundation.org/parcels/core) and has a
        virtual root of //Schema/Core.  Lookups done through the CORE
        namespace will end up finding the items under //Schema/Core, and since
        this parcel also defines a namespace map we can rearrange the core
        schema items in the repository without affecting other code and XML.
        Normally, looking up a parcel without passing the "name" parameter
        will return a parcel's real item; to retrieve a parcel's virtual root
        item, pass in an empty string for the name (not None, but "")::

            mgr.lookup(CORE).itsPath       # //parcels/core
            mgr.lookup(CORE, "").itsPath   # //Schema/Core


        @param namespace: The name of the namespace to look for
        @type namespace: string
        @param name: The name to look up within the namespace
        @type name: string
        """

        self.log.debug("lookup: args (%s) (%s)" % (namespace, name))

        if not namespace:
            self.log.warning("lookup: no namespace provided")
            return None

        if not self._ns2parcel.has_key(namespace):
            self.log.debug("lookup: no such namespace (%s)" % \
             namespace)
            return None

        pDesc = self._ns2parcel[namespace]

        if name == "":
            # We're after the parcel that this namespace secretly refers to:
            if pDesc["aliases"].has_key(""):
                # The namespace map has an alias for the parcel itself, so
                # let's return the alias
                parcel = self.repo.findPath(pDesc["aliases"][""])
                return parcel
            return None

        # Get the parcel associated with this namespace name (if no name
        # was provided; otherwise we have all the info in pDesc)
        if not name:
            return self.repo.findPath(pDesc["path"])

        # The name passed in could actually be something like "Parcel/createdOn"
        # so we want to pull out the first part of this (before the /) and use
        # that string to lookup
        slash = name.find("/")
        if slash != -1:
            nameHead = name[:slash]
            nameTail = name[slash+1:]
        else:
            nameHead = name
            nameTail = None

        if not pDesc["aliases"].has_key(nameHead):
            # The name is not in the map.
            # Because of how the repository determines what kind of string
            # is being passed to find(), we need to convert name to a Path
            # object (otherwise there is a chance that
            # our string will appear to be a UUID).
            # Also, we convert the name from dot-separated to slash-separated
            # (repo path format)

            path = Path(pDesc["path"])
            # path.extend(Path(nameHead.replace(".", "/")))
            path.extend(Path(nameHead))
            item = self.repo.findPath(path)
            if not item:
                # There is no item with this name
                self.log.debug("lookup: no such name (%s) in namespace "
                 "(%s)" % (nameHead, namespace))
                return None
            else:
                # Found an item with this name
                self.log.debug("lookup: found matching item (%s)" % \
                 item.itsPath)
                if nameTail:
                    return item.findPath(nameTail)
                return item
        else:
            # The name is in the map
            repoPath = pDesc["aliases"][nameHead]
            if nameTail:
                repoPath = "%s/%s" % (repoPath, nameTail)
            self.log.debug("lookup: yielded item (%s)" % \
             repoPath)
            return self.repo.findPath(repoPath)


    def __scanParcels(self):
        """
        Scan through all the parcel XML files looking for namespace definitions,
        building a dictionary mapping namespaces to files.  Any files not
        defining a namespace name get one computed for them, based on their
        parent.
        Also check files for XML correctness (mismatched tags, etc).
        """

        class MappingHandler(xml.sax.ContentHandler):
            """ A SAX2 handler for parsing namespace information """

            def startElementNS(self, (uri, local), qname, attrs):
                # TODO:  remove this remapping once all parcel.xml files
                # are fixed
                if uri == "//Schema/Core":
                    uri = CORE
                if local == "namespace" and uri == CORE:
                    if attrs.has_key((None, 'value')):
                        value = attrs.getValue((None, 'value'))
                        self.namespace = value
                if local == "namespaceMap" and uri == CORE:
                    if attrs.has_key((None, 'key')):
                        key = attrs.getValue((None, 'key'))
                        if attrs.has_key((None, 'value')):
                            value = attrs.getValue((None, 'value'))
                            self.aliases[key] = value

        # Reset any stored error
        self.lastError = None

        # Dictionaries used for quick lookup of mappings between namespace,
        # repository path, and parcel file name.  Populated first by looking
        # at existing parcel items, then overriden by newer parcel.xml files
        self._ns2parcel = { }  # namespace -> "parcel descriptor" (see below)
        self._repo2ns = { }    # repository path -> namespace
        self._file2ns = { }    # file path -> namespace

        # Do a Parcel-kind query for existing parcels; populate a dictionary
        # of "parcel descriptors" (pDesc) which cache parcel information.
        # After reading info from existing parcel items, this info may be
        # overriden from parcel.xml files further down.
        parcelKind = self.repo.findPath("//Schema/Core/Parcel")
        for parcel in KindQuery().run([parcelKind]):
            pDesc = {
             "time" : parcel.modifiedOn.ticks(),
             "path" : str(parcel.itsPath),
             "file" : parcel.file,
             "aliases" : parcel.namespaceMap,
            }
            self._ns2parcel[parcel.namespace] = pDesc
            self._repo2ns[pDesc["path"]] = parcel.namespace

        handler = MappingHandler()
        parser = xml.sax.make_parser()
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        parser.setContentHandler(handler)

        filesToParse = []
        self.__namespacesToLoad = []

        try:
            # Scan the parcel directories for parcel.xml files that are
            # newer than existing parcel items.  Add qualifying files to
            # the "filesToParse" list:
            for directory in self.path:
                for root, dirs, files in os.walk(directory):
                    if 'parcel.xml' in files:
                        repoPath = "//parcels/%s" % root[len(directory)+1:]
                        repoPath = repoPath.replace(os.path.sep, "/")
                        parcelFile = os.path.join(root, 'parcel.xml')

                        # Do we need to open this file? Skip the file only
                        # if the parcel exists and file is not more recent
                        parseThisFile = True
                        if self._repo2ns.has_key(repoPath):
                            # We already have this parcel in the repo; get
                            # it's descriptor by first looking up its namespace
                            pDesc = self._ns2parcel[self._repo2ns[repoPath]]
                            if pDesc["time"] >= os.stat(parcelFile).st_mtime:
                                # The file is not more recent
                                parseThisFile = False

                        if parseThisFile:
                            filesToParse.append((parcelFile, repoPath))

            # We have the list of files to parse, so let's open them up:
            for (parcelFile, repoPath) in filesToParse:

                # initialize the per-file variables:
                handler.namespace = None
                handler.aliases = { }

                # actually parse:
                parser.parse(parcelFile)

                # examine the results:
                namespace = handler.namespace
                if not namespace:
                    # No namespace was specified in the XML.
                    # Need to calculate a namespace for this file,
                    # based on it's parent parcel's namespace
                    # (just append our name to it)
                    myName = repoPath[repoPath.rfind('/')+1:]
                    parentPath = repoPath[:repoPath.rfind('/')]
                    namespace = "%s/%s" % \
                    ( self._repo2ns[parentPath], myName )

                # Set up the parcel descriptor
                pDesc = {
                 "time" : DateTime.now(),
                 "path" : repoPath,
                 "file" : parcelFile,
                 "aliases" : handler.aliases,
                }

                # Update the quick-lookup dictionaries
                self._ns2parcel[namespace] = pDesc
                self._repo2ns[repoPath] = namespace
                self._file2ns[parcelFile] = namespace

                # Load this file during LoadParcels
                self.__namespacesToLoad.append(namespace)


            for file in self._file2ns.keys():
                self.log.debug("scan: file (%s) --> ns (%s)" % \
                 ( file, self._file2ns[file] ) )
            for repoPath in self._repo2ns.keys():
                self.log.debug("scan: path (%s) --> ns (%s)" % \
                 ( repoPath, self._repo2ns[repoPath] ) )
            for uri in self._ns2parcel.keys():
                pDesc = self._ns2parcel[uri]
                self.log.debug("scan: pDesc ns (%s), file (%s), path (%s)" % \
                 ( uri, pDesc["file"], pDesc["path"] ) )
                for alias in pDesc["aliases"].keys():
                    self.log.debug("scan:    alias (%s) --> (%s)" % \
                     (alias, pDesc["aliases"][alias]) )

        except xml.sax._exceptions.SAXParseException, e:
            self.saveErrorState(e.getMessage(), e.getSystemId(), 
             e.getLineNumber())
            raise


    def __walkParcels(self, rootParcel):
        """
        A generator returning all parcel items below rootParcel
        """

        rootParcelPath = tuple(rootParcel.itsPath)
        rootParcelPathLen = len(rootParcelPath)

        parcels = {}

        parcelKind = self.repo.findPath("//Schema/Core/Parcel")
        for parcel in KindQuery().run([parcelKind]):
            p = tuple(parcel.itsPath)
            if p[:rootParcelPathLen] == rootParcelPath:
                parcels[p] = parcel

        parcelPaths = parcels.keys()
        parcelPaths.sort()
        for inPathOrder in parcelPaths:
            yield parcels[inPathOrder]


    def _convertOldUris(self, oldUri):
        """
        A temporary hack until we modify all the parcel.xml files
        """

        if oldUri == "//Schema/Core":
            print "Deprecation warning:  %s" % oldUri
            return CORE
        if not self._repo2ns.has_key(oldUri):
            return oldUri
        print "Deprecation warning:  %s" % oldUri
        return self._repo2ns[oldUri]


    def __loadParcel(self, namespace):
        """
        Load a specific parcel (specified by namespace).

        If the given parcel's parent isn't loaded yet, load the parent first.
        """

        global globalDepth
        globalDepth = globalDepth + 1

        # Look for the parcel's namespace in the parcel descriptors
        if not self._ns2parcel.has_key(namespace):
            raise NamespaceUndefinedException, namespace
        pDesc = self._ns2parcel[namespace]
        repoPath = pDesc["path"]
        parcelFile = pDesc["file"]

        # make sure we're not already loaded
        parcel = self.repo.findPath(repoPath)
        if parcel:
            globalDepth = globalDepth - 1
            return parcel

        # make sure parent is loaded
        parentRepoPath = repoPath[:repoPath.rfind('/')]
        parcelParent = self.repo.findPath(parentRepoPath)
        if not parcelParent:
            parentUri = self._repo2ns[parentRepoPath]
            for i in range(globalDepth):
                print " ",
            print "(%s waiting for parent)" % namespace
            self.__loadParcel(parentUri)

        # make sure we're not already loaded (as a side effect of loading
        # parent)
        parcel = self.repo.findPath(repoPath)
        if parcel:
            # for i in range(globalDepth):
            #     print " ",
            # print "(skipping %s)" % namespace
            globalDepth = globalDepth - 1
            return parcel

        for i in range(globalDepth):
            print " ",
        print namespace

        # prepare the handler
        handler = ParcelItemHandler()
        handler.manager = self
        handler.repository = self.repo
        handler.file = parcelFile
        handler.repoPath = repoPath
        handler.namespace = namespace
        handler.depCallback = self.__loadParcel

        # prepare the parser
        parser = xml.sax.make_parser()
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        parser.setContentHandler(handler)

        # parse the file and load the items
        parser.parse(parcelFile)

        # get the item and make sure it has its namespace assigned
        parcel = self.repo.findPath(repoPath)
        parcel.namespace = namespace
        parcel.file = parcelFile
        globalDepth = globalDepth - 1
        return parcel


    def __displayError(self):
        """
        Print out the error information that was tucked away in lastError
        """

        print
        print "Error during parcel loading..."
        if self.lastError:
            print "   Exception '%s'" % self.lastError["message"]
            print "   File %s" % self.lastError["file"]
            print "   Line %d" % self.lastError["line"]
            self.log.error("Exception '%s' loading %s:%s" % \
             (self.lastError["message"], self.lastError["file"], \
             self.lastError["line"]))
        else:
            print "  [state of the error wasn't captured]"
            self.log.error("An error occurred but state wasn't captured")
        print


    def loadParcels(self, namespaces=None):
        """
        Load parcel items into the repository.

        This method scans all the parcel.xml files it finds below all
        directories in the parcel search path, populating a namespace registry.
        The namespaces passed in via the namespaces parameter (a list) are then
        loaded into the repository.  If that parameter is None, then all parcels
        are loaded.

        @param namespaces: The list of namespaces to load
        @type namespace: list of strings
        """
        global globalDepth
        globalDepth = 0

        try:
            print "Scanning parcels...",
            self.__scanParcels()
            print " done"

            if not namespaces and self.__namespacesToLoad:
                namespaces = self.__namespacesToLoad

            if namespaces:
                print "Loading parcels..."
                for namespace in namespaces:
                    parcel = self.__loadParcel(namespace)
                    parcel.modifiedOn = DateTime.now()
                print "...done"

            print "Starting parcels...",
            root = self.repo.findPath("//parcels")
            for parcel in self.__walkParcels(root):
                parcel.startupParcel()
            print " done"

        except Exception, e:
            self.__displayError()
            raise


    def saveErrorState(self, message, file, line):
        self.lastError = {
            "message"   : message,
            "file"      : file,
            "line"      : line,
        }
        return ParcelException("%s at %s:%s" % (message, file, line))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class ParcelException(Exception):
    """
    The exception class raised whenever the parcel manager itself
    discovers an error condition.  If a lower-level library, such
    as the repository or XML parser, raises an exception, the parcel
    manager will intercept it, print out debugging info about which
    file was being parsed, and re-raise the original exception.
    """

    def __init__(self, args=None):
        self.args = args

class NamespaceUndefinedException(ParcelException):
    """
    An exception raised when the namespace that was being looked up doesn't
    exist.
    """
    pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Parcel(Item):
    """
    The parcel item class.

    parcel.xml files should always define an item of kind Parcel as the root
    element of the document.  These items receive a callback, startupParcel(),
    each time the loadParcels() method is run, after all parcel items have
    been loaded in.

    Items within a parcel may be retrieved via the lookup() method.
    """

    def __init__(self, name, parent, kind):
        super(Parcel, self).__init__(name, parent, kind)
        self.createdOn = DateTime.now()
        self.modifiedOn = self.createdOn

    def _fillItem(self, name, parent, kind, **kwds):
        super(Parcel, self)._fillItem(name, parent, kind, **kwds)

    def startupParcel(self):
        """
        Method called at the end of loadParcels().  Parcel items can perform
        whatever non-persisted setup they need to do.
        """
        pass

    def onItemLoad(self):
        # TODO:  Find out if we really need this here.  Subclasses of Parcel 
        # seem to be expecting this method to be here.
        pass

    def lookup(self, name=None):
        """
        Retrieve an item from the parcel.

        By default, if a parcel does not have a namespace map (defined by
        <namespaceMap> XML elements), the parcel's child item with that
        name will be returned.  If there is a namespace map, then the 
        name will first be looked up in the map, returning the aliased item
        instead.
        """

        if not name:
            return None

        # The name passed in could actually be something like "Parcel/createdOn"
        # so we want to pull out the first part of this (before the /) and use
        # that string to lookup
        slash = name.find("/")
        if slash != -1:
            nameHead = name[:slash]
            nameTail = name[slash+1:]
        else:
            nameHead = name
            nameTail = None

        if not self.namespaceMap.has_key(""):
            # This parcel is simply acting on behalf of another parcel, and
            # when we lookup items they should be relative to the other parcel.
            parcel = self.findPath(self.namespaceMap[""])
        else:
            # Lookups will be done relative to this parcel, not another
            parcel = self

        if not self.namespaceMap.has_key(nameHead):
            # The name is not in the map.
            item = parcel.findPath(nameHead)
            if not item:
                # There is no item with this name
                return None
            else:
                # Found an item with this name
                if nameTail:
                    return item.findPath(nameTail)
                return item
        else:
            # The name is in the map
            repoPath = self.namespaceMap[nameHead]
            if nameTail:
                repoPath = "%s/%s" % (repoPath, nameTail)
            return self.findPath(repoPath)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class ParcelItemHandler(xml.sax.ContentHandler):
    """ A SAX2 ContentHandler responsible for loading items into the 
        repository.
    """
    _DELAYED_REFERENCE = 0
    _DELAYED_LITERAL   = 1

    def saveErrorState(self, message):
        return self.manager.saveErrorState(
         message,
         self.locator.getSystemId(),
         self.locator.getLineNumber()
        )

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

        # For debugging, save a list of items we've generated for this file
        self.itemsCreated = []

        self.currentItem = None

        # Get the parcel's parent
        parentRepoPath = self.repoPath[:self.repoPath.rfind('/')]
        self.parcelParent = self.repository.findPath(parentRepoPath)

    def endDocument(self):
        """SAX2 callback at the end of the document"""

        # We've delayed loading the references until the end of the file.
        # Wire up attribute/reference pairs to the items.
        for (item, attributes) in self.delayedReferences:
            self.addReferences(item, attributes)

        # Uncomment the following lines for file-by-file printouts of what
        # items are being created:

        # print "\n=-=-=-=-=-=-=-=-= Items for %s" % self.file
        # for item in self.itemsCreated:
        #     PrintItem(item.itsPath, self.repository)
        # print "=-=-=-=-=-=-=-=-= Done with items for %s\n" % self.file

    def characters(self, content):
        """SAX2 callback for character content within the tag"""

        (uri, local, element, item, references) = self.tags[-1]

        if element == 'Attribute' or element == 'Dictionary':
            self.currentValue += content

    def startElementNS(self, (uri, local), qname, attrs):
        """SAX2 callback for the beginning of a tag"""

        if not uri:
            raise self.saveErrorState("Element not properly prefixed (%s)" % \
             local)

        uri = self.manager._convertOldUris(uri)

        nameString = None
        if attrs.has_key((None, 'itemName')):
            # print "Deprecation warning: itemName should now be itsName"
            nameString = attrs.getValue((None, 'itemName'))
        elif attrs.has_key((None, 'itsName')):
            nameString = attrs.getValue((None, 'itsName'))
        if nameString:
            # If it has an item name, its an item
            element = 'Item'

            if attrs.has_key((None, 'itemClass')):
                classString = attrs.getValue((None, 'itemClass'))
            else:
                classString = None
            self.currentItem = self.createItem(uri, local,
                                               nameString, classString)
            self.itemsCreated.append(self.currentItem)
            self.currentReferences = []

        elif attrs.has_key((None, 'itemref')):
            # If it has an itemref, assume its a reference attribute
            # print "Deprecation warning: itemref should now be ref"
            element = 'Reference'
            self.currentValue = attrs.getValue((None, 'itemref'))

        elif attrs.has_key((None, 'ref')):
            # If it has an itemref, assume its a reference attribute
            element = 'Reference'
            self.currentValue = attrs.getValue((None, 'ref'))

        elif attrs.has_key((None, 'key')):
            # If it has a key, assume its a dictionary of literals
            element = 'Dictionary'
            self.currentKey = attrs.getValue((None, 'key'))
            if attrs.has_key((None, 'type')):
                # Store the full path to the type item
                (typeNamespace, typeName) = self.getNamespaceName(
                 attrs.getValue((None, 'type')))
                typeItem = self.manager.lookup(typeNamespace, typeName)
                self.currentType = str(typeItem.itsPath) # TODO, perhaps
                # instead of converting to string and back, just store item
                # reference ?
            else:
                self.currentType = None
            if attrs.has_key((None, 'value')):
                self.currentValue = attrs.getValue((None, 'value'))
            else:
                self.currentValue = ''

        else:
            # Otherwise, assume its a literal attribute
            element = 'Attribute'
            if attrs.has_key((None, 'type')):
                # Store the full path to the type item
                (typeNamespace, typeName) = self.getNamespaceName(
                 attrs.getValue((None, 'type')))
                typeItem = self.manager.lookup(typeNamespace, typeName)
                self.currentType = str(typeItem.itsPath) # TODO, perhaps
                # instead of converting to string and back, just store item
                # reference ?

            else:
                self.currentType = None
            if attrs.has_key((None, 'value')):
                self.currentValue = attrs.getValue((None, 'value'))
            else:
                self.currentValue = ''

        # Add the tag to our context stack
        self.tags.append((uri, local, element,
                          self.currentItem, self.currentReferences))

    def endElementNS(self, (uri, local), qname):
        """SAX2 callback for the end of a tag"""

        uri = self.manager._convertOldUris(uri)

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
                        value = self.makeValue(currentItem, elementLocal,
                         self.currentType, self.currentValue,
                         self.locator.getLineNumber())
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
                    value = self.makeValue(currentItem, elementLocal,
                     self.currentType, self.currentValue,
                     self.locator.getLineNumber())
                    currentItem.addValue(elementLocal, value)
            else: # Delay
                self.currentReferences.append((self._DELAYED_LITERAL, local,
                 self.currentType, self.currentValue, None,
                 self.locator.getLineNumber()))

        # We have a dictionary, similar to attribute, but we have a key
        elif element == 'Dictionary':
            if isSchemaItem:
                value = self.makeValue(currentItem, elementLocal,
                 self.currentType, self.currentValue,
                 self.locator.getLineNumber())
                currentItem.setValue(elementLocal, value, self.currentKey)
            else: # Delay
                self.currentReferences.append((self._DELAYED_LITERAL, local,
                 self.currentType, self.currentValue, self.currentKey,
                 self.locator.getLineNumber()))

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
        uri = self.manager._convertOldUris(uri)

        self.mapping[prefix] = uri

    def endPrefixMapping(self, prefix):
        """ SAX2 callback for namespace prefixes """

        # If we define a prefix mapping, it means we depend on
        # the parcel. Load the uri, if it does not match the uri
        # for this file.

        uri = self.mapping[prefix]
        if uri != self.namespace:
            self.depCallback(uri)

        self.mapping[prefix] = None


    def makeValue(self, item, attributeName, attributeTypePath, value, line):
        """ Creates a value from a string, based on the type
            of the attribute.
        """
        if attributeTypePath:
            attributeType = self.repository.findPath(attributeTypePath)
            value = attributeType.makeValue(value)
        else:
            if not item:
                raise self.saveErrorState("No parent item")

            kindItem = item.itsKind
            attributeItem = kindItem.getAttribute(attributeName)

            if not attributeItem:
                raise self.saveErrorState( \
                 "Kind %s does not have the attribute '%s'" % \
                 (kindItem.itsPath, attributeName) )

            try:
                value = attributeItem.type.makeValue(value)
            except ImportError, e:
                self.saveErrorState( \
                 "'%s' for item '%s', attribute '%s'" % \
                 ( e, item.itsPath, attributeName ) )
                raise

        return value

    def findItem(self, namespace, name, line):
        """ Find the item with the namespace indicated by prefix,
            and with the given name.  If it isn't yet in the repository
            the try loading the parcel it's supposed to be in.
        """

        item = self.manager.lookup(namespace, name)

        # If the item doesn't yet exist, load the parcel it's supposed
        # to be in and try again
        if not item:
            self.depCallback(namespace)
            item = self.manager.lookup(namespace, name)

        if not item:
            raise self.saveErrorState("No item %s:%s" % (namespace, name))

        return item

    def getNamespaceName(self, nameString):
        """ Given a nameString, parse out the namespace prefix and look
            it up in the dictionary of namespace mappings.
            'core:String' => ('//Schema/Core', String)

            If there's no prefix, use the default namespace set by xmlns=
            'String' => ('//Schema/Core', String)
        """

        hasPrefix = nameString.count(':')

        if not (0 <= hasPrefix <= 1):
            raise self.saveErrorState("Bad itemref: %s" % nameString)

        # If there's no prefix, then use the default set by xmlns=
        if hasPrefix == 0:
            prefix = None
            name = nameString
        else:
            (prefix, name) = nameString.split(':')

        namespace = self.mapping.get(prefix, None)

        if not namespace:
            raise self.saveErrorState("No namespace: '%s'" % prefix)

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

        # If the item already exists, consider it an error.  In the future
        # we will want to support item reloading.
        item = parent.getItemChild(name)
        if item:
            raise self.saveErrorState("Item already exists %s" % item.itsPath)

        # Find the kind represented by the tag (uri, local). The
        # parser has already mapped the prefix to the namespace (uri).
        kind = self.findItem(uri, local,
                             self.locator.getLineNumber())

        try:
            if className:
                # Use the given class to instantiate the item
                cls = ClassLoader.loadClass(className)
                item = cls(name, parent, kind)
            else:
                # The kind knows how to instantiate an instance of the item
                item = kind.newItem(name, parent)
        except Exception, e:
            self.saveErrorState(str(e))
            raise

        if not item:
            raise self.saveErrorState("Item not created")

        return item

    def addReferences(self, item, attributes):
        """ Add all of the references in the list to the item """

        for (type, attributeName, namespace, name, key, line) in attributes:

            if type == self._DELAYED_REFERENCE:
                if namespace == CORE and name == "None":
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def PrintItem(path, rep, recursive=False, level=0):
    """
    A pretty-printer for repository items.

    Example::

        repository.parcel.PrintItem("//Schema", repository)

    @param rep: The repository object to use
    @type rep: L{repository.persistence.XMLRepository}
    @param recursive: Whether to also display child items or not (default=False)
    @type recursive:  Boolean
    """

    for i in range(level):
        print " ",
    item = rep.findPath(path)
    if not item:
        print "Error: %s was not found" % path
        return

    if item.itsKind:
        print "%s (Kind: %s)" % (path, item.itsKind.itsPath )
    else:
        print "%s" % (path)

    # For Kinds, display their attributes (except for the internal ones
    # like notFoundAttributes:
    if item.itsKind and "//Schema/Core/Kind" == str(item.itsKind.itsPath):
        for i in range(level+2):
            print " ",
        print "attributes for this kind:"

        displayedAttrs = { }
        for (name,attr) in item.iterAttributes():
            displayedAttrs[name] = attr

        keys = displayedAttrs.keys()
        keys.sort()
        for key in keys:
            for k in range(level+4):
                print " ",
            print "%s %s" % ( key, displayedAttrs[key].itsPath )

    displayedAttrs = { }
    for (name, value) in item.iterAttributeValues():
        displayedAttrs[name] = value

    keys = displayedAttrs.keys()
    keys.sort()
    for name in keys:
        value = displayedAttrs[name]
        t = type(value)

        if name == "attributes" or \
           name == "notFoundAttributes" or \
           name == "inheritedAttributes" or \
           name == "kind":
            pass

        elif t == list \
         or t == repository.item.PersistentCollections.PersistentList:
            for i in range(level+2):
                print " ",

            print "%s: (list)" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j

        elif t == repository.item.PersistentCollections.PersistentDict:
            for i in range(level+2):
                print " ",

            print "%s: (dict)" % name
            for key in value.keys():
                for k in range(level+4):
                    print " ",
                print "%s:" % key, value[key]

        elif t == repository.persistence.XMLRepositoryView.XMLRefDict \
         or t == repository.item.ItemRef.TransientRefDict:
            for i in range(level+2):
                print " ",

            print "%s: (dict)" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j.itsPath

        else:
            for i in range(level+2):
                print " ",

            print "%s:" % name,
            try:
                print value.itsPath
            except:
                print value, type(value)

    print

    if recursive and item.hasChildren():
        for child in item.iterChildren():
            childPath = str(child.itsPath)
            PrintItem(childPath, rep, recursive=True, level=level+1)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def __prepareRepo():
    from repository.persistence.XMLRepository import XMLRepository

    Globals.chandlerDirectory = os.path.join(os.environ['CHANDLERHOME'],
     "chandler")
    repoDir = os.path.join(Globals.chandlerDirectory, '__repository__')
    rep = XMLRepository(repoDir)
    rep.open(create=True)
    if not rep.findPath("//Schema"):
        print "Bootstrapping //Schema"
        bootstrapPack = os.path.join(Globals.chandlerDirectory, 'repository',
         'packs', 'schema.pack')
        rep.loadPack(bootstrapPack)
    Globals.repository = rep

    # Notification manager is now needed for Item Collections(?):
    from osaf.framework.notifications.NotificationManager import NotificationManager
    Globals.notificationManager = NotificationManager()
    return rep


def __test():
    """
    If this module is run as a script, run some tests
    """
    rep = __prepareRepo()

    parcelPath = [os.path.join(Globals.chandlerDirectory, "parcels")]
    manager = Manager.getManager(repository=rep, path=parcelPath)
    manager.loadParcels()

    # PrintItem("//parcels/osaf/contentmodel/mail", rep, recursive=True)

    # Get the "virtual" core parcel (//parcels/core)
    core = manager.lookup(CORE)
    print core.itsPath
    print core.lookup("Kind").itsPath
    print core.lookup("Parcel/file").itsPath

    # Get the "real" core (//Schema/Core)
    item = manager.lookup(CORE, "")
    print item.itsPath

    item = manager.lookup(CORE, "Parcel")
    print item.itsPath

    item = manager.lookup(CORE, "Parcel/file")
    print item.itsPath

    item = manager.lookup(CPIA, "Block")
    print item.itsPath

    # PrintItem("//Schema/Core/Parcel", rep, recursive=True)

    rep.commit()
    rep.close()

if __name__ == "__main__":
    __test()
