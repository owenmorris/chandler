import time
import application.Globals as Globals
from repository.item.Item import Item
import repository.item.Query as RepositoryQuery
from repository.util.UUID import UUID
import wx

class Query (Item):

    def __init__ (self, *args, **kwds):
        super(Query, self).__init__ (*args, **kwds)
        self.data = []
        self.results = []

        self.onItemLoad()

    def onItemLoad(self):
        events = [Globals.repository.findPath('//parcels/osaf/framework/commit_history')]
        Globals.notificationManager.Subscribe(events, id(self), self.onCommit)

    def onItemUnload(self):
        Globals.notificationManager.Unsubscribe(id(self))

    def __iter__(self):
        return self.iterateResults()

    def __nonzero__(self):
        return True
    
    def __len__(self):
        if self.resultsStale:
            self.refreshResults()
        return len (self.results)
    
    def refreshResults (self):
        if self.queryEnum == "Kind":
            self.results = []
            for item in self.iterateResults():
                self.results.append (item)
        self.resultsStale = False

    def iterateResults (self):
        if self.queryEnum == "Kind":
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

    def onCommit(self, notification):
        if self.queryEnum != "Kind":
            assert False, "Bad QueryEnum"
            return

        # array of (uuid, reason, kwds) tuples
        changes = notification.data['changes']

        repository = self.getRepositoryView()
        for uuid,reason,kwds in changes:
            item = repository.findUUID(uuid)
            if item:
                for kind in self.data:
                    if item.itsKind == kind:
                        # just mark the whole thing dirty, post query changed notification and return
                        self.resultsStale = True
                        repository.findPath('//parcels/osaf/framework/query_changed').Post( {'query' : self.itsUUID} )
                        return
