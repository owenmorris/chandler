__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application.Parcel
import osaf.framework.webdav.Dav
import osaf.mail.message
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ItemCollection as ItemCollection
from chandlerdb.util.UUID import UUID
import application.dialogs.PublishCollection
from repository.item.Query import KindQuery
import repository.query.Query as Query
import repository
import logging
import wx
import time, StringIO, urlparse, libxml2, os, mx
import chandlerdb
import vobject
import WebDAV


SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
EVENTS = "http://osafoundation.org/parcels/osaf/framework/blocks/Events"
MAINVIEW = "http://osafoundation.org/parcels/osaf/views/main"
CONTENT = "http://osafoundation.org/parcels/osaf/contentmodel"
WEBDAV_MODEL = "http://osafoundation.org/parcels/osaf/framework/webdav"

class Parcel(application.Parcel.Parcel):

    def _sharingUpdateCallback(self, url, collectionName, fromAddress):
        # When we receive the event, display a dialog
        logging.info("_sharingUpdateCallback: [%s][%s][%s]" % \
         (url, collectionName, fromAddress))
        collection = collectionFromSharedUrl(url)
        if collection is not None:
            # @@@ For 0.4 we will silently eat re-invites
            pass
            """
            application.dialogs.Util.ok( \
             Globals.wxApplication.mainFrame, "Sharing Invitation",
             "Received an invite for an already subscribed collection:\n" \
             "%s\n%s" % (collection.displayName, url))
            """
        else:
            if application.dialogs.Util.yesNo( \
             Globals.wxApplication.mainFrame, "Sharing Invitation",
             "%s\nhas invited you to subscribe to\n'%s'\n\n" \
             "Would you like to accept the invitation?" \
             % (fromAddress, collectionName) ):
                wx.Yield() # @@@ Give the UI a chance to redraw before
                           # long operation
                subscribeToWebDavCollection(url)

    def _errorCallback(self, error):
        # When we receive this event, display the error
        logging.info("_errorCallback: [%s]" % error)
        application.dialogs.Util.ok( \
         Globals.wxApplication.mainFrame, "Error", error)


def subscribeToWebDavCollection(url):
    """ Given a URL, tell the webdav subsystem to fetch the collection it
        points to, then add the collection to the sidebar. """

    collection = collectionFromSharedUrl(url)

    # See if we are already subscribed to the collection
    if collection is not None:
        application.dialogs.Util.ok( \
         Globals.wxApplication.mainFrame,
         "Already subscribed",
         "Already subscribed to collection '%s':\n"
         "%s" % (collection.displayName, url))
        return

    # Fetch the collection
    try:
        collection = osaf.framework.webdav.Dav.DAV(url).get( )
    except Exception, e:
        application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
         "WebDAV Error",
         "Couldn't get collection from:\n%s\n\nException %s: %s" % \
         (url, repr(e), str(e)))
        raise

    # Add the collection to the sidebar by...
    event = Globals.parcelManager.lookup(MAINVIEW, "NewItemCollection")
    args = {'collection':collection}
    # ...creating a new view (which gets returned as args['view'])...
    event.Post(args)
    Globals.repository.commit()
    # ...and selecting that view in the sidebar
    Globals.mainView.selectView(args['view'], showInDetailView=collection)


def manualSubscribeToCollection():
    """ Display a dialog box prompting the user for a webdav url to 
        subscribe to.  """
    # @@@ Obsolete, or for dev purposes only

    url = application.dialogs.Util.promptUser( \
     Globals.wxApplication.mainFrame, "Subscribe to Collection...",
     "Collection URL:", "")
    if url is not None:
        subscribeToWebDavCollection(url)

def manualPublishCollection(collection):
    application.dialogs.PublishCollection.ShowPublishCollectionsDialog( \
     Globals.wxApplication.mainFrame, collection)

def syncCollection(collection):
    if isShared(collection):
        print "Synchronizing", collection.sharedURL

        wx.Yield() # @@@ Give the UI a chance to redraw before
                   # long operation

        try:
            osaf.framework.webdav.Dav.DAV(collection.sharedURL).get()
        except Exception, e:
            application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
             "WebDAV Error",
             "Couldn't sync collection '%s'\nto %s\n\nException %s: %s" % \
             (collection.displayName, collection.sharedURL, repr(e), str(e)))
            raise

def putCollection(collection, url):
    """ Putting a collection on the webdav server for the first time. """

    wx.Yield() # @@@ Give the UI a chance to redraw before
               # long operation

    try:
        osaf.framework.webdav.Dav.DAV(url).put(collection)
    except Exception, e:
        application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
         "WebDAV Error",
         "Couldn't publish collection '%s'\nto %s\n\nException %s: %s" % \
         (collection.displayName, url, repr(e), str(e)))
        collection.sharedURL = None # consider it not shared
        raise

def isShared(collection):
    # @@@ Temporary hack until there is a better way to test for isShared
    return collection.hasAttributeValue('sharedURL') and (collection.sharedURL
     is not None)

def collectionFromSharedUrl(url):
    kind = Globals.parcelManager.lookup(CONTENT, "ItemCollection")
    for item in KindQuery().run([kind]):
        if isShared(item):
            if str(item.sharedURL) == (url):
                return item
    return None

def getWebDavPath():
    acct = getWebDavAccount()
    if acct and acct.host:
        return "http://%s/%s" % (acct.host, acct.path)
    else:
        return None

def getWebDavAccount():
    webDavAccountKind = application.Globals.parcelManager.lookup(WEBDAV_MODEL,
     "WebDAVAccount")

    account = None
    for item in KindQuery().run([webDavAccountKind]):
        account = item
        if item.isDefault:
            break
    return account

    return Globals.parcelManager.lookup(SHARING, 'WebDAVAccount')

def isMailSetUp():

    # Find imap account, and make sure email address is valid
    imap = Mail.MailParcel.getIMAPAccount()
    if not imap.emailAddress:
        return False

    # Find smtp account, and make sure server field is set
    smtp = imap.defaultSMTPAccount
    if not smtp.host:
        return False

    return True

# Non-blocking methods that the mail thread can use to call methods on the
# main thread:

def announceSharingInvitation(url, collectionName, fromAddress):
    """ Call this method to announce that an inbound sharing invitation has
        arrived. This method is non-blocking. """
    logging.info("announceSharingInvitation() received an invitation from " \
    "mail: [%s][%s][%s]" % (url, collectionName, fromAddress))

    sharingParcel = \
     Globals.repository.findPath("//parcels/osaf/framework/sharing")
    Globals.wxApplication.CallItemMethodAsync( sharingParcel,
     '_sharingUpdateCallback', url, collectionName, fromAddress)
    logging.info("invite, just after CallItemMethodAsync")

def announceError(error):
    """ Call this method to announce an error. This method is non-blocking. """
    logging.info("announceError() received an error from mail: [%s]" % error)

    sharingParcel = \
     Globals.repository.findPath("//parcels/osaf/framework/sharing")
    Globals.wxApplication.CallItemMethodAsync( sharingParcel,
     '_errorCallback', error)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# New sharing code follows.  It will most likely be split out into separate
# modules at some point.

class Share(ContentModel.ChandlerItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/Share"

    """ Represents a set of shared items, encapsulating contents, location,
        access method, data format, sharer and sharees. """

    def __init__(self, name=None, parent=None, kind=None, contents=None,
     conduit=None, format=None):

        super(Share, self).__init__(name, parent, kind)

        self.contents = contents # ItemCollection
        self.setConduit(conduit)
        self.format = format

        self.sharer = None
        self.sharees = []

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

    def put(self):
        self.conduit.put()

    def get(self):
        self.conduit.get()

    def exists(self):
        return self.conduit.exists()


class ShareConduit(ContentModel.ChandlerItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ShareConduit"

    """ Transfers items in and out. """

    def __init__(self, name=None, parent=None, kind=None, sharePath=None,
     shareName=None):
        super(ShareConduit, self).__init__(name, parent, kind)

        self.sharePath = sharePath
        self.shareName = shareName
        self.__clearManifest()

    def setShare(self, share):
        self.share = share

    def __conditionalPutItem(self, item):
        # assumes that self.resourceList has been populated
        if not item.hasAttributeValue("externalUUID"):
            item.externalUUID = str(chandlerdb.util.UUID.UUID())
        externalItemExists = self.__externalItemExists(item)
        itemVersion = item.getVersion()
        prevVersion = self.__lookupVersion(item)
        if itemVersion > prevVersion or not externalItemExists:
            logging.info("...putting Item %s (%d vs %d) (on server: %s)" % \
             (item.externalUUID, itemVersion, prevVersion, externalItemExists))
            data = self._putItem(item)
            self.__addToManifest(item, data, itemVersion)
            logging.info("...done, data: %s, version: %d" %
             (data, itemVersion))
        else:
            pass
            # logging.info("Item is up to date")
        try:
            del self.resourceList[self._getItemPath(item)]
        except:
            logging.info("...external item didn't previously exist")

    def put(self):
        """ Transfer entire 'contents', transformed, to server. """

        location = self._getLocation()
        logging.info("Starting PUT of %s" % (location))

        self.itsView.commit() # Make sure locally modified items have had
                              # their version numbers bumped up.

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:

            self.resourceList = self._getResourceList(location)

            for item in self.share.contents:
                self.__conditionalPutItem(item)

            self.__conditionalPutItem(self.share)

            for (itemPath, value) in self.resourceList.iteritems():
                self._deleteItem(itemPath)

        elif style == ImportExportFormat.STYLE_SINGLE:
            pass # @@@

        logging.info("Finished PUT of %s" % (location))

    def __conditionalGetItem(self, itemPath, into=None):
        # assumes self.resourceList is populated

        if itemPath not in self.resourceList:
            print "Hey, it's not there:", itemPath # @@@
            logging.info("...Not on server")
            return None

        if not self.__haveLatest(itemPath):
            # logging.info("...getting: %s" % itemPath)
            (item, data) = self._getItem(itemPath, into)
            # The version is set to -1 to indicate it needs to be
            # set later on (by syncManifestVersions) because we won't
            # know the item version until *after* commit
            self.__addToManifest(item, data, -1)
            logging.info("...imported item %s, data: %s" % (item, data))
            return item
        else:
            pass
            # logging.info("...skipping")

        return None

    def get(self):

        location = self._getLocation()
        logging.info("Starting GET of %s" % (location))

        self.resourceList = self._getResourceList(location)

        self.__resetSeen()
        itemPath = self._getItemPath(self.share)
        self.__conditionalGetItem(itemPath, into=self.share)
        self.__setSeen(itemPath)
        del self.resourceList[itemPath]

        for itemPath in self.resourceList:
            item = self.__conditionalGetItem(itemPath)
            if item is not None:
                self.share.contents.add(item)
            self.__setSeen(itemPath)

        # If an item was prevsiously on the server (it was in our manifest)
        # but is no longer on the server, remove it from the collection
        # locally:
        toRemove = []
        for unseenPath in self.__iterUnseen():
            uuid = self.manifest[unseenPath]['uuid']
            item = self.itsView.findUUID(uuid)
            if item is not None:
                logging.info("...removing %s from collection" % item)
                self.share.contents.remove(item)
                toRemove.append(unseenPath)
        for removePath in toRemove:
            self.__removeFromManifest(removePath)

        self.itsView.commit()
        # Now that we've committed all fetched items, we need to update
        # the versions in the manifest
        self.__syncManifestVersions()
        self.itsView.commit()

        logging.info("Finished GET of %s" % location)

    # Methods that subclasses *must* implement:

    def _getLocation(self):
        """ Return a string representing where the share is being exported
            to or imported from, such as a URL or a filesystem path
        """
        pass

    def _getItemPath(self, item):
        """ Return a string that uniquely identifies a resource in the remote
            share, such as a URL path or a filesystem path.  These strings
            will be used for accessing the manfist and resourceList dicts.
        """
        pass

    def _getResourceList(self, location):
        """ Return a dictionary representing what items exist in the remote
            share. """
        # 'location' is a location returned from _getLocation
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


    # Manifest mangement routines
    # The manifest keeps track of the state of shared items at the time of
    # last sync.  It is a dictionary keyed on "path" (not repo path, but
    # path at the external source), whose values are dictionaries containing
    # the item's internal UUID, external UUID, either a last-modified date
    # (if filesystem) or ETAG (if webdav), and the item's version (as in
    # what item.getVersion() returns)

    def __clearManifest(self):
        self.manifest = {}

    def __addToManifest(self, item, data, version):
        # data is an ETAG, or last modified date
        path = self._getItemPath(item)
        self.manifest[path] = {
         'uuid' : item.itsUUID,
         'extuuid' : item.externalUUID,
         'data' : data,
         'version' : version,
        }

    def __removeFromManifest(self, path):
        del self.manifest[path]

    def __externalItemExists(self, item):
        itemPath = self._getItemPath(item)
        return itemPath in self.resourceList

    def __lookupVersion(self, item):
        try:
            return self.manifest[self._getItemPath(item)]['version']
        except:
            return -1

    def __haveLatest(self, path, data=None):
        """ Do we have the latest copy of this item? """
        if data == None:
            data = self.resourceList[path]['data']
        try:
            record = self.manifest[path]
            if record['data'] == data:
                # logging.info("haveLatest: Yes (%s %s)" % (path, data))
                return True
            else:
                # print "MISMATCH: local=%s, remote=%s" % (record['data'], data)
                logging.info("...don't have latest (%s local:%s remote:%s)" % (path,
                 record['data'], data))
                return False
        except KeyError:
            pass
            # print "%s is not in manifest" % path
        logging.info("...don't yet have %s" % path)
        return False

    def __resetSeen(self):
        for value in self.manifest.itervalues():
            value['seen'] = False

    def __setSeen(self, path):
        self.manifest[path]['seen'] = True

    def __iterUnseen(self):
        for (path, value) in self.manifest.iteritems():
            if not value['seen']:
                yield path

    def __syncManifestVersions(self):
        # Since repository version numbers change once you have committed,
        # we need to commit first and then run this routine which gets the
        # new version numbers for items we've just imported.
        for (path, value) in self.manifest.iteritems():
            if value['version'] == -1:
                item = self.itsView.findUUID(value['uuid'])
                if item is not None:
                    value['version'] = item.getVersion()



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class FileSystemConduit(ShareConduit):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/FileSystemConduit"

    SHAREFILE = "share.xml"

    def __init__(self, name=None, parent=None, kind=None, sharePath=None,
     shareName=None):
        super(FileSystemConduit, self).__init__(name, parent, kind,
         sharePath, shareName)

        # @@@ What sort of processing should we do on sharePath for this
        # filesystem conduit?

        # @@@ Probably should remove any slashes, or warn if there are any?
        self.shareName = self.shareName.strip("/")

    def _getLocation(self): # must implement
        if self.hasAttributeValue("sharePath") and \
         self.hasAttributeValue("shareName"):
            return os.path.join(self.sharePath, self.shareName)
        raise Misconfigured()

    def _getItemPath(self, item): # must implement
        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            if isinstance(item, Share):
                fileName = self.SHAREFILE
            else:
                fileName = "%s.xml" % item.externalUUID
            return os.path.join(self._getLocation(), fileName)

        elif style == ImportExportFormat.STYLE_SINGLE:
            return self._getLocation()

        else:
            print "@@@ Raise an exception here"

    def _putItem(self, item): # must implement
        path = self._getItemPath(item)
        text = self.share.format.exportProcess(item)
        out = file(path, 'w')
        out.write(text)
        out.close
        stat = os.stat(path)
        return stat.st_mtime

    def _deleteItem(self, itemPath): # must implement
        logging.info("...removing from disk: %s" % itemPath)
        os.remove(itemPath)

    def _getItem(self, itemPath, into=None): # must implement
        # logging.info("Getting item: %s" % itemPath)
        text = file(itemPath).read()
        item = self.share.format.importProcess(text, item=into)
        stat = os.stat(itemPath)
        return (item, stat.st_mtime)

    def _getResourceList(self, location):
        fileList = {}

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            for filename in os.listdir(location):
                fullPath = os.path.join(location, filename)
                stat = os.stat(fullPath)
                fileList[fullPath] = { 'data' : stat.st_mtime }

        elif style == ImportExportFormat.STYLE_SINGLE:
            stat = os.stat(location)
            fileList[location] = { 'data' : stat.st_mtime }

        else:
            print "@@@ Raise an exception here"

        return fileList


    def exists(self):
        super(FileSystemConduit, self).exists()

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            return os.path.isdir(self._getLocation())
        elif style == ImportExportFormat.STYLE_SINGLE:
            return os.path.isfile(self._getLocation())
        else:
            print "@@@ Raise an exception here"

    def create(self):
        super(FileSystemConduit, self).create()

        if self.exists():
            raise AlreadyExists()

        if self.sharePath is None or not os.path.isdir(self.sharePath):
            raise NotFound()

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            path = self._getLocation()
            if not os.path.exists(path):
                os.mkdir(path)

    def destroy(self):
        super(FileSystemConduit, self).destroy()

        if not self.exists():
            raise NotFound()

        path = self._getLocation()

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            for filename in os.listdir(path):
                os.remove(os.path.join(path, filename))
            os.rmdir(path)
        elif style == ImportExportFormat.STYLE_SINGLE:
            os.remove(path)


    def open(self):
        super(FileSystemConduit, self).open()

        if not self.exists():
            raise NotFound()

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVConduit(ShareConduit):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/WebDAVConduit"

    def __init__(self, name=None, parent=None, kind=None, sharePath=None,
     shareName=None, host=None, port=80, username="", password=""):
        super(WebDAVConduit, self).__init__(name, parent, kind, sharePath,
         shareName)

        self.host = host
        self.port = port
        self.username = username
        self.password = password

        # Process sharePath and shareName (making sure they have no
        # leading or trailing slashes)
        self.sharePath = self.sharePath.strip("/")

        # @@@ Probably should remove any slashes, or warn if there are any?
        self.shareName = self.shareName.strip("/")

        self.onItemLoad()

    def onItemLoad(self, view=None):
        # view is ignored
        self.client = None

    def __getClient(self):
        if self.client is None:
            self.client = WebDAV.Client(self.host, port=self.port,
             username=self.username, password=self.password, useSSL=False)
        return self.client

    def _getLocation(self):  # must implement
        """ Return the url of the share """
        # @@@ need to handle https
        if self.port == 80:
            url = "http://%s" % self.host
        else:
            url = "http://%s:%d" % (self.host, self.port)
        url = urlparse.urljoin(url, self.sharePath + "/")
        url = urlparse.urljoin(url, self.shareName)
        return url

    def _getItemPath(self, item): # must implement
        """ Return the path (not the full url) of an item given its external
        UUID """

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:

            if isinstance(item, Share):
                return "/%s/%s/share.xml" % (self.sharePath, self.shareName)
            else:
                return "/%s/%s/%s.xml" % (self.sharePath, self.shareName,
                 item.externalUUID)

        elif style == ImportExportFormat.STYLE_SINGLE:
            return "/%s/%s" % (self.sharePath, self.shareName)

        else:
            print "Error" #@@@ Raise something

    def __getItemURL(self, item):
        """ Return the full url of an item """
        path = self._getItemPath(item)
        return self.__URLFromPath(path)

    def __URLFromPath(self, path):
        # @@@ need to handle https
        if self.port == 80:
            url = "http://%s%s" % (self.host, path)
        else:
            url = "http://%s:%s%s" % (self.host, self.port, path)
        return url

    def create(self):
        super(WebDAVConduit, self).create()

        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            url = self._getLocation()
            resp = self.__getClient().mkcol(url)
            # @@@ Raise an exception if already exists?
            # print "response from mkcol:", resp.read()

    def destroy(self):
        print " @@@ unimplemented"

    def open(self):
        super(WebDAVConduit, self).open()

    def _putItem(self, item): # must implement
        """ putItem should publish an item and return etag/date, etc.
        """
        url = self.__getItemURL(item)
        text = self.share.format.exportProcess(item)
        resp = self.__getClient().put(url, text)
        resp.read()
        etag = resp.getheader('ETag', None)
        if not etag:
            # mod_dav doesn't give us back an etag upon PUT
            resp = self.__getClient().head(url)
            resp.read()
            etag = resp.getheader('ETag', None)
            if not etag:
                print "HEAD didn't give me an etag"
                raise SharingError() #@@@
        return etag

    def _deleteItem(self, itemPath): # must implement
        itemURL = self.__URLFromPath(itemPath)
        logging.info("...removing from server: %s" % itemURL)
        resp = self.__getClient().delete(itemURL)
        deleteResp = resp.read()

    def _getItem(self, itemPath, into=None): # must implement
        itemURL = self.__URLFromPath(itemPath)
        resp = self.__getClient().get(itemURL)
        text = resp.read()
        etag = resp.getheader('ETag', None)
        item = self.share.format.importProcess(text, item=into)
        return (item, etag)

    def _getResourceList(self, location): # must implement
        """ Return information (etags) about all resources within a collection
        """
        resourceList = {}

        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:

            resources = self.__getClient().ls(location)
            for (path, etag) in resources:
                resourceList[path] = { 'data' : etag }

        elif style == ImportExportFormat.STYLE_SINGLE:
            resp = self.__getClient().head(location)
            resp.read()
            etag = resp.getheader('ETag', None)
            path = urlparse.urlparse(location)[2]
            resourceList[path] = { 'data' : etag }

        return resourceList


    def _dumpState(self):
        # print " - - - - - - - - - "
        # resourceList = self._getResourceList(self._getLocation())
        # print
        # print "On server:"
        # for (path, value) in resourceList.iteritems():
        #     print path, value
        # print
        print "In manifest:"
        for (path, value) in self.manifest.iteritems():
            print path, value
        print
        print "In contents:"
        try:
            for item in self.share.contents:
                print item.itsPath, item.externalUUID, item.getVersion(), item.getVersion(True)
        except:
            print "must be empty"
        print " - - - - - - - - - "

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingError(Exception):
    """ Generic Sharing exception. """
    pass

class AlreadyExists(SharingError):
    """ Exception raised if a share already exists. """
    pass

class NotFound(SharingError):
    """ Exception raised if a share/resource wasn't found. """
    pass

class NotAllowed(SharingError):
    """ Exception raised if we don't have access. """
    pass

class Misconfigured(SharingError):
    """ Exception raised if a share isn't properly configured. """
    pass

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ImportExportFormat(ContentModel.ChandlerItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ImportExportFormat"

    STYLE_SINGLE = 'single'
    STYLE_DIRECTORY = 'directory'

    def fileStyle(self):
        """ Should return 'single' or 'directory' """
        pass

    def _findByExternalUUID(self, kindPath, externalUUID):
        query = Query.Query(self.itsView.repository,
         "for i in '%s' where i.externalUUID == '%s'" % \
          (kindPath, externalUUID))
        query.execute()
        results = []
        for i in query:
            results.append(i)
        if len(results):
            return results[0]
        return None

class ICalendarFormat(ImportExportFormat):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ICalendarFormat"

    __calendarEventPath = "//parcels/osaf/contentmodel/calendar/CalendarEvent"

    def fileStyle(self):
        return self.STYLE_SINGLE

    def importProcess(self, text, item=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        if item is None:
            item = ItemCollection.ItemCollection()
        else:
            if isinstance(item, Share):
                if item.contents is None:
                    item.contents = ItemCollection.ItemCollection()
                item = item.contents

        if not isinstance(item, ItemCollection.ItemCollection):
            print "Only a share or an item collection can be passed in"
            #@@@ Raise something

        if not item.hasAttributeValue("externalUUID"):
            item.externalUUID = str(chandlerdb.util.UUID.UUID())

        # @@@ Total hack
        newtext = []
        for c in text:
            if ord(c) > 127:
                c = " "
            newtext.append(c)
        text = "".join(newtext)

        input = StringIO.StringIO(text)
        calendar = vobject.readComponents(input, validate=True).next()

        countNew = 0
        countUpdated = 0

        for event in calendar.vevent:

            # See if we have a corresponding item already, or create one
            externalUUID = event.uid[0].value
            eventItem = self._findByExternalUUID(self.__calendarEventPath,
             externalUUID)
            if eventItem is None:
                eventItem = Calendar.CalendarEvent()
                eventItem.externalUUID = externalUUID
                countNew += 1
            else:
                countUpdated += 1

            try:
                eventItem.displayName = event.summary[0].value
            except AttributeError:
                eventItem.displayName = ""

            try:
                eventItem.description = event.description[0].value
                # print "Has a description:", eventItem.description
            except AttributeError:
                eventItem.description = ""

            dt = event.dtstart[0].value
            eventItem.startTime = \
             mx.DateTime.ISO.ParseDateTime(dt.isoformat())

            try:
                dt = event.dtend[0].value
                eventItem.endTime = \
                 mx.DateTime.ISO.ParseDateTime(dt.isoformat())
            except:
                eventItem.duration = mx.DateTime.DateTimeDelta(0, 1)

            item.add(eventItem)
            # print "Imported", eventItem.displayName, eventItem.startTime,
            #  eventItem.duration, eventItem.endTime
        logging.info("...iCalendar import of %d new items, %d updated" % \
         (countNew, countUpdated))

        return item

    def exportProcess(self, item, depth=0):
        # item is the whole collection
        pass


class CloudXMLFormat(ImportExportFormat):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/CloudXMLFormat"

    # This dictionary helps convert XML nodes to items.  Its keys are XML
    # element names, and the values are dictionaries storing the corresponding
    # Kind and 'fingerprint' -- a fingerprint is a list of attributes that make
    # up the Kind's 'primary key'.  One item is considered to be the same as
    # another if all of the attributes in their fingerprint list have the
    # same values.  Set 'useFingerprintSearch' to True to enable this feature.
    # At the moment it is turned off because we have UUIDs in the XML and we
    # can simply look those up.

    # @@@ At some point, the __nodeDescriptors information might be better off
    # living inside the schema itself somewhere, rather than in this module.

    useFingerprintSearch = False

    __nodeDescriptors = {
        'CalendarEvent' : {
            'kind' : '//parcels/osaf/contentmodel/calendar/CalendarEvent',
            'fingerprint' : (
                'organizer.contactName.firstName',
                'organizer.contactName.lastName'
            ),
        },
        'Contact' : {
            'kind' : '//parcels/osaf/contentmodel/contacts/Contact',
            'fingerprint' : (
                'contactName.firstName',
                'contactName.lastName'
            ),
        },
        'ContactName' : {
            'kind' : '//parcels/osaf/contentmodel/contacts/ContactName',
            'fingerprint' : (
                'firstName',
                'lastName'
            ),
        },
        'Share' : {
            'kind' : '//parcels/osaf/framework/sharing/Share',
            'fingerprint' : (),
        },
        'ItemCollection' : {
            'kind' : '//parcels/osaf/contentmodel/ItemCollection',
            'fingerprint' : (),
        },
    }

    def __init__(self, name=None, parent=None, kind=None,
     cloudAlias='sharing'):
        super(CloudXMLFormat, self).__init__(name, parent, kind)

        self.cloudAlias = cloudAlias

    def fileStyle(self):
        return self.STYLE_DIRECTORY

    def importProcess(self, text, item=None):
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
        if not item.hasAttributeValue("externalUUID"):
            item.externalUUID = str(chandlerdb.util.UUID.UUID())

        # Collect the set of attributes that are used in this format
        attributes = self.__collectAttributes(item)

        result = indent * depth
        result += "<%s>\n" % item.itsKind.itsName

        depth += 1

        for (attrName, endpoint) in attributes.iteritems():

            if not item.hasAttributeValue(attrName):
                continue

            result += indent * depth
            result += "<%s>" % attrName

            otherName = item.getAttributeAspect(attrName, 'otherName')
            cardinality = item.getAttributeAspect(attrName, 'cardinality')

            if otherName: # it's a bidiref
                result += "\n"

                if cardinality == 'single':
                    value = item.getAttributeValue(attrName)

                    # @@@ avoid endless recursion in the case where an item
                    # has a reference to itself
                    if value is not item and value is not None:
                        result += self.exportProcess(value, depth+1)

                elif cardinality == 'list':
                    for value in item.getAttributeValue(attrName):
                        if value is not item:
                            result += self.exportProcess(value, depth+1)

                elif cardinality == 'dict':
                    # @@@
                    pass

                result += indent * depth

            else: # it's a literal (@@@ could be SingleRef though)

                if cardinality == 'single':
                    value = item.getAttributeValue(attrName)
                    result += str(value)

                elif cardinality == 'list':
                    depth += 1
                    result += "\n"
                    for value in item.getAttributeValue(attrName):
                        result += indent * depth
                        result += "<value>%s</value>\n" % value
                    depth -= 1

                    result += indent * depth

                elif cardinality == 'dict':
                    # @@@
                    pass

            result += "</%s>\n" % attrName

        depth -= 1
        result += indent * depth
        result += "</%s>\n" % item.itsKind.itsName
        return result

    def __collectAttributes(self, item):
        attributes = {}
        for cloud in item.itsKind.getClouds(self.cloudAlias):
            for (alias, endpoint, inCloud) in cloud.iterEndpoints(self.cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]
                attributes[attrName] = endpoint
        return attributes


    def __getNode(self, node, attribute):

        # @@@ This method only supports traversal of single-cardinality
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
                        # we need to recurse.  @@@ for now, not supporting list
                        grandChild = child.children
                        while grandChild.type != "element":
                            # skip over non-elements
                            grandChild = grandChild.next
                        return self.__getNode(grandChild,
                         ".".join(remaining))

            child = child.next
        return None


    def __iterMatchingItems(self, node):

        query = Query.Query(self.itsView.repository, "")
        desc = self.__nodeDescriptors[node.name]

        kindPath = desc['kind']
        kind = self.itsView.findPath(kindPath)

        argString = ""  # everthing after 'where'
        args = {}       # the query.args dictionary
        i = 0
        for arg in desc['fingerprint']:    # build the query
            if i > 0:
                argString += " and "
            argString += "i.%s == $%d" % (arg, i)
            args[i] = self.__getNode(node, arg).content
            i += 1
        queryString = "for i in '%s' where %s" % (kindPath, argString)

        print "Fingerprint query with", args
        query.queryString = queryString
        query.args = args
        query.execute()

        for i in query:
            yield i

    def __getMatchingItems(self, node):
        results = []
        for item in self.__iterMatchingItems(node):
            results.append(item)
        return results

    def __importNode(self, node, item=None):
        desc = self.__nodeDescriptors[node.name]
        kindPath = desc['kind']
        kind = self.itsView.findPath(kindPath)

        if item is None:

            # see if we have a matching item, first by examining externalUUID...
            uuidNode = self.__getNode(node, "externalUUID")
            if uuidNode is not None:
                externalUUID = uuidNode.content
                item = self._findByExternalUUID(kindPath, externalUUID)
                # if item is not None:
                #     print "UUID search found", item

            if self.useFingerprintSearch and item is None:
                # then look for items matching the "fingerprint"...
                matches = self.__getMatchingItems(node)
                length = len(matches)
                if length == 0:
                    pass
                elif length == 1:
                    # a single match; use that item
                    item = matches[0]
                else:
                    # multiple matches!  hmm, use the first
                    item = matches[0]
                if item is not None:
                    print "Fingerprint match found", item

        if item is None:
            # both types of searches failed, so create an item...
            # print "Creating item of kind", kind.itsPath, kind.getItemClass()
            item = kind.newItem(None, None)
            # print "created item", item.itsPath, item.itsKind

        # we have an item, now set attributes
        attributes = self.__collectAttributes(item)
        for (attrName, endpoint) in attributes.iteritems():

            attrNode = self.__getNode(node, attrName)
            if attrNode is None:
                if item.hasAttributeValue(attrName):
                    item.removeAttributeValue(attrName)
                continue

            otherName = item.getAttributeAspect(attrName, 'otherName')
            cardinality = item.getAttributeAspect(attrName, 'cardinality')

            if otherName: # it's a bidiref

                if cardinality == 'single':
                    valueNode = attrNode.children
                    while valueNode and valueNode.type != "element":
                        # skip over non-elements
                        valueNode = valueNode.next
                    if valueNode:
                        valueItem = self.__importNode(valueNode)
                        item.setAttributeValue(attrName, valueItem)

                elif cardinality == 'list':
                    valueNode = attrNode.children
                    while valueNode:
                        if valueNode.type == "element":
                            valueItem = self.__importNode(valueNode)
                            item.addValue(attrName, valueItem)
                        valueNode = valueNode.next

                elif cardinality == 'dict':
                    pass

            else: # it's a literal (could be SingleRef though)

                if cardinality == 'single':
                    attrItem = item.itsKind.getAttribute(attrName)
                    value = attrItem.type.makeValue(attrNode.content)
                    item.setAttributeValue(attrName, value)

                elif cardinality == 'list':
                    values = []
                    valueNode = attrNode.children
                    while valueNode:
                        if valueNode.type == "element":
                            value = attrItem.type.makeValue(valueNode.content)
                            values.append(value)
                        valueNode = valueNode.next
                    item.setAttributeValue(attrName, values)

                elif cardinality == 'dict':
                    pass

        return item
