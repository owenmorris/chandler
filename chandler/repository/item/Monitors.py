
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item


class Monitors(Item):

    def _fillItem(self, *args, **kwds):

        super(Monitors, self)._fillItem(*args, **kwds)
        self.monitoring = { 'set': {}, 'schema': {} }
        self.needsCaching = True

    def onItemLoad(self, view):

        self.setPinned()
        self.needsCaching = True
        Monitors.instances[view] = self

    def onItemImport(self, view):

        if view is not self.itsView:
            try:
                del Monitors.instances[self.itsView]
            except KeyError:
                pass

            self.setPinned()
            self.needsCaching = True
            Monitors.instances[view] = self

    def onViewClear(self, view):

        try:
            del Monitors.instances[view]
            self.needsCaching = True
        except KeyError:
            pass

    def _collectionChanged(self, op, name, other):

        if name == 'monitors':
            if op == 'remove':
                self.cacheMonitors()
            elif op == 'add':
                if other is self:
                    raise TypeError, "Monitors dispatcher cannot have monitors"

        super(Monitors, self)._collectionChanged(op, name, other)
                            
    def getInstance(cls, view):

        try:
            return cls.instances[view]
        except AttributeError:
            return view.findPath('//Schema/Core/items/Monitors')
        except KeyError:
            return view.findPath('//Schema/Core/items/Monitors')

    def cacheMonitors(self):

        self.monitoring = { 'set': {}, 'schema': {} }
        self.needsCaching = False

        for monitor in self.monitors:
            if not monitor.isDeleting():
                self._cacheMonitor(monitor)

    def _cacheMonitor(self, monitor):

        op = monitor.getAttributeValue('op', monitor._values)
        attribute = monitor.getAttributeValue('attribute', monitor._values)
        opDict = self.monitoring[op]

        if attribute in opDict:
            opDict[attribute].append(monitor)
        else:
            opDict[attribute] = [monitor]

    def invoke(cls, op, item, attribute, *args):

        #print op, item.itsPath, attribute, item.getAttributeValue(attribute)

        dispatcher = cls.getInstance(item.itsView)
        if dispatcher.needsCaching:
            dispatcher.cacheMonitors()

        try:
            monitors = dispatcher.monitoring[op][attribute]
        except KeyError:
            return
        except AttributeError:
            raise
            print 'no monitor singleton', op, item, attribute
            return

        for monitor in monitors:
            if monitor.isDeleting():
                continue

            monitorItem = monitor.getAttributeValue('item', monitor._references,
                                                    None, None)
            if monitorItem is None:
                continue

            monitorArgs = monitor.args
            if monitorArgs:
                if args:
                    _args = list(args)
                    _args.extend(monitorArgs)
                else:
                    _args = monitorArgs
            else:
                _args = args

            getattr(monitorItem, monitor.method)(op, item, attribute,
                                                 *_args, **monitor.kwds)

    def attach(cls, item, method, op, attribute, *args, **kwds):

        dispatcher = cls.getInstance(item.itsView)

        kind = dispatcher._kind.itsParent['Monitor']
        monitor = kind.newItem(None, dispatcher.itsParent['monitors'])

        monitor.item = item
        monitor.method = method
        monitor.op = op
        monitor.attribute = attribute
        monitor.args = args
        monitor.kwds = kwds
        monitor.dispatcher = dispatcher

        if dispatcher.needsCaching:
            dispatcher.cacheMonitors()
        else:
            dispatcher._cacheMonitor(monitor)

    def detach(cls, item, method, op, attribute, *args, **kwds):

        for monitor in item.monitors:
            if (monitor.method == method and monitor.op == op and
                monitor.attribute == attribute and
                monitor.args == args and monitor.kwds == kwds):
                monitor.delete()
                break


    invoke = classmethod(invoke)
    attach = classmethod(attach)
    detach = classmethod(detach)
    getInstance = classmethod(getInstance)

    instances = {}


class Monitor(Item):

    def __init__(self, name=None, parent=None, kind=None,
                 _uuid=None, _noMonitors=False):
        super(Monitor, self).__init__(name, parent, kind, _uuid, True)

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None,
               _noMonitors=False):
        return super(Monitor, self).delete(recursive, deletePolicy, cloudAlias,
                                           True)


#
# recursive import prevention
#

Item._monitorsClass = Monitors
