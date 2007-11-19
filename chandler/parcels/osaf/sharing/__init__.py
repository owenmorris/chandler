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


import logging, urlparse, datetime, wx, os.path, sys

from application import schema, dialogs, Globals
from application.Parcel import Reference
from application.Utility import getDesktopDir
from osaf import pim, ChandlerException, startup
from osaf.framework.password import Password, NoMasterPassword
from osaf.framework.twisted import waitForDeferred
from osaf.pim import isDead, has_stamp
from osaf.pim.calendar import Calendar
from osaf.pim.collections import (UnionCollection, DifferenceCollection,
                                  FilteredCollection)
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.c import UUID
from repository.persistence.RepositoryView import currentview
from osaf.activity import *

import twisted

from shares import *
from conduits import *
from errors import *
from utility import *
from webdav_conduit import *
from caldav_conduit import *
from recordset_conduit import *
from WebDAV import *
from callbacks import *
from eim import *
from model import *
from translator import *
from eimml import *
from cosmo import *
from itemcentric import *
from serialize import *
from ootb import *
from viewpool import *
from ics import *
from ICalendar import *
from stateless import *
from accounts import *


logger = logging.getLogger(__name__)



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingPreferences(schema.Item):
    import_dir = schema.One(schema.Text,
                     defaultValue = unicode(getDesktopDir(), sys.getfilesystemencoding()))
    import_as_new = schema.One(schema.Boolean, defaultValue = True)
    isOnline = schema.One(schema.Boolean, defaultValue=True)



class SyncPeriodicTask(startup.PeriodicTask):
    def fork(self):
        return startup.fork_item(self, name='Syncing', pruneSize=500,
            notify=False, mergeFn=mergeFunction)


def installParcel(parcel, oldVersion=None):

    rv = parcel.itsView

    SharingPreferences.update(parcel, "prefs")

    # Even though we're not using this at the moment, I'm leaving it here
    # because people's personal parcels refer to this and we'll probably
    # resurrect this someday:
    Reference.update(parcel, 'currentSharingAccount')

    SyncPeriodicTask.update(parcel, "sharingTask",
        invoke="osaf.sharing.BackgroundSyncHandler",
        run_at_startup=False,
        active=True,
        interval=datetime.timedelta(minutes=60)
    )


    # Make a collection of all Notes with an icalUID, so that
    # we can index it.
    filterAttribute = pim.Note.icalUID.name
    iCalendarItems = FilteredCollection.update(parcel, 'iCalendarItems',
        source=schema.ns('osaf.pim', rv).noteCollection,
        filterExpression="view.hasTrueValues(uuid, '%s')" % (filterAttribute,),
        filterAttributes=[filterAttribute])
    iCalendarItems.addIndex('icalUID', 'value', attribute=filterAttribute)


    # Make a collection used to let the main ui view know what new shared
    # inbound occurrences have come in so that OnIdle can check for duplicate
    # recurrenceIDs (via the processSharingQueue function below):
    pim.ListCollection.update(parcel, 'newItems')

    if not Globals.options.reload:
        prepareAccounts(rv)




def processSharingQueue(rv):
    # Called during OnIdle, this method looks for occurrences in this queue
    # (which is populated by recordset_conduit's sync( ) method) to check for
    # duplicate recurrenceIDs, caused by two views simultaneously creating
    # the same event modification. (bug 8213)

    q = schema.ns('osaf.sharing', rv).newItems
    for item in q:
        q.remove(item)
        if isinstance(item, pim.Occurrence):
            event = pim.EventStamp(item)
            id = event.recurrenceID
            for sibling in pim.EventStamp(item.inheritFrom).occurrences:
                if sibling is not item:
                    occurrence = pim.EventStamp(sibling)
                    if occurrence.recurrenceID == id:
                        # This occurrence is a locally-created duplicate of the
                        # one the sharing layer brought in.  For now, just
                        # delete it.  Later we can try to merge differences.
                        occurrence._safeDelete()
                        logger.info("Duplicate recurrenceID %s:%s, item: %s"
                            % (item.inheritFrom.itsUUID, id, sibling.itsUUID))




def getDefaultAccount(rv):
    # At the moment we're not using currentSharingAccount and don't have a
    # notion of a "default" sharing account, so just go through the list
    # and grab one.

    # Give preference to Cosmo accounts
    for account in CosmoAccount.iterItems(rv):
        if account.isSetUp():
            return account
    for account in WebDAVAccount.iterItems(rv):
        if account.isSetUp():
            return account
    return None


def isSharingSetUp(rv):
    for account in SharingAccount.iterItems(rv):
        if account.isSetUp():
            return True
    return False

def getSetUpAccounts(rv):
    accounts = []
    for account in CosmoAccount.iterItems(rv):
        if account.isSetUp():
            accounts.append(account)
    for account in WebDAVAccount.iterItems(rv):
        if account.isSetUp():
            accounts.append(account)
    return sorted(accounts, key = lambda x: x.displayName.lower())


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




current_activity = None

# ...set to an Activity object when sharing work is performed; interrupt( ) can
# be called from any thread -- it simply asks the activity to abort.  The next
# time the code which is carrying out the activity calls acitivity.update( ),
# the activity will raise an ActivityAborted.

def interrupt(graceful=True):
    """ Stop sync operations; if graceful=True, then the Share being synced
        at the moment is allowed to complete.  If graceful=False, stop the
        current Share in the middle of whatever it's doing.
    """
    global interrupt_flag, current_activity

    if graceful:
        interrupt_flag = GRACEFUL_STOP # allow the current sync( ) to complete
    else:
        interrupt_flag = IMMEDIATE_STOP # interrupt current sync( )
        if current_activity is not None:
            current_activity.requestAbort()



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

        global interrupt_flag, running_status, current_activity

        if running_status != IDLE:
            # busy
            return True

        stats = []
        running_status = RUNNING

        try: # ensuring we always return True {

            modeOverride = kwds.get('modeOverride', None)
            forceUpdate = kwds.get('forceUpdate', None)

            self.rv.refresh(notify=False)
            tz = self.rv.tzinfo.default

            if not (schema.ns('osaf.app', self.rv).prefs.isOnline and
                isOnline(self.rv)):
                # app and sharing layer must both be online to perform a sync
                running_status = IDLE
                return True

            shares = []

            if 'collection' in kwds:
                uuid = kwds['collection']
                collection = self.rv.findUUID(uuid)
            else:
                collection = None

                # TODO: someday replace this with an endpoint
                for account in CosmoAccount.iterAccounts(self.rv):
                    if  account.isSetUp():

                        if interrupt_flag != PROCEED: # interruption
                            raise ActivityAborted(_(u"Cancelled by user"))

                        try:
                            msg = _(u"Examining collections for %(account)s") \
                                % {'account' : account.displayName}
                            activity = Activity(msg)
                            activity.started()
                            current_activity = activity
                            info = account.getPublishedShares(blocking=True)
                            current_activity = None
                            activity.completed()

                            for uuid in account.unsubscribed:
                                if (uuid not in account.ignored and
                                    uuid not in account.requested):
                                    callCallbacks(UNSUBSCRIBEDCOLLECTIONS)

                        except ActivityAborted:
                            raise

                        except Exception, e:
                            logger.exception("Collection restore error")
                            activity.failed(e)
                            current_activity = None


            shares = getSyncableShares(self.rv, collection)

            for share in shares:

                if interrupt_flag != PROCEED: # interruption
                    raise ActivityAborted(_(u"Cancelled by user"))

                callCallbacks(UPDATE, msg="Syncing collection '%s'" %
                    share.contents.displayName)

                try:
                    activity = Activity("Sync: %s" % share.contents.displayName)
                    activity.started()
                    altView = viewpool.getView(self.rv.repository)
                    altShare = altView.findUUID(share.itsUUID)
                    current_activity = activity
                    stats.extend(altShare.sync(modeOverride=modeOverride,
                        activity=activity, forceUpdate=forceUpdate))
                    altView.commit(mergeFunction)
                    viewpool.releaseView(altView)
                    current_activity = None
                    activity.completed()

                except ActivityAborted:
                    logger.exception("Syncing cancelled")
                    altView.cancel()
                    viewpool.releaseView(altView)
                    raise

                except Exception, e:
                    logger.exception("Error syncing collection")
                    altView.cancel()
                    viewpool.releaseView(altView)
                    share.error, share.errorDetails = errors.formatException(e)
                    share.lastAttempt = datetime.datetime.now(tz)
                    stats.extend( [ { 'collection' : share.contents.itsUUID,
                                    'error' : str(e) } ] )
                    activity.failed(e)
                    current_activity = None


            try:
                log = schema.ns('osaf.sharing', self.rv).activityLog
            except AttributeError:
                log = None

            if log is not None:
                reportEvent = pim.CalendarEvent(itsView=self.rv,
                    displayName="Sync",
                    startTime=datetime.datetime.now(self.rv.tzinfo.default),
                    duration=datetime.timedelta(minutes=60),
                    anyTime=False,
                    transparency='fyi',
                    body=stats2str(self.rv, stats)
                )
                log.add(reportEvent.itsItem)

            self.rv.commit(mergeFunction)

            callCallbacks(UPDATE, msg='')


        except ActivityAborted:
            if shutdown_deferred:
                shutdown_deferred.callback(None)


        except: # } Can't raise an error from this method, so just log it
            logger.exception("Background sync error")


        running_status = IDLE
        interrupt_flag = PROCEED
        return True




def stats2str(rv, stats):
    # stats is an array of dictionaries, each of which have these keys:
    # share : a UUID object
    # added : a set of UUIDs
    # modified : a set of UUIDs
    # removed : a set of UUIDs
    # applied : a dictionary of aliases to Diffs
    # sent : a dictionary of aliases to Diffs
    lines = list()
    add = lines.append
    prevShare = None
    for stat in stats:
        shareUUID = stat.get('share', None)
        if shareUUID is not None:
            share = rv.findUUID(shareUUID)
            if share is not prevShare:
                coll = share.contents
                name = getattr(coll, 'displayName', _(u"Untitled"))
                add("Collection: %s" % name)
            prevShare = share
            if stat.has_key('applied'):
                for alias, diff in stat['applied'].iteritems():
                    for rec in sort_records(diff.inclusions):
                        add(" << ++ %s" % str(rec))
                    for rec in sort_records(diff.exclusions):
                        add(" << -- %s" % str(rec))
            if stat.has_key('sent'):
                for alias, diff in stat['sent'].iteritems():
                    if diff is not None:
                        for rec in sort_records(diff.inclusions):
                            add(" >> ++ %s" % str(rec))
                        for rec in sort_records(diff.exclusions):
                            add(" >> -- %s" % str(rec))
            for alias in stat['removed']:
                add(" %s !! %s" % ('>>' if stat['op'] == 'put' else '<<',
                    alias))

        else: # error
            coll = rv.findUUID(stat['collection'])
            name = getattr(coll, 'displayName', _(u"Untitled"))
            add("Collection: %s" % name)
            add("...error during sync: %s" % stat['error'])

    return "\n".join(lines)
            







# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def publish(collection, account, classesToInclude=None,
            filters=None, displayName=None, activity=None,
            overwrite=False, options=None):

    if not isOnline(collection.itsView):
        raise OfflineError(_(u"Could not perform request. Sharing is offline."))

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
        share.put()
        share.sharer = pim_ns.currentContact.item
        return share

    share = account.publish(collection, displayName=displayName,
        activity=activity, filters=filters, overwrite=overwrite,
        options=options)
    share.sharer = pim_ns.currentContact.item

    return share


def destroyShare(share):
    # Remove from server (or disk, etc.)
    try:
        share.destroy()
    except:
        logger.exception("Error trying to delete shared collection")
        # Even though we failed to remove the collection, we still need to
        # clean up the share objects, so continue on
    deleteShare(share)


def unpublish(collection):
    """
    Remove a share from the server, and delete all associated Share objects

    @type collection: pim.ContentCollection
    @param collection: The shared collection to unpublish

    """

    if has_stamp(collection, SharedItem):
        for share in SharedItem(collection).shares:
            destroyShare(share)


def deleteTicket(share, ticket):
    """Delete ticket associated with the given ticket string from the share."""
    conduit = share.conduit
    location = conduit.getLocation()
    if not location.endswith("/"):
        location += "/"
    handle = conduit._getServerHandle()
    resource = handle.getResource(location)
    return handle.blockUntil(resource.deleteTicket, ticket)





def subscribe(view, url, activity=None, username=None, password=None,
    filters=None):

    if not isOnline(view):
        raise OfflineError(_(u"Could not perform request. Sharing is offline."))

    if not url:
        raise URLParseError(_(u"No URL provided."))

    logger.info("Subscribing to URL: %s", url)

    try:
        (scheme, useSSL, host, port, path, query, fragment, ticket, parentPath,
            shareName) = splitUrl(url)
    except Exception, e:
        raise URLParseError(_(u"Could not parse URL: %(url)s") % {'url': url}, details=str(e))

    if not scheme:
        raise URLParseError(_(u"Protocol not specified."))

    if scheme not in ("http", "https", "webcal"):
        raise URLParseError(_(u"Protocol not supported: %(protocolName)s") % {"protocolName": scheme})

    if not host:
        raise URLParseError(_(u"No hostname specified."))

    if ticket:
        account = username = password = None

    else:
        # See if there is an account which matches this url already,
        # and use the username and password from it (as long as we're
        # not overriding it with passed-in username/password args)

        account = SharingAccount.findMatchingAccount(view, url)
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

            # update shareName if it's a subcollection in the account
            if account.path.strip("/") != parentPath.strip("/"):
                # account path: "a/b", parent path: "a/b/c", tail will be "c"
                tail = parentPath.strip("/")[len(account.path.strip("/"))+1:]
                if tail != "":
                    shareName = tail + "/" + shareName

    inspection = inspect(view, url, username=username, password=password)

    logger.info("Inspection results for %s: %s", url, inspection)


    for share in Share.iterItems(view):
        if url == share.getLocation("subscribed"):
            raise AlreadySubscribed(_(u"You are already subscribed to this collection."))

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
        text = getPage(view, url, username=username, password=password)

        # getPage needs to raise Forbidden exception, right?

        if text:
            links = extractLinks(text)

            selfUrl = links['self']
            if selfUrl is not None:
                if selfUrl.endswith('forbidden'):
                    raise NotAllowed(_(u"You don't have permission to access this collection."))

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

            # See if this was a "pim/collection" URL, and try the "mc" version
            try:
                index = url.index("pim/collection")
                url = url.replace("pim/collection", "mc/collection", 1)

                collection = subscribeMorsecode(view, url, url, inspection,
                    activity=activity,
                    account=account, username=username, password=password,
                    filters=filters)
                return collection

            except ValueError:
                # oh well, I can't find subscription information
                pass

        raise errors.WebPageParseError("Can't parse web page")

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
        collection = subscribeMorsecode(view, url, url, inspection,
            activity=activity, account=account,
            username=username, password=password,
            filters=filters)
        return collection

    else:
        # unknown
        raise errors.SharingError("Unknown content type")




def subscribeCalDAV(view, url, inspection, activity=None, account=None,
    parentPath=None, shareName=None, ticket=None,
    username=None, password=None, filters=None):

    parsedUrl = urlparse.urlsplit(url)
    path = parsedUrl.path
    if not path.endswith("/"):
        path += "/"

    shareMode = 'both' if inspection['priv:write'] else 'get'

    share = None

    share = Share(itsView=view)
    share.mode = shareMode

    if account:
        share.conduit = CalDAVRecordSetConduit(itsParent=share,
            shareName=shareName,
            account=account,
            translator=SharingTranslator,
            serializer=ICSSerializer)
    else:
        (scheme, useSSL, host, port, path, query, fragment, ticket,
            parentPath, shareName) = splitUrl(url)
        share.conduit = CalDAVRecordSetConduit(itsParent=share,
            host=host, port=port,
            sharePath=parentPath, shareName=shareName,
            useSSL=useSSL, ticket=ticket,
            translator=SharingTranslator,
            serializer=ICSSerializer)

    if filters:
        share.conduit.filters = filters


    share.get(activity=activity)
    share.conduit.getTickets()

    displayName = share.conduit.getCollectionName()
    share.contents.displayName = displayName
    share.displayName = displayName


    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    return share.contents




def subscribeWebDAV(view, url, inspection, activity=None, account=None,
    parentPath=None, shareName=None, ticket=None,
    username=None, password=None, filters=None):

    shareMode = 'both' if inspection['priv:write'] else 'get'

    share = Share(itsView=view)
    share.mode = shareMode

    if account:
        share.conduit = WebDAVRecordSetConduit(itsParent=share,
            account=account, shareName=shareName,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    else:
        (scheme, useSSL, host, port, path, query, fragment, ticket,
            parentPath, shareName) = splitUrl(url)
        share.conduit = WebDAVRecordSetConduit(itsParent=share, host=host,
            port=port, sharePath=parentPath, shareName=shareName,
            useSSL=useSSL, ticket=ticket,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    if filters:
        share.conduit.filters = filters

    share.get(activity=activity)
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

    (scheme, useSSL, host, port, ignore, query, ignore, ignore, ignore,
        ignore) = splitUrl(url)

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
        if query:
            share.conduit.shareName += "?%s" % query
        # Not setting share.conduit.ticket here because we'll just include it
        # in the URL during get/put


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

    # Get the user-facing sharePath from url, e.g.  "/cosmo/pim/collection"
    (scheme, useSSL, host, port, path, query, fragment, ticket, sharePath,
        shareName) = splitUrl(url)

    if not ticket:
        shareMode = 'both'
    else:
        shareMode = 'both' if inspection['priv:write'] else 'get'

    share = Share(itsView=view)
    share.mode = shareMode

    if not ticket and account is None:
        # Create a new account
        account = CosmoAccount(itsView=view)
        account.displayName = url
        account.host = host
        account.path = path[:path.find("/mc/")] # everything up to /mc/
        # pimPath, morsecodePath, and davPath all have initialValues
        account.useSSL = useSSL
        account.port = port
        account.username = username
        account.password = Password(itsParent=account)
        if password:
            waitForDeferred(account.password.encryptPassword(password))

    if account:
        share.conduit = CosmoConduit(itsParent=share,
            shareName=shareName, account=account,
            translator=SharingTranslator, serializer=EIMMLSerializer)
        share.mode = 'both' # if account, assume read/write


    else:
        # Get the morsecode path from url, e.g.  "/cosmo/mc/collection"
        (scheme, useSSL, host, port, path, query, fragment, ticket,
            morsecodePath, shareName) = splitUrl(morsecodeUrl)

        share.conduit = CosmoConduit(itsParent=share, host=host,
            port=port, sharePath=sharePath, morsecodePath=morsecodePath,
            shareName=shareName,
            useSSL=useSSL, ticket=ticket,
            translator=SharingTranslator, serializer=EIMMLSerializer)

    if filters:
        share.conduit.filters = filters

    share.get(activity=activity)

    if account:
        # Retrieve tickets
        shares = account.getPublishedShares(blocking=True)
        for name, uuid, href, tickets, subscribed in shares:
            if uuid == share.contents.itsUUID.str16():
                for ticket, ticketType in tickets:
                    if ticketType == 'read-only':
                        share.conduit.ticketReadOnly = ticket
                    elif ticketType == 'read-write':
                        share.conduit.ticketReadWrite = ticket

    try:
        SharedItem(share.contents).shares.append(share, 'main')
    except ValueError:
        # There is already a 'main' share for this collection
        SharedItem(share.contents).shares.append(share)

    return share.contents





def unsubscribe(collection):
    if has_stamp(collection, SharedItem):

        # Make all CosmoAccounts ignore this collection when it comes to
        # auto-restore:
        CosmoAccount.ignoreCollection(collection)

        collection = SharedItem(collection)
        for share in collection.shares:
            deleteShare(share)







# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Formatters for conflicts (not sure where these should live yet)

# don't use context sensitive formatters for special values like inherit
global_formatters[Inherit] = lambda f, v: _('Inherit')

triage_code_map = {
    "100" : _(u'Now'),
    "200" : _(u'Later'),
    "300" : _(u'Done'),
}
@format_field.when_object(ItemRecord.triage)
def format_item_triage(field, value):
    try:
        code, timestamp, auto = value.split(" ")
    except AttributeError:
        return _(u'Unknown')
    return triage_code_map.get(code, _(u'Unknown'))


event_status_map = {
    'cancelled' : _(u'FYI'),
    'confirmed' : _(u'Confirmed'),
    'tentative' : _(u'Tentative'),
}
@format_field.when_object(EventRecord.status)
def format_event_status(field, value):
    return event_status_map.get(value.lower(), _(u'Unknown'))



@format_field.when_object(EventRecord.dtstart)
def format_event_dtstart(field, value):
    start, allDay, anyTime = fromICalendarDateTime(currentview.get(), value)
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
    parent = wx.GetApp().mainFrame

    try:
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
                msg += _(u" - Inbound Mail\n")
            if not EmailReady:
                msg += _(u" - At least one email address must be configured.\n")
            if not OutgoingMailReady:
                msg += _(u" - Outbound Mail\n")
            msg += _(u"\nWould you like to set up your accounts now?")

            response = wx.MessageBox(msg, _(u"Account Set-up"), style = wx.YES_NO,
                parent=parent) == wx.YES
            if response == False:
                return False
    
            account = None
            create = None
    
            if not IncomingMailReady:
                account = pim.mail.getCurrentIncomingAccount(view)
            elif not OutgoingMailReady:
                """ Returns the default SMTP Account or None"""
                account = pim.mail.getCurrentOutgoingAccount(view)
            else:
                # Sharing is not set up, so grab an account
                accounts = list(SharingAccount.iterItems(view))
                if len(accounts) == 0:
                    create = "SHARING_HUB"
                else:
                    account = accounts[0]
    
    
            response = dialogs.AccountPreferences.ShowAccountPreferencesDialog(
                account=account, rv=view, create=create)
    
            if response == False:
                return False
    except NoMasterPassword:
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




def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'Sharing.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

