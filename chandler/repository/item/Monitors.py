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

class Monitors(Item):

    def _fillItem(self, *args):

        super(Monitors, self)._fillItem(*args)
        self.itsView.MONITORING = False

    def onItemLoad(self, view):

        self.setPinned()
        view.MONITORING = False
        view.setSingleton(view.MONITORS, self)

    def onItemImport(self, view):

        if view is not self.itsView:
            view.setSingleton(view.MONITORS, None)
            view.MONITORING = False

            self.setPinned()
            view = self.itsView
            view.MONITORING = False
            view.setSingleton(view.MONITORS, self)

    def onViewClear(self, view):

        view.setSingleton(view.MONITORS, None)

    def _collectionChanged(self, op, change, name, other):

        if change == 'collection' and name == 'monitors':
            if op == 'remove':
                self.cacheMonitors()
            elif op == 'add':
                if other is self:
                    raise TypeError, "Monitors dispatcher cannot have monitors"

        super(Monitors, self)._collectionChanged(op, change, name, other)
                            
    def cacheMonitors(self):

        view = self.itsView
        view._monitors = { 'set': {}, 'remove': {} }
        self.itsView.MONITORING = True

        for monitor in getattr(self, 'monitors', []):
            if not monitor.isDeleting():
                self._cacheMonitor(monitor)

    def _cacheMonitor(self, monitor):

        op = monitor.getAttributeValue('op', monitor._values)
        attribute = monitor.getAttributeValue('attribute', monitor._values)
        opDict = self.itsView._monitors[op]

        if attribute in opDict:
            opDict[attribute].append(monitor)
        else:
            opDict[attribute] = [monitor]

    @classmethod
    def attach(cls, item, method, op, attribute, *args, **kwds):

        view = item.itsView
        dispatcher = view.getSingleton(view.MONITORS)

        kind = dispatcher._kind.itsParent['Monitor']
        monitor = kind.newItem(None, dispatcher.itsParent['monitors'])

        monitor.item = item
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
                 _uuid=None, _noMonitors=False):
        super(Monitor, self).__init__(name, parent, kind, _uuid, True)

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None,
               _noMonitors=False):
        return super(Monitor, self).delete(recursive, deletePolicy, cloudAlias,
                                           True)
