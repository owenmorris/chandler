"""
Notification

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore.schema"

import repository.item.Item as Item

class NotificationItem(Item.Item):
    """
    A notification item, mainly intended as a dummy for query subscriptions.
    """
    def __init__(self, name=None, parent=None, kind=None):
        super(NotificationItem, self).__init__(name, parent, kind)

    def handle(self, action):
        pass
