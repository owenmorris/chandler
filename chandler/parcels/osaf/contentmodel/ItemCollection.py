__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item.Item as Item
import application.Globals as Globals

"""
 * Need to dirty the collection when the rule attribute is changed
 * think about implementing the full Set API
"""

import logging
log = logging.getLogger("ItemCollection")
log.setLevel(logging.INFO)

class ItemCollection(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = Globals.repository.findPath('//userdata/contentitems')
        super(ItemCollection, self).__init__(name, parent, kind)

        # our result cache
        self.results = []

        self.__subscribe()

    def onItemLoad(self):
        log.debug("ItemCollection<%s>.onItemLoad:" % (self.itsUUID))
        self.__subscribe()
        # refresh the result cache
        self.__refresh()

    def __subscribe(self):
        # subscribe to query_changed notifications incase our query changes
        events = [Globals.repository.findPath('//parcels/osaf/framework/rule_changed')]
        Globals.notificationManager.Subscribe(events, self.itsUUID, self._queryChangedCallback)


    def onItemUnload(self):
        Globals.notificationManager.Unsubscribe(self.itsUUID)

    def _queryChangedCallback(self, notification):
        log.debug("ItemCollection<%s>._queryCallback:" % self.itsUUID)
        # if the query that changed is ours, we must refresh our result cache
        if self.rule:
            if notification.data['query'] == self.rule.itsUUID:
                log.debug("ItemCollection<%s>._queryCallback for %s" % (self.itsUUID, self.rule.itsUUID))
                self.__refresh()


    # python container functions
    def __nonzero__(self):
        return True

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        repository = self.getRepositoryView()
        results = self.results
        for uuid in results:
            yield repository[uuid]

    def __contains__(self, item):
        return item.itsUUID in self.results

    def __getitem__(self, index):
        return self.getRepositoryView()[self.results[index]]

    def __delitem__(self, index):
        self.__remove(self.results[index])

    def index(self, item):
        return self.results.index(item.itsUUID)

    def remove(self, item):
        return self.__remove(item.itsUUID)
            
    def __remove(self, uuid):
        if uuid not in self.results:
            raise ValueError, 'list.remove(x): x not in list'

        self.exclusions.append(uuid)

        # if the item we're removing was included manually then
        # remove it from that list
        if uuid in self.inclusions:
            self.inclusions.remove(uuid)

        # remove it from our result cache
        self.results.remove(uuid)
        self.__dirty()

    def add(self, item):
        uuid = item.itsUUID

        # don't add ourselves more than once
        if uuid in self.inclusions:
            return
        
        self.inclusions.append(uuid)

        # if the item we're including was already excluded, remove it
        # from that list
        # XXX this code could result in an item being included
        # both specifically and by a rule.  remove will do the right
        # thing though.
        if uuid in self.exclusions:
            self.exclusions.remove(uuid)

        if uuid not in self.results:
            self.results.append(uuid)
            self.__dirty()


    # APIs to deal with exclusions
    def iterExclusions(self):
        repository = self.getRepositoryView()
        results = self.exclusions
        for uuid in results:
            yield repository[uuid]

    def removeExclusion(self, item):
        self.exclusions.remove(item.itsUUID)
        # we can't know if removing an exclusion effects the result list
        # without rebuilding the whole thing...
        self.__refresh()


    # result cache building
    def __refresh(self):
        results = []

        inclusions = self.inclusions
        exclusions = self.exclusions
        rule = self.rule
        if not rule:
            rule = []

        log.debug("ItemCollection<%s>.__refresh: %s" % (self.itsUUID, self.rule))
        for item in rule:
            log.debug("ItemCollection<%s>.__refresh: i = %s" % (self.itsUUID, item))
            uuid = item.itsUUID
            if uuid not in exclusions:
                results.append(uuid)

        for uuid in inclusions:
            if uuid not in exclusions:
                if uuid not in results: # keep duplicates out
                    results.append(uuid)

        self.results = results
        log.debug("ItemCollection.__refresh: loaded %d items" % len(results))
        self.__dirty()

    def __dirty(self):
        # post collection_changed notification
        self.getRepositoryView().findPath('//parcels/osaf/contentmodel/collection_changed').Post( {'collection' : self.itsUUID} )



class NamedCollection(ItemCollection):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath('//parcels/osaf/contentmodel/NamedCollection')
        super(NamedCollection, self).__init__(name, parent, kind)

class AdHocCollection(ItemCollection):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath('//parcels/osaf/contentmodel/AdHocCollection')
        super(AdHocCollection, self).__init__(name, parent, kind)
        
class EphemeralCollection(ItemCollection):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath('//parcels/osaf/contentmodel/EphemeralCollection')
        super(EphemeralCollection, self).__init__(name, parent, kind)

