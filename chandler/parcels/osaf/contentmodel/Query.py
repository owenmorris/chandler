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

        self.onItemLoad()

    def onItemLoad(self):
        events = [Globals.repository.findPath('//parcels/osaf/framework/commit_history')]
        Globals.notificationManager.Subscribe(events, self.itsUUID, self.onCommit)

        self.__refresh()

    def onItemUnload(self):
        Globals.notificationManager.Unsubscribe(self.itsUUID)

    def __iter__(self):
        results = self.results
        for item in results:
            yield item

    def onCommit(self, notification):
        # array of (uuid, reason, kwds) tuples
        changes = notification.data['changes']

        repository = self.getRepositoryView()
        for uuid,reason,kwds in changes:
            item = repository.findUUID(uuid)
            if item:
                # why doesn't 'if item in self.results' work here?
                for i in self.results:
                    if i == item:
                        self.__refresh()
                        return

                for kind in self.data:
                    if item.isItemOf(kind):
                        self.__refresh()
                        return

    def __refresh(self):
        self.results = []

        for item in RepositoryQuery.KindQuery().run(self.data):
            self.results.append(item)

        self.__dirty()

    def __dirty(self):
        # post query changed notification and return
        self.getRepositoryView().findPath('//parcels/osaf/framework/query_changed').Post( {'query' : self.itsUUID} )
