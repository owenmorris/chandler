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

class WakeupCallException(Exception):
    """Exception class thrown if errors occur in WakeupCaller"""

class WakeupCall(Item.Item):
    def receiveWakeupCall(self):
        raise NotImplementedError

class WakeupCaller(TwistedRepositoryViewManager.RepositoryViewManager):
    """
      This core Chandler Service is called on Chandler Startup by Application.py.
      The WakeupCaller loads all Items of kind WakeupCall (see osaf/framework/wakeup/parcel.xml for
      schema definition). Each WakeupCall items recieveWakupCall method will be called at the
      interval specified.
    """
    MAX_POOL_SIZE = 15

    def __init__(self):
        #Create a unique view string
        super(WakeupCaller, self).__init__(Globals.repository, "WC_%s" % (str(UUID.UUID())))
        self.wakeupCallies = {}

    def startup(self):
        """
          Loads all items of kind WakeupCall. Each WakeupCall will get
          its receiveWakupCall method executed at the interval it specifes.
        """
        reactor.callFromThread(self.execInView, self.__startup)

    def shutdown(self):
        """
          Shuts down the WakeupCaller and unregisters all WakeupCall Items
        """
        reactor.callFromThread(self.execInView, self.__shutdown)

    def refresh(self):
        """
           Reloads all WakeupCall items from the Repository. This allows
           runtime changes to WakeupCall items.
        """
        reactor.callFromThread(self.execInView, self.__refresh)

    def __startup(self, callOnStartup=True):
        self.__populate()
        size = self.wakeupCallies.__len__()

        if size > self.MAX_POOL_SIZE:
            size = self.MAX_POOL_SIZE

        reactor.suggestThreadPoolSize(size)

        for wakeupCall in self.wakeupCallies.values():
            if not wakeupCall.enabled:
                continue

            if callOnStartup and wakeupCall.callOnStartup:
                reactor.callInThread(wakeupCall.receiveWakeupCall)

            wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                                  self.__triggerEvent, wakeupCall.itsUUID)

    def __shutdown(self):
        for wakeupCall in self.wakeupCallies.values():
            if wakeupCall.handle is not None:
                wakeupCall.handle.cancel()

            del self.wakeupCallies[wakeupCall.itsUUID]

    def __refresh(self):
        self.__shutdown()
        self.view.refresh()

        # When reloading wakeupCalls indicate to ignore callOnStartup flag
        # since this is a refresh
        self.__startup(False)

    def __triggerEvent(self, uuid):
        wakeupCall = self.wakeupCallies[uuid]
        assert wakeupCall is not None

        reactor.callInThread(wakeupCall.receiveWakeupCall)

        if wakeupCall.repeat:
            wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                                  self.__triggerEvent, wakeupCall.itsUUID)

        else:
            wakeupCall.handle = None

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
