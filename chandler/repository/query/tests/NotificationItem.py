__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item.Item as Item

class NotificationItem(Item.Item):
    """
    This is a simple item that serves as a notification handler for
    TestNotification.py.  The corresponding parcel.xml is in
    parcels/notification/parcel.xml
    """
    def __init__(self, name=None, parent=None, kind=None):
        super(NotificationItem, self).__init__(name, parent, kind)

    def handle(self, action):
        """
        Stash the notification action for later retrieval
        """
        self.action = action
