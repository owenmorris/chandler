__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

class Notification(object):
    def __init__(self, name, type, source, priority = 0):
        super(Notification, self).__init__()
        self._eventUUID = None
        self.name = name
        self.priority = priority
        self.type = type
        self.source = source
        self.data = None

    def __getEvent(self):
        return Globals.repository[self._eventUUID]
    event = property(__getEvent)

    def __repr__(self):
        return self.name + " " + self.type

    def GetName(self):
        return self.name

    def GetPriority(self):
        return self.priority

    def GetSource(self):
        return self.source

    def GetType(self):
        return self.type

    def GetData(self):
        return self.data

    def SetData(self,data):
        self.data = data
