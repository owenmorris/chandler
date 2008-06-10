#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
    'getLabeledUrls',
    'getShare',
    'isOnline',
    'takeOnline',
    'takeOffline',
    'isCollectionOnline',
    'takeCollectionOnline',
    'takeCollectionOffline',
    'getActiveShares',
    'checkForActiveShares',
    'getExistingResources',
    'extractLinks',
    'blockingGetPage',
    'getPage',
    'isReadOnly',
    'getOldestVersion',
    'deleteShare',
    'splitUUID',
    'fromICalendarDateTime',
    'getDateUtilRRuleSet',
    'checkTriageOnly',
    'code_to_triagestatus',
    'triagestatus_to_code',
    'mergeFunction',
    'syncAll',
    'findUID',
    'STYLE_SINGLE',
    'STYLE_DIRECTORY',
]

from application import schema, Globals
import WebDAV
import urlparse, base64, datetime
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.Lob import Lob
from chandlerdb.persistence.RepositoryError import MergeError
from itertools import chain
from osaf.sharing import errors
from HTMLParser import HTMLParser
import logging
import shares
from osaf import pim
from osaf.framework.twisted import waitForDeferred

from zanshin.webdav import (
    PropfindRequest, ServerHandle, CALDAV_NAMESPACE
)
from zanshin.util import PackElement
from zanshin.ticket import Ticket, getTicketInfoNodes
import zanshin.http
import zanshin.error
import zanshin.acl as acl
import twisted.web.http as http
from twisted.python.failure import Failure
import xml.etree.cElementTree as ElementTree
import M2Crypto

from dateutil.rrule import rrulestr
import dateutil
from vobject.icalendar import (DateOrDateTimeBehavior, MultiDateBehavior)
from vobject.base import textLineToContentLine
from util import indexes

import osaf.pim.calendar.TimeZone as TimeZone

logger = logging.getLogger(__name__)





def mergeFunction(code, item, attribute, value):
    # 'value' is the one from *this* view
    # getattr(item, attribute) is the value from a different view

    if code == MergeError.DELETE:
        return True
    if code == MergeError.ALIAS:
        key, currentKey, alias = value
        logger.warning("While merging attribute '%s' on %s, an alias conflict for key %s was detected: %s is set to the same alias: '%s'", attribute, item._repr_(), key, currentKey, alias)
        return alias + '_duplicate'

    return value # Change from *this* view wins





def inspect(rv, url, username=None, password=None):

    # Twisted doesn't understand "webcal:"
    if url.startswith('webcal'):
        url = 'http' + url[6:]


    def _catchError(method):

        try:
            return method(rv, url, username=username, password=password)

        except zanshin.webdav.ConnectionError, e:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': e})

        except M2Crypto.BIO.BIOError, e:
            raise errors.CouldNotConnect(_(u"Unable to connect to server: %(error)s") % {'error': e})

        except zanshin.http.HTTPError, e:

            if e.status == 400: # Bad Request
                raise errors.IllegalOperation("Bad request (%s)" % e.message)
            elif e.status == 401: # Unauthorized
                raise errors.NotAllowed("Not authorized (%s)" % e.message)
            elif e.status == 404: # Not Found
                raise errors.NotFound("Not found (%s)" % e.message)
            else:
                raise e


    try:
        result = _catchError(getOPTIONS)
    except (errors.NotFound, errors.IllegalOperation, zanshin.http.HTTPError):
        # Google returns 404 if you OPTIONS a .ics URL, or a 400 if you
        # OPTIONS an HTML URL. Other random server error messages are possible
        # here, so let's try move on to HEAD here.
        return _catchError(getHEADInfo)

    if 'dav' in result:
        return _catchError(getDAVInfo)

    else:
        return _catchError(getHEADInfo)





def sync(collection, modeOverride=None, activity=None,
         forceUpdate=None):

    stats = []
    for share in getSyncableShares(collection.itsView, collection):
        stats.extend(share.sync(modeOverride=modeOverride,
                                activity=activity))
    return stats


def syncAll(rv):
    for share in getSyncableShares(rv):
        share.sync()




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

            syncable.append(share)

    return syncable



def getOldestVersion(rv):
    oldest = rv.itsVersion
    for share in getSyncableShares(rv):
        conduit = getattr(share, 'conduit', None)
        if conduit is not None:
            if hasattr(conduit, 'lastVersion'):
                if conduit.lastVersion < oldest:
                    oldest = conduit.lastVersion
    return oldest




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
        (host, p) = host.split(':')
        try:
            port = int(p)
        except ValueError:
            raise errors.URLParseError(_(u"Invalid port number: %(portNum)s") % {'portNum': p})


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

    return (scheme, useSSL, host, port, path, query, fragment, ticket,
        parentPath, shareName)






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



def serializeLiteral(view, attrValue, attrType):

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
        if attrValue.tzinfo == view.tzinfo.floating:
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
    @type view: L{chandlerdb.persistence.RepositoryView}
    @param url: A url pointing at a WebDAV Collection
    @type url: String
    @return: A Share item, or None
    """
    import accounts

    account = accounts.SharingAccount.findMatchingAccount(view, url)
    if account is None:
        return None

    # If we found a matching account, that means *potentially* there is a
    # matching share; go through all conduits this account points to and look
    # for shareNames that match

    (scheme, useSSL, host, port, path, query, fragment, ticket, parentPath,
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




def deleteShare(share):
    # Clean up sharing-related objects
    if getattr(share, "conduit", None):
        share.conduit.delete(True)
    if getattr(share, "format", None):
        share.format.delete(True)
    for state in getattr(share, "states", []):
        state.delete(True)
    share.delete(recursive=True)


def getUrls(share):
    url = share.getLocation()
    result = [share.getLocation(privilege=priv)
                 for priv in ('readwrite', 'readonly')]
    result = [u for u in result if u != url]

    if result:
        return result
    else:
        return [share.getLocation(privilege='subscribed')]


VIEW_AND_EDIT_STR = _(u"View and Edit")
VIEW_ONLY_STR = _(u"View-only")

def getLabeledUrls(share):
    labeled = []

    urls = getUrls(share)
    if len(urls) == 1:
        prefix = VIEW_AND_EDIT_STR if share.mode == "both" else VIEW_ONLY_STR
        labeled.append("%s: %s" % (prefix, urls[0]))
    else:
        labeled.append("%s: %s" % (VIEW_AND_EDIT_STR, urls[0]))
        labeled.append("%s: %s" % (VIEW_ONLY_STR, urls[1]))

    return labeled


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

def isReadOnly(item):
    """
    Return C{True} iff participating in a read-only share.
    """

    item = getattr(item, 'inheritFrom', item)

    # If we're not stamped, we're not shared
    if not pim.has_stamp(item, shares.SharedItem):
        return False

    item = shares.SharedItem(item)
    
    sharedIn = getattr(item, 'sharedIn', [])
    itemShares   = getattr(item, 'shares', [])
    # We might have been shared, see if we still are
    if not sharedIn and not itemShares: # not in any shares
        return False

    # For each share we're in, if *any* are writable, isReadOnly is False
    for share in chain(sharedIn, itemShares):
        if share.mode not in ('put', 'both'):
            return True

    return False





# Controls the online/offline state of the entire sharing layer:

def isOnline(rv):
    return schema.ns('osaf.sharing', rv).prefs.isOnline

def takeOnline(rv):
    schema.ns('osaf.sharing', rv).prefs.isOnline = True
    rv.commit(mergeFunction)

def takeOffline(rv):
    schema.ns('osaf.sharing', rv).prefs.isOnline = False
    rv.commit(mergeFunction)





# Controls the online/offline state of a single collection:

def isCollectionOnline(collection):
    """ Return the active state of the first share, if any """
    if not isOnline(collection.itsView):
        return False

    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        for share in collection.shares:
            return share.active
    return False

def takeCollectionOnline(collection):
    rv = collection.itsView
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        for share in collection.shares:
            share.active = True
        takeOnline(rv) # take sharing layer online

def takeCollectionOffline(collection):
    if pim.has_stamp(collection, shares.SharedItem):
        collection = shares.SharedItem(collection)
        for share in collection.shares:
            share.active = False






def getActiveShares(view):
    for share in shares.Share.iterItems(view):
        if (share.active and
            share.contents is not None):
            yield share




def checkForActiveShares(view):
    """
    See if there are any non-hidden, active shares.

    @param view: The repository view object
    @type view: L{chandlerdb.persistence.RepositoryView}
    @return: True if there are non-hidden, active shares; False otherwise
    """

    for share in shares.Share.iterItems(view):
        if share.active and share.active:
            return True
    return False




def getExistingResources(account):
    path = account.path.strip("/")
    handle = WebDAV.ChandlerServerHandle(account.host, port=account.port,
         username=account.username,
         password=waitForDeferred(account.password.decryptPassword()),
         useSSL=account.useSSL, repositoryView=account.itsView)

    if len(path) > 0:
        path = "/%s/" % path
    else:
        path = "/"

    existing = []
    parent   = handle.getResource(path)

    skipLen = len(path)

    resources = handle.blockUntil(parent.getAllChildren)

    for resource in resources:
        path = resource.path[skipLen:]
        path = path.strip(u"/")
        if path:
            existing.append(path)

    # @@@ [grant] Localized sort?
    existing.sort( )
    return existing




# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


def getDAVInfo(rv, url, username=None, password=None):
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

    handle = WebDAV.ChandlerServerHandle(host, port, username, password, useSSL,
        repositoryView=rv)

    properties = (
        PackElement("current-user-privilege-set"),
        PackElement("ticketdiscovery", Ticket.TICKET_NAMESPACE),
        PackElement("getcontenttype"),
        PackElement("resourcetype"),
    )

    path = parsedUrl.path
    if not path:
        path = "/"
    if parsedUrl.query:
        path = "%s?%s" % (path, parsedUrl.query)

    request = PropfindRequest(path, 0, list(properties), {})

    resp = handle.blockUntil(handle.addRequest, request)

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











def getHEADInfo(rv, url, username=None, password=None):
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

    handle = WebDAV.ChandlerServerHandle(host, port, username, password, useSSL,
        repositoryView=rv)

    path = parsedUrl.path
    if not path:
        path = "/"
    if parsedUrl.query:
        path = "%s?%s" % (path, parsedUrl.query)

    request = zanshin.http.Request('HEAD', path, None, None)
    resp = handle.blockUntil(handle.addRequest, request)

    resultDict = {
        'calendar' : False,
        'collection' : False,
        'priv:read' : True,
        'priv:write' : False,
    }

    if resp.status == http.FORBIDDEN:
        msg = _(u"The server rejected our request. Please check the URL. (HTTP status %(status)d)") % { 'status' : resp.status }
        raise errors.SharingError(msg,
            details=_(u"Received [%(body)s]") % {'body' : resp.body })
    elif resp.status != http.OK:
        raise zanshin.http.HTTPError(status=resp.status,
                                     message=resp.message)


    contentType = resp.headers.getHeader('Content-Type')
    if contentType:
        resultDict['contentType'] = contentType[0]

    return resultDict




def getOPTIONS(rv, url, username=None, password=None):

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

    handle = WebDAV.ChandlerServerHandle(host, port, username, password,
        useSSL, repositoryView=rv)

    path = parsedUrl.path
    if not path:
        path = "/"
    if parsedUrl.query:
        path = "%s?%s" % (path, parsedUrl.query)

    request = zanshin.http.Request('OPTIONS', path, None, None)
    resp = handle.blockUntil(handle.addRequest, request)

    resultDict = { }

    if resp.status == http.FORBIDDEN:
        msg = _(u"The server rejected our request. Please check the URL. (HTTP status %(status)d)") % { 'status' : resp.status }
        raise errors.SharingError(msg,
            details=_(u"Received [%(body)s]") % {'body' : resp.body })
    elif resp.status != http.OK:
        raise zanshin.http.HTTPError(status=resp.status,
                                     message=resp.message)


    cosmo = resp.headers.getHeader('X-Cosmo-Version')
    if cosmo:
        resultDict['cosmo'] = cosmo[0]

    dav = resp.headers.getHeader('DAV')
    if dav:
        resultDict['dav'] = dav[0]

    allow = resp.headers.getHeader('Allow')
    if allow:
        resultDict['allow'] = allow[0]

    return resultDict




def blockingGetPage(rv, url, username=None, password=None):
    """
    Returns the body of a resource
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

    handle = WebDAV.ChandlerServerHandle(host, port, username, password, useSSL,
        repositoryView=rv)

    path = parsedUrl.path
    if not path:
        path = "/"
    if parsedUrl.query:
        path = "%s?%s" % (path, parsedUrl.query)

    request = zanshin.http.Request('GET', path, None, None)
    resp = handle.blockUntil(handle.addRequest, request)

    if resp.status != http.OK:
        raise zanshin.http.HTTPError(status=resp.status,
                                     message=resp.message)

    return resp.body


def getPage(rv, url, **kw):
    """
    Similar to C{twisted.web.client.getPage}, except:
    
    (1) Does certificate matching.
    (2) Respects Chandler HTTP proxy settings.
    (3) Translates lower-level errors into L{osaf.sharing.error.Error}
        objects.
    """
    
    method = kw.pop('method', 'GET')
    
    username = kw.pop('username', None)
    password = kw.pop('password', None)
    body = kw.pop('body', None)
    factory = kw.pop('factory', WebDAV.ChandlerServerHandle)

    headers = dict(kw)
    
    parsedUrl = urlparse.urlsplit(url)
    useSSL = (parsedUrl.scheme == "https")
    if parsedUrl.port:
        port = parsedUrl.port
    elif useSSL:
        port = 443
    else:
        port = 80

    handle = factory(parsedUrl.hostname, port, username, password, useSSL, rv)

    path = parsedUrl.path

    if not path:
        path = "/"
    if parsedUrl.query:
        path = "%s?%s" % (path, parsedUrl.query)

    request = zanshin.http.Request('GET', path, headers, body)
    
    def got(response):
        if response.status == http.OK:
            return response.body
        elif response.status == http.UNAUTHORIZED:
            raise errors.NotAllowed(
                      _(u"Please verify your username and password"),
                      details="Received [%s]" % response.body
                  )
        else:
            raise zanshin.http.HTTPError(status=response.status,
                                         message=response.message)

    def failed(failure, host):
        logger.error("Error for url %s: %s", url, failure)
        if failure.check(zanshin.error.ConnectionError, errors.CouldNotConnect):
            # Note: do not localize the 'startswith' strings -- these need
            # to match twisted error messages:
            msg = failure.value.message
            if msg.startswith("DNS lookup failed"):
                msg = _(u"Unable to look up address '%(host)s via DNS. Check that your computer is correctly configured to access the internet.") % { 'host': host }
            elif msg.startswith("Connection was refused"):
                msg = _(u"The server '%(host)s' refused the connection.") % { 'host' : host }
            
            raise errors.CouldNotConnect(msg)

        return failure

    return handle.addRequest(request).addCallback(
               got).addErrback(
               failed, parsedUrl.hostname
          )
    

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



# = = = = = = = = = EIM Recurrence helper functions = = = = = = = = = = = = = = 

code_to_triagestatus = {
    "100" : pim.TriageEnum.now,
    "200" : pim.TriageEnum.later,
    "300" : pim.TriageEnum.done,
}
triagestatus_to_code = dict([[v, k] for k, v in code_to_triagestatus.items()])

def getDateUtilRRuleSet(field, value, dtstart):
    """
    Turn EIM recurrence fields into a dateutil rruleset.

    dtstart is required to deal with count successfully.
    """
    ical_string = ""
    if value.startswith(';'):
        # remove parameters, dateutil fails when it sees them
        value = value.partition(':')[2]
    # EIM uses a colon to concatenate RRULEs, which isn't iCalendar
    for element in value.split(':'):
        ical_string += field
        ical_string += ':'
        ical_string += element
        ical_string += "\r\n"
    # dateutil chokes on unicode, pass in a string
    return rrulestr(str(ical_string), forceset=True, dtstart=dtstart)

du_utc = dateutil.tz.tzutc()

def fromICalendarDateTime(view, text, multivalued=False):
    prefix = 'dtstart' # arbitrary
    if not text.startswith(';') and not text.startswith(':'):
        # no parameters
        prefix += ':'
    line = textLineToContentLine(prefix + text)
    if multivalued:
        line.behavior = MultiDateBehavior
    else:
        line.behavior = DateOrDateTimeBehavior
    line.transformToNative()
    anyTime = getattr(line, 'x_osaf_anytime_param', "").upper() == 'TRUE'
    allDay = False
    start = line.value
    if not multivalued:
        start = [start]
    if type(start[0]) == datetime.date:
        allDay = not anyTime
        start = [TimeZone.forceToDateTime(view, dt) for dt in start]
    else:
        tzid = line.params.get('X-VOBJ-ORIGINAL-TZID')
        if tzid is None:
            # RDATEs and EXDATEs won't have an X-VOBJ-ORIGINAL-TZID
            tzid = getattr(line, 'tzid_param', None)
        if start[0].tzinfo == du_utc:
            tzinfo = view.tzinfo.UTC
        elif tzid is None:
            tzinfo = view.tzinfo.floating
        else:
            # this parameter was broken, fixed in vobject 0.6.6, handle either
            # a string or take the first element of a list
            if not isinstance(tzid, basestring):
                tzid = tzid[0]
            tzinfo = view.tzinfo.getInstance(tzid)
        start = [dt.replace(tzinfo=tzinfo) for dt in start]
    if not multivalued:
        start = start[0]
    return (start, allDay, anyTime)

def getMasterAlias(alias):
    """Return the portion of the alias before the colon."""
    position = alias.find(':')
    if position == -1:
        return alias
    else:
        return alias[:position]

def splitUUID(view, recurrence_aware_uuid):
    """
    Split an EIM recurrence UUID.

    Return the tuple (UUID, recurrenceID or None).  UUID will be a string,
    recurrenceID will be a datetime or None.
    """
    pseudo_uuid = str(recurrence_aware_uuid)
    # tolerate old-style, double-colon pseudo-uuids
    position = pseudo_uuid.find('::')
    if position != -1:
        return (pseudo_uuid[:position],
                fromICalendarDateTime(view, pseudo_uuid[position + 2:])[0])
    position = pseudo_uuid.find(':')
    if position != -1:
        return (pseudo_uuid[:position],
                fromICalendarDateTime(view, pseudo_uuid[position:])[0])
    return (pseudo_uuid, None)

def checkTriageOnly(item):
    """
    Return true if item is a triage-only modification whose triage matches its
    startTime.
    """
    return (isinstance(item, pim.Note) and
            pim.EventStamp(item).isTriageOnlyModification() and
            pim.EventStamp(item).simpleAutoTriage() == item._triageStatus)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

STYLE_SINGLE = 'single' # Share represented by monolithic file
STYLE_DIRECTORY = 'directory' # Share is a directory where each item has
                              # its own file


def findUID(view, uid):
    """
    Return the master event whose icalUID matched uid, or None.
    """
    iCalendarItems = schema.ns("osaf.sharing", view).iCalendarItems
    return indexes.valueLookup(iCalendarItems, 'icalUID',
                                    pim.Note.icalUID.name, uid)

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

