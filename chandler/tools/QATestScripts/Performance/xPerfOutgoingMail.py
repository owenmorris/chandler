#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import tools.QAUITestAppLib as QAUITestAppLib
from osaf.mail.message import kindToMessageText
from osaf.pim import MailStamp, EventStamp, TaskStamp, notes
from osaf.pim.mail import EmailAddress
from i18n.tests import uw
from datetime import datetime, timedelta
import random
from osaf.pim.calendar import Calendar
from osaf import pim
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet

# Globals
app_ns = app_ns()
view = app_ns.itsView

OUTGOING_TEST_CASES = [
("", "Mail"),
("E", "MailEvent"),
("T", "MailTask"),
("ET", "MailEventTask"),
("R", "MailRecurringEvent"),
("RT", "MailRecurringEventTask"),
]

logger = QAUITestAppLib.QALogger("PerfOutgoingMail.log", "message.kindToMessageText")

# If running with --catsProfile, we don't want to include
# all the setup code in the output profile.
logger.SuspendProfiling()


def randomEnum(cls):
    return getattr(cls, cls.values.keys()[random.randint(0, len(cls.values)-1)])

def addEventStamp(item, recur=False):
    es = EventStamp(item)
    es.add()
    es.summary = uw("Test Event Summary")

    tzinfo = item.itsView.tzinfo.floating

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


try:
    # Test Phase: Action
    # ResumeProfiling() will make the logger start profiling
    # in Start().
    logger.ResumeProfiling()

    try:

        for case in OUTGOING_TEST_CASES:
            action, logName = case

            item = notes.Note(itsView=view)

            ms = addMaiStamp(item)

            if "E" in action:
                addEventStamp(item)

            if "T" in action:
                addTaskStamp(item)

            if "R" in action:
                addEventStamp(item, recur=True)

            logger.Start(logName)
            ms.outgoingMessage()
            text = kindToMessageText(ms)

            # Commiting of message conversion is
            # part of the performance metrics.
            view.commit()
            logger.Stop()

            # Test Phase: Verification
            logger.SetChecked(True)
            logger.Report(logName)

    except Exception, e:
        import logging
        logging.exception(e)
finally:
    # cleanup
    logger.Close()

