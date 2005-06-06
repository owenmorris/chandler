Allowed = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application.Parcel
import osaf.mail.message
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.contacts.Contacts as Contacts
import osaf.contentmodel.calendar.Calendar as Calendar
from osaf.contentmodel.ItemCollection import ItemCollection
import osaf.current.Current as Current
from chandlerdb.util.uuid import UUID
import application.dialogs.PublishCollection
from repository.item.Query import KindQuery
from repository.util.Lob import Lob
from repository.item.Item import Item
from repository.schema.Types import Type
import repository.query.Query as Query
import M2Crypto.BIO
import repository
import logging
import wx
import time, StringIO, urlparse, libxml2, os
import chandlerdb
import zanshin.webdav
import WebDAV
import zanshin.util
import twisted.web.http
import AccountInfoPrompt

logger = logging.getLogger('Sharing')
logger.setLevel(logging.INFO)


SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
EVENTS = "http://osafoundation.org/parcels/osaf/framework/blocks/Events"
CONTENT = "http://osafoundation.org/parcels/osaf/contentmodel"

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Share(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/Share"

    """ Represents a set of shared items, encapsulating contents, location,
        access method, data format, sharer and sharees. """

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 contents=None, conduit=None, format=None):

        super(Share, self).__init__(name, parent, kind, view)

        self.contents = contents # ItemCollection
        try:
            self.displayName = contents.displayName
        except:
            self.displayName = ""

        self.setConduit(conduit)
        self.format = format

        self.sharer = None
        self.sharees = []
        self.filterKinds = []

    def setConduit(self, conduit):
        self.conduit = conduit
        self.conduit.share = self

    def create(self):
        self.conduit.create()

    def destroy(self):
        self.conduit.destroy()

    def open(self):
        self.conduit.open()

    def close(self):
        self.conduit.close()

    def sync(self):
        if self.mode in ('get', 'both'):
            items = self.conduit.get()
        else:
            items = []

        # @@@MOR For now, since server changes clobber local changes, don't
        # bother putting an item we have just fetched

        if self.mode in ('put', 'both'):
            self.conduit.put(skipItems=items)

    def put(self):
        if self.mode in ('put', 'both'):
            self.conduit.put()

    def get(self):
        if self.mode in ('get', 'both'):
            self.conduit.get()

    def exists(self):
        return self.conduit.exists()

    def getLocation(self):
        return self.conduit.getLocation()
    
    
class OneTimeShare(Share):
    """Delete format, conduit, and share after the first get or put."""

    def remove(self):
        self.conduit.delete(True)
        self.format.delete(True)
        self.delete(True)

    def put(self):
        super(OneTimeShare, self).put()
        collection = self.contents
        self.remove()
        return collection

    def get(self):
        super(OneTimeShare, self).get()
        collection = self.contents
        self.remove()
        return collection



class ShareConduit(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ShareConduit"

    """ Transfers items in and out. """

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(ShareConduit, self).__init__(name, parent, kind, view)

        self.__clearManifest()
        
        # 'marker' is an item which exists only to keep track of the repository
        # view version number at the time of last sync
        self.marker = Item('marker', self, None)
        
    def setShare(self, share):
        self.share = share

    def __conditionalPutItem(self, item, skipItems=None):
        # assumes that self.resourceList has been populated
        skip = False
        if skipItems and item in skipItems:
            skip = True
        if not skip:
            externalItemExists = self.__externalItemExists(item)
            itemVersion = item.getVersion()
            prevVersion = self.marker.getVersion()
            if itemVersion > prevVersion or not externalItemExists:
                logger.info("...putting '%s' %s (%d vs %d) (on server: %s)" % \
                 (item.getItemDisplayName(), item.itsUUID, itemVersion,
                 prevVersion, externalItemExists))
                data = self._putItem(item)
                if data is not None:
                    self.__addToManifest(item, data)
                    logger.info("...done, data: %s, version: %d" %
                     (data, itemVersion))
            else:
                pass
                # logger.info("Item is up to date")
        try:
            del self.resourceList[self._getItemPath(item)]
        except:
            logger.info("...external item %s didn't previously exist" % self._getItemPath(item))

    def put(self, skipItems=None):
        """ Transfer entire 'contents', transformed, to server. """

        self.connect()

        location = self.getLocation()
        logger.info("Starting PUT of %s" % (location))

        # @@@DLD bug 1998 - would refresh do here?
        self.itsView.commit() # Make sure locally modified items have had
                              # their version numbers bumped up.

        filterKinds = None
        if len(self.share.filterKinds) > 0:
            filterKinds = []
            for path in self.share.filterKinds:
                filterKinds.append(self.itsView.findPath(path))

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:

            self.resourceList = self._getResourceList(location)

            # If we're sharing a collection, put the collection's items
            # individually:
            if isinstance(self.share.contents, ItemCollection):
                for item in self.share.contents:

                    if item.isPrivate:
                        continue

                    if filterKinds is not None:
                        match = False
                        for kind in filterKinds:
                            if item.isItemOf(kind):
                                match = True
                                break

                        if not match:
                            continue

                    self.__conditionalPutItem(item, skipItems)

            self.__conditionalPutItem(self.share, skipItems)

            for (itemPath, value) in self.resourceList.iteritems():
                self._deleteItem(itemPath)
                self.__removeFromManifest(itemPath)

        elif style == ImportExportFormat.STYLE_SINGLE:
            #@@@MOR This should be beefed up to only publish if at least one
            # of the items has changed.
            self._putItem(self.share)

        # dirty our marker
        self.marker.setDirty(Item.NDIRTY)

        # @@@DLD bug 1998 - why do we need a second commit here?
        # Is this just for the setDirty above?
        self.itsView.commit()

        self.disconnect()

        logger.info("Finished PUT of %s" % (location))

    def __conditionalGetItem(self, itemPath, into=None):
        # assumes self.resourceList is populated

        if itemPath not in self.resourceList:
            logger.info("...Not on server: %s" % itemPath)
            return None

        if not self.__haveLatest(itemPath):
            # logger.info("...getting: %s" % itemPath)
            (item, data) = self._getItem(itemPath, into)

            if item is not None:
                self.__addToManifest(item, data)
                logger.info("...imported '%s' %s, data: %s" % \
                 (item.getItemDisplayName(), item, data))
                return item

            logger.info("...NOT able to import '%s'" % itemPath)
            msg = "Not able to import '%s'" % itemPath
            raise SharingError(message=msg)
        else:
            pass
            # logger.info("...skipping")

        return None

    def get(self):

        self.connect()

        location = self.getLocation()
        logger.info("Starting GET of %s" % (location))

        if not self.exists():
           raise NotFound(message="%s does not exist" % location)

        retrievedItems = []
        self.resourceList = self._getResourceList(location)

        self.__resetSeen()

        itemPath = self._getItemPath(self.share)
        item = self.__conditionalGetItem(itemPath, into=self.share)

        if item is not None:
            retrievedItems.append(item)
        self.__setSeen(itemPath)
        try:
            del self.resourceList[itemPath]
        except:
            pass

        # If share.contents is an ItemCollection, treat other resources as
        # items to add to the collection:

        if isinstance(self.share.contents, ItemCollection):

            filterKinds = None
            if len(self.share.filterKinds) > 0:
                filterKinds = []
                for path in self.share.filterKinds:
                    filterKinds.append(self.itsView.findPath(path))

            # Conditionally fetch items, and add them to collection
            for itemPath in self.resourceList:
                item = self.__conditionalGetItem(itemPath)
                if item is not None:
                    self.share.contents.add(item)
                    retrievedItems.append(item)
                self.__setSeen(itemPath)

            # When first importing a collection, name it after the share
            if not hasattr(self.share.contents, 'displayName'):
                self.share.contents.displayName = self.share.displayName

            # If an item was prevsiously on the server (it was in our manifest)
            # but is no longer on the server, remove it from the collection
            # locally:
            toRemove = []
            for unseenPath in self.__iterUnseen():
                uuid = self.manifest[unseenPath]['uuid']
                item = self.itsView.findUUID(uuid)
                if item is not None:

                    # If an item has disappeared from the server, only remove
                    # it locally if it matches the current share filter.

                    removeLocally = True

                    if filterKinds is not None:
                        match = False
                        for kind in filterKinds:
                            if item.isItemOf(kind):
                                match = True
                                break
                        if match is False:
                            removeLocally = False

                    if removeLocally:
                        logger.info("...removing %s from collection" % item)
                        self.share.contents.remove(item)

                    # In either case, remove from manifest
                    toRemove.append(unseenPath)

            for removePath in toRemove:
                self.__removeFromManifest(removePath)

        # @@@DLD bug 1998 does this happen multiple times for a single collection share?
        self.itsView.commit()

        logger.info("Finished GET of %s" % location)

        self.disconnect()

        return retrievedItems

    # Methods that subclasses *must* implement:

    def getLocation(self):
        """ Return a string representing where the share is being exported
            to or imported from, such as a URL or a filesystem path
        """
        pass

    def _getItemPath(self, item):
        """ Return a string that uniquely identifies a resource in the remote
            share, such as a URL path or a filesystem path.  These strings
            will be used for accessing the manifest and resourceList dicts.
        """
        pass

    def _getResourceList(self, location):
        """ Return a dictionary representing what items exist in the remote
            share. """
        # 'location' is a location returned from getLocation
        # The returned dictionary should be keyed on a string that uniquely
        # identifies a resource in the remote share.  For example, a url
        # path or filesystem path.  The values of the dictionary should
        # be dictionaries of the format { 'data' : <string> } where <string>
        # is some piece of data that encapsulates version information for
        # the remote resources (such as a last modified date, or an ETag).
        pass

    def _putItem(self, item, where):
        """ Must implement """
        pass

    def _deleteItem(self, itemPath):
        """ Must implement """
        pass

    def _getItem(self, itemPath, into=None):
        """ Must implement """
        pass

    # Manifest mangement routines
    # The manifest keeps track of the state of shared items at the time of
    # last sync.  It is a dictionary keyed on "path" (not repo path, but
    # path at the external source), whose values are dictionaries containing
    # the item's internal UUID, external UUID, either a last-modified date
    # (if filesystem) or ETAG (if webdav), and the item's version (as in
    # what item.getVersion() returns)

    def __clearManifest(self):
        self.manifest = {}

    def __addToManifest(self, item, data):
        # data is an ETAG, or last modified date
        path = self._getItemPath(item)
        self.manifest[path] = {
         'uuid' : item.itsUUID,
         'data' : data,
        }


    def __removeFromManifest(self, path):
        try:
            del self.manifest[path]
        except:
            pass

    def __externalItemExists(self, item):
        itemPath = self._getItemPath(item)
        return itemPath in self.resourceList

    def __haveLatest(self, path, data=None):
        """ Do we have the latest copy of this item? """
        if data == None:
            data = self.resourceList[path]['data']
        try:
            record = self.manifest[path]
            if record['data'] == data:
                # logger.info("haveLatest: Yes (%s %s)" % (path, data))
                return True
            else:
                # print "MISMATCH: local=%s, remote=%s" % (record['data'], data)
                logger.info("...don't have latest (%s local:%s remote:%s)" % (path,
                 record['data'], data))
                return False
        except KeyError:
            pass
            # print "%s is not in manifest" % path
        logger.info("...don't yet have %s" % path)
        return False

    def __resetSeen(self):
        for value in self.manifest.itervalues():
            value['seen'] = False

    def __setSeen(self, path):
        try:
            self.manifest[path]['seen'] = True
        except:
            pass

    def __iterUnseen(self):
        for (path, value) in self.manifest.iteritems():
            if not value['seen']:
                yield path


    def connect(self):
        pass

    def disconnect(self):
        pass

    def exists(self):
        pass

    def create(self):
        """ Create the share on the server. """
        pass

    def destroy(self):
        """ Remove the share from the server. """
        pass

    def open(self):
        """ Open the share for access. """
        pass

    def close(self):
        """ Close the share. """
        pass


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class FileSystemConduit(ShareConduit):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/FileSystemConduit"

    SHAREFILE = "share.xml"

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 sharePath=None, shareName=None):
        super(FileSystemConduit, self).__init__(name, parent, kind, view)

        self.sharePath = sharePath
        self.shareName = shareName

        if not self.shareName:
            self.shareName = str(UUID())

        # @@@MOR What sort of processing should we do on sharePath for this
        # filesystem conduit?

        # @@@MOR Probably should remove any slashes, or warn if there are any?
        self.shareName = self.shareName.strip("/")

    def getLocation(self): # must implement
        if self.hasLocalAttributeValue("sharePath") and \
         self.hasLocalAttributeValue("shareName"):
            return os.path.join(self.sharePath, self.shareName)
        raise Misconfigured()

    def _getItemPath(self, item): # must implement
        extension = self.share.format.extension(item)
        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            if isinstance(item, Share):
                fileName = self.SHAREFILE
            else:
                fileName = "%s.%s" % (item.itsUUID, extension)
            return fileName

        elif style == ImportExportFormat.STYLE_SINGLE:
            return self.shareName

        else:
            print "@@@MOR Raise an exception here"

    def _putItem(self, item): # must implement
        path = self.__getItemFullPath(self._getItemPath(item))
        
        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            raise TransformationFailed(message=str(e))

        if text is None:
            return None
        out = file(path, 'wb') #outputting in binary mode to preserve ics CRLF
        out.write(text)
        out.close()
        stat = os.stat(path)
        return stat.st_mtime

    def _deleteItem(self, itemPath): # must implement
        path = self.__getItemFullPath(itemPath)

        logger.info("...removing from disk: %s" % path)
        os.remove(path)

    def _getItem(self, itemPath, into=None): # must implement
        # logger.info("Getting item: %s" % itemPath)
        path = self.__getItemFullPath(itemPath)

        extension = os.path.splitext(path)[1].strip(os.path.extsep)
        text = file(path).read()

        try:
            item = self.share.format.importProcess(text, extension=extension,
             item=into)
        except Exception, e:
            raise TransformationFailed(message=str(e))

        stat = os.stat(path)
        return (item, stat.st_mtime)

    def _getResourceList(self, location):
        fileList = {}

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            for filename in os.listdir(location):
                fullPath = os.path.join(location, filename)
                stat = os.stat(fullPath)
                fileList[filename] = { 'data' : stat.st_mtime }

        elif style == ImportExportFormat.STYLE_SINGLE:
            stat = os.stat(location)
            fileList[self.shareName] = { 'data' : stat.st_mtime }

        else:
            print "@@@MOR Raise an exception here"

        return fileList

    def __getItemFullPath(self, path):
        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            path = os.path.join(self.sharePath, self.shareName, path)
        elif style == ImportExportFormat.STYLE_SINGLE:
            path = os.path.join(self.sharePath, self.shareName)
        return path

        
        
    def exists(self):
        super(FileSystemConduit, self).exists()

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            return os.path.isdir(self.getLocation())
        elif style == ImportExportFormat.STYLE_SINGLE:
            return os.path.isfile(self.getLocation())
        else:
            print "@@@MOR Raise an exception here"

    def create(self):
        super(FileSystemConduit, self).create()

        if self.exists():
            raise AlreadyExists()

        if self.sharePath is None or not os.path.isdir(self.sharePath):
            raise Misconfigured(message="Share path is not set, or path doesn't exist")

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            path = self.getLocation()
            if not os.path.exists(path):
                os.mkdir(path)

    def destroy(self):
        super(FileSystemConduit, self).destroy()

        path = self.getLocation()

        if not self.exists():
            raise NotFound(message="%s does not exist" % path)

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            for filename in os.listdir(path):
                os.remove(os.path.join(path, filename))
            os.rmdir(path)
        elif style == ImportExportFormat.STYLE_SINGLE:
            os.remove(path)


    def open(self):
        super(FileSystemConduit, self).open()

        path = self.getLocation()

        if not self.exists():
            raise NotFound(message="%s does not exist" % path)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVConduit(ShareConduit):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/WebDAVConduit"

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 shareName=None, account=None, host=None, port=80,
                 sharePath=None, username="", password="", useSSL=False):
        super(WebDAVConduit, self).__init__(name, parent, kind, view)

        # Use account, if provided.  Otherwise use host, port, username,
        # password and useSSL parameters instead.
        self.account = account
        if account is None:
            self.host = host
            self.port = port
            self.sharePath = sharePath
            self.username = username
            self.password = password
            self.useSSL = useSSL

        if not shareName:
            self.shareName = str(UUID())
        else:
            # @@@MOR Probably should remove any slashes, or warn if there are
            # any?
            self.shareName = shareName.strip("/")

        self.onItemLoad()

    def onItemLoad(self, view=None):
        # view is ignored
        self.serverHandle = None

    def __getSettings(self):
        if self.account is None:
            return (self.host, self.port, self.sharePath.strip("/"),
                    self.username, self.password, self.useSSL)
        else:
            return (self.account.host, self.account.port,
                    self.account.path.strip("/"), self.account.username,
                    self.account.password, self.account.useSSL)

    def _getServerHandle(self):
        # @@@ [grant] Collections and the trailing / issue.
        if self.serverHandle == None:
            logger.info("...creating new webdav ServerHandle")
            (host, port, sharePath, username, password, useSSL) = \
            self.__getSettings()
            
            self.serverHandle = WebDAV.ChandlerServerHandle(host, port=port,
                username=username, password=password, useSSL=useSSL,
                repositoryView=self.itsView)
                
        return self.serverHandle

    def __releaseServerHandle(self):
        self.serverHandle = None

    def getLocation(self):  # must implement
        """ Return the url of the share """

        (host, port, sharePath, username, password, useSSL) = self.__getSettings()
        if useSSL:
            scheme = "https"
            defaultPort = 443
        else:
            scheme = "http"
            defaultPort = 80

        if port == defaultPort:
            url = "%s://%s" % (scheme, host)
        else:
            url = "%s://%s:%d" % (scheme, host, port)
        url = urlparse.urljoin(url, sharePath + "/")
        url = urlparse.urljoin(url, self.shareName)
        return url

    def _getItemPath(self, item): # must implement
        """ Return the path (not the full url) of an item given its external
        UUID """

        # (host, port, sharePath, username, password, useSSL) = self.__getSettings()
        extension = self.share.format.extension(item)
        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            if isinstance(item, Share):
                path = "share.xml"
                return path
            else:
                path = "%s.%s" % (item.itsUUID, extension)
                return path

        elif style == ImportExportFormat.STYLE_SINGLE:
            path = self.shareName
            return path

        else:
            print "Error" #@@@MOR Raise something

    def __getSharePath(self):
        return "/" + self.__getSettings()[2]
            
    def __resourceFromPath(self, path):

        serverHandle = self._getServerHandle()
        sharePath = self.__getSharePath()
        
        resourcePath = "%s/%s" % (sharePath, self.shareName)

        if self.share.format.fileStyle() == ImportExportFormat.STYLE_DIRECTORY:
            resourcePath += "/" + path

        return serverHandle.getResource(resourcePath)

    def exists(self):
        result = super(WebDAVConduit, self).exists()
        
        resource = self.__resourceFromPath("")

        try:
            result = zanshin.util.blockUntil(resource.exists)
        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(message=err.args[0])
        except M2Crypto.BIO.BIOError, err:
            message = "%s" % (err)
            raise CouldNotConnect(message=message)
        except zanshin.webdav.PermissionsError, err:
            message = "Not authorized to PUT %s" % self.getLocation()
            raise NotAllowed(message=err.message)
            
        return result

    def create(self):
        super(WebDAVConduit, self).create()
        
        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            url = self.getLocation()
            try:
                if url[-1] != '/': url += '/'
                resource = zanshin.util.blockUntil(self.serverHandle.mkcol, url)
            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(message=err.message)
            except M2Crypto.BIO.BIOError, err:
                message = "%s" % (err)
                raise CouldNotConnect(message=message)
    
            except zanshin.webdav.WebDAVError, err:
                if err.status == twisted.web.http.METHOD_NOT_ALLOWED:
                    # already exists
                    message = "Collection at %s already exists" % url
                    raise AlreadyExists(message=message)
    
                if err.status == twisted.web.http.UNAUTHORIZED:
                    # not authorized
                    message = "Not authorized to create collection %s" % url
                    raise NotAllowed(message=message)
    
                if err.status == twisted.web.http.CONFLICT:
                    # this happens if you try to create a collection within a
                    # nonexistent collection
                    message = "Parent collection for %s not found" % url
                    raise NotFound(message=message)
    
                if err.status == twisted.web.http.FORBIDDEN:
                    # the server doesn't allow the creation of a collection here
                    message = "Server doesn't allow the creation of collections at %s" % url
                    raise IllegalOperation(message=message)
    
                if err.status != twisted.web.http.CREATED:
                     message = "WebDAV error, status = %d" % err.status
                     raise IllegalOperation(message=message)

    def destroy(self):
        print " @@@MOR unimplemented"

    def open(self):
        super(WebDAVConduit, self).open()
        
    def __getContainerResource(self):
        
        serverHandle = self._getServerHandle()
        
        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            path = self.getLocation()
        else:
            path = self.__getSharePath()

        # Make sure we have a container
        if path and path[-1] != '/':
            path += '/'

        return serverHandle.getResource(path)
        

    def _putItem(self, item): # must implement
        """ putItem should publish an item and return etag/date, etc.
        """

        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            raise TransformationFailed(message=str(e))

        if text is None:
            return None

        itemName = self._getItemPath(item)
        container = self.__getContainerResource()
        
        try:
            newResource = zanshin.util.blockUntil(container.createFile,
                                itemName, body=text)
        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(message=err.message)
        except M2Crypto.BIO.BIOError, err:
            message = "%s" % (err)
            raise CouldNotConnect(message=message)
        # 201 = new, 204 = overwrite

        except zanshin.webdav.PermissionsError:
            message = "Not authorized to PUT %s" % itemName
            raise NotAllowed(message=message)
            
        except zanshin.webdav.WebDAVError, err:

            if err.status == twisted.web.http.FORBIDDEN or err.status == twisted.web.http.CONFLICT:
                # seen if trying to PUT to a nonexistent collection (@@@MOR verify)
                message = "Parent collection for %s is not found" % itemName
                raise NotFound(message=message)


        etag = newResource.etag
        
        # @@@ [grant] Get mod-date?
        return etag

    def _deleteItem(self, itemPath): # must implement
        resource = self.__resourceFromPath(itemPath)
        logger.info("...removing from server: %s" % resource.path)
        
        if resource != None:
            try:
                deleteResp = zanshin.util.blockUntil(resource.delete)
            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(message=err.message)
            except M2Crypto.BIO.BIOError, err:
                message = "%s" % (err)
                raise CouldNotConnect(message=message)

    def _getItem(self, itemPath, into=None):
        resource = self.__resourceFromPath(itemPath)

        try:
            resp = zanshin.util.blockUntil(resource.get)

        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(message=err.message)
        except M2Crypto.BIO.BIOError, err:
            message = "%s" % (err)
            raise CouldNotConnect(message=message)

        if resp.status == twisted.web.http.NOT_FOUND:
            message = "Not found: %s" % resource.path
            raise NotFound(message=message)

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = "Not authorized to get %s" % resource.path
            raise NotAllowed(message=message)

        text = resp.body
        
        etag = resource.etag

        try:
            item = self.share.format.importProcess(text, item=into)
        except Exception, e:
            raise TransformationFailed(message="%s:%s" % (str(e), text))

        return (item, etag)


    def _getResourceList(self, location): # must implement
        """ Return information (etags) about all resources within a collection
        """
        
        resourceList = {}
        
        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            shareCollection = self.__getContainerResource()

            try:
                children = zanshin.util.blockUntil(
                                shareCollection.getAllChildren)

            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(message=err.message)
            except M2Crypto.BIO.BIOError, err:
                message = "%s" % (err)
                raise CouldNotConnect(message=message)
            except zanshin.webdav.WebDAVError, e:

                if e.status == twisted.web.http.NOT_FOUND:
                    raise NotFound(message="Not found: %s" % shareCollection.path)

                if e.status == twisted.web.http.UNAUTHORIZED:
                    raise NotAllowed(message="Not allowed: %s" % shareCollection.path)

                raise

            for child in children:
                if child != shareCollection:
                    path = child.path.split("/")[-1]
                    etag = child.etag
                    resourceList[path] = { 'data' : etag }

        elif style == ImportExportFormat.STYLE_SINGLE:
            resource = self._getServerHandle().getResource(location)
            # @@@ [grant] Error handling and reporting here
            # are crapski
            try:
                zanshin.util.blockUntil(resource.propfind, depth=0)
            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(message=err.message)
            except M2Crypto.BIO.BIOError, err:
                message = "%s" % (err)
                raise CouldNotConnect(message=message)
            except zanshin.webdav.PermissionsError, err:
                message = "Not authorized to get %s" % location
                raise NotAllowed(message=message)
#            except NotFoundError:
#                message = "Not found: %s" % url
#                raise NotFound(message=message)
#
            
            etag = resource.etag
            # @@@ [grant] count use resource.path here
            path = urlparse.urlparse(location)[2]
            path = path.split("/")[-1]
            resourceList[path] = { 'data' : etag }

        return resourceList

    def connect(self):
        self.__releaseServerHandle()
        self._getServerHandle() # @@@ [grant] Probably not necessary

    def disconnect(self):
        self.__releaseServerHandle()


    def _dumpState(self):
        print " - - - - - - - - - "
        resourceList = self._getResourceList(self.getLocation())
        print
        print "Remote:"
        for (itemPath, value) in resourceList.iteritems():
            print itemPath, value
        print
        print "In manifest:"
        for (path, value) in self.manifest.iteritems():
            print path, value
        print
        print "In contents:"
        for item in self.share.contents:
            print item.getItemDisplayName(), item.itsUUID, item.getVersion(), item.getVersion(True)
        print " - - - - - - - - - "

class SimpleHTTPConduit(WebDAVConduit):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/SimpleHTTPConduit"

    def get(self):
        self.connect()

        location = self.getLocation()
        logger.info("Starting GET of %s" % (location))
        extraHeaders = { }
        if self.lastModified:
            extraHeaders['If-Modified-Since'] = self.lastModified
            logger.info("...last modified: %s" % self.lastModified)

        try:
            resp = zanshin.util.blockUntil(self._getServerHandle().get,
                        location, extraHeaders=extraHeaders)

            if resp.status == twisted.web.http.NOT_MODIFIED:
                # The remote resource is as we saw it before
                logger.info("...not modified")
                return

        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(message=err.message)
        except M2Crypto.BIO.BIOError, err:
            message = "%s" % (err)
            raise CouldNotConnect(message=message)

        if resp.status == twisted.web.http.NOT_FOUND:
            message = "Not found: %s" % location
            raise NotFound(message=message)

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = "Not authorized to get %s" % location
            raise NotAllowed(message=message)

        logger.info("...received; processing...")

        try:
            text = resp.body
            self.share.format.importProcess(text, item=self.share)
        except Exception, e:
            raise TransformationFailed(message=str(e))

        lastModified = resp.headers.getHeader('Last-Modified')
        self.lastModified = lastModified[-1]
        logger.info("...imported, new last modified: %s" % self.lastModified)

    def put(self, skipItems=None):
        logger.info("'put( )' not support in SimpleHTTPConduit")

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingError(Exception):
    """ Generic Sharing exception. """
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        try:
            return "Sharing error '%s'" % self.message
        except:
            return "Sharing error"

class AlreadyExists(SharingError):
    """ Exception raised if a share already exists. """

class NotFound(SharingError):
    """ Exception raised if a share/resource wasn't found. """

class NotAllowed(SharingError):
    """ Exception raised if we don't have access. """

class Misconfigured(SharingError):
    """ Exception raised if a share isn't properly configured. """

class CouldNotConnect(SharingError):
    """ Exception raised if a conduit can't connect to an external entity
        due to DNS/network problems.
    """
class IllegalOperation(SharingError):
    """ Exception raised if the entity a conduit is communicating with is
        denying an operation for some reason not covered by other exceptions.
    """
class TransformationFailed(SharingError):
    """ Exception raised if import or export process failed. """

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVAccount(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/WebDAVAccount"

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ImportExportFormat(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ImportExportFormat"

    STYLE_SINGLE = 'single'
    STYLE_DIRECTORY = 'directory'

    def fileStyle(self):
        """ Should return 'single' or 'directory' """
        pass


class CloudXMLFormat(ImportExportFormat):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/CloudXMLFormat"

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 cloudAlias='sharing'):
        super(CloudXMLFormat, self).__init__(name, parent, kind, view)

        self.cloudAlias = cloudAlias

    def fileStyle(self):
        return self.STYLE_DIRECTORY

    def extension(self, item):
        return "xml"

    def importProcess(self, text, extension=None, item=None):
        doc = libxml2.parseDoc(text)
        node = doc.children
        try:
            item = self.__importNode(node, item)
        except KeyError:
            print "Couldn't parse:", text

        doc.freeDoc()
        return item

    def exportProcess(self, item, depth=0):

        indent = "   "

        # print "export cloud for %s (%s)" % (item, item.itsKind)

        # Collect the set of attributes that are used in this format
        attributes = self.__collectAttributes(item)

        result = indent * depth
        
        if item.itsKind.isMixin():
            kindsList = []
            for kind in item.itsKind.superKinds:
                kindsList.append(str(kind.itsPath))
            kinds = ",".join(kindsList)
        else:
            kinds = str(item.itsKind.itsPath)
        
        result += "<%s kind='%s' uuid='%s'>\n" % (item.itsKind.itsName,
                                                  kinds,
                                                  item.itsUUID)

        depth += 1

        for (attrName, endpoint) in attributes.iteritems():

            if not hasattr(item, attrName):
                continue

            result += indent * depth
            result += "<%s>" % attrName

            otherName = item.itsKind.getOtherName(attrName, None, item, None)
            cardinality = item.getAttributeAspect(attrName, 'cardinality')
            type = item.getAttributeAspect(attrName, 'type')

            if otherName: # it's a bidiref
                result += "\n"

                if cardinality == 'single':
                    value = item.getAttributeValue(attrName)

                    # @@@MOR avoid endless recursion in the case where an item
                    # has a reference to itself
                    if value is not item and value is not None:
                        result += self.exportProcess(value, depth+1)

                elif cardinality == 'list':
                    for value in item.getAttributeValue(attrName):
                        if value is not item:
                            result += self.exportProcess(value, depth+1)

                elif cardinality == 'dict':
                    # @@@MOR
                    pass

                result += indent * depth

            else: # it's a literal (@@@MOR could be SingleRef though)

                if cardinality == 'single':
                    value = item.getAttributeValue(attrName)
                    if isinstance(value, Lob):
                        # @@@MOR For 0.5 convert to ASCII
                        # For 0.6, we should handle encoding properly.
                        uStr = value.getReader().read()
                        value = uStr.encode('ascii', 'replace')
                        
                    if isinstance(value, Item):
                        result += "\n"
                        result += self.exportProcess(value, depth+1)
                    else:
                        result += "<![CDATA[" + type.makeString(value) + "]]>"

                elif cardinality == 'list':
                    depth += 1
                    result += "\n"
                    for value in item.getAttributeValue(attrName):
                        result += indent * depth
                        result += "<value>%s</value>\n" % type.makeString(value)
                    depth -= 1

                    result += indent * depth

                elif cardinality == 'dict':
                    # @@@MOR
                    pass

            result += "</%s>\n" % attrName

        depth -= 1
        result += indent * depth
        result += "</%s>\n" % item.itsKind.itsName
        return result


    def __collectAttributes(self, item):
        attributes = {}
        skip = {}
        for cloud in item.itsKind.getClouds(self.cloudAlias):
            for (alias, endpoint, inCloud) in cloud.iterEndpoints(self.cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]
                
                # An includePolicy of 'none' is how we override an inherited
                # endpoint
                if endpoint.includePolicy == 'none':
                    skip[attrName] = 1
                    
                attributes[attrName] = endpoint

        for attrName in skip.iterkeys():
            del attributes[attrName]
            
        return attributes


    def __getNode(self, node, attribute):

        # @@@MOR This method only supports traversal of single-cardinality
        # attributes

        # attribute can be a dot-separated chain of attribute names
        chain = attribute.split(".")
        attribute = chain[0]
        remaining = chain[1:]

        child = node.children
        while child:
            if child.type == "element":
                if child.name == attribute:
                    if not remaining:
                        # we're at the end of the chain
                        return child
                    else:
                        # we need to recurse. @@@MOR for now, not supporting
                        # list
                        grandChild = child.children
                        while grandChild.type != "element":
                            # skip over non-elements
                            grandChild = grandChild.next
                        return self.__getNode(grandChild,
                         ".".join(remaining))

            child = child.next
        return None


    def __importNode(self, node, item=None):

        kind = None
        kinds = []

        kindNode = node.hasProp('kind')
        if kindNode:
            kindPathList = kindNode.content.split(",")
            for kindPath in kindPathList:
                kind = self.itsView.findPath(kindPath)
                if kind is not None:
                    kinds.append(kind)
        else:
            logger.info("No kinds provided")
            return None

        if len(kinds) == 0:
            # we don't have any of the kinds provided
            logger.info("No kinds found locally for %s" % kindPathList)
            return None
        elif len(kinds) == 1:
            kind = kinds[0]
        else: # time to mixin
            kind = kinds[0].mixin(kinds[1:])

        if item is None:

            uuidNode = node.hasProp('uuid')
            if uuidNode:
                try:
                    uuid = UUID(uuidNode.content)
                    item = self.itsView.findUUID(uuid)
                except Exception, e:
                    print e
            else:
                uuid = None

        if item is None:
            # item search turned up empty, so create an item...
            if uuid:
                parent = self.findPath("//userdata")
                item = kind.instantiateItem(None, parent, uuid,
                                            withInitialValues=True)
            else:
                item = kind.newItem(None, None)

        else:
            # there is a chance that the incoming kind is different than the
            # item's kind
            item.itsKind = kind

        # we have an item, now set attributes
        attributes = self.__collectAttributes(item)
        for (attrName, endpoint) in attributes.iteritems():

            attrNode = self.__getNode(node, attrName)
            if attrNode is None:
                if item.hasLocalAttributeValue(attrName):
                    item.removeAttributeValue(attrName)
                continue

            otherName = item.itsKind.getOtherName(attrName, None, item, None)
            cardinality = item.getAttributeAspect(attrName, 'cardinality')
            type = item.getAttributeAspect(attrName, 'type')

            # @@@MOR What's the right way to tell if this is a single ref -- checking type for non-type items is a kludge:

            if otherName or (isinstance(type, Item) and not isinstance(type, Type)): # it's a ref

                if cardinality == 'single':
                    valueNode = attrNode.children
                    while valueNode and valueNode.type != "element":
                        # skip over non-elements
                        valueNode = valueNode.next
                    if valueNode:
                        valueItem = self.__importNode(valueNode)
                        if valueItem is not None:
                            item.setAttributeValue(attrName, valueItem)

                elif cardinality == 'list':
                    valueNode = attrNode.children
                    while valueNode:
                        if valueNode.type == "element":
                            valueItem = self.__importNode(valueNode)
                            if valueItem is not None:
                                item.addValue(attrName, valueItem)
                        valueNode = valueNode.next

                elif cardinality == 'dict':
                    pass

            else: # it's a literal

                if cardinality == 'single':
                    value = type.makeValue(attrNode.content)
                    item.setAttributeValue(attrName, value)

                elif cardinality == 'list':
                    values = []
                    valueNode = attrNode.children
                    while valueNode:
                        if valueNode.type == "element":
                            value = type.makeValue(valueNode.content)
                            values.append(value)
                        valueNode = valueNode.next
                    item.setAttributeValue(attrName, values)

                elif cardinality == 'dict':
                    pass

        return item


class MixedFormat(ImportExportFormat):
    """
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/MixedFormat"

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 cloudAlias='sharing'):
        super(CloudXMLFormat, self).__init__(name, parent, kind, view)
        self.cloudAlias = cloudAlias

    def fileStyle(self):
        return self.STYLE_DIRECTORY

    handlers = (
        ('CalendarEvent', 'ics', iCalendarHandler),
        ('Contact', 'vcd', vCardHandler),
    )

    def extension(self, item):
        # search the handlers for appropriate extension

    def importProcess(self, text, extension=None, item=None):
        ### Import a chunk of text, need to figure out which handler to pass
        ### it to.

        # return item
        pass

    def exportProcess(self, item):
        ### Output an item
        pass
    """
    pass

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Sharing helper methods

def newOutboundShare(view, collection, kinds=None, shareName=None,
                     account=None):
    """ Create a new Share item for a collection this client is publishing.

    If account is provided, it will be used; otherwise, the default WebDAV
    account will be used.  If there is no default account, None will be
    returned.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param collection: The ItemCollection that will be shared
    @type collection: ItemCollection
    @param account: The WebDAV Account item to use
    @type account: An item of kind WebDAVAccount
    @return: A Share item, or None if no WebDAV account could be found.
    """

    if account is None:
        # Find the default WebDAV account
        account = getWebDAVAccount(view)
        if account is None:
            return None

    conduit = WebDAVConduit(view=view, account=account, shareName=shareName)
    format = CloudXMLFormat(view=view)
    share = Share(view=view, conduit=conduit, format=format,
                  contents=collection)

    if kinds is None:
        share.filterKinds = []
    else:
        share.filterKinds = kinds

    share.displayName = collection.displayName
    share.hidden = False # indicates that the DetailView should show this share
    share.sharer = Contacts.Contact.getCurrentMeContact(view)
    return share


def newInboundShare(view, url):
    """ Create a new Share item for a URL this client is subscribing to.

    Finds a WebDAV account which matches this URL; if none match then
    prompt the user for username/password for that URL.  If either of
    these result in finding/creating an account, then create a Share item
    and return it.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param url: The url which points to a collection to import
    @type url: String
    @return: A Share item, or None if no WebDAV account could be found.
    """

    (useSSL, host, port, path, query, fragment) = splitUrl(url)

    parent = view.findPath("//userdata")

    account = findMatchingWebDAVAccount(view, url)

    if account is None:
        # Prompt user for account information then create an account

        # Get the parent directory of the given path:
        # '/dev1/foo/bar' becomes ['dev1', 'foo']
        parentPath = path.strip('/').split('/')[:-1]
        # ['dev1', 'foo'] becomes "dev1/foo"
        parentPath = "/".join(parentPath)

        # Examine the URL for scheme, host, port, path
        info = AccountInfoPrompt.PromptForNewAccountInfo(wx.GetApp().mainFrame,
                                                         host=host,
                                                         path=parentPath)
        if info is not None:
            (description, username, password) = info
            kindPath = "//parcels/osaf/framework/sharing/WebDAVAccount"
            webDAVAccountKind = view.findPath(kindPath)
            account = webDAVAccountKind.newItem(name=None, parent=parent)
            account.displayName = description
            account.host = host
            account.path = parentPath
            account.username = username
            account.password = password
            account.useSSL = useSSL
            account.port = port

    share = None
    if account is not None:
        shareName = path.strip("/").split("/")[-1]
        mode = "both"
        if url.endswith(".ics"):
            import ICalendar
            format = ICalendar.ICalendarFormat(view=view)
            conduit = SimpleHTTPConduit(view=view, shareName=shareName,
                                        account=account)
            mode = "get"
        else:
            conduit = WebDAVConduit(view=view, shareName=shareName,
                                    account=account)
            format = CloudXMLFormat(view=view)
        share = Share(view=view, conduit=conduit, format=format)
        share.hidden = False
        share.mode = mode
    return share


def getWebDAVAccount(view):
    """ Return the current default WebDAV account item.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: An account item, or None if no WebDAV account could be found.
    """
    return Current.Current.get(view, "WebDAVAccount")


def findMatchingWebDAVAccount(view, url):
    """ Find a WebDAV account which corresponds to a URL.

    The url being passed in is for a collection -- it will include the
    collection name in the url.  We need to find a webdav account who
    has been set up to operate on the parent directory of this collection.
    For example, if the url is http://pilikia.osafoundation.org/dev1/foo/
    we need to find an account whose schema+host+port match and whose path
    is /dev1

    Note: this logic assumes only one account will match; you aren't
    currently allowed to have to multiple webdav accounts pointing to the
    same scheme+host+port+path combination.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param url: The url which points to a collection
    @type url: String
    @return: An account item, or None if no WebDAV account could be found.
    """

    webDAVAccountKind = view.findPath("//parcels/osaf/framework/sharing/WebDAVAccount")

    (useSSL, host, port, path, query, fragment) = splitUrl(url)

    # Get the parent directory of the given path:
    # '/dev1/foo/bar' becomes ['dev1', 'foo']
    path = path.strip('/').split('/')[:-1]
    # ['dev1', 'foo'] becomes "dev1/foo"
    path = "/".join(path)


    for account in KindQuery().run([webDAVAccountKind]):
        # Does this account's url info match?
        accountPath = account.path.strip('/')
        if account.useSSL == useSSL and account.host == host and account.port == port and accountPath == path:
            return account

    return None


def findMatchingShare(view, url):
    """ Find a Share which corresponds to a URL.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param url: A url pointing at a WebDAV Collection
    @type url: String
    @return: A Share item, or None
    """

    account = findMatchingWebDAVAccount(view, url)
    if account is None:
        return None

    # If we found a matching account, that means *potentially* there is a
    # matching share; go through all conduits this account points to and look
    # for shareNames that match

    (useSSL, host, port, path, query, fragment) = splitUrl(url)

    # '/dev1/foo/bar' becomes 'bar'
    shareName = path.strip("/").split("/")[-1]

    if hasattr(account, 'conduits'):
        for conduit in account.conduits:
            if conduit.shareName == shareName:
                if conduit.share.hidden == False:
                    return conduit.share

    return None


def splitUrl(url):
    (scheme, host, path, query, fragment) = urlparse.urlsplit(url)

    if scheme == 'https':
        port = 443
        useSSL = True
    else:
        port = 80
        useSSL = False

    if host.find(':') != -1:
        (host, port) = host.split(':')
        port = int(port)

    return (useSSL, host, port, path, query, fragment)


def isShared(collection):
    """ Return whether an ItemCollection has a Share item associated with it.

    @param collection: an ItemCollection
    @type collection: ItemCollection
    @return: True if collection does have a Share associated with it; False
        otherwise.
    """

    # See if any non-hidden shares are associated with the collection.
    # A "hidden" share is one that was not requested by the DetailView,
    # This is to support shares that don't participate in the whole
    # invitation process (such as transient import/export shares, or shares
    # for publishing an .ics file to a webdav server).

    for share in collection.shares:
        if share.hidden == False:
            return True
    return False


def getShare(collection):
    """ Return the Share item (if any) associated with an ItemCollection.

    @param collection: an ItemCollection
    @type collection: ItemCollection
    @return: A Share item, or None
    """

    # Return the first "non-hidden" share for this collection -- see isShared()
    # method for further details.

    for share in collection.shares:
        if share.hidden == False:
            return share
    return None


def isInboundMailSetUp(view):
    """ See if the IMAP/POP account has at least the minimum setup needed for
        sharing (IMAP/POP needs email address).

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    # Find imap account, and make sure email address is valid
    account = Mail.MailParcel.getCurrentMailAccount(view)
    if account is not None and account.replyToAddress and account.replyToAddress.emailAddress:
        return True
    return False


def isSMTPSetUp(view):
    """ See if SMTP account has at least the minimum setup needed for
        sharing (SMTP needs host).

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    # Find smtp account, and make sure server field is set
    (smtp, replyTo) = Mail.MailParcel.getCurrentSMTPAccount(view)
    if smtp is not None and smtp.host:
        return True
    return False


def isMailSetUp(view):
    """ See if the email accounts have at least the minimum setup needed for
        sharing.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the accounts are set up; False otherwise.
    """
    if isInboundMailSetUp(view) and isSMTPSetUp(view):
        return True
    return False


def isWebDAVSetUp(view):
    """ See if WebDAV is set up.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if accounts are set up; False otherwise.
    """

    account = getWebDAVAccount(view)
    return account is not None

def ensureAccountSetUp(view):
    """ A helper method to make sure the user gets the account info filled out.

    This method will examine all the account info and if anything is missing,
    a dialog will explain to the user what is missing; if they want to proceed
    to enter that information, the accounts dialog will pop up.  If at any
    point they hit Cancel, this method will return False.  Only when all
    account info is filled in will this method return True.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if accounts are set up; False otherwise.
    """

    while True:

        DAVReady = isWebDAVSetUp(view)
        InboundMailReady = isInboundMailSetUp(view)
        SMTPReady = isSMTPSetUp(view)
        if DAVReady and InboundMailReady and SMTPReady:
            return True

        msg = "The following account(s) need to be set up:\n\n"
        if not DAVReady:
            msg += " - WebDAV (collection publishing)\n"
        if not InboundMailReady:
            msg += " - IMAP/POP (inbound email)\n"
        if not SMTPReady:
            msg += " - SMTP (outound email)\n"
        msg += "\nWould you like to enter account information now?"

        response = application.dialogs.Util.yesNo(wx.GetApp().mainFrame,
                                                  "Account set up",
                                                  msg)
        if response == False:
            return False

        if not InboundMailReady:
            account = Mail.MailParcel.getCurrentMailAccount(view)
        elif not SMTPReady:
            """ Returns the defaultSMTPAccount or None"""
            account = Mail.MailParcel.getCurrentSMTPAccount(view)
        else:
            account = getWebDAVAccount(view)

        response = \
          application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(
          wx.GetApp().mainFrame, account=account, view=view)

        if response == False:
            return False


def syncShare(share):

    try:
        share.sync()
    except SharingError, err:
        try:
            msg = "Error syncing the '%s' collection\n" % share.contents.getItemDisplayName()
            msg += "using the '%s' account:\n\n" % share.conduit.account.getItemDisplayName()
            msg += err.message
        except:
            msg = "Error during sync"
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    "Synchronization Error", msg)


def syncAll(view):
    """ Synchronize all active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    """

    shareKind = view.findPath("//parcels/osaf/framework/sharing/Share")
    for share in KindQuery().run([shareKind]):
        if share.active:
            syncShare(share)


def checkForActiveShares(view):
    """ See if there are any non-hidden, active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if there are non-hidden, active shares; False otherwise
    """

    shareKind = view.findPath("//parcels/osaf/framework/sharing/Share")
    for share in KindQuery().run([shareKind]):
        if share.active and not share.hidden:
            return True
    return False

def manualSubscribeToCollection(view):
    url = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                              "Subscribe to share",
                                              "Enter the share's URL", "")
    if not url:
        return

    share = newInboundShare(view, url)
    if share is None:
        return

    try:
        share.get()
    except SharingError, err:
        msg = "Error syncing '%s'\n" % url
        msg += "using the '%s' account:\n\n" % share.conduit.account.getItemDisplayName()
        msg += err.message
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    "Synchronization Error", msg)
        share.conduit.delete()
        share.format.delete()
        share.delete()
        return

    collection = share.contents
    mainView = Globals.views[0]
    mainView.postEventByName("AddToSidebarWithoutCopyingAndSelectFirst", {'items':[collection]})

def manualPublishCollection(view, collection):
    share = getShare(collection)
    if share is not None:
        msg = "This collection is already shared at:\n%s" % share.conduit.getLocation()
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    "Already shared", msg)
        return

    shareName = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                              "Publish share",
                                              "Enter a name",
                                              collection.getItemDisplayName())

    if shareName is None:
        return

    share = newOutboundShare(view, collection, shareName=shareName)
    if share.exists():
        msg = "There is already a share at:\n%s" % share.conduit.getLocation()
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    "Share exists", msg)
        share.conduit.delete()
        share.format.delete()
        share.delete()
        return

    if shareName.endswith(".ics"):
        import ICalendar
        format = ICalendar.ICalendarFormat(view=view)
        share.mode = "put"
        share.format = format

    try:
        share.create()
        share.put()
    except SharingError, err:
        msg = "Error syncing the '%s' collection\n" % share.contents.getItemDisplayName()
        msg += "using the '%s' account:\n\n" % share.conduit.account.getItemDisplayName()
        msg += err.message
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    "Synchronization Error", msg)




class OneTimeFileSystemShare(OneTimeShare):
    def __init__(self, path, name, formatclass, kind=None, view=None,
                 contents=None):
        conduit = FileSystemConduit(kind=kind, view=view, sharePath=path,
                                    shareName=name)
        format  = formatclass(view=view)
        super(OneTimeFileSystemShare, self).__init__(kind=kind, view=view,
                 contents=contents, conduit=conduit, format=format)
