
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item


class Monitors(Item):

    def onItemLoad(self, view):

        if not view.isRefCounted():
            self.setPinned()
        Monitors.instances[view] = self

        if 'monitoring' not in self._values:
            self.setAttributeValue('monitoring', { 'set': {} },
                                   _attrDict=self._values)

    def getInstance(cls, view):

        try:
            return cls.instances[view]
        except AttributeError:
            return view.findPath('//Schema/Core/Items/Monitors')
        except KeyError:
            return view.findPath('//Schema/Core/Items/Monitors')

    def invoke(cls, op, item, attribute):

        #print op, item.itsPath, attribute, item.getAttributeValue(attribute)

        try:
            monitors = cls.getInstance(item.itsView).monitoring[op][attribute]
        except KeyError:
            return

        for monitorItem, method, args, kwds in monitors:
            getattr(monitorItem, method)(op, item, attribute, *args, **kwds)

    def attach(cls, item, method, op, attribute, *args, **kwds):

        instance = cls.getInstance(item.itsView)
        monitor = [item, method, args, kwds]
        try:
            instance.monitoring[op][attribute].append(monitor)
        except KeyError:
            instance.monitoring[op][attribute] = [monitor]

    def detach(cls, item, method, op, attribute, *args, **kwds):

        instance = cls.getInstance(item.itsView)
        monitor = [item, method, args, kwds]

        instance.monitoring[op][attribute].remove(monitor)


    invoke = classmethod(invoke)
    attach = classmethod(attach)
    detach = classmethod(detach)
    getInstance = classmethod(getInstance)

    instances = {}


class Monitor(Item):
    pass
