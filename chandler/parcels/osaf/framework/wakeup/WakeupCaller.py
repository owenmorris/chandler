import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import repository.item.Query as Query
import application.Globals as Globals
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import logging as logging
import twisted.internet.error as error
import chandlerdb.util.UUID as UUID
import repository.item.Item as Item
import mx.DateTime as DateTime

"""
Notes:
   1. Could just have the class name as an argument with out having 
      to make it an item
"""
class WakeupCall(Item.Item):
    def receiveWakeupCall(self):
        pass

class WakeupCaller(TwistedRepositoryViewManager.RepositoryViewManager):
    MAX_POOL_SIZE = 15

    def __init__(self):
        """Create a unique view string"""
        super(WakeupCaller, self).__init__(Globals.repository, "WC_%s" % (str(UUID.UUID())))
        self.wakeupCallies = {}

    def startup(self):
        if __debug__:
            self.printCurrentView("startup")

        reactor.callFromThread(self.execInView, self.__startup)

    def __startup(self):
        if __debug__:
            self.printCurrentView("__startup")

        self.__populate()
        size = self.wakeupCallies.__len__()

        if size > self.MAX_POOL_SIZE:
            size = self.MAX_POOL_SIZE

        reactor.suggestThreadPoolSize(size)

        for item in self.wakeupCallies.values():
            if not item.enabled:
                continue

            if item.callOnStartup:
                reactor.callInThread(item.receiveWakeupCall)

            item.handle = reactor.callLater(item.delay.seconds, self.execInView, 
                                            self.__triggerEvent, item.itsUUID)

    def askForWakeupCall(self, item):
        #Do assert checking here
        if __debug__:
            self.printCurrentView("askForWakeupCall")

        reactor.callFromThread(self.execInView, self.__askForWakeupCall, item)

    def __askForWakeupCall(self, item):
        if not item.enabled:
            return

        self.wakeupCallies[item.itsUUID] = item

        if item.callOnStartup:
            reactor.callInThread(item.receiveWakeupCall)

        item.handle = reactor.callLater(item.delay.seconds, self.execInView,
                                        self.__triggerEvent, item.itsUUID)

    def cancelWakeupCall(self, item):
        #Do assert checking here
        if __debug__:
            self.printCurrentView("cancelWakeupCall")

        reactor.callFromThread(self.execInView, self.__cancelWakeupCall, item)

    def __cancelWakeupCall(self, item):
        item = self.wakeupCallies[item.itsUUID]

        if item is not None:
            if item.handle is not None:
               item.handle.cancel()

            del self.wakeupCallies[item.itsUUID]

    def __triggerEvent(self, uuid):
        if __debug__:
            self.printCurrentView("__triggerEvent")

        item = self.wakeupCallies[uuid]
        assert item is not None

        reactor.callInThread(item.receiveWakeupCall)

        if item.repeat:
            item.handle = reactor.callLater(item.delay.seconds, self.execInView,
                                            self.__triggerEvent, item.itsUUID)

        else:
            item.handle = None

    def shutdown(self):
        if __debug__:
            self.printCurrentView("shutdown")

        reactor.callFromThread(self.execInView, self.__shutdown)

    def __shutdown(self):
        if __debug__:
            self.printCurrentView("__shutdown")

        for item in self.wakeupCallies.values():
            if item.handle is not None:
                item.handle.cancel()

            del self.wakeupCallies[item.itsUUID]

    def __populate(self):
        wakeupKind = Globals.repository.findPath('//parcels/osaf/framework/wakeup/WakeupCall')
        for wakeup in Query.KindQuery().run([wakeupKind]):
            self.wakeupCallies[wakeup.itsUUID] = wakeup
