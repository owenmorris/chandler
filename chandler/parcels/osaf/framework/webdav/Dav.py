import davlib

from repository.item.Item import Item
from repository.util.URL import URL

import application.Globals as Globals
import Sync

"""
 * If I make ItemCollections use a refcollection under the hood as a real attribute
   then I can get rid of most of the code in put/getCollection as it will just do
   the right thing automatically.  Wouldn't that be nice.
"""

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

    def putResource(self, body, mimetype='text/plain/'):
        return self.newConnection().put(unicode(self.url), body, mimetype, None)
        # return status.. or maybe just throw an exception if the put failed

    def getHeaders(self):
        r = self.newConnection().head(unicode(self.url))
        if r.status == 404:
            raise NotFound
        return r

    def _getETag(self):
        return self.getHeaders().getheader('ETag', default='')

    def _getLastModified(self):
        return self.getHeaders().getheader('Last-Modified', default='')


    def get(self):
        """ returns a newly created Item """
        try:
            return Sync.getItem(self)
        except NotFound:
            return None

    def put(self, item):
        # add an entry here to say that we're already here
        sharing = Globals.repository.findPath('//parcels/osaf/framework/GlobalShare') 
        sharing.itemMap[item.itsUUID] = item.itsUUID
        
        if item.hasAttributeValue('sharedURL'):
            # we only support you sharing to a single URL at the moment
            # it is an error to try and share to another place..
            if item.sharedURL != self.url:
                print 'Warning: trying to share %s to %s' % (unicode(item.sharedURL), unicode(self.url))
            # for now, force our current url to be the shared url
            self.url = item.sharedURL
        else:
            item.sharedURL = self.url

        self.sync(item)

    def sync(self, item):
        """
        clouds = item.itsKind.getClouds('default')
        for cloud in clouds:
            for i in cloud.getItems(item):
                Sync.syncItem(self, i)
        """
        Sync.syncItem(self, item)

    etag = property(_getETag)
    lastModified = property(_getLastModified)


class DAVConnection(davlib.DAV):
    def __init__(self, url):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        self.setauth('test', 'test')
