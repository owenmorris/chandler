
import application.Globals as Globals
from repository.item.Item import Item
import repository.item.Query as RepositoryQuery

class Query (Item):

    def __init__ (self, *arguments, **keywords):
        super (Query, self).__init__ (*arguments, **keywords)
        self.data = []
        self.results = []

    def getResultSize(self):
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
            for item in self.getResultsIterator():
                self.results.append (item)
        self.resultsStale = False

    def getResultsIterator (self):
        if self.queryEnum == "ContainerSearch":
            assert False, "This code isn't written"

        elif self.queryEnum == "ListOfItems":
            return self.data

        elif self.queryEnum == "Kind":
            return RepositoryQuery.KindQuery().run(self.data)
        
        elif __debug__:
            assert False, "Bad QueryEnum"

    def indexResult (self, index):
        if self.resultsStale:
            self.refreshResults()
        return self.results [index]
 
    def onItemChanges(self, notification):
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
            for kind in self.data:
                if kind is item.kind:
                    for block in self.usedInBlocks:
                        self.resultsStale = True
                        block.update()

        elif __debug__:
            assert False, "Bad QueryEnum"
