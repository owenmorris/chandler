__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
NotificationManager.py
Version .1
Written by Andrew Francis

July 4th, 2003

While listening to "Mystery Achievement" :-)
"""

from NotificationQueue import NotificationQueue
#from DeclarationEntry import DeclarationEntry
import Queue
import re
import thread

from wxPython.wx import wxWakeUpIdle

from persistence import Persistent 
from persistence.list import PersistentList
from persistence.dict import PersistentDict

DuplicateClient = "Duplicate Client"
SchemaNotFound = "Schema not found"
SubscriberNotFound = "Subscriber not Found"
SubscriberRegistered = "Subscriber Already registered"
InvalidSubscriberId = "Invalid Subscriber Id"

class NotificationManager(Persistent):
    
    TRUE = 1
    FALSE = 0
    BLOCKING = 1
    NONBLOCKING = 0
    
    SYSTEM_CLIENT = 1
    
    """
    Enumerated error codes
    """
    OKAY = 0
    DECLARATION_NOT_FOUND = 1
    SUBSCRIBER_NOT_FOUND = 2
    DUPLICATE_CLIENT = 3
    DUPLICATE_DECLARATION = 4

    notificationMutex = thread.allocate_lock()
    
    # the message queues are not persistent, so keep them in a class variable
    # messageTable = MessageTable()
    
    def __init__(self):
        self.declarations = Declarations()   #handle declarations
        self.messageTable = MessageTable()
        self.subscriberList = PersistentList()
                
    # EXPERIMENTAL
    def Register(self,clientID):
        self.messageTable.AddQueue(clientID)
 
        try:
            index = self.subscriberList.index(clientID)
            # FIXME: should throw an 'AlreadyRegistered' exception here?
        except ValueError:
            self.subscriberList.append(clientID)

        
    def Unregister(self,clientID):
        self.messageTable.DeleteQueue(clientID)

        try:
            index = self.subscriberList.index(clientID)
            del self.subscriberList[index]
        except ValueError:
            # FIXME: should throw a 'NotRegistered' exception here?
            pass
        
    # called when the app is started up to add queues for all the persistent subscribers
    def PrepareSubscribers(self):
        self.messageTable.AddSubscribers(self.subscriberList)

    # END EXPERIMENTAL
    
    #UTILITY
    """
    The purpose of the utility methods is to add an additional level of
    indirection between the low level implementation details and the
    higher level logic. In this fashion, low level details can
    be altered with a higher chance of not disturbing the public methods
    """
    
    def DeleteDeclaration(self,name):
        return self.declarations.DeleteDeclaration(name)
    
    def GetDeclarationNames(self):
        return self.declarations.GetDeclarationNames()
    
    def GetMessage(self, subscriber, mode):
        return self.messageTable.GetMessage(subscriber, mode)
        
    def GetSubscriptionList(self, schemaName):
        return self.declarations.GetSubscriptionList(schemaName)

    def IsDeclared(self, name):
        return self.declarations.IsDeclared(name)

    def Lock(self):
         NotificationManager.notificationMutex.acquire()
    
    def PutMessage(self, subscriber, notification):
        self.messageTable.PutMessage(subscriber, notification)
        
    def RemoveMessage(self,notificationID, subscriber):
        self.messageTable.RemoveMessage(notificationID,subscriber)
    
    def Unlock(self):
        NotificationManager.notificationMutex.release()
            
    #END UTILITY
    
    """
    Override the following methods
    """
    
    def _declareNotification(self,name,clientID,schema,description):
        errorCode = self.declarations.AddDeclaration(name,description,schema)
        """
        July 15th, try to fix inconsistency in AddDeclaration's return code
        """
        if errorCode != True:
            result = False
            errorCode = NotificationManager.DUPLICATE_DECLARATION
        else:
            result = True
            errorCode = NotificationManager.OKAY
            
        return Status(result, errorCode)
         
    
    
    def _undeclareNotification(self,name,clientID):
        errorCode = self.declarations.DeleteDeclaration(name)           
        if errorCode != NotificationManager.OKAY:
            result = False
        else:
            result = True
        return Status(result, errorCode)
        
        
    def _findNotifications(self,wildcard):
        
        declarationList = self.GetDeclarationNames()
        result = []
        
        #compile the regular expression
        try:
           regularExpression = re.compile(wildcard,re.IGNORECASE)
        except:
            #should tell the client that there is a problem with the regular expression
            result = None    
        else:
            for declaration in declarationList:
               matchObject = regularExpression.match(declaration)
               if (matchObject != None):
                  result.append(matchObject.group())
                  
        return


    def _getDescription(self, name):
        return self.declarations.GetDeclarationDescription(name)

    
    def _subscribe(self,name,clientID,source=None):
       try:
           self.declarations.AddSubscriber(name,clientID)        
           errorCode = NotificationManager.OKAY
          
       except (SchemaNotFound, name):   
           errorCode = NotificationManager.DECLARATION_NOT_FOUND

       except (DuplicateClient, clientID):
           errorCode = NotificationManager.DUPLICATE_CLIENT
       
       if errorCode != NotificationManager.OKAY:
           result = False
       else:
           result = True
      
       return Status(result, errorCode)
      
    
    
    def _unsubscribe(self,name,clientID):
        try:
           self.declarations.DeleteSubscriber(name, clientID)
           errorCode = NotificationManager.OKAY
        except SubscriberNotFound:
           errorCode = NotificationManager.SUBSCRIBER_NOT_FOUND    
        except SchemaNotFound:
           errorCode = NotificationManager.DECLARATION_NOT_FOUND
           
        if errorCode != NotificationManager.OKAY:
            result = False
        else:
            result = True
        return Status(result, errorCode)   
        
           
    # for now we don't care who posts......
    # future version should check notification for validity
    def _postNotification(self,notification):         
        if self.IsDeclared(notification.GetName()):      
           subscriptionList = self.GetSubscriptionList(notification.GetName())
           
           # what do we do if there are no subscribers?
           # for now we will assume the post suceeded.
           
           for subscriber in subscriptionList:
               # NOTE race a client could have unsubscribed.....
               # we will ignore the error
               try:
                   notification.SetTime()
                   self.PutMessage(subscriber, notification)
               except SubscriberNotFound:
                   pass
                   
           result = Status(True)
           
           # call wxWakeUpIdle to give a chance for idle handlers to notice the notification
           wxWakeUpIdle()
        else:
           result = Status(False, NotificationManager.DECLARATION_NOT_FOUND)
       
        return result
    
    
    def _getNextNotification(self,clientID):
        return self.messageTable.GetMessage(clientID, NotificationManager.NONBLOCKING)
        
             
    def _waitForNextNotification(self,clientID):
        return messageTable.GetMessage(clientID, NotificationManager.BLOCKING)
    
    
    def _cancelNotification(self, notificationID, clientID = 0):
        try:
            result = False
            declarations = self.GetDeclarationNames()
            for declaration in declarations:
                #NOTE race condition - an undeclare could be occuring
                subscriptionList = self.GetSubscriptionList(declaration)
                for subscriber in subscriptionList:
                    """
                    RemoveMessage can fail because:
                    Subscriber has unsubscribed
                    Message has been consumed
                    """
                    self.RemoveMessage(notificationID, subscriber)   
                result = Status(True)
        except SchemaNotFound:
            result = Status(False, NotificationManager.DECLARATION_NOT_FOUND)
        except SubscriberNotFound:
            result = Status(False, NotificationManager.SUBSCRIBER_NOT_FOUND)
        return result
   
    """
    Public Methods
    """
   
    def DeclareNotification(self,name,clientID,schema,description):
        try:
            self.Lock()
            result = self._declareNotification(name,clientID,schema,description)
        finally:
            self.Unlock()
            return result
    
    
    def UndeclareNotification(self,name,clientID):
        try:
            self.Lock()
            result = self._undeclareNotification(name,clientID)
        finally:
            self.Unlock()
            return result
         
    def FindNotifications(self,wildcard):
        try:
            self.Lock()
            result = self._findNotifications(wildcard)
        finally:
            self.Unlock()
            return result


    def GetDescription(self, name):
        try:
            self.Lock()
            result = self._getDescription(name)
        finally:
            self.Unlock()
            return result

    
    def Subscribe(self,name,clientID,source = None):
        try:
            self.Lock()
            result = self._subscribe(name,clientID,source)
        finally:
            self.Unlock()
            return result
        
    
    def Unsubscribe(self,name,clientID):
        try:
            self.Lock()
            result = self._unsubscribe(name,clientID)
        finally:
            self.Unlock()
            return result

    # for now we don't care who posts......
    # future version should check notification for validity
    def PostNotification(self,notification):    
        try:
            self.Lock()
            result = self._postNotification(notification)
        finally:
            self.Unlock()
            return result
    
    def GetNextNotification(self,clientID):
        return self._getNextNotification(clientID)       
             
             
    """
    Warning I need to analyse this method more - if I lock, I will
    get a hold-and-wait condition if the consumer is also
    calling the Notification Manager. So far, it does not seem
    that this method needs synchronization
    """
    def WaitForNextNotification(self,clientID):
        return self._waitForNextNotification(clientID)
        
    
    def CancelNotification(self, notificationID, clientID = 0):
        try:
            self.Lock()
            result = self._cancelNotification(notificationID, clientID)
        finally:
            self.Unlock()
            return result
      
"""
The MessageTable class handles subscription details
"""

class MessageTable: 
   
    table = {}
    
    def __init__(self): 
        return
    
    def AddQueue(self, subscriber):
        if subscriber == "":
            raise InvalidSubscriberId
        
        if MessageTable.table.has_key(subscriber):
            raise SubscriberRegistered
        else:
           MessageTable.table[subscriber] = NotificationQueue()

    def HasQueue(self, subscriber):
        return MessageTable.table.has_key(subscriber)
    
    def DeleteQueue(self,subscriber):
        del MessageTable.table[subscriber]


    def AddSubscribers(self, subscriberList):
        for subscriber in subscriberList:
            if not self.HasQueue(subscriber):
                self.AddQueue(subscriber)
            
    def GetMessage(self, subscriber, mode):
        try:
            queue = MessageTable.table[subscriber]
            notification = queue.get(mode)
        
        except Queue.Empty:
            notification = None
    
        except KeyError:
            raise SubscriberNotFound, subscriber
        
        return notification
    
    def PutMessage(self, subscriber, notification):
        try:         
            queue = MessageTable.table[subscriber]
            queue.put(notification)
        
        except KeyError:
            raise SubscriberNotFound, subscriber
        
        return
    
    
    def RemoveMessage(self, notificationID, subscriber):
        result = True
        try:         
            queue = MessageTable.table[subscriber]
            result = queue.remove(notificationID)
        except KeyError:
            result = False
        return result
        
"""
The Declaration class handles declaration details
"""

class Declarations(Persistent):
    def __init__(self):
        self.subscriptions = PersistentDict()
        return
         
    
    def AddDeclaration(self, name, description, type, clientID = 0):
        if self.subscriptions.has_key(name) and \
           self.subscriptions[name].GetType() == type:
            return False
        else:
            self.subscriptions[name] = DeclarationEntry(name, clientID, type, \
                                                        description)
        return True           
    
    
    
    #associate a subscriber with a declaration
    def AddSubscriber(self, name, clientID):
        try:
            subscriptionList = self.subscriptions[name].GetSubscriptionList()
        except KeyError:
            raise SchemaNotFound, name
       
        #cannot have duplicates 
        if (clientID in subscriptionList):
            raise DuplicateClient, clientID
        else:
            subscriptionList.append(clientID)
       
       
    def DeleteDeclaration(self, name, clientID=0):
        try:
            del self.subscriptions[name]
            result = NotificationManager.OKAY
        except:
            result = NotificationManager.DECLARATION_NOT_FOUND
        return result
       
       
    def DeleteSubscriber(self, name, clientID):
        try:
            subscriptionList = self.subscriptions[name].GetSubscriptionList()
            del subscriptionList[subscriptionList.index(clientID)]
        except KeyError:
            raise SchemaNotFound, name
        except ValueError:
            raise SubscriberNotFound, clientID
        return
    
    # NOTE this ought to throw an error
    def GetDeclarationDescription(self,name):
        try:
            result =  self.subscriptions[name].GetDescription()
        except KeyError:
            result = None
            #raise SchemaNotFound, name
        return result
    
    def GetDeclarationNames(self):
        return self.subscriptions.keys()
    
    #get the list of subscribers associated with a declaration type
    def GetSubscriptionList(self, name):
        try:
            subscriptionList = self.subscriptions[name].GetSubscriptionList()
        
        except KeyError:
            subscriptionList = None
        
        return subscriptionList

    
    def IsDeclared(self,name):
        return self.subscriptions.has_key(name)
    
    """
    DeclarationEntry class
    """
    
class DeclarationEntry(Persistent):
    def __init__(self, name, clientID, type, description, acl = None):
        self.name = name
        self.owner = clientID
        self.type = type
        self.description = description
        self.acl = acl
        self.subscriptionList = PersistentList()
        return 
    
    #def __repr__(self):
    #    return self.name + " " + self.clientID + self.type + \
    #           self.description + str(self.subscriptionList)

    def GetName(self):
        return self.name
    
    def GetOwner(self):
        return self.owner
    
    def GetType(self):
        return self.type
    
    def GetDescription(self):
        return self.description
    
    def GetAcl(self):
        return self.acl
    
    def GetSubscriptionList(self):
        return self.subscriptionList
    
"""
July 14th, change
"""
class Status:
    True = 1
    
    def __init__(self, isOkay = True, errorCode = 0):
        self.isOkay = isOkay
        self.errorCode = errorCode

    def __nonzero__(self):
        return self.isOkay
    
    def getErrorStatus(self):
        return self.errorCode
        

