__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Queue
import thread
import Notification

"""
NotificationQueue.py
Version .1
Written by Andrew Francis
July 4th, 2003
"""

# the default strategy is to order notification 
# in order of arrival. Thread scheduling may
# otherwise account for discepencies for notifications
# being timestamped and placed on a subscriber queue
# This guarantees that notifications are enqueued in
# the order which they are timestamped.
def _timestamp(notification, queue):
    l  = len(queue) - 1
    if l == -1:
        queue.append(notification)
        #most notifications will be temporally ordered
    elif notification.GetTime() >= queue[l].GetTime():  
        queue.append(notification)
    else:
        i = 0
        while (i <= l):
            if notification.GetTime() <= queue[i].GetTime():
                queue.insert(i,notification)
                break
            else:
                i = i + 1
    return


class NotificationQueue(Queue.Queue):
    def __init__(self, maxsize=0, strategy = _timestamp):
        #self.cancelSema = thread.allocate_lock()   #allocate a lock for cancelling notifications       
        Queue.Queue.__init__(self, maxsize)        #initialise underlying superclass
        self.strategy = strategy
        return

    def _put(self,item):
        self.strategy(item, self.queue)  #add according to strategy 
        return
    
    def remove(self, notificationId):
        #self.cancelSema.acquire()
        result =  self._remove(notificationId)    
        #self.cancelSema.release()
        return result
        
    def _remove(self,notificationId):
        result = False
        for i in range(len(self.queue)):
            if self.queue[i].GetID() == notificationId:
                del self.queue[i]
                result = True
                break
        return result
    
    def debug(self):
        for notification in self.queue:
            print notification
                