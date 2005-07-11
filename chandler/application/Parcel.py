"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import sys, os, logging
import xml.sax
import xml.sax.handler

from time import mktime
from datetime import datetime

import application
import application.Globals as Globals
import repository
from repository.item.Item import Item
from repository.item.Query import KindQuery
from repository.schema.Kind import Kind
from repository.util.ClassLoader import ClassLoader
from repository.util.Path import Path
from repository.item.RefCollections import RefList
import repository.item.Values
from repository.schema.Attribute import Attribute

logger = logging.getLogger('Parcel')
logger.setLevel(logging.INFO)

NS_ROOT = "http://osafoundation.org/parcels"
CORE = "parcel:core"

#@@@Temporary testing tool written by Morgen -- DJA
timing = False
if timing: import util.timing

class Manager(Item):
    """
    The Parcel Manager, responsible for loading items from XML files into
    the repository and providing a namespace --> item mapping function.

    To use the parcel manager, retrieve an instance of it by using the class
    method get()::

        import application
        mgr = application.Parcel.Manager.get(view, path=parcelSearchPath)
        mgr.loadParcels()

    if "path" is not passed in, it will use
    os.path.join(Globals.chandlerDirectory, "parcels").
    """

    def get(cls, view, path=None):
        """
        Class method for getting an instance of the parcel manager.

        If there is a manager item already already in this repository, that
        will be returned.  Otherwise one will be created.

        @param view: The repository view object to load items into.
        @type view: L{repository.persistence.RepositoryView}
        @param path: The search path for finding parcels.  This is a list
        of absolute directory paths; when loading parcels, each directory
        in the search path will be used as a starting point for recursively
        finding parcel.xml files.
        @type path: list
        @return: parcel manager object
        """

        manager = view.findPath("//parcels/manager")
        if manager is None:
            parcelKind = view.findPath("//Schema/Core/Parcel")
            parcelRoot = view.findPath("//parcels")
            if parcelRoot is None:
                parcelRoot = parcelKind.newItem("parcels", view)
                parcelRoot.namespace = NS_ROOT
            manager = parcelRoot.findPath("manager")
            if manager is None:
                managerKind = view.findPath("//Schema/Core/ParcelManager")
                manager = managerKind.newItem("manager", parcelRoot)

        if path:
            manager.path = path
        elif not manager.path:
            manager.path = [os.path.join(Globals.chandlerDirectory, "parcels")]

        return manager

    get = classmethod(get)

    def __init__(self, name, parent, kind):
        super(Manager, self).__init__(name, parent, kind)
        self.onItemLoad(self.itsView)

    def onItemLoad(self, view):

        # Initialize any attributes that aren't persisted:
        self.repo = view
        self.currentXMLFile = None
        self.currentXMLLine = None
        self.currentExplanation = None
        self.kindUUID = view.findPath("//Schema/Core/Kind").itsUUID
        self.itemUUID = view.findPath("//Schema/Core/Item").itsUUID
        self.attrUUID = view.findPath("//Schema/Core/Attribute").itsUUID
        self.registryLoaded = False
        logger.info("Parcel Manager initialized")

    def getParentParcel(cls, item):
        parent = item.itsParent
        while str(parent.itsKind.itsPath) != "//Schema/Core/Parcel":
            if str(parent.itsPath) == "//":
                return None
            parent = parent.itsParent
        return parent

    getParentParcel = classmethod(getParentParcel)

    def _addParcelDescriptor(self, ns, pDesc):
        self._ns2parcel[ns] = pDesc
        self._repo2ns[pDesc["path"]] = ns
        if ns.startswith(NS_ROOT+'/'):
            ns = "parcel:%s" % ns[len(NS_ROOT)+1:].replace('/','.')
            self._ns2parcel[ns] = pDesc
            self._repo2ns[pDesc["path"]] = ns
        elif ns.startswith('parcel:'):
            altns = NS_ROOT+'/'+ns[7:].replace('.','/')
            self._ns2parcel.setdefault(altns, pDesc)

        if ns.startswith('parcel:'):
            if '.' in ns:
                parent,name = ns.rsplit('.',1)
                if ns not in self._ns2parcel:
                    self._addParcelDescriptor(ns, {
                        "path" : pDesc["path"].rsplit('/',1)[0],
                        "aliases" : {},
                    })


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
        CORE (parcel:core) and has a
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

        logger.debug("lookup: args (%s) (%s)" % (namespace, name))

        if not self.registryLoaded:
            self.__refreshRegistry()

        if namespace is None:
            logger.warning("lookup: no namespace provided")
            return None

        if not self._ns2parcel.has_key(namespace):
            logger.debug("lookup: no such namespace (%s)" % \
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
                logger.debug("lookup: no such name (%s) in namespace "
                 "(%s)" % (nameHead, namespace))
                return None
            else:
                # Found an item with this name
                logger.debug("lookup: found matching item (%s)" % \
                 item.itsPath)
                if nameTail:
                    return item.findPath(nameTail)
                return item
        else:
            # The name is in the map
            repoPath = pDesc["aliases"][nameHead]
            if nameTail:
                repoPath = "%s/%s" % (repoPath, nameTail)
            logger.debug("lookup: yielded item (%s)" % \
             repoPath)
            return self.repo.findPath(repoPath)

    def _parcelDescriptor(self, parcel):
        return {
             "time" : mktime(parcel.modifiedOn.timetuple()),
             "path" : str(parcel.itsPath),
             "file" : parcel.file,
             "aliases" : parcel.namespaceMap,
            }

    def __refreshRegistry(self):
        # Dictionaries used for quick lookup of mappings between namespace,
        # repository path, and parcel file name.  Populated first by looking
        # at existing parcel items, then overriden by newer parcel.xml files
        self._ns2parcel = { }  # namespace -> "parcel descriptor" (see below)
        self._repo2ns = {'//parcels':NS_ROOT}  # repository path -> namespace
        self._file2ns = { }    # file path -> namespace
        self._imported = set()    # imported namespaces

        # Do a Parcel-kind query for existing parcels; populate a dictionary
        # of "parcel descriptors" (pDesc) which cache parcel information.
        # After reading info from existing parcel items, this info may be
        # overridden from parcel.xml files further down.
        parcelKind = self.repo.findPath("//Schema/Core/Parcel")
        for parcel in KindQuery().run([parcelKind]):
            pDesc = self._parcelDescriptor(parcel)
            self._addParcelDescriptor(parcel.namespace, pDesc)

        self.registryLoaded = True

    def __scanParcels(self):
        """
        Scan through all the parcel XML files looking for namespace definitions,
        building a dictionary mapping namespaces to files.  Any files not
        defining a namespace name get one computed for them, based on their
        parent.
        Also check files for XML correctness (mismatched tags, etc).
        """
        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.begin("Scan XML for namespaces")

        class MappingHandler(xml.sax.ContentHandler):
            """ A SAX2 handler for parsing namespace information """

            def startElementNS(self, (uri, local), qname, attrs):
                if local == "namespace" and uri in (CORE,NS_ROOT+'/core'):
                    if attrs.has_key((None, 'value')):
                        value = attrs.getValue((None, 'value'))
                        self.namespace = value
                if local == "namespaceMap" and uri in (CORE,NS_ROOT+'/core'):
                    if attrs.has_key((None, 'key')):
                        key = attrs.getValue((None, 'key'))
                        if attrs.has_key((None, 'value')):
                            value = attrs.getValue((None, 'value'))
                            self.aliases[key] = value

        self.__refreshRegistry()

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
                # When doing test cases, 'directory' might be a package
                # directory, so ensure that we compute its repository path
                # based on its full package name, not just relative to
                # the directory searched in.
                base_path = ''
                directory = os.path.abspath(directory)
                for path_item in sys.path:
                    if directory==path_item or directory.startswith(path_item+os.path.sep):
                        if len(path_item)>len(base_path):
                            base_path = path_item

                base_path = base_path or directory

                for root, dirs, files in os.walk(directory):

                    # Allows you to skip specific parcels
                    if 'noload' in files:
                        continue

                    if 'parcel.xml' in files:
                        repoPath = "//parcels/%s" % root[len(base_path)+1:]
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
                    try:
                        parentNS = self._repo2ns[parentPath]
                    except KeyError:
                        if parentPath.startswith('//parcels/'):
                            parentNS = 'parcel:'+parentPath[10:].replace('/','.')
                        else:
                            raise
                    if parentNS.startswith('parcel:'):
                        namespace = "%s.%s" % (parentNS,myName)
                    else:
                        namespace = "%s/%s" % (parentNS, myName )
                #else:
                #    print "<namespace %s> being used in %s" %(namespace, parcelFile)

                # Set up the parcel descriptor
                pDesc = {
                 "time" : datetime.now(),
                 "path" : repoPath,
                 "file" : parcelFile,
                 "aliases" : handler.aliases,
                }

                # Update the quick-lookup dictionaries
                self._addParcelDescriptor(namespace,pDesc)
                self._file2ns[parcelFile] = namespace

                # Load this file during LoadParcels
                logger.debug("scan: adding %s to load list" % namespace)
                self.__parcelsToLoad.append(namespace)


            for file in self._file2ns.keys():
                logger.debug("scan: file (%s) --> ns (%s)" % \
                 ( file, self._file2ns[file] ) )
            for repoPath in self._repo2ns.keys():
                logger.debug("scan: path (%s) --> ns (%s)" % \
                 ( repoPath, self._repo2ns[repoPath] ) )
            for uri in self._ns2parcel.keys():
                pDesc = self._ns2parcel[uri]
                logger.debug("scan: pDesc ns (%s), file (%s), path (%s)" % \
                 ( uri, pDesc["file"], pDesc["path"] ) )
                for alias in pDesc["aliases"].keys():
                    logger.debug("scan:    alias (%s) --> (%s)" % \
                     (alias, pDesc["aliases"][alias]) )

        except xml.sax._exceptions.SAXParseException, e:
            self.saveState(file=e.getSystemId(), line=e.getLineNumber())
            self.saveExplanation(e.getMessage())
            raise

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.end("Scan XML for namespaces")

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


    def __syncParcel(self, namespace):
        """Synchronize the specified parcel's Python schema with self.repo

        If the namespace is under NS_ROOT, this will import the corresponding
        Python module and synchronize its schema with the repository.  If the
        imported module has a parent module that has not yet been synchronized,
        this method will load the parent parcel, thereby synchronizing the
        parent module first.

        ``self.__parcelsToReload`` is updated to include the given `namespace`
        if it is not already present.  This ensures that the loader will not
        skip a parcel just because it was already created by a Python schema
        module.
        """
        if namespace in self._imported:
            return  # skip already-processed parcels
        else:
            self._imported.add(namespace)

        if namespace.startswith('parcel:') or  namespace.startswith(NS_ROOT):
            if namespace.startswith('parcel:'):
                pkg = namespace[7:]
            else:
                # The package we need to import and sync          
                pkg = namespace[len(NS_ROOT)+1:].replace('/','.')

            # Mark for reload *before* the nested __loadParcel(parent) call,
            # because otherwise the nested call may re-invoke __loadParcel()
            # on this parcel, and then not reload it properly
            if namespace not in self.__parcelsToReload:
                self.__parcelsToReload.append(namespace)
                
            if '.' in pkg:
                # load parent first - even though schema API does this too,
                # the parcel loader will get confused and not load the
                # parent parcel correctly, unless we process it here.  :(
                parent_pkg = pkg.rsplit('.',1)[0]
                if parent_pkg not in self._imported:
                    self.__loadParcel('parcel:'+parent_pkg)

            # Last, but not least, actually synchronize the package
            schema.synchronize(self.repo, pkg)


    def __loadParcel(self, namespace):
        """
        Load a specific parcel (specified by namespace).

        If the given parcel's parent isn't loaded yet, load the parent first.
        """
        # To ensure parcels with a dual identity don't get loaded twice
        if namespace.startswith(NS_ROOT):
            namespace = 'parcel:' + namespace[len(NS_ROOT)+1:].replace('/','.')

        global globalDepth
        globalDepth = globalDepth + 1

        if namespace not in self._imported:
            self.__syncParcel(namespace)

        # Look for the parcel's namespace in the parcel descriptors
        if not self._ns2parcel.has_key(namespace):
            if not namespace.startswith('parcel:'):
                self.saveExplanation("Undefined namespace (%s)" % namespace)
                raise NamespaceUndefinedException, namespace
            else:
                #print "Simulating load for", namespace
                globalDepth -= 1
                if namespace in self.__parcelsToReload:
                    self.__parcelsToReload.remove(namespace)
                parcel = schema.parcel_for_module(namespace[7:],self.repo)
                self._addParcelDescriptor(namespace,self._parcelDescriptor(parcel))
                return parcel

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
            # for i in range(globalDepth):
            #     print " ",
            # print "(%s waiting for parent)" % namespace
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

        # for i in range(globalDepth):
        #     print " ",
        # print str(namespace)
        logger.info(str(namespace))

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
        
        # get the parcel item ...
        parcel = self.repo.findPath(repoPath)

        # ... and, during the schema pass, make sure it
        # has its namespace assigned
        if self.schemaPhase:
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
        logger.error(msg)
        print
        if self.currentXMLFile:
            msg = "   File %s" % self.currentXMLFile
            print msg
            logger.error(msg)
        if self.currentXMLLine:
            msg = "   Line %d" % self.currentXMLLine
            print msg
            logger.error(msg)
        if self.currentExplanation:
            msg = "   Reason: %s" % self.currentExplanation
            print msg
            logger.error(msg)
        else:
            msg = "   Reason not recorded"
            print msg
            logger.error(msg)
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

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.begin("Load parcels")

        try:
            self.resetState()
            logger.info("Scanning parcels...")
            self.__scanParcels()
            logger.info("...done")
            
            self.__parcelsWithData = []
            self.__delayedOperations = []

            if not namespaces and self.__parcelsToLoad:
                namespaces = self.__parcelsToLoad

            self.resetState()
            if namespaces:
                self.schemaPhase = True
                logger.info("Loading Schema items from parcels...")
                for namespace in namespaces:
                    parcel = self.__loadParcel(namespace)
                    parcel.modifiedOn = datetime.now()
                logger.info("...done")
                
            self.resetState()
            namespaces = self.__parcelsWithData
            # At this point (the non-schema item pass), we want to reload
            # all parcels that contained data
            self.__parcelsToReload[:] = namespaces
            if (len(namespaces) > 0):
                self.schemaPhase = False
                logger.info("Loading other items from parcels...")
                for namespace in namespaces:
                    parcel = self.__loadParcel(namespace)
                logger.info("...done")

            self.__parcelsWithData = None
            
            for (item, file, line, call, arguments, keywords) in self.__delayedOperations:
                try:
                    if keywords == None:
                        call(*arguments)
                    else:
                        call(*arguments, **keywords)
                except Exception, e:
                    self.saveState(file, line)
                    explanation = "Unable to perform assignment: %s" % e
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)

            self.__delayedOperations = None
            
            self.resetState()
            logger.info("Starting parcels...")
            root = self.repo.findPath("//parcels")
            for parcel in self.__walkParcels(root):
                parcel.startupParcel()
            logger.info("...done")
            self.resetState()

        except:
            self.__displayError()
            raise

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.end("Load parcels")
        
    def handleKind(self, handler, kind):
        """
        Callback for ParcelItemManager to determine whether or not
        to handle (i.e. add to repository, or update existing
        repository instance) a given Kind while processing a
        parcel.xml. Used to make sure only schema items get
        added/updated during the first pass of parcel parsing,
        and the rest handled during the second pass.
        """
        
        isSchemaKind = (str(kind.itsPath[:2]) == "//Schema")
        
        result = (isSchemaKind == self.schemaPhase)

        # If the handler has encountered a non-schema item,
        # during the first pass, save off its namespace for
        # the second pass in loadParcels().
        if self.schemaPhase and \
           not result and \
           not handler.namespace in self.__parcelsWithData:
            self.__parcelsWithData.append(handler.namespace)
            
        return result
        
    def addDelayedCall(self, item, file, line, call, args, keywords):
        self.__delayedOperations.append((item, file, line, call, args, keywords))

    def performCopyOperation(self, reference, copyName, item, attributeName):
        # We may be reloading, so if the copy is already there,
        # remove it and re-copy
        existingCopy = item.findPath(copyName)
        if existingCopy is not None:
            existingCopy.delete(recursive=True)

        # (either) Copy the item using cloud-copy:

        copy = reference.copy(name=copyName, parent=item, cloudAlias="copying")

        # (or) Copy the item using attribute-copy:
        # copy = reference.copy(name=copyName, parent=item)
        if copy == None:
            explanation = \
                ("Unable to make copy named '%s' for attribute '%s'. " + 
                "Maybe the original was moved/deleted?") % \
                (copyName, attributeName)
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        item.addValue(attributeName, copy)
        
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
        self.createdOn = datetime.now()
        self.modifiedOn = self.createdOn

    def _fillItem(self, name, parent, kind, **kwds):
        super(Parcel, self)._fillItem(name, parent, kind, **kwds)

    def startupParcel(self):
        """
        Method called at the end of loadParcels().  Parcel items can perform
        whatever non-persisted setup they need to do.
        """
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

class ParcelXMLElement:
    """A helper class to track values for a given element inside
    a parcel.xml file.
    """
    
    def __init__(self, namespaceUri, elementName, attributes, elementType,
         item, value, assignments, reloading):
        self.namespaceUri = namespaceUri
        self.elementName = elementName
        self.attributes = attributes.copy()
        self.elementType = elementType
        self.item = item
        self.value = value
        self.assignments = assignments
        self.reloading = reloading
        

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class ParcelItemHandler(xml.sax.ContentHandler):
    """ A SAX2 ContentHandler responsible for loading items into the 
        repository.
    """
    _DELAYED_REFERENCE  = 0
    _DELAYED_LITERAL    = 1
    _DELAYED_UUIDOF     = 2
    _DELAYED_RESET      = 3

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
        self.elementStack = []

        # Keep track of namespace prefixes
        self.mapping = {}

        # Save a list of items and attributes, wire them up later
        # to be able to handle forward references
        self.delayedAssignments = []

        # For debugging, save a list of items we've generated for this file
        self.itemsCreated = []

        # Get the parcel's parent
        parentRepoPath = self.repoPath[:self.repoPath.rfind('/')]
        self.parcelParent = self.repository.findPath(parentRepoPath)

    def endDocument(self):
        """SAX2 callback at the end of the document"""

        # We've delayed loading the references until the end of the file.
        # Wire up attribute/reference pairs to the items.
        for (item, attributes) in self.delayedAssignments:
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

        currentElement = self.elementStack[-1]

        if currentElement.elementType in ('Attribute', 'Subattribute'):
            if currentElement.value is None:
                if len(content.strip()) > 0: currentElement.value = ''

            if type(currentElement.value) in (str, unicode):
                currentElement.value += content
                
    def __getCurrentItem(self):
        """Returns the most recent item in self's elementStack"""
        
        for index in range(0, len(self.elementStack)):
            item = self.elementStack[-index - 1].item
            if item is not None:
                return item
        return None
        
        
    def startElementNS(self, (uri, local), qname, attrs):
        """SAX2 callback for the beginning of a tag"""

        self.saveState()

        if not uri:
            explanation = "Element not properly prefixed (%s)" % local
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        currentItem = None
        currentValue = None

        # Find the kind represented by the tag (uri, local). The
        # parser has already mapped the prefix to the namespace (uri).
        kind = self.findItem(uri, local, self.locator.getLineNumber())
        nameString = None
        if attrs.has_key((None, 'itemName')):
            print "Deprecation warning: 'itemName' should be 'itsName' at", \
             self.locator.getSystemId(), self.locator.getLineNumber()
            nameString = attrs.getValue((None, 'itemName'))
        elif attrs.has_key((None, 'itsName')):
            nameString = attrs.getValue((None, 'itsName'))
            
        
        if kind and kind.itsKind.itsUUID == self.manager.kindUUID:
            element = 'Item'

            if attrs.has_key((None, 'itemClass')):
                classString = attrs.getValue((None, 'itemClass'))
            else:
                classString = None

            # If we have the document root, use the parcel parent.
            # Otherwise, the currentItem is the parent.
            parent = self.__getCurrentItem()
            if parent is None:
                parent = self.parcelParent
                lastComponent = self.repoPath.split('/')[-1]

                # A top-level anonymous Parcel item has an implicit
                # itsName of lastComponent here.
                if nameString is None:
                    nameString = lastComponent
                # <http://bugzilla.osafoundation.org/show_bug.cgi?id=2495>
                # Make sure that the top-level parcel's itsName
                # actually matches where it's going in the repository.
                # Otherwise, it's possible to run into an infinite
                # recursion here.
                elif nameString != lastComponent:
                    explanation = "Parcel's itsName '%s' doesn't match last component of repository path '%s'" % \
                                (nameString, self.repoPath)
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)


            self.currentAssignments = []

            if not self.manager.handleKind(self, kind):
                element = 'Ignore'
                
            # If the item already exists, we're reloading the item
            currentItem = parent.getItemChild(nameString)

            if currentItem is not None:
                try:
                    index = self.itemsCreated.index(currentItem)
                    explanation = \
                       "Child '%s' of item '%s' is already in this parcel" % \
                       (nameString, self.itemsCreated[index].itsPath)
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)
                except ValueError:
                   self.reloadingCurrentItem = True
                   self.itemsCreated.append(currentItem) # ensure we'll catch dupe reloads
            else:
                self.reloadingCurrentItem = False
                    
                if element is not 'Ignore':
                    currentItem = self.createItem(kind, parent,
                                                  nameString, classString)

        elif nameString:
            
            # We have an itsName, but for some reason we can't figure out
            # the Kind of this item. Either it doesn't exist...
            if kind is None:
                explanation = "Kind doesn't exist: %s:%s" % (uri, local)
            # ... or it isn't a Kind at all.
            else:
                explanation = "Expected a kind: %s:%s" % (uri, local)
                
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        elif len(self.elementStack) > 0 and \
             self.elementStack[-1].elementType == 'Ignore':
            # If we're ignoring the current item, ignore its attributes, etc
            # as well.
            element = 'Ignore'

        elif attrs.has_key((None, 'uuidOf')):
            # We need to get the UUID of the target item and assign it
            # to the attribute
            element = 'UuidOf'
            currentValue = attrs.getValue((None, 'uuidOf'))
            self.currentCopyName = None

        elif attrs.has_key((None, 'itemref')):
            # If it has an itemref, assume its a reference attribute
            element = 'Reference'
            currentValue = attrs.getValue((None, 'itemref'))
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
            print "Deprecation warning: 'ref' should be 'itemref' at", \
             self.locator.getSystemId(), self.locator.getLineNumber()
            element = 'Reference'
            currentValue = attrs.getValue((None, 'ref'))
            if attrs.has_key((None, 'copy')):
                self.currentCopyName = attrs.getValue((None, 'copy'))
            else:
                self.currentCopyName = None
            if attrs.has_key((None, 'alias')):
                self.currentAliasName = attrs.getValue((None, 'alias'))
            else:
                self.currentAliasName = None

        else:
            # Otherwise, assume it's a literal attribute
            element = 'Attribute'
            
            # ... except in some special cases!
            
            if len(self.elementStack) > 0:

                if self.elementStack[-1].elementType in ('Attribute', 'Subattribute'):
                    element = 'Subattribute'

            if attrs.has_key((None, 'value')):
                currentValue = attrs.getValue((None, 'value'))
            else:
                item = self.__getCurrentItem()
                
                if item is not None:
                    itemType = self._getTypeForAttribute(item, uri, local, attrs)
                    
                    if itemType is not None and \
                       itemType.itsKind.itsUUID == self.manager.kindUUID:
                        currentItem = self.createItem(itemType, item,
                                                      None, None)
                        currentValue = currentItem

        # Add the tag to our context stack
        self.elementStack.append(ParcelXMLElement(uri, local, attrs,
                          element, currentItem,
                          currentValue,
                          self.currentAssignments,
                          self.reloadingCurrentItem))

    def _getTypeForAttribute(self, currentItem,
                             elementUri, elementLocal, elementAttrs):
        resultType = None
        
        if elementAttrs.has_key((None, 'type')):
            # Store the full path to the type item
            (typeNamespace, typeName) = \
             self.getNamespaceName(elementAttrs.getValue((None, 'type')))
            resultType = self.manager.lookup(typeNamespace, typeName)
            if resultType is None:
                explanation = \
                 "Type doesn't exist: %s:%s" % (typeNamespace, typeName)
                self.saveExplanation(explanation)
                raise ParcelException(explanation)
        
        # "initialValue", regrettably, is a special case. In many cases, we
        # don't know enough about its Kind to be able to figure out the correct
        # type (eg, we need to know <type> and possibly <cardinality>), but
        # due to the delayed assignment mechanism, these aren't known at the
        # time this method is called.
        #
        # One way to fix this would be to parse "initialValue" when
        # self.schemaPhase is False. (Or change Manager.handleKind() to
        # be able to reject attributes as well as kinds).
        if elementLocal != "initialValue":
            
            if resultType is None:
                #
                # Possibly element is pointing to an attribute
                # of currentItem
                #
                if currentItem is None:
                    explanation = "Neither attribute type or item specified"
                    self.saveExplanation(explanation)
                    raise ParcelException(explanation)

                kindItem = currentItem.itsKind
                try:
                    resultType = kindItem.getAttribute(elementLocal)
                except AttributeError:
                    resultType = None

            if resultType is None:
                #
                # See what the (elementUri, elementLocal) pair point to.
                # Hopefully, it's either some known attribute of the
                # currentItem, or a type (including kinds).
                resultType = self.manager.lookup(elementUri, elementLocal)

            if resultType is None:
                explanation = \
                            "Kind %s does not have the attribute '%s'" \
                            % (kindItem.itsPath, elementLocal)
                self.saveExplanation(explanation)
                raise ParcelException(explanation)
                

            # If it's an Attribute, try to figure out the appropriate
            # type
            if isinstance(resultType,Attribute):
                try:
                    resultType = resultType.type
                except Exception, e:
                    explanation = \
                        "Unable to determine type of attribute '%s' for value '%s':'%s'" % \
                        ( resultType.itsPath, currentElement.value, e )
                    self.saveExplanation(explanation)
                    raise
                
        return resultType



    def endElementNS(self, (uri, local), qname):
        """SAX2 callback for the end of a tag"""

        self.saveState()

        elementUri = uri
        elementLocal = local
        
        currentElement = self.elementStack[-1]
        currentItem = self.__getCurrentItem()

        # We have an item, add the collected attributes to the list
        if currentElement.elementType == 'Item':
            if currentItem is not None:
                self.delayedAssignments.append((currentItem, \
                                                self.currentAssignments))
    
            # Look at the tags stack for the parent item, and the
            # parent references
            if len(self.elementStack) >= 2:
                nextElement = self.elementStack[-2]
                self.currentAssignments = nextElement.assignments
                self.reloadingCurrentItem = nextElement.reloading
        elif currentElement.elementType in ('Attribute', 'Subattribute'):
            currentType = self._getTypeForAttribute(currentItem,
                                                    elementUri,
                                                    elementLocal, 
                                                    currentElement.attributes)
            # For non-top-level attributes (i.e. literals), make sure we
            # propagate the value up the tags stack.
            if (len(self.elementStack) >= 2):
                nextElement = self.elementStack[-2]
                if nextElement.value is None: nextElement.value = []
                if currentElement.elementType is 'Subattribute':
                    currentElement.value = self.makeValue(currentItem, \
                                                  currentType, elementLocal, \
                                                  currentElement.value)
                if type(nextElement.value) is list:
                    nextElement.value.append(currentElement.value)
                    

        if currentItem is not None and \
           not currentElement.elementType in ('Ignore', 'Item', 'Subattribute'): \
            # This is a top-level assignment; Delay the assignment
            # until we reach the end of the xml document
            
            if currentElement.value is None:
                currentElement.value = ''

            # We are deprecating defaultValue:
            if currentElement.elementName == "defaultValue":
                explanation = \
                 "The 'defaultValue' attribute has been deprecated"
                self.saveExplanation(explanation)
                raise ParcelException(explanation)

            # Initialize the assignment with values shared by all types:
            assignment = {
               "reloading"  : currentElement.reloading,
               "attrName"   : currentElement.elementName,
               "key"        : None,
               "copyName"   : None,
               "file"       : self.locator.getSystemId(),
               "line"       : self.locator.getLineNumber()
            }
            
            if currentElement.elementType == 'Reference':
                (namespace, name) = self.getNamespaceName(currentElement.value)
                assignment["assignType"] = self._DELAYED_REFERENCE
                assignment["namespace"] = namespace
                assignment["name"] = name
                assignment["copyName"] = self.currentCopyName
                assignment["aliasName"] = self.currentAliasName

            elif currentElement.elementType == 'UuidOf':
                (namespace, name) = self.getNamespaceName(currentElement.value)
                assignment["assignType"] = self._DELAYED_UUIDOF
                assignment["namespace"] = namespace
                assignment["name"] = name
                
            elif currentElement.elementType == 'Attribute': # A scalar or a list
                assignment["assignType"] = self._DELAYED_LITERAL
                assignment["valueType"] = currentType
                assignment["value"] = currentElement.value
                if currentElement.attributes.has_key((None, "key")):
                    # a cardinality=dict attribute
                    assignment["key"] = \
                              currentElement.attributes.getValue((None, 'key'))
            
            # Store this assignment
            self.currentAssignments.append(assignment)

        self.elementStack.pop()

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
        if uri != self.namespace and self.depCallback is not None:
            self.depCallback(uri)

        self.mapping[prefix] = None

    def itemPostProcess(self, item):
        """ Perform any post-creation-processing such as ensuring a superkind
            has been assigned to a kind, or local attributes have been hooked
            up """

        if isinstance(item,Attribute) and isinstance(item.itsParent,Kind):
            # Hook the attribute up to its containing kind
            if item not in getattr(item.itsParent,'attributes',()):
                item.itsParent.addValue("attributes",item,alias=item.itsName)

        elif isinstance(item,Kind):
            # Assign superKind of //Schema/Core/Item if none assigned
            if not item.hasLocalAttributeValue("superKinds") or \
             (len(item.superKinds) == 0):
                item.addValue("superKinds",
                 self.repository.findUUID(self.manager.itemUUID))

    def makeValue(self, item, valueType, attributeName, rawValue):
        """ Creates a value from a string, based on the type
            of the attribute.
        """

        value = rawValue
        
        if type(value) in (unicode, str):
            try:
                value = valueType.makeValue(value)
            except Exception, e:
                explanation = \
                            "Unable to create value for type '%s' from string '%s': %s" % \
                            ( valueType.itsPath, value, e )
                self.saveExplanation(explanation)
                raise
        elif type(value) is list:
            try:
                value = valueType.makeCollection(value)
            except Exception, e:
                explanation = \
                            "Unable to create value for type '%s' from sub-items '%s': %s" % \
                            ( valueType.itsPath, value, e )
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
        if item is None and self.depCallback is not None:
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

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.begin("Creating items")
        
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

        #@@@Temporary testing tool written by Morgen -- DJA
        if timing: util.timing.end("Creating items")

        if item is None:
            explanation = "Item not created"
            self.saveExplanation(explanation)
            raise ParcelException(explanation)

        self.itemsCreated.append(item)

        return item

    def completeAssignments(self, item, assignments):
        """ Perform all the delayed attribute assignments for an item """

        (old, new) = ValueSet.getValueSets(item)
        copiedAnAssignment = False

        # For bug 3361, improper handling of assignments when an initialValue
        # is a list/tuple.  The fix is to blow away the initialValue of an
        # item's attribute the first time parcel.xml sets the value.
        seenAttributes = {}

        for assignment in assignments:
            assignmentCallable = None
            assignmentArgs = None
            assignmentKeywords = None

            attributeName = str(assignment["attrName"])
            reloading = assignment["reloading"]
            line = assignment["line"]
            file = assignment["file"]
            if assignment.has_key("key"):
                key = assignment["key"]
            else:
                key = None


            self.saveState(line=line, file=file)

            #@@@Temporary testing tool written by Morgen -- DJA
            if timing: util.timing.begin("Attribute assignments")
            
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
                        copiedAnAssignment = True
                        assignmentCallable = self.manager.performCopyOperation
                        assignmentArgs = (reference, copyName, item, attributeName,)
                    elif attributeName == 'inverseAttribute':
                        assignmentCallable = item.addValue
                        assignmentArgs = ('otherName', reference.itsName, )
                    elif attributeName == 'displayAttribute':
                        assignmentCallable = item.addValue
                        assignmentArgs = ('displayAttribute', reference.itsName, )
                    elif attributeName == 'attributes':
                        assignmentCallable = item.addValue
                        assignmentArgs = ('attributes', reference, )
                        assignmentKeywords = { 'alias' : reference.itsName }
                    else:
                        assignmentCallable = item.addValue
                        assignmentArgs = (attributeName, reference, )
                        if aliasName:
                             assignmentKeywords = { 'alias': aliasName }

                    if reloading:
                        if reference is None:
                            displayPath = "None"
                        else:
                            displayPath = reference.itsPath
                        logger.debug("Reload: item %s, assigning %s = %s" % \
                         (item.itsPath, attributeName, displayPath))

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
                    
                    assignmentCallable = item.addValue
                    assignmentArgs = (attributeName, reference.itsUUID, )

                    if reloading:
                        logger.debug("Reload: item %s, assigning %s = UUID of %s" % \
                         (item.itsPath, attributeName, reference.itsPath))

                # Record this assignment in the new set of assignments
                new.addAssignment(assignmentTuple)

            elif assignment["assignType"] == self._DELAYED_LITERAL:

                rawValue = assignment["value"]
                valueType = assignment["valueType"]

                if attributeName == "initialValue" and rawValue == "":
                    # Set a reasonable default for an empty <initialValue>
                    # attribute.
                    cardinality = item.cardinality
            
                    if cardinality == "list":
                        value = []
                    elif cardinality == "dict":
                        value = {}
                    else:
                        value = rawValue

                else:
                    if valueType is None:
                        try:
                            valueType = item.type
                        except Exception, e:
                            explanation = \
                                        "Unable to determine type of attribute '%s' for value '%s':'%s'" % \
                                        ( item.itsPath, assignment["value"], e )
                            self.saveExplanation(explanation)
                            raise

                    value = self.makeValue(item, valueType, attributeName, rawValue)
                
                
                #@@@ Weird behaviour of Lobs here mean we would run into
                # trouble if we stuck value and not rawValue in
                # assignmentTuple.
                assignmentTuple = (attributeName, rawValue, key)

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

                    if key is not None:
                        assignmentCallable = item.setValue
                        assignmentArgs = (attributeName, value, key, )
                        if reloading:
                            logger.debug("Reload: item %s, assigning %s[%s] = " \
                             "'%s'" % \
                             (item.itsPath, attributeName, key, value))
                    else:
                        assignmentCallable = item.addValue
                        assignmentArgs = (attributeName, value, )
                        if reloading:
                            logger.debug("Reload: item %s, assigning %s = '%s'" % \
                             (item.itsPath, attributeName, value))

                # If this is the first time we're assigning to this
                # attribute for this item within this method, let's
                # remove whatever initialValue is there.
                # Note: If in reloading mode, removing the value completely
                # isn't safe because of changes that could have been made
                # during a previous run (outside of parcel.xml).  Therefore
                # in reload mode be aware that if you didn't previously have
                # an assignment to a given list attribute in XML, but now you
                # have added one, the item's attribute value is going to be
                # the initialValue list plus whatever attributes you have
                # added in XML (which actually makes sense because by reloading
                # you are modifying an existing item, not creating a new one).
                if not reloading and not seenAttributes.has_key(attributeName):
                    if hasattr(item, attributeName):
                        try:
                            item.removeAttributeValue(attributeName)
                        except:
                            # This could fail for various reasons, none of
                            # which are important
                            pass
                    seenAttributes[attributeName] = 1

                # Record this assignment in the new set of assignments
                new.addAssignment(assignmentTuple)


                
            if assignmentCallable is not None:
                if copiedAnAssignment:
                    self.manager.addDelayedCall(item, file, line, assignmentCallable, assignmentArgs, assignmentKeywords)
                else:
                    try:
                        if assignmentKeywords is not None:
                            assignmentCallable(*assignmentArgs, **assignmentKeywords)
                        else:
                            assignmentCallable(*assignmentArgs)
                    except Exception, e:
                        explanation = "Couldn't add value to item (%s)" % e
                        self.saveExplanation(explanation)
                        raise ParcelException(explanation)

            #@@@Temporary testing tool written by Morgen -- DJA
            if timing: util.timing.end("Attribute assignments")

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
            #
            # Note that it's possible (for anonymous items)
            # to have an itsName of None. So, we don't want
            # to build up the relative path to each item by using
            # str(item.itsName), or item.itsName, because those
            # return "None", or None. Instead, we use item.itsPath[-1]:
            # that returns the UUID-generated path component the
            # repository uses for anonymous items, and is suitable for
            # tracking down items for comparisons.
            #
            relPath = item.itsPath[-1]
            parcel = item.itsParent
            while str(parcel.itsKind.itsPath) != "//Schema/Core/Parcel":
                relPath = "%s/%s" % (parcel.itsPath[-1], relPath)
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
                logger.debug("Reload: item %s, unassigning %s[%s] = '%s'" % \
                 (self.item.itsPath, attrName, key, value))
                self.item.removeValue(attrName, key=key)
            elif card == "list":
                # First, see if this is a ref collection, since we handle those
                # differently; to remove an item from a ref collection, we use
                # remove() which takes an item parameter -- therefore we
                # first need to findUUID() the item.
                if self.item.getAttributeAspect(attrName, "otherName"):
                    attr = self.item.getAttributeValue(attrName)
                    # value is a UUID -- let's load the associated item and then
                    # remove it from this collection
                    otherItem = self.item.findUUID(value)
                    attr.remove(otherItem)
                    logger.debug("Reload: item %s, unassigning %s = '%s'" % \
                     (self.item.itsPath, attrName, otherItem.itsPath))
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
                            logger.debug("Reload: item %s, unassigning %s = '%s'" % \
                             (self.item.itsPath, attrName, listValue.itsPath))
                    else:
                        if str(listValue) == value:
                            list.remove(listValue)
                            logger.debug("Reload: item %s, unassigning %s = '%s'" % \
                             (self.item.itsPath, attrName, value))
            else:
                attrValue = self.item.getAttributeValue(attrName)
                if isinstance(attrValue, repository.item.Item.Item):
                    if str(attrValue.itsUUID) == value:
                        self.item.removeAttributeValue(attrName)
                        logger.debug("Reload: item %s, unassigning %s = '%s'" % \
                         (self.item.itsPath, attrName, attrValue.itsPath))
                else:
                    if str(attrValue) == value:
                        self.item.removeAttributeValue(attrName)
                        logger.debug("Reload: item %s, unassigning %s = '%s'" % \
                         (self.item.itsPath, attrName, value))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def PrintItem(path, rep, recursive=False, level=0):
    """
    A pretty-printer for repository items.

    Example::

        repository.parcel.PrintItem("//Schema", repository)

    @param rep: The repository object to use
    @type rep: L{repository.persistence.Repository}
    @param recursive: Whether to also display child items or not (default=False)
    @type recursive:  Boolean
    """

    for i in xrange(level):
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
        for i in xrange(level+2):
            print " ",
        print "attributes for this kind:"

        displayedAttrs = { }
        for (name, attr, k) in item.iterAttributes():
            displayedAttrs[name] = attr

        keys = displayedAttrs.keys()
        keys.sort()
        for key in keys:
            for k in xrange(level+4):
                print " ",
            print "%s %s" % ( key, displayedAttrs[key].itsPath )

    displayedAttrs = { }
    for (name, value) in item.iterAttributeValues():
        displayedAttrs[name] = value

    keys = displayedAttrs.keys()
    keys.sort()
    for name in keys:
        value = displayedAttrs[name]

        if name in ("attributes", "notFoundAttributes",
                    "inheritedAttributes", "kind"):
            pass

        if isinstance(value, RefList):
            for i in xrange(level+2):
                print " ",

            print "%s: (list)" % name
            for j in value:
                for k in xrange(level+4):
                    print " ",
                print j.itsPath

        elif isinstance(value, dict):
            for i in xrange(level+2):
                print " ",

            print "%s: (dict)" % name
            for key in value.keys():
                for k in xrange(level+4):
                    print " ",
                print "%s:" % key, value[key]

        elif isinstance(value, list):
            for i in xrange(level+2):
                print " ",

            print "%s: (list)" % name
            for j in value:
                for k in xrange(level+4):
                    print " ",
                print j

        else:
            for i in xrange(level+2):
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

import schema

