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
    'inspect',
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
    'extractLinks',
    'getPage',
    'isReadOnly'
]

from application import schema
import WebDAV
import urlparse, base64, datetime
from PyICU import ICUtzinfo
from i18n import ChandlerMessageFactory as _
from repository.util.Lob import Lob
from itertools import chain
from osaf.sharing import errors
from HTMLParser import HTMLParser
import logging
import sys
from twisted.internet import reactor
import shares
from osaf import pim

from zanshin.webdav import (
    PropfindRequest, ServerHandle, quote, CALDAV_NAMESPACE
)
from zanshin.util import PackElement
from zanshin.ticket import Ticket, getTicketInfoNodes
import zanshin.http
import zanshin.acl as acl
import twisted.web.http as http
import xml.etree.cElementTree as ElementTree

logger = logging.getLogger(__name__)



def inspect(url, username=None, password=None):

    # Twisted doesn't understand "webcal:"
    if url.startswith('webcal'):
        url = 'http' + url[6:]

    try:
        return zanshin.util.blockUntil(getDAVInfo, url, username=username,
            password=password)

    except zanshin.http.HTTPError, e:

        if e.status == 401: # Unauthorized
            raise errors.NotAllowed("Not authorized (%s)" % e.message)
        elif e.status == 404: # Not Found
            raise errors.NotFound("Not found (%s)" % e.message)
        else:
            # just try to HEAD the resource
            return zanshin.util.blockUntil(getHEADInfo, url, username=username,
                password=password)

    except zanshin.webdav.ConnectionError, e:
        raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': e})

    except M2Crypto.BIO.BIOError, e:
        raise errors.CouldNotConnect(_(u"Unable to connect to server. Received the following error: %(error)s") % {'error': e})




def sync(collection, modeOverride=None, updateCallback=None,
         forceUpdate=None):

    stats = []
    for share in getSyncableShares(collection.itsView, collection):
        stats.extend(share.sync(modeOverride=modeOverride,
                                updateCallback=updateCallback))
    return stats






def getSyncableShares(rv, collection=None):

    syncable = []
    potential = []

    if collection is None:
        potential = shares.Share.iterItems(rv)
    else:
        if pim.has_stamp(collection, shares.SharedItem):
            potential = shares.SharedItem(collection).shares

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

    if url.startswith('webcal'):
        url = 'http' + url[6:]

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

    ticket = None
    if query:
        for part in query.split('&'):
            (arg, value) = part.split('=')
            if arg == 'ticket':
                ticket = value.encode('utf8')
                break

    # Get the parent directory of the given path:
    # '/dev1/foo/bar' becomes ['dev1', 'foo']
    pathList = path.strip(u'/').split(u'/')

    # ['dev1', 'foo'] becomes "dev1/foo"
    parentPath = u"/".join(pathList[:-1])

    shareName = pathList[-1]

    return (useSSL, host, port, path, query, fragment, ticket, parentPath,
        shareName)






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

    if not pim.has_stamp(collection, shares.SharedItem):
        return False

    for share in shares.SharedItem(collection).shares:
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
    import accounts

    account = accounts.WebDAVAccount.findMatchingAccount(view, url)
    if account is None:
        return None

    # If we found a matching account, that means *potentially* there is a
    # matching share; go through all conduits this account points to and look
    # for shareNames that match

    (useSSL, host, port, path, query, fragment, ticket, parentPath,
         shareName) = splitUrl(url)

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

    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        if hasattr(collection, 'shares') and collection.shares:

            share = collection.shares.getByAlias('main')
            if share is not None:
                return share

            for share in collection.shares:
                if share.hidden == False:
                    return share

    return None

def isReadOnly(collection):
    """
    Return C{True} iff participating in only read-only shares.
    """

    if not pim.has_stamp(collection, shares.SharedItem):
        return False

    collection = shares.SharedItem(collection)

    if not collection.shares:
        return False

    for share in collection.shares:
        if share.mode in ('put', 'both'):
            return False

    return True



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
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        if hasattr(collection, 'shares') and collection.shares:
            return collection.shares.getByAlias('freebusy')
    return None




def isOnline(collection):
    """ Return the active state of the first share, if any """
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        for share in collection.shares:
            return share.active
    return False

def takeOnline(collection):
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        for share in collection.shares:
            share.active = True

def takeOffline(collection):
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
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


def getDAVInfo(url, username=None, password=None):
    """
    Returns a deferred to a dict, describing various DAV properties of
    the URL. The deferred may errback if the resource doesn't support DAV.

    Keys in the resulting dictionary:

      - "priv:read", "priv:write", "priv:freebusy"
           Values are True if the given privilege is supported on the resource

      - "contentType"
           Value is a str indicating the MIME type of the resource. May not
           be present in the dictionary if the resource has no
           DAV:getcontenttype property.

      - "collection"
           Value is a bool that's True if url represents a DAV collection

      - "calendar"
          Value is a bool that's True if the url represents a CALDAV
          calendar collection.
    """

    parsedUrl = urlparse.urlsplit(url)
    useSSL = (parsedUrl.scheme == "https")
    host = parsedUrl.hostname
    if parsedUrl.port:
        port = parsedUrl.port
    else:
        if useSSL:
            port = 443
        else:
            port = 80

    handle = ServerHandle(host, port, username, password, useSSL)

    properties = (
        PackElement("current-user-privilege-set"),
        PackElement("ticketdiscovery", Ticket.TICKET_NAMESPACE),
        PackElement("getcontenttype"),
        PackElement("resourcetype"),
    )

    request = PropfindRequest(url, 0, list(properties), {})

    d = handle.addRequest(request)


    def handlePropfindResponse(resp):
        resultDict = dict(calendar=False, collection=False)

        if resp.status != http.MULTI_STATUS:
            raise zanshin.http.HTTPError(status=resp.status,
                                         message=resp.message)

        try:
            cups = acl.CurrentUserPrivilegeSet.parse(resp.body)
        except ValueError:
            # Some servers ignore the CUPS request, which is illegal,
            # but tolerate it and just return an empty privilege set
            cups = acl.CurrentUserPrivilegeSet()

        if not cups.privileges:
            ticketInfoNodes = getTicketInfoNodes(resp.body)
            if ticketInfoNodes:
                for node in ticketInfoNodes:
                    ticket = Ticket.parse(node)
                    for privName, value in ticket.privileges.iteritems():
                        # the ticket privileges dictionary currently doesn't
                        # have the flexibility to handle namespaces, that should
                        # probably be added.
                        if value and (privName, "DAV:") not in cups.privileges:
                            cups.privileges.append((privName, "DAV:"))
            else:
                # As Indiana Jones would say, "No ticket".
                # If the username was provided, and we got this far, then
                # the username and password is valid.  Assume we have read
                # and write permission
                cups.privileges.extend([('write', 'DAV:'), ('read', 'DAV:')])

        logger.debug("inspect getDAVinfo cups.privileges: %s", cups.privileges)
        for priv in (('read', "DAV:"), ('write', "DAV:"),
                           ('freebusy', CALDAV_NAMESPACE)):
            resultDict["priv:%s" % priv[0]] = (priv in cups.privileges)
        logger.debug("inspect getDAVinfo results: %s", resultDict)

        xml = ElementTree.XML(resp.body)

        for ctype in xml.getiterator(properties[2]):
            if ctype.text:
                resultDict.update(contentType=ctype.text)
                break

        calendarTag = PackElement("calendar", CALDAV_NAMESPACE)
        collectionTag = PackElement("collection")

        for rtype in xml.getiterator(properties[3]):
            for calendarElement in rtype.getiterator(calendarTag):
                resultDict.update(calendar=True)
                break
            for collectionElement in rtype.getiterator(collectionTag):
                resultDict.update(collection=True)
                break

        return resultDict


    return d.addCallback(handlePropfindResponse)




def getHEADInfo(url, username=None, password=None):
    """
    Returns a deferred to a dict, describing various DAV properties of
    the URL. The deferred may errback if the resource doesn't support DAV.

    Keys in the resulting dictionary:

      - "priv:read", "priv:write", "priv:freebusy"
           Values are True if the given privilege is supported on the resource

      - "contentType"
           Value is a str indicating the MIME type of the resource. May not
           be present in the dictionary if the resource has no
           DAV:getcontenttype property.

      - "collection"
           Value is a bool that's True if url represents a DAV collection

      - "calendar"
          Value is a bool that's True if the url represents a CALDAV
          calendar collection.
    """

    parsedUrl = urlparse.urlsplit(url)
    useSSL = (parsedUrl.scheme == "https")
    host = parsedUrl.hostname
    if parsedUrl.port:
        port = parsedUrl.port
    else:
        if useSSL:
            port = 443
        else:
            port = 80

    handle = ServerHandle(host, port, username, password, useSSL)
    request = zanshin.http.Request('HEAD', url, None, None)
    d = handle.addRequest(request)

    def handleHeadResponse(resp):
        resultDict = {
            'calendar' : False,
            'collection' : False,
            'priv:read' : True,
            'priv:write' : False,
        }

        if resp.status != http.OK:
            raise zanshin.http.HTTPError(status=resp.status,
                                         message=resp.message)


        contentType = resp.headers.getHeader('Content-Type')
        if contentType:
            resultDict['contentType'] = contentType[0]

        return resultDict


    return d.addCallback(handleHeadResponse)

def getPage(url, username=None, password=None):
    return zanshin.util.blockUntil(_getPage, url, username=username,
        password=password)


def _getPage(url, username=None, password=None):
    """
    Returns a deferred to a string
    """

    parsedUrl = urlparse.urlsplit(url)
    useSSL = (parsedUrl.scheme == "https")
    host = parsedUrl.hostname
    if parsedUrl.port:
        port = parsedUrl.port
    else:
        if useSSL:
            port = 443
        else:
            port = 80

    handle = ServerHandle(host, port, username, password, useSSL)
    request = zanshin.http.Request('GET', url, None, None)
    d = handle.addRequest(request)

    def handleGetResponse(resp):

        if resp.status != http.OK:
            raise zanshin.http.HTTPError(status=resp.status,
                                         message=resp.message)

        return resp.body

    return d.addCallback(handleGetResponse)



# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =



class LinkExtracter(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if tag == "link":
            data = dict(attrs)
            rel = data.get('rel', None)
            if rel == 'self':
                self.links['self'] = data.get('href', None)
            elif rel == 'alternate':
                linkType = data.get('type', None)
                link = data.get('href', None)
                if linkType and link:
                    self.links['alternate'][linkType] = link

def extractLinks(text):
    p = LinkExtracter()
    p.links = {'self' : None, 'alternate' : { }}
    p.feed(text)
    return p.links





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

