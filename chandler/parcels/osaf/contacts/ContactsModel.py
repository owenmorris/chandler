#!bin/env python

"""
Temporary Model Classes for Chandler Contacts - will integrate with application.model soon
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import string
import os
import xml.sax.handler

from wxPython.wx import *

from application.repository.Repository import Repository
from application.repository.Namespace import chandler
from application.repository.Contact import Contact, AkoContactFactory
from application.repository.ContactName import ContactName, AkoPersonNameFactory
                        
# here's the contact template class
class ContactTemplate:
    def __init__(self, templateType):
        self.templateType = templateType
        self.contactClass = 'Person'
        self.contactMethods = []
        self.headerAttributes = []
        self.bodyAttributes = []
        self.groups = []
        
    def GetContactMethods(self):
        return self.contactMethods
 
    def HasContactMethod(self, methodName):
        try:
          self.contactMethods.index(methodName)
          return true
        except ValueError:
          return false
      
    def HasAttribute(self, attribute, position):
        if position == 'header':
            list = self.headerAttributes
        else:
            list = self.bodyAttributes
            
        try:
          result = list.index(attribute)
          return true
        except ValueError:
          return false
    
    def GetContactClass(self):
        return self.contactClass
    
    def SetContactClass(self, classType):
        self.contactClass = classType
        
    def GetHeaderAttributes(self):
        return self.headerAttributes
    
    def GetBodyAttributes(self):
        return self.bodyAttributes
    
    def AddContactMethod(self, methodName):
        if not self.HasContactMethod(methodName):
            self.contactMethods.append(methodName)
            
    def RemoveContactMethod(self, methodName):
        try:
            methodIndex = self.contactMethods.index(methodName)
            del self.contactMethods[methodIndex]
        except:
            pass
        
    def AddGroup(self, groupName):
        self.groups.append(groupName)
    
    def GetGroups(self):
        return self.groups
    
    def AddAttribute(self, attributeName, attributePosition):
        if self.HasAttribute(attributeName, attributePosition):
            return
        
        if attributePosition == 'header':
            self.headerAttributes.append(attributeName)
        else:
            self.bodyAttributes.append(attributeName)
 
    def RemoveAttribute(self, attributeName, attributePosition):
        if attributePosition == 'header':
            list = self.headerAttributes
        else:
            list = self.bodyAttributes
            
        try:
            attributeIndex = list.index(attributeName)
            del list[attributeIndex]
        except:
            pass
 
# here's the parser for the contact template file
class ContactTemplateHandler(xml.sax.handler.ContentHandler):
    def __init__(self, contactDictionary):
        self.contacts = contactDictionary
        self.contactTemplate = None
        self.buffer = ""
        
    def startElement(self, name, attributes):		
        self.buffer = ""
                
        if name == 'ContactTemplate':
            currentType = attributes['type']
            self.contactTemplate = ContactTemplate(currentType)
            self.contacts.AddContactTemplate(currentType, self.contactTemplate)
        elif name == 'ContactMethod':
            contactMethodName = attributes['name']
            self.contactTemplate.AddContactMethod(contactMethodName)
        elif name == 'ContactClass':
            classType = attributes['type']
            self.contactTemplate.SetContactClass(classType)
        elif name == 'Group':
            groupName = attributes['name']
            self.contactTemplate.AddGroup(groupName)
        elif name == 'Attribute':
            position = attributes['position']
            attributeName = attributes['name']
            self.contactTemplate.AddAttribute(attributeName, position)
    
    def characters(self, data):
        self.buffer += data
                                
    def endElement(self, name):					
        if name == 'ContactTemplate':
            self.contactTemplate = None

# the ContactMetaData class keeps track of templates and other metadata.  More of this should
# eventually go into the repository
class ContactMetaData:
    def __init__(self, contactView, basePath):
        self.contactView = contactView
        self.basePath = basePath
        self.templates = {}
        
        self.LoadAttributeDictionary()      
        self.LoadTemplates()
        
    def GetTemplates(self):
        return self.templates
    
    def GetTemplate(self, templateType):
        if self.templates.has_key(templateType):
            return self.templates[templateType]        
        return None
    
    def GetTemplateNames(self):
        return self.templates.keys()
 
    # return a list of all the groups by iterating through the contacts
    def GetGroupsList(self):
        allGroups = []
        repository = Repository()
        for item in repository.thingList:
            if isinstance(item, Contact):
                contactGroups = item.GetGroups()
                for currentGroup in contactGroups:
                    try:
                        index = allGroups.index(currentGroup)
                    except ValueError:
                        allGroups.append(currentGroup)
                    
        return allGroups
     
    # FIXME: Katie: Shouldn't be hardwired to "PersonName"
    def LoadAttributeDictionary(self):
        self.attributeDictionary = AkoContactFactory().GetAko()
        self.nameAttributeDictionary = AkoPersonNameFactory().GetAko()
       
    def GetAttributeDictionary(self):
        return self.attributeDictionary
    
    def GetAttributeTemplate(self, attribute):
        return self.attributeDictionary.GetAttributeTemplate(attribute)
    
    def GetNameAttributeTemplate(self, attribute):
        return self.nameAttributeDictionary.GetAttributeTemplate(attribute)

    def GetAttributeLabel(self, attribute):
        attributeTemplate = self.GetAttributeTemplate(attribute)
        if (attributeTemplate != None):
            return attributeTemplate.GetDisplayName()
        return None

    def AddContactTemplate(self, templateType, template):
        self.templates[templateType] = template
    
    def RemoveContactTemplate(self, templateType):
        try:
            del self.templates[templateType]
        except:
            pass
        
    # get the default value for a given attribute
    def GetAttributeDefaultValue(self, attribute):
        attributeTemplate = self.GetAttributeTemplate(attribute)
        if (attributeTemplate != None):
            return attributeTemplate.GetDefault()
        return ''
    
    def GetNameAttributeDefaultValue(self, attribute):
        attributeTemplate = self.GetNameAttributeTemplate(attribute)
        if (attributeTemplate != None):
            return attributeTemplate.GetDefault()
        return ''
    
    # get the type for the passed in attribute
    def GetAttributeType(self, attribute):
        attributeTemplate = self.GetAttributeTemplate(attribute)
        if (attributeTemplate != None):
            range = attributeTemplate.GetRange()
            cardinality = attributeTemplate.GetCardinality()
            if ((type(range) is list) and (cardinality is None)):
                attributeType = 'multienum'
            elif ((type(range) is list) and (cardinality == 1)):
                attributeType = 'enumeration'
            else:
                attributeType = range
        else:
            attributeType = 'string'
        return attributeType
    
    # get the choice list or constraints for the passed in attribute
    def GetAttributeData(self, attribute):
        attributeTemplate = self.GetAttributeTemplate(attribute)
        if (attributeTemplate != None):
            return attributeTemplate.GetRange()
        return None
         
    def LoadTemplates(self):
        parser = xml.sax.make_parser()
        handler = ContactTemplateHandler(self)
                
        parser.setContentHandler(handler)
        path = self.basePath + os.sep + 'resources/contactTemplates.xml'
        parser.parse(path)
                
    # return a list of all of the choices for the passed-in attribute
    def GetAttributeChoices(self, attributeName):
        choices = []
        repository = Repository()
        for item in repository.thingList:
            if isinstance(item, Contact):
                contact = item                
                value = contact.GetAttribute(attributeName)
                
                # if it's comma separated, parse and enter each phrase separately
                if value != None:
                    if value.find(',') > 0:
                        list = value.split(',')
                    else:
                        list = [value]
                
                        for phrase in list:
                            phrase = phrase.strip()
                            if phrase != None:
                                try:
                                    choices.index(phrase)
                                except:
                                    choices.append(phrase)
 
                # special hack to include company names in the company attribute choices
                if attributeName == chandler.companyName and contact.GetContactType() == 'Company':
                    companyName = contact.GetFullName()
                    try:
                        choices.index(companyName)
                    except:
                        choices.append(companyName)
        
        return choices
                
