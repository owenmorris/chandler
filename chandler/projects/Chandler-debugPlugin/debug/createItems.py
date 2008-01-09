# -*- coding: utf-8 -*-
#   Copyright (c) 2008 Open Source Applications Foundation
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


import random
import osaf.pim.calendar.Calendar as Calendar
from osaf import pim 
from datetime import datetime, timedelta, date, time
from application import schema
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from osaf.framework.blocks.Block import Block
import osaf.pim.mail as Mail
import os  
from dateutil.relativedelta import relativedelta
import wx 
import codecs

if bool(wx.GetApp()): 
    import tools.QAUITestAppLib as QAUITestAppLib #import only if we really have a Chandler window
    inTest = False 
else:
    from chandlerdb.persistence.RepositoryView import NullRepositoryView #import for tests
    inTest = True


firstNames = ['Aleks', 'Alec', 'Andi', 'Andy', 'Anthony', 'Aparna', 'Berook', 
              'Bobby', 'Brian', 'Brian', 'Bryan', 'Chao', 'Chris', 'Dan', 'Dave', 
              'David', 'Donn', 'Ducky', 'Ed', 'Esther', 'Grant', 'Heikki', 'Jared', 
              'Jed', 'Jeffrey', 'John', 'John', u'J\xfcrgen', 'Katie', 'Lisa', 
              'Lori', 'Lou', 'Markku', 'Matthew', 'Michael', 'Mikeal', 'Mike', 'Mimi', 
              'Mitch', 'Mitchell', 'Morgen', 'Pieter', 'Philippe', 'Phillip', 'Priscilla', 
              'Randy', 'Reid', 'Robin', 'Sheila', 'Stuart', 'Suzette', 'Ted', 'Travis']
lastNames = ['Totic', 'Flett', 'Vajda', 'Hertzfeld', 'Franco', 'Kadakia', 'Alemayehu', 
             'Rullo', 'Kirsch', 'Moseley', 'Stearns', 'Lam', 'Haumesser', 'Steinicke', 
             'Cowen', 'Surovell', 'Denman', 'Sherwood', 'Bindl', 'Sun', 'Baillie', 
             'Toivonen', 'Rhine', 'Burgess', 'Harris', 'Anderson', 'Townsend', 'Botz', 
             'Parlante', 'Dusseault', 'Motko', 'Montulli', 'Mielityinen', 'Eernisse', 
             'Toy', 'Rogers', 'Taylor', 'Yin', 'Kapor', 'Baker', 'Sagen', 'Hartsook', 
             'Bossut', 'Eby', 'Chung', 'Letness', 'Ellis', 'Dunn', 'Mooney', 'Parmenter', 
             'Tauber', 'Leung', 'Vachon']
domainList = [u'flossrecycling.com', u'flossresearch.org', u'rosegardens.org',
               u'electricbagpipes.com', u'facelessentity.com', u'example.com',
               u'example.org', u'example.net', u'hangarhonchos.org', u'ludditesonline.net']

fruit = {'apples':20, 'oranges':15, 'banana':25}

def percentsToCount(total, percents, randomize=False):
    """
    Given total as an int or a range and percents as a dictionary of 
    named percentages {'events':50, 'tasks':25, 'mail':25} returns a dictionary 
    of named ranges, {'events:[0,1,2,3,4,5,6,7,8,9], 'tasks':[10,11,12,13,14], 'mail':[15,16,17,18,19]}
    @param total the number of items to be in returned dictionary
    @type total can be an integer or a range 
    @param percents = a dictionary of range names and int representing percentage of total for each range
    @randomize bool randomly swaps indexes between returned ranges if true
    
    >>> fruit = {'apples':20, 'oranges':15, 'banana':25}
    >>> percentsToCount(20, fruit)
    {'apples': [0, 1, 2, 3], 'oranges': [4, 5, 6], 'banana': [7, 8, 9, 10, 11]}
    >>> percentsToCount([0,1,2,3,4,5,6,7,8,9] fruit)
    {'apples': [0, 1], 'oranges': [2], 'banana': [3, 4]}
    >>> fruit={'apples':50, 'oranges':25, 'banana':25}
    >>> percentsToCount(20, fruit)
    {'apples': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'oranges': [10, 11, 12, 13, 14], 'banana': [15, 16, 17, 18, 19]}
    >>> fruit={'apples':50, 'oranges':50, 'banana':50}
    >>> percentsToCount(30, fruit)
    {'apples': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], 'oranges': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29], 'banana': [30, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]}
    >>> 
    """
    #total can be a int or a range, make adjustments accordingly
    if type(total) == type([]):
        if len(total) == 0:
            rangeIndex = 0
            total = 0
        else:
            rangeIndex = min(total) #set returned range to start at bottom of passed in range
            total = len(total)
    else:
        rangeIndex =  0

    #assign values to percentages 
    counts = {}
    for name, percent in percents.iteritems():
        counts[name] = (percent * total) / 100

    if sum(percents.values()) == 100:
        #distribute remaining to largest percentages first
        roundingError = total - sum(counts.itervalues())
        if roundingError > 0:
            second = lambda x: x[1]
            sortedTuples = sorted(counts.iteritems(), key=second, reverse=True)
            highestIndex = len(sortedTuples) - 1
            for i in xrange(roundingError):
                # in some cases i can be > len(sortedTuples) so use modulo to ensure i !> len(sortedTuples)
                if i > highestIndex:
                    key, value = sortedTuples[i%highestIndex]
                else:
                    key, value = sortedTuples[i]
                counts[key] = value + 1
        assert sum(counts.values()) == total

    #convert counts into ranges
    ranges = mkRanges(rangeIndex, (total + rangeIndex) -1, counts)
    
    if randomize is True: ranges = randomizeDict(ranges)
    
    return ranges

def mkRanges (lowestIndex, highestIndex, countDict):
    """ @lowestIndex = int
        @highestIndex = int
        @countDict = dict of named counts ie, {'apples':20, 'oranges':15, 'banana':25}
        returns a dict of named ranges all within lowest and highest indexes

    """
    index = lowestIndex
    ranges = {}
    for name, count in countDict.iteritems():
        tmpRange = []
        counter = 0
        while counter < count:
            tmpRange.append(index)
            counter += 1
            index += 1
            if index > highestIndex: 
                index = lowestIndex
        ranges[name] = tmpRange[:]
    return ranges 

def randomizeDict(dictToRandomize):
    """randomly distribute the indexes in a percentage dict
    
       example {'a':[1,2,3], 'b':[4,5,6], 'c':[7,8,9]}
            becomes something like
            {'a':[5,2,7], 'b':[4,9,3], 'c':[6,8,1]
    """
    allIndexes = []
    valueLengths = {}
    for key, value in dictToRandomize.iteritems():
        allIndexes += value
        valueLengths[key] = len(value)
    random.shuffle(allIndexes)
    dictToRandomize = {}
    startIndex = 0
    for key, length in valueLengths.iteritems():
        endIndex = startIndex + length
        dictToRandomize[key] = allIndexes[startIndex: endIndex]
        startIndex = endIndex
    return dictToRandomize 
    

def createDurationIndex(durationText, indexes):
    """ indexes are indexes to items that can have durations
    durationText is what the user types in dialog box duration field:
    h.m:p
    where h = integer representing hours of duration
          m = integer representing minutes of duration
          p = percent of events to use that duration
    multiple specs can be entered by separating them with a comma   
    so making 20% of the events have duration of 10 minutes and 80% 
    of the events have a duration of 2 hours would look like this:
    0.10:20, 2.0:80 
    return value is a dictionary where the key is the items index and 
    the value is its duration is a timedelta object representing the duration
    
    >>> createDurationIndex('1.1:100',[0,1,2,3,4,5,6,7,8,9])
    {0: datetime.timedelta(0, 3660), 1: datetime.timedelta(0, 3660), 2: datetime.timedelta(0, 3660), 3: datetime.timedelta(0, 3660), 4: datetime.timedelta(0, 3660), 5: datetime.timedelta(0, 3660), 6: datetime.timedelta(0, 3660), 7: datetime.timedelta(0, 3660), 8: datetime.timedelta(0, 3660), 9: datetime.timedelta(0, 3660)}
    >>> createDurationIndex('3.0:30, 0.3:30, 9.59:40',[0,1,2,3,4,5,6,7,8,9])
    {0: datetime.timedelta(0, 35940), 1: datetime.timedelta(0, 10800), 2: datetime.timedelta(0, 180), 3: datetime.timedelta(0, 35940), 4: datetime.timedelta(0, 35940), 5: datetime.timedelta(0, 180), 6: datetime.timedelta(0, 180), 7: datetime.timedelta(0, 10800), 8: datetime.timedelta(0, 35940), 9: datetime.timedelta(0, 10800)}
    >>> 
    """
    percentToCreate = {}
    for spec in durationText.split(','):
        duration, prc = spec.split(':')
        percentToCreate[duration] = int(prc)
    returnDict = percentsToAssignments(percentsToCount(indexes, percentToCreate, randomize=True))
    for index,value in returnDict.iteritems():
        h, m = value.split('.')
        returnDict[index] = timedelta(hours=int(h)) + timedelta(minutes=int(m))
    return returnDict

def createMembershipIndex(membershipText, indexes):
    """ indexes = list of int indexes to all items 
        membershipText = string list of comma separated membership specs
        in the form of "c:p" where c is the number of collections an item should 
        have membership in, and p is the percentatage of items to use that rule.
        Returns a dictionary where the keys are item indexes and the values are the
        number of collections that item should have membership in.
    """
    precentToCreate = {}
    membershipDict = {}
    for spec in membershipText.split(','):
        collectionNumber, percent = spec.split(':')
        precentToCreate[spec] = int(percent)
        membershipDict[spec] = int(collectionNumber)
    returnDict = percentsToAssignments(percentsToCount(indexes, precentToCreate, randomize=True))
    for index, value in returnDict.iteritems():
        returnDict[index] = membershipDict[value]
    return returnDict

def createEndDateIndex(endDateText, indexes):
    """ indexes = list of int indexes to items with recurrence
        endDateText = string list of comma separated end date specs
        in the form of "e:p" where e is the number of times the event should recur before the 
        end date, and p is the percent of items that should have this end date
        Returns a dictionary with the keys being indexes to events with end dates and the values
        a integer that represents how many time the item should recur before the end date
    """
    precentToCreate = {}
    endDateDict = {}
    for spec in endDateText.split(','):
        endDate, percent = spec.split(':')
        precentToCreate[spec] = int(percent)
        endDateDict[spec] = int(endDate)
    returnDict = percentsToAssignments(percentsToCount(indexes, precentToCreate, randomize=True))
    for index, value in returnDict.iteritems():
        returnDict[index] = endDateDict[value]
    return returnDict

def calcEndDate(beginDate, numOfOccurrences, recurFreq):
    """Takes beginDate and adds (numOfOccurrences * recurFreq)
    to produce an end date"""
    frequencies = {'daily':('days=',1),'weekly':('weeks=',1),'biweekly':('weeks=',2),'monthly':('months=',1), 'yearly':('years=',1)}
    timeUnit, multiplier = frequencies[recurFreq]
    exec('delta = relativedelta(' + timeUnit + str(numOfOccurrences * multiplier) + ')')
    return beginDate + delta 

def createDateRange(startDate, endDate, interval=timedelta(days=1)):
    """returns a list of datetime objects for all the intervals between the dates"""
    tmpDate = startDate
    dateRange = []
    while tmpDate <= endDate:
        dateRange.append(tmpDate)
        tmpDate += interval
    return dateRange

def createAlarmIndex(alarmText, eventIndexes, allIndexes, tzinfo):
    """given alarmText from dialog and valid item indexes to apply it to 
    produces a index of alarm values to use.  Alarm times are:
    a comma separated list specs in the form of th.m:p ( type Hour.minute:percent) 
    valid types are
      b = before time (applicable only to events)
      a = after time  (applicable only to events)
      c = custom      (applicable to all item types)
    hour/ minutes for b & a types are integers (number of hours/minutes before/after alarm) 
                  for c type hour must < 24 and minute < 60 (an actual time of day)
    percent to use is an integer greater than zero and less than 100
    relative reminders can only work with event items
    absolute reminders can work with any type of item so two dictionaries are built and returned"""
    relPercentDict = {} 
    absPercentDict = {}
    alarmSpecs = {} 
    alarmText = alarmText.replace(' ','')
    for spec in alarmText.split(','):
        key, value = spec.split(':')
        if key[:1] == 'c':
            absPercentDict[key] = int(value)
        else:
            relPercentDict[key] = int(value)
        try:
            alarmType = spec[:1] 
            alarmHours = int(spec[1:].split('.')[0]) 
            alarmMinutes = int(spec[1:].split('.')[1].split(':')[0]) 
            percent = int(spec.split(':')[1])  
        except:
            print 'ERROR unable to parse alarm spec ,' , spec 
        if alarmType == 'b' : 
            alarmSpecs[spec.split(':')[0]] = (timedelta(minutes=alarmMinutes) + timedelta(hours=alarmHours)) * -1 #before alarms are negative
        elif alarmType == 'a':
            alarmSpecs[spec.split(':')[0]] = timedelta(minutes=alarmMinutes) + timedelta(hours=alarmHours)
        elif alarmType == 'c':
            alarmSpecs[spec.split(':')[0]] = time(alarmHours, alarmMinutes, 0, 0, tzinfo)
            
    relAlarmIndex = percentsToAssignments(percentsToCount(eventIndexes, relPercentDict))
    absAlarmIndex = percentsToAssignments(percentsToCount(allIndexes, absPercentDict))
    for index, spec in relAlarmIndex.iteritems():
        relAlarmIndex[index] = alarmSpecs[spec]
    for index, spec in absAlarmIndex.iteritems():
        absAlarmIndex[index] = alarmSpecs[spec]
    return relAlarmIndex, absAlarmIndex
    

def rangeName(i, rangeDict):
    """i= int range index, rangeDict=dict of names ranges"""
    for name, domain in rangeDict.iteritems():
        if i in domain: return name 
        
def createStartTimeRange(text2Parse, eventIndexes):
    """produce start time range from values entered in dialog
    user enters time range as startHour-endHour:percentOfEventsInThisRange ie, 8-17:30 
    eventIndexes is a list of indexes that point to events
    returns a dictionary where the keys are the indexes and the values are a list of 
    start times"""
    startTimeDict = {} 
    if text2Parse == '': #if no time range given spread the events over the full 24 hours
        startTimeDict = {'1-23':range(0,24)}
        startTimes = percentsToCount(eventIndexes,{'0-23':100})
    else:
        percentDict = {}
        for x in text2Parse.split(','):
            rg, prc = x.split(':')
            startRange, endRange = rg.split('-')
            startTimeDict[rg] = range(int(startRange), int(endRange) + 1)
            percentDict[rg] = int(prc)
        startTimes = percentsToCount(eventIndexes,percentDict, randomize=True)
    result = {}
    for name, indexList in startTimes.iteritems():
        for index in indexList:
            result[index] = startTimeDict[name]
    return result
    
def percentsToAssignments(percentDict):
    """Changes a percentDict as returned by percentsToCount 
    example: {'events:[0,1,2,3,4,5,6,7,8,9], 'tasks':[10,11,12,13,14], 'mail':[15,16,17,18,19]}
    to a dictionary where the index is the key and the name is the value for easier lookups using the index
    {0:'event',1:'event',2:'event'..... 18:'mail',19:'mail'} """
    result = {}
    for name, indexList in percentDict.iteritems():
        for index in indexList:
            result[index] = name 
    return result 

def createAddressIndex(indexRange, text2Parse, addresses):
    """ @indexRange = list of int, a range of indexes to use
        @text2Parse = string, in the form of comma separated specs: count_of_addresses:percentage
        @addresses = list of strings, email addresses to use
        return a dictionary where each index (key) is associated with the proper number of addresses
    """
    def createAddressList(num, addresses):
        out = []
        for i in range(num):
            out.append(random.choice(addresses))
        return out[:]
    
    percentDict = {}
    countDict = {}
    for spec in text2Parse.split(','):
        spec = spec.replace(' ','') 
        count, percent = spec.split(':')
        percentDict[spec] = int(percent)
        countDict[spec] = int(count) 
    addressIndex = percentsToAssignments(percentsToCount(indexRange, percentDict))
    for i in addressIndex.keys():
        addressIndex[i] = createAddressList(countDict[addressIndex[i]], addresses)
    return addressIndex

def createStartTime(index, tzinfo):
    day = random.choice(dates)
    hour = time(random.choice(startTimes[index]),0,0,0, tzinfo)
    return datetime.combine(day, hour)

def getDataFromFile(pathFile, note=False):
    """returns a list of strings
    used to read strings from files for titles, location, collection names..."""
    if not os.path.lexists(pathFile):
        # if file name has no path assume its in the same directory as this file
        pathFile = os.path.join(os.path.split(__file__)[0], pathFile)
    f = codecs.open(pathFile, encoding='utf-8')
    data = f.readlines()
    f.close()
    if note: 
        return [s.replace('\t','\n') for s in data]
    return data

def addRandomWithoutDups(listOfStrings, total):
    """
    Randomly picks requested number of strings from listOfStrings without duplicating any.  
    Intended mainly for creating collections.
    """
    outCollection = []
    numAdded = 0
    tries = 0
    numAvailable = len(listOfStrings)
    while len(outCollection) < total:
        tmp = random.choice(listOfStrings)
        tries += 1
        if tmp not in outCollection: 
            outCollection.append(tmp)
            numAdded += 1
        if numAdded > numAvailable or tries > 100:
            print 'Source collection contains less unique items than the total requested'
            print 'or number of tries to create collections exceeded 100'
            print 'Stopping at %d items, %d tries' % (numAdded, tries) 
            break 
    return outCollection

def createCollections(collectionNames, view):
    sidebarCollections = []
    for collName in collectionNames:
        if inTest: # create collections differently for unit tests
            col = pim.ListCollection("testCollection", itsView=view, 
                           displayName=collName.strip('\n'))
        else:
            col = Block.postEventByNameWithSender ("NewCollection", {})
            col.displayName = collName.strip('\n')
        sidebarCollections.append(col)
    return sidebarCollections
    

def createItems(paramDict):
    
    if bool(wx.GetApp()):
        view = QAUITestAppLib.App_ns.itsView
    else: # when running unit tests there is no app
        view = NullRepositoryView(verify=True)
    tzinfo = view.tzinfo.getDefault()
    
    totalItems = int(paramDict['textCtrlTotalItems'])
    
    #get titles to use
    TITLES = getDataFromFile(paramDict['textCtrlTitleSourceFile'])
    
    #create collections to use
    collectionNames = addRandomWithoutDups(getDataFromFile(paramDict['textCtrlCollectionFileName']), 
                                    int(paramDict['textCtrlCollectionCount']))
    sidebarCollections = createCollections(collectionNames, view)
    
    #determine how many collections each item should participate in
    collectionMembershipIndex = createMembershipIndex(paramDict['textCtrlCollectionMembership'], range(totalItems))
    collectionMembershipDict = {} 
    ##fill collectionMembershipDict with correct number of collections for each item index 
    for i in range(totalItems):
        collectionMembershipDict[i] = addRandomWithoutDups(sidebarCollections, collectionMembershipIndex[i])
    
    #get locations to use
    LOCATIONS = getDataFromFile(paramDict['textCtrlLocationSourceFilePath'])
    
    #get note field text
    NOTES = getDataFromFile(paramDict['textCtrlNoteSourceFilePath'], note=True)
        
    itemTypes = percentsToCount(totalItems,
                                {'mail':int(paramDict['choicePercentMail']), 
                                'task':int(paramDict['choicePercentTask']), 
                                'event':int(paramDict['choicePercentEvent'])})
    
    triageStatus = percentsToCount(totalItems,
                            {'unassigned': int(paramDict['choicePercentUnassignedStatus']), 
                             'now': int(paramDict['choicePercentNow']),
                             'later': int(paramDict['choicePercentLater']),
                             'done': int(paramDict['choicePercentDone'])}, randomize=True)
    triageStatusAssignments = percentsToAssignments(triageStatus)
    #convert the string triage value to the triageEnum that can be used to set it
    triageEnums = {'now':pim.TriageEnum.now, 'later':pim.TriageEnum.later, 'done':pim.TriageEnum.done}
    triageStatusUnassigned = []
    for index, status in triageStatusAssignments.iteritems():
        if status == 'unassigned':
            triageStatusUnassigned.append(index)
        else:
            triageStatusAssignments[index] = triageEnums[status]
    
    recurTypes = percentsToCount(itemTypes['event'],
                           {'non':int(paramDict['choicePercentNonRecurring']),
                            'daily':int(paramDict['choicePercentDaily']), 
                            'weekly':int(paramDict['choicePercentWeekly']), 
                            'biweekly':int(paramDict['choicePercentBiWeekly']), 
                            'monthly':int(paramDict['choicePercentMonthly']), 
                            'yearly':int(paramDict['choicePercentYearly'])}, randomize=True)
    
    durationTypes = percentsToCount(itemTypes['event'],
                            {'allDay': int(paramDict['choicePercentAllDay']),
                             'atTime': int(paramDict['choicePercentAtTime']),
                             'anyTime': int(paramDict['choicePercentAnyTime']),
                             'duration': int(paramDict['choicePercentDuration'])}, randomize=True) 
    
    eventStatus = percentsToCount(durationTypes['duration'],
                           {'confirmed':int(paramDict['choicePercentConfirmed']),
                            'FYI': int(paramDict['choicePercentFYI']),
                            'tentative': int(paramDict['choicePercentTentative'])}, randomize=True)
    eventStatusAssignment = percentsToAssignments(eventStatus)
    
    global startTimes
    startTimes = createStartTimeRange(paramDict['textCtrlTimeOfDay'], itemTypes['event'])
    
    startDateText = paramDict['textCtrlStartDate']
    if startDateText:
        y, m, d = startDateText.split(',')
        startDate = datetime(int(y), int(m), int(d))
        y, m, d = paramDict['textCtrlEndDate'].split(',')
        endDate = datetime(int(y), int(m), int(d))
        global dates 
        dates = createDateRange(startDate, endDate)
    
    durationsTimed = createDurationIndex(paramDict['textCtrlDuration'], durationTypes['duration'])
    itemsWithDuration = durationsTimed.keys()
    
    relativeReminders, absoluteReminders = createAlarmIndex(paramDict['textCtrlAlarmSpec'],itemTypes['event'], totalItems, tzinfo)
    
    allRecurring = recurTypes['daily'] + recurTypes['weekly'] + recurTypes['biweekly'] + recurTypes['monthly'] + recurTypes['yearly']
    recurenceEndDate = createEndDateIndex(paramDict['textCtrlRecurrenceEndDates'], allRecurring)
    
    # email stuff
    emailAddresses = [] 
    for firstName in firstNames:
        for lastName in lastNames:                 
            for domain in domainList:
                emailAddresses.append(firstName + lastName + '@' + domain)
    # get address sources
    if paramDict['textCtrlToFile'] == '':
        toAddresses = emailAddresses
    else:
        toAddresses = getDataFromFile(paramDict['textCtrlToFile'])
        
    if paramDict['textCtrlCCFileName'] == '':
        ccAddresses = emailAddresses
    else:
        ccAddresses = getDataFromFile(paramDict['textCtrlCCFileName'])
        
    if paramDict['textCtrlBCCFileName'] == '':
        bccAddresses = emailAddresses
    else:
        bccAddresses = getDataFromFile(paramDict['textCtrlBCCFileName'])
        
    # make email indexes from specs
    toIndex = createAddressIndex(itemTypes['mail'],paramDict['textCtrlToSpec'], toAddresses)
    ccIndex = createAddressIndex(itemTypes['mail'],paramDict['textCtrlCCSpec'], ccAddresses)
    bccIndex = createAddressIndex(itemTypes['mail'],paramDict['textCtrlBCCSpec'], bccAddresses)
    
    created = []
    for i in range(totalItems):
        created.append(pim.notes.Note(itsView=view))
        item = created[i]
        item.displayName = random.choice(TITLES)
        item.body = random.choice(NOTES)
        if i not in triageStatusUnassigned:
            item.setTriageStatus(triageStatusAssignments[i])
        if i in absoluteReminders.keys():
            item.setUserReminderTime(datetime.combine(date.today(), absoluteReminders[i])) 
        if i in itemTypes['mail']: 
            mailStampedItem = pim.MailStamp(item)
            mailStampedItem.add()
            if i in toIndex.keys(): 
                for address in toIndex[i]:
                    mailStampedItem.toAddress.append(Mail.EmailAddress.getEmailAddress(view, address))
            if i in ccIndex.keys(): 
                for address in ccIndex[i]:
                    mailStampedItem.ccAddress.append(Mail.EmailAddress.getEmailAddress(view, address))
            if i in bccIndex.keys(): 
                for address in bccIndex[i]:
                    mailStampedItem.bccAddress.append(Mail.EmailAddress.getEmailAddress(view, address))
        if i in itemTypes['task']: pim.TaskStamp(item).add()
        if i in itemTypes['event']: 
            eventStampedItem = pim.EventStamp(item)
            eventStampedItem.add()
            if i in itemsWithDuration: #if its an event with duration then assign status
                eventStampedItem.transparency = eventStatusAssignment[i].lower()
            eventStampedItem.location = Calendar.Location.getLocation(view, random.choice(LOCATIONS))
            eventStampedItem.anyTime = i in durationTypes['anyTime']
            eventStampedItem.allDay = i in durationTypes['allDay']
            eventStampedItem.startTime = createStartTime(i, tzinfo)
            if i in durationTypes['atTime']:
                eventStampedItem.duration = timedelta(0)
            else:
                if i in itemsWithDuration:
                    eventStampedItem.duration = durationsTimed[i]
            if i in relativeReminders.keys():
                    eventStampedItem.setUserReminderInterval(relativeReminders[i])
            if i in allRecurring:
                ruleItem = RecurrenceRule(None, itsView=view)
                ruleSetItem = RecurrenceRuleSet(None, itsView=view)
                recurFreq = rangeName(i, recurTypes)
                #specail case biweekly
                if recurFreq == 'biweekly':
                    ruleItem.freq = 'weekly'
                    ruleItem.interval = 2
                else:
                    ruleItem.freq = recurFreq
                #add end date
                if i in recurenceEndDate and recurenceEndDate[i]: # zero means don't use an end date
                    endDateDate = calcEndDate(eventStampedItem.startTime, recurenceEndDate[i], recurFreq)
                    ruleItem.until = endDateDate
                ruleSetItem.addRule(ruleItem)
                eventStampedItem.rruleset = ruleSetItem
        for collection in collectionMembershipDict[i]:
            collection.add(item)
    return created #return value used for testing in TestCreateItems.py:TestItemCreation
        
