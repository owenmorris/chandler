"""
Generate sample items: calendar, contacts, etc.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import random

from mx import DateTime

import OSAF.contentmodel.calendar.Calendar as Calendar
import OSAF.contentmodel.contacts.Contacts as Contacts
import OSAF.contentmodel.mail.Mail as Mail

HEADLINES = ["Dinner", "Lunch", "Meeting", "Movie", "Games"]

DURATIONS = [30, 60, 90, 120, 150, 180]

def GenerateCalendarEvent(days):
    event = Calendar.CalendarEvent()
    event.headline = random.choice(HEADLINES)
    
    # Choose random days, hours
    startDelta = DateTime.DateTimeDelta(random.randint(0, days),
                                        random.randint(0, 24))
    
    event.startTime = DateTime.now() + startDelta
    
    # Choose random minutes
    event.duration = DateTime.DateTimeDelta(0, 0, random.choice(DURATIONS))
    
def GenerateCalendarEvents(count, days):
    """ Generate _count_ events over the next _days_ number of days """
    for index in range(count):
        GenerateCalendarEvent(days)

DOMAIN_LIST = ['aol.com', 'earthlink.net', 'mac.com', 'yahoo.com',
               'hotmail.com', 'mailblocks.com', 'pacbell.net',
               'osafoundation.org']

FIRSTNAMES = ['Aleks', 'Alexis', 'Amy', 'Andi', 'Andy', 'Aparna',
              'Bart', 'Blue', 'Brian', 'Caroline', 'Cedric', 'Chao', 'Chris',
              'Ducky', 'Dulcy', 'Erin', 'Esther',
              'Freada', 'Greg', 'Heikki', 'Hilda',
              'Jed', 'John', 'Jolyn', 'Jurgen', 'Jae Hee',
              'Katie', 'Kevin', 'Lou',
              'Michael', 'Mimi', 'Mitch', 'Mitchell', 'Morgen',
              'Pieter', 'Robin', 'Stefanie', 'Stuart', 'Suzette',
              'Ted', 'Trudy', 'William']

LASTNAMES = ['Anderson', 'Baker', 'Botz', 'Brown', 'Burgess',
             'Capps', 'Cerneka', 'Chang', 'Decker', 'Decrem', 'Desai', 'Dunn',
             'Figueroa', 'Gamble', 'Gravelle',
             'Hartsook', 'Haurnesser', 'Hernandez', 'Hertzfeld', 'Humpa',
             'Kapor', 'Klein', 'Kim', 'Lam', 'Leung', 'McDevitt', 'Montulli',
             'Okimoto', 'Parlante', 'Parmenter', 'Rosa',
             'Sagen', 'Sciabica', 'Sherwood', 'Skinner', 'Sun',
             'Tauber', 'Totic', 'Toivonen', 'Toy', 'Tsurutome', 'Vajda', 'Yin']

PHONETYPES = ['cell', 'voice', 'fax', 'pager']

def GeneratePhoneNumber():
    areaCode = random.randint(201, 799)
    exchange = random.randint(220, 999)
    number = random.randint(1000, 9999)
    return "(%3d) %3d-%4d" % (areaCode, exchange, number)

def GeneratePhoneNumbers():
    list = []
    for i in range(random.randint(1, 3)):
        phone = Contacts.PhoneNumber()
        phone.phoneNumber = GeneratePhoneNumber()
        # phone.phoneType = random.choice(PHONETYPES)
        list.append(phone)
    return list

def GenerateEmailAddress(name):
    domainName = random.choice(DOMAIN_LIST)
    handle = random.choice([name.firstName, name.lastName])
    return "%s@%s" % (handle, domainName)

def GenerateEmailAddresses(name):
    list = []
    for i in range(random.randint(1, 2)):
        email = Mail.EmailAddress()
        email.emailAddress = GenerateEmailAddress(name)
        list.append(email)
    return list

def GenerateContactName():
    name = Contacts.ContactName()
    name.firstName = random.choice(FIRSTNAMES)
    name.lastName = random.choice(LASTNAMES)
    return name

def GenerateContactSection(name):
    section = Contacts.ContactSection()
    section.phoneNumbers = GeneratePhoneNumbers()
    section.emailAddresses = GenerateEmailAddresses(name)
    return section

def GenerateContact():
    contact = Contacts.Contact()
    contact.name = GenerateContactName()
    contact.homeSection = GenerateContactSection(contact.name)
    contact.workSection = GenerateContactSection(contact.name)

def GenerateContacts(count):
    for index in range(count):
        GenerateContact()
        

    
    
