#!bin/env python

"""
The ContactsTest class contains test routines for the Contacts parcel, including
routines to generate lots of sample contacts
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import string
import os
import xml.sax.handler

from wxPython.wx import *
import random

from parcels.OSAF.contacts.ContactsModel import *

from application.repository.Namespace import chandler
from application.repository.Repository import Repository

from application.repository.Contact import Contact

NAME_FILE = "names.txt"

class ContactsTest:
    def __init__(self, contactView):
        self.contactView = contactView

        self.firstnames = []
        self.lastnames = []
        self.LoadNames()
        self.domainList = ['random', 'aol.com', 'earthlink.net', 'mac.com', 'yahoo.com', 'hotmail.com', 'mailblocks.com', 'pacbell.net']
        self.domainSuffixes = ['com', 'org']
        self.groups = ['', '', 'Friends', 'Family', 'Coworkers']
        
    # load the name data from a file
    def LoadNames(self):
        namePath = self.contactView.contactMetaData.basePath + os.sep + 'resources/' + NAME_FILE
        nameFile = open(namePath)
        isFirstName = true
        for nameline in nameFile.readlines():
            if nameline.startswith('--'):
                isFirstName = false
            else:
                result = nameline.strip().capitalize()

            if isFirstName:
                self.firstnames.append(result)
            else:
                self.lastnames.append(result)

        nameFile.close()
        
    # generate a random firstname and last name and return them in a list
    def GenerateName(self):
        suffixes = ['man', 'son', 'smith', 'berg']

        first = random.choice(self.firstnames)
        last = random.choice(self.lastnames)

        # there are a number of different modes to derive last names
        lastnameMode = random.randint(0, 8)
        if lastnameMode < 2:
            last = random.choice(self.firstnames)
        elif lastnameMode == 2:
            last = random.choice(self.firstnames) + suffixes[random.randint(0, 3)]			
        elif lastnameMode == 3:
            last = last + suffixes[random.randint(0, 3)]			
                
        return [first, last]
        
    # add some random addresses to the contact
    def GeneratePhoneNumber(self):
        areaCode = random.randint(201,799)
        exchange = random.randint(220,999)
        number = random.randint(1000,9999)
        return "(%3d) %3d-%4d" % (areaCode, exchange, number)
 
    def GenerateEmailAddress(self, firstName):
        domainName = random.choice(self.domainList)
        if domainName == 'random':
            prefix = random.choice(self.firstnames)
            suffix = random.choice(self.domainSuffixes)
            domainName = prefix + '.' + suffix
        return firstName + '@' + domainName
    
    def AddAddresses(self, contact, firstName):
        phoneNumber = self.GeneratePhoneNumber()
        contactMethod = contact.AddAddress("phone", "Home Phone")		
        contactMethod.SetAttribute(chandler.phonenumber, phoneNumber)
        
        phoneNumber = self.GeneratePhoneNumber()
        contactMethod = contact.AddAddress("phone", "Work Phone")
        contactMethod.SetAttribute(chandler.phonenumber, phoneNumber)
        
        emailAddress = self.GenerateEmailAddress(firstName)
        contactMethod = contact.AddAddress("email", "Main Email")
        contactMethod.SetAttribute(chandler.emailAddress, emailAddress)
 
        # display the sharing policy
        contact.SetBodyAttributes([chandler.sharing])

    def GenerateContact(self):
        # make a new contact
        newContact = Contact('Person')		
                
        # generate a name
        contactName = self.GenerateName()
        newContact.SetNameAttribute(chandler.firstname, contactName[0])
        newContact.SetNameAttribute(chandler.lastname, contactName[1])
                
        # generate some addresses and attributes
        self.AddAddresses(newContact, contactName[0])               
        
        # add it to a random group
        group = random.choice(self.groups)
        if len(group) > 0:
            newContact.AddGroup(group)
            
        return newContact
    
    def GenerateContacts(self, count):
        currentCount = count
        repository = Repository()
        while (currentCount > 0):
            contact = self.GenerateContact()
            repository.thingList.append(contact)          
            currentCount -= 1
                        
        self.contactView.contactList = self.contactView.QueryContacts()
        repository.Commit()
        