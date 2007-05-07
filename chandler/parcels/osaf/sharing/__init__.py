#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


import logging, urlparse, datetime, wx
from PyICU import ICUtzinfo

from application import schema, dialogs, Globals
from application.Parcel import Reference
from application.Utility import getDesktopDir, CertificateVerificationError
from osaf import pim, ChandlerException
from osaf.framework.password import Password
from osaf.framework.twisted import waitForDeferred
from osaf.pim import isDead, has_stamp
from osaf.pim.calendar import Calendar
from osaf.pim.collections import (UnionCollection, DifferenceCollection,
                                  FilteredCollection)
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.c import UUID
from osaf.activity import *

import zanshin, M2Crypto, twisted, re

from shares import *
from conduits import *
from formats import *
from errors import *
from utility import *
from accounts import *
from filesystem_conduit import *
from webdav_conduit import *
from inmemory_conduit import *
from caldav_conduit import *
from recordset_conduit import *
from WebDAV import *
from ICalendar import *
from callbacks import *
from eim import *
from model import *
from translator import *
from eimml import *
from cosmo import *
from itemcentric import *
from ics import *
from serialize import *


logger = logging.getLogger(__name__)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CalDAV settings:

caldav_atop_eim = False

# What to name the CloudXML subcollection on a CalDAV server:
SUBCOLLECTION = u".chandler"

# What attributes to filter out in the CloudXML subcollection on a CalDAV
# server (@@@MOR This should change to using a schema decoration instead
# of thie explicit list):

CALDAVFILTER = [attr.name for attr in (
                    pim.EventStamp.allDay,
                    pim.EventStamp.anyTime,
                    pim.EventStamp.duration,
                    pim.EventStamp.isGenerated,
                    pim.EventStamp.location,
                    pim.EventStamp.modifications,
                    pim.EventStamp.modifies,
                    pim.EventStamp.occurrenceFor,
                    pim.EventStamp.recurrenceID,
                    pim.Remindable.reminders,
                    pim.EventStamp.rruleset,
                    pim.EventStamp.startTime,
                    pim.EventStamp.transparency,
                )]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

PUBLISH_MONOLITHIC_ICS = True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingPreferences(schema.Item):
    import_dir = schema.One(schema.Text, defaultValue = getDesktopDir())
    import_as_new = schema.One(schema.Boolean, defaultValue = True)
    freeBusyAccount = schema.One(WebDAVAccount, defaultValue=None)
    freeBusyShare   = schema.One(Share, defaultValue=None)

def installParcel(parcel, oldVersion=None):

    SharingPreferences.update(parcel, "prefs")

    Reference.update(parcel, 'currentSharingAccount')

    from osaf import startup
    startup.PeriodicTask.update(parcel, "sharingTask",
        invoke="osaf.sharing.BackgroundSyncHandler",
        run_at_startup=False,
        active=True,
        interval=datetime.timedelta(minutes=60)
    )
    pim.ListCollection.update(parcel, "activityLog",
        displayName="Sharing Activity"
    )

    publishedFreeBusy = UnionCollection.update(parcel, 'publishedFreeBusy')
    pim_ns = schema.ns('osaf.pim', parcel.itsView)
    hiddenEvents = DifferenceCollection.update(parcel, "hiddenEvents",
        sources=[pim_ns.allEventsCollection,
            publishedFreeBusy],
        displayName = 'Unpublished Freebusy Events'
    )

    
    # Make a collection of all Notes with an icalUID, so that
    # we can index it.    
    filterAttribute = pim.Note.icalUID.name
    iCalendarItems = FilteredCollection.update(parcel, 'iCalendarItems',
        source=pim_ns.noteCollection,
        filterExpression="view.hasTrueValues(uuid, '%s')" % (filterAttribute,),
        filterAttributes=[filterAttribute])
    iCalendarItems.addIndex('icalUID', 'value', attribute=filterAttribute)


def getDefaultAccount(rv):
    cur = schema.ns('osaf.sharing', rv).currentSharingAccount
    account = cur.item
    if account and account.isSetUp():
        return account
    for account in SharingAccount.iterItems(rv):
        if account.isSetUp():
            return account
    return None


def createDefaultAccount(rv):
    cur = schema.ns('osaf.sharing', rv).currentSharingAccount
    if cur.item is None:
        cur.item = WebDAVAccount(itsView=rv,
            displayName=_(u'Cosmo Sharing Service'),
            host=u'osaf.us', path=u'/cosmo/dav/<username>',
            username=u'',
            password=Password(itsView=rv),
            useSSL=True, port=443
        )

        # Use this one when morsecode becomes the default:

        # CosmoAccount(itsView=parcel.itsView,
        #     displayName=_(u'Chandler Hub Service'),
        #     host=u'qacosmo.osafoundation.org', path=u'/cosmo',
        #     username=u'',
        #     password=Password(itsView=parcel.itsView),
        #     useSSL=False, port=80
        # )

    return cur.item


def isSharingSetUp(view):
    for account in SharingAccount.iterItems(view):
        if account.isSetUp():
            return True
    return False

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

PROCEED        = 1
GRACEFUL_STOP  = 2
IMMEDIATE_STOP = 3
interrupt_flag = PROCEED

IDLE           = 1
RUNNING        = 2
running_status = IDLE


# In order to shut down cleanly, the BackgroundSyncHandler registers itself
# with twisted to be alerted when reactor shutdown is beginning.  If the
# sharing layer is in the middle of a job, a Deferred is returned to twisted,
# and Twisted suspends shutdown until BackgroundSyncHandler triggers the
# Deferred.  If no job is running, None is returned and twisted continues
# with shutdown immediately.

# The Deferred object is stored in shutdown_deferred for later use by
# BackgroundSyncHandler's run method.
shutdown_deferred = None


def setAutoSyncInterval(rv, minutes):
    # If minutes is None, that means manual mode only, and we'll set the
    # interval to a really big number until bug 5903 is fixed.

    task = schema.ns('osaf.sharing', rv).sharingTask
    if minutes is None:
        interval = datetime.timedelta(days=365)
    else:
        interval = datetime.timedelta(minutes=minutes)
    task.reschedule(interval)

def getAutoSyncInterval(rv):
    task = schema.ns('osaf.sharing', rv).sharingTask
    interval = task.interval
    if interval == datetime.timedelta(days=365):
        return None
    else:
        return interval.days * 1440 + interval.seconds / 60

def scheduleNow(rv, *args, **kwds):
    """ Initiate a sync right now, queuing up if one is running already """
    task = schema.ns('osaf.sharing', rv).sharingTask

    collection = kwds.get('collection', None)
    if collection is not None:
        kwds['collection'] = collection.itsUUID

    task.run_once(*args, **kwds)

def interrupt(graceful=True):
    """ Stop sync operations; if graceful=True, then the Share being synced
        at the moment is allowed to complete.  If graceful=False, stop the
        current Share in the middle of whatever it's doing.
    """
    global interrupt_flag

    if graceful:
        interrupt_flag = GRACEFUL_STOP # allow the current sync( ) to complete
    else:
        interrupt_flag = IMMEDIATE_STOP # interrupt current sync( )



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class BackgroundSyncHandler:

    def __init__(self, item):
        global running_status

        def shutdownCallback():
            # This gets called before twisted starts shutting down, since we
            # register this callback a few lines down

            # Return a Deferred that we can return to twisted -- twisted will
            # wait for the Deferred to be called-back when shutting down; if
            # no current sync activity, then return None
            global shutdown_deferred

            if running_status == IDLE:
                # Returning None since we're not running
                return None

            shutdown_deferred = twisted.internet.defer.Deferred()
            return shutdown_deferred

        # Register a callback for when twisted is being shutdown
        twisted.internet.reactor.addSystemEventTrigger('before', 'shutdown',
            shutdownCallback)

        # Store the repository view provided to us
        self.rv = item.itsView

        running_status = IDLE

    def run(self, *args, **kwds):

        # This method must return True -- no raising exceptions!

        global interrupt_flag, running_status

        # A callback to allow cancelling of a sync( )
        def callback(msg=None, work=None, totalWork=None):
            kwds = {'msg':msg, 'work':work, 'totalWork':totalWork}
            callCallbacks(UPDATE, **kwds)
            return interrupt_flag == IMMEDIATE_STOP

        def silentCallback(*args, **kwds):
            # Simply return the interrupt flag
            return interrupt_flag == IMMEDIATE_STOP

        if Globals.options.offline:
            # In offline mode, no sharing
            return True

        if running_status != IDLE:
            # busy
            return True

        stats = []
        running_status = RUNNING

        try: # Sync collections

            modeOverride = kwds.get('modeOverride', None)
            forceUpdate = kwds.get('forceUpdate', None)

            self.rv.refresh(notify=False)

            shares = []

            if 'collection' in kwds:
                uuid = kwds['collection']
                collection = self.rv.findUUID(uuid)
            else:
                collection = None

            shares = getSyncableShares(self.rv, collection)

            for share in shares:

                if interrupt_flag != PROCEED: # interruption
                    # We have been asked to stop, so fire the deferred
                    if shutdown_deferred:
                        shutdown_deferred.callback(None)
                    return True

                callCallbacks(UPDATE, msg="Syncing collection '%s'" %
                    share.contents.displayName)
                try:
                    activity = Activity("Sync: %s" % share.contents.displayName)
                    activity.started()
                    stats.extend(share.sync(modeOverride=modeOverride,
                                            activity=activity,
                                            forceUpdate=forceUpdate))
                    activity.completed()

                except Exception, e:
                    stats.extend( [ { 'collection' : share.contents.itsUUID,
                                    'error' : str(e) } ] )

                    if not isinstance(e, ActivityAborted):
                        activity.failed(e)

        except: # Failed to sync at least one collection; continue on
            logger.exception("Background sync error")

        try: # Create the sync report event
            log = schema.ns('osaf.sharing', self.rv).activityLog
            reportEvent = pim.CalendarEvent(itsView=self.rv,
                displayName="Sync",
                startTime=datetime.datetime.now(ICUtzinfo.default),
                duration=datetime.timedelta(minutes=60),
                anyTime=False,
                transparency='fyi',
                body=str(stats)
            )
            log.add(reportEvent.itsItem)

        except: # Don't worry if this fails, just report it
            logger.exception("Error trying to create sync report")

        try: # Commit sync report and possible errors
            self.rv.commit()
        except: # No matter what we have to continue on
            logger.exception("Error trying to commit in bgsync")


        try: # One final update callback with an empty string
            callCallbacks(UPDATE, msg='')
        except: # No matter what we have to continue on
            logger.exception("Error calling callbacks")


        running_status = IDLE
        if interrupt_flag != PROCEED:
            # We have been asked to stop, so fire the deferred
            if shutdown_deferred:
                shutdown_deferred.callback(None)

        interrupt_flag = PROCEED

        return True








# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def publish(collection, account, classesToInclude=None,
            publishType = 'collection',
            attrsToExclude=None, displayName=None, activity=None):
    """
    Publish a collection, automatically determining which conduits/formats
    to use, and how many

    @type collection: pim.ContentCollection
    @param collection: The collection to publish
    @type account: WebDAVAccount
    @param account: The sharing (WebDAV) account to use
    @type classesToInclude: list of str
    @param classesToInclude: An optional list of dotted class names;
                             if provided, then only items matching those
                             classes will be shared
    @type attrsToExclude: list of str
    @param attrsToExclude: An optional list of attribute names to skip when
                           publishing
    @type displayName: unicode
    @param displayName: An optional name to use for publishing; if not provided,
                        the collection's displayName will be used as a starting
                        point.  In either case, to avoid collisions with existing
                        collections, '-1', '-2', etc., may be appended.
    """

    if Globals.options.offline:
        raise OfflineError(_(u"Offline mode"))

    try:
        totalWork = len(collection)
    except TypeError: # Some collection classes don't support len( )
        totalWork = len(list(collection))

    if activity:
        activity.update(totalWork=totalWork)


    view = collection.itsView

    pim_ns = schema.ns("osaf.pim", view)
    # If no account passed in, use an inmemory conduit (for development)
    if account is None:
        conduit = InMemoryDiffRecordSetConduit(itsView=view,
            translator=SharingTranslator,
            serializer=EIMMLSerializer
        )
        share = Share(itsView=view, contents=collection, conduit=conduit)
        share.create()
        share.sync()
        share.sharer = pim_ns.currentContact.item
        return [share]

    # If the account knows how to publish, delegate:
    if hasattr(account, 'publish'):
        shares = account.publish(collection, activity=activity,
            filters=attrsToExclude)
        for share in shares:
            share.sharer = pim_ns.currentContact.item
        return shares



    # Stamp the collection
    if not has_stamp(collection, SharedItem):
        SharedItem(collection).add()

    conduit = WebDAVConduit(itsView=view, account=account)

    # Interrogate the server associated with the account

    location = account.getLocation()
    if not location.endswith("/"):
        location += "/"
    handle = conduit._getServerHandle()
    resource = handle.getResource(location)

    logger.debug('Examining %s ...', location.encode('utf8', 'replace'))
    exists = handle.blockUntil(resource.exists)
    if not exists:
        logger.debug("...doesn't exist")
        raise NotFound(_(u"%(location)s does not exist") %
            {'location': location})

    isCalendar = handle.blockUntil(resource.isCalendar)
    logger.debug('...Calendar?  %s', isCalendar)
    isCollection =  handle.blockUntil(resource.isCollection)
    logger.debug('...Collection?  %s', isCollection)

    response = handle.blockUntil(resource.options)
    dav = response.headers.getHeader('DAV')
    logger.debug('...DAV:  %s', dav)
    allowed = response.headers.getHeader('Allow')
    logger.debug('...Allow:  %s', allowed)
    supportsTickets = handle.blockUntil(resource.supportsTickets)
    logger.debug('...Tickets?:  %s', supportsTickets)

    conduit.delete(True) # Clean up the temporary conduit


    # Prepare the share objects

    shares = []

    try:

        if isCalendar:
            # We've been handed a calendar directly.  Just publish directly
            # into this calendar collection rather than making a new one.
            # Create a CalDAV share with empty sharename, doing a GET and PUT

            share = _newOutboundShare(view, collection,
                                     classesToInclude=classesToInclude,
                                     shareName=u"",
                                     account=account,
                                     useCalDAV=True)

            try:
                SharedItem(collection).shares.append(share, 'main')
            except ValueError:
                # There is already a 'main' share for this collection
                SharedItem(collection).shares.append(share)

            if attrsToExclude:
                share.filterAttributes = attrsToExclude

            shares.append(share)
            share.displayName = collection.displayName

            share.sync(activity=activity)

        else:
            # the collection should be published
            # determine a share name
            existing = getExistingResources(account)
            displayName = displayName or collection.displayName

            shareName = displayName
            alias = 'main'

            # See if there are any non-ascii characters, if so, just use UUID
            try:
                shareName.encode('ascii')
                pattern = re.compile('[^A-Za-z0-9]')
                shareName = re.sub(pattern, "_", shareName)
            except UnicodeEncodeError:
                shareName = unicode(collection.itsUUID)

            shareName = _uniqueName(shareName, existing)

            if ('calendar-access' in dav or 'MKCALENDAR' in allowed):
                # We're speaking to a CalDAV server                
                sharing_ns = schema.ns('osaf.sharing', view)
                if publishType == 'freebusy':
                    share = Share(itsView=view)
                    share.conduit = CalDAVConduit(itsView=view, account=account,
                                                  shareName='')
                    
                    share.conduit.createFreeBusyTicket()
                    
                    sharing_ns.prefs.freeBusyShare   = share
                    sharing_ns.prefs.freeBusyAccount = account
                    published = sharing_ns.publishedFreeBusy
                    
                    # put the appropriate collections into publishedFreeBusy to
                    # avoid syncing the same event multiple times
                    for share in getActiveShares(view):
                        updatePublishedFreeBusy(share, location)
                    
                    
                    hiddenResource = handle.getResource(location + 'hiddenEvents/')
                    
                    if handle.blockUntil(hiddenResource.exists):
                        # someone has already published hiddenEvents for this
                        # account.  It's hard to say what should happen in this
                        # case, for now just fail
                        raise SharingError(_(u"Free/Busy information has already been published for this account"))
                    # publish hiddenEvents
                    share = _newOutboundShare(view,
                                              sharing_ns.hiddenEvents,
                                              shareName='hiddenEvents',
                                              account=account,
                                              useCalDAV=True)
                    shares.append(share)
                    sharing_ns.hiddenEvents.shares.append(share)

                    share.conduit.inFreeBusy = True
                    share.create()
                    share.put(activity=activity)

                else:
                    if caldav_atop_eim:
                        share = Share(itsView=view, contents=collection)
                        conduit = CalDAVRecordSetConduit(itsParent=share,
                            account=account,
                            shareName=shareName,
                            translator=SharingTranslator,
                            serializer=ICSSerializer)
                        share.conduit = conduit
                        if attrsToExclude:
                            conduit.filters = attrsToExclude

                        share.displayName = displayName or collection.displayName
                        share.sharer = pim_ns.currentContact.item

                    else:
                        # Create a CalDAV conduit / ICalendar format
                        # Create a cloudxml subcollection
                        # or just a freebusy resource
                        share = _newOutboundShare(view, collection,
                            classesToInclude=classesToInclude,
                            shareName=shareName,
                            displayName=displayName,
                            account=account,
                            useCalDAV=True,
                            publishType=publishType)

                        if attrsToExclude:
                            share.filterAttributes = attrsToExclude

                    try:
                        SharedItem(collection).shares.append(share, alias)
                    except ValueError:
                        # There is already a 'main' share for this collection
                        SharedItem(collection).shares.append(share)

                    shares.append(share)

                    if share.exists():
                        raise SharingError(_(u"Share already exists"))

                    inFreeBusy = collection in pim_ns.mine.sources
                    if inFreeBusy:
                        share.conduit.inFreeBusy = True

                    share.create()
                    # bug 8128, this setDisplayName shouldn't be required, but
                    # cosmo isn't accepting setting displayname in MKCALENDAR
                    share.conduit.setDisplayName(displayName)
    
                    if not caldav_atop_eim and (publishType == 'collection'):
                        # Create a subcollection to contain the cloudXML versions of
                        # the shared items
                        subShareName = u"%s/%s" % (shareName, SUBCOLLECTION)
    
                        subShare = _newOutboundShare(view, collection,
                                                     classesToInclude=classesToInclude,
                                                     shareName=subShareName,
                                                     displayName=displayName,
                                                     account=account)
        
                        if attrsToExclude:
                            subShare.filterAttributes = attrsToExclude
                        else:
                            subShare.filterAttributes = []
    
                        for attr in CALDAVFILTER:
                            subShare.filterAttributes.append(attr)
    
                        shares.append(subShare)
    
                        if subShare.exists():
                            raise SharingError(_(u"Share already exists"))
    
                        try:
                            subShare.create()
    
                            # sync the subShare before the CalDAV share
                            share.follows = subShare
    
                            # Since we're publishing twice as many resources:
                            if activity:
                                totalWork *= 2
                                activity.update(totalWork=totalWork)
    
                        except SharingError:
                            # We're not able to create the subcollection, so
                            # must be a vanilla CalDAV Server.  Continue on.
                            subShare.delete(True)
                            subShare = None
    
                    else:
                        subShare = None
    
                    share.put(activity=activity)

                    # tickets after putting
                    if supportsTickets and publishType == 'collection':
                        share.conduit.createTickets()

                    if inFreeBusy:
                        if account == sharing_ns.prefs.freeBusyAccount:
                            sharing_ns.publishedFreeBusy.addSource(collection)


            elif dav is not None:

                if publishType == 'freebusy':
                    shareName += '.ifb'
                    alias = 'freebusy'

                # We're speaking to a WebDAV server -- use EIMML

                share = Share(itsView=view, contents=collection)
                conduit = WebDAVRecordSetConduit(itsParent=share,
                    shareName=shareName, account=account,
                    translator=SharingTranslator,
                    serializer=EIMMLSerializer)
                share.conduit = conduit

                # TODO: support filters on WebDAV + EIMML

                try:
                    SharedItem(collection).shares.append(share, alias)
                except ValueError:
                    # There is already a 'main' share for this collection
                    SharedItem(collection).shares.append(share)

                shares.append(share)

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(activity=activity)

                if supportsTickets:
                    share.conduit.createTickets()

                if False and PUBLISH_MONOLITHIC_ICS:
                    icsShareName = u"%s.ics" % shareName
                    icsShare = _newOutboundShare(view, collection,
                                             classesToInclude=classesToInclude,
                                             shareName=icsShareName,
                                             displayName=displayName,
                                             account=account)
                    shares.append(icsShare)
                    # icsShare.follows = share
                    icsShare.displayName = u"%s.ics" % displayName
                    icsShare.format = ICalendarFormat(itsParent=icsShare)
                    icsShare.mode = "put"

                    if icsShare.exists():
                        raise SharingError(_(u"Share already exists"))

                    icsShare.create()
                    icsShare.put(activity=activity)
                    if supportsTickets:
                        icsShare.conduit.createTickets()

    except (SharingError,
            zanshin.error.Error,
            M2Crypto.SSL.Checker.WrongHost,
            CertificateVerificationError,
            twisted.internet.error.TimeoutError), e:

        # Clean up share objects
        try:
            for share in shares:
                share.delete(True)
        except:
            pass # ignore stale shares

        # Note: the following "raise e" line used to just read "raise".
        # However, if the try block immediately preceeding this comment
        # raises an exception, the "raise" following this comment was
        # raising that *new* exception instead of the original exception
        # that got us here, "e".
        raise e

    return shares

def updatePublishedFreeBusy(share, fbLocation=None):
    """Add the given share to publishedFreeBusy if it matches fbLocation."""
    sharing_ns = schema.ns('osaf.sharing', share.itsView)
    if fbLocation == None:
        if sharing_ns.prefs.freeBusyShare is not None:
            location = freeBusyShare.getLocation()
        else:
            return
        
    published = sharing_ns.publishedFreeBusy
    conduit = share.conduit
    if (conduit.inFreeBusy and 
        conduit.getLocation().startswith(fbLocation) and
        share.contents != sharing_ns.hiddenEvents):
            published.addSource(share.contents)

def destroyShare(share):
    # Remove from server (or disk, etc.)
    try:
        share.destroy()
    except:
        logger.exception("Error trying to delete shared collection")
        # Even though we failed to remove the collection, we still need to
        # clean up the share objects, so continue on
    deleteShare(share)


def deleteShare(share):
    # Clean up sharing-related objects
    if getattr(share, "conduit", None):
        share.conduit.delete(True)
    if getattr(share, "format", None):
        share.format.delete(True)
    for state in getattr(share, "states", []):
        state.delete(True)
    share.delete(recursive=True)

def unpublish(collection):
    """
    Remove a share from the server, and delete all associated Share objects

    @type collection: pim.ContentCollection
    @param collection: The shared collection to unpublish

    """

    if has_stamp(collection, SharedItem):
        for share in SharedItem(collection).shares:
            destroyShare(share)

        sharing_ns = schema.ns('osaf.sharing', collection.itsView)
        if collection in sharing_ns.publishedFreeBusy.sources:
            sharing_ns.publishedFreeBusy.removeSource(collection)

def deleteTicket(share, ticket):
    """Delete ticket associated with the given ticket string from the share."""
    conduit = share.conduit
    location = conduit.getLocation()
    if not location.endswith("/"):
        location += "/"
    handle = conduit._getServerHandle()
    resource = handle.getResource(location)
    return handle.blockUntil(resource.deleteTicket, ticket)

def unpublishFreeBusy(collection):
    """
    Remove a share from the server, and delete all associated Share objects
    """
    share = getFreeBusyShare(collection)
    if share is not None:
        # .ifb share, delete it
        if share.contents == collection:
            destroyShare(share)
        # CalDAV parent collection for live data, deleting would be BAD
        else:
            # remove freebusy ticket from the collection
            try:
                deleteTicket(share, share.conduit.ticketFreeBusy)
            except zanshin.http.HTTPError, err:
                raise NotFound("Freebusy ticket not found")
            # Clean up sharing-related objects
            share.conduit.delete(True)
            share.delete(True)

            # also stop publishing hiddenEvents
            sharing_ns = schema.ns('osaf.sharing', collection.itsView)
            for share in sharing_ns.hiddenEvents.shares:
                destroyShare(share)


def subscribe(view, url, activity=None, username=None, password=None,
    filters=None, forceFreeBusy=False):

    if Globals.options.offline:
        raise OfflineError(_(u"Offline mode"))

    (useSSL, host, port, path, query, fragment, ticket, parentPath,
        shareName) = splitUrl(url)

    if ticket:
        account = username = password = None

    else:
        # See if there is an account which matches this url already,
        # and use the username and password from it (as long as we're
        # not overriding it with passed-in username/password args)

        account = WebDAVAccount.findMatchingAccount(view, url)
        if account is not None:
            # There is a matching account
            if username is None:
                # We're not overriding the username/passwd on this account
                username = account.username
                password = waitForDeferred(account.password.decryptPassword())
            else:
                # We're overriding the username/passwd on this account
                account.username = username
                waitForDeferred(account.password.encryptPassword(password))

            # update shareName if it's a subscollection in the account
            if account.path.strip("/") != parentPath.strip("/"):
                # account path: "a/b", parent path: "a/b/c", tail will be "c"
                tail = parentPath.strip("/")[len(account.path.strip("/"))+1:]
                if tail != "":
                    shareName = tail + "/" + shareName

    inspection = inspect(url, username=username, password=password)

    logger.info("Inspection results for %s: %s", url, inspection)

    # TODO: check for "already subscribed"
    # TODO: upgrade to read-write if provided new ticket

    # Override, because we can't trust .mac to return 'text/calendar'
    parsedUrl = urlparse.urlsplit(url)
    if parsedUrl.scheme.startswith('webcal'):
        inspection['contentType'] = 'text/calendar'

    contentType = inspection.get('contentType', None)

    if contentType:
        contentType = contentType.split(";")[0]

    if inspection['calendar']: # CalDAV collection

        if not ticket and account is None:
            # Create a new account
            account = WebDAVAccount(itsView=view)
            account.displayName = url
            account.host = host
            account.path = parentPath
            account.useSSL = useSSL
            account.port = port
            if username is not None:
                account.username = username
            if password is not None:
                account.password = Password(itsParent=account)
                waitForDeferred(account.password.encryptPassword(password))

        collection = subscribeCalDAV(view, url, inspection,
            activity=activity, account=account,
            parentPath=parentPath, shareName=shareName, ticket=ticket,
            username=username, password=password, filters=filters)
        return collection

    elif inspection['collection']: # WebDAV collection

        if not ticket and account is None:
            # Create a new account
            account = WebDAVAccount(itsView=view)
            account.displayName = url
            account.host = host
            account.path = parentPath
            account.useSSL = useSSL
            account.port = port
            if username is not None:
                account.username = username
            if password is not None:
                account.password = Password(itsParent=account)
                waitForDeferred(account.password.encryptPassword(password))

        collection = subscribeWebDAV(view, url, inspection,
            activity=activity, account=account,
            parentPath=parentPath, shareName=shareName, ticket=ticket,
            username=username, password=password, filters=filters)
        return collection

    elif contentType == "text/html":
        # parse the webpage for embedded link to real url
        text = getPage(url, username=username, password=password)

        # getPage needs to raise Forbidden exception, right?

        if text:
            links = extractLinks(text)

            selfUrl = links['self']
            if selfUrl is not None:
                if selfUrl.endswith('forbidden'):
                    raise NotAllowed(_("You don't have permission"))

                davUrl = links['alternate'].get('text/html', None)
                if davUrl:
                    davUrl = urlparse.urlunparse((parsedUrl.scheme,
                        parsedUrl.netloc, davUrl, "", "", ""))

                morsecodeUrl = links['alternate'].get('text/xml', None)
                if morsecodeUrl:
                    morsecodeUrl = urlparse.urlunparse((parsedUrl.scheme,
                        parsedUrl.netloc, morsecodeUrl, "", "", ""))

                if davUrl and morsecodeUrl:

                    collection = subscribeMorsecode(view, url, morsecodeUrl,
                        inspection, activity=activity,
                        account=account, username=username, password=password,
                        filters=filters)
                    return collection

        raise errors.SharingError("Can't parse webpage")

    elif contentType == "text/calendar":

        # monolithic .ics file
        collection = subscribeICS(view, url, inspection,
            activity=activity, account=account,
            parentPath=parentPath, shareName=shareName,
            ticket=ticket, username=username, password=password,
            filters=filters)
        return collection

    elif contentType == "application/eim+xml":

        # Note: For now we won't allow a subscription to a morsecode url
        # with no ticket and no pre-existing CosmoAccount set up,
        # since creation of a CosmoAccount item requires handshaking
        # with the server; we can add this later if needed

        # morsecode + eimml recordsets
        collection = subscribeMorsecode(view, url, inspection,
            activity=activity, account=account,
            ticket=ticket, username=username, password=password,
            filters=filters)
        return collection

    else:
        # unknown
        raise errors.SharingError("Unknown content type")




def subscribeCalDAV(view, url, inspection, activity=None, account=None,
    parentPath=None, shareName=None, ticket=None,
    username=None, password=None, filters=None):

    # TODO: Use filters parameter when this switches to CalDAV atop EIM

    # Append .chandler to the path
    parsedUrl = urlparse.urlsplit(url)
    path = parsedUrl.path
    if not path.endswith("/"):
        path += "/"

    if caldav_atop_eim:
        hasSubCollection = False

    else:
        subUrl = urlparse.urlunsplit((parsedUrl.scheme,
            parsedUrl.netloc, "%s%s/" % (path, SUBCOLLECTION), parsedUrl.query,
            parsedUrl.fragment))

        try:
            subInspection = inspect(subUrl, username=username,
                password=password)
        except:
            hasSubCollection = False
        else:
            hasSubCollection = True

    shareMode = 'both' if inspection['priv:write'] else 'get'

    share = None
    subShare = None

    if hasSubCollection:
        # Here is the Share for the subcollection with cloudXML
        subShare = Share(itsView=view)
        subShare.mode = shareMode
        subShareName = "%s/%s" % (shareName, SUBCOLLECTION)

        if account:
            subShare.conduit = WebDAVConduit(itsParent=subShare,
                shareName=subShareName, account=account)
        else:
            (useSSL, host, port, path, query, fragment, ticket, parentPath,
                shareName) = splitUrl(url)
            subShare.conduit = WebDAVConduit(itsParent=subShare, host=host,
                port=port, sharePath=parentPath, shareName=subShareName,
                useSSL=useSSL, ticket=ticket)

        subShare.format = CloudXMLFormat(itsParent=subShare)

        subShare.filterAttributes = []
        for attr in CALDAVFILTER:
            subShare.filterAttributes.append(attr)

    share = Share(itsView=view)
    share.mode = shareMode

    if caldav_atop_eim:

        if account:
            share.conduit = CalDAVRecordSetConduit(itsParent=share,
                shareName=shareName,
                account=account,
                translator=SharingTranslator,
                serializer=ICSSerializer)
        else:
            (useSSL, host, port, path, query, fragment, ticket, parentPath,
                shareName) = splitUrl(url)
            share.conduit = CalDAVRecordSetConduit(itsParent=share,
                host=host, port=port,
                sharePath=parentPath, shareName=shareName,
                useSSL=useSSL, ticket=ticket,
                translator=SharingTranslator,
                serializer=ICSSerializer)

        if filters:
            share.conduit.filters = filters


    else:
        share.format = CalDAVFormat(itsParent=share)
        if account:
            share.conduit = CalDAVConduit(itsParent=share,
                shareName=shareName, account=account)
        else:
            (useSSL, host, port, path, query, fragment, ticket, parentPath,
                shareName) = splitUrl(url)
            share.conduit = CalDAVConduit(itsParent=share, host=host,
                port=port, sharePath=parentPath, shareName=shareName,
                useSSL=useSSL, ticket=ticket)

    if subShare is not None:
        share.follows = subShare


    share.sync(activity=activity, modeOverride='get')
    share.conduit.getTickets()

    if caldav_atop_eim:
        displayName = share.conduit.getCollectionName()
        share.contents.displayName = displayName
        share.displayName = displayName

    if subShare is not None:
        # If this is a partial share, we need to store that fact
        # into this Share object
        if hasattr(subShare, 'filterClasses'):
            share.filterClasses = list(subShare.filterClasses)

        # Because of a bug, we don't really know whether the
        # publisher of this share intended to share alarms and
        # event status (transparency).  Let's assume not.  However,
        # we *can* determine their intention for sharing triage
        # status.
        share.filterAttributes = [
             pim.Remindable.reminders.name,
             pim.EventStamp.transparency.name
        ]
        if '_triageStatus' in getattr(subShare, 'filterAttributes', []):
            share.filterAttributes.append('_triageStatus')
        """
        Why just triageStatus and not triageStatusChanged in the code above?
        Is that a bug?

        Actually, not a bug.  Just an inconvenience related to
        having dual-fork shares (.ics and .xml).  What happens is
        the subShare (.xml fork) gets its filter list from the
        server, then lets the upper share (.ics) know that triageStatus
        is or is not being filtered.  As triageStatus is not actually
        shared via .ics, it doesn't matter to the sharing layer
        that triageStatusChanged isn't listed in the upper share's
        filter list.  The real reason I add triageStatus to the
        upper share's filter list is so the "manage share" dialog
        can see that the triage status sharing checkbox should be
        checked or not.  This is what happens when the system is
        designed for one thing (single-fork shares) and eventually
        bent to fit a new need (dual-fork shares).  As the dual-fork
        stuff is going away soon, I wouldn't worry about this.
        """

    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    # If free busy has already been published, add the subscribed
    # collection to publishedFreeBusy if appropriate
    updatePublishedFreeBusy(share)

    return share.contents




def subscribeWebDAV(view, url, inspection, activity=None, account=None,
    parentPath=None, shareName=None, ticket=None,
    username=None, password=None, filters=None):

    shareMode = 'both' if inspection['priv:write'] else 'get'

    share = Share(itsView=view)
    share.mode = shareMode
    share.format = CloudXMLFormat(itsParent=share)

    if account:
        share.conduit = WebDAVRecordSetConduit(itsParent=share,
            account=account, shareName=shareName,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    else:
        (useSSL, host, port, path, query, fragment, ticket, parentPath,
            shareName) = splitUrl(url)
        share.conduit = WebDAVRecordSetConduit(itsParent=share, host=host,
            port=port, sharePath=parentPath, shareName=shareName,
            useSSL=useSSL, ticket=ticket,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    if filters:
        share.conduit.filters = filters

    share.sync(activity=activity, modeOverride='get')
    share.conduit.getTickets()

    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    return share.contents




def subscribeICS(view, url, inspection, activity=None,
    account=None, parentPath=None, shareName=None, ticket=None,
    username=None, password=None, filters=None):

    share = Share(itsView=view)

    (useSSL, host, port, path, query, fragment, ticket, parentPath,
        shareName) = splitUrl(url)

    if not account and not ticket and username:
        # Create a new account
        account = WebDAVAccount(itsView=view)
        account.displayName = url
        account.host = host
        account.path = parentPath
        account.useSSL = useSSL
        account.port = port
        account.username = username
        if password:
            account.password = Password(itsParent=account)
            waitForDeferred(account.password.encryptPassword(password))

    if account:
        share.conduit = WebDAVMonolithicRecordSetConduit(
            itsParent=share,
            shareName=shareName,
            account=account,
            translator=SharingTranslator,
            serializer=ICSSerializer
        )

    else:
        share.conduit = WebDAVMonolithicRecordSetConduit(
            itsParent=share,
            host=host, port=port,
            sharePath=parentPath, shareName=shareName,
            useSSL=useSSL,
            translator=SharingTranslator,
            serializer=ICSSerializer
        )
        if ticket:
            share.conduit.ticket = ticket
        if username:
            share.conduit.username = username
        if password:
            share.conduit.password = Password(itsParent=share.conduit)
            waitForDeferred(share.conduit.password.encryptPassword(password))

    share.mode = "both" if inspection['priv:write'] else "get"
    if filters:
        share.conduit.filters = filters

    if activity:
        activity.update(msg=_(u"Subscribing to calendar..."))

    share.get(activity=activity)

    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    return share.contents




def subscribeMorsecode(view, url, morsecodeUrl, inspection, activity=None,
    account=None, username=None, password=None, filters=None):

    shareMode = 'both' if inspection['priv:write'] else 'get'

    share = Share(itsView=view)
    share.mode = shareMode

    # Get the user-facing sharePath from url, e.g.  "/cosmo/pim/collection"
    (useSSL, host, port, path, query, fragment, ticket, sharePath,
        shareName) = splitUrl(url)

    if not ticket and account is None:
        # Create a new account
        account = CosmoAccount(itsView=view)
        account.displayName = url
        account.host = host
        account.path = "cosmo" # TODO: See if we can really determine this.
        # pimPath, morsecodePath, and davPath all have initialValues
        account.useSSL = useSSL
        account.port = port
        account.username = username
        waitForDeferred(account.password.encryptPassword(password))

    if account:
        share.conduit = CosmoConduit(itsParent=share,
            shareName=shareName, account=account,
            translator=SharingTranslator, serializer=EIMMLSerializer)
    else:
        # Get the morsecode path from url, e.g.  "/cosmo/mc/collection"
        (useSSL, host, port, path, query, fragment, ticket, morsecodePath,
            shareName) = splitUrl(morsecodeUrl)

        share.conduit = CosmoConduit(itsParent=share, host=host,
            port=port, sharePath=sharePath, morsecodePath=morsecodePath,
            shareName=shareName,
            useSSL=useSSL, ticket=ticket,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    if filters:
        share.conduit.filters = filters

    share.sync(activity=activity, modeOverride='get')

    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    return share.contents





def unsubscribe(collection):
    if has_stamp(collection, SharedItem):
        collection = SharedItem(collection)
        for share in collection.shares:
            deleteShare(share)


def interrogate(conduit, location, ticket=None):
    """ Determine sharing permissions and other details about a collection """

    if not location.endswith("/"):
        location += "/"

    handle = conduit._getServerHandle()
    resource = handle.getResource(location)
    if ticket:
        resource.ticketId = ticket
    
    logger.debug('Examining %s ...', location)
    try:
        exists = handle.blockUntil(resource.exists)
        if not exists:
            logger.debug("...doesn't exist")
            raise NotFound(message="%s does not exist" % location)
    except zanshin.webdav.PermissionsError:
        raise NotAllowed(_("You don't have permission"))

    isReadOnly = True
    shareMode = 'get'
    hasPrivileges = False
    hasSubCollection = False

    logger.debug('Checking for write-access to %s...', location)
    try:
        privilege_set = handle.blockUntil(resource.getPrivileges)
        if ('read', 'DAV:') in privilege_set.privileges:
            hasPrivileges = True
        if ('write', 'DAV:') in privilege_set.privileges:
            isReadOnly = False
            shareMode = 'both'
    except zanshin.http.HTTPError, err:
        logger.debug("PROPFIND of current-user-privilege-set failed; error status %d", err.status)


    if isReadOnly and not hasPrivileges:
        # Cosmo doesn't support the current-user-privilege-set property yet,
        # so fall back to trying to create a child collection
        # Create a random collection name to create
        testCollName = u'.%s.tmp' % (UUID())
        try:
            child = handle.blockUntil(resource.createCollection,
                                      testCollName)
            handle.blockUntil(child.delete)
            isReadOnly = False
            shareMode = 'both'
        except zanshin.http.HTTPError, err:
            logger.debug("Failed to create test subcollection %s; error status %d", testCollName, err.status)

    logger.debug('...Read Only?  %s', isReadOnly)

    isCalendar = handle.blockUntil(resource.isCalendar)

    subLocation = urlparse.urljoin(location, SUBCOLLECTION)
    if not subLocation.endswith("/"):
        subLocation += "/"
    subResource = handle.getResource(subLocation)
    if ticket:
        subResource.ticketId = ticket
    try:
        hasSubCollection = handle.blockUntil(subResource.exists) and \
            handle.blockUntil(subResource.isCollection)
    except Exception, e:
        logger.exception("Couldn't determine existence of subcollection %s",
            subLocation)
        hasSubCollection = False
    logger.debug('...Has subcollection?  %s', hasSubCollection)

    if hasSubCollection:
        isCalendar = True # if there is a subcollection, then the main
                          # collection has to be a calendar

    logger.debug('...Calendar?  %s', isCalendar)

    isCollection =  handle.blockUntil(resource.isCollection)
    logger.debug('...Collection?  %s', isCollection)

    response = handle.blockUntil(resource.options)
    dav = response.headers.getHeader('DAV')
    logger.debug('...DAV:  %s', dav)
    allowed = response.headers.getHeader('Allow')
    logger.debug('...Allow:  %s', allowed)

    return (shareMode, hasSubCollection, isCalendar)




# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


class ProgressMonitor:

    def __init__(self, totalWork, callback):
        self.totalWork = totalWork
        self.updateCallback = callback
        self.workDone = 0

    def callback(self, **kwds):

        totalWork = kwds.get('totalWork', None)
        if totalWork is not None:
            self.totalWork = totalWork

        if kwds.get('work', None) is True:
            self.workDone += 1
            try:
                percent = int(self.workDone * 100 / self.totalWork)
            except ZeroDivisionError:
                percent = 100
            percent = min(percent, 100)
        else:
            percent = None

        msg = kwds.get('msg', None)

        return self.updateCallback(msg=msg, percent=percent)




# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Internal methods


def _newOutboundShare(view, collection, classesToInclude=None, shareName=None,
        displayName=None, account=None, useCalDAV=False,
        publishType='collection', inFreeBusy = False):
    """ Create a new Share item for a collection this client is publishing.

    If account is provided, it will be used; otherwise, the default WebDAV
    account will be used.  If there is no default account, None will be
    returned.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param collection: The ContentCollection that will be shared
    @type collection: ContentCollection
    @param classesToInclude: Which classes to share
    @type classesToInclude: A list of dotted class names
    @param account: The WebDAV Account item to use
    @type account: An item of kind WebDAVAccount
    @return: A Share item, or None if no WebDAV account could be found.
    """

    if account is None:
        # Find the default WebDAV account
        account = schema.ns('osaf.sharing', view).currentSharingAccount.item
        if account is None:
            return None

    share = Share(itsView=view, contents=collection)

    if useCalDAV and publishType=='collection':
        conduit = CalDAVConduit(itsParent=share, account=account,
                                shareName=shareName)
        format = CalDAVFormat(itsParent=share)
    else:
        conduit = WebDAVConduit(itsParent=share, account=account,
                                shareName=shareName)
        if publishType == 'freebusy':
            format = FreeBusyFileFormat(itsParent=share)
        else:
            format = CloudXMLFormat(itsParent=share)

    share.conduit = conduit
    share.format = format


    if classesToInclude is None:
        share.filterClasses = []
    else:
        share.filterClasses = classesToInclude

    share.displayName = displayName or collection.displayName
    # indicates that the DetailView should show this share
    fb = (publishType == 'freebusy')
    share.hidden = fb
    if fb:
        share.mode = 'put'
    
    share.sharer = schema.ns("osaf.pim", view).currentContact.item
    return share


def _uniqueName(basename, existing):
    name = basename
    counter = 1
    while name in existing:
        name = "%s-%d" % (basename, counter)
        counter += 1
    return name


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Formatters for conflicts (not sure where these should live yet)


triage_code_map = {
    "100" : _(u'Now'),
    "200" : _(u'Later'),
    "300" : _(u'Done'),
}
@format_field.when_object(ItemRecord.triage)
def format_item_triage(field, value):
    code, timestamp, auto = value.split(" ")
    return triage_code_map.get(code, _('Unknown'))


event_status_map = {
    'cancelled' : _(u'FYI'),
    'confirmed' : _(u'Confirmed'),
    'tentative' : _(u'Tentative'),
}
@format_field.when_object(EventRecord.status)
def format_event_status(field, value):
    return event_status_map.get(value.lower(), _('Unknown'))



@format_field.when_object(EventRecord.dtstart)
def format_event_dtstart(field, value):
    start, allDay, anyTime = fromICalendarDateTime(value)
    s = str(start)
    if allDay:
        s = "%s (all day)" % s
    if anyTime:
        s = "%s (any time)" % s
    return s


@format_field.when_object(EventRecord.duration)
def format_event_duration(field, value):
    duration = fromICalendarDuration(value)
    return "%s (hh:mm:ss)" % duration








# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Public methods that belong elsewhere:

def isIncomingMailSetUp(view):
    """
    See if the IMAP/POP account has at least the minimum setup needed.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    i = pim.mail.getCurrentIncomingAccount(view)

    return i is not None and i.isSetUp()

def isEmailAddressSetUp(view):
    me = pim.mail.getCurrentMeEmailAddress(view)

    return me is not None and me.isValid()

def isOutgoingMailSetUp(view):
    """
    See if SMTP account has at least the minimum setup needed for
    sharing (SMTP needs host).

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    # Find smtp account, and make sure server field is set
    o = pim.mail.getCurrentOutgoingAccount(view)

    return o is not None and o.isSetUp()

def isMailSetUp(view):
    """
    See if the email accounts have at least the minimum setup needed for
    sharing.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the accounts are set up; False otherwise.
    """
    if isIncomingMailSetUp(view) and isOutgoingMailSetUp(view) and \
       isEmailAddressSetUp(view):
        return True
    return False


def ensureAccountSetUp(view, sharing=False, inboundMail=False,
                       outboundMail=False, emailAddress=False):
    """
    A helper method to make sure the user gets the account info filled out.

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

        SharingReady = not sharing or isSharingSetUp(view)
        IncomingMailReady = not inboundMail or isIncomingMailSetUp(view)
        OutgoingMailReady = not outboundMail or isOutgoingMailSetUp(view)
        EmailReady = not emailAddress or isEmailAddressSetUp(view)

        if SharingReady and IncomingMailReady and OutgoingMailReady and EmailReady:
            return True

        msg = _(u"The following account(s) need to be set up:\n\n")
        if not SharingReady:
            msg += _(u" - Sharing\n")
        if not IncomingMailReady:
            msg += _(u" - IMAP/POP (inbound email)\n")
        if not EmailReady:
            msg += _(u" - At least one email address must be configured\n")
        if not OutgoingMailReady:
            msg += _(u" - SMTP (outbound email)\n")
        msg += _(u"\nWould you like to enter account information now?")

        response = wx.MessageBox(msg, _(u"Account set up"), style = wx.YES_NO) == wx.YES
        if response == False:
            return False

        if not IncomingMailReady:
            account = pim.mail.getCurrentIncomingAccount(view)
        elif not OutgoingMailReady:
            """ Returns the default SMTP Account or None"""
            account = pim.mail.getCurrentOutgoingAccount(view)
        else:
            account = schema.ns('osaf.sharing', view).currentSharingAccount.item

        response = dialogs.AccountPreferences.ShowAccountPreferencesDialog(
            account=account, rv=view)

        if response == False:
            return False




def getFilteredCollectionDisplayName(collection, filterClasses):
    """
    Return a displayName for a collection, taking into account what the
    current sidebar filter is, and whether this is the All collection.
    """
    # In the case of the All collection, the name is fixed for each kind.
    # l10n requires that each name be assigned specifically so the correct 
    # translation can be done (i.e. "My" is not context free in most languages, e.g. French)
    # In other cases, a compound name is built with the name of the collection and a
    # qualifier specific to the kind.
    
    allName = _(u"My items")
    ext = None

    if len(filterClasses) > 0:
        classString = filterClasses[0] # Only look at the first class
        if classString == "osaf.pim.tasks.TaskStamp":
            allName = _(u"My tasks")
            ext = _(u"tasks")
        elif classString == "osaf.pim.mail.MailStamp":
            allName = _(u"My mail")
            ext = _(u"mail")
        elif classString == "osaf.pim.calendar.Calendar.EventStamp":
            allName = _(u"My calendar")
            ext = _(u"calendar")

    if collection is schema.ns('osaf.pim', collection.itsView).allCollection:
        name = allName
    else:
        if ext is not None:
            # Genitive is different in each language so that requires an l10n string also
            name = _(u"%(collectionName)s %(kindFilter)s") % {
                'collectionName': collection.displayName, 'kindFilter': ext }
        else:
            name = collection.displayName

    return name

def fixTriageStatusCallback(share=None, uuids=None):
    """ 
    Set triageStatus on new 'now' items received from sharing, importing,
    or restore.
    """
    ## This is only called for old-style sharing, which should mostly be going
    ## away.  But now that triageStatus sharing includes the
    ## doAutoTriageOnDateChange flag, do auto-triage on import, even if
    ## triage status is shared.
    # Don't do this if we're sharing triageStatus (bug 7193)
    #if '_triageStatus' not in share.filterAttributes:
        #return

    for u in uuids:
        item = share.itsView.find(u)
        # @@@ bug 6700: Can't do this for recurring events for now.
        if Calendar.isRecurring(item):
            continue
        
        item.read = False
        item.setTriageStatus('auto', popToNow=True)
        
register(NEWITEMSUNESTABLISHED, fixTriageStatusCallback)
