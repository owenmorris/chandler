__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

class Notification(object):
    __slots__ = [ 'data', '__eventUUID' ]
    def __init__(self, event, *args):
        super(Notification, self).__init__()
        self.__eventUUID = event.getUUID()
        self.data = None

    def __getEvent(self):
        return Globals.repository[self.__eventUUID]
    event = property(__getEvent)

    def GetData(self):
        return self.data

    def SetData(self,data):
        self.data = data
