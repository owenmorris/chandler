__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


""""
NotificationTests.py
Written by Andrew Francis
July 5th, 2003

TestOne - test DeclareNotification,UndeclareNotification,Subscribe,Unsubscribe
          GetDescription, PostNotification, GetNextNotification,
          WaitForNextNotification
          
TestTwo - test WaitForNextNotification and PostNotification under concurrent
        conditions

TestThree -  FindNotification tests

TestFive - Test NotificationQueue
TestSix -  Test NotificationQueue

TestSeven - Test CancelNotification

"""

from  NotificationManager import NotificationManager
from  NotificationManager import Status
from  Notification import Notification
from  NotificationQueue import NotificationQueue
import threading
import time

def nop():
    print "sending message to worker"
 
class Worker(threading.Thread):
    def __init__(self, notificationManager,identity):
        self.notificationManager = notificationManager
        self.identity = identity
        
        #subscribe to an event type
        self.notificationManager.Register(self.identity)
        self.notificationManager.Subscribe("foo", self.identity, None)
                
        threading.Thread.__init__(self)
        
             
    def run(self):
        print "I am about to wait in child"
        fooEvent = self.notificationManager.WaitForNextNotification(self.identity)
        print "this is the foo event",fooEvent
        
        
class NotificationTests:
    def __init__(self):
        
        return
    
    def TestOne(self):
        manager = NotificationManager()
        
        # register two clients        
        manager.Register(1)
        manager.Register(2)
        
        #define some test events
        fooEvent1 = Notification("foo","fooType",None,0)
        fooEvent2 = Notification("foo","fooType",None,0)
        barEvent1 = Notification("bar","barType",None,0)
        barEvent2 = Notification("bar","barType",None,0)
        acmeEvent = Notification("acme","acmeType",None,0)
        mumbleEvent = Notification("mumble","mumbleType",None,0)
            
        
        #register two declarations
        print "****TESTING DECLARATIONS****"
        result = manager.DeclareNotification("foo",1,"fooType","testing foo")
        if result == True:
            print "PASS"
        else:
            print "FAILED"
            
        print "Testing duplicate Declaration"
        result = manager.DeclareNotification("foo",1,"fooType","testing foo")
        if result == 0:
            print "PASS - duplicate"
        else:
            print "FAILED"
            
        print "Testing same name different type"
        result = manager.DeclareNotification("foo",1,"acmeType","testing acme foo")
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
            
        result = manager.DeclareNotification("bar",2,"barType","testing bar")
        if result == 1:
            print "PASS"
        else:
            print "FAILED"        
        
        result = manager.DeclareNotification("acme",3,"acmeType","testing bar")
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
    
        result = manager.UndeclareNotification("acme",3)
        print "Testing Undeclaration"
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
            
        print "Testing non-existant undeclared"    
        result = manager.UndeclareNotification("acme",3)
        if result == 0:
            print "PASS"
        else:
            print "FAILED"
            
        print "testing description"
        result = manager.GetDescription("foo")
        if result == None:
            print "FAILED"
        else:
            print "PASS",result
            
        print "testing description of non-existant type"    
        result = manager.GetDescription("acme")
        if result == None:
            print "PASS"
        else:
            print "FAIL",result
           
        print "**** END DECLARATION TESTS ****"           
              
        print "***** SUBSCRIBE TESTS ******"
        
        result = manager.Subscribe("foo", 1, None)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
            
        print "test duplicate subscription"
        result = manager.Subscribe("foo", 1, None)
        if result == 0:
            print "PASS"
        else:
            print "FAILED"

        result = manager.Subscribe("foo", 2, None)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"

        result = manager.Subscribe("bar", 1, None)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"        
        
        result = manager.Subscribe("bar", 2, None)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
                
        result = manager.Subscribe("foo", 4,None)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
        
        print "subscribe to non existant type"
        result = manager.Subscribe("non-existant",1,None)
        if result == 0:
            print "PASS"
        else:
            print "FAILED"
          
        
        print "Testing Unsubscribe"
        result = manager.Unsubscribe("foo",4)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
            
            
        print "Testing unsubscribing to non-existant type"    
        result = manager.Unsubscribe("foo",4)
        if result == 0:
            print "PASS"
        else:
            print "FAILED"
            
        print "**** SUBSCRIPTION END *****"
       
        result = manager.PostNotification(fooEvent1)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
            
        result = manager.PostNotification(fooEvent2)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"

        result = manager.PostNotification(barEvent1)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"

        result = manager.PostNotification(barEvent2)
        if result == 1:
            print "PASS"
        else:
            print "FAILED"
    
        print "Testing posting non-existant event"
        result = manager.PostNotification(acmeEvent)
        if result == 0:
            print "PASS"
        else:
            print "FAILED"
        
        print "Testing posting non-existant event"    
        result = manager.PostNotification(mumbleEvent)   
        if result == 0:
            print "PASS"
        else:
            print "FAILED"   
    
        #now test the GetNextEvent
        #check if NONblocking is working
        for i in [1,2]:
            testEvent = manager.GetNextNotification(i)
            while testEvent != None:
                print i,":",testEvent
                testEvent = manager.GetNextNotification(i)
                
        #check error checking #1 - Non-Existant client
        try:
            testEvent = manager.GetNextNotification(3)
        except:
            print "An exception has occured"
            
            
    def TestTwo(self):
        manager = NotificationManager()
        
        # register two clients        
        manager.Register(1)
        
        #define some test events
        fooEvent1 = Notification("foo","fooType", None, 0)
        
        #register two declarations
        manager.DeclareNotification("foo",1,"fooType","testing foo")

        
        #main thread starts worker
        worker = Worker(manager,2)
        worker.start()
        
        print "Main thread - waiting 10 seconds"
        timer = time.sleep(10)
    
        
        #post an event
        print "In main thread about to Post"
        manager.PostNotification(fooEvent1)
        
        
        return
            
            
    def TestThree(self):
        print "**** TEST THREE ****"
        manager = NotificationManager()
        manager.DeclareNotification("chandler/email/arrival/urgentMessageArrived",1,"email","testing foo")
        manager.DeclareNotification("chandler/email/arrival/replyMessageArrived",1,"email","testing foo")
        manager.DeclareNotification("chandler/email/arrival/messageArrived",1,"email","testing foo")
        
        manager.DeclareNotification("chandler/jabber/arrival/urgentMessageArrived",1,"email","testing foo")
        manager.DeclareNotification("chandler/jabber/arrival/replyMessageArrived",1,"email","testing foo")
        manager.DeclareNotification("chandler/jabber/arrival/messageArrived",1,"email","testing foo")
                
        results = manager.FindNotifications(".*")
        print "everything:"
        
        if results == []:
            print "nothing found"
        else:
            for result in results:
               print result
            
        # fixed regular expression    
        results = manager.FindNotifications("chandler/.*/arrival/*");
        print "all arrivals:"
        if results == []:
            print "Nothing found"
        else:
            for result in results:
               print result
               
        results = manager.FindNotifications("");
        print "nothing"
        if results == []:
            print "Nothing found"
        else:
            for result in results:
               print result
               
        print "bad regular expression"
        results = manager.FindNotifications("[]]");
        if results == []:
            print "Nothing found"
        else:
            for result in results:
               print result       
        
        
    #note watch the queue in the debugger.
    def TestFive(self):
        print "**** TEST FIVE *****"
        q = NotificationQueue()
        ids = []        
           
        #define some test events
        fooEvent1 = Notification("foo","fooType",None,0)
        q.put(fooEvent1)
        ids.append(fooEvent1.GetID())        
        
        fooEvent2 = Notification("foo","fooType",None,0)
        q.put(fooEvent2)
        ids.append(fooEvent2.GetID())
        
        barEvent1 = Notification("bar","barType",None,0)
        q.put(barEvent1)
        ids.append(barEvent1.GetID())        
        
        barEvent2 = Notification("bar","barType",None,0)
        q.put(barEvent2)
        ids.append(barEvent2.GetID())
        
        ids.append(0)
        
        for id in ids:
            print q.remove(id)
            
            
    def TestSix(self):
        q = NotificationQueue()
        n = []
        
        for i in range(4):
            n.append(Notification("foo","fooType",None,0))
            time.sleep(1)
            n[i].SetTime()
            q.put(n[i])
        
        for i in [4,5,6,7,8]:
            n.append(Notification("foo","fooType",None,0))
            time.sleep(1)
            n[i].SetTime()
            q.put(n[i])
        
        for i in [8,7,6,5,4,3,2,1,0]:
            q.put(n[i])
        
        for i in [9,10,11]:
            n.append(Notification("foo","fooType",None,0))
            n[i].SetTime()
            q.put(n[i])
            
        q.debug()
    
            
    def TestSeven(self):
        print "****TEST SEVEN ****"
        manager = NotificationManager()
        
        # register four clients        
        manager.Register(1)
        manager.Register(2)
        manager.Register(3)
        manager.Register(4)
        
        #define some test events
        fooEvent1 = Notification("foo","fooType",None,0)
        fooEvent2 = Notification("foo","fooType",None,0)
        
        result = manager.DeclareNotification("foo",1,"fooType","testing foo")
        
        result = manager.Subscribe("foo", 1, None) 
        result = manager.Subscribe("foo", 2, None)
     
        result = manager.PostNotification(fooEvent1)
        result = manager.PostNotification(fooEvent2)
        
        print '->', fooEvent2
        manager.CancelNotification(fooEvent2.GetID(),1)
        
        
        result = manager.GetNextNotification(1)
        if result.GetID() == fooEvent2.GetID():
            print "FAILED"
        else:
            print "PASSED"
        
        result = manager.GetNextNotification(2)
        if result.GetID() == fooEvent2.GetID():
            print "FAILED"
        else:
            print "PASSED"
      
        result = manager.GetNextNotification(1)
        if result == None:
            print "PASSED"
        else:
            print "FAILED"
        
        result = manager.GetNextNotification(2)
        if result == None:
            print "PASSED"
        else:
            print "FAILED"
        
        
    def TestEight(self):
        a = Status()
        b = Status(False)
        if (a):
            print "PASS A is True"
        else:
            print "Failed A is False"
            
        if (b):
            print "Failed B is True (should be False)"
        else:
            print "Passed B is False"    
                    
        return
    
    
    def TestNine(self):
        manager = NotificationManager()
        
        # register two clients        
        manager.Register(1)
        manager.Register(2)
        
        #define some test events
        fooEvent1 = Notification("foo","fooType",None,0)
        fooEvent2 = Notification("foo","fooType",None,0)
        barEvent1 = Notification("bar","barType",None,0)
        barEvent2 = Notification("bar","barType",None,0)
        acmeEvent = Notification("acme","acmeType",None,0)
        mumbleEvent = Notification("mumble","mumbleType",None,0)
            
        
        #register two declarations
        print "****TESTING DECLARATIONS****"
        result = manager.DeclareNotification("foo",1,"fooType","testing foo")
        if result:
            print "PASS"
        else:
            print "FAILED"
            
        print "Testing duplicate Declaration"
        result = manager.DeclareNotification("foo",1,"fooType","testing foo")
        if  not result:
            print "PASS - duplicate"
        else:
            print "FAILED"
            
        print "Testing same name different type"
        result = manager.DeclareNotification("foo",1,"acmeType","testing acme foo")
        if result:
            print "PASS"
        else:
            print "FAILED"
            
        result = manager.DeclareNotification("bar",2,"barType","testing bar")
        if result:
            print "PASS"
        else:
            print "FAILED"        
        
        result = manager.DeclareNotification("acme",3,"acmeType","testing bar")
        if result:
            print "PASS"
        else:
            print "FAILED"
    
        result = manager.UndeclareNotification("acme",3)
        print "Testing Undeclaration"
        if result:
            print "PASS"
        else:
            print "FAILED"
            
        print "Testing non-existant undeclared"    
        result = manager.UndeclareNotification("acme",3)
        if  not result:
            print "PASS"
        else:
            print "FAILED"
            
        print "testing description"
        result = manager.GetDescription("foo")
        if result == None:
            print "FAILED"
        else:
            print "PASS",result
            
        print "testing description of non-existant type"    
        result = manager.GetDescription("acme")
        if result == None:
            print "PASS"
        else:
            print "FAIL",result
           
        print "**** END DECLARATION TESTS ****"           
              
        print "***** SUBSCRIBE TESTS ******"
        
        result = manager.Subscribe("foo", 1, None)
        if result:
            print "PASS"
        else:
            print "FAILED"
            
        print "test duplicate subscription"
        result = manager.Subscribe("foo", 1, None)
        if  not result:
            print "PASS"
        else:
            print "FAILED"

        result = manager.Subscribe("foo", 2, None)
        if result:
            print "PASS"
        else:
            print "FAILED"

        result = manager.Subscribe("bar", 1, None)
        if result:
            print "PASS"
        else:
            print "FAILED"        
        
        result = manager.Subscribe("bar", 2, None)
        if result:
            print "PASS"
        else:
            print "FAILED"
                
        result = manager.Subscribe("foo", 4,None)
        if result:
            print "PASS"
        else:
            print "FAILED"
        
        print "subscribe to non existant type"
        result = manager.Subscribe("non-existant",1,None)
        if  not result:
            print "PASS"
        else:
            print "FAILED"
          
        
        print "Testing Unsubscribe"
        result = manager.Unsubscribe("foo",4)
        if result:
            print "PASS"
        else:
            print "FAILED"
            
            
        print "Testing unsubscribing to non-existant type"    
        result = manager.Unsubscribe("foo",4)
        if  not result:
            print "PASS"
        else:
            print "FAILED"
            
        print "**** SUBSCRIPTION END *****"
       
        result = manager.PostNotification(fooEvent1)
        if result:
            print "PASS"
        else:
            print "FAILED"
            
        result = manager.PostNotification(fooEvent2)
        if result:
            print "PASS"
        else:
            print "FAILED"

        result = manager.PostNotification(barEvent1)
        if result:
            print "PASS"
        else:
            print "FAILED"

        result = manager.PostNotification(barEvent2)
        if result:
            print "PASS"
        else:
            print "FAILED"
    
        print "Testing posting non-existant event"
        result = manager.PostNotification(acmeEvent)
        if  not result:
            print "PASS"
        else:
            print "FAILED"
        
        print "Testing posting non-existant event"    
        result = manager.PostNotification(mumbleEvent)   
        if  not result:
            print "PASS"
        else:
            print "FAILED"   
    
        #now test the GetNextEvent
        #check if NONblocking is working
        for i in [1,2]:
            testEvent = manager.GetNextNotification(i)
            while testEvent != None:
                print i,":",testEvent
                testEvent = manager.GetNextNotification(i)
                
        #check error checking #1 - Non-Existant client
        try:
            testEvent = manager.GetNextNotification(3)
        except:
            print "An exception has occured"
            
                
    
    
    
test = NotificationTests()
test.TestNine()
#test.TestTwo()
#test.TestThree()
#test.TestFive()
#test.TestSix()
#test.TestSeven()
#test.TestEight()

