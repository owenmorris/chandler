import davlib

from repository.item.Item import Item
from repository.util.URL import URL

import Sync

#@@@ Temporary way for retrieving webdav 'account' information
import osaf.framework.sharing.Sharing

import logging
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

class DAV(object):
    def __init__(self, resourceURL):
        super(DAV, self).__init__()
        if isinstance(resourceURL, basestring):
            resourceURL = URL(resourceURL)

        if not isinstance(resourceURL, URL):
            raise TypeError

        self.url = resourceURL

    def newConnection(self):
        return DAVConnection(self.url)

    def getHeaders(self):
        """ Perform a HTTP HEAD operation """
        r = self.newConnection().head(unicode(self.url))
        if r.status == 404:
            raise NotFound
        return r

    def putResource(self, body, type='text/plain'):
        """ Perform a HTTP PUT operation """
        return self.newConnection().put(unicode(self.url), body, type, None)
        # return status.. or maybe just throw an exception if the put failed

    def deleteResource(self):
        """ Perform a WebDAV DELETE operation """
        return self.newConnection().delete(unicode(self.url))

    def getProps(self, body, depth=0):
        """ Perform a WebDAV PROPFIND operation """
        r = self.newConnection().propfind(unicode(self.url), body, depth)
        if r.status == 404:
            raise NotFound
        return r

    def setProps(self, props):
        """ Perform a WebDAV PROPPATCH """
        r = self.newConnection().setprops2(unicode(self.url), props)
        log.debug('PROPPATCH returned:')
        log.debug(r.read())
        if r.status == 404:
            raise NotFound
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

        clouds = item.itsKind.getClouds('default')
        for cloud in clouds:
            for i in cloud.getItems(item):
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
    def __init__(self, url):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        acct = osaf.framework.sharing.Sharing.getWebDavAccount()
        self.setauth(acct.username, acct.password)
