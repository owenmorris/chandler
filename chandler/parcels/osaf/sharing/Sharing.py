__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.sharing"


__all__ = [
    'Share',
    'OneTimeShare',
    'ShareConduit',
    'FileSystemConduit',
    'WebDAVConduit',
    'CalDAVConduit',
    'SimpleHTTPConduit',
    'OneTimeFileSystemShare',
    'SharingError',
    'AlreadyExists',
    'NotFound',
    'NotAllowed',
    'Misconfigured',
    'CouldNotConnect',
    'IllegalOperation',
    'TransformationFailed',
    'AlreadySubscribed',
    'WebDAVAccount',
    'ImportExportFormat',
    'CloudXMLFormat',
    'splitUrl',
]

import time, StringIO, urlparse, libxml2, os, base64, logging
from application import schema
from chandlerdb.util.uuid import UUID
from osaf.pim import (AbstractCollection, ListCollection,
    InclusionExclusionCollection, DifferenceCollection, CalendarEventMixin)
from repository.item.Item import Item
from repository.item.Sets import Set
from repository.schema.Types import Type
from repository.util.Lob import Lob
import application.dialogs.AccountInfoPrompt as AccountInfoPrompt
import M2Crypto.BIO
import WebDAV
import application.Parcel
import osaf.pim.items as items
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.contacts import Contact
import osaf.pim.mail as Mail
import osaf.mail.utils as utils
import twisted.web.http
import wx
import zanshin.webdav
from i18n import OSAFMessageFactory as _
from osaf import messages
from osaf import ChandlerException


logger = logging.getLogger(__name__)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


class modeEnum(schema.Enumeration):
    schema.kindInfo(displayName=u"Mode Enumeration")
    values = "put", "get", "both"


class Share(items.ContentItem):
    """
    Represents a set of shared items, encapsulating contents, location,
    access method, data format, sharer and sharees.
    """

    schema.kindInfo(
        displayName=u"Share Kind",
        description="Represents a shared collection",
    )

    hidden = schema.One(
        schema.Boolean,
        doc = 'This attribute is used to denote which shares have been '
              'created by the user via the detail view (hidden=False) versus '
              'those that are being created for other purposes (hidden=True), '
              'such as transient import/export shares, .ics publishing, etc.',
        initialValue = False,
    )

    active = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether this share should be synced "
              "during a 'sync all' operation.",
        initialValue = True,
    )

    mode = schema.One(
        modeEnum,
        doc = 'This attribute indicates the sync mode for the share:  '
              'get, put, or both',
        initialValue = 'both',
    )

    error = schema.One(
        schema.String,
        doc = 'A message describing the last error; empty string otherwise',
        initialValue = ''
    )

    contents = schema.One(items.ContentItem, otherName = 'shares')

    items = schema.Sequence(items.ContentItem, initialValue=[],
        otherName = 'sharedIn')

    conduit = schema.One('ShareConduit', inverse = 'share')

    format = schema.One('ImportExportFormat', inverse = 'share')

    sharer = schema.One(
        Contact,
        doc = 'The contact who initially published this share',
        initialValue = None,
        otherName = 'sharerOf',
    )

    sharees = schema.Sequence(
        Contact,
        doc = 'The people who were invited to this share',
        initialValue = [],
        otherName = 'shareeOf',
    )

    filterClasses = schema.Sequence(
        schema.String,
        doc = 'The list of classes to import/export',
        initialValue = [],
    )

    filterAttributes = schema.Sequence(schema.String, initialValue=[])

    schema.addClouds(
        sharing = schema.Cloud(byCloud=[contents,sharer,sharees,filterClasses,
                                        filterAttributes])
    )

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 contents=None, conduit=None, format=None):

        super(Share, self).__init__(name, parent, kind, view)

        self.contents = contents # AbstractCollection
        try:
            self.displayName = contents.displayName
        except:
            self.displayName = u""

        self.conduit = conduit
        self.format = format

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
            sharingView = self.conduit.get()
        else:
            sharingView = None

        if self.mode in ('put', 'both'):
            self.conduit.put(view=sharingView)

    def put(self):
        if self.mode in ('put', 'both'):
            self.conduit.put()

    def get(self):
        if self.mode in ('get', 'both'):
            self.conduit.get()

    def exists(self):
        return self.conduit.exists()

    def getLocation(self, privilege=None):
        return self.conduit.getLocation(privilege=privilege)

    def getSharedAttributes(self, item, cloudAlias='sharing'):
        """
        Examine sharing clouds and filterAttributes to determine which
        attributes to share for a given item
        """

        attributes = []
        skip = {}
        if hasattr(self, 'filterAttributes'):
            for attrName in self.filterAttributes:
                skip[attrName] = 1

        for cloud in item.itsKind.getClouds(cloudAlias):
            for (alias, endpoint, inCloud) in cloud.iterEndpoints(cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]

                # An includePolicy of 'none' is how we override an inherited
                # endpoint
                if endpoint.includePolicy == 'none':
                    skip[attrName] = 1

                if attrName not in attributes:
                    attributes.append(attrName)

        for attrName in skip.iterkeys():
            try:
                attributes.remove(attrName)
            except:
                pass

        return attributes

    def configureInbound(self, url):

        view = self.itsView

        (useSSL, host, port, path, query, fragment) = splitUrl(url)

        account = WebDAVAccount.findMatch(view, url)

        if account is None:
            # Prompt user for account information then create an account

            # Get the parent directory of the given path:
            # '/dev1/foo/bar' becomes ['dev1', 'foo']
            parentPath = path.strip(u'/').split(u'/')[:-1]
            # ['dev1', 'foo'] becomes "dev1/foo"
            parentPath = u"/".join(parentPath)

            # Examine the URL for scheme, host, port, path
            frame = wx.GetApp().mainFrame
            info = AccountInfoPrompt.PromptForNewAccountInfo(frame,
                                                             host=host,
                                                             path=parentPath)
            if info is not None:
                (description, username, password) = info
                account = WebDAVAccount(view=view)
                account.displayName = description
                account.host = host
                account.path = parentPath
                account.username = username
                account.password = password
                account.useSSL = useSSL
                account.port = port

        if account is not None:
            # compute shareName relative to the account path:
            accountPathLen = len(account.path.strip(u"/"))
            shareName = path.strip(u"/")[accountPathLen:]

            self.hidden = False

            if url.endswith(u".ics"):
                import ICalendar
                self.format = ICalendar.ICalendarFormat(parent=self)
                self.conduit = SimpleHTTPConduit(parent=self,
                                                 shareName=shareName,
                                                 account=account)
                self.mode = "get"

            else:
                self.conduit = WebDAVConduit(parent=self,
                                             shareName=shareName,
                                             account=account)
                location = self.getLocation()
                if not location.endswith(u"/"):
                    location += u"/"
                handle = self.conduit._getServerHandle()
                resource = handle.getResource(location)
                if getattr(self.conduit, 'ticket', False):
                    resource.ticketId = self.conduit.ticket

                exists = handle.blockUntil(resource.exists)
                if not exists:
                    raise NotFound(_(u"%(location)s does not exist") % {'location': location})

                isCalendar = handle.blockUntil(resource.isCalendar)
                isCollection =  handle.blockUntil(resource.isCollection)
                if isCalendar:
                    import ICalendar
                    self.format = ICalendar.CalDAVFormat(parent=self)
                else:
                    self.format = CloudXMLFormat(parent=self)
                self.mode = "both"



class OneTimeShare(Share):
    """
    Delete format, conduit, and share after the first get or put.
    """

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



class ShareConduit(items.ContentItem):
    """
    Transfers items in and out.
    """

    schema.kindInfo(displayName = u"Share Conduit Kind")

    share = schema.One(Share, inverse = Share.conduit)

    sharePath = schema.One(
        schema.String, doc = "The parent 'directory' of the share",
    )

    shareName = schema.One(
        schema.String,
        doc = "The 'directory' name of the share, relative to 'sharePath'",
    )

    manifest = schema.Mapping(
        schema.Dictionary,
        doc = "Keeps track of 'remote' item information, such as last "
              "modified date or ETAG",
        initialValue = {}
    )

    marker = schema.One(schema.SingleRef)

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(ShareConduit, self).__init__(name, parent, kind, view)

        # 'marker' is an item which exists only to keep track of the repository
        # view version number at the time of last sync
        self.marker = Item('marker', self, None)

    @classmethod
    def getSharingView(self, repo, version=None):
        # @@@MOR
        # Until we can switch over to using view merging, returning None
        # here is a sign that no view switching should take place.  When
        # we can use view merging, this 'return None' should be removed.
        return None

        if not hasattr(self, 'sharingView'):
            self.sharingView = repo.createView("Sharing", version)
            logger.info("Created sharing view (version %d)" % \
                self.sharingView._version)
        return self.sharingView


    def __conditionalPutItem(self, item):
        """
        Put an item if it's not on the server or is out of date
        """

        if self._getItemPath(item) is None:
            # According to the Format, we don't export this item
            return

        # Assumes that self.resourceList has been populated:
        externalItemExists = self.__externalItemExists(item)

        # Check to see if the item or any of its itemCloud items have a
        # more recent version than the last time we synced
        highVersion = -1
        for relatedItem in item.getItemCloud('sharing'):
            itemVersion = relatedItem.getVersion()
            if itemVersion > highVersion:
                highVersion = itemVersion

        prevVersion = self.marker.getVersion()

        if highVersion > prevVersion or not externalItemExists:

            logger.info("...putting '%s' %s (%d vs %d) (on server: %s)" % \
             (item.getItemDisplayName().encode('utf8'), item.itsUUID, itemVersion,
             prevVersion, externalItemExists))

            data = self._putItem(item)

            if data is not None:
                self.__addToManifest(self._getItemPath(item), item, data)
                logger.info("...done, data: %s, version: %d" %
                 (data, itemVersion))

            self.share.items.append(item)

        try:
            del self.resourceList[self._getItemPath(item)]
        except:
            logger.info("...external item %s didn't previously exist" % \
                self._getItemPath(item))

    def put(self, view=None):
        """
        Transfer entire 'contents', transformed, to server.
        """

        self.connect()

        if view is None:

            # We didn't get a view, so we must not have been called during
            # a sync -- just a put( )
            # @@@DLD bug 1998 - would refresh do here?
            # @@@MOR, I think I need a commit for the view merging to work
            self.itsView.commit()

            # We need to switch to a repository view with the version number
            # set to the last time we synced.
            sharingView = self.getSharingView(self.itsView.repository)

            # if getSharingView returns None, that's an indication we aren't
            # using view merging.  So just stick with the current view as is.
            if sharingView is None:
                sharingView = self.itsView
            else:
                # Make sure we have the latest
                sharingView.refresh()

        else:
            sharingView = view

        # "self" is an object in the main view; we need a reference to self
        # that is in the sharing view:
        sharingSelf = sharingView[self.itsUUID]

        try:
            location = sharingSelf.getLocation()
            logger.info("Starting PUT of %s" % (location))

            logger.debug("Manifest: %s" % self.manifest)

            # share.filterClasses includes the dotted names of classes so
            # they can be shared.
            filterClasses = sharingSelf._getFilterClasses()

            style = sharingSelf.share.format.fileStyle()
            if style == ImportExportFormat.STYLE_DIRECTORY:

                sharingSelf.resourceList = \
                    sharingSelf._getResourceList(location)

                # If we're sharing a collection, put the collection's items
                # individually:
                if isinstance(sharingSelf.share.contents, AbstractCollection):
                    for item in sharingSelf.share.contents:

                        # Skip private items
                        if item.private:
                            continue

                        # Skip generated items:
                        if getattr(item, 'isGenerated', False):
                            continue

                        # Skip modification items:
                        if getattr(item, 'modificationFor', None) is not None:
                            continue

                        # Skip any items matching the filtered classes
                        if filterClasses is not None:
                            match = False
                            for klass in filterClasses:
                                if isinstance(item, klass):
                                    match = True
                                    break
                            if not match:
                                continue

                        # Put the item
                        sharingSelf.__conditionalPutItem(item)

                # Put the Share item itself
                sharingSelf.__conditionalPutItem(sharingSelf.share)

                logger.debug("Manifest: %s" % self.manifest)
                # Any items on the server that weren't in our collection now
                # get removed from the server:
                for (itemPath, value) in sharingSelf.resourceList.iteritems():
                    uuid = sharingSelf.manifest[itemPath]['uuid']
                    if uuid is not None:
                        sharingSelf._deleteItem(itemPath)
                    sharingSelf.__removeFromManifest(itemPath)


            elif style == ImportExportFormat.STYLE_SINGLE:
                # Put a monolithic file representing the share item.
                #@@@MOR This should be beefed up to only publish if at least one
                # of the items has changed.
                sharingSelf._putItem(sharingSelf.share)


            # dirty our marker
            sharingSelf.marker.setDirty(Item.NDIRTY)


            # @@@DLD bug 1998 - why do we need a second commit here?
            # Is this just for the setDirty above?
            # @@@MOR This is to make our changes available to the main view
            sharingSelf.itsView.commit()

        finally:

            # If sharing work happened in a different view, refresh the
            # main view
            if self.itsView is not sharingView:
                self.itsView.refresh()

        self.disconnect()

        logger.info("Finished PUT of %s" % (location))


    def __conditionalGetItem(self, itemPath, into=None):
        """
        Get an item from the server if we don't yet have it or our copy
        is out of date
        """

        # assumes self.resourceList is populated

        if itemPath not in self.resourceList:
            logger.info("...Not on server: %s" % itemPath)
            return None

        if not self.__haveLatest(itemPath):
            # logger.info("...getting: %s" % itemPath)
            (item, data) = self._getItem(itemPath, into)

            if item is not None:
                self.__addToManifest(itemPath, item, data)
                logger.info("...imported '%s' '%s' %s, data: %s" % \
                 (itemPath, item.getItemDisplayName().encode('utf8'), item, data))

                self.share.items.append(item)

                return item

            logger.error("...NOT able to import '%s'" % itemPath)
            # Record with no item, indicating an error
            self.__addToManifest(itemPath)

            msg = _(u"Not able to import '%(itemPath)s'") % {'itemPath': itemPath}
            # @@@MOR Shall we just skip bogus imported items?
            # raise SharingError(message=msg)

        return None


    def get(self):

        self.itsView.commit() # Make sure locally modified items are available
                              # for merging into sharingView at the end of this
                              # method

        self.connect()

        # We need to switch to a repository view with the version number
        # set to the last time we synced.
        sharingView = self.getSharingView(self.itsView.repository,
                                          version=self.marker.getVersion())

        # @@@MOR
        # Until we can do view merging, getsharingView will return None,
        # in which case just use the main view:

        if sharingView is None:
            sharingView = self.itsView

        else:
            # Make sure our version is as it was at last sync
            version = self.marker.getVersion()
            sharingView.itsVersion = version

        # "self" is an object in the main view; we need a reference to self
        # that is in the sharing view:
        sharingSelf = sharingView[self.itsUUID]

        location = sharingSelf.getLocation()
        logger.info("Starting GET of %s" % (location))

        if not sharingSelf.exists():
           raise NotFound(_(u"%(location)s does not exist") % {'location': location})

        sharingSelf.resourceList = sharingSelf._getResourceList(location)
        logger.debug("Resources on server: %s", sharingSelf.resourceList)

        # We need to keep track of which items we've seen on the server so
        # we can tell when one has disappeared.
        sharingSelf.__resetSeen()

        itemPath = sharingSelf._getItemPath(sharingSelf.share)
        # if itemPath is None, the Format we're using doesn't have a file
        # that represents the Share item (CalDAV, for instance).

        if itemPath:
            # Get the file that represents the Share item
            item = sharingSelf.__conditionalGetItem(itemPath,
                                                    into=sharingSelf.share)

            # Whenever we get an item, mark it seen in our manifest and remove
            # it from the server resource list:
            sharingSelf.__setSeen(itemPath)
            try:
                del sharingSelf.resourceList[itemPath]
            except:
                pass

        # Make sure we have a collection to add items to:
        if sharingSelf.share.contents is None:
            sharingSelf.share.contents = InclusionExclusionCollection( \
                view=sharingView)
            trash = schema.ns('osaf.app', sharingView).TrashCollection
            sharingSelf.share.contents.setup(trash=trash)

        contents = sharingSelf.share.contents

        # If share.contents is an AbstractCollection, treat other resources as
        # items to add to the collection:
        if isinstance(contents, AbstractCollection):

            # Make sure the collection item is properly set up:

            if isinstance(contents, ListCollection) and \
                not hasattr(contents, 'rep'):
                    contents.rep = Set((contents,'refCollection'))

            if isinstance(contents, InclusionExclusionCollection) and \
                not hasattr(contents, 'rep'):
                    trash = schema.ns('osaf.app', sharingView).TrashCollection
                    contents.setup(trash=trash)

            filterClasses = sharingSelf._getFilterClasses()

            # Conditionally fetch items, and add them to collection
            for itemPath in sharingSelf.resourceList:
                item = sharingSelf.__conditionalGetItem(itemPath)
                if item is not None:
                    sharingSelf.share.contents.add(item)

                sharingSelf.__setSeen(itemPath)

            # When first importing a collection, name it after the share
            if not hasattr(sharingSelf.share.contents, 'displayName'):
                sharingSelf.share.contents.displayName = \
                    sharingSelf.share.displayName

            # If an item was previously on the server (it was in our
            # manifest) but is no longer on the server, remove it from
            # the collection locally:
            toRemove = []
            for unseenPath in sharingSelf.__iterUnseen():
                uuid = sharingSelf.manifest[unseenPath]['uuid']
                if uuid:
                    item = sharingView.findUUID(uuid)
                    if item is not None:

                        # If an item has disappeared from the server, only
                        # remove it locally if it matches the current share
                        # filter.

                        removeLocally = True

                        if filterClasses is not None:
                            match = False
                            for klass in filterClasses:
                                if isinstance(item, klass):
                                    match = True
                                    break
                            if match is False:
                                removeLocally = False

                        if removeLocally:
                            logger.info("...removing %s from collection" % item)
                            sharingSelf.share.contents.remove(item)
                            sharingSelf.share.items.remove(item)
                else:
                    logger.info("Just removed a phantom manifest entry for %s",
                                unseenPath)

                # In any case, remove from manifest
                toRemove.append(unseenPath)

            for removePath in toRemove:
                sharingSelf.__removeFromManifest(removePath)


        # This is where merge conflicts will happen:

        def tmpMergeFn(code, item, attribute, value):
            # print "Conflict:", code, item, attribute, value
            logger.info("Sharing conflict: Item=%s, Attribute=%s, Local=%s, Remote=%s" % (item.displayName.encode('utf8'), attribute, str(item.getAttributeValue(attribute)), str(value)))
            return value # let the user win
            # return item.getAttributeValue(attribute) # let the server win

        sharingView.refresh(tmpMergeFn)

        logger.info("Finished GET of %s" % location)

        self.disconnect()

        return sharingView



    def _getFilterClasses(self):
        filterClasses = None
        if len(self.share.filterClasses) > 0:
            filterClasses = []
            for classString in self.share.filterClasses:
                filterClasses.append(schema.importString(classString))
        return filterClasses



    def _getItemPath(self, item):
        """
        Return a string that uniquely identifies a resource in the remote
        share, such as a URL path or a filesystem path.  These strings
        will be used for accessing the manifest and resourceList dicts.
        """
        extension = self.share.format.extension(item)
        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            if isinstance(item, Share):
                path = self.share.format.shareItemPath()
            else:
                for (path, record) in self.manifest.iteritems():
                    if record['uuid'] == item.itsUUID:
                        return path

                path = "%s.%s" % (item.itsUUID, extension)
                self.manifest[path] = {'uuid':item.itsUUID, 'data':None}
            return path

        elif style == ImportExportFormat.STYLE_SINGLE:
            return self.shareName

        else:
            print "@@@MOR Raise an exception here"


    # Manifest mangement routines
    # The manifest keeps track of the state of shared items at the time of
    # last sync.  It is a dictionary keyed on "path" (not repo path, but
    # path at the external source), whose values are dictionaries containing
    # the item's internal UUID, external UUID, either a last-modified date
    # (if filesystem) or ETAG (if webdav), and the item's version (as in
    # what item.getVersion() returns)
    # 
    # If we tried to get an item but the transform failed, we add that resource
    # to the manifest with "" as the uuid

    def __clearManifest(self):
        self.manifest = {}

    def __addToManifest(self, path, item=None, data=None):
        # data is an ETAG, or last modified date

        if item is None:
            uuid = None
        else:
            uuid = item.itsUUID

        self.manifest[path] = {
         'uuid' : uuid,
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
        """
        Do we have the latest copy of this item?
        """
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


    # Methods that subclasses *must* implement:

    def getLocation(self):
        """
        Return a string representing where the share is being exported
        to or imported from, such as a URL or a filesystem path
        """
        pass

    def _getResourceList(self, location):
        """
        Return a dictionary representing what items exist in the remote
        share.
        """
        # 'location' is a location returned from getLocation
        # The returned dictionary should be keyed on a string that uniquely
        # identifies a resource in the remote share.  For example, a url
        # path or filesystem path.  The values of the dictionary should
        # be dictionaries of the format { 'data' : <string> } where <string>
        # is some piece of data that encapsulates version information for
        # the remote resources (such as a last modified date, or an ETag).
        pass

    def _putItem(self, item, where):
        """
        Must implement
        """
        pass

    def _deleteItem(self, itemPath):
        """
        Must implement
        """
        pass

    def _getItem(self, itemPath, into=None):
        """
        Must implement
        """
        pass

    def connect(self):
        pass

    def disconnect(self):
        pass

    def exists(self):
        pass

    def create(self):
        """
        Create the share on the server.
        """
        pass

    def destroy(self):
        """
        Remove the share from the server.
        """
        pass

    def open(self):
        """
        Open the share for access.
        """
        pass

    def close(self):
        """
        Close the share.
        """
        pass


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class FileSystemConduit(ShareConduit):

    schema.kindInfo(displayName=u"File System Share Conduit Kind")


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

    def getLocation(self):
        if self.hasLocalAttributeValue("sharePath") and \
         self.hasLocalAttributeValue("shareName"):
            return os.path.join(self.sharePath, self.shareName)
        raise Misconfigured(_(u"A misconfiguration error was encountered"))

    def _putItem(self, item):
        path = self.__getItemFullPath(self._getItemPath(item))

        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            logging.exception(e)
            raise TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

        if text is None:
            return None
        out = file(path, 'wb') #outputting in binary mode to preserve ics CRLF
        out.write(text.encode('utf-8'))
        out.close()
        stat = os.stat(path)
        return stat.st_mtime

    def _deleteItem(self, itemPath):
        path = self.__getItemFullPath(itemPath)

        logger.info("...removing from disk: %s" % path)
        os.remove(path)

    def _getItem(self, itemPath, into=None):
        view = self.itsView

        # logger.info("Getting item: %s" % itemPath)
        path = self.__getItemFullPath(itemPath)

        extension = os.path.splitext(path)[1].strip(os.path.extsep)
        text = file(path).read()

        try:
            item = self.share.format.importProcess(text,
                extension=extension, item=into)
        except Exception, e:
            logging.exception(e)
            raise TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

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
            raise AlreadyExists(_(u"Share path already exists"))

        if self.sharePath is None or not os.path.isdir(self.sharePath):
            raise Misconfigured(_(u"Share path is not set, or path doesn't exist"))

        style = self.share.format.fileStyle()
        if style == ImportExportFormat.STYLE_DIRECTORY:
            path = self.getLocation()
            if not os.path.exists(path):
                os.mkdir(path)

    def destroy(self):
        super(FileSystemConduit, self).destroy()

        path = self.getLocation()

        if not self.exists():
            raise NotFound(_(u"%(path)s does not exist") % {'path': path})

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
            raise NotFound(_(u"%(path)s does not exist") % {'path': path})

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVConduit(ShareConduit):

    schema.kindInfo(displayName=u"WebDAV Share Conduit Kind")

    account = schema.One('WebDAVAccount', inverse = 'conduits')
    host = schema.One(schema.String)
    port = schema.One(schema.Integer)
    username = schema.One(schema.String)
    password = schema.One(schema.String)
    useSSL = schema.One(schema.Boolean)

    # The ticket this conduit will use (we're a sharee and we're using this)
    ticket = schema.One(schema.String, initialValue="")

    # The tickets we generated if we're a sharer
    ticketReadOnly = schema.One(schema.String, initialValue="")
    ticketReadWrite = schema.One(schema.String, initialValue="")

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 shareName=None, account=None, host=None, port=80,
                 sharePath=None, username="", password="", useSSL=False,
                 ticket=""):
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
            self.ticket = ticket

        if shareName is None:
            self.shareName = str(UUID())
        else:
            # @@@MOR Probably should remove any slashes, or warn if there are
            # any?
            self.shareName = shareName.strip("/")

        self.onItemLoad()

    def onItemLoad(self, view=None):
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

    def getLocation(self, privilege=None, includeShare=True):
        """
        Return the url of the share
        """

        (host, port, sharePath, username, password, useSSL) = \
            self.__getSettings()
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
        if includeShare:
            url = urlparse.urljoin(url, self.shareName)

        if privilege == 'readonly':
            if self.ticketReadOnly:
                url = url + "?ticket=%s" % self.ticketReadOnly
        elif privilege == 'readwrite':
            if self.ticketReadWrite:
                url = url + "?ticket=%s" % self.ticketReadWrite
        elif privilege == 'subscribed':
            if self.ticket:
                url = url + "?ticket=%s" % self.ticket

        return url

    def __getSharePath(self):
        return "/" + self.__getSettings()[2]

    def __resourceFromPath(self, path):

        serverHandle = self._getServerHandle()
        sharePath = self.__getSharePath()

        resourcePath = "%s/%s" % (sharePath, self.shareName)

        if self.share.format.fileStyle() == ImportExportFormat.STYLE_DIRECTORY:
            resourcePath += "/" + path

        resource = serverHandle.getResource(resourcePath)
        if getattr(self, 'ticket', False):
            resource.ticketId = self.ticket
        return resource

    def exists(self):
        result = super(WebDAVConduit, self).exists()

        resource = self.__resourceFromPath("")

        try:
            result = self._getServerHandle().blockUntil(resource.exists)
        except zanshin.error.ConnectionError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err.args[0]})
        except M2Crypto.BIO.BIOError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except zanshin.webdav.PermissionsError, err:
            message = _(u"Not authorized to PUT %(info)s") % {'info': self.getLocation()}
            logging.exception(err)
            raise NotAllowed(message)


        return result

    def _createCollectionResource(self, handle, resource, childName):
        return handle.blockUntil(resource.createCollection, childName)

    def create(self):
        super(WebDAVConduit, self).create()

        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            url = self.getLocation()
            handle = self._getServerHandle()
            try:
                if url[-1] != '/': url += '/'

                # need to get resource representing the parent of the
                # collection we want to create

                # Get the parent directory of the given path:
                # '/dev1/foo/bar' becomes ['dev1', 'foo', 'bar']
                path = url.strip('/').split('/')
                parentPath = path[:-1]
                childName = path[-1]
                # ['dev1', 'foo'] becomes "dev1/foo"
                url = "/".join(parentPath)
                resource = handle.getResource(url)
                if getattr(self, 'ticket', False):
                    resource.ticketId = self.ticket

                child = self._createCollectionResource(handle, resource,
                    childName)

            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.http.HTTPError, err:
                logger.error('Received status %d attempting to create %s',
                             err.status, self.getLocation())

                if err.status == twisted.web.http.NOT_ALLOWED:
                    # already exists
                    message = _(u"Collection at %(url)s already exists") % {'url': url}
                    raise AlreadyExists(message)

                if err.status == twisted.web.http.UNAUTHORIZED:
                    # not authorized
                    message = _(u"Not authorized to create collection %(url)s") % {'url': url}
                    raise NotAllowed(message)

                if err.status == twisted.web.http.CONFLICT:
                    # this happens if you try to create a collection within a
                    # nonexistent collection
                    (host, port, sharePath, username, password, useSSL) = \
                        self.__getSettings()
                    message = _(u"The directory '%(directoryName)s' could not be found on %(server)s.\nPlease verify the Path setting in your %(accountType)s account") % {'directoryName': sharePath, 'server': host,
                                                        'accountType': 'WebDAV'}
                    raise NotFound(message)

                if err.status == twisted.web.http.FORBIDDEN:
                    # the server doesn't allow the creation of a collection here
                    message = _(u"Server doesn't allow the creation of collections at %(url)s") % {'url': url}
                    raise IllegalOperation(message)

                if err.status != twisted.web.http.CREATED:
                     message = _(u"WebDAV error, status = %(statusCode)d") % {'statusCode': err.status}
                     raise IllegalOperation(message)

    def destroy(self):
        if self.exists():
            self._deleteItem("")

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

        resource = serverHandle.getResource(path)
        if getattr(self, 'ticket', False):
            resource.ticketId = self.ticket
        return resource


    def _putItem(self, item):
        """
        putItem should publish an item and return etag/date, etc.
        """

        try:
            text = self.share.format.exportProcess(item)
        except Exception, e:
            logging.exception(e)
            msg = _(u"Transformation failed for %(item)s") % {'item': item}
            raise TransformationFailed(msg)

        if text is None:
            return None

        contentType = self.share.format.contentType(item)
        itemName = self._getItemPath(item)
        container = self.__getContainerResource()

        try:
            # @@@MOR For some reason, when doing a PUT on the rpi server, I
            # can see it's returning 400 Bad Request, but zanshin doesn't
            # seem to be raising an exception.  Putting in a check for
            # newResource == None as another indicator that it failed to
            # create the resource
            newResource = None

            newResource = self._getServerHandle().blockUntil(
                                    container.createFile, itemName, body=text,
                                    type=contentType)
        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        # 201 = new, 204 = overwrite

        except zanshin.webdav.PermissionsError:
            message = _(u"Not authorized to PUT %(info)s") % {'info': itemName}
            raise NotAllowed(message)

        except zanshin.webdav.WebDAVError, err:

            if err.status == twisted.web.http.FORBIDDEN or \
               err.status == twisted.web.http.CONFLICT:
                # seen if trying to PUT to a nonexistent collection (@@@MOR verify)
                message = _(u"Publishing %(itemName)s failed; server rejected our request with status %(status)d") % {'itemName': itemName, 'status': err.status}
                raise NotAllowed(message)

        if newResource is None:
            message = _(u"Not authorized to PUT %(itemName)s") % {'itemName': itemName}
            raise NotAllowed(message)

        etag = newResource.etag

        # @@@ [grant] Get mod-date?
        return etag

    def _deleteItem(self, itemPath):
        resource = self.__resourceFromPath(itemPath)
        logger.info("...removing from server: %s" % resource.path)

        if resource != None:
            try:
                deleteResp = self._getServerHandle().blockUntil(resource.delete)
            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

    def _getItem(self, itemPath, into=None):
        view = self.itsView
        resource = self.__resourceFromPath(itemPath)

        try:
            resp = self._getServerHandle().blockUntil(resource.get)

        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        if resp.status == twisted.web.http.NOT_FOUND:
            message = _(u"Path %(path)s not found") % {'path': resource.path}
            raise NotFound(message)

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = _(u"Not authorized to GET %(path)s") % {'path': resource.path}
            raise NotAllowed(message)

        text = resp.body

        etag = resource.etag

        try:
            item = self.share.format.importProcess(text, item=into)
        except Exception, e:
            logger.exception("Failed to parse XML for item %s: '%s'" % (itemPath,
                                                                    text))
            raise TransformationFailed(_(u"%(itemPath)s %(error)s (See chandler.log for text)") % \
                                       {'itemPath': itemPath, 'error': e})

        return (item, etag)


    def _getResourceList(self, location): # must implement
        """
        Return information (etags) about all resources within a collection
        """

        resourceList = {}

        style = self.share.format.fileStyle()

        if style == ImportExportFormat.STYLE_DIRECTORY:
            shareCollection = self.__getContainerResource()

            try:
                children = self._getServerHandle().blockUntil(
                                shareCollection.getAllChildren)

            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.webdav.WebDAVError, e:

                if e.status == twisted.web.http.NOT_FOUND:
                    raise NotFound(_(u"Path %(path)s not found") % {'path': shareCollection.path})

                if e.status == twisted.web.http.UNAUTHORIZED:
                    raise NotAllowed(_(u"Not authorized to get %(path)s") % {'path': shareCollection.path})

                raise SharingError(_(u"The following sharing error occurred: %(error)s") % {'error': e})


            for child in children:
                if child != shareCollection:
                    path = child.path.split("/")[-1]
                    etag = child.etag
                    if path:
                        resourceList[path] = { 'data' : etag }
                    else:
                        logger.info("Child has no path")

        elif style == ImportExportFormat.STYLE_SINGLE:
            resource = self._getServerHandle().getResource(location)
            if getattr(self, 'ticket', False):
                resource.ticketId = self.ticket
            # @@@ [grant] Error handling and reporting here
            # are crapski
            try:
                self._getServerHandle().blockUntil(resource.propfind, depth=0)
            except zanshin.webdav.ConnectionError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except M2Crypto.BIO.BIOError, err:
                raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
            except zanshin.webdav.PermissionsError, err:
                message = _(u"Not authorized to GET %(path)s") % {'path': location}
                raise NotAllowed(message)
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

    def createTickets(self):
        handle = self._getServerHandle()
        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        resource = handle.getResource(location)

        ticket = handle.blockUntil(resource.createTicket)
        logger.debug("Read Only ticket: %s %s",
            ticket.ticketId, ticket.ownerUri)
        self.ticketReadOnly = ticket.ticketId

        ticket = handle.blockUntil(resource.createTicket, readonly=False)
        logger.debug("Read Write ticket: %s %s",
            ticket.ticketId, ticket.ownerUri)
        self.ticketReadWrite = ticket.ticketId

        return (self.ticketReadOnly, self.ticketReadWrite)



class CalDAVConduit(WebDAVConduit):

    def _createCollectionResource(self, handle, resource, childName):
        return handle.blockUntil(resource.createCalendar, childName)

    def _getFilterClasses(self):
        return [CalendarEventMixin]



class SimpleHTTPConduit(WebDAVConduit):
    """
    Useful for get-only subscriptions of remote .ics files
    """

    schema.kindInfo(displayName=u"Simple HTTP Share Conduit Kind")

    lastModified = schema.One(schema.String, initialValue = '')

    def get(self):
        self.connect()

        location = self.getLocation()
        logger.info("Starting GET of %s" % (location))
        extraHeaders = { }
        if self.lastModified:
            extraHeaders['If-Modified-Since'] = self.lastModified
            logger.info("...last modified: %s" % self.lastModified)

        try:
            handle = self._getServerHandle()
            resp = handle.blockUntil(handle.get, location,
                                    extraHeaders=extraHeaders)

            if resp.status == twisted.web.http.NOT_MODIFIED:
                # The remote resource is as we saw it before
                logger.info("...not modified")
                return

        except zanshin.webdav.ConnectionError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        if resp.status == twisted.web.http.NOT_FOUND:
            raise NotFound(_(u"%(location)s does not exist") % {'location': location})

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = _(u"Not authorized to GET %(path)s") % {'path': location}
            raise NotAllowed(message)

        logger.info("...received; processing...")

        try:
            text = resp.body
            self.share.format.importProcess(text, item=self.share)

            # The share maintains bi-di-refs between Share and Item:
            for item in self.share.contents:
                self.share.items.append(item)

        except Exception, e:
            logging.exception(e)
            raise TransformationFailed(_(u"Transformation error: see chandler.log for more information"))

        lastModified = resp.headers.getHeader('Last-Modified')
        self.lastModified = lastModified[-1]
        logger.info("...imported, new last modified: %s" % self.lastModified)

    def put(self):
        logger.info("'put( )' not support in SimpleHTTPConduit")

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class OneTimeFileSystemShare(OneTimeShare):
    def __init__(self, path, name, formatclass, kind=None, view=None,
                 contents=None):
        conduit = FileSystemConduit(kind=kind, view=view, sharePath=path,
                                    shareName=name)
        format  = formatclass(view=view)
        super(OneTimeFileSystemShare, self).__init__(kind=kind, view=view,
                 contents=contents, conduit=conduit, format=format)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

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

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingError(ChandlerException):
    pass


class AlreadyExists(SharingError):
    """
    Exception raised if a share already exists.
    """

class NotFound(SharingError):
    """
    Exception raised if a share/resource wasn't found.
    """

class NotAllowed(SharingError):
    """
    Exception raised if we don't have access.
    """

class Misconfigured(SharingError):
    """
    Exception raised if a share isn't properly configured.
    """

class CouldNotConnect(SharingError):
    """
    Exception raised if a conduit can't connect to an external entity
    due to DNS/network problems.
    """
class IllegalOperation(SharingError):
    """
    Exception raised if the entity a conduit is communicating with is
    denying an operation for some reason not covered by other exceptions.
    """
class TransformationFailed(SharingError):
    """
    Exception raised if import or export process failed.
    """
class AlreadySubscribed(SharingError):
    """
    Exception raised if subscribing to an already-subscribed url
    """

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class WebDAVAccount(items.ContentItem):
    schema.kindInfo(
        displayName=messages.ACCOUNT % {'accountName': 'WebDAV Account'},
        description="A WebDAV 'Account'\n\n"
            "Issues:\n"
            "   Long term we're probably not going to treat WebDAV as an "
            "account, but rather how a web browser maintains URL-to-ACL "
            "mappings.\n",
    )
    username = schema.One(
        schema.String, displayName = messages.USERNAME, initialValue = '',
    )
    password = schema.One(
        schema.String,
        displayName = messages.PASSWORD,
        description = 
            'Issues: This should not be a simple string. We need some solution for '
            'encrypting it.\n',
        initialValue = '',
    )
    host = schema.One(
        schema.String,
        displayName = messages.HOST,
        doc = 'The hostname of the account',
        initialValue = '',
    )
    path = schema.One(
        schema.String,
        displayName = messages.PATH,
        doc = 'Base path on the host to use for publishing',
        initialValue = '',
    )
    port = schema.One(
        schema.Integer,
        displayName = messages.PORT,
        doc = 'The non-SSL port number to use',
        initialValue = 80,
    )
    useSSL = schema.One(
        schema.Boolean,
        displayName = _(u'Use secure connection (SSL/TLS)'),
        doc = 'Whether or not to use SSL/TLS',
        initialValue = False,
    )
    accountType = schema.One(
        displayName = _(u'Account Type'), initialValue = 'WebDAV',
    )
    conduits = schema.Sequence(WebDAVConduit, inverse = WebDAVConduit.account)

    def getLocation(self):
        """
        Return the base url of the account
        """

        if self.useSSL:
            scheme = "https"
            defaultPort = 443
        else:
            scheme = "http"
            defaultPort = 80

        if self.port == defaultPort:
            url = "%s://%s" % (scheme, self.host)
        else:
            url = "%s://%s:%d" % (scheme, self.host, self.port)

        sharePath = self.path.strip("/")
        url = urlparse.urljoin(url, sharePath + "/")
        return url

    @classmethod
    def findMatch(cls, view, url):
        """
        Find a WebDAV account which corresponds to a URL.

        The url being passed in is for a collection -- it will include the
        collection name in the url.  We need to find a webdav account who
        has been set up to operate on the parent directory of this collection.
        For example, if the url is http://pilikia.osafoundation.org/dev1/foo/
        we need to find an account whose schema+host+port match and whose path
        starts with /dev1

        Note: this logic assumes only one account will match; you aren't
        currently allowed to have to multiple webdav accounts pointing to the
        same scheme+host+port+path combination.

        @param view: The repository view object
        @type view: L{repository.persistence.RepositoryView}
        @param url: The url which points to a collection
        @type url: String
        @return: An account item, or None if no WebDAV account could be found.
        """

        (useSSL, host, port, path, query, fragment) = splitUrl(url)

        # Get the parent directory of the given path:
        # '/dev1/foo/bar' becomes ['dev1', 'foo']
        path = path.strip('/').split('/')[:-1]
        # ['dev1', 'foo'] becomes "dev1/foo"
        path = "/".join(path)

        for account in cls.iterItems(view):
            # Does this account's url info match?
            accountPath = account.path.strip('/')
            if account.useSSL == useSSL and account.host == host and \
               account.port == port and path.startswith(accountPath):
                return account

        return None


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ImportExportFormat(items.ContentItem):

    schema.kindInfo(displayName=u"Import/Export Format Kind")

    share = schema.One(Share, inverse = Share.format)

    STYLE_SINGLE = 'single' # Share represented by monolithic file
    STYLE_DIRECTORY = 'directory' # Share is a directory where each item has
                                  # its own file

    def fileStyle(self):
        """
        Should return 'single' or 'directory'
        """
        pass

    def shareItemPath(self):
        """
        Return the path for the file representing the Share item
        """
        return None # None indicates there is no file representing the Share
                    # item

    def contentType(self, item):
        return "text/plain"

class CloudXMLFormat(ImportExportFormat):

    schema.kindInfo(displayName=u"Cloud XML Import/Export Format Kind")

    cloudAlias = schema.One(schema.String)

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 cloudAlias='sharing'):
        super(CloudXMLFormat, self).__init__(name, parent, kind, view)
        self.cloudAlias = cloudAlias

    def fileStyle(self):
        return self.STYLE_DIRECTORY

    def extension(self, item):
        return "xml"

    def shareItemPath(self):
        return "share.xml"

    def importProcess(self, text, extension=None, item=None):
        doc = libxml2.parseDoc(text)
        node = doc.children
        try:

            # @@@MOR Disabling the use of queued notifications, as it is
            # not needed at the moment.  Leaving it in (commented out) in
            # case the need arises.

            # self.itsView.recordChangeNotifications()

            item = self.__importNode(node, item)

        finally:

            # self.itsView.playChangeNotifications()

            doc.freeDoc()

        return item

    def exportProcess(self, item, depth=0, items=None):

        if items is None:
            items = {}

        if depth == 0:
            result = '<?xml version="1.0" encoding="UTF-8"?>\n\n'
        else:
            result = ''

        # Collect the set of attributes that are used in this format
        attributes = self.share.getSharedAttributes(item)

        indent = "   "

        if items.has_key(item.itsUUID):
            result += indent * depth
            result += "<%s uuid='%s' />\n" % (item.itsKind.itsName,
                item.itsUUID)
            return result

        items[item.itsUUID] = 1

        result += indent * depth

        if item.itsKind.isMixin():
            classNames = []
            for kind in item.itsKind.superKinds:
                klass = kind.classes['python']
                className = "%s.%s" % (klass.__module__, klass.__name__)
                classNames.append(className)
            classes = ",".join(classNames)
        else:
            klass = item.itsKind.classes['python']
            classes = "%s.%s" % (klass.__module__, klass.__name__)

        result += "<%s class='%s' uuid='%s'>\n" % (item.itsKind.itsName,
                                                  classes,
                                                  item.itsUUID)

        depth += 1

        for attrName in attributes:

            if not hasattr(item, attrName):
                continue

            attrValue = item.getAttributeValue(attrName)
            if attrValue is None:
                continue


            otherName = item.itsKind.getOtherName(attrName, None, item, None)
            cardinality = item.getAttributeAspect(attrName, 'cardinality')
            attrType = item.getAttributeAspect(attrName, 'type')

            result += indent * depth

            if otherName: # it's a bidiref
                result += "<%s>\n" % attrName

                if cardinality == 'single':
                    if attrValue is not None:
                        result += self.exportProcess(attrValue, depth+1, items)

                elif cardinality == 'list':
                    for value in attrValue:
                        result += self.exportProcess(value, depth+1, items)

                elif cardinality == 'dict':
                    # @@@MOR
                    pass

                result += indent * depth

            else: # it's a literal (@@@MOR could be SingleRef though)

                result += "<%s" % attrName

                if cardinality == 'single':
                    if isinstance(attrValue, Lob):
                        mimeType = attrValue.mimetype
                        data = attrValue.getInputStream().read()
                        attrValue = base64.b64encode(data)
                        result += " mimetype='%s'" % mimeType

                    result += ">"
                    if isinstance(attrValue, Item):
                        result += "\n"
                        result += self.exportProcess(attrValue, depth+1, items)
                    else:
                        result += "<![CDATA[" + attrType.makeString(attrValue) + "]]>"

                elif cardinality == 'list':
                    result += ">"
                    depth += 1
                    result += "\n"

                    for value in attrValue:
                        result += indent * depth
                        result += "<value>%s</value>\n" % attrType.makeString(value)
                    depth -= 1

                    result += indent * depth

                elif cardinality == 'dict':
                    result += ">"
                    # @@@MOR
                    pass

            result += "</%s>\n" % attrName

        depth -= 1
        result += indent * depth
        result += "</%s>\n" % item.itsKind.itsName
        return result


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

        view = self.itsView
        kind = None
        kinds = []

        if item is None:

            uuidNode = node.hasProp('uuid')
            if uuidNode:
                try:
                    uuid = UUID(uuidNode.content)
                    item = self.itsView.findUUID(uuid)
                except Exception, e:
                    logger.exception("Problem processing uuid %s" % uuid)
                    return item
            else:
                uuid = None

        classNode = node.hasProp('class')
        if classNode:
            classNameList = classNode.content.split(",")
            for classPath in classNameList:
                try:
                    klass = schema.importString(classPath)
                    kind = klass.getKind(view)
                    if kind is not None:
                        kinds.append(kind)
                except ImportError:
                    pass
        else:
            # No kind means we're simply looking up an item by uuid and
            # returning it
            return item

        if len(kinds) == 0:
            # we don't have any of the kinds provided
            logger.info("No kinds found locally for %s" % classNameList)
            return None
        elif len(kinds) == 1:
            kind = kinds[0]
        else: # time to mixin
            kind = kinds[0].mixin(kinds[1:])

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

        # Set a temporary attribute that items can check to see if they're in
        # the middle of being imported:
        item._share_importing = True

        try:
            attributes = self.share.getSharedAttributes(item)
            for attrName in attributes:

                attrNode = self.__getNode(node, attrName)
                if attrNode is None:
                    if item.hasLocalAttributeValue(attrName):
                        item.removeAttributeValue(attrName)
                    continue

                otherName = item.itsKind.getOtherName(attrName, None, item, None)
                cardinality = item.getAttributeAspect(attrName, 'cardinality')
                type = item.getAttributeAspect(attrName, 'type')

                # This code depends on attributes having their type set, which
                # might not always be the case.  What should be done is to encode
                # the value type into the shared xml itself:

                if otherName or (isinstance(type, Item) and \
                    not isinstance(type, Type)): # it's a ref

                    if cardinality == 'single':
                        valueNode = attrNode.children
                        while valueNode and valueNode.type != "element":
                            # skip over non-elements
                            valueNode = valueNode.next
                        if valueNode:
                            valueItem = self.__importNode(valueNode)
                            if valueItem is not None:
                                logger.debug("for %s setting %s to %s" % \
                                    (item.getItemDisplayName().encode('utf8'),
                                     attrName,
                                     valueItem.getItemDisplayName().encode('utf8')))
                                item.setAttributeValue(attrName, valueItem)

                    elif cardinality == 'list':
                        valueNode = attrNode.children
                        while valueNode:
                            if valueNode.type == "element":
                                valueItem = self.__importNode(valueNode)
                                if valueItem is not None:
                                    logger.debug("for %s setting %s to %s" % \
                                        (item.getItemDisplayName().encode("utf8"),
                                         attrName,
                                         valueItem.getItemDisplayName().encode('utf8')))
                                    item.addValue(attrName, valueItem)

                            valueNode = valueNode.next

                    elif cardinality == 'dict':
                        pass

                else: # it's a literal

                    if cardinality == 'single':

                        mimeTypeNode = attrNode.hasProp('mimetype')
                        if mimeTypeNode: # Lob
                            mimeType = mimeTypeNode.content
                            value = base64.b64decode(attrNode.content)
                            value = utils.dataToBinary(item, attrName, value,
                                                       mimeType=mimeType)
                        else:
                            value = type.makeValue(attrNode.content)

                        logger.debug( "for %s setting %s to %s" % \
                            (item.getItemDisplayName().encode('utf8'),
                             attrName, value))
                        item.setAttributeValue(attrName, value)

                    elif cardinality == 'list':
                        values = []
                        valueNode = attrNode.children
                        while valueNode:
                            if valueNode.type == "element":
                                value = type.makeValue(valueNode.content)
                                values.append(value)
                            valueNode = valueNode.next
                        logger.debug("for %s setting %s to %s" % \
                            (item.getItemDisplayName().encode('utf8'), attrName, values))
                        item.setAttributeValue(attrName, values)

                    elif cardinality == 'dict':
                        pass

            # @@@MOR Hack to add imported modification items to the shared
            # collection as well.  This is a temporary fix for bugs 3790 and
            # 3954 (modification events need to get added to their master's
            # collection currently, although this may change)
            if hasattr(item, 'modificationFor'):
                if not item in self.share.contents:
                    self.share.contents.add(item)

        finally:
            del item._share_importing

        return item


