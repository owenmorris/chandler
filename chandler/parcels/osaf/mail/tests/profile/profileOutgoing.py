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


from osaf.mail.message import kindToMessageText
from osaf.pim import MailStamp, EventStamp, TaskStamp, notes
from osaf.pim.mail import EmailAddress
from i18n.tests import uw
from datetime import datetime, timedelta
import random
from osaf.pim.calendar import Calendar
from osaf import pim
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from util.easyprof import QuickProfile
from repository.persistence.RepositoryView import NullRepositoryView
import sys

view = NullRepositoryView()

ARG_LOOKUP = {
"": "Mail",
"M": "Mail",
"E": "Event",
"T": "Task",
"R": "RecurringEvent",
}

def getOpts():
    try:
        return sys.argv[1]
    except:
        return ""

def randomEnum(cls):
    return getattr(cls, cls.values.keys()[random.randint(0, len(cls.values)-1)])

def addEventStamp(item, recur=False):
    es = EventStamp(item)
    es.add()
    es.summary = uw("Test Event Summary")

    tzinfo = view.tzinfo.floating

    # Choose random days, hours
    startDelta = timedelta(days=random.randint(0, 30),
                           hours=random.randint(0, 24))

    now = datetime.now(tzinfo)

    closeToNow = datetime(now.year, now.month, now.day, now.hour,
                          int(now.minute/30) * 30, tzinfo=now.tzinfo)

    es.startTime = closeToNow + startDelta
    es.anyTime = True

    # Choose random minutes
    es.duration = timedelta(minutes=60)

    es.location = Calendar.Location.getLocation(view, uw("My House"))

    es.itsItem.importance = random.choice(pim.ImportanceEnum.values)

    es.itsItem.setTriageStatus(randomEnum(pim.TriageEnum))

    if recur:
        rule = RecurrenceRule(itsView=view)
        rule.freq = 'daily'
        rule.until =  datetime(2008, 9, 14, 19, tzinfo=view.tzinfo.default)
        rule.untilIsDate = False

        ruleSet = RecurrenceRuleSet(itsView=view)
        ruleSet.addRule(rule)

        es.rruleset = ruleSet

    return es

def addTaskStamp(item):
    ts = TaskStamp(item)
    ts.add()

    ts.summary = uw("Test Task Summary")
    ts.itsItem.setTriageStatus(randomEnum(pim.TriageEnum))
    return ts


def addMaiStamp(item):
    ms = MailStamp(item)
    ms.add()

    ms.subject = uw("Test Mail")
    ms.body = uw("Test ") * 60

    toAddr = EmailAddress.getEmailAddress(view, "demo2@osafoundation.org")
    ms.toAddress.append(toAddr)

    ms.fromAddress = EmailAddress.getEmailAddress(view, "demo3@osafoundation.org")

    ms.ccAddress.append(ms.fromAddress)

    org = EmailAddress.getEmailAddress(view, "The Management")
    ms.originators.append(org)

    return ms

def profile(ms, profFile):

    @QuickProfile(profFile)
    def _profile():
        ms.outgoingMessage()
        text = kindToMessageText(ms)

    _profile()

try:
    action = getOpts()
    profName = []

    for arg in action:
        profName.append(ARG_LOOKUP[arg])

    profName = "".join(profName)

    if not "Mail" in profName:
        profName = "Mail%s" % profName

    item = notes.Note(itsView=view)

    ms = addMaiStamp(item)

    if "E" in action:
        addEventStamp(item)

    if "T" in action:
        addTaskStamp(item)

    if "R" in action:
        addEventStamp(item, recur=True)

    profile(ms, "%s.prof" % profName)

except Exception, e:
    import logging
    logging.exception(e)
