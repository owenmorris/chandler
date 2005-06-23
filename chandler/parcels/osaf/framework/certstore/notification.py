"""
Notification

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore.schema"

from application import schema

class NotificationItem(schema.Item):
    """
    A notification item, mainly intended as a dummy for query subscriptions.
    """

    schema.kindInfo(
        displayName = "Notification Item",
        description = "A notification item, mainly intended as a dummy for "
                      "query subscriptions."
    )

    def __init__(self, name=None, parent=None, kind=None):
        super(NotificationItem, self).__init__(name, parent, kind)

    def handle(self, action):
        pass
