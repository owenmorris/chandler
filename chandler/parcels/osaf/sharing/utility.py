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
    'sync',
    'getSyncableShares',
    'splitUrl',
    'isShared',
    'localChanges',
    'serializeLiteral',
    'findMatchingShare',
    'isSharedByMe',
    'getUrls',
    'getShare',
    'getFreeBusyShare',
    'isOnline',
    'takeOnline',
    'takeOffline',
    'isWebDAVSetUp',
    'getActiveShares',
    'checkForActiveShares',
    'getExistingResources',
]

from application import schema
import WebDAV
import urlparse, base64, datetime
from PyICU import ICUtzinfo
from i18n import ChandlerMessageFactory as _
from repository.util.Lob import Lob
from itertools import chain
import logging

logger = logging.getLogger(__name__)




def sync(collection, modeOverride=None, updateCallback=None,
         forceUpdate=None):

    stats = []
    for share in getSyncableShares(collection.itsView, collection):
        stats.extend(share.sync(modeOverride=modeOverride,
                                updateCallback=updateCallback))
    return stats






def getSyncableShares(rv, collection=None):
    import shares

    syncable = []

    if collection is None:
        potential = shares.Share.iterItems(rv)
    else:
        potential = collection.shares

    for share in potential:

        if (share.active and
            share.established and
            share.contents is not None):

            linkedShares = share.getLinkedShares()
            leader = linkedShares[0]
            if leader not in syncable:
                syncable.append(leader)

    return syncable





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






def localChanges(view, fromVersion, toVersion):
    logger.debug("Computing changes from version %d to %d", fromVersion,
        toVersion)

    changedItems = {}

    for (uItem, version, kind, status, values, references,
         prevKind) in view.mapHistory(fromVersion, toVersion):
        if uItem in changedItems:
            changes = changedItems[uItem]
        else:
            changes = set([])
            changedItems[uItem] = changes
        changes.update(values)
        changes.update(references)

    return changedItems



def serializeLiteral(attrValue, attrType):

    mimeType = None
    encoding = None

    if isinstance(attrValue, Lob):
        mimeType = getattr(attrValue, 'mimetype', None)
        encoding = getattr(attrValue, 'encoding', None)
        data = attrValue.getInputStream().read()
        attrValue = base64.b64encode(data)

    if type(attrValue) is unicode:
        attrValue = attrValue.encode('utf-8')
    elif type(attrValue) is datetime.datetime:
        # @@@MOR 0.6 sharing compatibility
        # For backwards compatibility with 0.6 clients: since 0.6 doesn't
        # know about 'World/Floating' timezone, strip out the timezone when
        # exporting
        if attrValue.tzinfo is ICUtzinfo.floating:
            attrValue = attrValue.replace(tzinfo=None)
        attrValue = attrType.makeString(attrValue)
    elif type(attrValue) is not str:
        attrValue = attrType.makeString(attrValue)

    return (mimeType, encoding, attrValue)





def isShared(collection):
    """ Return whether an ContentCollection has a Share item associated with it.

    @param collection: an ContentCollection
    @type collection: ContentCollection
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
                if(getattr(conduit, 'share', None) and
                   conduit.share.hidden == False):
                    return conduit.share

    return None






def isSharedByMe(share):
    if share is None:
        return False
    me = schema.ns("osaf.pim", share.itsView).currentContact.item
    sharer = getattr(share, 'sharer', None)
    return sharer is me





def getUrls(share):
    if share == schema.ns('osaf.sharing', share.itsView).prefs.freeBusyShare:
        return [share.getLocation(privilege='freebusy')]
    elif isSharedByMe(share):
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
    caldavShare = schema.ns('osaf.sharing', collection.itsView).prefs.freeBusyShare
    if caldavShare is not None:
        return caldavShare
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




def getActiveShares(view):
    import shares
    for share in shares.Share.iterItems(view):
        if (share.active and
            share.contents is not None):
            yield share




def checkForActiveShares(view):
    """
    See if there are any non-hidden, active shares.

    @param view: The repository view object
    @type view: L{repository.persistence.RepositoryView}
    @return: True if there are non-hidden, active shares; False otherwise
    """

    import shares
    for share in shares.Share.iterItems(view):
        if share.active and share.active:
            return True
    return False




def getExistingResources(account):

    path = account.path.strip("/")
    handle = WebDAV.ChandlerServerHandle(account.host,
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
    parent   = handle.getResource(path)

    fbparent = handle.getResource(path + 'freebusy/')
    fbexists = handle.blockUntil(fbparent.exists)

    skipLen = len(path)

    resources = handle.blockUntil(parent.getAllChildren)
    if fbexists:
        resources = chain(resources, handle.blockUntil(fbparent.getAllChildren))
    ignore = ('', 'freebusy', 'freebusy/hiddenEvents', 'hiddenEvents')

    for resource in resources:
        path = resource.path[skipLen:]
        path = path.strip(u"/")
        if path not in ignore:
            # path = urllib.unquote_plus(path).decode('utf-8')
            existing.append(path)

    # @@@ [grant] Localized sort?
    existing.sort( )
    return existing




# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# Not used at the moment, but might be revived soon

def changedAttributes(item, fromVersion, toVersion):

    changes = set([])
    uuid = item.itsUUID

    for (uItem, version, kind, status, values, references,
         prevKind) in item.itsView.mapHistory(fromVersion, toVersion):
        if uItem == uuid:
            changes.update(values)
            changes.update(references)

    return changes

