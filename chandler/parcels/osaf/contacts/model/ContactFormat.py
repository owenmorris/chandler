#!bin/env python

"""Model object defining the format of a contact (which attributes are
   displayed where).
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

'''
This is the ContactFormat class, which maintains lists of attributes that are
displayed in the header or body of a contact.  For now, it's implemented with a
comma-delimited string in the data-base, but soon we should use a list of references
to real schema attributes.
'''

class ContactFormatFactory:
    def __init__(self, rep):
        self._container = rep.find("//Contacts")
        self._kind = rep.find("//Schema/ContactsSchema/ContactFormat")
        
    def NewItem(self):
        item = ContactFormat(None, self._container, self._kind)
        
        item.setAttributeValue('headerAttributes', '')
        item.setAttributeValue('bodyAttributes', '')
        
        return item

class ContactFormat(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(ContactFormat, self).__init__(name, parent, kind, **_kwds)
        
    def GetHeaderAttributes(self):
        attributeStr = self.getAttributeValue('headerAttributes')
        if attributeStr == None or len(attributeStr) == 0:
            return []
        
        return attributeStr.split(',')
    
    def SetHeaderAttributes(self, headerAttributes):
        attributeStr = ''
        for attribute in headerAttributes:
            attributeStr += attribute + ','
        self.setAttributeValue('headerAttributes', attributeStr[0:-1])
        
    def HasHeaderAttribute(self, attribute):
        try:
            index = self.headerAttributes.index(attribute)
            return True
        except ValueError:
            return False

    def AddHeaderAttribute(self, newAttribute):
        if not self.HasHeaderAttribute(newAttribute):
            list = self.GetHeaderAttributes()
            list.append(newAttribute)
            self.SetHeaderAttributes(list)
        
    def GetBodyAttributes(self):
        attributeStr = self.getAttributeValue('bodyAttributes')
        if attributeStr == None or len(attributeStr) == 0:
            return []
        
        return attributeStr.split(',')
    
    def SetBodyAttributes(self, bodyAttributes):
        attributeStr = ''
        for attribute in bodyAttributes:
            attributeStr += attribute + ','
        self.setAttributeValue('bodyAttributes', attributeStr[0:-1])
    
    def HasBodyAttribute(self, attribute):
        try:
            index = self.bodyAttributes.index(attribute)
            return True
        except ValueError:
            return False
    
    def AddBodyAttribute(self, attribute):
       if not self.HasBodyAttribute(attribute):
            list = self.GetBodyAttributes()
            list.append(attribute)
            self.SetBodyAttributes(list)
    
    headerAttributes = property(GetHeaderAttributes, SetHeaderAttributes)
    bodyAttributes = property(GetBodyAttributes, SetBodyAttributes)
