
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item


class Monitors(Item):

    def onItemLoad(self, view):

        self.setPinned()
        Monitors.instances[view] = self

    def onItemImport(self, view):

        if view is not self.itsView:
            try:
                del Monitors.instances[self.itsView]
            except KeyError:
                pass
            self.setPinned()
            Monitors.instances[view] = self

    def onViewClose(self, view):

        try:
            del Monitors.instances[view]
        except KeyError:
            pass

    def getInstance(cls, view):

        try:
            return cls.instances[view]
        except AttributeError:
            return view.findPath('//Schema/Core/Items/Monitors')
        except KeyError:
            return view.findPath('//Schema/Core/Items/Monitors')

    def invoke(cls, op, item, attribute, *args):

        #print op, item.itsPath, attribute, item.getAttributeValue(attribute)

        try:
            monitors = cls.getInstance(item.itsView).monitoring[op][attribute]
        except KeyError:
            return
        except AttributeError:
            print 'no monitor singleton', op, item, attribute
            return

        for monitorItem, method, monitorArgs, kwds in monitors:
            if monitorItem is None:
                continue
            if monitorArgs:
                if args:
                    _args = list(args)
                    _args.extend(monitorArgs)
                else:
                    _args = monitorArgs
            else:
                _args = args
            getattr(monitorItem, method)(op, item, attribute, *_args, **kwds)

    def attach(cls, item, method, op, attribute, *args, **kwds):

        instance = cls.getInstance(item.itsView)
        monitor = [item, method, args, kwds]
        try:
            instance.monitoring[op][attribute].append(monitor)
        except KeyError, e:
            if e.args[0] == op:
                instance.monitoring[op] = {}
            instance.monitoring[op][attribute] = [monitor]

    def detach(cls, item, method, op, attribute, *args, **kwds):

        instance = cls.getInstance(item.itsView)
        monitor = (item, method, args, kwds)

        instance.monitoring[op][attribute].remove(monitor)


    invoke = classmethod(invoke)
    attach = classmethod(attach)
    detach = classmethod(detach)
    getInstance = classmethod(getInstance)

    instances = {}


class Monitor(Item):
    pass


#
# recursive import prevention
#

Item._monitorsClass = Monitors
