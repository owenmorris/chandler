"""
Generate sample items: calendar, contacts, etc.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import random

from datetime import datetime, timedelta

import osaf.contentmodel.calendar.Calendar as Calendar
from osaf.contentmodel.contacts import Contact, ContactName
import osaf.contentmodel.mail as Mail
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.ItemCollection as ItemCollection

HEADLINES = ["Dinner", "Lunch", "Meeting", "Movie", "Games"]

DURATIONS = [60, 90, 120, 150, 180]

REMINDERS = [None, None, None, None, 1, 10] # The "None"s make only a 30% chance an event will have a reminder...

def GenerateCalendarParticipant(view):
    email = Mail.EmailAddress(view=view)
    domainName = random.choice(DOMAIN_LIST)
    handle = random.choice(LASTNAMES).lower()
    email.emailAddress = "%s@%s" % (handle, domainName)
    return email

IMPORTANCE = ["important", "normal", "fyi"]
LOCATIONS  = ["Home", "Office", "School"]



def GenerateCalendarEvent(view, days=30):
    event = Calendar.CalendarEvent(view=view)
    event.displayName = random.choice(HEADLINES)
    
    # Choose random days, hours
    startDelta = timedelta(days=random.randint(0, days),
                           hours=random.randint(0, 24))

    now = datetime.now()
    closeToNow = datetime(now.year, now.month, now.day, now.hour,
                          int(now.minute/30) * 30)
    event.startTime = closeToNow + startDelta

    # Events are anyTime by default. Give a 5% chance of allDay instead,
    # or 90% of a normal event.
    r = random.randint(0,100)
    if r < 95: # 5% chance that we'll turn anyTime off
        event.anyTime = False
    if r < 5: # 5% chance of allDay
        event.allDay = True

    # Choose random minutes
    event.duration = timedelta(minutes=random.choice(DURATIONS))
    
    # Maybe a nice reminder?
    reminderInterval = random.choice(REMINDERS)
    if reminderInterval is not None:
        event.reminderTime = event.startTime - timedelta(minutes=reminderInterval)
        
    # Add a location to 2/3 of the events
    if random.randrange(3) > 0:
        event.location = Calendar.Location.getLocation(view, random.choice(LOCATIONS))

    event.importance = random.choice(IMPORTANCE)
    return event


TITLES = ["reading list", "restaurant recommendation", "vacation ideas",
          "grocery list", "gift ideas", "life goals", "fantastic recipe",
          "garden plans", "funny joke", "story idea", "poem"]

EVENT, TASK, BOTH = range(2, 5)
M_TEXT  = "This is a test email message"
M_EVENT = " that has been stamped as a Calendar Event"
M_TASK  = " that has been stamped as a Task"
M_BOTH  = " that has been stamped as a Task and a Calendar Event"
M_FROM  = None

def GenerateMailMessage(view):
    global M_FROM
    message  = Mail.MailMessage(view=view)
    body     = M_TEXT

    outbound = random.randint(0, 1)
    type     = random.randint(1, 8)
    numTo    = random.randint(1, 3)

    if M_FROM is None:
        M_FROM = GenerateCalendarParticipant(view)

    message.fromAddress = M_FROM

    for num in range(numTo):
        message.toAddress.append(GenerateCalendarParticipant(view))

    message.subject  = random.choice(TITLES)
    message.dateSent = datetime.now()



    if outbound:
        acc = Mail.getCurrentSMTPAccount(view)[0]
        message.outgoingMessage(acc)

        """Make the Message appear as if it has already been sent"""
        message.deliveryExtension.sendSucceeded()

    else:
        acc = Mail.getCurrentMailAccount(view)
        message.incomingMessage(acc)

    if type == EVENT:
        message.StampKind('add', Calendar.CalendarEventMixin.getKind(message.itsView))
        body += M_EVENT

    if type == TASK:
        message.StampKind('add', Task.TaskMixin.getKind(message.itsView))
        body += M_TASK

    if type == BOTH:
        message.StampKind('add', Task.TaskMixin.getKind(message.itsView))
        message.StampKind('add', Calendar.CalendarEventMixin.getKind(message.itsView))
        body += M_BOTH

    message.body = message.getAttributeAspect('body', 'type').makeValue(body)

    return message

def GenerateNote(view):
    """ Generate one Note item """
    note = Notes.Note(view=view)
    note.displayName = random.choice(TITLES)
    delta = timedelta(days=random.randint(0, 5),
                      hours=random.randint(0, 24))
    note.createdOn = datetime.now() + delta
    return note

def GenerateTask(view):
    """ Generate one Task item """
    task = Task.Task(view=view)
    delta = timedelta(days=random.randint(0, 5),
                      hours=random.randint(0, 24))
    task.dueDate = datetime.today() + delta    
    task.displayName = random.choice(TITLES)
    return task

def GenerateEventTask(view, days=30):
    """ Generate one Task/Event stamped item """
    event = GenerateCalendarEvent(view, days)
    event.StampKind('add', Task.TaskMixin.getKind(event.itsView))
    return event

DOMAIN_LIST = ['flossrecycling.com', 'flossresearch.org', 'rosegardens.org',
               'electricbagpipes.com', 'facelessentity.com', 'example.com',
               'example.org', 'example.net', 'hangarhonchos.org', 'ludditesonline.net']

FIRSTNAMES = ['Alec', 'Aleks', 'Alexis', 'Amy', 'Andi', 'Andy', 'Aparna',
              'Bart', 'Blue', 'Brian', 'Bryan', 'Caroline', 'Cedric', 'Chao', 'Chris',
              'David', 'Donn', 'Ducky', 'Dulcy', 'Erin', 'Esther',
              'Freada', 'Grant', 'Greg', 'Heikki', 'Hilda',
              'Jed', 'John', 'Jolyn', 'Jurgen', 'Jae Hee',
              'Katie', 'Kevin', 'Lisa', 'Lou',
              'Michael', 'Mimi', 'Mitch', 'Mitchell', 'Morgen',
              'Pieter', 'Robin', 'Stefanie', 'Stuart', 'Suzette',
              'Ted', 'Trudy', 'William']

LASTNAMES = ['Anderson', 'Baillie', 'Baker', 'Botz', 'Brown', 'Burgess',
             'Capps', 'Cerneka', 'Chang', 'Decker', 'Decrem', 'Denman', 'Desai', 'Dunn', 'Dusseault',
             'Figueroa', 'Flett', 'Gamble', 'Gravelle',
             'Hartsook', 'Haurnesser', 'Hernandez', 'Hertzfeld', 'Humpa',
             'Kapor', 'Klein', 'Kim', 'Lam', 'Leung', 'McDevitt', 'Montulli', 'Moseley',
             'Okimoto', 'Parlante', 'Parmenter', 'Rosa',
             'Sagen', 'Sciabica', 'Sherwood', 'Skinner', 'Stearns', 'Sun', 'Surovell',
             'Tauber', 'Totic', 'Toivonen', 'Toy', 'Tsurutome', 'Vajda', 'Yin']

COLLECTION_ADJECTIVES = ['Critical', 'Eventual', 'Sundry', 'Ignorable', 'Miscellaneous', 'Fascinating']
COLLECTION_NOUNS = ['Items', 'Scratchings', 'Things', 'Oddments', 'Stuff', 'Dregs', 'Fewmets' ]

PHONETYPES = ['cell', 'voice', 'fax', 'pager']

#area codes not listed as valid at http://www.cs.ucsd.edu/users/bsy/area.html
AREACODES = [311,411,555,611,811,324,335]

def GeneratePhoneNumber():
    areaCode = random.choice(AREACODES)
    exchange = random.randint(220, 999)
    number = random.randint(1000, 9999)
    return "(%3d) %3d-%4d" % (areaCode, exchange, number)

def GenerateEmailAddress(name):
    domainName = random.choice(DOMAIN_LIST)
    handle = random.choice([name.firstName, name.lastName])
    return "%s@%s" % (handle.lower(), domainName)

def GenerateEmailAddresses(view, name):
    list = []
    for i in range(random.randint(1, 2)):
        email = Mail.EmailAddress(view=view)
        email.emailAddress = GenerateEmailAddress(name)
        list.append(email)
    return list

def GenerateContactName(view):
    name = ContactName(view=view)
    name.firstName = random.choice(FIRSTNAMES)
    name.lastName = random.choice(LASTNAMES)
    return name

def GenerateContact(view):
    contact = Contact(view=view)
    contact.contactName = GenerateContactName(view)
    return contact

def GenerateCollection(view, postToView=None, existingNames=None):
    collection = ItemCollection.ItemCollection(view=view)
    
    while True:
        # Find a name that isn't already in use
        potentialName = ' '.join((random.choice(COLLECTION_ADJECTIVES), random.choice(COLLECTION_NOUNS),))
        if existingNames is None or potentialName not in existingNames:
            collection.displayName = potentialName
            if existingNames is not None:
                existingNames.append(potentialName)
            break
        
    if postToView is not None:
        postToView.postEventByName ('AddToSidebarWithoutCopyingOrCommiting', {'items': [ collection ] })
    return collection


def GenerateItems(view, count, function, collections=[], *args, **dict):
    """ 
    Generate 'count' content items using the given function (and args), and
    add them to a subset of the given collections (if given)
    """
    
    # At most, we'll add each item to a third of the collections, if we were given any
    maxCollCount = (len(collections) / 3)
    
    results = []
    for index in range(count):
        newItem = function(view, *args, **dict)
        
        if maxCollCount > 0:
            for index in range(random.randint(1, maxCollCount)):
                collections[random.randint(0, len(collections)-1)].add(newItem)    
            
        results.append(newItem)

    return results

def GenerateAllItems(view, count, mainView=None, sidebarCollection=None):
    """ Generate a bunch of items of several types, for testing. """
    
    # Generate some item collections to put them in.
    existingNames = sidebarCollection is not None and [ existingCollection.displayName for existingCollection in sidebarCollection] or []
    collections = GenerateItems(view, 5, GenerateCollection, [], mainView, existingNames)
    
    for fn in GenerateMailMessage, GenerateNote, GenerateCalendarEvent, GenerateTask, GenerateEventTask: # GenerateContact omitted.
        GenerateItems(view, count, fn, collections)

    view.commit() 
