#!bin/env python

"""
  This class implements the message class for the Instant Messaging
  Parcel, which is used to represent and display a Jabber Message
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import time
from wxPython.wx import *
from application.Application import app
        
# here's the main class for the control bar		
class RosterMessage:
    def __init__(self, date, sender, subject, body):
        if date == None:
            date = time.time()
        self.date = date
        
        self.sender = sender
        self.subject = subject
        self.body = body

    # just dummy code for now
    def GetSummaryLine(self):
        return sender + '-' + subject

    def FormatTwoDigits(self, value):
        if value < 10:
            return '0' + str(value)
        return str(value)
    
    def RenderDate(self, dateValue):
        timeArray = time.localtime(dateValue)
        year, month, day, hour, minute, second = timeArray[0:6]
        
        hourStr = self.FormatTwoDigits(hour)
        minuteStr = self.FormatTwoDigits(minute)
        secStr = self.FormatTwoDigits(second)
        return '%s:%s:%s' % (hourStr, minuteStr, secStr)

    def RenderSender(self, jabberID):
        jabberName = app.jabberClient.GetNameFromID(jabberID)
        
        return 'From ' + jabberName + ': '
    
    def RenderShortMessage(self):
        dateText = '[' + self.RenderDate(self.date) + '] '
        senderText = self.RenderSender(self.sender)
        messageText = dateText + senderText + '\n' + self.body
        return messageText
    
    def GetSender(self):
        pass
    