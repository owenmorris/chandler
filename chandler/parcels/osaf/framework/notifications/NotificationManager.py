"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import application.Globals as Globals
import Queue
import threading
import types

# Exceptions
class AlreadySubscribed(Exception):
    """ Raised when you try to subscribe with a clientID already subscribed """
    pass
class NotSubscribed(Exception):
    """ Raised when you try to unsubscribe to a clientID not subscribed """
    pass

class NotificationManager(object):
    """
    The Notification Manager is an object that maintains information
    about notifications and events.  Parcels can declare
    L{events<osaf.framework.notifications.schema.Event.Event>}. The
    Notification Manager provides a way for clients to post notifications
    when they occur, and to subscribe to them in order to be notified as
    necessary.

    Many of the notification manager calls take a 'clientID', which is a
    unique ID used to identify a caller.

    Event declarations are persistent while subscriptions are not.
    """
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
            eventKind = Globals.repository.findPath('//parcels/osaf/framework/notifications/schema/Event')
            if eventKind is not None:
                for item in KindQuery().run([eventKind]):
                    if not self.declarations.has_key(item.itsUUID):
                        self.declarations[item.itsUUID] = Declaration(item)
        finally:
            self.declarations.release()

    def AddEvent(self, item):
        self.declarations.acquire()
        try:
            self.declarations[item.itsUUID] = Declaration(item)
        finally:
            self.declarations.release()

    def Subscribe(self, events, clientID, callback):
        """
        Subscribe a callback to a list of events

        @param events: events you wish to subscribe to
        @type events: C{list} of L{Event<osaf.framework.notifications.schema.Event.Event>} items

        @param clientID: The 'name' of this subscription.  Used to unsubscribe.
        @type clientID: L{UUID}

        @param callback: Function to call when an event that matches is posted
        @type callback: callable function

        @raise AlreadySubscribed: When you have already subscribed with the same clientID
        """

        # make a subscription object
        self.subscriptions.acquire()
        try:
            if self.subscriptions.has_key(clientID):
                raise AlreadySubscribed, 'client ID %d on events %s is already subscribed' % (clientID, events)
        finally:
            self.subscriptions.release()
            
        self.declarations.acquire()
        try:
            decls = []
            for event in events:
                eventUUID = event.itsUUID
                try:
                    declaration = self.declarations[eventUUID]
                except KeyError:
                    declaration = Declaration(event)
                    self.declarations[eventUUID] = declaration

                decls.append(declaration)

            #print decls

            # make a new subscription object
            sub = Subscription(decls, callback)
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
        """
        Unsubscribe

        @param clientID: The clientID you used to subscribe
        @type clientID: L{UUID}

        @raise NotSubscribed: When you try to unsubscribe to something not
            subscribed
        """

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

    def PostNotification(self, notification):
        """
        Get the next notification in the queue or None if there are no pending events

        @param notification: The notification you wish to send
        @type notification: L{Notification<osaf.framework.notifications.Notification.Notification>}
        """
        # for now we don't care who posts......
        # future version should check notification for validity
        self.declarations.acquire()
        try:
            eventID = notification.event.itsUUID

            decl = self.declarations[eventID]

            subscribers = decl.subscribers.values()
        finally:
            self.declarations.release()

        for sub in subscribers:
            sub.post(notification)

class Declaration(object):
    """ Internal class used by the notification manager """
    __slots__ = [ 'subscribers', '__uuid' ]
    def __init__(self, event):
        self.subscribers = {}
        self.__uuid = event.itsUUID
    def __repr__(self):
        return '<Declaration> ' +  self.event.name
    def __getEvent(self):
        return Globals.repository[self.__uuid]
    event = property(__getEvent)

class Subscription(object):
    """ Internal class used by the notification manager """
    __slots__ = [ 'declarations', 'callback', 'threadid' ]
    def __init__(self, declarations, callback):
        super(Subscription, self).__init__()
        self.declarations = declarations
        self.callback = callback
        self.threadid = id(threading.currentThread())

    def post(self, notification):
        if notification.threadid != None:
            if notification.threadid != self.threadid:
                return
        self.callback(notification)

class LockableDict(dict):
    """ Lockable dictionary """
    def __init__(self, *args, **kwds):
        super(LockableDict, self).__init__(*args, **kwds)
        self.__lock = threading.Lock()
    def acquire(self):
        """ @see: C{threading.Lock::acquire()} """
        self.__lock.acquire()
    def release(self):
        """ @see: C{threading.Lock::release()} """
        self.__lock.release()
    def locked(self):
        """
        @see: C{threading.Lock::locked()}
        @return: L{bool}
        """
        return self.__lock.locked()
