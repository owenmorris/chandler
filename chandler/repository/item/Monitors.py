#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


from repository.item.Item import Item
from chandlerdb.util.c import Nil, Default

class Monitors(Item):

    def _fillItem(self, *args):

        super(Monitors, self)._fillItem(*args)
        self.itsView.MONITORING = False

    def onItemLoad(self, view):

        view.MONITORING = False
        view.setSingleton(view.MONITORS, self)

    def onViewClear(self, view):

        view.setSingleton(view.MONITORS, None)

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
    def attachIndexMonitor(cls, item, op, attribute, *args, **kwds):

        monitor = cls._attach(IndexMonitor, item, None, op, attribute,
                              *args, **kwds)
        monitor._status |= Item.SYSMONITOR | Item.IDXMONITOR

        return monitor

    @classmethod
    def detach(cls, item, method, op, attribute, *args, **kwds):

        for monitor in item.monitors:
            if (monitor.method == method and monitor.op == op and
                monitor.attribute == attribute and
                monitor.args == args and monitor.kwds == kwds):
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
            if view._isRecording():
                view._notifyChange(method, *(args + _args), **_kwds)
            else:
                method(*(args + _args), **_kwds)
        else:
            if view._isRecording():
                view._notifyChange(method, *args)
            else:
                method(*args)

    def getItemIndex(self):
        return None, None, None


class IndexMonitor(Item):

    def getItemIndex(self):

        attribute, indexName = self.args
        return self.item.itsUUID, attribute, indexName

    def __call__(self, op, item, attribute):

        view = self.itsView

        if view._isRecording():
            view._notifyChange(self, op, item, attribute)

        else:
            attribute, indexName = self.args
            collection = getattr(self.item, attribute, None)

            if collection is not None:
                hook = getattr(type(self.item), 'onCollectionReindex', None)
                if callable(hook):
                    keys = hook(self.item, view, item, attribute, *self.args)
                else:
                    keys = None

                if view.isReindexingDeferred():
                    _keys = getattr(self, '_keys', None)
                    if _keys is None:
                        self.setPinned(True)
                        self._keys = _keys = set()
                        index = collection.getIndex(indexName)
                        index.validateIndex(False)
                    if item in collection:
                        _keys.add(item.itsUUID)
                    if keys:
                        _keys.update(keys)

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

        _keys = getattr(self, '_keys', None)
        if _keys is not None:
            self.setPinned(False)
            del self._keys
            attribute, indexName = self.args
            collection = getattr(self.item, attribute, None)
            if collection is not None:
                index = collection.getIndex(indexName)
                index.validateIndex(True)
                index.moveKeys(_keys)
                collection._setDirty(True)
