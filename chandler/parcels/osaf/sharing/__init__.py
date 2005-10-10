"""

The sharing package provides a framework for importing, exporting,
and synchronizing collections of ContentItems.

Use the publish( ) and subscribe( ) methods to set up the sharing
of a collection and do the initial export/import; use sync( ) to
update.

"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import logging, urlparse

from application import schema, Utility
from osaf import pim
from i18n import OSAFMessageFactory as _

from repository.item.Monitors import Monitors
import chandlerdb

import zanshin, M2Crypto, twisted


import wx          # For the dialogs, but perhaps this is better accomplished
import application # via callbacks


from Sharing import *
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

def installParcel(parcel, old_version=None):
    """
    Install an instance of UIDMap which maintains a calendar UID lookup table
    """

    uid_map = UIDMap.update(parcel, 'uid_map')

    # Anytime someone sets/removes an icalUID attribute, the UIDMap will
    # get updated:
    Monitors.attach(uid_map, 'icaluid_changed', 'set', 'icalUID')
    Monitors.attach(uid_map, 'icaluid_changed', 'remove', 'icalUID')

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def publish(collection, account, classesToInclude=None,
            attrsToExclude=None, basename=None, updateCallback=None):
    """
    Publish a collection, automatically determining which conduits/formats
    to use, and how many

    @type collection: pim.AbstractCollection
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
    @type basename: unicode
    @param basename: An optional name to use for publishing; if not provided,
                     the collection's displayName will be used as a starting
                     point.  In either case, to avoid collisions with existing
                     collections, '-1', '-2', etc., may be appended.
    @type updateCallback: method
    @param updateCallback: An optional callback method, which will get called
                           periodically during the publishing process.  If the
                           callback returns True, the publishing operation
                           will stop
    """

    view = collection.itsView

    conduit = WebDAVConduit(view=view, account=account)
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

            share.sync(updateCallback=updateCallback)

        else:

            # determine a share name
            existing = _getExistingResources(account)
            name = _uniqueName(basename or collection.displayName, existing)

            if ('calendar-access' in dav or 'MKCALENDAR' in allowed):

                # We're speaking to a CalDAV server

                # Create a CalDAV conduit / ICalendar format
                # Potentially create a cloudxml subcollection

                share = _newOutboundShare(view, collection,
                                         classesToInclude=classesToInclude,
                                         shareName=name,
                                         account=account,
                                         useCalDAV=True)

                if attrsToExclude:
                    share.filterAttributes = attrsToExclude

                try:
                    collection.shares.append(share, 'main')
                except ValueError:
                    # There is already a 'main' share for this collection
                    collection.shares.append(share)

                shares.append(share)
                share.displayName = name

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(updateCallback=updateCallback)

                if supportsTickets:
                    share.conduit.createTickets()

                # Create a subcollection to contain the cloudXML versions of
                # the shared items

                sub_name = u"%s/%s" % (name, SUBCOLLECTION)

                share = _newOutboundShare(view, collection,
                                         classesToInclude=classesToInclude,
                                         shareName=sub_name,
                                         account=account)

                if attrsToExclude:
                    share.filterAttributes = attrsToExclude
                else:
                    share.filterAttributes = []

                for attr in CALDAVFILTER:
                    share.filterAttributes.append(attr)

                shares.append(share)
                share.displayName = name

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(updateCallback=updateCallback)

                # Let's place the xml share first in the ref collection
                # so that it gets synced before the others
                collection.shares.placeItem(share, None)

            elif dav is not None:

                # We're speaking to a WebDAV server

                # Create a WebDAV conduit / cloudxml format
                share = _newOutboundShare(view, collection,
                                         classesToInclude=classesToInclude,
                                         shareName=name,
                                         account=account)

                try:
                    collection.shares.append(share, 'main')
                except ValueError:
                    # There is already a 'main' share for this collection
                    collection.shares.append(share)

                shares.append(share)
                share.displayName = name

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(updateCallback=updateCallback)
                if supportsTickets:
                    share.conduit.createTickets()

                ics_name = u"%s.ics" % name
                share = _newOutboundShare(view, collection,
                                         classesToInclude=classesToInclude,
                                         shareName=ics_name,
                                         account=account)
                shares.append(share)
                share.displayName = u"%s.ics" % name
                share.format = ICalendarFormat(parent=share)
                share.mode = "put"

                if share.exists():
                    raise SharingError(_(u"Share already exists"))

                share.create()
                share.put(updateCallback=updateCallback)
                if supportsTickets:
                    share.conduit.createTickets()

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


def unpublish(collection):
    """
    Remove a share from the server, and delete all associated Share objects

    @type collection: pim.AbstractCollection
    @param collection: The shared collection to unpublish
    """

    for share in collection.shares:

        # Remove from server (or disk, etc.)
        share.destroy()

        # Clean up sharing-related objects
        share.conduit.delete(True)
        share.format.delete(True)
        share.delete(True)



def subscribe(view, url, accountInfoCallback=None, updateCallback=None,
              username=None, password=None):

    (useSSL, host, port, path, query, fragment) = splitUrl(url)

    ticket = ""
    if query:
        for part in query.split('&'):
            (arg, value) = part.split('=')
            if arg == 'ticket':
                ticket = value.encode('utf8')
                break

    if ticket:
        account = None

        # Get the parent directory of the given path:
        # '/dev1/foo/bar' becomes ['dev1', 'foo']
        pathList = path.strip(u'/').split(u'/')
        parentPath = pathList[:-1]
        # ['dev1', 'foo'] becomes "dev1/foo"
        parentPath = u"/".join(parentPath)
        shareName = pathList[-1]

    else:
        account = WebDAVAccount.findMatch(view, url)

        # Allow the caller to override (and set) new username/password; helpful
        # from a 'subscribe' dialog:
        if username is not None:
            account.username = username
        if password is not None:
            account.password = password


        if account is None:
            # Prompt user for account information then create an account

            # Get the parent directory of the given path:
            # '/dev1/foo/bar' becomes ['dev1', 'foo']
            parentPath = path.strip(u'/').split(u'/')[:-1]
            # ['dev1', 'foo'] becomes "dev1/foo"
            parentPath = u"/".join(parentPath)

            if accountInfoCallback:
                # Prompt the user for username/password/description:
                info = accountInfoCallback(host, path)
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

        # The user cancelled out of the dialog
        if account is None:
            return None

        # compute shareName relative to the account path:
        accountPathLen = len(account.path.strip(u"/"))
        shareName = path.strip(u"/")[accountPathLen:]

    if account:
        conduit = WebDAVConduit(view=view, account=account,
            shareName=shareName)
    else:
        conduit = WebDAVConduit(view=view, host=host, port=port,
            sharePath=parentPath, shareName=shareName, useSSL=useSSL,
            ticket=ticket)

    try:
        location = conduit.getLocation()
        for share in Share.iterItems(view=view):
            if share.getLocation() == location:
                raise AlreadySubscribed(_(u"Already subscribed"))


        # Shortcut: if it's a .ics file we're subscribing to, it's only
        # going to be read-only (in 0.6 at least), and we don't need to
        # mess around with checking Allow headers and the like:

        if url.endswith(".ics"):
            share = Share(view=view)
            share.format = ICalendarFormat(parent=share)
            share.conduit = SimpleHTTPConduit(parent=share,
                                              shareName=shareName,
                                              account=account)
            share.mode = "get"
            try:
                share.sync(updateCallback=updateCallback)

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

        if ticket:
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

    finally:
        conduit.delete(True) # Clean up the temporary conduit

    if not isCalendar:

        # Just a WebDAV/XML collection

        share = Share(view=view)

        share.mode = shareMode

        share.format = CloudXMLFormat(parent=share)
        if account:
            share.conduit = WebDAVConduit(parent=share,
                                          shareName=shareName,
                                          account=account)
        else:
            share.conduit = WebDAVConduit(parent=share, host=host, port=port,
                sharePath=parentPath, shareName=shareName, useSSL=useSSL,
                ticket=ticket)

        try:
            share.sync(updateCallback=updateCallback)

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

        # We need to perform two syncs as one, so wrap these operations in
        # commit calls, and call the lower-level _get and _put methods directly
        view.commit()

        if hasSubCollection:
            # Here is the Share for the subcollection with cloudXML
            subShare = Share(view=view)
            subShare.mode = shareMode
            subShareName = "%s/%s" % (shareName, SUBCOLLECTION)

            if account:
                subShare.conduit = WebDAVConduit(parent=subShare,
                                                 shareName=subShareName,
                                                 account=account)
            else:
                subShare.conduit = WebDAVConduit(parent=subShare, host=host,
                    port=port, sharePath=parentPath, shareName=subShareName,
                    useSSL=useSSL, ticket=ticket)

            subShare.format = CloudXMLFormat(parent=subShare)

            for attr in CALDAVFILTER:
                subShare.filterAttributes.append(attr)

            try:
                subShare.conduit._get(updateCallback=updateCallback)
                contents = subShare.contents

            except Exception, err:
                location = subShare.getLocation()
                logger.exception("Failed to subscribe to %s", location)
                subShare.delete(True)
                raise

        else:
            subShare = None
            contents = None

        share = Share(view=view, contents=contents)
        share.mode = shareMode
        share.format = CalDAVFormat(parent=share)
        if account:
            share.conduit = CalDAVConduit(parent=share,
                                          shareName=shareName,
                                          account=account)
        else:
            share.conduit = CalDAVConduit(parent=share, host=host,
                port=port, sharePath=parentPath, shareName=shareName,
                useSSL=useSSL, ticket=ticket)

        try:
            share.conduit._get(updateCallback=updateCallback)

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

        if not isReadOnly:
            try:
                if subShare is not None:
                    subShare.conduit._put(updateCallback=updateCallback)
                share.conduit._put(updateCallback=updateCallback)
                view.commit()
                if subShare is not None:
                    subShare.conduit.syncVersion = view.itsVersion
                share.conduit.syncVersion = view.itsVersion

            except Exception, err:
                location = share.getLocation()
                logger.exception("Failed to subscribe to %s", location)
                if subShare is not None:
                    subShare.delete(True)
                share.delete(True)
                raise

        return share.contents


def sync(collection, firstTime=False):

    view = collection.itsView

    view.commit()

    stats = {}

    try:
        # perform the 'get' operations of all associated shares
        for share in collection.shares:
            if share.active and share.mode in ('get', 'both'):
                share.conduit._get()

        # perform the 'put' operations of all associated shares
        for share in collection.shares:
            if share.active and share.mode in ('put', 'both'):
                share.conduit._put()

    except SharingError, err:
        share.error = err.message

        try:
            msgVars = {
                'collectionName': share.contents.getItemDisplayName(),
                'accountName': share.conduit.account.getItemDisplayName()
            }

            msg = _(u"Error syncing the '%(collectionName)s' collection\nusing the '%(accountName)s' account\n\n") % msgVars
            msg += err.message
        except:
            msg = _(u"Error during sync")

        logger.exception("Sharing Error: %s" % msg)
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    _(u"Synchronization Error"), msg)

    view.commit()

    for share in collection.shares:
        if share.active and share.mode in ('put', 'both'):
            share.conduit.syncVersion = view.itsVersion


def unsubscribe(collection):
    for share in collection.shares:
        share.conduit.delete(True)
        share.format.delete(True)
        share.delete(True)


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Public helper methods

def restoreFromAccount(account):

    view = account.itsView

    me = pim.Contact.getCurrentMeContact(view)

    accountUrl = account.getLocation()
    if not accountUrl.endswith('/'):
        accountUrl += "/"

    collections = []
    failures = []

    existing = _getExistingResources(account)

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

    account = WebDAVAccount.findMatch(view, url)
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



def isShared(collection):
    """ Return whether an AbstractCollection has a Share item associated with it.

    @param collection: an AbstractCollection
    @type collection: AbstractCollection
    @return: True if collection does have a Share associated with it; False
        otherwise.
    """

    # See if any non-hidden shares are associated with the collection.
    # A "hidden" share is one that was not requested by the DetailView,
    # This is to support shares that don't participate in the whole
    # invitation process (such as transient import/export shares, or shares
    # for publishing an .ics file to a webdav server).

    for share in collection.shares:
        if share.hidden == False:
            return True
    return False

def isSharedByMe(share):
    if share is None:
        return False
    me = pim.Contact.getCurrentMeContact(share.itsView)
    return share.sharer is me



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
    """ Return the Share item (if any) associated with an AbstractCollection.

    @param collection: an AbstractCollection
    @type collection: AbstractCollection
    @return: A Share item, or None
    """

    # First, see if there is a 'main' share for this collection.  If not,
    # return the first "non-hidden" share for this collection -- see isShared()
    # method for further details.

    if collection.shares:

        share = collection.shares.getByAlias('main')
        if share is not None:
            return share

        for share in collection.shares:
            if share.hidden == False:
                return share

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

    account = schema.ns('osaf.app', view).currentWebDAVAccount.item
    if account and account.host and account.username and account.password:
        return True
    else:
        return False


def syncAll(view):
    """
    Synchronize all active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    """

    for collection in pim.AbstractCollection.iterItems(view):
        sync(collection)


def checkForActiveShares(view):
    """
    See if there are any non-hidden, active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if there are non-hidden, active shares; False otherwise
    """

    for share in Share.iterItems(view):
        if share.active and not share.hidden:
            return True
    return False


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Internal methods

def _getExistingResources(account):

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


def _newOutboundShare(view, collection, classesToInclude=None, shareName=None,
                     account=None, useCalDAV=False):
    """ Create a new Share item for a collection this client is publishing.

    If account is provided, it will be used; otherwise, the default WebDAV
    account will be used.  If there is no default account, None will be
    returned.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @param collection: The AbstractCollection that will be shared
    @type collection: AbstractCollection
    @param classesToInclude: Which classes to share
    @type classesToInclude: A list of dotted class names
    @param account: The WebDAV Account item to use
    @type account: An item of kind WebDAVAccount
    @return: A Share item, or None if no WebDAV account could be found.
    """

    if account is None:
        # Find the default WebDAV account
        account = schema.ns('osaf.app', view).currentWebDAVAccount.item
        if account is None:
            return None

    share = Share(view=view, contents=collection)

    if useCalDAV:
        conduit = CalDAVConduit(parent=share, account=account,
                                shareName=shareName)
        format = CalDAVFormat(parent=share)
    else:
        conduit = WebDAVConduit(parent=share, account=account,
                                shareName=shareName)
        format = CloudXMLFormat(parent=share)

    share.conduit = conduit
    share.format = format


    if classesToInclude is None:
        share.filterClasses = []
    else:
        share.filterClasses = classesToInclude

    share.displayName = collection.displayName
    share.hidden = False # indicates that the DetailView should show this share
    share.sharer = pim.Contact.getCurrentMeContact(view)
    return share


def _uniqueName(basename, existing):
    name = basename
    counter = 1
    while name in existing:
        name = "%s-%d" % (basename, counter)
        counter += 1
    return name


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

# The import/export mechanism needs a way to quickly map iCalendar UIDs to
# Chandler event items, so this singleton exists to store a ref collection
# containing imported calendar events, aliased by iCalendar UID:

class UIDMap(schema.Item):

    items = schema.Sequence("osaf.pim.CalendarEventMixin",
        otherName = "icalUIDMap",
        initialValue = {}
    )

    def icaluid_changed(self, op, item, attrName, *args, **kwds):

        if op == 'set':
            uid = getattr(item, 'icalUID', u'')
            if uid:
                try:
                    self.items.append(item, uid)
                except ValueError:
                    # Another event with this uid is in the map.
                    pass

        elif op == 'remove':
            self.items.remove(item)



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
            account = schema.ns('osaf.app', view).currentWebDAVAccount.item

        response = \
          application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(
          app.mainFrame, account=account, view=view)

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

    if collection is schema.ns('osaf.app', collection.itsView).allCollection:
        name = _(u"My")
        if ext == u"":
            ext = _(u" items")

    name += ext

    return name
