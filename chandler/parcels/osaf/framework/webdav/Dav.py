import davlib

from repository.item.Item import Item
from repository.util.URL import URL

from M2Crypto import SSL, httpslib

import Sync

#@@@ Temporary way for retrieving webdav 'account' information
import osaf.framework.sharing.Sharing

import logging, socket
log = logging.getLogger("sharing")
log.setLevel(logging.INFO)

"""
 * If I make ItemCollections use a refcollection under the hood as a real
   attribute then I can get rid of most of the code in put/getCollection
   as it will just do the right thing automatically.  Wouldn't that be nice.
"""

class NotShared(Exception):
    pass
class DAVException(Exception):
    pass
class NotFound(DAVException):
    pass
class NotAuthorized(DAVException):
    pass

class DAV(object):
    def __init__(self, resourceURL):
        super(DAV, self).__init__()
        if isinstance(resourceURL, basestring):
            resourceURL = URL(resourceURL)

        if not isinstance(resourceURL, URL):
            raise TypeError

        self.url = resourceURL

    def newConnection(self):
        acct = osaf.framework.sharing.Sharing.getWebDavAccount()
        if acct.useSSL:
            return SSLDAVConnection(self.url, acct)
        return DAVConnection(self.url, acct)

    def __request(self, func, *args):
        for i in xrange(4):
            try:
                # since we need to do a new connection if a timeout happens
                # this needs to go here and not in davlib's __request..
                # oh well.
                connection = self.newConnection()
                return  getattr(connection, func)(*args)
            except socket.timeout:
                log.warning('connection timed out.. retrying')
                continue
        raise socket.timeout

    def getHeaders(self):
        """ Perform a HTTP HEAD operation """
        r = self.__request('head', unicode(self.url))
        if r.status == 404:
            raise NotFound
        if r.status == 401:
            raise NotAuthorized
        return r

    def putResource(self, body, type='text/plain'):
        """ Perform a HTTP PUT operation """
        return self.__request('put', unicode(self.url), body, type, None)
        # return status.. or maybe just throw an exception if the put failed

    def deleteResource(self):
        """ Perform a WebDAV DELETE operation """
        return self.__request('delete', unicode(self.url))

    def getProps(self, body, depth=0):
        """ Perform a WebDAV PROPFIND operation """
        r = self.__request('propfind', unicode(self.url), body, depth)
        if r.status == 404:
            raise NotFound
        if r.status == 401:
            raise NotAuthorized
        return r

    def setProps(self, props):
        """ Perform a WebDAV PROPPATCH """
        r = self.__request('setprops2', unicode(self.url), props)
        log.debug('PROPPATCH returned:')
        log.debug(r.read())
        if r.status == 404:
            raise NotFound
        if r.status == 401:
            raise NotAuthorized
        return r

    def _getETag(self):
        """ Get the ETag using getHeaders() -- not cached """
        return self.getHeaders().getheader('ETag', default='')

    def _getLastModified(self):
        """ Get the last modified date using getHeaders() -- not cached """
        return self.getHeaders().getheader('Last-Modified', default='')


    def get(self):
        """ returns a newly created Item """
        return Sync.getItem(self)

    def put(self, item):
        """ puts items to the webdav server """
        # add an entry into the itemMap to indicate that there is a local copy of a foreign item
        sharing = item.itsView.findPath('//parcels/osaf/framework/GlobalShare')
        # XXX if item.itsUUID not in sharing.values(): # only add us if we originated here
        sharing.itemMap[item.itsUUID] = item.itsUUID

        if item.hasAttributeValue('sharedURL'):
            # warn if we're trying to share to another place
            if unicode(item.sharedURL) != unicode(self.url):
                log.warning('Trying to share %s to %s' % (unicode(item.sharedURL), unicode(self.url)))

        # let you share it to the new URL anyways
        item.sharedURL = self.url

        contentItemKind = item.itsView.findPath('//parcels/osaf/contentmodel/ContentItem')

        for i in item.getItemCloud('default'):
            # we only support publishing content items
            if not i.isItemOf(contentItemKind):
                log.warning('Skipping %s -- Not a ContentItem' % (str(i)))
                continue
            try:
                durl = i.sharedURL
            except AttributeError:
                durl = self.url.join(i.itsUUID.str16())
                i.sharedURL = durl

            sharing.itemMap[i.itsUUID] = i.itsUUID
            DAV(durl).sync(i)

        #self.sync(item)

    def sync(self, item):
        if not item.hasAttributeValue('sharedURL'):
            raise NotShared
        Sync.syncItem(self, item)

    etag = property(_getETag)
    lastModified = property(_getLastModified)


class DAVConnection(davlib.DAV):
    def __init__(self, url, acct):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        self.setauth(acct.username, acct.password)

class SSLDAV(httpslib.HTTPSConnection, davlib.DAV, object):
    """
    SSL-enabled "davlib.DAV". See M2Crypto.httpslib.HTTPSConnection for
    SSL-specific information.
    """
    def __init__(self, *args, **kwds):
        super(SSLDAV, self).__init__(*args, **kwds)

class SSLDAVConnection(SSLDAV):
    def __init__(self, url, acct):
        host = url.host
        port = url.port or 443

        super(SSLDAVConnection, self).__init__(host, port, ssl_context=SSL.Context('tlsv1'))
        self.setauth(acct.username, acct.password)
