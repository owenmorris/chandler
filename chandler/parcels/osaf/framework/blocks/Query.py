
import application.Globals as Globals
from repository.item.Item import Item
import repository.item.Query as RepositoryQuery

class ItemCollection (Item):

    def __init__ (self, *arguments, **keywords):
        super (ItemCollection, self).__init__ (*arguments, **keywords)
        self.data = []
        self.results = []

    def __iter__(self):
        return self.iterateResults()

    def len(self):
        if self.resultsStale:
            self.refreshResults()
        return len (self.results)
    
    def refreshResults (self):
        if self.queryEnum == "ContainerSearch":
            assert False, "This code isn't written"

        elif self.queryEnum == "ListOfItems":
            self.results = self.data

        elif self.queryEnum == "Kind":
            self.results = []
            for item in self.iterateResults():
                self.results.append (item)
        self.resultsStale = False

    def iterateResults (self):
        if self.queryEnum == "ContainerSearch":
            assert False, "This code isn't written"

        elif self.queryEnum == "ListOfItems":
            return self.data

        elif self.queryEnum == "Kind":
            return RepositoryQuery.KindQuery().run(self.data)
        
        elif __debug__:
            assert False, "Bad QueryEnum"

    def __getitem__ (self, index):
        if self.resultsStale:
            self.refreshResults()
        return self.results [index]
 
    def index (self, item):
        if self.resultsStale:
            self.refreshResults()
        """
          Apparent repository bug: comment in the following instruction and watch it fail -- DJA
        return self.results.index (item)
        """
        index = 0
        for object in self.iterateResults():
            if object == item:
                return index
            index = index + 1
        assert (False)
 
    def onItemChanges (self, notification):
        if self.queryEnum == "ContainerSearch":
            assert False, "This code isn't written"

        elif self.queryEnum == "ListOfItems":
            assert False, "This code isn't written"

        elif self.queryEnum == "Kind":

            """
              This is a hack -- it's more complicated that just checking
            to see if an item is of a particular kind. You need to consider
            the separate cases of insert, delete and change. It's not worth
            solving this problem now since Ted's rewriting queries.
            """
            item = Globals.repository.find(notification.data['uuid'])
            # Repository limitation: list doesn't implement index
            if item:
                for kind in self.data:
                    if kind is item.itsKind:
                        self.resultsStale = True
                        for block in self.usedInBlocks:
                            try:
                                block.widget.scheduleUpdate = True
                            except AttributeError:
                                """
                                  We might not have a widget for every block that uses the
                                itemCollection, so ignore those that don't
                                """
                                pass


                            
        elif __debug__:
            assert False, "Bad QueryEnum"
