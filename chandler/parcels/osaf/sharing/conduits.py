#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__all__ = [
    'Conduit',
    'ServerConduit',
    'ManifestEngineMixin',
    'TokenEngineMixin',
    'HTTPMixin',
    'CosmoConduit',
    'SimpleHTTPConduit',
]

import shares, errors, formats, utility
from notifications import *
from application import schema
from osaf import pim
from repository.item.Item import Item
from chandlerdb.util.c import UUID
import logging
import M2Crypto.BIO
import WebDAV
import twisted.web.http
import zanshin
import urlparse
from i18n import ChandlerMessageFactory as _


logger = logging.getLogger(__name__)





class Conduit(pim.ContentItem):
    share = schema.One(shares.Share, inverse=shares.Share.conduit)





class ServerConduit(Conduit): # Not an accurate name; Andi added this when
                              # he added his p2p conduit

    itemsMarker = schema.One(schema.SingleRef)

    sharePath = schema.One(
        schema.Text,
        doc = "The parent 'directory' of the share",
    )

    shareName = schema.One(
        schema.Text, initialValue=u"",
        doc = "The 'directory' name of the share, relative to 'sharePath'",
    )


    def __init__(self, *args, **kw):

        if 'shareName' not in kw:
            kw['shareName'] = unicode(UUID())
        super(ServerConduit, self).__init__(*args, **kw)
        self.shareName = self.shareName.strip("/")

        self.itemsMarker = Item('itemsMarker', self, None)







class ManifestEngineMixin(pim.ContentItem):

    manifest = schema.Mapping(
        schema.Dictionary,
        doc = "Keeps track of 'remote' item information, such as last "
              "modified date or ETAG",
        initialValue = {}
    )

    def _conditionalPutItem(self, contentView, item, changes,
        updateCallback=None, forceUpdate=None):
        """
        Put an item if it's not on the server or is out of date
        """
        result = 'skipped'

        if not self.share.format.acceptsItem(item):
            return result

        # Assumes that self.resourceList has been populated:
        externalItemExists = self._externalItemExists(item)

        # logger.debug("Examining for put: %s, version=%d",
        #     item.getItemDisplayName().encode('utf8', 'replace'),
        #     item.getVersion())

        if not externalItemExists:
            result = 'added'
            needsUpdate = True
            reason = _(u"Not on server")

        else:
            if forceUpdate:
                needsUpdate = True
                result = 'modified'
                reason = 'forced update'
            else:
                needsUpdate = False

                # Check to see if the item or any of its itemCloud items have a
                # more recent version than the last time we synced
                for relatedItem in item.getItemCloud('sharing'):
                    if relatedItem.itsUUID in changes:
                        modifiedAttributes = changes[relatedItem.itsUUID]
                        sharedAttributes = \
                            self.share.getSharedAttributes(relatedItem.itsKind)
                        logger.debug("Changes for %s: %s", relatedItem.getItemDisplayName().encode('utf8', 'replace'), modifiedAttributes)
                        for change in modifiedAttributes:
                            if change in sharedAttributes:
                                logger.debug("A shared attribute (%s) changed for %s", change, relatedItem.getItemDisplayName())
                                needsUpdate = True
                                result = 'modified'
                                reason = change
                                break

        if needsUpdate:
            logger.info("...putting '%s' %s (%d vs %d) (%s)" %
                (
                    item.getItemDisplayName(), item.itsUUID, item.getVersion(),
                    self.itemsMarker.getVersion(), reason
                )
            )

            if updateCallback and updateCallback(msg="'%s'" %
                item.getItemDisplayName()):
                raise errors.SharingError(_(u"Cancelled by user"))

            # @@@MOR Disabling this for now
            # me = schema.ns('osaf.pim', item.itsView).currentContact.item
            # item.lastModifiedBy = me

            data = self._putItem(item)

            if data is not None:
                self._addToManifest(self._getItemPath(item), item, data)
                logger.info("...done, data: %s, version: %d" %
                 (data, item.getVersion()))

                cvSelf = contentView[self.itsUUID]
                cvSelf.share.items.append(item)
            else:
                return 'skipped'

        try:
            del self.resourceList[self._getItemPath(item)]
        except:
            logger.info("...external item %s didn't previously exist" % \
                self._getItemPath(item))

        return result


    @staticmethod
    def _matchesFilterClasses(item, filterClasses):
        if not filterClasses:
            return True

        for cls in filterClasses or [type(item)]:
            if issubclass(cls, pim.Stamp):
                matches = pim.has_stamp(item, cls)
            else:
                matches = isinstance(item, cls)
            if matches:
                return True
        return False

    def _put(self, contentView, resourceList, startVersion, endVersion,
             updateCallback=None, forceUpdate=None):
        """
        Transfer entire 'contents', transformed, to server.
        """

        view = self.itsView
        cvSelf = contentView[self.itsUUID]

        location = self.getLocation()
        logger.info("Starting PUT of %s" % (location))

        try:
            contentsName = "'%s' (%s)" % (self.share.contents.displayName,
                location)
        except:
            # contents is either not set, is None, or has no displayName
            contentsName = location

        if updateCallback and updateCallback(msg=_(u"Uploading to "
            "%(name)s...") % { 'name' : contentsName } ):
            raise errors.SharingError(_(u"Cancelled by user"))

        stats = {
            'share' : self.share.itsUUID,
            'op' : 'put',
            'added' : [],
            'modified' : [],
            'removed' : []
        }

        self.connect()

        # share.filterClasses includes the dotted names of classes so
        # they can be shared.
        filterClasses = self._getFilterClasses()

        style = self.share.format.fileStyle()
        if style == formats.STYLE_DIRECTORY:

            if resourceList is None:
                msg = _(u"Getting list of remote items...")
                if updateCallback and updateCallback(msg=msg):
                    raise errors.SharingError(_(u"Cancelled by user"))
                self.resourceList = self._getResourceList(location)
            else:
                self.resourceList = resourceList

            # logger.debug("Resources on server: %(resources)s" %
            #     {'resources':self.resourceList})
            # logger.debug("Manifest: %(manifest)s" %
            #     {'manifest':self.manifest})

            # Ignore any resources which we weren't able to parse during
            # a previous GET -- they're the ones in our manifest with
            # None as a uuid:
            for (path, record) in self.manifest.iteritems():
                if record['uuid'] is None:
                    if self.resourceList.has_key(path):
                        logger.debug('Removing an unparsable resource from the resourceList: %(path)s' % { 'path' : path })
                        del self.resourceList[path]

            changes = utility.localChanges(contentView, startVersion, endVersion)

            # If we're sharing a collection, put the collection's items
            # individually:
            if isinstance(cvSelf.share.contents, pim.ContentCollection):

                #
                # Remove any resources from the server that aren't in
                # our collection anymore.  The reason we have to do this
                # first is because if one .ics resource is replacing
                # another (on a CalDAV server) and they have the same
                # icalUID, the CalDAV server won't allow them to exist
                # simultaneously.
                # Any items that are in the manifest but not in the
                # collection are the ones to remove.

                removeFromManifest = []

                for (path, record) in self.manifest.iteritems():
                    if path in self.resourceList:
                        uuid = record['uuid']
                        if uuid:
                            item = contentView.findUUID(uuid)

                            if item is not cvSelf.share and (
                                item is None or
                                item not in cvSelf.share.contents or 
                                not self._matchesFilterClasses(item,
                                                               filterClasses)
                            ):

                                if updateCallback and updateCallback(msg=_(u"Removing item from server: '%(path)s'") % { 'path' : path }):
                                    raise errors.SharingError(_(u"Cancelled by user"))
                                self._deleteItem(path)
                                del self.resourceList[path]
                                removeFromManifest.append(path)
                                logger.debug('Item removed locally, so removing from server: %(path)s' % { 'path' : path })
                                stats['removed'].append(uuid)

                for path in removeFromManifest:
                    self._removeFromManifest(path)

                # logger.debug("Manifest: %(manifest)s" %
                #     {'manifest':self.manifest})


                for item in cvSelf.share.contents:

                    if updateCallback and updateCallback(work=True):
                        raise errors.SharingError(_(u"Cancelled by user"))

                    # Skip private items
                    if item.private:
                        continue

                    # Skip any items not matching the filtered classes
                    if not self._matchesFilterClasses(item, filterClasses):
                        continue

                    # Put the item
                    result = self._conditionalPutItem(contentView, item,
                        changes, updateCallback=updateCallback,
                        forceUpdate=forceUpdate)
                    if result in ('added', 'modified'):
                        stats[result].append(item.itsUUID)


            # Put the Share item itself
            result = self._conditionalPutItem(contentView, cvSelf.share,
                changes, updateCallback=updateCallback,
                forceUpdate=forceUpdate)
            if result in ('added', 'modified'):
                stats[result].append(self.share.itsUUID)


        elif style == formats.STYLE_SINGLE:
            # Put a monolithic file representing the share item.
            #@@@MOR This should be beefed up to only publish if at least one
            # of the items has changed.
            self._putItem(cvSelf.share)


        self.disconnect()

        logger.info("Finished PUT of %s", location) # , stats)

        return stats



    def _conditionalGetItem(self, contentView, itemPath, into=None,
        updateCallback=None, stats=None):
        """
        Get an item from the server if we don't yet have it or our copy
        is out of date
        """

        cvSelf = contentView.findUUID(self.itsUUID)

        # assumes self.resourceList is populated

        if itemPath not in self.resourceList:
            logger.info("...Not on server: %s" % itemPath)
            return None

        if not self._haveLatest(itemPath):
            # logger.info("...getting: %s" % itemPath)

            try:
                (item, data) = self._getItem(contentView, itemPath, into=into,
                    updateCallback=updateCallback, stats=stats)
            except errors.MalformedData:
                # This has already been logged; catch it and return None
                # to allow the sync to proceed.
                return None

            if item is not None:
                self._addToManifest(itemPath, item, data)
                self._setFetched(itemPath)
                logger.info("...imported '%s' '%s' %s, data: %s" % \
                 (itemPath, item.getItemDisplayName().encode('ascii',
                    'replace'), item, data))

                cvSelf.share.items.append(item)
                if updateCallback and updateCallback(msg="'%s'" %
                    item.getItemDisplayName()):
                    raise errors.SharingError(_(u"Cancelled by user"))

                return item

            logger.error("...NOT able to import '%s'" % itemPath)
            # Record with no item, indicating an error
            self._addToManifest(itemPath)

        return None




    def _get(self, contentView, resourceList, updateCallback=None,
             getPhrase=None):
        # cvSelf (contentViewSelf) is me as I was in the past
        cvSelf = contentView.findUUID(self.itsUUID)

        location = self.getLocation()
        logger.info("Starting GET of %s" % (location))

        try:
            contentsName = "'%s' (%s)" % (self.share.contents.displayName,
                location)
        except:
            # contents is either not set, is None, or has no displayName
            contentsName = location

        if getPhrase is None:
            getPhrase = _(u"Downloading from %(name)s...")
        if updateCallback and updateCallback(msg=getPhrase %
            { 'name' : contentsName } ):
            raise errors.SharingError(_(u"Cancelled by user"))

        view = self.itsView

        stats = {
            'share' : self.share.itsUUID,
            'op' : 'get',
            'added' : [],
            'modified' : [],
            'removed' : []
        }

        self.connect()

        if not self.exists():
            raise errors.NotFound(_(u"%(location)s does not exist") %
                {'location': location})

        if resourceList is None:
            msg = _(u"Getting list of remote items...")
            if updateCallback and updateCallback(msg=msg):
                raise errors.SharingError(_(u"Cancelled by user"))
            self.resourceList = self._getResourceList(location)
            totalWork = len(self.resourceList)
            if updateCallback and updateCallback(totalWork=totalWork):
                raise errors.SharingError(_(u"Cancelled by user"))
                updateCallback(totalWork=count)
        else:
            # make a copy, because we use it destructively
            self.resourceList = dict(resourceList)

        msg = _(u"Processing...")
        if updateCallback and updateCallback(msg=msg):
            raise errors.SharingError(_(u"Cancelled by user"))

        # logger.debug("Resources on server: %(resources)s" %
        #     {'resources':self.resourceList})
        # logger.debug("Manifest: %(manifest)s" %
        #     {'manifest':self.manifest})

        # We need to keep track of which items we've seen on the server so
        # we can tell when one has disappeared.
        self._resetFlags()

        itemPath = self._getItemPath(self.share)
        # if itemPath is None, the Format we're using doesn't have a file
        # that represents the Share item (CalDAV, for instance).

        if itemPath:
            # Get the file that represents the Share item

            if updateCallback and updateCallback(work=True):
                raise errors.SharingError(_(u"Cancelled by user"))

            item = self._conditionalGetItem(contentView, itemPath,
                into=cvSelf.share, updateCallback=updateCallback, stats=stats)

            # Whenever we get an item, mark it seen in our manifest and remove
            # it from the server resource list:
            self._setSeen(itemPath)
            try:
                del self.resourceList[itemPath]
            except:
                pass

        # Make sure we don't subscribe to a KindCollection, since some evil
        # person could slip you a KindCollection that would fill itself with
        # your items.
        if isinstance(cvSelf.share.contents, pim.KindCollection):
            raise errors.SharingError(_(u"Subscribing to KindCollections prohibited"))

        # Make sure we have a collection to add items to:
        if cvSelf.share.contents is None:
            cvSelf.share.contents = pim.SmartCollection(itsView=contentView)

        contents = cvSelf.share.contents

        # If share.contents is an ContentCollection, treat other resources as
        # items to add to the collection:
        if isinstance(contents, pim.ContentCollection):

            filterClasses = self._getFilterClasses()

            # If an item is in the manifest but it's no longer in the
            # collection, we need to skip the server's copy -- we'll
            # remove it during the PUT phase
            for (path, record) in self.manifest.iteritems():
                if path in self.resourceList:
                    uuid = record['uuid']
                    if uuid:
                        item = view.findUUID(uuid)
                        if item is None or \
                            item not in contents:
                            del self.resourceList[path]
                            self._setSeen(path)
                            logger.debug("Item removed locally, so not "
                                "fetching from server: %(path)s" %
                                { 'path' : path } )


            # Conditionally fetch items, and add them to collection
            for itemPath in self.resourceList:

                if updateCallback and updateCallback(work=True):
                    raise errors.SharingError(_(u"Cancelled by user"))

                item = self._conditionalGetItem(contentView, itemPath,
                    updateCallback=updateCallback, stats=stats)

                if item is not None:
                    cvSelf.share.contents.add(item)

                self._setSeen(itemPath)

            # When first importing a collection, name it after the share
            if not getattr(cvSelf.share.contents, 'displayName', ''):
                cvSelf.share.contents.displayName = \
                    self._getDisplayNameForShare(cvSelf.share)

            # If an item was previously on the server (it was in our
            # manifest) but is no longer on the server, remove it from
            # the collection locally:
            toRemove = []
            for unseenPath in self._iterUnseen():
                uuid = self.manifest[unseenPath]['uuid']
                if uuid:
                    item = contentView.findUUID(uuid)
                    if item is not None:

                        # If an item has disappeared from the server, only
                        # remove it locally if it matches the current share
                        # filter.

                        if (not filterClasses or
                            self._matchesFilterClasses(item, filterClasses)):

                            SharingNotification(itsView=contentView,
                                displayName="Removed item from collection")
                            logger.info("...removing %s from collection" % item)
                            if item in cvSelf.share.contents:
                                cvSelf.share.contents.remove(item)
                            if item in cvSelf.share.items:
                                cvSelf.share.items.remove(item)
                            stats['removed'].append(item.itsUUID)
                            if updateCallback and updateCallback(
                                msg=_(u"Removing from collection: '%(name)s'")
                                % { 'name' : item.getItemDisplayName() }
                                ):
                                raise errors.SharingError(_(u"Cancelled by user"))

                else:
                    logger.info("Removed an unparsable resource manifest entry for %s", unseenPath)

                # In any case, remove from manifest
                toRemove.append(unseenPath)

            for removePath in toRemove:
                self._removeFromManifest(removePath)

        self.disconnect()

        logger.info("Finished GET of %s", location) # , stats)

        return stats


    def _getFilterClasses(self):
        return tuple(schema.importString(classString) for classString in
            self.share.filterClasses)


    def _getItemPath(self, item):
        """
        Return a string that uniquely identifies a resource in the remote
        share, such as a URL path or a filesystem path.  These strings
        will be used for accessing the manifest and resourceList dicts.
        """
        extension = self.share.format.extension(item)
        style = self.share.format.fileStyle()
        if style == formats.STYLE_DIRECTORY:
            if isinstance(item, shares.Share):
                path = self.share.format.shareItemPath()
            else:
                for (path, record) in self.manifest.iteritems():
                    if record['uuid'] == item.itsUUID:
                        return path

                path = "%s.%s" % (item.itsUUID, extension)

            return path

        elif style == formats.STYLE_SINGLE:
            return self.shareName

        else:
            print "@@@MOR Raise an exception here"

    def _getDisplayNameForShare(self, share):
        """
        Return a C{str} (or C{unicode}) that specifies how the
        shared collection should be displayed. By default, this
        method just uses the share's displayName, but subclasses
        may override for custom behavior (e.g. fetching a DAV
        property).
        """
        return share.displayName
        
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

    def _clearManifest(self):
        self.manifest = {}

    def _addToManifest(self, path, item=None, data=None):
        # data is an ETAG, or last modified date

        if item is None:
            uuid = None
        else:
            uuid = item.itsUUID

        self.manifest[path] = {
         'uuid' : uuid,
         'data' : data,
        }


    def _removeFromManifest(self, path):
        try:
            del self.manifest[path]
        except:
            pass

    def _externalItemExists(self, item):
        itemPath = self._getItemPath(item)
        return itemPath in self.resourceList

    def _haveLatest(self, path, data=None):
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

        logger.info("...don't yet have %s" % path)
        return False

    def _resetFlags(self):
        for value in self.manifest.itervalues():
            value['seen'] = False
            value['fetched'] = False

    def _setSeen(self, path):
        try:
            self.manifest[path]['seen'] = True
        except:
            pass

    def _setFetched(self, path):
        try:
            self.manifest[path]['fetched'] = True
        except:
            pass

    def _wasFetched(self, path):
        try:
            return self.manifest[path]['fetched']
        except:
            return False

    def _iterUnseen(self):
        for (path, value) in self.manifest.iteritems():
            if not value['seen']:
                yield path


    # Methods that subclasses *must* implement:

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

    def _getItem(self, contentView, itemPath, into=None, updateCallback=None,
                 stats=None):
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



class TokenEngineMixin(pim.ContentItem):
    syncToken = schema.One(
        schema.Text,
        doc = "Sync token returned from Cosmo",
    )

class HTTPMixin(pim.ContentItem):

    account = schema.One('WebDAVAccount', inverse='conduits',initialValue=None)
    host = schema.One(schema.Text, initialValue=u"")
    port = schema.One(schema.Integer, initialValue=80)
    username = schema.One(schema.Text, initialValue=u"")
    password = schema.One(schema.Text, initialValue=u"")
    useSSL = schema.One(schema.Boolean, initialValue=False)
    inFreeBusy = schema.One(schema.Boolean, defaultValue=False)

    # The ticket this conduit will use (we're a sharee and we're using this)
    ticket = schema.One(schema.Text, initialValue="")

    # The tickets we generated if we're a sharer
    ticketReadOnly = schema.One(schema.Text, initialValue="")
    ticketReadWrite = schema.One(schema.Text, initialValue="")

    def __init__(self, *args, **kw):
        super(HTTPMixin, self).__init__(*args, **kw)
        self.onItemLoad() # Get a chance to clear out old connection

    def onItemLoad(self, view=None):
        self.serverHandle = None

    def _getSettings(self):
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
            # logger.debug("...creating new webdav ServerHandle")
            (host, port, sharePath, username, password, useSSL) = \
            self._getSettings()

            # The certstore parcel ends up doing a refresh( ) in the
            # middle of an SSL sync operation, which pollutes the sharing
            # view.  To work around this, pass the main view to certstore,
            # by way of zanshin.
            sslView = self.itsView.repository.views[0] # main repo view

            self.serverHandle = WebDAV.ChandlerServerHandle(host, port=port,
                username=username, password=password, useSSL=useSSL,
                repositoryView=sslView)

        return self.serverHandle

    def _releaseServerHandle(self):
        self.serverHandle = None


    def getLocation(self, privilege=None):
        """
        Return the url of the share
        """

        (host, port, sharePath, username, password, useSSL) = \
            self._getSettings()
        if useSSL:
            scheme = u"https"
            defaultPort = 443
        else:
            scheme = u"http"
            defaultPort = 80

        if port == defaultPort:
            url = u"%s://%s" % (scheme, host)
        else:
            url = u"%s://%s:%d" % (scheme, host, port)
        if self.shareName == '':
            url = urlparse.urljoin(url, sharePath)
        else:
            url = urlparse.urljoin(url, sharePath + "/")
            url = urlparse.urljoin(url, self.shareName)

        if privilege == 'readonly':
            if self.ticketReadOnly:
                url = url + u"?ticket=%s" % self.ticketReadOnly
        elif privilege == 'readwrite':
            if self.ticketReadWrite:
                url = url + u"?ticket=%s" % self.ticketReadWrite
        elif privilege == 'subscribed':
            if self.ticket:
                url = url + u"?ticket=%s" % self.ticket

        return url


class CosmoConduit(ServerConduit, TokenEngineMixin, HTTPMixin):
    pass






class SimpleHTTPConduit(ServerConduit, HTTPMixin):
    """
    Useful for get-only subscriptions of remote .ics files
    """

    lastModified = schema.One(schema.Text, initialValue = '')

    def _get(self, contentView, resourceList, updateCallback=None):

        stats = {
            'share' : self.share.itsUUID,
            'op' : 'get',
            'added' : [],
            'modified' : [],
            'removed' : []
        }

        view = self.itsView

        location = self.getLocation(privilege='readonly')
        if updateCallback and updateCallback(msg=_(u"Checking for update: '%(location)s'") % { 'location' : location } ):
            raise errors.SharingError(_(u"Cancelled by user"))

        self.connect()
        logger.info("Starting GET of %s" % (location))
        extraHeaders = { }
        if self.lastModified:
            extraHeaders['If-Modified-Since'] = self.lastModified
            logger.info("...last modified: %s" % self.lastModified)
        if self.ticket:
            extraHeaders['Ticket'] = self.ticket

        try:
            handle = self._getServerHandle()
            resp = handle.blockUntil(handle.get, location,
                                    extraHeaders=extraHeaders)

            if resp.status == twisted.web.http.NOT_MODIFIED:
                # The remote resource is as we saw it before
                if updateCallback and updateCallback(msg=_(u"Not modified")):
                    raise errors.SharingError(_(u"Cancelled by user"))
                logger.info("...not modified")
                return stats

            if updateCallback and updateCallback(msg='%s' % location):
                raise errors.SharingError(_(u"Cancelled by user"))

        except zanshin.webdav.ConnectionError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
        except M2Crypto.BIO.BIOError, err:
            raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})

        if resp.status == twisted.web.http.NOT_FOUND:
            raise errors.NotFound(_(u"%(location)s does not exist") % {'location': location})

        if resp.status == twisted.web.http.UNAUTHORIZED:
            message = _(u"Not authorized to GET %(path)s") % {'path': location}
            raise errors.NotAllowed(message)

        logger.info("...received; processing...")
        if updateCallback and updateCallback(msg=_(u"Processing: '%s'") % location):
            raise errors.SharingError(_(u"Cancelled by user"))

        try:
            text = resp.body
            cvSelf = contentView.findUUID(self.itsUUID)
            self.share.format.importProcess(contentView, text,
                item=cvSelf.share, updateCallback=updateCallback,
                stats=stats)

            # The share maintains bi-di-refs between Share and Item:
            for item in cvSelf.share.contents:
                cvSelf.share.items.append(item)

        except errors.MalformedData:
            logger.exception("Failed to parse: '%s'" %
                text.encode('utf8', 'replace'))
            raise

        lastModified = resp.headers.getHeader('Last-Modified')
        if lastModified:
            self.lastModified = lastModified[-1]

        logger.info("...imported, new last modified: %s" % self.lastModified)

        return stats

    def put(self):
        logger.info("'put( )' not support in SimpleHTTPConduit")

