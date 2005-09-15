__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application import schema

class _NotificationItem(schema.Item):
    """
    This is a simple item that serves as a notification handler for
    TestNotification.py.  The corresponding parcel.xml is in
    parcels/notification/parcel.xml
    """
    def __init__(self, name=None, parent=None, kind=None):
        super(NotificationItem, self).__init__(name, parent, kind)
        self.action = ([],[])

    def handle(self, action):
        """
        Stash the notification action for later retrieval
        """
        self.action = action

# schema API doesn't like a class and module having the same name
NotificationItem = _NotificationItem    

def installParcel(parcel, oldVersion=None):
    NotificationItem.update(parcel, "testNotifier")

