#!bin/env python

"""
ContactViewInfo holds the data that describes a particular view,
including its query, permission and display information
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from persistence import Persistent

from application.repository.Namespace import chandler

# a query contains a list of filter conditions.  Each filter condition
# either accepts or rejects a contact based on its attributes
class FilterCondition:
    def __init__(self, attribute, operation, value, andFlag):
        self.attribute = attribute
        self.operation = operation
        self.value = value
        self.andFlag = andFlag
        
    # for now, we only support two operators, "equals" and "hasgroup"
    # eventually, we'll have more
    def FilterContact(self, contact):
        if self.operation == 'equals':
            attributeValue = contact.GetAttribute(self.attribute)
            return attributeValue == self.value
        
        if self.operation == 'contains':
            attributeValue = contact.GetAttribute(self.attribute)
            return attributeValue.find(self.value) > -1
            
        if self.operation == 'hasgroup':
            return contact.HasGroup(self.value)
        
        # otherwise, return true
        return true
    
class ContactViewInfo(Persistent):
    def __init__(self, queryClass, queryFilter, title, description):        
        self.queryClass = queryClass
        self.queryFilter = queryFilter
        self.title = title
        self.description = description
        self.sharingPolicy = 'private'
        self.remoteFlag = false
        
    def FilterContact(self, contact):
        # if a class is specified and it doesn't match, reject it
        if self.queryClass != None:
            akoURL = contact.GetAkoURL()
            if not (contact.GetAkoURL() == self.queryClass):
                return false
        
        # if there are any filter conditions, loop through them
        if self.queryFilter == None:
            return true
        
        for condition in self.queryFilter:
            acceptFlag = condition.FilterContact(contact)
            if acceptFlag and not condition.andFlag:
                return true
            
            if not acceptFlag and condition.andFlag:
                return false
            
        # if we've made it this far, accept it
        return true

    def GetURL(self):
        return 'Contacts/' + self.title
    
    def GetDescription(self):
        return self.description
    
    def SetDescription(self, description):
        self.description = description
        
    def GetTitle(self):
        return self.title
    
    def SetTitle(self, title):
        self.title = title
       
    def GetSharingPolicy(self):
        return self.sharingPolicy
    
    def SetSharingPolicy(self, newPolicy):
        self.sharingPolicy = newPolicy
        
    def IsRemote(self):
        return self.remoteFlag
    
    def SetRemote(self, remoteFlag):
        self.remoteFlag = remoteFlag
        