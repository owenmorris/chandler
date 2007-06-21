#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Generate sample items from a file
"""

import string
import random
import urllib
from datetime import datetime, timedelta
import logging
import osaf.pim.calendar.Calendar as Calendar
from osaf import pim
from osaf.pim.tasks import Task, TaskStamp
import osaf.pim.mail as Mail
import i18n
from i18n.tests import uw
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from application import schema

logger = logging.getLogger(__name__)

collectionsDict={}
TEST_I18N = i18n.getLocaleSet() and 'test' in i18n.getLocaleSet()

STATUS = ["confirmed", "tentative", "fyi"]
RECURRENCES = ["daily", "weekly", "monthly", "yearly"]
TIMEZONES = [u"US/Pacific", u"US/Central", u"Europe/Paris"]
IMPORTANCE = [u"important", u"normal", u"fyi"]
LOCATIONS  = [u"Home", u"Office", u"School"]
HEADLINES = [u"Dinner", u"Lunch", u"Meeting", u"Movie", u"Games"]
DURATIONS = [60, 90, 120, 150, 180]
REMINDERS = [1, 5, 10, 30, 60, 90] # should match the menu!
TITLES = [u"reading list", u"restaurant recommendation", u"vacation ideas",
          u"grocery list", u"gift ideas", u"life goals", u"fantastic recipe",
          u"garden plans", u"funny joke", u"story idea", u"poem"]
COLLECTION_ADJECTIVES = [u'Critical', u'Eventual', u'Sundry', u'Ignorable', u'Miscellaneous', u'Fascinating']
COLLECTION_NOUNS = [u'Items', u'Scratchings', u'Things', u'Oddments', u'Stuff', u'Dregs', u'Fewmets' ]
M_TEXT  = u"This is a test email message"
LASTNAMES = [u'Anderson', u'Baillie', u'Baker', u'Botz', u'Brown', u'Burgess',
             u'Capps', u'Cerneka', u'Chang', u'Decker', u'Decrem', u'Denman', u'Desai', u'Dunn', u'Dusseault',
             u'Figueroa', u'Flett', u'Gamble', u'Gravelle',
             u'Hartsook', u'Haurnesser', u'Hernandez', u'Hertzfeld', u'Humpa',
             u'Kapor', u'Klein', u'Kim', u'Lam', u'Leung', u'McDevitt', u'Montulli', u'Moseley',
             u'Okimoto', u'Parlante', u'Parmenter', u'Rosa',
             u'Sagen', u'Sciabica', u'Sherwood', u'Skinner', u'Stearns', u'Sun', u'Surovell',
             u'Tauber', u'Totic', u'Toivonen', u'Toy', u'Tsurutome', u'Vajda', u'Yin']
DOMAIN_LIST = [u'flossrecycling.com', u'flossresearch.org', u'rosegardens.org',
               u'electricbagpipes.com', u'facelessentity.com', u'example.com',
               u'example.org', u'example.net', u'hangarhonchos.org', u'ludditesonline.net']


def GenerateCollection(view, args):
    """ Generate one Collection Item """
    appNameSpace = schema.ns('osaf.app', view)
    collection = pim.SmartCollection(itsView=view)
    sidebarCollection = appNameSpace.sidebarCollection

    if args[0]=='*': # semi-random data
        while True:
             # Find a name that isn't already in use
             potentialName = ' '.join((random.choice(COLLECTION_ADJECTIVES), random.choice(COLLECTION_NOUNS),))
             if not collectionsDict.has_key(potentialName):
                 collection.displayName = potentialName
                 collectionsDict[potentialName] = collection
                 sidebarCollection.add (collection)
             break
    elif not args[0]=='':
        collection.displayName = u"%s" %args[0]
        if not collectionsDict.has_key(args[0]):
            sidebarCollection.add (collection)
            collectionsDict[args[0]]=collection
    else:
        #default value
        collection.displayName = u'Untitled'
        if not collectionsDict.has_key(u'Untitled'):
            sidebarCollection.add (collection)
            collectionsDict[u'Untitled']=collection
        
    return collection


def GenerateNote(view, args):
    """ Generate one Note item """
    note = pim.Note(itsView=view)
    #displayName
    if args[0]=='*': # semi-random data

        note.displayName = random.choice(TITLES)

    elif not args[0]=='':
         note.displayName = u"%s" %args[0]
    else:
        note.displayName = u'untitled' #default value which does not require localization since this is a util

    if TEST_I18N:
        note.displayName = uw(note.displayName)

    #createdOn
    note.createdOn = ReturnCompleteDatetime(args[2],args[3])
    #collection
    if args[1]=='*': # semi-random data
        collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(note)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';') 
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(note)
            else:
                GenerateCollection(view, [name])
                collectionsDict[name].add(note)

    return note


def GenerateCalendarEvent(view, args):
    """ Generate one calendarEvent item """
    event = Calendar.CalendarEvent(itsView=view)

    # displayName
    if args[0]=='*': # semi-random data
        event.displayName = random.choice(HEADLINES)

    elif not args[0]=='':
        event.displayName = u"%s" %args[0]
    else:
        event.displayName = u'untitled'

    if TEST_I18N:
        event.displayName = uw(event.displayName)

    #startTime (startDate + startTime) + TimeZone
    event.startTime = ReturnCompleteDatetime(view, args[2], args[3],
                                             tz=args[12])
   
    #anyTime
    if args[4]=='*': # semi-random data
        r = random.randint(0,100)
        if r < 95: # 95% chance that we'll turn anyTime off
            event.anyTime = False
        else:
            event.anyTime = True
    elif args[4]=='TRUE' :
        event.anyTime = True
    else:
        event.anyTime = False

    #allDay    
    if args[5]=='*': # semi-random data
        r = random.randint(0,100)
        if r < 5: # 5% chance of allDay
            event.allDay = True
        else:
            event.allDay = False
    elif args[5]=='TRUE' :
        event.allDay = True
    else:
        event.allDay = False

    #duration
    if args[6]=='*': # semi-random data
        event.duration = timedelta(minutes=random.choice(DURATIONS))
    elif not args[6]=='':
        event.duration = timedelta(minutes=string.atoi(args[6]))
    else:
        event.duration = timedelta(minutes=60) #default value 1h

    #reminders
    if not args[7]=='':
        if args[7]=='*': # semi-random data
            reminderInterval = random.choice(REMINDERS)
        else:
            reminderInterval = string.atoi(args[7])
        event.userReminderInterval = timedelta(minutes=-reminderInterval)

    #location
    if args[8]=='*': # semi-random data
        event.location = Calendar.Location.getLocation(view, random.choice(LOCATIONS))

    elif not args[8]=='':
        event.location = Calendar.Location.getLocation(view,u"%s"%args[8])    

    if TEST_I18N:
        event.location = uw(event.location)

    #status (only 3 values allowed : 'Confirmed','Tentative','fyi')
    if args[9]=='*': # semi-random data
        event.transparency = random.choice(STATUS)
    elif string.lower(args[9]) in STATUS:    
        event.transparency = string.lower(args[9])
    else: # default value (normal)
        event.transparency = 'confirmed'
    
    #recurrence ('daily','weekly','monthly','yearly') + recurrence end date
    ruleItem = RecurrenceRule(None, itsView=view)
    ruleSetItem = RecurrenceRuleSet(None, itsView=view)
    if not args[11] == '':
        ruleItem.until = ReturnCompleteDatetime(view, args[11])
    if args[10]=='*': # semi-random data
        ruleItem.freq = random.choice(RECURRENCES)
        ruleSetItem.addRule(ruleItem)
        event.rruleset = ruleSetItem
    elif string.lower(args[10]) in RECURRENCES:
        ruleItem.freq = string.lower(args[10])
        ruleSetItem.addRule(ruleItem)
        event.rruleset = ruleSetItem

    #collection
    if args[1]=='*': # semi-random data
        if not len(collectionsDict) == 0:
            collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(event)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';')
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(event)
            else:
                GenerateCollection(view, [name])
                collectionsDict[name].add(event)

    return event


def GenerateTask(view, args):
    """ Generate one Task item """
    task = Task(itsView=view)

    # displayName
    if args[0]=='*': # semi-random data
        task.displayName = random.choice(TITLES)


    elif not args[0]=='':
        task.displayName = u"%s" %args[0]
    else:
        task.displayName = u'untitled'

    if TEST_I18N:
        task.displayName = uw(task.displayName)


    #collection
    if args[1]=='*': # semi-random data
        collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(task)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';') 
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(task)
            else:
                GenerateCollection(view, [name])
                collectionsDict[name].add(task)

    return task


def ReturnCompleteDatetime(view, date, time='', tz=None):
    """ Return a datetime corresponding to the parameters """
    now = datetime.now()
    # date
    if date=='*': # semi-random data
        # Choose random days, hours
        startDelta = timedelta(days=random.randint(0, 300))
        closeToNow = datetime(now.year, now.month, now.day)
        tmp = closeToNow + startDelta
    elif not date=='':
        d = string.split(date,'/')
        if len(d[2])==2:
            d[2] = '20'+d[2]
        tmp = datetime(month=string.atoi(d[0]),day=string.atoi(d[1]),year=string.atoi(d[2]))
    else:
        tmp = now
    # time    
    if time=='*': # semi-random data
        result = datetime(year=tmp.year,month=tmp.month,day=tmp.day,hour=random.randint(0, 12),minute=random.randint(0, 59))
    elif not time=='':
        t = string.split(time,':')
        if len(t)==2: # hh:mm format
            if t[1][-2:] == 'PM' and not t[0]=='12':
                h = string.atoi(t[0]) + 12
            else: # AM or European time format
                h = string.atoi(t[0])  
            result = datetime(year=tmp.year,month=tmp.month,day=tmp.day,hour=h,minute=string.atoi(t[1]))
        elif len(t)==3: # hh:mm:ss format
            if t[2][-2:] == 'PM' and not t[0]=='12':
                h = string.atoi(t[0]) + 12
            else: #AM or European time format
                h = string.atoi(t[0])
            result = datetime(year=tmp.year,month=tmp.month,day=tmp.day,hour=h,minute=string.atoi(t[1]))
        else: # default value
            result = datetime(year=tmp.year,month=tmp.month,day=tmp.day,hour=now.hour,minute=now.minute)
    else:
        result = datetime(year=tmp.year,month=tmp.month,day=tmp.day,hour=now.hour,minute=now.minute)

    # time zone
    if tz=='*': # semi-random data
        tzinfo = view.tzinfo.getInstance(random.choice(TIMEZONES))
    elif tz in TIMEZONES:
        tzinfo = view.tzinfo.getInstance(tz)
    else: # default value
        tzinfo = view.tzinfo.default
        
    result = datetime(year=result.year,month=result.month,day=result.day,hour=result.hour,minute=result.minute,tzinfo=tzinfo)
    return result


def GenerateEventTask(view, args):
    """ Generate one Task/Event stamped item """
    event = GenerateCalendarEvent(view, args)
    TaskStamp(event).add()
    return event


def GenerateCalendarParticipant(view, emailAddress):
    """ Generate an email address corresponding to the parameters """ 
    if emailAddress == '*': # semi-random data
        domainName = random.choice(DOMAIN_LIST)
        handle = random.choice(LASTNAMES).lower()
        emailAddress = "%s@%s" % (handle, domainName)
    elif emailAddress=='': # default value
        emailAddress = 'Me'

    email = Mail.EmailAddress.getEmailAddress(view, emailAddress)
    return email



def GenerateMailMessage(view, args):
    """ Generate one Mail message item """

    message  = Mail.MailMessage(itsView=view)

    # subject
    if args[0]=='*': # semi-random data
        message.subject = random.choice(TITLES)

    elif not args[0]=='':
        message.subject = u"%s" %args[0]
    else: #default value
        message.subject = u'untitled'

    if TEST_I18N:
        message.subject = uw(message.subject)

    # dateSent (date + time)
    message.dateSent = ReturnCompleteDatetime(view, args[2], args[3])

    # fromAdress
    message.fromAddress = GenerateCalendarParticipant(view, args[4])
    
    # toAddress
    if args[5]=='*':
        for num in range(random.randint(1,3)):
            message.toAddress.append(GenerateCalendarParticipant(view, args[5]))
    elif not args[5]=='':
        addressList = string.split(args[5],';')
        for add in addressList:
            message.toAddress.append(GenerateCalendarParticipant(view, add))
    else: #default value
        message.toAddress.append(GenerateCalendarParticipant(view, 'foo@bar.com'))

    
    # outbound
    smtpAccount = Mail.getCurrentSMTPAccount(view)[0]
    mailAccount = Mail.getCurrentMailAccount(view)
    if args[6]=='*':
        outbound = random.randint(0, 1)
        if outbound:
            message.outgoingMessage(smtpAccount)
            """Make the Message appear as if it has already been sent"""
            message.deliveryExtension.sendSucceeded()
        else:
            message.incomingMessage(mailAccount)
    elif args[6]=='TRUE':
        message.outgoingMessage(smtpAccount)
        """Make the Message appear as if it has already been sent"""
        message.deliveryExtension.sendSucceeded()
    else: # default value "incoming"
        message.incomingMessage(mailAccount)

    # Stamp Event
    if args[7]=='*':
        type = random.randint(0, 1)
        if type:
            Calendar.EventStamp(message).add()
    elif args[7]=='TRUE':
            Calendar.EventStamp(message).add()

    # Stamp Task
    if args[8]=='*':
        type = random.randint(0, 1)
        if type:
            TaskStamp(message).add()
    elif args[8]=='TRUE':
        TaskStamp(message).add()

    # body
    if args[9]=='*':
        message.body = message.getAttributeAspect('body', 'type').makeValue(M_TEXT)
    elif not args[9]=='':
        txt = u"%s"%args[9]
        message.body = message.getAttributeAspect('body', 'type').makeValue(txt)
    else: # default value
        message.body = message.getAttributeAspect('body', 'type').makeValue(M_TEXT)
        
    #collection
    if args[1]=='*': # semi-random data
        if not len(collectionsDict) == 0:
            collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(message)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';') 
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(message)
            else:
                GenerateCollection(view, [name])
                collectionsDict[name].add(message)

    return message


def FindEnd(line,start):
    """ Find the end position of a text field in a csv file"""
    end = string.find(line,'"',start+2)
    if end < (len(line)-1):
        if line[end+1] == '"':
            return FindEnd(line,end)
        else:
            return end
    else:
        return end


def ComaManager(line):
    """ Pre-processing of CSV line """
    result = line[:]
    start = string.find(result,',"')
    while not start==-1:
        end = FindEnd(result,start)   
        # replace "" by " (" in a text field is doubled by the csv export)
        tmp1 = string.replace(result[start+2:end],'""','"')
        # replace caracters by "web code"
        tmp = urllib.quote(tmp1)
        result_tmp = result[:start+1]+tmp
        pos = len(result_tmp) # new end position
        result = result_tmp+result[end+1:]
        
        start = string.find(result,',"',pos)
    return result

        

def GenerateItems(view, filepath):
    """ Generate the Items defined in a csv file """
    if isinstance(filepath, unicode):
        filepath = filepath.encode('utf8')

    try:
        File = open(filepath, 'r')
        try:
            Lines = File.readlines()
        finally:
            File.close()
    except IOError:
        logger.error("Unable to open file %s" % filepath)
        return

    lineNum = 0
    for Line in Lines:
        lineNum = lineNum + 1
        Line = ComaManager(string.strip(Line)) # pre-processing of CSV line + withespace removing a the left, rigth
        args = string.split(Line, ',') # [:-1] remove the \n caracter
        for i in range(len(args)):
            args[i] = urllib.unquote(args[i]) # replace 'web-code' by the corresponding caracter
    
            
        if (string.upper(args[0])=='COLLECTION'):
            try:
                test = args[1]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateCollection(view, args[1:2])
        elif (string.upper(args[0])=='NOTE'):
            try:
                test = args[4]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateNote(view, args[1:5])
        elif (string.upper(args[0])=='CALENDAREVENT'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateCalendarEvent(view, args[1:14])
        elif(string.upper(args[0])=='TASK'):
            try:
                test = args[4]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateTask(view, args[1:5])
        elif(string.upper(args[0])=='EVENTTASK'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateEventTask(view, args[1:14])
        elif(string.upper(args[0])=='MAILMESSAGE'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateMailMessage(view, args[1:11])
                
    File.close()
    view.commit()
