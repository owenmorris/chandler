__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import OSAF.framework.utils.indexer as indexer
import Queue
import re
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
        # XXX Ideally declIndex and declarations would be the same object
        self.__declIndex = indexer.getIndex('events')
        self.declarations = LockableDict()
        self.subscriptions = LockableDict()

    # Public Methods
    def PrepareSubscribers(self):
        """ Start up the Notification Manager """
        self.declarations.acquire()
        try:
            for item in self.__declIndex.items:
                self.declarations[item.getUUID()] = Declaration(item)
        finally:
            self.declarations.release()

    def Subscribe(self, name, clientID, callback = None, *args):
        # make a subscription object
        self.subscriptions.acquire()
        try:
            if self.subscriptions.has_key(clientID):
                raise AlreadySubscribed
        finally:
            self.subscriptions.release()
            
        self.declarations.acquire()
        try:
            if type(name) != types.ListType:
                name = [name]
            decls = []
            for n in name:
                decls.append(self.declarations[n.getUUID()])

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

    def Unsubscribe(self, name, clientID):
        # this function doesn't work correctly right now
        return
    
        self.declarations.acquire()
        try:
            if not self.declarations.has_key(name):
                raise NotDeclared, '%s %s' % (name, clientID)

            # eventually if the subscriber isn't subscribed to anything
            # we should remove it from self.subscribers as well
            try:
                del self.declarations[name].subscribers[clientID]
            except KeyError:
                # throw something here
                return

        finally:
            self.declarations.release()

    def PostNotification(self, notification):
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
    __slots__ = [ 'declarations', 'queue', 'callback', 'args' ]
    def __init__(self, declarations, callback, *args):
        super(Subscription, self).__init__()
        self.declarations = declarations
        self.callback = callback
        self.args = args
        if not callable(callback):
            self.queue = Queue.Queue()

    def post(self, notification):
        if callable(self.callback):
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
