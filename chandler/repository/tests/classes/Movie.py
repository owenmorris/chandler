
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

    def kindChanged(self, op, item, attribute):

        self.monitorAttribute = attribute

    def onSetChange(self, op, item, name, other):

        #print op, item, name, other
        pass
