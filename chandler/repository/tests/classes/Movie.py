
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

    def collectionChanged(self, op, item, name, other, *args):

        print op, self, name, other, args

    def itemChanged(self, op, item, name):

        print self, 'itemChanged', op, item, name


class Cartoon(Movie):
    pass
