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
    'Share',
    'OneTimeShare',
    'OneTimeFileSystemShare',
    'isReadOnlyMode',
    'setReadOnlyMode',
]


from application import schema
from osaf import pim
from i18n import ChandlerMessageFactory as _
import errors
from callbacks import *
import logging
import zanshin, M2Crypto.BIO, twisted.web.http
from repository.item.Item import Item
from repository.persistence.RepositoryError import MergeError

import logging
logger = logging.getLogger(__name__)




# A flag to allow a developer to turn off all publishing while debugging
_readOnlyMode = False
def isReadOnlyMode():
    return _readOnlyMode
def setReadOnlyMode(active):
    global _readOnlyMode
    _readOnlyMode = active










class modeEnum(schema.Enumeration):
    values = "put", "get", "both"


class Share(pim.ContentItem):
    """
    Represents a set of shared items, encapsulating contents, location,
    access method, data format, sharer and sharees.
    """

    schema.kindInfo(
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

    established = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether the share has been "
              "successfully subscribed/published at least once.",
        initialValue = False,
    )

    mode = schema.One(
        modeEnum,
        doc = 'This attribute indicates the sync mode for the share:  '
              'get, put, or both',
        initialValue = 'both',
    )

    error = schema.One(
        schema.Text,
        doc = 'A message describing the last error; empty string otherwise',
        initialValue = u''
    )

    contents = schema.One(pim.ContentItem,otherName='shares',initialValue=None)

    items = schema.Sequence(pim.ContentItem, initialValue=[],
        otherName = 'sharedIn')

    conduit = schema.One(initialValue=None)
    # inverse of Conduit.share

    format = schema.One(initialValue=None)
    # inverse of ImportExportFormat.share

    sharer = schema.One(
        pim.Contact,
        doc = 'The contact who initially published this share',
        initialValue = None,
        otherName = 'sharerOf',
    )

    sharees = schema.Sequence(
        pim.Contact,
        doc = 'The people who were invited to this share',
        initialValue = [],
        otherName = 'shareeOf',
    )

    filterClasses = schema.Sequence(
        schema.Text,
        doc = 'The list of classes to import/export',
        initialValue = [],
    )

    filterAttributes = schema.Sequence(schema.Text, initialValue=[])

    # @@@ [grant] Try inverse, and explicit attributes
    leads = schema.Sequence('Share', initialValue=[], otherName='follows')
    follows = schema.One('Share', otherName='leads')

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [filterAttributes],
            byCloud = [contents, sharer, sharees]
        ),
        copying = schema.Cloud(byCloud=[format, conduit])
    )

    def __init__(self, *args, **kw):
        defaultDisplayName = getattr(kw.get('contents'),'displayName',u'')
        kw.setdefault('displayName',defaultDisplayName)
        super(Share, self).__init__(*args, **kw)

    def create(self):
        self.conduit.create()

    def destroy(self):
        self.conduit.destroy()

    def open(self):
        self.conduit.open()

    def close(self):
        self.conduit.close()

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None):
        return self._sync(modeOverride=modeOverride,
                          updateCallback=updateCallback,
                          forceUpdate=forceUpdate)

    def put(self, updateCallback=None):
        return self.sync(modeOverride='put', updateCallback=updateCallback,
                         forceUpdate=None)

    def get(self, updateCallback=None):
        return self.sync(modeOverride='get', updateCallback=updateCallback)

    def exists(self):
        return self.conduit.exists()

    def getLocation(self, privilege=None):
        return self.conduit.getLocation(privilege=privilege)

    def getSharedAttributes(self, kind, cloudAlias='sharing'):
        """
        Examine sharing clouds and filterAttributes to determine which
        attributes to share for a given kind
        """

        attributes = set()
        skip = getattr(self, 'filterAttributes', [])

        for cloud in kind.getClouds(cloudAlias):
            for alias, endpoint, inCloud in cloud.iterEndpoints(cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]

                # An includePolicy of 'none' is how we override an inherited
                # endpoint
                if not (endpoint.includePolicy == 'none' or
                        attrName in skip):
                    attributes.add(attrName)

        return attributes

    def getLinkedShares(self):

        def getFollowers(share):
            if hasattr(share, 'leads'):
                for follower in share.leads:
                    yield follower
                    for subfollower in getFollowers(follower):
                        yield subfollower

        # Find the root leader
        root = self
        leader = getattr(root, 'follows', None)
        while leader is not None:
            root = leader
            leader = getattr(root, 'follows', None)

        shares = [root]
        for follower in getFollowers(root):
            shares.append(follower)

        return shares


    def _sync(self, modeOverride=None, updateCallback=None, forceUpdate=None):
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
            #                'name' : item.getItemDisplayName(),
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



        shares = self.getLinkedShares()
        metaView = shares[0].itsView

        # @@@MOR -- Note for Andi...
        # Rather than doing this hack, the p2p stuff can simply override
        # Share.sync():

        # syncedByAccountShares = set()
        # for share in shares:
        #     conduit = getattr(share, 'conduit', None)
        #     if conduit is not None:
        #         if hasattr(type(getattr(conduit, 'account', None)), 'sync'):
        #             syncedByAccountShares.add(share)
        # for share in syncedByAccountShares:
        #     share.conduit.account.sync(share)
        #
        # shares = [share for share in shares if share not in syncedByAccountShares]
        # if not shares:
        #     return []


        itemsMarker = shares[0].conduit.itemsMarker

        stats = []

        timeTravel = False
        for share in shares:

            # resourceList is a non-persistent snapshot of what's on the server
            # (or filesystem, etc.)
            share.resourceList = None

            # The CloudXML and ICalendar Formats require rolling back the
            # sharing view (aka time travel)
            if (isinstance(share.format, CloudXMLFormat) or
                isinstance(share.format, ICalendarFormat)):
                    timeTravel = True


        # Don't commit if we're using a OneTimeShare
        commit = not isinstance(shares[0], OneTimeShare)

        established = shares[0].established
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
        if not isinstance(shares[0], OneTimeShare):
            contentView.deferDelete()

        if (len(shares) > 1 and
            isinstance(shares[0].conduit, WebDAVConduit) and
            isinstance(shares[1].conduit, CalDAVConduit)):
            # This is a hybrid share, XML + ICS
            hybrid = True
        else:
            hybrid = False

        try:

            # Build the resource list(s) up front so that we don't examine
            # XML files at one point in time, and ICS files at another
            if hybrid:
                upper = shares[1]
                lower = shares[0]
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
                for share in shares:
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
                # XML fork (shares[0]), and making sure those items were also
                # modified via the ICS fork.  Any events that don't have an ICS
                # fork are removed locally. Next, we need to adjust the manifests
                # so that during the PUT phase we don't remove the .xml resources
                # from the server.

                if hybrid:
                    # This is a hybrid share, XML + ICS
                    share0 = metaView.findUUID(shares[0].itsUUID)
                    share1 = metaView.findUUID(shares[1].itsUUID)

                    for uuid in stats[0]['added']:
                        item = contentView.findUUID(uuid)
                        if uuid not in stats[1]['modified']:
                            item = contentView.findUUID(uuid)
                            if pim.has_stamp(item, pim.EventStamp):
                                if updateCallback:
                                    updateCallback(msg=_(u"Incomplete Event Detected: '%(name)s'") % { 'name': item.getItemDisplayName() } )

                                # This indicates the resource is to be ignored
                                # during PUT (otherwise we would remove the .xml
                                # resource since the item isn't in our local copy
                                # of the collection:
                                itemPath = share0.conduit._getItemPath(item)
                                share0.conduit._addToManifest(itemPath, None)
                                logger.info("Incomplete event: '%s' %s" %
                                    (item.displayName, itemPath))
                                item.delete(True)


            for share in shares:
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
            newItemsUnestablishedNeedsCalling = (not shares[0].established and
                needsCalling(NEWITEMSUNESTABLISHED))

            if newItemsNeedsCalling or newItemsUnestablishedNeedsCalling:
                added = [ ]
                for stat in stats:
                    for uuid in stat['added']:
                        if uuid not in added:
                            added.append(uuid)

            if newItemsNeedsCalling:
                callCallbacks(NEWITEMS, share=shares[0], uuids=added)
            if newItemsUnestablishedNeedsCalling:
                callCallbacks(NEWITEMSUNESTABLISHED, share=shares[0], uuids=added)

            if needsCalling(MODIFIEDITEMS):
                modified = [ ]
                for stat in stats:
                    for uuid in stat['modified']:
                        if uuid not in modified:
                            modified.append(uuid)
                callCallbacks(MODIFIEDITEMS, share=shares[0], uuids=modified)


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
                for share in shares:
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

            for share in shares:
                share.established = True

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

        except Exception, e:

            # Discard any changes
            contentView.cancel()
            metaView.cancel()

            logger.exception("Sharing Error: %s" % e)
            raise

        return stats







class OneTimeShare(Share):
    """
    Delete format, conduit, and share after the first get or put.
    """

    def remove(self):
        # With deferred deletes, we need to also remove the Share from the
        # collection's shares ref collection
        if self.contents:
            self.contents.shares.remove(self)
        self.conduit.delete(True)
        self.format.delete(True)
        self.delete(True)

    def put(self, updateCallback=None):
        super(OneTimeShare, self).put(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection

    def get(self, updateCallback=None):
        super(OneTimeShare, self).get(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection




class OneTimeFileSystemShare(OneTimeShare):
    def __init__(self, path, itsName, formatclass, itsKind=None, itsView=None,
                 contents=None):

        import filesystem_conduit
        conduit = filesystem_conduit.FileSystemConduit(
            itsKind=itsKind, itsView=itsView, sharePath=path, shareName=itsName
        )
        format  = formatclass(itsView=itsView)
        super(OneTimeFileSystemShare, self).__init__(
            itsKind=itsKind, itsView=itsView,
            contents=contents, conduit=conduit, format=format
        )

