__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
Notification.py
Version .9
Written by Andrew Francis
July 4th, 2003
"""

import time

class Notification:
    def __init__(self, name, type, source, priority = 0):
        self.name = name
        self.priority = priority
        self.timestamp =""
        self.type = type
        self.source = source
        self.id = self.GetUniqueId()
        self.creationTime = time.time()       #add the time the event is created
        
    # Utility function
    
    # same signature as thing, hack for now
    def GetUniqueId(self):
        return str(id(self))

    def __repr__(self):
        return self.id + " " + self.name + " " + self.type + " " + str(self.creationTime) 
    
    # Public methods  
    def GetData(self):
        return self.data
      
    def GetDescription(self):
        return self.description
    
    def GetID(self):
        return self.id
      
    def GetName(self):
        return self.name
    
    def GetPriority(self):
        return self.priority
    
    def GetSource(self):
        return self.source
    
    def GetTime(self):
        return self.timestamp
    
    def GetType(self):
        return self.type
    
    def SetData(self,data):
        self.data = data
        
    #would like to change this in the future
    #changed, but work on immutability bit
    def SetTime(self):
        self.timestamp = time.time()
    
    
    
