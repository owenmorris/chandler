import davlib

from repository.item.Item import Item
from repository.util.URL import URL

import Import, Export

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

    # importing
    def get(self):
        """ returns a newly created Item """
        return Import.getItem(self)

    def getCollection(self):
        """ gives back a new ItemCollection """
        # figure out properties of the collection itself.. I should share code
        # with Import.py here..
        # get a listing of all items in the collection... propfind depth 1

        # make a new ItemCollection based on the properties of the dav
        # collection

        # for each resource found in the dav collection, get it and add it to
        # our itemcollection
        pass

    # exporting
    def put(self, item):
        Export.putItem(self, item)

    def putCollection(self, itemCollection):
        """
        returns a url to a webdav collection containing
        all of the items in 'itemCollection'
        """
        # XXX the following code probably belongs in Export.py

        # make new dir for the collection, get its base url
        collectionURL = self.url.join(itemCollection.itsUUID.str16() + '/')

        r = DAV(collectionURL).newConnection().mkcol(collectionURL.path)
        print collectionURL, collectionURL.path
        # XXX parse response..
        # set attributes on the collection

        for item in itemCollection:
            itemURL = collectionURL.join(item.itsUUID.str16())
            DAV(itemURL).put(item)

        return collectionURL

    def sync(self):
        raise NotImplementedError


class DAVConnection(davlib.DAV):
    def __init__(self, url):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        self.setauth('username', 'password')
