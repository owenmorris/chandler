"""
Generate sample items: calendar, contacts, etc.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import random

from mx import DateTime

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.contacts.Contacts as Contacts
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.Notes as Notes

HEADLINES = ["Dinner", "Lunch", "Meeting", "Movie", "Games"]

DURATIONS = [60, 90, 120, 150, 180]

REMINDERS = [None, None, 1, 10] # The "None"s make a 50% chance the event will have no reminder...

def GenerateCalendarParticipant():
    email = Mail.EmailAddress()
    domainName = random.choice(DOMAIN_LIST)
    handle = random.choice(LASTNAMES).lower()
    email.emailAddress = "%s@%s" % (handle, domainName)
    return email

IMPORTANCE = ["important", "normal", "fyi"]

def GenerateCalendarEvent(days):
    event = Calendar.CalendarEvent()
    event.displayName = random.choice(HEADLINES)
    
    # Choose random days, hours
    startDelta = DateTime.DateTimeDelta(random.randint(0, days),
                                        random.randint(0, 24))

    now = DateTime.now()
    closeToNow = DateTime.DateTime(now.year, now.month, now.day, now.hour,
                                   int(now.minute/30) * 30)
    event.startTime = closeToNow + startDelta
    
    # Choose random minutes
    event.duration = DateTime.DateTimeDelta(0, 0, random.choice(DURATIONS))
    
    # Maybe a nice reminder?
    reminderInterval = random.choice(REMINDERS)
    if reminderInterval is not None:
        event.reminderTime = event.startTime - DateTime.RelativeDateTime(minutes=reminderInterval)

    event.importance = random.choice(IMPORTANCE)
    return event
    
def generateCalendarEventItems(count, days):
    """ Generate _count_ events over the next _days_ number of days """
    for index in range(count):
        GenerateCalendarEvent(days)

TITLES = ["reading list", "restaurant recommendation", "vacation ideas",
          "grocery list", "gift ideas", "life goals", "fantastic recipe",
          "garden plans", "funny joke", "story idea", "poem"]

def GenerateNote():
    """ Generate one Note item """
    note = Notes.Note()
    note.displayName = random.choice(TITLES)
    delta = DateTime.DateTimeDelta(random.randint(0, 5),
                                   random.randint(0, 24))
    note.createdOn = DateTime.now() + delta
    return note

def GenerateNotes(count):
    """ Generate _count_ notes """
    for index in range(count):
        GenerateNote()

def GenerateTask():
    """ Generate one Task item """
    task = Task.Task()
    delta = DateTime.DateTimeDelta(random.randint(0, 5),
                                   random.randint(0, 24))
    task.dueDate = DateTime.today() + delta    
    task.displayName = random.choice(TITLES)
    return task

def GenerateTasks(count):
    """ Generate _count_ tasks """
    for index in range(count):
        GenerateTask()

def GenerateEventTask():
    """ Generate one Task/Event stamped item """
    event = GenerateCalendarEvent(30)
    event.StampKind('add', Task.TaskMixin.getKind())

def GenerateEventTasks(count):
    for index in range(count):
        GenerateEventTask()

DOMAIN_LIST = ['flossrecycling.com', 'flossresearch.org', 'rosegardens.org',
               'electricbagpipes.com', 'facelessentity.com', 'example.com',
               'example.org', 'example.net', 'hangarhonchos.org']

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

#area codes not listed as valid at http://www.cs.ucsd.edu/users/bsy/area.html
AREACODES = [311,411,555,611,811,324,335]

def GeneratePhoneNumber():
    areaCode = random.choice(AREACODES)
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
    return "%s@%s" % (handle.lower(), domainName)

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


def GenerateContact():
    contact = Contacts.Contact()
    contact.contactName = GenerateContactName()
    return contact

def GenerateContacts(count):
    for index in range(count):
        GenerateContact()
