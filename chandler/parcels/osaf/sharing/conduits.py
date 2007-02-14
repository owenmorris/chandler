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
    'BaseConduit',
    'LinkableConduit',
    'ManifestEngineMixin',
    'HTTPMixin',
    'SimpleHTTPConduit',
    'isReadOnlyMode',
    'setReadOnlyMode',
]

import shares, errors, formats, utility
from notifications import *
from callbacks import *
from application import schema
from osaf import pim
from repository.item.Item import Item
from repository.persistence.RepositoryError import MergeError
from chandlerdb.util.c import UUID
import zanshin, M2Crypto.BIO, twisted.web.http
import logging
import WebDAV
import urlparse
import datetime
from PyICU import ICUtzinfo
from i18n import ChandlerMessageFactory as _


logger = logging.getLogger(__name__)



# A flag to allow a developer to turn off all publishing while debugging
_readOnlyMode = False
def isReadOnlyMode():
    return _readOnlyMode
def setReadOnlyMode(active):
    global _readOnlyMode
    _readOnlyMode = active




class Conduit(pim.ContentItem):
    share = schema.One(shares.Share, inverse=shares.Share.conduit)

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):
        raise NotImplementedError


class BaseConduit(Conduit):

    itemsMarker = schema.One(schema.ItemRef)

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
        super(BaseConduit, self).__init__(*args, **kw)
        self.shareName = self.shareName.strip("/")

        self.itemsMarker = Item('itemsMarker', self, None)




class LinkableConduit(BaseConduit):

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):
        from formats import CloudXMLFormat
        from ICalendar import ICalendarFormat
        from webdav_conduit import WebDAVConduit
        from caldav_conduit import CalDAVConduit

        if _readOnlyMode:
            modeOverride='get'
            logger.warning("Sharing in read-only mode")

        def mergeFunction(code, item, attribute, value):
            # 'value' is the one from the *this* view
            # getattr(item, attribute) is the value from a different view

            if code == MergeError.DELETE:
                logger.debug("Sharing conflict on item %(item)s, "
                    "deleted locally, modified remotely",
                    { 'item' : item, }
                )
                return True

            # Uncomment to get sharing conflict log messages:
            # if logger.getEffectiveLevel() <= logging.DEBUG:
            #     logger.debug("Sharing conflict on item %(item)s, attribute "
            #         "%(attribute)s: %(local)s vs %(remote)s", {
            #             'item' : item,
            #             'attribute' : attribute,
            #             'local' : unicode(getattr(item, attribute,
            #                 Nil)).encode('utf8'),
            #             'remote' : unicode(value).encode('utf8'),
            #         })

            # @@@MOR Probably not a good idea to create new items inside the
            # conflict resolution callback.
            #
            # Commenting out for now
            # SharingConflictNotification(itsView=item.itsView,
            #     displayName="Conflict for attribute %s" % attribute,
            #     attribute=attribute,
            #     local=unicode(getattr(item, attribute, None)),
            #     remote=unicode(value),
            #     items=[item])

            # if updateCallback:
            #     updateCallback(
            #         msg=_(u"Conflict for item '%(name)s' "
            #         "attribute: %(attribute)s '%(local)s' vs '%(remote)s'") %
            #         (
            #             {
            #                'name' : item.displayName,
            #                'attribute' : attribute,
            #                'local' : unicode(getattr(item, attribute, Nil))
            #                'remote' : unicode(value),
            #             }
            #         )
            #     )

            LOCAL_CHANGES_WIN = False

            if LOCAL_CHANGES_WIN:
                return getattr(item, attribute, Nil) # Change from *other* views
            else:
                return value                         # Change from *this* view



        linkedShares = self.share.getLinkedShares()
        metaView = linkedShares[0].itsView

        itemsMarker = linkedShares[0].conduit.itemsMarker

        stats = []

        timeTravel = False
        for share in linkedShares:

            # resourceList is a non-persistent snapshot of what's on the server
            # (or filesystem, etc.)
            share.resourceList = None

            # The CloudXML and ICalendar Formats require rolling back the
            # sharing view (aka time travel)
            if (isinstance(share.format, CloudXMLFormat) or
                isinstance(share.format, ICalendarFormat)):
                    timeTravel = True


        # Don't commit if we're using a OneTimeShare
        commit = not isinstance(linkedShares[0], shares.OneTimeShare)

        established = linkedShares[0].established
        if established and timeTravel:
            # If established and timeTravel is required by the format(s) in use,
            # we'll use our special 'Sharing' view, rolling it back
            # in history to the way it was at last sync, just after the commit()
            # that followed the previous GET

            for existingView in metaView.repository.views:
                if existingView.name == 'Sharing':
                    contentView = existingView
                    logger.debug("Using existing sharing view")
                    break
            else:
                contentView = metaView.repository.createView("Sharing")
                logger.debug("Created new sharing view")

            syncVersion = itemsMarker.getVersion()
            logger.debug("(Established) Setting version to %d", syncVersion)

            contentView.refresh(lambda code, item, attr, val: val,
                version=syncVersion, notify=False)


        else:
            contentView = metaView
            logger.debug("No time travel; version is %d", contentView.itsVersion)

        # Make sure we aren't deferring the main repository view:
        if not isinstance(linkedShares[0], shares.OneTimeShare):
            contentView.deferDelete()

        if (len(linkedShares) > 1 and
            isinstance(linkedShares[0].conduit, WebDAVConduit) and
            isinstance(linkedShares[1].conduit, CalDAVConduit)):
            # This is a hybrid share, XML + ICS
            hybrid = True
        else:
            hybrid = False

        try:

            # Build the resource list(s) up front so that we don't examine
            # XML files at one point in time, and ICS files at another
            if hybrid:
                upper = linkedShares[1]
                lower = linkedShares[0]
                upper.resourceList = {}
                lower.resourceList = {}
                conduit = upper.conduit
                location = conduit.getLocation()
                if not location.endswith("/"):
                    location += "/"
                handle = conduit._getServerHandle()
                resource = handle.getResource(location)
                if getattr(conduit, 'ticket', False):
                    resource.ticketId = conduit.ticket

                msg = _(u"Getting list of remote items...")
                if updateCallback and updateCallback(msg=msg):
                    raise errors.SharingError(_(u"Cancelled by user"))

                try:
                    # @@@MOR Not all servers handle depty=infinity
                    children = handle.blockUntil(resource.propfind,
                                                 depth="infinity")

                except zanshin.webdav.ConnectionError, err:
                    raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
                except M2Crypto.BIO.BIOError, err:
                    raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': err})
                except zanshin.webdav.WebDAVError, e:
                    if e.status == twisted.web.http.NOT_FOUND:
                        raise errors.NotFound(_(u"%(location)s not found") % {'location': location})
                    if e.status == twisted.web.http.UNAUTHORIZED:
                        raise errors.NotAllowed(_(u"Not authorized to get %(location)s") % {'location': location})

                    raise errors.SharingError(_(u"The following sharing error occurred: %(error)s") % {'error': e})

                count = 0
                for child in children:
                    pieces = child.path.split("/")
                    name = pieces[-1]
                    dirName = pieces[-2]
                    etag = child.etag
                    # if name is empty, it's a subcollection (skip it)
                    if name:
                        count += 1
                        if dirName == ".chandler":
                            lower.resourceList[name] = { 'data' : etag }
                        else:
                            upper.resourceList[name] = { 'data' : etag }

                if not established and modeOverride == 'get' and updateCallback:
                    # An initial subscribe
                    updateCallback(totalWork=count)


            if not modeOverride or modeOverride == 'get':

                # perform the 'get' operations of all associated shares, applying
                # remote changes locally
                contents = None
                filterClasses = None
                for share in linkedShares:
                    if share.active and share.mode in ('get', 'both'):
                        cvShare = contentView[share.itsUUID]
                        if contents:
                            # If there are multiple shares involved, we take the
                            # resulting contents from the first Share and hand that
                            # to the remaining Shares:
                            cvShare.contents = contents
                        if filterClasses is not None:
                            # like 'contents' above, the filterClasses of a master
                            # share needs to be replicated to the slaves:
                            cvShare.filterClasses = filterClasses
                        stat = share.conduit._get(contentView, share.resourceList,
                            updateCallback=updateCallback)
                        stats.append(stat)

                        # Need to get contents/filterClasses that could have
                        # changed in the contentView:
                        contents = cvShare.contents
                        filterClasses = cvShare.filterClasses

                # Bug 4564 -- half baked calendar events (those with .xml resources
                # but not .ics resources)
                #
                # We need to detect/delete them from the repository.  This means
                # looking through the stats to find the items we just got from the
                # XML fork (linkedShares[0]), and making sure those items were also
                # modified via the ICS fork.  Any events that don't have an ICS
                # fork are removed locally. Next, we need to adjust the manifests
                # so that during the PUT phase we don't remove the .xml resources
                # from the server.

                if hybrid:
                    # This is a hybrid share, XML + ICS
                    share0 = metaView.findUUID(linkedShares[0].itsUUID)
                    share1 = metaView.findUUID(linkedShares[1].itsUUID)

                    for uuid in stats[0]['added']:
                        item = contentView.findUUID(uuid)
                        if uuid not in stats[1]['modified']:
                            item = contentView.findUUID(uuid)
                            if pim.has_stamp(item, pim.EventStamp):
                                if updateCallback:
                                    updateCallback(msg=_(u"Incomplete Event Detected: '%(name)s'") % { 'name': item.displayName } )

                                # This indicates the resource is to be ignored
                                # during PUT (otherwise we would remove the .xml
                                # resource since the item isn't in our local copy
                                # of the collection:
                                itemPath = share0.conduit._getItemPath(item)
                                share0.conduit._addToManifest(itemPath, None)
                                logger.info("Incomplete event: '%s' %s" %
                                    (item.displayName, itemPath))
                                item.delete(True)


            for share in linkedShares:
                cvShare = contentView[share.itsUUID]
                cvShare.conduit.itemsMarker.setDirty(Item.NDIRTY)

            # Remember the version of the itemsMarker -- it marks the starting
            # point at which to look for changes in the repository history
            # during the upcoming PUT phase
            putStartingVersion = cvShare.conduit.itemsMarker.itsVersion


            # Here's what we're working around here with
            # modifiedRecurringEvents:
            #
            # 1. client subscribes to a calendar with a recurring event e.
            #    At sync time, e.occurrences = [e].
            #
            # 2. The client displays that calendar in the UI, so a bunch
            #    of occurrences get added.
            #
            # 3. The client syncs, and there's a change in e's rruleset.
            #    We throw out the old (i.e. delayed delete) and make a new
            #    one.
            #
            # 4. When we merge repository views, e's occurrences will have
            #    e, and all the occurrences added in step 2. However, those
            #    events have an rruleset that's about to be deleted (i.e.
            #    become None, that's the defaultValue of rruleset).
            #
            # So, we go through the changed recurring events after refreshing
            # the view, and make sure their occurrences don't have an isDeferred
            # rruleset. [grant 2006/05/05].
            #
            modifiedRecurringEvents = []
            for stat in stats:
                for uuid in stat['modified']:
                    item = contentView.findUUID(uuid)
                    if (pim.has_stamp(item, pim.EventStamp) and
                        pim.EventStamp(item).rruleset is not None):
                        modifiedRecurringEvents.append(pim.EventStamp(item))

            if modifiedRecurringEvents:
                # Refresh so that we can mess up all the occurrences
                # reflists by adding all the occurrences generated by
                # the UI
                contentView.refresh(mergeFunction)

                for event in modifiedRecurringEvents:
                    # We really want to patch up master events here,
                    # since they're the ones that own occurrences.
                    # Syncing may cause an event that was a master to
                    # become a modification, which means we should
                    # call getMaster() here and not earlier when
                    # calculating modifiedRecurringEvents.
                    master = event.getMaster()

                    # Ensure that there is at least one occurrence:
                    master.getFirstOccurrence()

                    masterOccurrences = master.occurrences or []

                    for occurrence in masterOccurrences:
                        rruleset = pim.EventStamp(occurrence).rruleset
                        if (rruleset is None or rruleset.isDeferred()):
                            occurrence.delete(recursive=True)


            newItemsNeedsCalling = needsCalling(NEWITEMS)
            newItemsUnestablishedNeedsCalling = (not linkedShares[0].established and
                needsCalling(NEWITEMSUNESTABLISHED))

            if newItemsNeedsCalling or newItemsUnestablishedNeedsCalling:
                added = [ ]
                for stat in stats:
                    for uuid in stat['added']:
                        if uuid not in added:
                            added.append(uuid)

            if newItemsNeedsCalling:
                callCallbacks(NEWITEMS, share=linkedShares[0], uuids=added)
            if newItemsUnestablishedNeedsCalling:
                callCallbacks(NEWITEMSUNESTABLISHED, share=linkedShares[0], uuids=added)

            if needsCalling(MODIFIEDITEMS):
                modified = [ ]
                for stat in stats:
                    for uuid in stat['modified']:
                        if uuid not in modified:
                            modified.append(uuid)
                callCallbacks(MODIFIEDITEMS, share=linkedShares[0], uuids=modified)


            # Pull in local changes from other views, and commit.  However, in
            # the case of a first-time publish we skip this commit because we
            # don't want other views to see the Share item(s) if the put phase
            # results in an error.
            if commit and not (not established and modeOverride == 'put'):

                if updateCallback:
                    updateCallback(msg=_(u"Saving..."))

                contentView.commit(mergeFunction)



            # The version just before the current version marks the ending
            # point to look for changes in the repository history during
            # the upcoming PUT phase
            putEndingVersion = cvShare.conduit.itemsMarker.itsVersion - 1

            if not modeOverride or modeOverride == 'put':

                # perform the 'put' operations of all associated shares, putting
                # local changes to server
                for share in linkedShares:
                    if share.active and share.mode in ('put', 'both'):
                        stat = share.conduit._put(contentView,
                                                  share.resourceList,
                                                  putStartingVersion,
                                                  putEndingVersion,
                                                  updateCallback=updateCallback,
                                                  forceUpdate=forceUpdate)

                        stats.append(stat)

            sources = schema.ns('osaf.pim', metaView).mine.sources
            sharing_ns = schema.ns('osaf.sharing', metaView)
            freeBusyShare = sharing_ns.prefs.freeBusyShare
            me = schema.ns("osaf.pim", metaView).currentContact.item

            now = datetime.datetime.now(ICUtzinfo.default)

            for share in linkedShares:
                share.established = True
                share.lastSynced = now

                # update exclude-from-free-busy for shares if using a CalDAV
                # conduit and this share was shared by me
                if isinstance(share.conduit, CalDAVConduit) and share.sharer is me:
                    reallyMine = share.contents in sources
                    if (reallyMine != share.conduit.inFreeBusy):
                        if share.conduit.setCosmoExcludeFreeBusy(not reallyMine):
                            share.conduit.inFreeBusy = reallyMine


            # Record the post-PUT manifest
            if commit:
                contentView.commit(mergeFunction)
                metaView.commit(mergeFunction)

        except Exception:

            # Discard any changes
            contentView.cancel()
            metaView.cancel()

            logger.exception("Sharing Error")
            raise

        return stats




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
        #     item.displayName.encode('utf8', 'replace'),
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
                        displayName = (getattr(relatedItem, 'displayName',
                            None) or relatedItem._repr_()).encode('utf8',
                            'replace')
                        logger.debug("Changes for %s: %s",
                            displayName, modifiedAttributes)
                        for change in modifiedAttributes:
                            if change in sharedAttributes:
                                logger.debug("A shared attribute (%s) changed for %s", change, displayName)
                                needsUpdate = True
                                result = 'modified'
                                reason = change
                                break

        if needsUpdate:
            logger.info("...putting '%s' %s (%d vs %d) (%s)" %
                (
                    item.displayName, item.itsUUID, item.getVersion(),
                    self.itemsMarker.getVersion(), reason
                )
            )

            if updateCallback and updateCallback(msg="'%s'" %
                item.displayName):
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
                cvSelf.share.addSharedItem(item)
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
                    
                    if (pim.has_stamp(item, pim.EventStamp) and getattr(item,
                        pim.EventStamp.modificationFor.name, None) is not None):
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
        logger.debug("Manifest: %s", self.manifest)

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
                displayName = (getattr(item, 'displayName',
                    None) or item._repr_())

                debugString = u"...imported '%s' '%s' %s, data: %s" % \
                              (itemPath, displayName, item, data)

                logger.info(debugString.encode('utf8', 'replace'))

                cvSelf.share.addSharedItem(item)
                if updateCallback and updateCallback(msg="'%s'" %
                    displayName):
                    raise errors.SharingError(_(u"Cancelled by user"))

                return item

            logger.error("...NOT able to import '%s'" % itemPath.encode('utf8', 'replace'))
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
        if not pim.has_stamp(contents, shares.SharedItem):
            shares.SharedItem(contents).add()

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
                            cvSelf.share.removeSharedItem(item)
                            stats['removed'].append(item.itsUUID)
                            if updateCallback and updateCallback(
                                msg=_(u"Removing from collection: '%(name)s'")
                                % { 'name' : item.displayName }
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
                logger.debug("haveLatest: Yes (%s %s)" % (path, data))
                return True
            else:
                # print "MISMATCH: local=%s, remote=%s" % (record['data'], data)
                logger.debug("...don't have latest (%s local:%s remote:%s)" % (path,
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







class HTTPMixin(pim.ContentItem):

    account = schema.One(initialValue=None)
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






class SimpleHTTPConduit(LinkableConduit, ManifestEngineMixin, HTTPMixin):
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
                cvSelf.share.addSharedItem(item)

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

