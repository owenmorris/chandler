"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

from repository.item.Item import Item
from osaf.framework.notifications.Notification import Notification
import application.Globals as Globals

class Event(Item):
    """
    The Event Item
    """
    def __init__(self, *args, **kwds):
        super(Event, self).__init__(*args, **kwds)
        Globals.notificationManager.AddEvent(self)
    
    def Post(self, data):
        """
        Post a notification to all subscribers of this event

        @param data: Dictionary of data to send along with the event
        @type data: C{dict}
        """
        notification = Notification(self)
        notification.SetData(data)
        Globals.notificationManager.PostNotification(notification)
