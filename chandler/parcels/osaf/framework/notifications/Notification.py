"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import application.Globals as Globals

class Notification(object):
    """
    Notification

    @ivar data: dictionary passed along with the notification
    @type data: dict
    @ivar threadid: This should be set only if you wish for a notification to
                    go to a specific thread
    @type threadid: C{id(threading.currentThread())}

    @ivar __eventUUID: UUID of event

    """
    __slots__ = [ 'data', '__eventUUID', 'threadid' ]

    def __init__(self, event, *args):
        """
        @param event: The Event you wish this notification to be about
        @type event: L{Event}
        """
        super(Notification, self).__init__()
        self.__eventUUID = event.itsUUID
        self.data = None
        self.threadid = None

    def __getEvent(self):
        return Globals.repository[self.__eventUUID]
    event = property(__getEvent)

    def GetData(self):
        return self.data

    def SetData(self,data):
        self.data = data

    def __repr__(self):
        return '<Notification> ' +  str(self.event.itsPath)
