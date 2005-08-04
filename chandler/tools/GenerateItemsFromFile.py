"""
Generate sample items from a file
"""


import string
import random
import urllib
from datetime import datetime, timedelta
import logging
import application.Globals as Globals
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.Notes as Notes
from osaf.contentmodel.tasks import Task, TaskMixin
import osaf.contentmodel.mail as Mail

logger = logging.getLogger('Data loading Script')
logger.setLevel(logging.INFO)

collectionsDict={}

IMPORTANCE = ["important", "normal", "fyi"]
LOCATIONS  = ["Home", "Office", "School"]
HEADLINES = ["Dinner", "Lunch", "Meeting", "Movie", "Games"]
DURATIONS = [60, 90, 120, 150, 180]
REMINDERS = [1, 10, 20, 30, 40]
TITLES = ["reading list", "restaurant recommendation", "vacation ideas",
          "grocery list", "gift ideas", "life goals", "fantastic recipe",
          "garden plans", "funny joke", "story idea", "poem"]
COLLECTION_ADJECTIVES = ['Critical', 'Eventual', 'Sundry', 'Ignorable', 'Miscellaneous', 'Fascinating']
COLLECTION_NOUNS = ['Items', 'Scratchings', 'Things', 'Oddments', 'Stuff', 'Dregs', 'Fewmets' ]
M_TEXT  = "This is a test email message"
LASTNAMES = ['Anderson', 'Baillie', 'Baker', 'Botz', 'Brown', 'Burgess',
             'Capps', 'Cerneka', 'Chang', 'Decker', 'Decrem', 'Denman', 'Desai', 'Dunn', 'Dusseault',
             'Figueroa', 'Flett', 'Gamble', 'Gravelle',
             'Hartsook', 'Haurnesser', 'Hernandez', 'Hertzfeld', 'Humpa',
             'Kapor', 'Klein', 'Kim', 'Lam', 'Leung', 'McDevitt', 'Montulli', 'Moseley',
             'Okimoto', 'Parlante', 'Parmenter', 'Rosa',
             'Sagen', 'Sciabica', 'Sherwood', 'Skinner', 'Stearns', 'Sun', 'Surovell',
             'Tauber', 'Totic', 'Toivonen', 'Toy', 'Tsurutome', 'Vajda', 'Yin']
DOMAIN_LIST = ['flossrecycling.com', 'flossresearch.org', 'rosegardens.org',
               'electricbagpipes.com', 'facelessentity.com', 'example.com',
               'example.org', 'example.net', 'hangarhonchos.org', 'ludditesonline.net']


def GenerateCollection(view, mainView, args):
    """ Generate one Collection Item """
    collection = ItemCollection.ItemCollection(view=view)
    
    args[0]=args[0]
    if args[0]=='*': # semi-random data
        while True:
             # Find a name that isn't already in use
             potentialName = ' '.join((random.choice(COLLECTION_ADJECTIVES), random.choice(COLLECTION_NOUNS),))
             if not collectionsDict.has_key(potentialName):
                 collection.displayName = potentialName
                 collectionsDict[potentialName] = collection
                 mainView.postEventByName ('AddToSidebarWithoutCopyingOrCommiting', {'items': [ collection ] })
             break
    elif not args[0]=='':
        collection.displayName = args[0]
        if not collectionsDict.has_key(args[0]):
            mainView.postEventByName ('AddToSidebarWithoutCopyingOrCommiting', {'items': [ collection ] })
            collectionsDict[args[0]]=collection
    else:
        #default value
        collection.displayName = 'Untitled'
        if not collectionsDict.has_key('Untitled'):
            mainView.postEventByName ('AddToSidebarWithoutCopyingOrCommiting', {'items': [ collection ] })
            collectionsDict['Untitled']=collection
        
    return collection


def GenerateNote(view, mainView, args):
    """ Generate one Note item """
    note = Notes.Note(view=view)
    #displayName
    if args[0]=='*': # semi-random data
        note.displayName = random.choice(TITLES)
    elif not args[0]=='':
         note.displayName = args[0]
    else:
        note.displayName = 'untitled' #default value
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
                GenerateCollection(view, mainView, [name])
                collectionsDict[name].add(note)
            
    return note

    
def GenerateCalendarEvent(view, mainView, args):
    """ Generate one calendarEvent item """
    event = Calendar.CalendarEvent(view=view)

    # displayName
    if args[0]=='*': # semi-random data
        event.displayName = random.choice(HEADLINES)
    elif not args[0]=='':
        event.displayName = args[0]
    else:
        event.displayName = 'untitled'
        
    #startTime (startDate + startTime)
    event.startTime = ReturnCompleteDatetime(args[2],args[3])
   
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
        
    #reminderTime
    if args[7]=='*': # semi-random data
        reminderInterval = random.choice(REMINDERS)
        event.reminderTime = event.startTime - timedelta(minutes=reminderInterval)
    elif not args[7]=='':
        reminderTime = string.split(args[7],'/')
        event.reminderTime = datetime(month=string.atoi(reminderTime[0]),day=string.atoi(reminderTime[1]),year=string.atoi(reminderTime[2]))
        
    #location
    if args[8]=='*': # semi-random data
        event.location = Calendar.Location.getLocation(view, random.choice(LOCATIONS))
    elif not args[8]=='':
        event.location = Calendar.Location.getLocation(view,args[8])    

    #importance (only 3 values allowed : 'normal','important','fdy')
    if args[9]=='*': # semi-random data
        event.importance = random.choice(IMPORTANCE)
    elif args[9]=='normal' or args[9]=='important' or args[9]=='fdy':    
        event.importance = args[9]
    else: # default value (normal)
        event.importance = 'normal'

    #collection
    if args[1]=='*': # semi-random data
        collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(event)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';')
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(event)
            else:
                GenerateCollection(view, mainView, [name])
                collectionsDict[name].add(event)

    return event


def GenerateTask(view, mainView, args):
    """ Generate one Task item """
    task = Task(view=view)

    # displayName
    if args[0]=='*': # semi-random data
        task.displayName = random.choice(TITLES)
    elif not args[0]=='':
        task.displayName = args[0]
    else:
        task.displayName = 'untitled'
        
    #dueDate
    task.dueDate = ReturnCompleteDatetime(args[2],args[3])
    
    #collection
    if args[1]=='*': # semi-random data
        collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(task)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';') 
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(task)
            else:
                GenerateCollection(view, mainView, [name])
                collectionsDict[name].add(task)

    return task


def ReturnCompleteDatetime(date, time):
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

    return result


def GenerateEventTask(view, mainView, args):
    """ Generate one Task/Event stamped item """
    event = GenerateCalendarEvent(view, mainView, args)
    event.StampKind('add', TaskMixin.getKind(event.itsView))
    return event


def GenerateCalendarParticipant(view, emailAddress):
    """ Generate an email address corresponding to the parameters """ 
    email = Mail.EmailAddress(view=view)
    if emailAddress=='*': # semi-random data
        domainName = random.choice(DOMAIN_LIST)
        handle = random.choice(LASTNAMES).lower()
        email.emailAddress = "%s@%s" % (handle, domainName)
    elif not emailAddress=='': 
        email.emailAddress = emailAddress
    else: # default value
        email.emailAddress = 'Me'

    return email



def GenerateMailMessage(view, mainView, args):
    """ Generate one Mail message item """
    
    message  = Mail.MailMessage(view=view)

    # subject
    if args[0]=='*': # semi-random data
        message.subject = random.choice(TITLES)
    elif not args[0]=='':
        message.subject = args[0]
    else: #default value
        message.subject = 'untitled' 

    # dateSent (date + time)
    message.dateSent = ReturnCompleteDatetime(args[2],args[3])
    
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
            message.StampKind('add', Calendar.CalendarEventMixin.getKind(message.itsView))
    elif args[7]=='TRUE':
        message.StampKind('add', Calendar.CalendarEventMixin.getKind(message.itsView))

    # Stamp Task
    if args[8]=='*':
        type = random.randint(0, 1)
        if type:
            message.StampKind('add', TaskMixin.getKind(message.itsView))
    elif args[8]=='TRUE':
        message.StampKind('add', TaskMixin.getKind(message.itsView))

    # body
    if args[9]=='*':
        message.body = message.getAttributeAspect('body', 'type').makeValue(M_TEXT)
    elif not args[9]=='':
        message.body = message.getAttributeAspect('body', 'type').makeValue(args[9])
    else: # default value
        message.body = message.getAttributeAspect('body', 'type').makeValue(M_TEXT)
        
    #collection
    if args[1]=='*': # semi-random data
        collectionsDict.values()[random.randint(0,len(collectionsDict)-1)].add(message)
    elif not args[1]=='':
        collectionNames = string.split(args[1], ';') 
        for name in collectionNames:
            if collectionsDict.has_key(name):
                collectionsDict[name].add(message)
            else:
                GenerateCollection(view, mainView, [name])
                collectionsDict[name].add(message)

    return message



def RunScript(view, mainView):
    """ Run this script (command line invocation) """
    if Globals.options.createData:
        filepath = Globals.options.createData
        GenerateItems(view, mainView, filepath)
        Globals.options.createData = None


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

        

def GenerateItems(view, mainView, filepath):
    """ Generate the Items defined in a csv file """
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
                GenerateCollection(view, mainView, args[1:2])
        elif (string.upper(args[0])=='NOTE'):
            try:
                test = args[4]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateNote(view, mainView, args[1:5])
        elif (string.upper(args[0])=='CALENDAREVENT'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateCalendarEvent(view, mainView, args[1:11])
        elif(string.upper(args[0])=='TASK'):
            try:
                test = args[4]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateTask(view, mainView, args[1:5])
        elif(string.upper(args[0])=='EVENTTASK'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateEventTask(view, mainView, args[1:11])
        elif(string.upper(args[0])=='MAILMESSAGE'):
            try:
                test = args[10]
            except IndexError:
                logger.info("(Line skipped): Line %d of %s don't respect the chandler data format." % (lineNum, filepath))
            else:
                GenerateMailMessage(view, mainView, args[1:11])
                
    File.close()
    view.commit()
