import application.Globals as Globals
import repository.item.Item as Item
import repository.query.Query as RepositoryQuery

import logging
log = logging.getLogger("ContentQuery")
log.setLevel(logging.INFO)

class Query(Item.Item):

    def __init__ (self, *args, **kwds):
        super(Query, self).__init__ (*args, **kwds)
        log.debug("ContentQuery<%s>.__init__: %s" % (self.itsUUID, self))
        self.__changed = False # transient
        self.__query = RepositoryQuery.Query(Globals.repository) # transient
        self.__query.subscribe()
        self.__subscribe()


    def onItemLoad(self):
        self.__subscribe()
        log.debug("ContentQuery<%s>.onItemLoad: %s" % (self.itsUUID, self))
        self.__refresh()

    def __subscribe(self):
        events = [Globals.repository.findPath('//parcels/osaf/framework/query_changed')]
        Globals.notificationManager.Subscribe(events, self.itsUUID, self.onQueryChange)


    def onItemUnload(self):
        Globals.notificationManager.Unsubscribe(self.itsUUID)

    def _fillItem(self, name, parent, kind, **kwds):
        """
        Override of Item._fillItem
        
        @@@ this is a workaround for the fact the onItemLoad processing is done in a
        single pass at the end, not as items are loaded.  this is for rehydration
        """
        super(Query, self)._fillItem(name, parent, kind, **kwds)
        # populate transients
        self.__changed = True # cause initial reload
        self.__query = RepositoryQuery.Query(Globals.repository)
        self.__query.subscribe()
        if self.hasAttributeValue('data'):
            self.__query.queryString = self.data
        
    def setAttributeValue(self, name, value=None, setAliases=False,
                          _attrDict=None, setDirty=True):
        """
        Override of Item.setAttributeValue
        
        @@@ any time the 'data' attribute is updated we need to set the changed flag
        """
        super(Query, self).setAttributeValue(name ,value, setAliases, _attrDict, setDirty)
        if name == 'data':
            log.debug("ContentQuery<%s>.setAttribute: setting 'data' to %s" % (self.itsUUID, value))
            self.__query.queryString = value
            self.__changed = True # @@@ should be able to do this but need some fixes in repo Query
            # so for now do refresh
#            self.__refresh()

    def __iter__(self):
        """
        Return a generator for the cached query results
        
        The cached results are refreshed if necessary
        """
        log.debug("ContentQuery<%s>.__iter__: %s" % (self.itsUUID, self.results))
        if self.__changed:
            self.__refresh()
        for i in self.results:
            yield i

    def onQueryChange(self, notification):
        """
        The notification callback handler for the repository level query's change notifications
        """
        log.debug("ContentQuery<%s>.onQueryChange: %s %s:%s" % (self.itsUUID, self.__query.queryString, notification.data['query'], notification.data['action']))
        self.__changed = True
        self.__dirty()

    def __refresh(self):
        """
        Refresh the cached query results by executing the repository query
        """
        if self.exactKind:
            self.__query.recursive = False
        self.__query.execute()
        #@@@ due to generator wackiness (bad interactions with persistent list), force the query generatro to give up the whole thing
        self.results = [ i for i in self.__query ]

        log.debug("ContentQuery<%s>.__refresh: results = %s" % (self.itsUUID, self.results))
        self.__changed = False
        self.__dirty()

    def __dirty(self):
        # post query changed notification and return
        log.debug("ContentQuery<%s>.__dirty:" % self.itsUUID)
        self.getRepositoryView().findPath('//parcels/osaf/framework/rule_changed').Post( {'query' : self.itsUUID} )
