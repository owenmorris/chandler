"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import os, logging
import mx.DateTime as DateTime
import xml.sax
import xml.sax.handler

import application
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

timing = False
if timing: import tools.timing

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
        if repository is not None:
            cls.__repository = repository
        elif cls.__repository is None:
            cls.__repository = Globals.repository

        if cls.__instanceUUID is not None:
            # We already have an instance; find it via UUID
            instance = cls.__repository.findUUID(cls.__instanceUUID)
            if instance is None:
                # This case can happen when the repository gets swapped
                # out from below us (during unit test runs, for example)
                # so let's bootstrap another manager
                cls.__instanceUUID = None

        if cls.__instanceUUID is None:
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

    def getParentParcel(cls, item):
        parent = item.itsParent
        while str(parent.itsKind.itsPath) != "//Schema/Core/Parcel":
            if str(parent.itsPath) == "//":
                return None
            parent = parent.itsParent
        return parent

    getParentParcel = classmethod(getParentParcel)

    def __bootstrap(cls, repo):
        """
        Make sure that various the //parcels and //parcels/manager items
        are created
        """
        parcelKind = repo.findPath("//Schema/Core/Parcel")

        parcelRoot = repo.findPath("//parcels")
        if parcelRoot is None:
            parcelRoot = parcelKind.newItem("parcels", repo)
            parcelRoot.namespace = NS_ROOT

        manager = parcelRoot.findPath("manager")
        if manager is None:
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
        # Piggy-back on Chandler's handler unless we're outside of Chandler
        if len(self.log.handlers) == 0:
            # No matter our cwd, or sys.argv[0], locate the chandler directory:
            chandler = os.path.dirname(
             os.path.dirname(
              os.path.abspath(application.__file__)
             )
            )
            logHandler = logging.FileHandler(
             os.path.join(chandler,"chandler.log")
            )
            # logHandler.setFormatter(
            #  logging.Formatter('%(asctime)s %(levelname)s %(message)s',
            #   "%m/%d %H:%M:%S")
            # )
            self.log.addHandler(logHandler)
        self.log.setLevel(logging.INFO)

        # Initialize any attributes that aren't persisted:
        self.repo = repository
        self.currentXMLFile = None
        self.currentXMLLine = None
        self.currentExplanation = None
        self.kindUUID = repository.findPath("//Schema/Core/Kind").itsUUID
        self.itemUUID = repository.findPath("//Schema/Core/Item").itsUUID
        self.attrUUID = repository.findPath("//Schema/Core/Attribute").itsUUID
        self.log.info("Parcel Manager initialized")


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

        if namespace is None:
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
        if name is None:
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
            if item is None:
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

        if timing: tools.timing.begin("Scan XML for namespaces")

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
        parser = xml.sax.make_parser(["drv_libxml2"])
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        parser.setContentHandler(handler)

        filesToParse = []
        self.__parcelsToLoad = []
        self.__parcelsToReload = []

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
                            else:
                                self.__parcelsToReload.append(self._repo2ns[repoPath])

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
                self.log.debug("scan: adding %s to load list" % namespace)
                self.__parcelsToLoad.append(namespace)


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
            self.saveState(file=e.getSystemId(), line=e.getLineNumber())
            self.saveExplanation(e.getMessage())
            raise

        if timing: tools.timing.end("Scan XML for namespaces")

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
        @@@ A temporary hack until we modify all the parcel.xml files
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
            self.saveExplanation("Undefined namespace (%s)" % namespace)
            raise NamespaceUndefinedException, namespace
        pDesc = self._ns2parcel[namespace]
        repoPath = pDesc["path"]
        parcelFile = pDesc["file"]

        # make sure we're not already loaded
        parcel = self.repo.findPath(repoPath)
        if parcel is not None and namespace not in self.__parcelsToReload:
            globalDepth = globalDepth - 1
            return parcel

        # make sure parent is loaded
        parentRepoPath = repoPath[:repoPath.rfind('/')]
        parcelParent = self.repo.findPath(parentRepoPath)
        if parcelParent is None:
            parentUri = self._repo2ns[parentRepoPath]
            for i in range(globalDepth):
                print " ",
            print "(%s waiting for parent)" % namespace
            self.__loadParcel(parentUri)

        # make sure we're not already loaded (as a side effect of loading
        # parent)
        parcel = self.repo.findPath(repoPath)
        if parcel is not None and namespace not in self.__parcelsToReload:
            # for i in range(globalDepth):
            #     print " ",
            # print "(skipping %s)" % namespace
            globalDepth = globalDepth - 1
            return parcel

        for i in range(globalDepth):
            print " ",
        print str(namespace)

        # prepare the handler
        handler = ParcelItemHandler()
        handler.manager = self
        handler.repository = self.repo
        handler.file = parcelFile
        handler.repoPath = repoPath
        handler.namespace = namespace
        handler.depCallback = self.__loadParcel

        # prepare the parser
        parser = xml.sax.make_parser(["drv_libxml2"])
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.setFeature(xml.sax.handler.feature_namespace_prefixes, True)
        parser.setContentHandler(handler)

        # remove this parcel from the reload list
        if namespace in self.__parcelsToReload:
            self.__parcelsToReload.remove(namespace)

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
        Print out the error information that was tucked away
        """

        print "\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
        msg =  "Error during parcel loading..."
        print msg
        self.log.error(msg)
        print
        if self.currentXMLFile:
            msg = "   File %s" % self.currentXMLFile
            print msg
            self.log.error(msg)
        if self.currentXMLLine:
            msg = "   Line %d" % self.currentXMLLine
            print msg
            self.log.error(msg)
        if self.currentExplanation:
            msg = "   Reason: %s" % self.currentExplanation
            print msg
            self.log.error(msg)
        else:
            msg = "   Reason not recorded"
            print msg
            self.log.error(msg)
        print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n"



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


        if timing: tools.timing.begin("Load parcels")

        try:
            self.resetState()
            print "Scanning parcels..."
            self.__scanParcels()
            print "...done"

            if not namespaces and self.__parcelsToLoad:
                namespaces = self.__parcelsToLoad

            self.resetState()
            if namespaces:
                print "Loading parcels..."
                for namespace in namespaces:
                    parcel = self.__loadParcel(namespace)
                    parcel.modifiedOn = DateTime.now()
                print "...done"

            self.resetState()
            print "Starting parcels..."
            root = self.repo.findPath("//parcels")
            for parcel in self.__walkParcels(root):
                parcel.startupParcel()
            print "...done"
            self.resetState()

        except:
            self.__displayError()
            raise

        if timing: tools.timing.end("Load parcels")

    def resetState(self):
        self.currentXMLFile = None
        self.currentXMLLine = None
        self.currentExplanation = None

    def saveState(self, file=None, line=None):
        self.currentXMLFile = file
        self.currentXMLLine = line

    def saveExplanation(self, explanation):
        self.currentExplanation = explanation


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

        if self.namespaceMap.has_key(""):
            # This parcel is simply acting on behalf of another parcel, and
            # when we lookup items they should be relative to the other parcel.
            parcel = self.findPath(self.namespaceMap[""])
        else:
            # Lookups will be done relative to this parcel, not another
            parcel = self

        if not self.namespaceMap.has_key(nameHead):
            # The name is not in the map.
            item = parcel.findPath(nameHead)
            if item is None:
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
    _DELAYED_UUIDOF    = 2
    _DELAYED_RESET     = 3

    def saveState(self, file=None, line=None):
        if not file:
            file = self.locator.getSystemId()
        if not line:
            line = self.locator.getLineNumber()
        self.manager.saveState(file, line)

    def saveExplanation(self, explanation):
        self.manager.saveExplanation(explanation)
        return explanation

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
        self.delayedAssigments = []

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
        for (item, attributes) in self.delayedAssigments:
            self.completeAssignments(item, attributes)

        # Here we can perform any additional item clean-up such as ensuring a
        # superKind has been assigned to a kind, or local attributes have been
        # linked up:
        for item in self.itemsCreated:
            self.itemPostProcess(item)


        # Uncomment the following lines for file-by-file printouts of what
        # items are being created:

        # print "\n=-=-=-=-=-=-=-=-= Items for %s" % self.file
        # for item in self.itemsCreated:
        #     PrintItem(item.itsPath, self.repository)
        # print "=-=-=-=-=-=-=-=-= Done with items for %s\n" % self.file

    def characters(self, content):
        """SAX2 callback for character content within the tag"""

        self.saveState()

        (uri, local, element, item, references, reloading) = self.tags[-1]

        if element == 'Attribute' or element == 'Dictionary':
            self.currentValue += content

    def startElementNS(self, (uri, local), qname, attrs):
        """SAX2 callback for the beginning of a tag"""

        self.saveState()

        if not uri:
            explanation = "Element not properly prefixed (%s)" % local
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

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

            # Find the kind represented by the tag (uri, local). The
            # parser has already mapped the prefix to the namespace (uri).
            kind = self.findItem(uri, local, self.locator.getLineNumber())
            if kind is None:
                explanation = "Kind doesn't exist: %s:%s" % (uri, local)
                self.saveExplanation(explanation)
                raise ParcelException(explanation)

            # If we have the document root, use the parcel parent.
            # Otherwise, the currentItem is the parent.
            if len(self.tags) > 0:
                parent = self.currentItem
            else:
                parent = self.parcelParent

            self.currentAssigments = []

            # If the item already exists, we're reloading the item
            self.currentItem = parent.getItemChild(nameString)

            if self.currentItem is not None:
                self.reloadingCurrentItem = True
            else:
                self.reloadingCurrentItem = False
                self.currentItem = self.createItem(kind, parent,
                                                   nameString, classString)
                self.itemsCreated.append(self.currentItem)

        elif attrs.has_key((None, 'uuidOf')):
            # We need to get the UUID of the target item and assign it
            # to the attribute
            element = 'UuidOf'
            self.currentValue = attrs.getValue((None, 'uuidOf'))
            self.currentCopyName = None

        elif attrs.has_key((None, 'itemref')):
            # If it has an itemref, assume its a reference attribute
            # print "Deprecation warning: itemref should now be ref"
            element = 'Reference'
            self.currentValue = attrs.getValue((None, 'itemref'))
            if attrs.has_key((None, 'copy')):
                self.currentCopyName = attrs.getValue((None, 'copy'))
            else:
                self.currentCopyName = None
            if attrs.has_key((None, 'alias')):
                self.currentAliasName = attrs.getValue((None, 'alias'))
            else:
                self.currentAliasName = None

        elif attrs.has_key((None, 'ref')):
            # If it has a ref, assume its a reference attribute
            element = 'Reference'
            self.currentValue = attrs.getValue((None, 'ref'))
            if attrs.has_key((None, 'copy')):
                self.currentCopyName = attrs.getValue((None, 'copy'))
            else:
                self.currentCopyName = None
            if attrs.has_key((None, 'alias')):
                self.currentAliasName = attrs.getValue((None, 'alias'))
            else:
                self.currentAliasName = None

        elif attrs.has_key((None, 'key')):
            # If it has a key, assume its a dictionary of literals
            element = 'Dictionary'
            self.currentKey = attrs.getValue((None, 'key'))
            if attrs.has_key((None, 'type')):
                # Store the full path to the type item
                (typeNamespace, typeName) = self.getNamespaceName(
                 attrs.getValue((None, 'type')))
                typeItem = self.manager.lookup(typeNamespace, typeName)
                if typeItem is None:
                    explanation = \
                     "Type doesn't exist: %s:%s" % (typeNamespace, typeName)
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)
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
                if typeItem is None:
                    explanation = \
                     "Type doesn't exist: %s:%s" % (typeNamespace, typeName)
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)
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
                          self.currentItem, self.currentAssigments,
                          self.reloadingCurrentItem))

    def endElementNS(self, (uri, local), qname):
        """SAX2 callback for the end of a tag"""

        self.saveState()

        uri = self.manager._convertOldUris(uri)

        elementUri = uri
        elementLocal = local

        (uri, local, element, currentItem, currentAssigments,
         reloadingCurrentItem) = self.tags[-1]

        # We have an item, add the collected attributes to the list
        if element == 'Item':
            self.delayedAssigments.append((self.currentItem,
                                           self.currentAssigments))

            # Look at the tags stack for the parent item, and the
            # parent references
            if len(self.tags) >= 2:
                self.currentItem = self.tags[-2][3]
                self.currentAssigments = self.tags[-2][4]
                self.reloadingCurrentItem = self.tags[-2][5]

        else:
            # This is an attribute assignment; Delay it's assignment
            # until we reach the end of the xml document

            # We are deprecating defaultValue:
            if local == "defaultValue":
                explanation = \
                 "The 'defaultValue' attribute has been deprecated"
                self.saveExplanation(explanation)
                raise ParcelException(explanation)

            # Initialize the assignment with values shared by all types:
            assignment = {
               "reloading"  : reloadingCurrentItem,
               "attrName"   : local,
               "key"        : None,
               "copyName"   : None,
               "file"       : self.locator.getSystemId(),
               "line"       : self.locator.getLineNumber()
            }

            if element == 'Reference':
                (namespace, name) = self.getNamespaceName(self.currentValue)
                assignment["assignType"] = self._DELAYED_REFERENCE
                assignment["namespace"] = namespace
                assignment["name"] = name
                assignment["copyName"] = self.currentCopyName
                assignment["aliasName"] = self.currentAliasName

            elif element == 'UuidOf':
                (namespace, name) = self.getNamespaceName(self.currentValue)
                assignment["assignType"] = self._DELAYED_UUIDOF
                assignment["namespace"] = namespace
                assignment["name"] = name

            elif element == 'Attribute': # A scalar or a list
                assignment["assignType"] = self._DELAYED_LITERAL
                assignment["typePath"] = self.currentType
                assignment["value"] = self.currentValue

            elif element == 'Dictionary':
                assignment["assignType"] = self._DELAYED_LITERAL
                assignment["typePath"] = self.currentType
                assignment["value"] = self.currentValue
                assignment["key"] = self.currentKey

            # Store this assignment
            self.currentAssigments.append(assignment)

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

    def itemPostProcess(self, item):
        """ Perform any post-creation-processing such as ensuring a superkind
            has been assigned to a kind, or local attributes have been hooked
            up """

        isItemAKind = (item.itsKind.itsUUID == self.manager.kindUUID)

        if isItemAKind:
            # Assign superKind of //Schema/Core/Item if none assigned
            if not item.hasAttributeValue("superKinds") or \
             (len(item.superKinds) == 0):
                item.addValue("superKinds",
                 self.repository.findUUID(self.manager.itemUUID))

            # Hook up any local attributes to this kind
            if item.hasChildren():
                for child in item:
                    if child.itsKind.itsUUID == self.manager.attrUUID:
                        # child is an attribute
                        item.addValue("attributes", child)

    def makeValue(self, item, attributeName, attributeTypePath, value):
        """ Creates a value from a string, based on the type
            of the attribute.
        """
        if attributeTypePath:
            attributeType = self.repository.findPath(attributeTypePath)
            if attributeType is None:
                explanation = \
                 "Attribute type doesn't exist '%s'" % attributeTypePath
                self.saveExplanation(explanation)
                raise ParcelException(explanation)
            value = attributeType.makeValue(value)
        else:
            if item is None:
                explanation = \
                 "Neither attribute type or item specified"
                self.saveExplanation(explanation)
                raise ParcelException(explanation)

            kindItem = item.itsKind
            try:
                attributeItem = kindItem.getAttribute(attributeName)
            except AttributeError:
                explanation = \
                 "Kind %s does not have the attribute '%s'" \
                  % (kindItem.itsPath, attributeName)
                self.saveExplanation(explanation)
                raise ParcelException(explanation)

            try:
                value = attributeItem.type.makeValue(value)
            except Exception, e:
                explanation = \
                 "'%s' for item '%s', attribute '%s', value '%s'" % \
                 ( e, item.itsPath, attributeName, value )
                self.saveExplanation(explanation)
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
        if item is None:
            self.depCallback(namespace)
            item = self.manager.lookup(namespace, name)

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
            explanation = "Bad itemref: %s" % nameString
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        # If there's no prefix, then use the default set by xmlns=
        if hasPrefix == 0:
            prefix = None
            name = nameString
        else:
            (prefix, name) = nameString.split(':')

        namespace = self.mapping.get(prefix, None)

        if not namespace:
            explanation = "No namespace: '%s'" % prefix
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        return (namespace, name)

    def createItem(self, kind, parent, name, className):
        """ Create a new item, with the kind defined by the tag.
            The new item's namespace is derived from nameString.
            The new item's kind is derived from (uri, local).
        """

        if timing: tools.timing.begin("Creating items")

        try:
            if className:
                # Use the given class to instantiate the item
                cls = ClassLoader.loadClass(className)
                item = cls(name, parent, kind)
            else:
                # The kind knows how to instantiate an instance of the item
                item = kind.newItem(name, parent)
        except Exception, e:
            self.saveExplanation(str(e))
            raise

        if timing: tools.timing.end("Creating items")

        if item is None:
            explanation = "Item not created"
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        return item

    def completeAssignments(self, item, assignments):
        """ Perform all the delayed attribute assignments for an item """

        (old, new) = ValueSet.getValueSets(item)

        for assignment in assignments:

            attributeName = str(assignment["attrName"])
            reloading = assignment["reloading"]
            line = assignment["line"]
            file = assignment["file"]
            if assignment.has_key("key"):
                key = assignment["key"]
            else:
                key = None

            self.saveState(line=line, file=file)

            if timing: tools.timing.begin("Attribute assignments")

            if assignment["assignType"] == self._DELAYED_REFERENCE:

                namespace = assignment["namespace"]
                name = assignment["name"]
                copyName = assignment["copyName"]
                aliasName = assignment["aliasName"]

                # TODO: make sure that the kind does indeed have this
                # attribute (this is checked when it's a literal attribute,
                # but not checked when it's a reference)

                if namespace == CORE and name == "None":
                    reference = None
                    assignmentTuple = \
                     (attributeName, None, None)
                else:
                    reference = self.findItem(namespace, name, line)
                    if reference is None:
                        explanation = "Referenced item doesn't exist: %s:%s" \
                         % (namespace, name)
                        self.saveExplanation(explanation)
                        raise ParcelException(explanation)
                    # Note, for references we record a UUID in the ValueSet
                    assignmentTuple = \
                     (attributeName, str(reference.itsUUID), None)

                if old.assignmentExists(assignmentTuple):
                    # This assignment appeared in the XML file from before;
                    # Remove it from the old value set that it doesn't get
                    # "unassigned" at the end of this.
                    # Also, we can skip this assignment since it must have
                    # been applied before.
                    old.removeAssignment(assignmentTuple)
                else:
                    # This assignment doesn't appear in the previous version
                    # of XML, so let's apply it to the item.

                    # @@@ Special cases to resolve
                    if copyName:
                        # We may be reloading, so if the copy is already there,
                        # remove it and re-copy
                        existingCopy = item.findPath(copyName)
                        if existingCopy is not None:
                            existingCopy.delete(recursive=True)

                        # (either) Copy the item using cloud-copy:
                        copy = reference.copy(name=copyName, parent=item, 
                         cloudAlias="default")

                        # (or) Copy the item using attribute-copy:
                        # copy = reference.copy(name=copyName, parent=item)

                        item.addValue(attributeName, copy)
                    elif attributeName == 'inverseAttribute':
                        item.addValue('otherName', reference.itsName)
                    elif attributeName == 'displayAttribute':
                        item.addValue('displayAttribute', reference.itsName)
                    elif attributeName == 'attributes':
                        item.addValue('attributes', reference,
                                      alias=reference.itsName)
                    else:
                        if aliasName:
                            item.addValue(attributeName, reference,
                             alias=aliasName)
                        else:
                            item.addValue(attributeName, reference)

                    if reloading:
                        print "Reload: item %s, assigning %s = %s" % \
                         (item.itsPath, attributeName, reference.itsPath)

                # Record this assignment in the new set of assignments
                new.addAssignment(assignmentTuple)

            elif assignment["assignType"] == self._DELAYED_UUIDOF:
                namespace = assignment["namespace"]
                name = assignment["name"]

                reference = self.findItem(namespace, name, line)
                if reference is None:
                    explanation = \
                     "Referenced item doesn't exist: %s:%s" % (namespace, name)
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)

                assignmentTuple = \
                 (attributeName, str(reference.itsUUID), None)

                if old.assignmentExists(assignmentTuple):
                    # This assignment appeared in the XML file from before;
                    # Remove it from the old value set that it doesn't get
                    # "unassigned" at the end of this.
                    # Also, we can skip this assignment since it must have
                    # been applied before.
                    old.removeAssignment(assignmentTuple)
                else:
                    # This assignment doesn't appear in the previous version
                    # of XML, so let's apply it to the item.

                    item.addValue(attributeName, reference.itsUUID)

                    if reloading:
                        print "Reload: item %s, assigning %s = UUID of %s" % \
                         (item.itsPath, attributeName, reference.itsPath)

                # Record this assignment in the new set of assignments
                new.addAssignment(assignmentTuple)

            elif assignment["assignType"] == self._DELAYED_LITERAL:

                attributeTypePath = assignment["typePath"]
                value = assignment["value"]

                assignmentTuple = (attributeName, value, key)

                if old.assignmentExists(assignmentTuple):
                    # This assignment appeared in the XML file from before;
                    # Remove it from the old value set that it doesn't get
                    # "unassigned" at the end of this.
                    # Also, we can skip this assignment since it must have
                    # been applied before.
                    old.removeAssignment(assignmentTuple)
                else:
                    # This assignment doesn't appear in the previous version
                    # of XML, so let's apply it to the item.

                    # Special cases
                    if item.itsKind.itsUUID == self.manager.attrUUID and \
                     attributeName in ("initialValue", "defaultValue"):
                        card = item.cardinality
                        if card == "dict":
                            value = {}
                        elif card == "list":
                            value = []
                        else:
                            value = self.makeValue(item, attributeName,
                             attributeTypePath, value)
                    else:
                        value = self.makeValue(item, attributeName,
                         attributeTypePath, value)

                    try:
                        if key is not None:
                            item.setValue(attributeName, value, key)
                            if reloading:
                                print "Reload: item %s, assigning %s[%s] = " \
                                 "'%s'" % \
                                 (item.itsPath, attributeName, key, value)
                        else:
                            item.addValue(attributeName, value)
                            if reloading:
                                print "Reload: item %s, assigning %s = '%s'" % \
                                 (item.itsPath, attributeName, value)

                    except:
                        explanation = "Couldn't add value to item"
                        self.saveExplanation(explanation)
                        raise ParcelException(explanation)

                # Record this assignment in the new set of assignments
                new.addAssignment(assignmentTuple)

            if timing: tools.timing.end("Attribute assignments")

        # Remove any assignments still remaining in the old value set, since
        # we didn't see them in the new XML
        old.unapplyAssignments()

        # Save the new ValueSet into the parcel's originalValues dict
        new.save()


class ValueSet(object):
    def __init__(self, item, relPath, parcel):
        self.item = item
        self.relPath = relPath
        self.parcel = parcel
        self.assignments = {}

    def getValueSets(self, item):
        """ A class method which will return two value sets (original and new)
            for an item.  The new ValueSet will always be empty; the original
            will be created if the item doesn't yet have one.
        """

        # Given an item, find which parcel it lives in, and keep track of
        # the item's path relative to the parcel item.
        if str(item.itsKind.itsPath) == "//Schema/Core/Parcel":
            relPath = ""
            parcel = item
        else:
            relPath = str(item.itsName)
            parcel = item.itsParent
            while str(parcel.itsKind.itsPath) != "//Schema/Core/Parcel":
                relPath = "%s/%s" % (str(parcel.itsName), relPath)
                parcel = parcel.itsParent

        # parcel now points to a parcel
        # relPath is the path to the item relative to the parcel

        # Create two ValueSets, old and new
        oldSet = ValueSet(item, relPath, parcel)
        newSet = ValueSet(item, relPath, parcel)

        # See if the parcel item has an originalValues entry for this item.
        # If not, add an entry.
        # Bind the original ValueSet's attributes dict to the entry.
        # The new ValueSet's attributes dict always starts out empty.
        if relPath not in parcel.originalValues:
            parcel.originalValues[relPath] = {}
        oldSet.assignments = parcel.originalValues[relPath]

        return (oldSet, newSet)

    getValueSets = classmethod(getValueSets)

    def assignmentExists(self, (attrName, value, key)):
        """ Returns True if the ValueSet has this assignment in it. False
            otherwise.
        """
        if attrName not in self.assignments:
            return False

        if attrName == 'inverseAttribute':
            actualName = 'otherName'
        else:
            actualName = attrName

        card = self.item.getAttributeAspect(actualName, "cardinality")
        
        if card == "dict":
            if key not in self.assignments[attrName]:
                return False
            return (self.assignments[attrName][key] == value)
        elif card == "list":
            return value in self.assignments[attrName]
        else:
            return (self.assignments[attrName] == value)


    def removeAssignment(self, (attrName, value, key)):
        """ Remove an assignment from the ValueSet.
        """
        if attrName not in self.assignments:
            return

        if attrName == 'inverseAttribute':
            actualName = 'otherName'
        else:
            actualName = attrName

        card = self.item.getAttributeAspect(actualName, "cardinality")
        
        if card == "dict":
            del self.assignments[attrName][key]
        elif card == "list":
            self.assignments[attrName].remove(value)
        else:
            if self.assignments[attrName] == value:
                del self.assignments[attrName]


    def addAssignment(self, (attrName, value, key)):
        """ Add an assignment to the ValueSet.
        """

        if attrName == 'inverseAttribute':
            actualName = 'otherName'
        else:
            actualName = attrName

        card = self.item.getAttributeAspect(actualName, "cardinality")

        # add attribute to assignments dictionary if not already there
        if attrName not in self.assignments:
            if card == "dict":
                self.assignments[attrName] = {}
            elif card == "list":
                self.assignments[attrName] = []

        if card == "dict":
            self.assignments[attrName][key] = value
        elif card == "list":
            self.assignments[attrName].append(value)
        else:
            self.assignments[attrName] = value


    def save(self):
        """ Bind the parcel's originalValues to this ValueSet's assignments.
        """
        self.parcel.originalValues[self.relPath] = self.assignments


    def getAssignments(self):
        """ A generator which yields assignments tuples
        """
        for (attrName, values) in self.assignments.iteritems():
            card = self.item.getAttributeAspect(attrName, "cardinality")
            if card == "dict":
                for (key, value) in values.iteritems():
                    yield(attrName, value, key)
            elif card == "list":
                for value in values:
                    yield(attrName, value, None)
            else:
                yield(attrName, values, None)

    def unapplyAssignments(self):
        """ Do whatever needs to be done to the item to "remove" this 
            assignment.
        """
        for (attrName, value, key) in self.getAssignments():
            card = self.item.getAttributeAspect(attrName, "cardinality")
            if card == "dict":
                print "Reload: item %s, unassigning %s[%s] = '%s'" % \
                 (self.item.itsPath, attrName, key, value)
                self.item.removeValue(attrName, key)
            elif card == "list":
                # First, see if this is a ref collection, since we handle those
                # differently; to remove an item from a ref collection, we use
                # removeItem( ) which takes an item parameter -- therefore we
                # first need to findUUID() the item.
                if self.item.getAttributeAspect(attrName, "otherName"):
                    attr = self.item.getAttributeValue(attrName)
                    # value is a UUID -- let's load the associated item and then
                    # remove it from this collection
                    otherItem = self.item.findUUID(value)
                    attr.removeItem(otherItem)
                    print "Reload: item %s, unassigning %s = '%s'" % \
                     (self.item.itsPath, attrName, otherItem.itsPath)
                    continue

                # For list and single cardinality attributes, unassigning
                # requires matching "value" to the item's attribute value.
                # For itemrefs, we need to instead match the UUID; that's
                # why we check to see if the value is an item first.
                list = self.item.getAttributeValue(attrName)
                for listValue in list:
                    if isinstance(listValue, repository.item.Item.Item):
                        if str(listValue.itsUUID) == value:
                            list.remove(listValue)
                            print "Reload: item %s, unassigning %s = '%s'" % \
                             (self.item.itsPath, attrName, listValue.itsPath)
                    else:
                        if str(listValue) == value:
                            list.remove(listValue)
                            print "Reload: item %s, unassigning %s = '%s'" % \
                             (self.item.itsPath, attrName, value)
            else:
                attrValue = self.item.getAttributeValue(attrName)
                if isinstance(attrValue, repository.item.Item.Item):
                    if str(attrValue.itsUUID) == value:
                        self.item.removeAttributeValue(attrName)
                        print "Reload: item %s, unassigning %s = '%s'" % \
                         (self.item.itsPath, attrName, attrValue.itsPath)
                else:
                    if str(attrValue) == value:
                        self.item.removeAttributeValue(attrName)
                        print "Reload: item %s, unassigning %s = '%s'" % \
                         (self.item.itsPath, attrName, value)


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
    if item is None:
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
                print str(value), type(value)

    print

    if recursive and item.hasChildren():
        for child in item.iterChildren():
            childPath = str(child.itsPath)
            PrintItem(childPath, rep, recursive=True, level=level+1)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def __prepareRepo():
    from repository.persistence.XMLRepository import XMLRepository

    Globals.chandlerDirectory = os.path.join(os.environ['CHANDLERHOME'])
    repoDir = os.path.join(Globals.chandlerDirectory, '__repository__')
    rep = XMLRepository(repoDir)
    rep.open(create=True)
    if rep.findPath("//Schema") is None:
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
    import time

    rep = __prepareRepo()

    parcelPath = [os.path.join(Globals.chandlerDirectory, "parcels")]
    manager = Manager.getManager(repository=rep, path=parcelPath)
    manager.loadParcels()

    if False:
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


    rep.commit()
    rep.close()

    if timing:
        print "\nTiming results:"
        tools.timing.results()


if __name__ == "__main__":
    __test()
