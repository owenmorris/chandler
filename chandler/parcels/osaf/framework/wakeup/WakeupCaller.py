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
import repository.item.ItemError as ItemError

"""
Notes:
   2. Add in enabled check each time

Error Checking:
1. Test that add and remove work ok
"""

class WakeupCallException(Exception):
    """Exception class thrown if errors occur in WakeupCaller"""

class WakeupCall(Item.Item):
    def receiveWakeupCall(self):
        raise NotImplementedError

class WakeupCaller(TwistedRepositoryViewManager.RepositoryViewManager):
    MAX_POOL_SIZE = 15

    def __init__(self):
        """Create a unique view string"""
        super(WakeupCaller, self).__init__(Globals.repository, "WC_%s" % (str(UUID.UUID())))
        self.wakeupCallies = {}

    def startup(self):
        reactor.callFromThread(self.execInView, self.__startup)

    def shutdown(self):
        reactor.callFromThread(self.execInView, self.__shutdown)

    def askForWakeupCall(self, wakeupCall):
        if __debug__:
            self.printCurrentView("askForWakeupCall")

        if not isinstance(wakeupCall, WakeupCall) or not self.__isValid(wakeupCall):
            raise WakeupCallException("Item must be of type WakeupCall with a delay greater than 0 and an Item Class")

        reactor.callFromThread(self.execInView, self.__askForWakeupCall, wakeupCall)

    def cancelWakeupCall(self, wakeupCall):
        if __debug__:
            self.printCurrentView("cancelWakeupCall")

        if not isinstance(wakeupCall, WakeupCall) or self.wakeupCallies[wakeupCall.itsUUID] is None:
            raise WakeupCallException("Item must be of type WakeupCall and already registered with the WakeupCaller")

        reactor.callFromThread(self.execInView, self.__cancelWakeupCall, wakeupCall)

    def __startup(self):
        self.__populate()
        size = self.wakeupCallies.__len__()

        if size > self.MAX_POOL_SIZE:
            size = self.MAX_POOL_SIZE

        reactor.suggestThreadPoolSize(size)

        for wakeupCall in self.wakeupCallies.values():
            if not wakeupCall.enabled:
                continue

            if wakeupCall.callOnStartup:
                reactor.callInThread(wakeupCall.receiveWakeupCall)

            wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                                  self.__triggerEvent, wakeupCall.itsUUID)

    def __askForWakeupCall(self, wakeupCall):
        if not wakeupCall.enabled:
            return

        self.wakeupCallies[wakeupCall.itsUUID] = wakeupCall

        if wakeupCall.callOnStartup:
            reactor.callInThread(wakeupCall.receiveWakeupCall)

        wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                              self.__triggerEvent, wakeupCall.itsUUID)


    def __cancelWakeupCall(self, wakeupCall):
        if wakeupCall.handle is not None:
           wakeupCall.handle.cancel()

        del self.wakeupCallies[wakeupCall.itsUUID]

    def __triggerEvent(self, uuid):
        wakeupCall = self.wakeupCallies[uuid]
        assert wakeupCall is not None

        reactor.callInThread(wakeupCall.receiveWakeupCall)

        if wakeupCall.repeat:
            wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                                  self.__triggerEvent, wakeupCall.itsUUID)

        else:
            wakeupCall.handle = None

    def __shutdown(self):
        for wakeupCall in self.wakeupCallies.values():
            if wakeupCall.handle is not None:
                wakeupCall.handle.cancel()

            del self.wakeupCallies[wakeupCall.itsUUID]

    def __populate(self):
        wakeupCallKind = Globals.repository.findPath('//parcels/osaf/framework/wakeup/WakeupCall')

        for wakeupCall in Query.KindQuery().run([wakeupCallKind]):
            if not self.__isValid(wakeupCall):
                error  = "An invalid WakeupCall was found with UUID: %s." % wakeupCall.itsUUID
                error += "The WakeupCall must specify and Item Class and have a delay value greater than 0"

                self.log.error(error)

            else:
                self.wakeupCallies[wakeupCall.itsUUID] = wakeupCall

    def __isValid(self, wakeupCall):
        if wakeupCall is None or wakeupCall.delay.seconds <= 0:
            return False

        try:
            wakeupCall.receiveWakeupCall

        except ItemError.NoSuchAttributeError:
            return False

        else:
            return True
