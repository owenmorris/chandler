__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.util.Path import Path
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

def SetAttributes(self, data, attributes, encoding=None):
    if type(attributes) == types.DictType:
        for attr, nattr in attributes.items():
            SetAttribute(self, data, attr, nattr=nattr, encoding=encoding)
    elif type(attributes) == types.ListType:
        for attr in attributes:
            SetAttribute(self, data, attr, encoding=encoding)


class RSSChannel(Item):
    def __getItemsParent(self):
        repository = self.getRepository()
        parent = repository.find('//userdata/contentitems')
        if parent:
            return parent
        itemKind = repository.find('//Schema/Core/Item')
        userdata = repository.find('//userdata')
        if not userdata:
            userdata = itemKind.newItem('userdata', repository)
        return itemKind.newItem('contentitems', userdata)

    def Update(self, data):
        # get the encoding
        encoding = data.get('encoding', 'latin_1')

        # set etag
        SetAttribute(self, data, 'etag')

        # set lastModified
        modified = data.get('modified')
        if modified:
            self.lastModified = mx.DateTime.mktime(modified)

        self._DoChannel(data['channel'], encoding)
        self._DoItems(data['items'], encoding)

    def _DoChannel(self, data, encoding):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs, encoding)

        attrs = ['link', 'description', 'copyright', 'creator', 'category', 'language']
        SetAttributes(self, data, attrs, encoding)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(date)

    def _DoItems(self, items, encoding):
        # make children
        itemKind = self.getRepository().find(RSSITEM_KIND_PATH)
        for itemData in items:
            #print 'new item'
            item = itemKind.newItem(None, self.__getItemsParent())
            item.Update(itemData, encoding)
            self.addValue('items', item)

class RSSItem(Item):
    def Update(self, data, encoding):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs, encoding)

        attrs = ['description', 'creator', 'link', 'category']
        SetAttributes(self, data, attrs, encoding)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(date)
