from repository.item.Item import Item
from application.Application import app
import mx.DateTime

BASE_PATH = '//Parcels/OSAF/examples/zaobao'
RSSITEM_KIND_PATH = BASE_PATH + '/RSSItem'

class RSSChannel(Item):
    def Update(self, url, data):
        # set the url
        self.setAttributeValue('rssURL', url)

        etag = data.get('etag', None)
        if etag:
            self.setAttributeValue('etag', etag)

        channel = data['channel']
        encoding = data.get('encoding', 'latin_1')

        # bunch of attributes
        for attr in ['creator', 'description', 'link', 'title', \
                     'category', 'language', 'encoding']:
            value = channel.get(attr, None)
            if value:
                self.setAttributeValue(attr, unicode(value, encoding))

        # set lastModified
        try:
            lastModified = mx.DateTime.DateTimeFrom(channel['date'])
        except KeyError:
            modifiedDate = data.get('modified')
            if modifiedDate and len(modifiedDate) > 5:
                #FIXME, need to store the whole date
                lastModified = apply(mx.DateTime.DateTime, modifiedDate[0:3])
            else:
                lastModified = None
        if lastModified:
            self.setAttributeValue('lastModified', lastModified)

        # make children
        itemKind = app.repository.find(RSSITEM_KIND_PATH)
        for itemData in data['items']:
            item = itemKind.newItem(None, self)
            item.Update(itemData, encoding)
            self.addValue('items', item)

        #items = self.getItemsFromParseData(parserData)
        #self.updateItems(items)
        #self.setAttributeValue('isUnread',len(items) > 0)

class RSSItem(Item):
    def Update(self, data, encoding):
        for attr in ['creator', 'description', 'link', 'title', \
                     'category']:
            value = data.get(attr, None)
            if value:
                self.setAttributeValue(attr, unicode(value, encoding))

        try:
            date = mx.DateTime.DateTimeFrom(data['date'])
            self.setAttributeValue('lastModified', date)
        except KeyError:
            self.removeAttributeValue('lastModified')
        
