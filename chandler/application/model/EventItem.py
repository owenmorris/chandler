#!bin/env python

"""Model object representing a calendar event in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from InformationItem import InformationItem

class EventItem(InformationItem):
    def __init__(self):
        InformationItem.__init__(self)

        # headline is a string
        self.headline = None

        # startTime and endTime are mxDateTime objects
        self.startTime = None
        self.endTime = None

    def getDuration(self):
        """Returns an mxDateTimeDelta, None if startTime or endTime is None"""

        if (self.endTime == None) or (self.startTime == None): return None
        return self.endTime - self.startTime
    
    def setDuration(self, dateTimeDelta):
        """Set duration of event, expects value to be mxDateTimeDelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
    
        if (self.startTime != None) :
            self.endTime = self.startTime + dateTimeDelta

    duration = property(getDuration, setDuration)

    def changeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration
        

