#!bin/env python

"""EntityItem, common subclass for PersonItem, OrganizationItem, GroupItem
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from InformationItem import InformationItem
from EmailAddress import EmailAddress
from Address import Address
from PlaceItem import PlaceItem

from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler

class EntityItem(InformationItem):
    """EntityItem"""

    rdfs = Persist.Dict()
    
    rdfs[chandler.name] = RdfRestriction(InformationItem, 1) #Name
    rdfs[chandler.place] = RdfRestriction(PlaceItem) #PlaceItem
    rdfs[chandler.email] = RdfRestriction(EmailAddress)
    rdfs[chandler.phone] = RdfRestriction(InformationItem) #PhoneService
    rdfs[chandler.im] = RdfRestriction(InformationItem) #IMAddress
    rdfs[chandler.image] = RdfRestriction(InformationItem) #Image
    rdfs[chandler.notes] = RdfRestriction(str)
    rdfs[chandler.status] = RdfRestriction(str)

    def __init__(self):
        InformationItem.__init__(self)

    def getName(self):
        pass
    
    def setName(self, name):
        pass

    def getPlaces(self):
        pass

    def setPlaces(self, placeList):
        pass

    def getEmailAddresses(self):
        pass

    def setEmailAddresses(self, emailList):
        pass

    def getPhones(self):
        pass

    def setPhones(self, phoneList):
        pass

    def getIMAddresses(self):
        pass

    def setIMAddresses(self, addressList):
        pass

    def getImages(self):
        pass

    def setImages(self, imageList):
        pass

    def getNotes(self):
        pass

    def setNotes(self, noteList):
        pass

    def getStatus(self):
        pass

    def setStatus(self, status):
        pass
    
    name = property(getName, setName)

    places = property(getPlaces, setPlaces)

    emailAddresses = property(getEmailAddresses, setEmailAddresses)

    phones = property(getPhones, setPhones)

    imAddresses = property(getIMAddresses, setIMAddresses)

    images = property(getImages, setImages)

    notes = property(getNotes, setNotes)

    status = property(getStatus, setStatus)

