__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.util.Path import Path
from application.Application import app
import mx.DateTime
import types

BASE_PATH = '//Parcels/OSAF/examples/zaobao'
RSSITEM_KIND_PATH = BASE_PATH + '/RSSItem'

def SetAttribute(self, data, attr, nattr=None, encoding=None):
    if not nattr:
        nattr = attr
    value = data.get(attr)
    if value:
        if encoding:
            value = unicode(value, encoding)
        self.setAttributeValue(nattr, value)

def SetAttributes(self, data, attributes, encoding):
    if type(attributes) == types.DictType:
        for attr, nattr in attributes.items():
            SetAttribute(self, data, attr, nattr=nattr, encoding=encoding)
    elif type(attributes) == types.ListType:
        for attr in attributes:
            SetAttribute(self, data, attr, encoding=encoding)

class RSSFeed(Item):
    def Update(self, data):
        chanKind = app.repository.find(BASE_PATH + '/RSSChannel')

        # get the encoding
        encoding = data.get('encoding', 'latin_1')

        # set etag
        SetAttribute(self, data, 'etag')

        # set lastModified
        modified = data.get('modified')
        if modified:
            lastModified = mx.DateTime.mktime(modified)
            self.setAttributeValue('lastModified', lastModified)

        # update the feed's channel
        if not self.hasAttributeValue('channel'):
            self.channel = chanKind.newItem(None, self)
        self.channel.Update(data['channel'], data['items'], encoding)


class RSSChannel(Item):
    def Update(self, data, items, encoding):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs, encoding)

        attrs = ['description', 'creator', 'link', 'category', 'language', 'date']
        SetAttributes(self, data, attrs, encoding)

        # make children
        itemKind = app.repository.find(RSSITEM_KIND_PATH)
        for itemData in items:
            item = itemKind.newItem(None, self)
            item.Update(itemData, encoding)
            self.addValue('items', item)

class RSSItem(Item):
    def Update(self, data, encoding):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs, encoding)

        attrs = ['description', 'creator', 'link', 'category', 'date']
        SetAttributes(self, data, attrs, encoding)
