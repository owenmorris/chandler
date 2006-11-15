__all__ = [
    'sync',
    'isReadOnlyMode',
    'setReadOnlyMode',
]

from application import schema
from osaf import pim
from formats import CloudXMLFormat
from ICalendar import ICalendarFormat
from shares import Share, OneTimeShare
from webdav_conduit import WebDAVConduit
from caldav_conduit import CalDAVConduit
import errors
from callbacks import *
import logging
import zanshin, M2Crypto.BIO, twisted.web.http
from i18n import ChandlerMessageFactory as _
from repository.item.Item import Item
from repository.persistence.RepositoryError import MergeError


logger = logging.getLogger(__name__)

# A flag to allow a developer to turn off all publishing while debugging
_readOnlyMode = False
def isReadOnlyMode():
    return _readOnlyMode
def setReadOnlyMode(active):
    global _readOnlyMode
    _readOnlyMode = active

def sync(collectionOrShares, modeOverride=None, updateCallback=None,
    forceUpdate=None):

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



    if isinstance(collectionOrShares, list):
        # a list of Shares
        shares = collectionOrShares
        metaView = shares[0].itsView

    elif isinstance(collectionOrShares, Share):
        # just one Share
        shares = [collectionOrShares]
        metaView = collectionOrShares.itsView

    else:
        # just a collection
        shares = collectionOrShares.shares.first().getLinkedShares()
        metaView = collectionOrShares.itsView

    syncedByAccountShares = set()
    for share in shares:
        conduit = getattr(share, 'conduit', None)
        if conduit is not None:
            if hasattr(type(getattr(conduit, 'account', None)), 'sync'):
                syncedByAccountShares.add(share)
    for share in syncedByAccountShares:
        share.conduit.account.sync(share)

    shares = [share for share in shares if share not in syncedByAccountShares]
    if not shares:
        return []


    itemsMarker = shares[0].conduit.itemsMarker

    stats = []

    timeTravel = False
    for share in shares:

        # resourceList is a non-persistent snapshot of what's on the server
        # (or filesystem, etc.)
        share.resourceList = None

        # The CloudXML and ICalendar Formats require rolling back the sharing
        # view (aka time travel)
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


