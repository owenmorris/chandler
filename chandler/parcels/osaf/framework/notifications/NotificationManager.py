__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import Queue
import threading
import types

# Exceptions
class AlreadyDeclared(Exception):
    pass
class AlreadySubscribed(Exception):
    pass
class NotDeclared(Exception):
    pass
class NotSubscribed(Exception):
    pass

class NotificationManager(object):
    def __init__(self):
        super(NotificationManager, self).__init__()
        # XXX Ideally declarations would be a 'live' query
        self.declarations = LockableDict()
        self.subscriptions = LockableDict()

    # Public Methods
    def PrepareSubscribers(self):
        """ Start up the Notification Manager """
        self.declarations.acquire()
        try:
            from repository.item.Query import KindQuery
            eventKind = Globals.repository.find('//parcels/OSAF/framework/notifications/schema/Event')
            for item in KindQuery().run([eventKind]):
                self.declarations[item.getUUID()] = Declaration(item)
        finally:
            self.declarations.release()

    def Subscribe(self, events, clientID, callback = None, *args):
        # make a subscription object
        self.subscriptions.acquire()
        try:
            if self.subscriptions.has_key(clientID):
                raise AlreadySubscribed
        finally:
            self.subscriptions.release()
            
        self.declarations.acquire()
        try:
            decls = []
            for e in events:
                decls.append(self.declarations[e.getUUID()])

            #print decls

            # make a new subscription object
            sub = Subscription(decls, callback, *args)
            for decl in decls:
                # add the subscription to the declaration's list of subscribers
                decl.subscribers[clientID] = sub

            self.subscriptions.acquire()
            try:
                self.subscriptions[clientID] = sub
            finally:
                self.subscriptions.release()

            return clientID
        finally:
            self.declarations.release()

    def Unsubscribe(self, clientID):
        self.declarations.acquire()
        try:
            if not self.subscriptions.has_key(clientID):
                raise NotSubscribed, '%s' % (clientID)

            sub = self.subscriptions[clientID]
            for decl in sub.declarations:
                del decl.subscribers[clientID]

            self.subscriptions.acquire()
            try:
                del self.subscriptions[clientID]
            finally:
                self.subscriptions.release()

        finally:
            self.declarations.release()

    def PostNotification(self, notification, sender = None):
        # for now we don't care who posts......
        # future version should check notification for validity
        self.declarations.acquire()
        try:
            eventID = notification.event.getUUID()
            if not self.declarations.has_key(eventID):
                raise NotDeclared, '%s %s' % (eventID, clientID)

            decl = self.declarations[eventID]

            subscribers = decl.subscribers.values()
        finally:
            self.declarations.release()

        for sub in subscribers:
            sub.post(notification)

    def GetNextNotification(self, clientID):
        self.subscriptions.acquire()
        try:
            try:
                subscription = self.subscriptions[clientID]
            except KeyError:
                #raise NotSubscribed
                return None
        finally:
            self.subscriptions.release()

        try:
            return subscription.get(False)
        except Queue.Empty:
            # Queue.Empty: empty queue
            return None

    def WaitForNextNotification(self, clientID):
        self.subscriptions.acquire()
        try:
            try:
                subscription = self.subscriptions[clientID]
            except KeyError:
                raise NotSubscribed
        finally:
            self.subscriptions.release()

        return subscription.get(True)

    def CancelNotification(self, notificationID, clientID = 0):
        # we need a way to remove the notification from all the queues its in
        pass

class Declaration(object):
    __slots__ = [ 'subscribers', '__uuid' ]
    def __init__(self, event):
        self.subscribers = {}
        self.__uuid = event.getUUID()
    def __repr__(self):
        return '<Declaration> ' +  self.event.name
    def __getEvent(self):
        return Globals.repository[self.__uuid]
    event = property(__getEvent)

class Subscription(object):
    __slots__ = [ 'declarations', 'queue', 'callback', 'args', 'threadid' ]
    def __init__(self, declarations, callback, *args):
        super(Subscription, self).__init__()
        self.declarations = declarations
        self.callback = callback
        self.args = args
        self.threadid = id(threading.currentThread())
        if not callable(callback):
            self.queue = Queue.Queue()

    def post(self, notification):
        if callable(self.callback):
            if notification.threadid != None:
                if notification.threadid != id(threading.currentThread()):
                    print 'ignoring notification from', notification.threadid
                    return
            self.callback(notification, *self.args)
        else:
            self.queue.put(notification)

    def get(self, wait):
        if callable(self.callback):
            return None
        return self.queue.get(wait)


class LockableDict(dict):
    def __init__(self, *args, **kwds):
        super(LockableDict, self).__init__(*args, **kwds)
        self.__lock = threading.Lock()
    def acquire(self):
        self.__lock.acquire()
    def release(self):
        self.__lock.release()
    def locked(self):
        return self.__lock.locked()
