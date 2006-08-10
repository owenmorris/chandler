#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


"""
The sharing package provides a framework for importing, exporting,
and synchronizing collections of ContentItems.

Use the publish( ) and subscribe( ) methods to set up the sharing
of a collection and do the initial export/import; use sync( ) to
update.
"""


import logging, urlparse, datetime
from PyICU import ICUtzinfo

from application import schema, Utility, dialogs
from application.Parcel import Reference
from application.Utility import getDesktopDir
from osaf import pim
from i18n import ChandlerMessageFactory as _
import vobject

from repository.item.Monitors import Monitors
from repository.item.Item import Item
import chandlerdb

import zanshin, M2Crypto, twisted, re

from Sharing import *
from conduits import *
from WebDAV import *
from ICalendar import *

logger = logging.getLogger(__name__)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# CalDAV settings:

# What to name the CloudXML subcollection on a CalDAV server:
SUBCOLLECTION = u".chandler"

# What attributes to filter out in the CloudXML subcollection on a CalDAV
# server (@@@MOR This should change to using a schema decoration instead
# of thie explicit list):

CALDAVFILTER = [
    'allDay', 'anyTime', 'duration', 'expiredReminders', 'isGenerated',
    'location', 'modifications', 'modifies', 'occurrenceFor',
    'recurrenceID', 'reminders', 'rruleset', 'startTime',
    'transparency'
]

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

PUBLISH_MONOLITHIC_ICS = True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class SharingPreferences(schema.Item):
    import_dir = schema.One(schema.Text, defaultValue = getDesktopDir())
    import_as_new = schema.One(schema.Boolean, defaultValue = True)


def installParcel(parcel, oldVersion=None):

    SharingPreferences.update(parcel, "prefs")
    Reference.update(parcel, 'currentWebDAVAccount')

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

    if running_status == IDLE:
        return

    if graceful:
        interrupt_flag = GRACEFUL_STOP # allow the current sync( ) to complete
    else:
        interrupt_flag = IMMEDIATE_STOP # interrupt current sync( )


registeredCallbacks = { }

def register(func, *args):
    global registeredCallbacks
    if func not in registeredCallbacks:
        registeredCallbacks[func] = args

def unregister(func):
    global registeredCallbacks
    try:
        del registeredCallbacks[func]
    except KeyError:
        pass

def _callCallbacks(**kwds):
    for (func, args) in registeredCallbacks.items():
        func(*args, **kwds)

# An example callback which simply prints to stdout:
# def printIt(*args, **kwds):
#     print args, kwds
# register(printIt)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _setError(collection, message):
    for share in getLinkedShares(collection.shares.first()):
        share.error = message

def _clearError(collection):
    for share in getLinkedShares(collection.shares.first()):
        if hasattr(share, 'error'):
            del share.error

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

        repo = item.itsView.repository
        for view in repo.views:
            if view.name == 'BackgroundSync':
                break
        else:
            view = repo.createView('BackgroundSync')

        self.rv = view
        running_status = IDLE

    def run(self, *args, **kwds):
        global interrupt_flag, running_status

        # A callback to allow cancelling of a sync( )
        def callback(msg=None, work=None, totalWork=None):
            kwds = {'msg':msg, 'work':work, 'totalWork':totalWork}
            _callCallbacks(**kwds)
            return interrupt_flag == IMMEDIATE_STOP

        def silentCallback(*args, **kwds):
            # Simply return the interrupt flag
            return interrupt_flag == IMMEDIATE_STOP

        if running_status != IDLE:
            # busy
            return True

        modeOverride = kwds.get('modeOverride', None)
        forceUpdate = kwds.get('forceUpdate', None)

        stats = []
        try:
            running_status = RUNNING


            try:
                self.rv.refresh(notify=False)


                collections = []

                if 'collection' in kwds:
                    uuid = kwds['collection']
                    collection = self.rv.findUUID(uuid)
                    collections.append(collection)

                else:
                    for share in Sharing.Share.iterItems(self.rv):
                        try:
                            if(share.active and
                                share.established and
                                share.contents is not None and
                                share.contents not in collections):
                                collections.append(share.contents)
                        except Exception, e:
                            logger.exception("Error with Share object")

                for collection in collections:

                    if interrupt_flag != PROCEED: # interruption
                        return True

                    _callCallbacks(msg="Syncing collection '%s'" %
                        collection.displayName)
                    try:
                        stats.extend(sync(collection,
                            modeOverride=modeOverride,
                            updateCallback=silentCallback,
                            forceUpdate=forceUpdate))
                        _clearError(collection)

                    except Exception, e:
                        # print "Exception", e
                        logger.exception("Error syncing collection")
                        if hasattr(e, 'message'): # Sharing error
                            msg = e.message
                        else:
                            msg = str(e)
                        _setError(collection, msg)
                        stats.extend( { 'collection' : collection.itsUUID,
                                        'error' : msg } )


            except Exception, e:
                # print "Exception", e
                logger.exception("Background sync error")

        finally:

            # Create the sync report event
            log = schema.ns('osaf.sharing', self.rv).activityLog
            reportEvent = pim.CalendarEvent(itsView=self.rv,
                displayName="Sync",
                startTime=datetime.datetime.now(ICUtzinfo.default),
                duration=datetime.timedelta(minutes=60),
                anyTime=False,
                transparency='fyi',
                body=str(stats)
            )
            log.add(reportEvent)

            self.rv.commit()

            running_status = IDLE
            _callCallbacks(msg='')
            if interrupt_flag != PROCEED:
                # We have been asked to stop, so fire the deferred
                if shutdown_deferred:
                    shutdown_deferred.callback(None)

            interrupt_flag = PROCEED

        return True

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
        else:
            percent = None

        msg = kwds.get('msg', None)

        return self.updateCallback(msg=msg, percent=percent)



def publish(collection, account, classesToInclude=None,
            publishType = 'collection',
            attrsToExclude=None, displayName=None, updateCallback=None):
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
    @type updateCallback: method
    @param updateCallback: An optional callback method, which will get called
                           periodically during the publishing process.  If the
                           callback returns True, the publishing operation
                           will stop
    """

    try:
        totalWork = len(collection)
    except TypeError: # Some collection classes don't support len( )
        totalWork = len(list(collection))

    if updateCallback:
        progressMonitor = ProgressMonitor(totalWork, updateCallback)
        callback = progressMonitor.callback
    else:
        progressMonitor = None
        callback = None

    view = collection.itsView

    conduit = WebDAVConduit(itsView=view, account=account)
    path = account.path.strip("/")

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
                collection.shares.append(share, 'main')
            except ValueError:
                # There is already a 'main' share for this collection
                collection.shares.append(share)

            if attrsToExclude:
                share.filterAttributes = attrsToExclude

            shares.append(share)
            share.displayName = collection.displayName

            share.sync(updateCallback=callback)

        else:

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

            if publishType == 'freebusy':
                shareName += '.ifb'
                alias = 'freebusy'


            if ('calendar-access' in dav or 'MKCALENDAR' in allowed):

                # We're speaking to a CalDAV server

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
                    collection.shares.append(share, alias)
                except ValueError:
                    # There is already a 'main' share for this collection
                    collection.shares.append(share)

                shares.append(share)

                # allow freebusy resources to just be overwritten
                if share.exists() and publishType != 'freebusy':
                    raise SharingError(_(u"Share already exists"))

                share.create()

                share.conduit.setDisplayName(displayName)

                if publishType == 'collection':
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
                        if progressMonitor:
                            progressMonitor.totalWork *= 2

                    except SharingError:
                        # We're not able to create the subcollection, so
                        # must be a vanilla CalDAV Server.  Continue on.
                        subShare.delete(True)
                        subShare = None

                else:
                    subShare = None

                share.put(updateCallback=callback)

                # tickets after putting
                if supportsTickets:
                    if publishType == 'collection':
                        share.conduit.createTickets()
                    elif publishType == 'freebusy':
                        share.conduit.getTickets()
                        # reuse existing tickets if possible
                        if not share.conduit.ticketReadOnly:
                            share.conduit.createTickets()


            elif dav is not None:

                # We're speaking to a WebDAV server

                # Create a WebDAV conduit / cloudxml or freebusy format
                share = _newOutboundShare(view, collection,
                                         classesToInclude=classesToInclude,
                                         shareName=shareName,
                                         displayName=displayName,
                                         account=account,
                                         publishType=publishType)

                try:
                    collection.shares.append(share, alias)
                except ValueError:
                    # There is already a 'main' share for this collection
                    collection.shares.append(share)

                shares.append(share)

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(updateCallback=callback)

                if supportsTickets:
                    share.conduit.createTickets()

                if PUBLISH_MONOLITHIC_ICS:
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
                    icsShare.put(updateCallback=callback)
                    if supportsTickets:
                        icsShare.conduit.createTickets()

    except (SharingError,
            zanshin.error.Error,
            M2Crypto.SSL.Checker.WrongHost,
            Utility.CertificateVerificationError,
            twisted.internet.error.TimeoutError), e:

        # Clean up share objects
        try:
            for share in shares:
                share.delete(True)
        except:
            pass

        raise

    return shares


def deleteShare(share):
    # Remove from server (or disk, etc.)
    if share.exists():
        share.destroy()

    # Clean up sharing-related objects
    share.conduit.delete(True)
    share.format.delete(True)
    share.delete(True)

def unpublish(collection):
    """
    Remove a share from the server, and delete all associated Share objects

    @type collection: pim.ContentCollection
    @param collection: The shared collection to unpublish

    """

    for share in collection.shares:
        deleteShare(share)

def unpublishFreeBusy(collection):
    """
    Remove a share from the server, and delete all associated Share objects

    @type collection: pim.ContentCollection
    @param collection: The collection to unpublish FreeBusy from

    """

    share = getFreeBusyShare(collection)
    if share is not None:
        deleteShare(share)


def subscribe(view, url, updateCallback=None, username=None, password=None,
              forceFreeBusy=False):

    if updateCallback:
        progressMonitor = ProgressMonitor(0, updateCallback)
        callback = progressMonitor.callback
    else:
        progressMonitor = None
        callback = None

    (useSSL, host, port, path, query, fragment) = splitUrl(url)

    ticket = ""
    if query:
        for part in query.split('&'):
            (arg, value) = part.split('=')
            if arg == 'ticket':
                ticket = value.encode('utf8')
                break

    # Get the parent directory of the given path:
    # '/dev1/foo/bar' becomes ['dev1', 'foo']
    pathList = path.strip(u'/').split(u'/')
    parentPath = pathList[:-1]
    # ['dev1', 'foo'] becomes "dev1/foo"
    parentPath = u"/".join(parentPath)

    if ticket:
        account = None
        shareName = pathList[-1]
    else:
        account = WebDAVAccount.findMatchingAccount(view, url)

        if account is None:
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
            account.password = password

        # compute shareName relative to the account path:
        accountPathLen = len(account.path.strip(u"/"))
        shareName = path.strip(u"/")[accountPathLen:]

    if account:
        conduit = WebDAVConduit(itsView=view, account=account,
            shareName=shareName)
    else:
        conduit = WebDAVConduit(itsView=view, host=host, port=port,
            sharePath=parentPath, shareName=shareName, useSSL=useSSL,
            ticket=ticket)

    try:
        location = conduit.getLocation()
        for share in Share.iterItems(view):
            if share.getLocation() == location:
                if share.established:
                    raise AlreadySubscribed(_(u"Already subscribed"))
                else:
                    share.delete(True)
                    break


        # Shortcut: if it's a .ics file we're subscribing to, it's only
        # going to be read-only (in 0.6 at least), and we don't need to
        # mess around with checking Allow headers and the like:

        if url.endswith(".ics"):
            share = Share(itsView=view)
            share.format = ICalendarFormat(itsParent=share)
            share.conduit = SimpleHTTPConduit(itsParent=share,
                                              shareName=shareName,
                                              account=account)
            share.mode = "get"
            share.filterClasses = \
                ["osaf.pim.calendar.Calendar.CalendarEventMixin"]

            if updateCallback:
                updateCallback(msg=_(u"Subscribing to calendar..."))

            try:
                share.get(updateCallback=callback)

                try:
                    share.contents.shares.append(share, 'main')
                except ValueError:
                    # There is already a 'main' share for this collection
                    share.contents.shares.append(share)

                return share.contents

            except Exception, err:
                logger.exception("Failed to subscribe to %s", url)
                share.delete(True)
                raise

        # Shortcut: similarly, if it's a .ifb file we're subscribing to, it's
        # read-only

        elif path.endswith(".ifb"):
            share = Share(itsView=view)
            share.format = FreeBusyFileFormat(itsParent=share)
            share.conduit = SimpleHTTPConduit(itsParent=share,
                                              host=host,
                                              port=port,
                                              useSSL=useSSL,
                                              shareName=shareName,
                                              sharePath=parentPath,
                                              account=account)
            if ticket:
                share.conduit.ticketReadOnly = ticket
            share.mode = "get"
            share.filterClasses = \
                ["osaf.pim.calendar.Calendar.CalendarEventMixin"]

            if updateCallback:
                updateCallback(msg=_(u"Subscribing to freebusy..."))

            try:
                share.get(updateCallback=callback)

                try:
                    share.contents.shares.append(share, 'main')
                except ValueError:
                    # There is already a 'main' share for this collection
                    share.contents.shares.append(share)

                return share.contents

            except Exception, err:
                logger.exception("Failed to subscribe to %s", url)
                share.delete(True)
                raise

        elif forceFreeBusy:
            share = Share(itsView=view)
            share.format = FreeBusyFileFormat(itsParent=share)
            share.conduit = CalDAVFreeBusyConduit(itsParent=share,
                                                  host=host,
                                                  port=port,
                                                  useSSL=useSSL,
                                                  shareName=shareName,
                                                  sharePath=parentPath,
                                                  account=account)
            if ticket:
                share.conduit.ticketReadOnly = ticket
            share.mode = "get"
            share.filterClasses = \
                ["osaf.pim.calendar.Calendar.CalendarEventMixin"]

            if updateCallback:
                updateCallback(msg=_(u"Subscribing to freebusy..."))

            try:
                share.get(updateCallback=callback)

                try:
                    share.contents.shares.append(share, 'main')
                except ValueError:
                    # There is already a 'main' share for this collection
                    share.contents.shares.append(share)

                return share.contents

            except Exception, err:
                logger.exception("Failed to subscribe to %s", url)
                share.delete(True)
                raise            

        if updateCallback:
            updateCallback(msg=_(u"Detecting share settings..."))

        # Interrogate the server

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
            testCollName = u'.%s.tmp' % (chandlerdb.util.c.UUID())
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
        logger.debug('...Calendar?  %s', isCalendar)

        if isCalendar:
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

        isCollection =  handle.blockUntil(resource.isCollection)
        logger.debug('...Collection?  %s', isCollection)

        response = handle.blockUntil(resource.options)
        dav = response.headers.getHeader('DAV')
        logger.debug('...DAV:  %s', dav)
        allowed = response.headers.getHeader('Allow')
        logger.debug('...Allow:  %s', allowed)

        if updateCallback:
            updateCallback(msg=_(u"Share settings detected; ready to subscribe"))


    finally:
        conduit.delete(True) # Clean up the temporary conduit

    if not isCalendar:

        # Just a WebDAV/XML collection

        share = Share(itsView=view)

        share.mode = shareMode

        share.format = CloudXMLFormat(itsParent=share)
        if account:
            share.conduit = WebDAVConduit(itsParent=share,
                                          shareName=shareName,
                                          account=account)
        else:
            share.conduit = WebDAVConduit(itsParent=share, host=host, port=port,
                sharePath=parentPath, shareName=shareName, useSSL=useSSL,
                ticket=ticket)

        try:
            if progressMonitor:
                if updateCallback and updateCallback(
                    msg=_(u"Getting list of remote items...")):
                    raise SharingError(_(u"Cancelled by user"))
                progressMonitor.totalWork = share.getCount()
            share.sync(updateCallback=callback, modeOverride='get')
            share.conduit.getTickets()

            try:
                share.contents.shares.append(share, 'main')
            except ValueError:
                # There is already a 'main' share for this collection
                share.contents.shares.append(share)

        except Exception, err:
            location = share.getLocation()
            logger.exception("Failed to subscribe to %s", location)
            share.delete(True)
            raise

        return share.contents

    else:

        # This is a CalDAV calendar, possibly containing an XML subcollection

        totalWork = 0

        try:
            share = None
            subShare = None

            if hasSubCollection:
                # Here is the Share for the subcollection with cloudXML
                subShare = Share(itsView=view)
                subShare.mode = shareMode
                subShareName = "%s/%s" % (shareName, SUBCOLLECTION)

                if account:
                    subShare.conduit = WebDAVConduit(itsParent=subShare,
                                                     shareName=subShareName,
                                                     account=account)
                else:
                    subShare.conduit = WebDAVConduit(itsParent=subShare, host=host,
                        port=port, sharePath=parentPath, shareName=subShareName,
                        useSSL=useSSL, ticket=ticket)

                subShare.format = CloudXMLFormat(itsParent=subShare)

                subShare.filterAttributes = []
                for attr in CALDAVFILTER:
                    subShare.filterAttributes.append(attr)

                if updateCallback and updateCallback(
                    msg=_(u"Getting list of remote items...")):
                    raise SharingError(_(u"Cancelled by user"))
                totalWork += subShare.getCount()


            share = Share(itsView=view)
            share.mode = shareMode
            share.format = CalDAVFormat(itsParent=share)
            if account:
                share.conduit = CalDAVConduit(itsParent=share,
                                              shareName=shareName,
                                              account=account)
            else:
                share.conduit = CalDAVConduit(itsParent=share, host=host,
                    port=port, sharePath=parentPath, shareName=shareName,
                    useSSL=useSSL, ticket=ticket)

            if updateCallback and updateCallback(
                msg=_(u"Getting list of remote items...")):
                raise SharingError(_(u"Cancelled by user"))
            totalWork += share.getCount()

            if subShare is not None:
                share.follows = subShare

            if progressMonitor:
                progressMonitor.totalWork = totalWork
            share.sync(updateCallback=callback, modeOverride='get')
            share.conduit.getTickets()

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
                share.filterAttributes = ['reminders', 'expiredReminders',
                    'transparency']
                if 'triageStatus' in getattr(subShare, 'filterAttributes', []):
                    share.filterAttributes.append('triageStatus')

            try:
                share.contents.shares.append(share, 'main')
            except ValueError:
                # There is already a 'main' share for this collection
                share.contents.shares.append(share)

        except Exception, err:
            logger.exception("Failed to subscribe to %s", url)
            raise

        return share.contents



def unsubscribe(collection):
    for share in collection.shares:
        share.delete(recursive=True, cloudAlias='copying')



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Public helper methods


def findMatchingShare(view, url):
    """ Find a Share which corresponds to a URL.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param url: A url pointing at a WebDAV Collection
    @type url: String
    @return: A Share item, or None
    """

    account = WebDAVAccount.findMatchingAccount(view, url)
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
                if conduit.share and conduit.share.hidden == False:
                    return conduit.share

    return None



def isSharedByMe(share):
    if share is None:
        return False
    me = schema.ns("osaf.pim", share.itsView).currentContact.item
    sharer = getattr(share, 'sharer', None)
    return sharer is me



def getUrls(share):
    if isSharedByMe(share):
        url = share.getLocation()
        readWriteUrl = share.getLocation(privilege='readwrite')
        readOnlyUrl = share.getLocation(privilege='readonly')
        if url == readWriteUrl:
            # Not using tickets
            return [url]
        else:
            return [readWriteUrl, readOnlyUrl]
    else:
        url = share.getLocation(privilege='subscribed')
        return [url]


def getShare(collection):
    """ Return the Share item (if any) associated with an ContentCollection.

    @param collection: an ContentCollection
    @type collection: ContentCollection
    @return: A Share item, or None
    """

    # First, see if there is a 'main' share for this collection.  If not,
    # return the first "non-hidden" share for this collection -- see isShared()
    # method for further details.

    if hasattr(collection, 'shares') and collection.shares:

        share = collection.shares.getByAlias('main')
        if share is not None:
            return share

        for share in collection.shares:
            if share.hidden == False:
                return share

    return None

def getFreeBusyShare(collection):
    """Return the free/busy Share item (if any) associated with a 
    ContentCollection.

    @param collection: an ContentCollection
    @type collection: ContentCollection
    @return: A Share item, or None
    
    """
    if hasattr(collection, 'shares') and collection.shares:
        return collection.shares.getByAlias('freebusy')
    return None

def isOnline(collection):
    """ Return the active state of the first share, if any """
    for share in collection.shares:
        return share.active
    return False


def takeOnline(collection):
    for share in collection.shares:
        share.active = True


def takeOffline(collection):
    for share in collection.shares:
        share.active = False


def isWebDAVSetUp(view):
    """
    See if WebDAV is set up.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if accounts are set up; False otherwise.
    """

    account = schema.ns('osaf.sharing', view).currentWebDAVAccount.item
    if account and account.host and account.username and account.password:
        return True
    else:
        return False


def syncAll(view, updateCallback=None):
    """
    Synchronize all active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    """

    sharedCollections = []
    for share in Share.iterItems(view):
        if (share.active and
            share.contents is not None and
            share.contents not in sharedCollections):
            sharedCollections.append(share.contents)

    stats = []
    for collection in sharedCollections:
        stats.extend(sync(collection, updateCallback=updateCallback))
    return stats


def checkForActiveShares(view):
    """
    See if there are any non-hidden, active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if there are non-hidden, active shares; False otherwise
    """

    for share in Share.iterItems(view):
        if share.active and share.active:
            return True
    return False


def getExistingResources(account):

    path = account.path.strip("/")
    handle = ChandlerServerHandle(account.host,
                                  port=account.port,
                                  username=account.username,
                                  password=account.password,
                                  useSSL=account.useSSL,
                                  repositoryView=account.itsView)

    if len(path) > 0:
        path = "/%s/" % path
    else:
        path = "/"

    existing = []
    parent = handle.getResource(path)
    skipLen = len(path)
    for resource in handle.blockUntil(parent.getAllChildren):
        path = resource.path[skipLen:]
        path = path.strip(u"/")
        if path:
            # path = urllib.unquote_plus(path).decode('utf-8')
            existing.append(path)

    # @@@ [grant] Localized sort?
    existing.sort( )
    return existing


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Internal methods


def _newOutboundShare(view, collection, classesToInclude=None, shareName=None,
        displayName=None, account=None, useCalDAV=False,
        publishType='collection'):
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
        account = schema.ns('osaf.sharing', view).currentWebDAVAccount.item
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
# Public methods that belong elsewhere:

def isInboundMailSetUp(view):
    """
    See if the IMAP/POP account has at least the minimum setup needed for
    sharing (IMAP/POP needs email address).

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    # Find imap account, and make sure email address is valid
    account = pim.mail.getCurrentMailAccount(view)
    if account is not None and account.replyToAddress and account.replyToAddress.emailAddress:
        return True
    return False


def isSMTPSetUp(view):
    """
    See if SMTP account has at least the minimum setup needed for
    sharing (SMTP needs host).

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the account is set up; False otherwise.
    """

    # Find smtp account, and make sure server field is set
    (smtp, replyTo) = pim.mail.getCurrentSMTPAccount(view)
    if smtp is not None and smtp.host:
        return True
    return False


def isMailSetUp(view):
    """
    See if the email accounts have at least the minimum setup needed for
    sharing.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if the accounts are set up; False otherwise.
    """
    if isInboundMailSetUp(view) and isSMTPSetUp(view):
        return True
    return False


def ensureAccountSetUp(view, sharing=False, inboundMail=False,
                       outboundMail=False):
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

        DAVReady = not sharing or isWebDAVSetUp(view)
        InboundMailReady = not inboundMail or isInboundMailSetUp(view)
        SMTPReady = not outboundMail or isSMTPSetUp(view)

        if DAVReady and InboundMailReady and SMTPReady:
            return True

        msg = _(u"The following account(s) need to be set up:\n\n")
        if not DAVReady:
            msg += _(u" - WebDAV (collection publishing)\n")
        if not InboundMailReady:
            msg += _(u" - IMAP/POP (inbound email)\n")
        if not SMTPReady:
            msg += _(u" - SMTP (outbound email)\n")
        msg += _(u"\nWould you like to enter account information now?")

        response = dialogs.Util.yesNo(None, _(u"Account set up"), msg)
        if response == False:
            return False

        if not InboundMailReady:
            account = pim.mail.getCurrentMailAccount(view)
        elif not SMTPReady:
            """ Returns the defaultSMTPAccount or None"""
            account = pim.mail.getCurrentSMTPAccount(view)
        else:
            account = schema.ns('osaf.sharing', view).currentWebDAVAccount.item

        response = dialogs.AccountPreferences.ShowAccountPreferencesDialog(
            None, account=account, rv=view)

        if response == False:
            return False




def getFilteredCollectionDisplayName(collection, filterClasses):
    """
    Return a displayName for a collection, taking into account what the
    current sidebar filter is, and whether this is the All collection.
    """

    #XXX: [i18n] logic needs to be refactored. It is impossible for a translator to 
    #     determine context from these sentence fragments.

    ext = u""

    if len(filterClasses) > 0:
        classString = filterClasses[0] # Only look at the first class
        if classString == "osaf.pim.tasks.TaskMixin":
           ext = _(u" tasks")
        if classString == "osaf.pim.mail.MailMessageMixin":
           ext = _(u" mail")
        if classString == "osaf.pim.calendar.Calendar.CalendarEventMixin":
           ext = _(u" calendar")

    name = collection.displayName

    if collection is schema.ns('osaf.pim', collection.itsView).allCollection:
        name = _(u"My")
        if ext == u"":
            ext = _(u" items")

    name += ext

    return name
