#   Copyright (c) 2004-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from repository.item.Item import Item, override
from chandlerdb.util.c import Nil, Default

class Monitors(Item):

    @override(Item)
    def _fillItem(self, *args):

        super(Monitors, self)._fillItem(*args)
        self.itsView.MONITORING = False

    def onItemLoad(self, view):

        view.MONITORING = False
        view.setSingleton(view.MONITORS, self)

    def onViewClear(self, view):

        view.setSingleton(view.MONITORS, None)

    @override(Item)
    def _collectionChanged(self, op, change, name, other):

        if change == 'collection' and name == 'monitors':
            if op == 'remove':
                self._uncacheMonitor(other)
            elif op == 'add':
                if other is self:
                    raise TypeError, "Monitors dispatcher cannot have monitors"

        super(Monitors, self)._collectionChanged(op, change, name, other)
                            
    def cacheMonitors(self):

        view = self.itsView
        view._monitors = { 'init': {}, 'set': {}, 'remove': {} }
        self.itsView.MONITORING = True

        for monitor in getattr(self, 'monitors', []):
            if not monitor.isDeferringOrDeleting():
                self._cacheMonitor(monitor)

    def _cacheMonitor(self, monitor):

        op = monitor.getAttributeValue('op', monitor._values)
        attribute = monitor.getAttributeValue('attribute', monitor._values)
        opDict = self.itsView._monitors[op]

        if attribute in opDict:
            opDict[attribute].append(monitor)
        else:
            opDict[attribute] = [monitor]

    def _uncacheMonitor(self, monitorId):

        view = self.itsView
        monitor = view.findUUID(monitorId, False)

        def _uncacheMonitor(monitors):
            count = 0
            for monitor in monitors:
                if monitor.itsUUID == monitorId:
                    break
                count += 1
            else:
                return False
            del monitors[count]
            return True

        op = getattr(monitor, 'op', None)
        if op is not None:
            opDict = view._monitors[op]
            attribute = getattr(monitor, 'attribute', None)
            if attribute is not None:
                _uncacheMonitor(opDict.get(attribute, ()))
                return
            else:
                for attrList in opDict.itervalues():
                    if _uncacheMonitor(attrList):
                        return
        else:
            for opDict in self.itsView._monitors.itervalues():
                for attrList in opDict.itervalues():
                    if _uncacheMonitor(attrList):
                        return

    @classmethod
    def _attach(cls, monitorClass, item, method, op, attribute, *args, **kwds):

        view = item.itsView
        dispatcher = view.getSingleton(view.MONITORS)

        kind = dispatcher._kind.itsParent['Monitor']
        monitor = kind.newItem(None, dispatcher.itsParent['monitors'],
                               monitorClass)

        monitor.item = item
        if method is not None:
            monitor.method = method
        monitor.op = op
        monitor.attribute = attribute
        monitor.args = args
        monitor.kwds = kwds
        monitor.dispatcher = dispatcher

        if not view.MONITORING:
            dispatcher.cacheMonitors()
        else:
            dispatcher._cacheMonitor(monitor)

        return monitor

    @classmethod
    def attach(cls, item, method, op, attribute, *args, **kwds):

        return cls._attach(None, item, method, op, attribute, *args, **kwds)

    @classmethod
    def attachIndexMonitor(cls, item, op, attribute, *args):

        monitor = cls._attach(IndexMonitor, item, None, op, attribute, *args)
        monitor._status |= Item.SYSMONITOR | Item.IDXMONITOR

        return monitor

    @classmethod
    def attachFilterMonitor(cls, item, op, attribute, *args):

        monitor = cls._attach(FilterMonitor, item, None, op, attribute, *args)
        monitor._status |= Item.SYSMONITOR

        return monitor

    @classmethod
    def detach(cls, item, method, op, attribute, *args, **kwds):

        for monitor in item.monitors:
            if (monitor.method == method and monitor.op == op and
                monitor.attribute == attribute and
                monitor.args == args and monitor.kwds == kwds):
                monitor.delete()
                break

    @classmethod
    def detachFilterMonitor(cls, item, op, attribute, *args):

        for monitor in item.monitors:
            if (isinstance(monitor, FilterMonitor) and monitor.op == op and
                monitor.attribute == attribute and
                monitor.args == args):
                monitor.delete()
                break

    instances = {}


class Monitor(Item):

    def __init__(self, name=None, parent=None, kind=None,
                 _uuid=None, _noFireChanges=False):
        super(Monitor, self).__init__(name, parent, kind, _uuid, True)

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None,
               _noFireChanges=False):
        return super(Monitor, self).delete(recursive, deletePolicy, cloudAlias,
                                           True)

    def __call__(self, *args):

        view = self.itsView
        method = getattr(self.item, self.method)
        _args = self.args
        _kwds = self.kwds

        if _args or _kwds:
            method(*(args + _args), **_kwds)
        else:
            method(*args)

    def getItemIndex(self):
        return None, None, None


class IndexMonitor(Monitor):

    def getItemIndex(self):

        collectionName, indexName = self.args
        return self.item.itsUUID, collectionName, indexName

    def __call__(self, op, item, attribute):

        view = self.itsView

        collectionName, indexName = self.args
        collection = getattr(self.item, collectionName, None)

        if collection is not None:
            hook = getattr(type(self.item), 'onCollectionReindex', None)
            if callable(hook):
                keys = hook(self.item, view, item, attribute,
                            collectionName, indexName)
            else:
                keys = None

            if view.isReindexingDeferred():
                deferredKeys = getattr(self, 'deferredKeys', None)
                if deferredKeys is None:
                    self.setPinned(True)
                    self.deferredKeys = deferredKeys = set()
                    index = collection.getIndex(indexName)
                    index.validateIndex(False)
                if item in collection:
                    deferredKeys.add(item.itsUUID)
                if keys:
                    deferredKeys.update(keys)
                view._deferIndexMonitor(self)

            elif item in collection:
                if keys:
                    keys.append(item.itsUUID)
                    collection.getIndex(indexName).moveKeys(keys)
                else:
                    collection.getIndex(indexName).moveKey(item.itsUUID)
                collection._setDirty(True)

            elif keys:
                collection.getIndex(indexName).moveKeys(keys)
                collection._setDirty(True)

    def reindex(self):

        deferredKeys = getattr(self, 'deferredKeys', None)
        if deferredKeys is not None:
            self.setPinned(False)
            del self.deferredKeys
            collectionName, indexName = self.args
            collection = getattr(self.item, collectionName, None)
            if collection is not None:
                index = collection.getIndex(indexName)
                index.validateIndex(True)
                if len(deferredKeys) == 1:
                    index.moveKey(deferredKeys.pop())
                else:
                    index.moveKeys(deferredKeys)
                collection._setDirty(True)


class FilterMonitor(Monitor):

    def __call__(self, op, item, attribute):

        if not (self.item._isNoDirty() or item.isDeleting()):
            view = self.itsView

            collectionName, = self.args
            collection = getattr(self.item, collectionName, None)

            if collection is not None:
                collection.itemChanged(item.itsUUID, attribute)

                hook = getattr(type(self.item), 'onFilteredItemChange', None)
                if callable(hook):
                    keys = hook(self.item, view, item, attribute,
                                collectionName)
                    if keys:
                        for key in keys:
                            collection.itemChanged(key, attribute)
