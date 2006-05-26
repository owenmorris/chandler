"""

The sharing package provides a framework for importing, exporting,
and synchronizing collections of ContentItems.

Use the publish( ) and subscribe( ) methods to set up the sharing
of a collection and do the initial export/import; use sync( ) to
update.

"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import logging, urlparse, datetime

from application import schema, Utility
from application.Parcel import Reference
from osaf import pim
from i18n import OSAFMessageFactory as _

from repository.item.Monitors import Monitors
from repository.item.Item import Item
import chandlerdb

import zanshin, M2Crypto, twisted, re

import wx          # For the dialogs, but perhaps this is better accomplished
import application # via callbacks

from Sharing import *
from conduits import *
from WebDAV import *
from ICalendar import *
from application.Utility import getDesktopDir
import vobject

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
    background_syncing = schema.One(schema.Boolean, defaultValue = False)


def installParcel(parcel, oldVersion=None):

    SharingPreferences.update(parcel, "prefs")
    Reference.update(parcel, 'currentWebDAVAccount')

    from osaf import startup
    startup.PeriodicTask.update(parcel, "BackgroundSync",
        invoke="osaf.sharing.BackgroundSyncTask",
        run_at_startup=True,
        interval=datetime.timedelta(seconds=30)
    )

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class BackgroundSyncTask:

    def __init__(self, item):
        repo = item.itsView.repository
        for view in repo.views:
            if view.name == 'BackgroundSync':
                break
        else:
            view = repo.createView('BackgroundSync')

        self.rv = view
        self.busy = False

    def run(self):

        if self.busy:
            return True

        try:
            self.busy = True

            try:
                self.rv.refresh(notify=False)

                prefs = schema.ns('osaf.sharing', self.rv).prefs
                enabled = prefs.background_syncing
                if not enabled:
                    return True

                collections = []
                for share in Sharing.Share.iterItems(self.rv):
                    if(share.active and
                        share.contents is not None and
                        share.contents not in collections):
                        collections.append(share.contents)

                stats = []
                for collection in collections:
                    stats.extend(sync(collection, background=True))

            except Exception, e:
                logger.exception("Background sync error")

        finally:
            self.busy = False

        return True

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class ProgressMonitor:

    def __init__(self, totalWork, callback):
        self.totalWork = totalWork
        self.updateCallback = callback
        self.workDone = 0

    def callback(self, msg=None, work=None, totalWork=None):

        if totalWork is not None:
            self.totalWork = totalWork

        if work is True:
            self.workDone += 1
            try:
                percent = int(self.workDone * 100 / self.totalWork)
            except ZeroDivisionError:
                percent = 100
        else:
            percent = None

        return self.updateCallback(msg, percent)



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

    logger.debug('Examining %s ...', location.encode('ascii', 'replace'))
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
                    icsShare.follows = share
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


def subscribe(view, url, accountInfoCallback=None, updateCallback=None,
              username=None, password=None):

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

        # Allow the caller to override (and set) new username/password; helpful
        # from a 'subscribe' dialog:
        if username is not None:
            account.username = username
        if password is not None:
            account.password = password


        if account is None:
            # Prompt user for account information then create an account

            if accountInfoCallback:
                # Prompt the user for username/password/description:
                info = accountInfoCallback(host, path)
                if info is not None:
                    (description, username, password) = info
                    account = WebDAVAccount(itsView=view)
                    account.displayName = description
                    account.host = host
                    account.path = parentPath
                    account.username = username
                    account.password = password
                    account.useSSL = useSSL
                    account.port = port

        # The user cancelled out of the dialog
        if account is None:
            return None

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
                raise AlreadySubscribed(_(u"Already subscribed"))


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
        exists = handle.blockUntil(resource.exists)
        if not exists:
            logger.debug("...doesn't exist")
            raise NotFound(message="%s does not exist" % location)

        isReadOnly = False
        shareMode = 'both'

        # if ticket:
        # @@@MOR:  Grant -- canWrite( ) would be used here, hint hint

        logger.debug('Checking for write-access to %s...', location)
        # Create a random collection name to create
        testCollName = u'.%s.tmp' % (chandlerdb.util.c.UUID())
        try:
            child = handle.blockUntil(resource.createCollection,
                                      testCollName)
            handle.blockUntil(child.delete)
        except zanshin.http.HTTPError, err:
            logger.debug("Failed to create test subcollection %s; error status %d", testCollName, err.status)
            isReadOnly = True
            shareMode = 'get'
            
        # Creating a subcollection failed, but subcollections aren't required
        # for CalDAV servers.  Before deciding that the collection is really
        # read-only, try putting an empty event.  This should be replaced with
        # code that does a PROPFIND on current-user-privilege-set and checks
        # for the write privilege.
        if isReadOnly:
            dummyICS = vobject.iCalendar()
            vevent = dummyICS.add('vevent')
            vevent.add('dtstart').value = datetime.datetime.now(vobject.icalendar.utc)
            vevent.add('duration').value = datetime.timedelta(hours=1)
            id = str(chandlerdb.util.c.UUID())
            vevent.add('uid').value = id
            vevent.add('summary').value = "Test event"
            
            dummyPath = location + id + '.ics'

            handle = conduit._getServerHandle()

            dummyResource = handle.getResource(dummyPath)
            if ticket:
                dummyResource.ticketId = ticket
            
            try:
                handle.blockUntil(dummyResource.put, dummyICS.serialize(),
                                  checkETag=False, contentType="text/calendar")
            except zanshin.http.HTTPError, err:
                logger.debug("Failed to create dummy event; error status %d",
                             err.status)
                
            else:
                
                # succeeded at putting the resource, now delete it
                try:
                    handle.blockUntil(dummyResource.delete)
                except zanshin.webdav.ConnectionError, M2Crypto.BIO.BIOError:
                    msg = "Failed to delete dummy event, dangling resource " \
                          "%s left on server!"
                    logger.debug(msg, dummypath)
                
                isReadOnly = False
                shareMode = 'both'


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

            try:
                share.contents.shares.append(share, 'main')
            except ValueError:
                # There is already a 'main' share for this collection
                share.contents.shares.append(share)

        except Exception, err:
            logger.exception("Failed to subscribe to %s", url)

            if share:
                share.delete(True)
            if subShare:
                subShare.delete(True)
            raise

        return share.contents



def unsubscribe(collection):
    for share in collection.shares:
        share.delete(recursive=True, cloudAlias='copying')


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class Task(object):
    """
    Task class.

    @ivar running: Whether or not this task is actually running
    @type running: C{bool}
    """

    def __init__(self, repo):
        super(Task, self).__init__()
        self.view = repo.createView(name=repr(self))

    def start(self, inOwnThread=False):
        """
        Launches an activity either in the twisted thread,
        or in its own background thread.

        @param inOwnThread: If C{True}, this activity runs in its
           own thread. Otherwise, it is launched in the twisted
           thread.
        @type inOwnThread: bool
        """

        from twisted.internet import reactor
        if inOwnThread:
            fn = reactor.callInThread
        else:
            fn = reactor.callFromThread

        fn(self.__threadStart)

    def cancel(self):
        # Note that _callInMainThread() should work from
        # the main thread!
        self._callInMainThread(self.error,
                               SharingError(_(u"Cancelled by user")),
                               done=True)
        # XXX: [grant] Does self._error get called? Otherwise self.view
        # will never get cancelled.

    def __threadStart(self):
        # Run from background thread
        self.running = True

        try:
            self._run()
        except Exception, e:
            logger.exception("%s raised an error" % (self,))
            self._error(e)

    def _callInMainThread(self, f, arg, done=False):
        if self.running:
            def mainCallback(x):
                if self.running:
                    if done: self.running = False
                    f(x)
            wx.GetApp().PostAsyncEvent(mainCallback, arg)

    def _run(self):
        """Subclass hook; always called from the task's thread"""
        pass

    def _status(self, msg):
        """
        Subclasses can call this to ensure self.status() gets called in
        the UI thread.
        """

        self._callInMainThread(self.status, msg)

    def _completed(self, result):
        """
        Subclasses can call this to ensure self.completed() gets called in
        the UI thread.
        """
        self.view.commit()
        self._callInMainThread(self.completed, result, done=True)

    def _error(self, failure):
        """
        Subclasses can call this to ensure self.error() gets called in
        the UI thread
        """
        self.view.cancel()
        self._callInMainThread(self.error, failure, done=True)

    error = completed = status = lambda self, arg : None



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Public helper methods

def restoreFromAccount(account):

    view = account.itsView

    me = schema.ns("osaf.pim", view).currentContact.item

    accountUrl = account.getLocation()
    if not accountUrl.endswith('/'):
        accountUrl += "/"

    collections = []
    failures = []

    existing = getExistingResources(account)

    for name in existing:

        # name = urllib.quote_plus(name).decode('utf-8')
        url = accountUrl + name

        share = findMatchingShare(view, url)

        if share is None:
            try:
                collection = subscribe(view, url)

                # Make me the sharer
                for share in collection.shares:
                    share.sharer = me

                collections.append(collection)

            except Exception, err:
                failures.append(name)

    return (collections, failures)


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

        app = wx.GetApp()
        response = application.dialogs.Util.yesNo(app.mainFrame,
                                                  _(u"Account set up"),
                                                  msg)
        if response == False:
            return False

        if not InboundMailReady:
            account = pim.mail.getCurrentMailAccount(view)
        elif not SMTPReady:
            """ Returns the defaultSMTPAccount or None"""
            account = pim.mail.getCurrentSMTPAccount(view)
        else:
            account = schema.ns('osaf.sharing', view).currentWebDAVAccount.item

        response = \
          application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(
          app.mainFrame, account=account, rv=view)

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
