__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import OSAF.framework.utils.indexer as indexer
import Queue
import re
import threading

# Exceptions
class AlreadyDeclared(Exception):
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
        self.subscribers = LockableDict()

    # Public Methods
    def PrepareSubscribers(self):
        """ Start up the Notification Manager """
        self.declarations.acquire()
        try:
            for item in self.__declIndex.items:
                self.declarations[item.name] = DeclarationFromEvent(item)
        finally:
            self.declarations.release()

    def FindNotifications(self, wildcard):
        results = []
        regex = re.compile(wildcard,re.IGNORECASE)

        for name in self.declarations.keys():
               matchObject = regularExpression.match(declaration)
               if matchObject != None:
                  results.append(matchObject.group())

        return results

    def Subscribe(self, name, clientID, source = None):
        self.declarations.acquire()
        try:
            if not self.declarations.has_key(name):
                #raise NotDeclared, '%s %s' % (name, clientID)
                return

            self.subscribers.acquire()
            try:
                try:
                    subscriber = self.subscribers[clientID]
                except KeyError:
                    subscriber = Subscriber(clientID, source)
                    self.subscribers[clientID] = subscriber
            finally:
                self.subscribers.release()

            self.declarations[name].subscribers[clientID] = subscriber
        finally:
            self.declarations.release()

    def Unsubscribe(self, name, clientID):
        self.declarations.acquire()
        try:
            if not self.declarations.has_key(name):
                #raise NotDeclared, '%s %s' % (name, clientID)
                return

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
            name = notification.GetName()
            if not self.declarations.has_key(name):
                raise NotDeclared, '%s %s' % (name, clientID)

            subscribers = self.declarations[name].subscribers.values()
            for sub in subscribers:
                sub.queue.put(notification)
        finally:
            self.declarations.release()

    def GetNextNotification(self, clientID):
        self.subscribers.acquire()
        try:
            try:
                return self.subscribers[clientID].queue.get(False)
            except (KeyError, Queue.Empty):
                # KeyError: this clientID has never subscribed for anything
                # Queue.Empty: empty queue
                return None
        finally:
            self.subscribers.release()

    def WaitForNextNotification(self, clientID):
        self.subscribers.acquire()
        try:
            try:
                return self.subscribers[clientID].queue.get()
            except KeyError:
                raise NotSubscribed
        finally:
            self.subscribers.release()

    def CancelNotification(self, notificationID, clientID = 0):
        # we need a way to remove the notification from all the queues its in
        pass



    ##
    # OBSOLETE FUNCTIONS
    ##
    BLOCKING = 1
    NONBLOCKING = 0
    SYSTEM_CLIENT = 1
    """ Enumerated error codes """
    OKAY = 0
    DECLARATION_NOT_FOUND = 1
    SUBSCRIBER_NOT_FOUND = 2
    DUPLICATE_CLIENT = 3
    DUPLICATE_DECLARATION = 4

    def Register(self,clientID):
        pass
        
    def Unregister(self,clientID):
        pass
 
    def IsRegistered(self, clientID):
        return self.subscribers.has_key(clientID)

    def DeleteDeclaration(self, name):
        del self.declarations[name]
    
    def GetDeclarationNames(self):
        return self.declarations.keys()
    
    def GetMessage(self, subscriber, mode):
        #return self.messageTable.GetMessage(subscriber, mode)
        return None
        
    def GetSubscriptionList(self, schemaName):
        #return self.declarations.GetSubscriptionList(schemaName)
        return []

    def IsDeclared(self, name):
        return self.declarations.has_key(name)

    def GetDescription(self, name):
        try:
            return self.declarations[name].description
        except (KeyError, AttributeError):
            return None

    def PutMessage(self, subscriber, notification):
        subscriber.queue.put(notification)
        
    def RemoveMessage(self,notificationID, subscriber):
        # we really dont want to get it.. just remove it
        subscriber.queue.get(notification)

    def Lock(self):
        pass

    def Unlock(self):
        pass
            
    def DeclareNotification(self, name, clientID, schema, description):
        self.declarations.acquire()
        try:
            if self.declarations.has_key(name):
                #raise AlreadyDeclared
                return

            self.declarations[name] = Declaration(name, clientID,
                                                  schema, description)

        finally:
            self.declarations.release()

    def UndeclareNotification(self,name,clientID):
        # figure out what clientID does here
        self.declarations.acquire()
        try:
            if not self.declarations.has_key(name):
                raise NotDeclared

            del self.declarations[name]

        finally:
            self.declarations.release()






def DeclarationFromEvent(event):
    name = event.name
    desc = event.getAttributeValue('description', default=None)
    return Declaration(name, None, None, desc)
    
class Declaration(object):
    def __init__(self, entryName, clientID, type, description):
        super(Declaration, self).__init__()
        self.name = entryName
        self.owner = clientID
        self.type = type
        self.description = description
        self.subscribers = {}

class Subscriber(object):
    def __init__(self, clientID, source):
        super(Subscriber, self).__init__()
        self.clientID = clientID
        self.source = source
        self.queue = Queue.Queue()

class LockableDict(dict):
    def __init__(self, *args, **kwds):
        super(LockableDict, self).__init__(*args, **kwds)
        self.__lock = threading.Lock()
    def acquire(self):
        self.__lock.acquire()
    def release(self):
        self.__lock.release()
