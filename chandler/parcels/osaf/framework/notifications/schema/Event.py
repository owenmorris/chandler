__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from OSAF.framework.notifications.Notification import Notification
import application.Globals as Globals

class Event(Item):
    def Post(self, data):
        notification = Notification(self)
        notification.SetData(data)
        Globals.notificationManager.PostNotification(notification)
