#!bin/env python

"""Model object representing contact attributes.
"""

__author__ = "Andy Hertzfeld"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

class ContactAttributes(RdfObject):
    """ContactAttributes"""

# many of these strings should really be enumerated types; we'll convert them
# to that when the infrastructure is ready.

    rdfs = PersistentDict()

    rdfs[chandler.companyname] = RdfRestriction(str, 1)
    rdfs[chandler.jobtitle] = RdfRestriction(str, 1)
    rdfs[chandler.occupation] = RdfRestriction(str, 1)
    rdfs[chandler.relationship] = RdfRestriction(str, 1)
    
    rdfs[chandler.age] = RdfRestriction(str, 1)
    rdfs[chandler.birthday] = RdfRestriction(str, 1)
    rdfs[chandler.gender] = RdfRestriction(str, 1)
    
    rdfs[chandler.sharing] = RdfRestriction(str, 1)
    
    rdfs[chandler.project] = RdfRestriction(str, 1)
    rdfs[chandler.status] = RdfRestriction(str, 1)
    rdfs[chandler.topic] = RdfRestriction(str, 1)

    rdfs[chandler.reputation] = RdfRestriction(str, 1)
    rdfs[chandler.interests] = RdfRestriction(str, 1)

    def __init__(self):
        RdfObject.__init__(self)
         
    def GetCompanyName(self):
        return self.getRdfAttribute(chandler.companyname, ContactAttributes.rdfs)
    
    def SetCompanyName(self, companyName):
        self.setRdfAttribute(chandler.companyname, companyName, ContactAttributes.rdfs)
        
    def GetJobTitle(self):
        return self.getRdfAttribute(chandler.jobtitle, ContactAttributes.rdfs)
    
    def SetJobTitle(self, jobTitle):
        self.setRdfAttribute(chandler.jobtitle, jobTitle, ContactAttributes.rdfs)
        
    def GetOccupation(self):
        return self.getRdfAttribute(chandler.occupation, ContactAttributes.rdfs)
    
    def SetOccupation(self, occupation):
        self.setRdfAttribute(chandler.occupation, occupation, ContactAttributes.rdfs)
    
    def GetRelationship(self):
        return self.getRdfAttribute(chandler.relationship, ContactAttributes.rdfs)
    
    def SetRelationship(self, relationship):
        self.setRdfAttribute(chandler.relationship, relationship, ContactAttributes.rdfs)

    def GetAge(self):
        return self.getRdfAttribute(chandler.age, ContactAttributes.rdfs)
    
    def SetAge(self, age):
        self.setRdfAttribute(chandler.age, age, ContactAttributes.rdfs)
    
    def GetBirthday(self):
        return self.getRdfAttribute(chandler.birthday, ContactAttributes.rdfs)
    
    def SetBirthday(self, birthday):
        self.setRdfAttribute(chandler.birthday, birthday, ContactAttributes.rdfs)

    def GetGender(self):
        return self.getRdfAttribute(chandler.gender, ContactAttributes.rdfs)
    
    def SetGender(self, gender):
        self.setRdfAttribute(chandler.gender, gender, ContactAttributes.rdfs)
        
    def GetSharing(self):
        return self.getRdfAttribute(chandler.sharing, ContactAttributes.rdfs)
    
    def SetSharing(self, sharing):
        self.setRdfAttribute(chandler.sharing, sharing, ContactAttributes.rdfs)
        
    def GetProject(self):
        return self.getRdfAttribute(chandler.project, ContactAttributes.rdfs)
    
    def SetProject(self, project):
        self.setRdfAttribute(chandler.project, project, ContactAttributes.rdfs)
    
    def GetStatus(self):
        return self.getRdfAttribute(chandler.status, ContactAttributes.rdfs)
    
    def SetStatus(self, status):
        self.setRdfAttribute(chandler.status, status, ContactAttributes.rdfs)
   
    def GetTopic(self):
        return self.getRdfAttribute(chandler.topic, ContactAttributes.rdfs)
    
    def SetTopic(self, status):
        self.setRdfAttribute(chandler.topic, topic, ContactAttributes.rdfs)
    
    def GetReputation(self):
        return self.getRdfAttribute(chandler.reputation, ContactAttributes.rdfs)
    
    def SetReputation(self, reputation):
        self.setRdfAttribute(chandler.reputation, reputation, ContactAttributes.rdfs)
        
    def GetInterests(self):
        return self.getRdfAttribute(chandler.interests, ContactAttributes.rdfs)
    
    def SetInterests(self, reputation):
        self.setRdfAttribute(chandler.interests, interests, ContactAttributes.rdfs)

    # FIXME:  need to handle all the attributes, but in a more generic way
    def GetAttribute(self, attributeName):
        if attributeName == 'companyname':
            return self.GetCompanyName()
        
        if attributeName == 'jobtitle':
            return self.GetJobTitle()
        
        if attributeName == 'occupation':
            return self.GetOccupation()
        
        if attributeName == 'relationship':
            return self.GetRelationship()
        
        if self.__dict__.has_key(attributeName):
            return self.__dict__[attributeName]
    
    # FIXME:  need to handle all the attributes, but in a more generic way
    def SetAttribute(self, attributeName, attributeValue):
        if attributeName == 'companyname':
            self.SetCompanyName(attributeValue)
        elif attributeName == 'jobtitle':
            self.SetJobTitle(attributeValue)
        elif attributeName == 'occupation':
            self.SetOccupation(attributeValue)
        elif attributeName == 'relationship':
            self.SetRelationship(attributeValue)
        else:
            self.__dict__[attributeName] = attributeValue

    companyname = property(GetCompanyName, SetCompanyName)
    jobtitle = property(GetJobTitle, SetJobTitle)
    occupation = property(GetOccupation, SetOccupation)
    relationship = property(GetRelationship, SetRelationship)
    age = property(GetAge, SetAge)
    birthday = property(GetBirthday, SetBirthday)
    gender = property(GetGender, SetGender)
    sharing = property(GetSharing, SetSharing)
    project = property(GetProject, SetProject)
    status = property(GetStatus, SetStatus)
    topic = property(GetTopic, SetTopic)
    reputation = property(GetReputation, SetReputation)
    interests = property(GetInterests, SetInterests)
    
   
        