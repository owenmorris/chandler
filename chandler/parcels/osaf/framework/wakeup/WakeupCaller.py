import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import osaf.framework.twisted.TwistedThreadPool as TwistedThreadPool
import repository.item.Query as Query
import repository.util.ClassLoader as ClassLoader
import twisted.internet.reactor as reactor
import logging as logging
import chandlerdb.util.uuid as UUID
import WakeupCallerParcel

class WakeupCall(object):
    def receiveWakeupCall(self, wakeupCallItem):
        """
           This method will be called by the C{WakeupCaller}.
           The method runs in a thread from a pool and
           has its own C{RepositoryView}.

           @param wakeupCallItem: The WakeupCall item that is associated with this class
           @type  wakeupCallItem: WakeupCall kind

        """
        raise NotImplementedError, "Please implement a sub-class of WakeupCall and register it with your parcel"

class WakeupCaller(TwistedRepositoryViewManager.RepositoryViewManager):
    """
      This core Chandler Service is called on Chandler Startup by Application.py.
      The WakeupCaller loads all Items of kind WakeupCall (see osaf/framework/wakeup/parcel.xml for
      schema definition). Each WakeupCall items recieveWakupCall method will be called at the
      interval specified.
    """

    def __init__(self, repository):
        #Create a unique view string
        super(WakeupCaller, self).__init__(repository, "WC_%s" % (str(UUID.UUID())))
        self.wakeupCallies = {}
        self.threadPool = TwistedThreadPool.RepositoryThreadPool()
        self.wakeupCallKindID = None

    def startup(self):
        """
          Loads all items of kind WakeupCall. Each WakeupCall will get
          its receiveWakupCall method executed at the interval it specifes.
        """
        self.threadPool.start()
        reactor.callFromThread(self.execInView, self.__startup)

    def shutdown(self):
        """
          Shuts down the WakeupCaller and unregisters all WakeupCall Items
        """
        reactor.callFromThread(self.execInView, self.__shutdown)
        self.threadPool.stop()

    def refresh(self):
        """
           Reloads all WakeupCall items from the Repository. This allows
           runtime changes to WakeupCall items.
        """
        reactor.callFromThread(self.execInView, self.__refresh)

    def __startup(self, callOnStartup=True):
        self.__populate()

        for wakeupCall in self.wakeupCallies.values():
            if not wakeupCall.enabled:
                continue

            if callOnStartup and wakeupCall.callOnStartup:
                self.threadPool.callInThread(self.__proxy,
                                             wakeupCall.callback.receiveWakeupCall,
                                             wakeupCall.itsUUID)

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

        """ When reloading wakeupCalls indicate to ignore callOnStartup flag
            since this is a refresh"""
        self.__startup(False)

    def __proxy(self, wakeupCallCallback, UUID):
        #XXX: At some point may wanna look at caching and returning 
        #     one view for a WakeupCall item so that each time it '
        #     is called it has the same view to work with.
        #     At this point it is not needed but may be useful in the 
        #     future
        prevView = self.repository.setCurrentView(self.repository.view)
        try:
            wakeupCall = self.getCurrentView().findUUID(UUID)
            wakeupCallCallback(wakeupCall)
        finally:
            self.repository.setCurrentView(prevView)

    def __triggerEvent(self, uuid):
        wakeupCall = self.wakeupCallies[uuid]

        self.threadPool.callInThread(self.__proxy,
                                     wakeupCall.callback.receiveWakeupCall,
                                     wakeupCall.itsUUID)

        if wakeupCall.repeat:
            wakeupCall.handle = reactor.callLater(wakeupCall.delay.seconds, self.execInView,
                                                  self.__triggerEvent, wakeupCall.itsUUID)

        else:
            wakeupCall.handle = None

    def __populate(self):
        view = self.getCurrentView()
        for wakeupCall in WakeupCallerParcel.WakeupCall.iterItems(view):
            if not self.__isValid(wakeupCall):
                error  = "An invalid WakeupCall was found with UUID: %s." % wakeupCall.itsUUID
                error += "The WakeupCall must specify a WakeupCall.py sub-class ", \
                         "and have a delay value greater than 0"

                self.log.error(error)

            else:
                self.wakeupCallies[wakeupCall.itsUUID] = wakeupCall

    def __isValid(self, wakeupCall):
        if wakeupCall is None or wakeupCall.delay.seconds <= 0:
            return False

        callback = wakeupCall.wakeupCallClass()

        if not isinstance(callback, WakeupCall):
            return False

        wakeupCall.callback = callback
        wakeupCall.handle = None

        return True
