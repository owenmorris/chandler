import davlib

from repository.item.Item import Item
from repository.util.URL import URL

import Import, Export

"""
 * If I make ItemCollections use a refcollection under the hood as a real attribute
   then I can get rid of most of the code in put/getCollection as it will just do
   the right thing automatically.  Wouldn't that be nice.
"""

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
        collection = self.get()

        # XXX i really don't like duplicating the code in Import.py
        listXmlGoop = collection._getAttribute('http://www.osafoundation.org/', 'items')
        nodes = Import.makeAndParse(listXmlGoop)

        for node in nodes:
            item = DAV(node.content).get()
            collection.add(item)

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
        # just put the item collection as a normal item first
        self.put(itemCollection)

        # then attatch extra data to it
        itemList = '<o:items xmlns:o="http://www.osafoundation.org/">'

        for item in itemCollection:
            itemURL = self.url.join(item.itsUUID.str16())
            DAV(itemURL).put(item)
            itemList = itemList + '<itemref>' + unicode(itemURL) + '</itemref>'

        itemList = itemList + '</o:items>'

        self.newConnection().setprops2(unicode(self.url), itemList)

        return self.url

    def sync(self):
        raise NotImplementedError


class DAVConnection(davlib.DAV):
    def __init__(self, url):
        host = url.host
        port = url.port or 80

        davlib.DAV.__init__(self, host, port)
        self.setauth('test', 'test')
