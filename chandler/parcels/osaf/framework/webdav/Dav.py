import davlib
import httplib
import xml.sax.saxutils
import libxml2

from repository.item.Item import Item

import Import, Export

# WebDAVServer APIs

class DAV(object):
    def __init__(self, resourceURL):
        super(DAV, self).__init__()
        self.url = resourceURL

    def newConnection(self):
        return DavConnection(self.url)

    # importing
    def get(self):
        """ returns a newly created Item """
        return Import.getItem(self)

    def getCollection(self):
        """ gives back a new ItemCollection """
        # figure out properties of the collection itself.. I should share code
        # with Import.py here..
        # get a listing of all items in the collection... propfind?

        # make a new ItemCollection based on the properties of the dav
        # collection

        # for each resource found in the dav collection, get it and add it to
        # our itemcollection
        pass

    # exporting
    def put(self, item):
        Export.DAVExport(self, item)

    def putCollection(self, itemCollection):
        """
        returns a url to a webdav collection containing
        all of the items in 'itemCollection'
        """
        # XXX the following code probably belongs in Export.py

        # make new dir for the collection, get its base url
        collectionURL = self.url.join(itemCollection.itsUUID.str16())

        r = DAV(collectionURL).newConnection().mkcol(collectionURL.path)
        # parse response..
        # set attributes on the collection

        for item in itemCollection:
            itemURL = self.url.join(item.itsUUID.str16())
            DAV(itemURL).put(item)


class DavConnection(davlib.DAV):
    def __init__(self, url):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        self.setauth('username', 'password')
