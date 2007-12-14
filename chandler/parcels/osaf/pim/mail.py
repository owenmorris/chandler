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
Classes used for Mail parcel kinds.
"""

__all__ = [
     'IMAPAccount', 'MIMEBase', 'MIMEBinary', 'MIMEContainer', 'MIMENote',
     'MIMESecurity', 'MIMEText', 'IMAPFolder',
     'ProtocolTypeEnum', 'MailMessage', 'MailStamp',
     'POPAccount', 'SMTPAccount', 'addressMatchGenerator',
     'replyToMessage', 'replyAllToMessage', 'forwardMessage',
     'getCurrentOutgoingAccount', 'getCurrentIncomingAccount',
     'getCurrentMeEmailAddress',
     'getMessageBody', 'ACCOUNT_TYPES', 'EmailAddress', 'OutgoingAccount',
     'IncomingAccount', 'MailPreferences', 'getRecurrenceMailStamps']

import logging
from application import schema
import items, notes, stamping, collections, itertools
import email.Utils as Utils
import re as re
from chandlerdb.util.c import Empty
import PyICU

from i18n import ChandlerMessageFactory as _
from osaf import messages, preferences
from osaf.pim.calendar import EventStamp
from tasks import TaskStamp
from osaf.pim import Modification, setTriageStatus, TriageEnum
from osaf.pim.calendar.TimeZone import formatTime, getTimeZoneCode
from osaf.pim.calendar.DateTimeUtil import weekdayName
from datetime import datetime
from stamping import has_stamp, Stamp

from osaf.framework import password
from osaf.framework.twisted import waitForDeferred

log = logging.getLogger(__name__)

# Kind Combinations
MESSAGE = _(u"Message")
TASK = _(u"Task")
EVENT = _(u"Event")
R_EVENT = _(u"Recurring Event")
A_EVENT = _(u"All-day Event")
RA_EVENT = _(u"Recurring All-day Event")
SCHEDULED_TASK = _(u"Scheduled Task")
R_SCHEDULED_TASK = _(u"Recurring Scheduled Task")
A_SCHEDULED_TASK = _(u"All-day Scheduled Task")

# Kind Combinations with sentence prefix
# XXX This is not the ideal way to do this but
# am having trouble capturing the finer aspects
# of the English language in a localization friendly
# manner. I will revisit this decision at a later date.
P_TASK = _(u"a Task")
P_EVENT = _(u"an Event")
P_R_EVENT = _(u"a Recurring Event")
P_A_EVENT = _(u"an All-day Event")
P_RA_EVENT = _(u"a Recurring All-day Event")
P_SCHEDULED_TASK = _(u"a Scheduled Task")
P_R_SCHEDULED_TASK = _(u"a Recurring Scheduled Task")
P_A_SCHEDULED_TASK = _(u"an All-day Scheduled Task")

# L10N: Description of a recurring event with a specific end to its recurrence
# %(recurrenceFrequency)s will be replaced with something like "every month".
# %(particularDateTime)s will be replaced by the text that would be used to
# describe a non-recurring event
RECUR_FOREVER = _(u"%(particularDateTime)s (otherwise %(recurrenceFrequency)s starting %(recurrenceStartDate)s)")
# L10N: Description of a recurring event with a specific end to its recurrence
# %(recurrenceFrequency)s will be replaced with something like "every month".
# %(particularDateTime)s will be replaced by the text that would be used to
# describe a non-recurring event
RECUR_UNTIL = _(u"%(particularDateTime)s (otherwise %(recurrenceFrequency)s from %(recurrenceStartDate)s to %(recurrenceEndDate)s)")

# L10N: Description of a recurring event with a specific end to its recurrence
# %(recurrenceFrequency)s will be replaced with something like "every month".
# %(normalTime)s will be replaced with a sentence fragment like
# "at %(originalStartTime)s".  %(particularDateTime)s will be replaced by the
# text that would be used to describe a non-recurring event
RECUR_FOREVER_SHOW_TIME = _(u"%(particularDateTime)s (otherwise %(recurrenceFrequency)s %(normalTime)s starting %(recurrenceStartDate)s)")
# L10N: Description of a recurring event with a specific end to its recurrence
# %(recurrenceFrequency)s will be replaced with something like "every month".
# %(normalTime)s will be replaced with a sentence fragment like
# "at %(originalStartTime)s".  %(particularDateTime)s will be replaced by the
# text that would be used to describe a non-recurring event
RECUR_UNTIL_SHOW_TIME = _(u"%(particularDateTime)s (otherwise %(recurrenceFrequency)s %(normalTime)s from %(recurrenceStartDate)s to %(recurrenceEndDate)s)")

# L10N: time-only description for an event that occurs at a specific time with no duration,
# this is one of the possible replacements for the %(normalTime)s parameter
AT_TIME_ONLY = _(u"at %(originalStartTime)s")
# L10N: time-only description for an event that starts and ends at different times,
# this is one of the possible replacements for the %(normalTime)s parameter
TIME_ONLY_WITH_END = _(u"from %(originalStartTime)s-%(originalEndTime)s")
# L10N: description of an event that lasts all day, this is one of the possible
# replacements for the %(normalTime)s parameter
ALL_DAY_TIME_ONLY = _(u"all-day")


## Frequency strings for recurrence
# L10N: Description of the frequency of a complex recurrence rule, used to build %(recurrenceFrequency)s
COMPLEX_FREQ = _(u"Custom recurrence rule: No description.")
FREQ_MATCHING_DAY = {
    # L10N: description of repetition for a daily recurring event, used to build %(recurrenceFrequency)s
    'daily'    : _(u"every day"),
    # L10N: description of repetition for a weekly recurring event, used to build %(recurrenceFrequency)s
    'weekly'   : _(u"every week"),
    # L10N: description of repetition for a biweekly recurring event, used to build %(recurrenceFrequency)s
    'biweekly' : _(u"every other week"),
    # L10N: description of repetition for a monthly recurring event, used to build %(recurrenceFrequency)s
    'monthly'  : _(u"every month"),
    # L10N: description of repetition for a yearly recurring event, one of the replacements for %(recurrenceFrequency)s
    'yearly'   : _(u"every year")
}
FREQ_DIFFERENT_DAY = FREQ_MATCHING_DAY.copy()
# L10N: description of repetition for a weekly recurring event with a changed weekday, used to build %(recurrenceFrequency)s
FREQ_DIFFERENT_DAY['weekly']   = _(u"every %(recurrenceDayName)s")
# L10N: description of repetition for a biweekly recurring event with a changed weekday, used to build %(recurrenceFrequency)s
FREQ_DIFFERENT_DAY['biweekly'] = _(u"every other %(recurrenceDayName)s")

## Anytime or Allday events
ONE_DAY_ALLDAY = _(u"%(dayName)s %(startDate)s")
MULTI_DAY_ALLDAY = _(u"%(dayName)s %(startDate)s - %(endDayName)s %(endDate)s")

## Timed events
# L10N: description of an event with equal start and end time
AT_TIMED = _(u"%(dayName)s %(startDate)s at %(startTime)s %(timezone)s")
# L10N: description of an event on a single day with different start and end times
ONE_DAY_TIMED = _(u"%(dayName)s %(startDate)s %(startTime)s - %(endTime)s %(timezone)s")
# L10N: description of an event with time that ends on a different day then it starts
MULTI_DAY_TIMED = _(u"%(dayName)s %(startDate)s %(startTime)s - %(endDayName)s %(endDate)s %(endTime)s %(timezone)s")

## Main template for event description
# L10N: Text describing an event, inserted into emailed events
TIME_DESCRIPTION = _(u"""\
Title: %(title)s
Location: %(location)s

%(time_information)s
""")

## Full email templates
NEW_BODY_SAME_FROM = _(u"""\
%(sender)s sent you %(kindCombination)s from Chandler:

%(description)s%(itemBody)s
""")

UPDATE_BODY_SAME_FROM = _(u"""\
%(sender)s sent you an Update on %(kindCombination)s from Chandler:

%(description)s%(itemBody)s
""")

NEW_BODY_DIFFERENT_FROM = _(u"""\
%(sender)s sent you %(kindCombination)s from Chandler:

From: %(originators)s
To: %(toAddresses)s%(ccAddressLine)s
%(description)s
%(itemBody)s
""")

UPDATE_BODY_DIFFERENT_FROM = _(u"""\
%(sender)s sent you an Update on %(kindCombination)s from Chandler:

From: %(originators)s
To: %(toAddresses)s%(ccAddressLine)s
%(description)s
%(itemBody)s
""")

def getMessageBody(mailStamp):
    if not has_stamp(mailStamp.itsItem, EventStamp) and \
       not has_stamp(mailStamp.itsItem, TaskStamp):
        #XXX NEED TO BE UPDATED WHEN MORE STAMPING TYPES ADDED
        # If it is just a mail message then return the
        # ContentItem body
        return mailStamp.itsItem.body

    showFrom = False
    ret = None

    orig = getattr(mailStamp, "originators", [])

    size = len(orig)

    if size == 1:
        #Compare the from and originators[0] for a match
        for addr in orig:
            # See if the firt value in originators matches the sender
            if addr != mailStamp.getSender():
                showFrom = True
            break

    elif len(orig) > 1:
        # There is more than one address in the Chandler From field
        # so it must differ from the RFC 2822 from.
        showFrom = True


    if mailStamp.isAnUpdate():
        if showFrom:
            ret = UPDATE_BODY_DIFFERENT_FROM
        else:
            ret = UPDATE_BODY_SAME_FROM
    else:
        if showFrom:
            ret = NEW_BODY_DIFFERENT_FROM
        else:
            ret = NEW_BODY_SAME_FROM

    args = getBodyValues(mailStamp, usePrefix=True)

    if not has_stamp(mailStamp.itsItem, EventStamp):
        # Only include a description (title) if the
        # item is an Event
        args['description'] = u''
    else:
        # Add two new lines to the description.
        # This is done to minimize the number of
        # unique sentences that have to be defined
        # to support localization.
        args['description'] = u'%s\n' % args['description']

    return ret %  args


def getForwardBody(mailStamp):
    return _(u"""\
Begin forwarded %(kindCombination)s:

> From: %(originators)s
> To: %(toAddresses)s%(ccAddressLine)s
> Sent by %(sender)s on %(date)s at %(time)s
>
> %(description)s
>
%(itemBody)s

""") % getBodyValues(mailStamp, addGT=True)


def getReplyBody(mailStamp):
    return _(u"""\
%(sender)s wrote on %(date)s at %(time)s:

> %(description)s
>
%(itemBody)s

""") % getBodyValues(mailStamp, addGT=True)

def formatDateAndTime(view, dateStamp):
    dateTime = formatTime(view, dateStamp, noTZ=True, includeDate=True)
    time = formatTime(view, dateStamp, noTZ=True, includeDate=False)

    # Parse the date from a date time string since formatTime does
    # not have an option to get just the date.
    date = dateTime.split(time)[0]

    try:
        date = date.strip()
        time = time.strip()
    except:
        pass

    return (date, time)

def isMeAddress(addr):
    if addr is None:
        return False

    meAddresses = getCurrentMeEmailAddresses(addr.itsView)

    for me in meAddresses:
        if addr.emailAddress.lower() == me.emailAddress.lower():
            return True
    return False

def in_collection(addr, collection):
    for address in collection:
        if addr.emailAddress.lower() == address.emailAddress.lower():
            return True
        return False

def getRecurrenceMailStamps(mailStamp):
    """
    Recurring mails get most of their mail attributes from the recurrence
    master, but a few details (subject, body, description) are based on which
    occurrence was sent.  Return (mailStampOccurrence, mailStampMaster), which
    will be equal for non-recurring events.

    """
    mailStampMaster = mailStampOccurrence = mailStamp
    if has_stamp(mailStampOccurrence, EventStamp):
        mailStampMaster = MailStamp(EventStamp(mailStampOccurrence).getMaster())
    return (mailStampOccurrence, mailStampMaster)

def getBodyValues(mailStamp, addGT=False, usePrefix=False):
    view = mailStamp.itsItem.itsView

    mailStampOccurrence, mailStamp = getRecurrenceMailStamps(mailStamp)

    if not hasattr(mailStamp, 'dateSent'):
        from osaf.mail.utils import dateTimeToRFC2822Date
        mailStamp.dateSent = datetime.now(view.tzinfo.default)

    date, time = formatDateAndTime(view, mailStamp.dateSent)

    to = []

    for addr in mailStamp.toAddress:
        to.append(addr.format())

    cc = []

    for addr in mailStamp.ccAddress:
        cc.append(addr.format())

    if len(cc):
        # Cc: is a RFC mail header and does not need
        # to be localized
        if addGT:
            ccLine = u"\n> Cc: %s" % u", ".join(cc)
        else:
            ccLine = u"\nCc: %s" % u", ".join(cc)
    else:
       ccLine = u""

    if addGT:
        body = mailStampOccurrence.itsItem.body.split(u"\n")
        buffer = []

        for line in body:
            if line.startswith(u">"):
                buffer.append(u">%s" % line)
            else:
                buffer.append(u"> %s" % line)

        body = u"\n".join(buffer)

    else:
        body = mailStampOccurrence.itsItem.body

    sender = mailStamp.getSender().format()

    originators = []

    for addr in mailStamp.originators:
        originators.append(addr.format())

    originators = u", ".join(originators)

    return {
             "sender":  sender,
             "kindCombination": buildKindCombination(mailStampOccurrence,
                                                     usePrefix),
             "originators": originators,
             "toAddresses": u", ".join(to),
             "ccAddressLine": ccLine,
             "description": buildItemDescription(mailStampOccurrence),
             "itemBody": body,
             "date": date,
             "time": time,
           }


def buildItemDescription(mailStamp):

    item = mailStamp.itsItem
    view = item.itsView

    if not has_stamp(item, EventStamp):
        return item.displayName

    event = EventStamp(item)
    master = event.getMaster()
    recur = getattr(master, 'rruleset', None)
    noTime = event.allDay or event.anyTime

    location = getattr(event, 'location', u'')

    if location:
        location = location.displayName.strip()

    startDate, startTime = formatDateAndTime(view, event.startTime)
    endDate, endTime = formatDateAndTime(view, event.endTime)

    if getattr(event.startTime, "tzinfo", None) == view.tzinfo.floating:
        timezone = u""

    else:
        timezone = getTimeZoneCode(view, event.startTime)

    if startDate == endDate:
        # The Event starts and ends on the same day
        endDate = None

        if startTime == endTime:
            # The Event has no duration
            endTime = None

    # If the event endDate and endTime
    # match the event startDate and startTime
    # then the event is singular in nature
    # ie. Event on 12/31/207 at 12pm
    single = endDate == endTime == None

    args = {'title': item.displayName,
            'startTime': startTime,
            'startDate': startDate,
            'dayName': weekdayName(event.startTime),
            'endTime': endTime,
            'endDate': endDate,
            'endDayName': weekdayName(event.endTime),
            'location': location,
            'timezone': timezone,
           }

    if noTime:
        simpleTemplate = MULTI_DAY_ALLDAY if endDate else ONE_DAY_ALLDAY
    else:
        if endDate:
            simpleTemplate = MULTI_DAY_TIMED
        else:
            simpleTemplate = AT_TIMED if single else ONE_DAY_TIMED

    particularDateTime = simpleTemplate % args

    if not recur:
        args['time_information'] = particularDateTime
        return TIME_DESCRIPTION % args

    args['particularDateTime'] = particularDateTime
    rule = recur.rrules.first()
    freq = rule.freq
    interval = rule.interval
    until = rule.calculatedUntil()

    args['recurrenceDayName'] = weekdayName(master.startTime)

    if recur.isComplex():
        args['recurrenceFrequency'] = COMPLEX_FREQ % args
    else:
        if freq == 'weekly' and interval == 2:
            freq = 'biweekly'
        
        freqSource = (FREQ_MATCHING_DAY if event.recurrenceID.date() == 
                                           event.startTime.date() else
                      FREQ_DIFFERENT_DAY)
        
        args['recurrenceFrequency'] = freqSource[freq] % args
    
    masterDate, masterTime = formatDateAndTime(view, master.startTime)
    ignore, masterEndTime  = formatDateAndTime(view, master.endTime)
    args['recurrenceStartDate'] = masterDate
    args['recurrenceEndDate'] = (formatDateAndTime(view, until)[0]
                                 if until else u'')
    
    
    if master.anyTime or master.allDay:
        # the occurrence isn't all day, the master is
        args['normalTime'] = ALL_DAY_TIME_ONLY
    else:
        normalTemplate = AT_TIME_ONLY if single else TIME_ONLY_WITH_END
        args['normalTime'] = normalTemplate % {
            'originalStartTime' : masterTime,
            'originalEndTime'   : masterEndTime
        }

    if noTime:
        recurTemplate = RECUR_UNTIL if until else RECUR_FOREVER
    else:        
        recurTemplate = RECUR_UNTIL_SHOW_TIME if until else RECUR_FOREVER_SHOW_TIME

    args['time_information'] = recurTemplate % args
    return TIME_DESCRIPTION % args


def buildKindCombination(mailStamp, usePrefix=False):
    item = mailStamp.itsItem

    isEvent = has_stamp(item, EventStamp)
    isTask  = has_stamp(item, TaskStamp)

    if isEvent:
        event = EventStamp(item)
        isAllDay = event.allDay or event.anyTime
        isRecurring = getattr(event, 'rruleset', False)

        if isAllDay:
            # If it is an all day event then it is
            # not any time
            isAnytime = False

        if isRecurring:
            if usePrefix:
                return isAllDay and (isTask and P_R_SCHEDULED_TASK or P_RA_EVENT) or \
                       (isTask and P_R_SCHEDULED_TASK or P_R_EVENT)
            else:
                return isAllDay and (isTask and R_SCHEDULED_TASK or RA_EVENT) or \
                       (isTask and R_SCHEDULED_TASK or R_EVENT)

        if usePrefix:
            return isAllDay and (isTask and P_A_SCHEDULED_TASK or P_A_EVENT) or \
                   (isTask and P_SCHEDULED_TASK or P_EVENT)

        else:
            return isAllDay and (isTask and A_SCHEDULED_TASK or A_EVENT) or \
                   (isTask and SCHEDULED_TASK or EVENT)

    if isTask:
        if usePrefix:
            return P_TASK
        else:
            return TASK

    return MESSAGE

def __actionOnMessage(view, mailStamp, action="REPLY"):
    assert(isinstance(mailStamp, MailStamp))
    assert(action == "REPLY" or action == "REPLYALL" or action == "FORWARD")

    newMailStamp = MailMessage(itsView=view)
    newMailStamp.InitOutgoingAttributes()

    if action == "REPLY" or action == "REPLYALL":
        sender = mailStamp.getSender()
        previousSender = mailStamp.getPreviousSender()

        if previousSender and not isMeAddress(previousSender):
            # Only add the previous sender to the toAddress list
            # if the sender is not one of the me addresses.
            # This works around the use case where the
            # the current me Chandler user edited an
            # email sent from another Chandler user thus
            # overwriting the sender attribute.
            newMailStamp.toAddress.append(previousSender)
        else:
            newMailStamp.toAddress.append(sender)

        for ea in mailStamp.getOriginators():
            # Only add valid email addresses to the
            # ccAddress list.
            if not in_collection(ea, newMailStamp.toAddress) and \
               not in_collection(ea, newMailStamp.ccAddress) and \
               not isMeAddress(ea):
                newMailStamp.ccAddress.append(ea)

        if mailStamp.subject:
            if mailStamp.subject.lower().startswith(u"re: "):
                newMailStamp.subject = mailStamp.subject
            else:
                newMailStamp.subject = u"Re: %s" % mailStamp.subject

        newMailStamp.inReplyTo = mailStamp.messageId

        for ref in mailStamp.referencesMID:
            newMailStamp.referencesMID.append(ref)

        newMailStamp.referencesMID.append(mailStamp.messageId)

        newMailStamp.itsItem.body = getReplyBody(mailStamp)

        if action == "REPLYALL":
            for ea in mailStamp.toAddress:
                if not in_collection(ea, newMailStamp.toAddress) and \
                   not in_collection(ea, newMailStamp.ccAddress) and \
                   not isMeAddress(ea):
                    newMailStamp.ccAddress.append(ea)

            for ea in mailStamp.ccAddress:
                if not in_collection(ea, newMailStamp.toAddress) and \
                   not in_collection(ea, newMailStamp.ccAddress) and \
                   not isMeAddress(ea):
                    newMailStamp.ccAddress.append(ea)

        if len(newMailStamp.toAddress) == 0:
            # If there is no email addresses in the to field
            # then add the sender or previous sender to the
            # toAddress list even if the address == me.
            # The idea is to avoid a reply to 'me'. However,
            # a 'to address' is required to send a message.
            # So in this case go ahead and add the address
            # to the toAddress list.
            if previousSender:
                newMailStamp.toAddress.append(previousSender)
            else:
                newMailStamp.toAddress.append(sender)
    else:
        #FORWARD CASE
        #XXX I don't think this makes sense. Commenting
        # out till I get further feedback. A forward
        # should not contain the originators from the
        # previous message.
        # By default the me address gets added to the
        # originators when the Note is stamped as mail.
        # So start with a fresh list.
        #newMailStamp.originators = []

        #for ea in mailStamp.originators:
        #    newMailStamp.originators.append(ea)

        if mailStamp.subject:
            if mailStamp.subject.lower().startswith(u"fwd: ") or \
               mailStamp.subject.lower().startswith(u"[fwd: "):
                newMailStamp.subject = mailStamp.subject
            else:
                newMailStamp.subject = u"Fwd: %s" % mailStamp.subject

        newMailStamp.itsItem.body = getForwardBody(mailStamp)

    return newMailStamp.itsItem

def replyToMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "REPLY")

def replyAllToMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "REPLYALL")

def forwardMessage(view, mailStamp):
    """
        @return: a C{Note} item which has been stamped as a c{MailStamp}
    """
    return __actionOnMessage(view, mailStamp, "FORWARD")

def checkIfToMe(mailStamp):
    assert(isinstance(mailStamp, MailStamp))

    if getattr(mailStamp, 'viaMailService', False):
        # Mail arriving via the Mail Service never
        # has its toMe value recalculated
        return 

    view = mailStamp.itsItem.itsView

    meEmailAddresses = schema.ns("osaf.pim", view).meEmailAddressCollection.inclusions

    found = False

    if hasattr(mailStamp, "toAddress"):
        for addr in mailStamp.toAddress:
            if addr in meEmailAddresses:
                found = True
                break

    if not found and hasattr(mailStamp, "ccAddress"):
        for addr in mailStamp.ccAddress:
            if addr in meEmailAddresses:
                found = True
                break

    if not found and hasattr(mailStamp, "bccAddress"):
        for addr in mailStamp.bccAddress:
            if addr in meEmailAddresses:
                found = True
                break

    # Even though 'toMe' has an initialValue, it may not have
    # been set when this code is called (e.g. from a schema.observer
    # during stamp addition).

    if found != getattr(mailStamp, 'toMe', False):
        mailStamp.toMe = found

def checkIfFromMe(mailStamp):
    assert(isinstance(mailStamp, MailStamp))
    view = mailStamp.itsItem.itsView

    meAddresses = schema.ns("osaf.pim", view).meEmailAddressCollection.inclusions

    found = False

    if getattr(mailStamp, 'fromAddress', None) and \
       mailStamp.fromAddress in meAddresses:
        found = True

    if not found and getattr(mailStamp, 'replyToAddress', None) and \
       mailStamp.replyToAddress in meAddresses:
            found = True

    if not found and getattr(mailStamp, 'originators', None):
        for ea in mailStamp.originators:
            if ea is not None and ea in meAddresses:
                found = True
                break

    # Even though 'fromMe' has an initialValue, it may not have
    # been set when this code is called (e.g. from a schema.observer
    # during stamp addition).
    if found != getattr(mailStamp, 'fromMe', False):
        mailStamp.fromMe = found

def getCurrentOutgoingAccount(view, ignorePassword=False):
    """
    This function returns the default C{OutgoingAccount} account
    or the first C{OutgoingAccount} found if no default exists.

    @return C{OutgoingAccount} or None
    """

    outgoingAccount = None

    # Get the current SMTP Account
    ref = schema.ns('osaf.pim', view).currentOutgoingAccount
    outgoingAccount = getattr(ref, 'item', None)

    if outgoingAccount is None or not outgoingAccount.isSetUp(ignorePassword):
        for account in OutgoingAccount.iterItems(view):
            if account.isSetUp(ignorePassword):
                return account

    return outgoingAccount


def getCurrentIncomingAccount(view, ignorePassword=False):
    """
    This function returns the current (default) C{IncomingAccount} in the
    Repository.

    @return C{IncomingAccount} or None
    """
    ref = schema.ns('osaf.pim', view).currentIncomingAccount
    incomingAccount = getattr(ref, 'item', None)

    if incomingAccount is None or not incomingAccount.isSetUp(ignorePassword):
        for account in IncomingAccount.iterItems(view):
            if account.isSetUp(ignorePassword):
                return account

    return incomingAccount

def getCurrentMeEmailAddress(view):
    return schema.ns('osaf.pim', view).currentMeEmailAddress.item

def getCurrentMeEmailAddresses(view):
    return schema.ns('osaf.pim', view).currentMeEmailAddresses

def _recalculateMeEmailAddresses(view):
    pim_ns =  schema.ns("osaf.pim", view)
    pim_ns.currentMeEmailAddress.item = _calculateCurrentMeEmailAddress(view)
    addresses = pim_ns.currentMeEmailAddresses.inclusions
    oldAddresses = set(addresses)
    for address in _calculateCurrentMeEmailAddresses(view):
        if not address in oldAddresses:
            addresses.add(address)
        else:
            oldAddresses.remove(address)
    for address in oldAddresses:
        addresses.remove(address)

def addressMatchGenerator(address):
    if address is None:
        return

    view = address.itsView
    lowerAddress = address.emailAddress.lower()
    pim_ns =  schema.ns("osaf.pim", view)

    # Find all the EmailAddress items whose emailAddress attribute
    # matches this one, case-insensitively (this will include the one we
    # were called with).
    emailAddressCollection = pim_ns.emailAddressCollection
    def _compare(uuid):
        attrValue = view.findValue(uuid, 'emailAddress').lower()
        return cmp(lowerAddress, attrValue)

    firstUUID = emailAddressCollection.findInIndex('emailAddress', 'first', _compare)

    if firstUUID is None:
        return

    lastUUID = emailAddressCollection.findInIndex('emailAddress', 'last', _compare)

    for uuid in emailAddressCollection.iterindexkeys('emailAddress', firstUUID, lastUUID):
        yield view[uuid]

def _registerNewMeAddress(newAddress):
    """ 
    If this address isn't a "me" address, make it one.
    - add it to the "me" list
    - reconsider toMe/fromMe of any messages that reference this address
    - Do the same for all existing EmailAddress items whose emailAddress
      attribute differs from this only by case.
    """
    if newAddress is not None and newAddress.isValid():
        view = newAddress.itsView
        pim_ns =  schema.ns("osaf.pim", view)
        meEmailAddressCollection = pim_ns.meEmailAddressCollection

        # For each, check toMe/fromMe on its messages.
        for address in addressMatchGenerator(newAddress):
            if address not in meEmailAddressCollection:
                meEmailAddressCollection.append(address)

                checkList = set([item for item in 
                                 itertools.chain(address.messagesFrom,
                                                 address.messagesReplyTo,
                                                 address.messagesOriginator)
                                 if not getattr(item, MailStamp.fromMe.name, False)])
                for item in checkList:
                    checkIfFromMe(MailStamp(item))

                checkList = set([item for item in
                                 itertools.chain(address.messagesTo,
                                                 address.messagesCc,
                                                 address.messagesBcc)
                                 if not getattr(item, MailStamp.toMe.name, False)])
                for item in checkList:
                    checkIfToMe(MailStamp(item))

        _recalculateMeEmailAddresses(view)


def _potentialMeAccount(account):
    """
       Checks the account settings to confirm
       that account is active and has a host name
       filled in.
    """
    return account.isActive and len(account.host.strip())

def _calculateCurrentMeEmailAddress(view):
    """
        Lookup the "me" EmailAddress.

        The "me" is determined as follows:
            1. Return the default outgoing email address
            2. Return the first outgoing account containing an email address
            3. Return the default incoming email address
            4. Return the first incoming account containing an email address
            5. Return None
    """
    account = getCurrentOutgoingAccount(view, ignorePassword=True)

    if account is not None and _potentialMeAccount(account) and \
       account.fromAddress and account.fromAddress.isValid():
        return account.fromAddress

    #Loop through till we find an outging account with an emailAddress
    for account in OutgoingAccount.iterItems(view):
        if _potentialMeAccount(account) and account.fromAddress and \
           account.fromAddress.isValid():
            return account.fromAddress

    # No Outgoing accounts found with an email address so try
    # the Incoming accounts
    account = getCurrentIncomingAccount(view, ignorePassword=True)

    if account is not None and _potentialMeAccount(account) and \
       account.replyToAddress and \
       account.replyToAddress.isValid():
        return account.replyToAddress

    for account in IncomingAccount.iterItems(view):
        if _potentialMeAccount(account) and account.replyToAddress and \
           account.replyToAddress.isValid():
            return account.replyToAddress

    return None

def _calculateCurrentMeEmailAddresses(view):
    """
      Returns a list of c{EmailAddress} items.
      The list contains the email addresses
      for all configured Outgoing and Incoming
      Accounts.

      The list email address ordering will be determined
       as follows:
           1. The default outgoing email address
           2. Any outgoing account containing an email address
           3. The default incoming email address
           4. Any incoming account containing an email address

      Note that there may be other EmailAddress items in the historic
      meEmailAddressCollection that differ only from these by case; we
      don't add them here, though, because we don't want them in eg popups.
    """

    addrs = []

    outgoing = getCurrentOutgoingAccount(view, ignorePassword=True)

    if outgoing is not None and _potentialMeAccount(outgoing) and \
       outgoing.fromAddress and \
       outgoing.fromAddress.isValid():
        addrs.append(outgoing.fromAddress)

    for account in OutgoingAccount.iterItems(view):
        if _potentialMeAccount(account) and account.fromAddress and \
           account.fromAddress.isValid() and \
           account != outgoing:
            addrs.append(account.fromAddress)

    incoming = getCurrentIncomingAccount(view, ignorePassword=True)

    if incoming is not None and _potentialMeAccount(incoming) and \
       incoming.replyToAddress and \
       incoming.replyToAddress.isValid():
        addrs.append(incoming.replyToAddress)

    for account in IncomingAccount.iterItems(view):
        if _potentialMeAccount(account) and account.replyToAddress and \
           account.replyToAddress.isValid() and \
           account != incoming:
            addrs.append(account.replyToAddress)

    return addrs


class MailPreferences(preferences.Preferences):
    isOnline = schema.One(schema.Boolean, initialValue = True)

class ConnectionSecurityEnum(schema.Enumeration):
    values = "NONE", "TLS", "SSL"


class AccountBase(items.ContentItem):
    schema.kindInfo(
        description="The base kind for various account kinds, such as "
                    "IMAP, SMTP, WebDav"
    )

    numRetries = schema.One(
        schema.Integer,
        doc = 'How many times to retry before giving up',
        initialValue = 0,
    )
    username = schema.One(
        schema.Text,
        doc = 'The account login name',
        initialValue = u'',
    )

    password = password.passwordAttribute

    host = schema.One(
        schema.Text,
        doc = 'The hostname of the account',
        initialValue = u'',
    )
    port = schema.One(
        schema.Integer, doc = 'The port number to use',
    )
    connectionSecurity = schema.One(
        ConnectionSecurityEnum,
        doc = 'The security mechanism to leverage for a network connection',
        initialValue = 'NONE',
    )
    pollingFrequency = schema.One(
        schema.Integer,
        doc = 'Frequency in seconds',
        initialValue = 300,
    )

    isActive = schema.One(
        schema.Boolean,
        doc = 'Whether or not an account should be used for sending or '
              'fetching email',
        initialValue = True,
    )

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host and item.username:
                yield item


class IncomingAccount(AccountBase):
    accountType = "INCOMING"

    schema.kindInfo(
        description="Base Account for protocols that download mail",
    )

    replyToAddress = schema.One(
        initialValue = None
    ) # inverse of EmailAddress.accounts

    @apply
    def emailAddress():
        def fget(self):
            if getattr(self, "replyToAddress", None) is not None:
                return self.replyToAddress.emailAddress
            return None

        def fset(self, value):
            if getattr(self, "replyToAddress", None) is not None:
                oldFullName = self.replyToAddress.fullName
            else:
                oldFullName = u''
            self.replyToAddress = \
                EmailAddress.getEmailAddress(self.itsView, value, oldFullName) or \
                EmailAddress(itsView=self.itsView)

        return property(fget, fset)

    @apply
    def fullName():
        def fget(self):
            if getattr(self, "replyToAddress", None) is not None:
                return self.replyToAddress.fullName
            return None

        def fset(self, value):
            if getattr(self, "replyToAddress", None) is not None:
                oldAddress = self.replyToAddress.emailAddress
            else:
                oldAddress = u''
            self.replyToAddress = \
                EmailAddress.getEmailAddress(self.itsView, oldAddress, value) or \
                EmailAddress(itsView=self.itsView)

        return property(fget, fset)

    @schema.observer(replyToAddress)
    def onReplyToAddressChange(self, op, name):
        _registerNewMeAddress(getattr(self, 'replyToAddress', None))

    def isSetUp(self, ignorePassword=False):
        res = self.isActive and \
               len(self.host.strip()) and \
               len(self.username.strip())

        if not ignorePassword:
            res = res and \
                  len(waitForDeferred(self.password.decryptPassword()).strip())

        return res


class OutgoingAccount(AccountBase):
    accountType = "OUTGOING"

    schema.kindInfo(
        description="An Outgoing Account",
    )

    fromAddress = schema.One(
        initialValue = None
    )

    @apply
    def emailAddress():
        def fget(self):
            if getattr(self, "fromAddress", None) is not None:
                return self.fromAddress.emailAddress
            return None

        def fset(self, value):
            if getattr(self, "fromAddress", None) is not None:
                oldFullName = self.fromAddress.fullName
            else:
                oldFullName = u''
            self.fromAddress = \
                EmailAddress.getEmailAddress(self.itsView, value, oldFullName) or \
                EmailAddress(itsView=self.itsView)

        return property(fget, fset)

    @apply
    def fullName():
        def fget(self):
            if getattr(self, "fromAddress", None) is not None:
                return self.fromAddress.fullName
            return None

        def fset(self, value):
            if getattr(self, "fromAddress", None) is not None:
                oldAddress = self.fromAddress.emailAddress
            else:
                oldAddress = u''
            self.fromAddress = \
                EmailAddress.getEmailAddress(self.itsView, oldAddress, value) or \
                EmailAddress(itsView=self.itsView)

        return property(fget, fset)

    messageQueue = schema.Sequence(
        doc = "The Queue of mail messages  to be sent from this account. "
              "Used primarily for offline mode.",
        initialValue = [],
    )



    #Commented out for Preview
    #signature = schema.One(
    #    schema.Text,
    #    description =
    #        "Issues:\n"
    #        '   Basic signature addition to an outgoing message will be refined '
    #        'in future releases\n',
    #)

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host:
                yield item

    @schema.observer(fromAddress)
    def onFromAddressChange(self, op, name):
        _registerNewMeAddress(getattr(self, "fromAddress", None))

    def isSetUp(self, ignorePassword=False):
        res = self.isActive and len(self.host.strip())

        if self.useAuth:
            res = res and len(self.username.strip())

            if not ignorePassword:
               res = res and \
                      len(waitForDeferred(self.password.decryptPassword()).strip())

        return res


class SMTPAccount(OutgoingAccount):
    accountProtocol = "SMTP"

    schema.kindInfo(
        description="An SMTP Account",
    )


    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use',
        initialValue = 25,
    )

    useAuth = schema.One(
        schema.Boolean,
        doc = 'Whether or not to use authentication when sending mail',
        initialValue = False,
    )


class IMAPAccount(IncomingAccount):
    accountProtocol = "IMAP"

    schema.kindInfo(
        description = "An IMAP Account",
    )

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "an IMAPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 143,
    )

    folders = schema.Sequence(
        doc = 'Details which IMAP folders to download mail from',
        initialValue = [],
    ) # inverse of IMAPFolder.parentAccount

    def __setup__(self):
        self._addInbox()

    def _addInbox(self):
        # Create the Inbox IMAPFolder and add to the account
        # folders collection
        inbox = IMAPFolder(
            itsView = self.itsView,
            # L10N: The UI display name for an IMAP Inbox
            displayName = _(u"Inbox"),
            folderName  = u"INBOX",
            folderType  = "CHANDLER_HEADERS",
        )

        self.folders.append(inbox)


class ProtocolTypeEnum(schema.Enumeration):
    values = "CHANDLER_HEADERS", "MAIL", "TASK", "EVENT"

class IMAPFolder(items.ContentItem):
    schema.kindInfo(
        description=
            "Chandler representation of a Folder on a IMAP server "
    )

    folderName = schema.One(
        schema.Text,
        doc = 'The name of the folder on the IMAP server.',
    )

    folderType = schema.One(
        ProtocolTypeEnum,
        doc = 'The value of this dictates whether the action to perform on the downloaded message',
        initialValue = 'MAIL',
    )

    #This contains the last downloaded IMAP Message UID
    #for the folder.
    lastMessageUID = schema.One(
        schema.Integer,
        initialValue = 0,
    )

    deleteOnDownload = schema.One(
        schema.Boolean,
        doc = 'Whether to delete the message after downloading',
        initialValue = False,
    )
    downloaded = schema.One(
        schema.Integer,
        doc = 'The number of messages downloaded to this folder.',
        initialValue = 0,
    )


    downloadMax = schema.One(
        schema.Integer,
        doc = 'The maximum number of messages to download for this folder. A value of 0 indicates that there is no download message limit.',
        initialValue = 0,
    )

    parentAccount = schema.One(
        IMAPAccount, initialValue = None, inverse = IMAPAccount.folders,
    ) # Inverse ofIMAPAccount.folders sequence


class POPAccount(IncomingAccount):
    accountProtocol = "POP"

    schema.kindInfo(
        description = "A POP Account",
    )

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "a POPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 110,
    )

    seenMessageUIDS = schema.Mapping(
        schema.Text,
        doc = 'Used for quick look up to discover messages that have already been downloaded or inspected.',
        initialValue = {},
    )

    actionType = schema.One(
        ProtocolTypeEnum,
        doc = 'The value of this dictates whether the action to perform on the downloaded message',
        initialValue = "CHANDLER_HEADERS",
    )

    deleteOnDownload = schema.One(
        schema.Boolean,
        doc = 'Whether or not to leave messages on the server after downloading',
        initialValue = False,
    )

    downloadMax = schema.One(
        schema.Integer,
        doc = 'The maximum number of messages to download. A value of 0 indicates that there is no download message limit.',
        initialValue = 0,
    )

    downloaded = schema.One(
        schema.Integer,
        doc = 'The number of messages downloaded from this account.',
        initialValue = 0,
    )


class MIMEBase(items.ContentItem):
    """Superclass for the various MIME classes"""
    mimeType = schema.One(schema.Text, initialValue = '')

    mimeContainer = schema.One() # inverse of MIMEContainer.mimeParts

    schema.addClouds(
        sharing = schema.Cloud(literal = [mimeType]),
    )


class MIMENote(MIMEBase):
    # @@@MOR This used to subclass notes.Note also, but since that superKind
    # was removed from MIMENote's superKinds list
    """MIMEBase and Note, rolled into one"""

    filename = schema.One(
        schema.Text, initialValue = u'',
    )
    filesize = schema.One(schema.Long)

    schema.addClouds(
        sharing = schema.Cloud(literal = [filename, filesize]),
    )


class MIMEContainer(MIMEBase):
    mimeParts = schema.Sequence(
        MIMEBase,
        initialValue = [],
        inverse = MIMEBase.mimeContainer,
    )

    schema.addClouds(
        sharing = schema.Cloud(
            byValue = [mimeParts]
        )
    )


class MailStamp(stamping.Stamp):
    """

    MailStamp is the bag of Message-specific attributes.

    Used to stamp a content item with mail message attributes.

    Issues:
      - Once we have attributes and a cloud defined for Attachment,
        we need to include attachments by cloud, and not by value.
      - Really not sure what to do with the 'downloadAccount' attribute
        and how it should be included in the cloud.  For now it's byValue.
    """

    schema.kindInfo(annotates = notes.Note)
    __use_collection__ = True

    mimeContent = schema.One(
        MIMEContainer,
    )

    #Commented out for Preview
    #spamScore = schema.One(schema.Float, initialValue = 0.0)
    rfc2822Message = schema.One(schema.Lob, indexed=False)

    dateSentString = schema.One(schema.Text, defaultValue='')
    dateSent = schema.One(schema.DateTimeTZ, indexed=True)
    messageId = schema.One(schema.Text, defaultValue='')

    # inverse of EmailAddress.messagesTo
    toAddress = schema.Sequence(initialValue = [],)

    # inverse of EmailAddress.messagesFrom
    fromAddress = schema.One()

    # inverse of EmailAddress.messagesOriginator
    originators = schema.Sequence()

    # inverse of EmailAddress.messagesReplyTo
    replyToAddress = schema.One(defaultValue=None)

    # inverse of EmailAddress.messagesCc
    ccAddress = schema.Sequence(initialValue = [])

    # inverse of EmailAddress.messagesBcc
    bccAddress = schema.Sequence(initialValue = [])



    @apply
    def subject():
        def fget(self):
            return self.itsItem.displayName
        def fset(self, value):
            self.itsItem.displayName = value
        return schema.Calculated(schema.Text, (items.ContentItem.displayName,),
                                 fget, fset)

    @apply
    def body():
        def fget(self):
            return self.itsItem.body
        def fset(self, value):
            self.itsItem.body = value
        return schema.Calculated(schema.Text, (items.ContentItem.body,),
                                 fget, fset)

    referencesMID = schema.Sequence(schema.Text, initialValue = [])

    inReplyTo = schema.One(schema.Text, indexed=False)


    headers = schema.Mapping(
        schema.Text, doc = 'Catch-all for headers', initialValue = {},
    )

    fromMe = schema.One(schema.Boolean, defaultValue=False, doc = "Boolean flag used to signal that the MailStamp instance contains a from or reply to address that matches one or more of the me addresses")

    toMe = schema.One(schema.Boolean, defaultValue=False, doc = "boolean flag used to signal that the MailStamp instance contains a to or cc address that matches one or more of the me addresses")

    viaMailService = schema.One(schema.Boolean, defaultValue=False, doc = "boolean flag used to signal that the mail message arrived via the mail service and thus must appear in the In Collection even if the to or cc does not contain a me address")

    isUpdated = schema.One(schema.Boolean, defaultValue=False, doc = "boolean flag used to signal whether this is a new mail or an update. There is currently no way to determine if the item is an update or new via the content model.")

    fromEIMML = schema.One(schema.Boolean, defaultValue=False, doc = "boolean flag used to signal whether mail message came from EIMML")

    previousInRecipients = schema.One(schema.Boolean, defaultValue=False, doc = "boolean flag used to signal whether the previous sender was in any of the addressing fields")


    previousSender = schema.One(defaultValue = None, doc = "The From: EmailAddress of an incoming message. The address is used to ensure the sender of the message is not lost from the workflow")

    def initialOriginators(self):
        me = getCurrentMeEmailAddress(self.itsItem.itsView)
        if me is not None:
            return [me]
        else:
            return []
    schema.initialValues(
        mimeContent=lambda self: MIMEContainer(itsView=self.itsItem.itsView,
                                               mimeType='message/rfc822'),
        fromAddress=lambda self: getCurrentMeEmailAddress(self.itsItem.itsView),
        originators=initialOriginators,
    )

    def addPreviousSenderToCC(self):
        """
            If a previous sender exists
            and is not referenced in
            the Chandler from, to, or cc
            and is not the current sender,
            add the previous sender to the
            MailStamp.ccAddress sequence.

            Returns a boolean whether the
            previous sender was added
            to the ccAdddress
        """
        previousSender = self.getPreviousSender()

        if previousSender is None:
            return False

        if self.previousInRecipients:
            # The previous sender was in the
            # addressing fields at the time of
            # download.
            return False

        currentSender = self.getSender()

        if previousSender == currentSender:
            return False

        # Since the purpose of this action is to make
        # sure the previous sender does not get
        # accidentally removed from the Edit / Update
        # workflow, the bccAddress attribute is ignored
        # because it won't be seen by all participants.
        if previousSender not in self.toAddress and \
           previousSender not in self.getRecipients(includeBcc=False,
                                                    includeSender=True):
            self.ccAddress.append(previousSender)
            return True

        return False

    def getSendableState(self):
        """
          Returns a tuple containing:
          (statusCode, numberValid, numberInvalid)

          The possilbe status codes are:

             0 = no valid addresses
             1 = some valid addresses
             2 = missing a to field
             3 = all valid addresses
        """

        # ignore originator
        # scan to, cc
        # scan bcc but only for possible not valid addresses
        # 0 = no valid addresses
        # 1 = some valid addresses
        # 2 = missing a to field
        # 3 = all valid addresses


        foundValid = 0
        foundInvalid = 0
        foundBccValid = 0
        foundBccInvalid = 0

        if len(self.toAddress) == 0:
            # A message must have at least one to
            # address to send
            return (2, 0, 0)

        for address in self.toAddress:
            if address.isValid():
                foundValid += 1
            else:
                foundInvalid += 1

        for address in self.ccAddress:
            if address.isValid():
                foundValid += 1
            else:
                foundInvalid += 1

        for address in self.bccAddress:
            if address.isValid():
                foundBccValid += 1
            else:
                foundBccInvalid += 1

        if foundValid == 0 and foundInvalid == 0 and \
           foundBccValid == 0 and foundBccInvalid == 0:
            # There are no email addresses in the mail
            return (0, 0, 0)


        if foundValid > 0 and foundInvalid == 0 and \
           foundBccInvalid == 0:
           # All addresses are valid
            return (3, foundValid + foundBccValid, 0)

        if foundValid > 0 or foundBccValid > 0:
            # At least one address is valid
            return (1, foundValid + foundBccValid,
                       foundInvalid + foundBccInvalid)

        return (0, 0, foundInvalid + foundBccInvalid)



    def getRecipients(self, includeOriginators=True,
                      includeBcc=True, includeSender=False):
        """
           Returns a list of all recipents of
           this MailStamp.

           The method filters out duplicates ie.
           the same email address in the to and
           cc.

           The recipents are determined as follows:

           1. All email addresses in the toAddress list
           2. All email addresses in the ccAddress list
           3. If includeOriginators is True, all *valid* email
              addresses in the originators list that are not
              equal to the current sender unless includeSender
              is True.
           4. If includeBcc is True, all email addresses in
              the bccAddress list
        """

        sender = self.getSender()

        recipients = []

        for address in self.toAddress:
            if address not in recipients:
                recipients.append(address)

        for address in self.ccAddress:
            if address not in recipients:
                recipients.append(address)

        if includeOriginators:
            for address in self.getOriginators():
                if includeSender and \
                   address not in recipients:
                    recipients.append(address)

                elif address != sender and \
                   address not in recipients:
                    recipients.append(address)

        if includeBcc:
            for address in self.bccAddress:
                if address not in recipients:
                    recipients.append(address)

        return recipients


    def getOriginators(self):
        originators = []

        for ea in self.originators:
            if ea is not None and ea.isValid():
                originators.append(ea)

        return originators

    def getUniqueOriginators(self):
        """
           Returns a list of all originators that:
              1. have a valid email address
              2. are not in the toAddress list
              3. are not in the ccAddress list
              4. are not in the bccAddress list
              4. are not equal to the sender
        """
        recipients  = self.getRecipients(includeOriginators=False)
        sender      = self.getSender()
        originators = self.getOriginators()

        res = []

        for originator in originators:
            if originator not in recipients and \
               originator != sender:
                res.append(originator)

        return res

    def getSender(self):
        return getattr(self, "fromAddress", None)

    def getPreviousSender(self):
        #XXX This will either be a place holder for
        # communication status or be kept as an
        # additional attribute on MailStamp.
        # The last modified by can be
        # overwritten by server based sharing
        # or mail sharing losing the last sender.
        # Keeping this info in an attribute on
        # MailStamp works around this issue
        return getattr(self, "previousSender", None)

    def isSent(self):
        return items.Modification.sent in self.itsItem.modifiedFlags

    def isAnUpdate(self):
        return self.isUpdated

    @schema.observer(fromAddress, replyToAddress, originators)
    def onFromMeChange(self, op, name):
        if op != "set":
            return

        checkIfFromMe(self)
        self.itsItem.updateDisplayWho(op, name)

    @schema.observer(toAddress, ccAddress, bccAddress)
    def onToMeChange(self, op, name):
        if op != "set":
            return

        if getattr(self, 'viaMailService', False):
            # Mail arriving via the Mail Service never
            # has its toMe value recalculated
            return

        checkIfToMe(self)
        self.itsItem.updateDisplayWho(op, name)

    schema.addClouds(
        sharing = schema.Cloud(
            byValue = [fromAddress, toAddress, dateSent,
                       ccAddress, bccAddress, replyToAddress],
        ),
        copying = schema.Cloud(
            mimeContent, dateSent,
            fromAddress, toAddress, ccAddress, bccAddress, replyToAddress,
        ),
    )

    def getHeaders(self):
        """
           Returns a Unicode string representation
           of all mail headers associated with this
           MailStamp instance.
        """
        buf = []

        for (key, val) in self.headers.items():
            buf.append(u"%s: %s" % (key, val))

        return buf and u"\n".join(buf) or u""


    def InitOutgoingAttributes(self):
        """
        Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        self.itsItem.InitOutgoingAttributes()

    @schema.observer(dateSent)
    def onDateSentChanged(self, op, name):
        self.itsItem.updateDisplayDate(op, name)

    def addDisplayDates(self, dates, now):
        dateSent = getattr(self, 'dateSent', None)
        if dateSent is not None and Modification.sent in self.itsItem.modifiedFlags:
            dates.append((50, dateSent, 'dateSent'))

    def outgoingMessage(self):
        from osaf.mail.utils import createMessageID, \
                                    dateTimeToRFC2822Date


        mId = getattr(self, "messageId", None)

        if mId:
            # set the new reply to / references logic
            # for edit / update workflows.
            self.inReplyTo = mId
            self.referencesMID.append(mId)

            # The presence of an mId indicates
            # an update. There is currently
            # no way to determine new vs. update
            # via the content model.
            self.isUpdated = True

        if self.isAnUpdate():
            # Adds the previous sender to the
            # mails cc list if the previous
            # sender is not already in one of the
            # addressing fields.
            self.addPreviousSenderToCC()

            self.previousSender = None
            self.previousInRecipients = False

        # Overwrite or add a new message Id
        self.messageId = createMessageID()

        self.dateSent = datetime.now(self.itsItem.itsView.tzinfo.default)
        self.dateSentString = dateTimeToRFC2822Date(self.dateSent)
        self.fromEIMML = False

        if len(self.originators) == 0:
            # We've been lazily defaulting the "From:" field to the "Send As"
            # value, but now that the message is really heading out, fix
            # the "From:" field so that subsequent updaters won't do this lazy
            # defaulting.
            self.originators.add(self.fromAddress)


        if Modification.sent in self.itsItem.modifiedFlags:
            modFlag = Modification.updated
        else:
            modFlag = Modification.sent

        # XXX - Grant, please change this once pim.CHANGE_ALL or an equivalent
        # mechanism works with changeEditState
        items = [self.itsItem]
        if has_stamp(self.itsItem, EventStamp):
            items.extend(EventStamp(self.itsItem).getMaster().modifications 
                         or [])
        for item in items:
            item.changeEditState(modFlag, self.getSender(), self.dateSent)

        # Commit the changes to the MailStamped Item.
        # The commit is needed at this point since
        # the Item could be the recurrence master but the
        # instance actually being sent is an occurrence.
        self.itsItem.itsView.commit()

    def incomingMessage(self, ignoreMe=False):
        view = self.itsItem.itsView

        # Flags to indicate that this message arrived via the
        # maill service and thus will appear in the In collection
        # regardless of whether the to or cc of the message
        # contain a me address.
        self.viaMailService = True
        self.toMe = True

        if ignoreMe:
            sender = self.getSender()

            if isMeAddress(sender):
                self.toMe = False

        # Flag indicating that the previous sender
        # was in the addressing fields when the mail
        # was downloaded. The previous sender
        # should be add to the cc list if not
        # in the addressing fields unless the
        # previous sender was removed by the 
        # current sender.
        self.previousInRecipients = self.previousSender in \
                           self.getRecipients(includeBcc=False,
                                              includeSender=True)

        # For Preview we add all downloaded mail via POP and IMAP
        # accounts to the Dashboard.
        schema.ns('osaf.pim', view).allCollection.add(self.itsItem)

        self.itsItem.mine = True
        self.itsItem.read = False

        if self.isUpdated:
            # Updated Items:
            #   Do not change existing buttonTriageStatus
            #   Set sectionTriageStatus to NOW
            triageArg = None
        else:
            # New Items:
            #   buttonTriageStatus is set to NOW
            #   sectionTriageStatus is set to NOW
            triageArg = "auto"


        log.info("Mail Service popping item '%s (%s)' to NOW" % \
                (self.itsItem.displayName.encode("utf-8"), self.itsItem.itsUUID))

        setTriageStatus(self.itsItem, triageArg, popToNow=True)

        if not self.fromEIMML:
            if Modification.sent in self.itsItem.modifiedFlags:
                modFlag = Modification.updated
            else:
                modFlag = Modification.sent

            self.itsItem.changeEditState(modFlag,
                                         self.getSender(),
                                         self.dateSent)

    def getAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        content = self.mimeContent # Never raises b/c defaultValue
        if content is None:
            return []
        else:
            return list(content.mimeParts or [])

    def getNumberOfAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        return len(self.getAttachments())

    def getSendability(self, ignoreAttr=None):
        """
        Return whether this item is ready to send:
         'send': Item is sendable, would be a first-time send
         'update': Item is sendable, would be an update to a previous send
         'not': Item is not sendable (e.g. not addressed)
         'sent':  Item is not sendable; it was just sent.

        If ignoreAttr is specified, don't verify that value
        (because it's being edited in the UI and is known to be valid,
        and will get saved before sending).
        """

        lastModification = self.itsItem.lastModification

        # You can't send unless you've made changes
        if (lastModification in (
                    Modification.sent,
                    Modification.queued,
                    Modification.updated
                ) and not self.itsItem.error):
            return 'sent'

        # Addressed?
        # (This test will get more complicated when we add cc, bcc, etc.)
        sendable = ((ignoreAttr == 'toAddress' or len(self.toAddress) > 0) and
                    (ignoreAttr == 'fromAddress' or self.fromAddress is not None))

        if not sendable:
            return 'not'

        if Modification.sent in self.itsItem.modifiedFlags:
            return 'update'
        else:
            return 'send'


def MailMessage(*args, **keywds):
    """Return a newly created Note, stamped with MailStamp."""
    note = notes.Note(*args, **keywds)
    message = MailStamp(note)

    message.add()
    return message


class MIMEBinary(MIMENote):
    data = schema.One(schema.Lob, indexed=False)


class MIMEText(MIMENote):

    charset = schema.One(
        schema.Text,
        initialValue = 'utf-8',
    )
    lang = schema.One(
        schema.Text,
        initialValue = 'en',
    )

    data = schema.One(schema.Text, indexed=False)

class MIMESecurity(MIMEContainer):
    pass

class CollectionInvitation(schema.Annotation):
    schema.kindInfo(annotates = collections.ContentCollection)

    invitees = schema.Sequence(
        doc="The people who are being invited to share in this item; filled "
        "in when the user types in the DV's 'invite' box, then cleared on "
        "send (entries copied to the share object).\n\n"
        "Issue: Bad that we have just one of these per item collection, "
        "though an item collection could have multiple shares post-0.5",
        defaultValue=Empty,
    ) # inverse of EmailAddress


class EmailAddresses(items.ContentItem):
     emailAddresses = schema.Sequence(
     doc = 'List of Email Addresses',
     initialValue = [],
   )

class EmailAddress(items.ContentItem):
    """An item that represents a simple email address, plus
all the info we might want to associate with it, like
lists of message to and from this address.

Example: abe@osafoundation.org

Issues:
   Someday we might want to have other attributes.  One example
   might be an 'is operational' flag that tells whether this
   address is still in service, or whether mail to this has been
   bouncing lately. Another example might be a 'superseded by'
   attribute, which would point to another Email Address item.

"""

    schema.kindInfo(notify = False) # no 'refresh' notifs on this kind

    emailAddress = schema.One(
        schema.Text,
        doc = 'The email address.\n\n'
            "Examples:\n"
            '   "abe@osafoundation.org"\n',
        indexed = True,
        initialValue = u'',
    )
    fullName = schema.One(
        schema.Text,
        doc = 'A first and last name associated with this email address',
        indexed = True,
        initialValue = u'',
    )

    #vcardType = schema.One(
    #    schema.Text,
    #    doc = "Typical vCard types are values like 'internet', 'x400', and "
    #          "'pref'. Chandler will use this attribute when doing "
    #          "import/export of Contact records in vCard format.",
    #    initialValue = u'',
    #)

    accounts = schema.Sequence(
        OutgoingAccount,
        doc = 'A list of Outgoing Accounts that use this Email Address as the '
              'from address for mail sent from the account.',
        initialValue = [],
        inverse = OutgoingAccount.fromAddress,
    )

    messagesBcc = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their Bcc: header referring to this address',
        initialValue = [],
        inverse = MailStamp.bccAddress,
    )

    messagesCc = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their cc: header referring to this address',
        initialValue = [],
        inverse = MailStamp.ccAddress,
    )

    messagesFrom = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their From: header referring to this address',
        initialValue = [],
        inverse = MailStamp.fromAddress,
    )

    messagesReplyTo = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their Reply-To: header referring to this address',
        initialValue = [],
        inverse = MailStamp.replyToAddress,
    )

    messagesTo = schema.Sequence(
        MailStamp,
        doc = 'A list of messages with their To: header referring to this address',
        initialValue = [],
        inverse = MailStamp.toAddress,
    )

    messagesOriginator = schema.Sequence(
        MailStamp,
        doc = 'A list of messages whose "originators" contain this address',
        initialValue = [],
        inverse = MailStamp.originators,
    )

    inviteeOf = schema.Sequence(
        collections.ContentCollection,
        doc = 'List of collections that the user is about to be invited to share with.',
        inverse = CollectionInvitation.invitees,
    )

    schema.addClouds(
        sharing = schema.Cloud(literal = [emailAddress, fullName])
    )

    itemsLastModified = schema.Sequence(
        items.ContentItem,
        doc="List of content items last modified by this user.",
        inverse=items.ContentItem.lastModifiedBy
    )

    @schema.observer(emailAddress)
    def onEmailAddressChange(self, op, attr):
        # If this address matches a "me" address (presumably, with different
        # fullname or case, add it to the "me" list too.
        emailAddress = getattr(self, 'emailAddress', u'')
        if emailAddress != u'':
            view = self.itsView
            collection = schema.ns("osaf.pim", view).meEmailAddressCollection
            if self not in collection.inclusions:
                lowerAddress = emailAddress.lower()
                def compareAddressOnly(uuid):
                    return cmp(lowerAddress,
                               view.findValue(uuid, 'emailAddress').lower())
                match = collection.findInIndex('emailAddress', 'exact', compareAddressOnly)
                if match is not None:
                    if __debug__:
                        log.debug("Is me: '%s'", self)
                    collection.append(self)

    def __str__(self):
        if self.isStale():
            return super(EmailAddress, self).__str__()

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        """
        User readable string version of this address.
        """
        if self.isStale():
            return super(EmailAddress, self).__unicode__()
            # Stale items shouldn't go through the code below

        fullName = getattr(self, 'fullName', u'')
        if len(fullName) > 0:
            if self.emailAddress:
                return fullName + u' <' + self.emailAddress + u'>'
            else:
                return fullName

        elif self is getCurrentMeEmailAddress(self.itsView):
            return messages.ME
        else:
            return unicode(getattr(self, 'emailAddress', self.itsName) or
                           self.itsUUID.str64())


    def format(self, encode=False):
        if self.fullName is not None and \
           len(self.fullName.strip()) > 0:
            if encode:
                from email.Header import Header
                return Header(self.fullName).encode() + u" <" + \
                              self.emailAddress + u">"
            else:
                return self.fullName + u" <" + self.emailAddress + u">"

        return self.emailAddress

    def getLabel(self):
        """ 
        Get a possibly-shortened version of this address;
        used in the byline and "Who" column.
        """
        # Use the fullname if we have it
        label = unicode(self.fullName)
        if len(label) == 0:
            # no fullname - show the email account part, if it looks like
            # an email address
            label = self.emailAddress
            atIndex = label.find(u"@")
            if atIndex != -1:
                label = label[:atIndex]
        return label

    def isValid(self):
        """ See if this address looks valid. """

        if self.emailAddress is None:
            return False

        return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", self.emailAddress) is not None

    def getShortenedDisplayAddress(self, stringCanFit):
        """
        @param stringCanFit: callback to test the newly shortened address
        @type nameOrAddressString: C{bound method}

        @return: C{String} if possible, the shortened address, otherwise
        the first character
        """
        # 'address' will never contain an ellipsis ("..."), although it will be
        # the "shortened version".
        # 'tryAddress' is the version of the address with one or more
        # ellipses in it, which is built each time throgh the loop, based on the
        # current value of 'address' and a
        address = unicode(self)
        tryAddress = address
        addressIsTooShort = False
        ellipsis = u"..."
        minimumLength = 2
        while not stringCanFit(tryAddress) and not addressIsTooShort:
            atLocation = address.find("@")
            if atLocation >= 0:
                before = address[:atLocation]
                after = address[atLocation+1:]
                # check for either degenerate <char>... case or
                # single-letter case
                if len(after) > 1:
                    # try shrinking the domain
                    address = u"%s@%s" % (before, after[:-1])
                    tryAddress = u"%s@%s..." % (before, after[:-1])
                elif len(before) > 1:
                    # domain has been shortened to one character, so
                    # shorten the username
                    address = u"%s@%s" % (before[:-1], after)
                    tryAddress = u"%s...@%s" % (before[:-1], after)
                else:
                    # the address can't be shortened any more
                    addressIsTooShort = True
            else:
                # no "@" sign, must be a plain email address, so just
                # shorten it by one, if it's long enough
                if len(address) > minimumLength:
                    address = address[:-1]
                    tryAddress = u"%s..." % address
                else:
                    addressIsTooShort = True

        return tryAddress

    @classmethod
    def getEmailAddress(cls, view, nameOrAddressString, fullName=u'', create=True):
        """
        Factory Method
        --------------
        When creating a new EmailAddress, we check for an existing item first.
        We do look them up in the repository to prevent duplicates, but there's
        nothing to keep bad ones from accumulating, although repository
        garbage collection should eventually remove them.

        If a matching EmailAddress object is found in the repository, it
        is returned. If there is no match, but create is True, then a new item 
        is created and returned; otherwise, None will be returned.

        There are two ways to call this method:
          1. with something the user typed in nameOrAddressString, which
             will be parsed, and no fullName is needed
          2. with an plain email address in the nameOrAddressString, and a
             full name in the fullName field

        If an exact match is found for both name and address then it will be 
        returned; otherwise, a new EmailAddress item will be created and 
        returned. (None will be returned if both name and address are essentially
        empty.)

        @param nameOrAddressString: emailAddress string, or fullName for lookup,
        or both in the form "name <address>"
        @type nameOrAddressString: C{unicode}
        @param fullName: optional explict fullName when not using the
        "name <address>" form of the nameOrAddressString parameter
        @type fullName: C{unicode}

        @return: C{EmailAddress} or None if not found, and nameOrAddressString is\
        not a valid email address.
        """
        if nameOrAddressString is None:
            return None

        # strip the address string of whitespace and question marks
        address = nameOrAddressString.strip ().strip(u'?')

        # if no fullName specified, parse apart the name and address if we can
        if fullName != u'':
            name = fullName
        else:
            try:
                address.index(u'<')
            except ValueError:
                name = u''
            else:
                name, address = address.split(u'<')
                address = address.strip(u'>').strip()
                name = name.strip()
                # ignore a name of "me"
                if name == messages.ME:
                    name = u''

        # If we have nothing to search for, give up
        if address == u'' and name == u'':
            return None

        # See if we have this address
        collection = schema.ns("osaf.pim", view).emailAddressCollection
        def compareBothParts(uuid):
            targetAddress, targetName = view.findValues(uuid, ('emailAddress', u''),
                                                              ('fullName', u''))
            return cmp(address, targetAddress) or cmp(name, targetName)
        match = collection.findInIndex('both', 'exact', compareBothParts)
        if match:
            if __debug__:
               log.debug("Returning existing email address '%s' for '%s'/'%s'",
                         unicode(view[match]), name, address)
            return view[match]

        # no match - create a new address
        if create:
            if __debug__:
               log.debug("Making new email address for '%s'/'%s'", name, address)

            newAddress = EmailAddress(itsView=view, emailAddress=address,
                                      fullName=name)
            return newAddress

        # no match, but not create
        return None        

    @classmethod
    def generateMatchingEmailAddresses(cls, view, partialAddress):
        """
        Generate any EmailAddresses whose emailAddress or fullName starts
        with this. (Used for autocompletion.)
        """
        collection = schema.ns("osaf.pim", view).emailAddressCollection
        partialAddress = unicode(partialAddress).lower()
        for indexName in ('emailAddress', 'fullName'):
            def _compare(uuid):
                attrValue = view.findValue(uuid, indexName).lower()
                if attrValue.startswith(partialAddress):
                    return 0
                return cmp(partialAddress, attrValue)
            firstUUID = collection.findInIndex(indexName, 'first', _compare)

            if firstUUID is None:
                continue

            lastUUID = collection.findInIndex(indexName, 'last', _compare)
            for uuid in collection.iterindexkeys(indexName, firstUUID, lastUUID):
                match = view[uuid]
                if unicode(match).lower() != partialAddress:
                    yield match

    @classmethod
    def isValidEmailAddress(cls, emailAddress):
        """
        This method tests an email address for valid syntax as defined RFC 822.
        The method validates addresses in the form 'John Jones <john@test.com>'
        and 'john@test.com'

        (Note that we're perfectly happy for EmailAddress items to hold invalid
        or incomplete addresses; this classmethod is used when we need to ensure that
        an address is valid. If you want to ensure that a particular EmailAddress
        object is valid, you can call its isValid method, which'll call this.)

        @param emailAddress: A string containing a email address to validate.
        @type emailAddress: C{String}
        @return: C{Boolean}
        """

        assert isinstance(emailAddress, (str, unicode))

        emailAddress = Utils.parseaddr(emailAddress)[1]

        return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", emailAddress) is not None

    @classmethod
    def parseEmailAddresses(cls, view, addressesString, create=True):
        """
        Parse the email addresses in addressesString and return
        a tuple with: (the processed string, a list of EmailAddress
        items created/found for those addresses, the number of
        bad addresses we found). if Create is false, only existing EmailAddress
        items will be returned - the others will be counted as invalid addresses.

        Note: Now that we're no longer checking validity of addresses,
        invalidCount will always be zero unless the structure of the string
        is bad (like ",,,")
        """
        # If we got nothing or whitespace, return it as-is.
        if addressesString.strip() == u'':
            return (addressesString, [], 0)

        validAddresses = []
        processedAddresses = []
        invalidCount = 0

        # get the user's address strings into a list; tolerate
        # commas or semicolons as separators
        addresses = [ address.strip() for address in \
                      addressesString.replace('?','').replace(';', ',').split(',') ]

        # build a list of all processed addresses, and all valid addresses
        for address in addresses:
            ea = EmailAddress.getEmailAddress(view, address, create=create)
            if ea is None:
                processedAddresses.append(address + '?')
                invalidCount += 1
            else:
                processedAddresses.append(unicode(ea))
                validAddresses.append(ea)

        # prepare the processed addresses return value
        processedResultString = _(u', ').join(processedAddresses)
        return (processedResultString, validAddresses, invalidCount)


def makeCompareMethod(attrName):
    def compare(self, index, u1, u2, vals):
        if u1 in vals:
            v1 = vals[u1]
        else:
            v1 = self.itsView.findValue(u1, attrName).lower()
        if u2 in vals:
            v2 = vals[u2]
        else:
            v2 = self.itsView.findValue(u2, attrName).lower()
        return cmp(v1, v2)
    def compare_init(self, index, u, vals):
        return self.itsView.findValue(u, attrName).lower()
    return compare, compare_init

class EmailComparator(schema.Item):
    # For separately indexing emailAddress and fullName, case-insensitively
    cmpAddress, cmpAddress_init = makeCompareMethod('emailAddress')
    cmpFullName, cmpFullName_init = makeCompareMethod('fullName')

    # For indexing both attributes, case-sensitively
    bothValues = (('emailAddress', u''),
                  ('fullName', u''))
    def cmpBoth(self, index, u1, u2, vals):
        if u1 in vals:
            v1 = vals[u1]
        else:
            v1 = self.itsView.findValues(u1, *EmailComparator.bothValues)
        if u2 in vals:
            v2 = vals[u2]
        else:
            v2 = self.itsView.findValues(u2, *EmailComparator.bothValues)
        return cmp(v1, v2)
    def cmpBoth_init(self, index, u, vals):
        return self.itsView.findValues(u, *EmailComparator.bothValues)

# Map from account type strings to account types

ACCOUNT_TYPES = {
    'POP': POPAccount,
    'SMTP': SMTPAccount,
    'IMAP': IMAPAccount,
}


