
from repository.item.Item import Item


class Movie(Item):

    def compareFrench(self, other):

        if self.frenchTitle < other.frenchTitle:
            return -1
        elif self.frenchTitle > other.frenchTitle:
            return 1
        else:
            return 0

    def onItemCopy(self, view, original):

        print 'copied', self.title, 'from', original.itsUUID

    def onItemMerge(self, code, attribute, value):

        return self.getAttributeValue(attribute)

    def kindChanged(self, op, kind, item):

        self.monitorAttribute = 'kind'
        print self, 'kindChanged', op, self, kind, item

    def itemChanged(self, op, item, names):

        print self, 'itemChanged', op, item, names

    def onCollectionNotification(self, op, collection, name, other):

        print self, 'onCollectionNotification', op, collection, name, other


class Cartoon(Movie):
    pass
