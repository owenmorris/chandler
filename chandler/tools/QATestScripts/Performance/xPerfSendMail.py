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

import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

logger = QAUITestAppLib.QALogger("PerfSendMail.log", "SendMail")

# If running with --catsProfile, we don't want to include
# all the setup code in the output profile.
logger.SuspendProfiling()

SEND_TEST_CASES = [
("", "Mail"),
("E", "MailEvent"),
("T", "MailTask"),
("ET", "MailEventTask"),
]

COUNTER = 0

def getCounterNext():
    global COUNTER

    COUNTER += 1

    return COUNTER


def createAccounts():
    ap = QAUITestAppLib.UITestAccounts(logger)

    pSMTP   = uw("Personal SMTP")
    pIMAP   = uw("Personal IMAP")
    pEMAIL  = "demo1@osafoundation.org"
    pNAME   = uw("Demo One")

    # action
    ap.Open() # first, open the accounts dialog window

    ap.GetDefaultAccount("OUTGOING")
    ap.TypeValue("displayName", pSMTP) # type the following values into their apporpriate fields
    ap.TypeValue("host","smtp.osafoundation.org")
    ap.SelectValue("security",  'TLS') # select the TLS radio button
    ap.ToggleValue("authentication", True) # turn on the authentication checkbox
    ap.TypeValue("port", '587')
    ap.TypeValue("email", pEMAIL)
    ap.TypeValue('username', 'demo1')
    ap.TypeValue('password', 'ad3leib5')

    ap.GetDefaultAccount("INCOMING")
    ap.TypeValue("displayName", pIMAP)
    ap.TypeValue("email", pEMAIL)
    ap.TypeValue("name", pNAME)
    ap.TypeValue("host", "imap.osafoundation.org")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.SelectValue("security", "SSL")
    ap.SelectValue("protocol", "IMAP")

    ap.Ok()

def sendMail(type, logName):
    mail = QAUITestAppLib.UITestItem("MailMessage", None)

    pt = uw("Performance Test")

    attrs = {
       "displayName": u"[%s] %s" % (getCounterNext(), pt),
       "toAddress": "demo2@osafoundation.org",
       "body": "%s " % pt * 15,
    }


    if "E" in type:
        mail.StampAsCalendarEvent(True, timeInfo=False)

        attrs["startDate"] ="3/2/2007"
        attrs["startTime"] = "6:00 PM"
        attrs["endTime"] = "7:00PM"
        attrs["location"] = uw("Performance Test Location")
        attrs["status"] = "FYI"

    if "T" in type:
        mail.StampAsTask(True, timeInfo=False)

    mail.SetAttr(**attrs)

    logger.Start(logName)
    mail.SendMail(timeInfo=False)
    logger.Stop()

    # Test Phase: Verification
    logger.SetChecked(True)
    logger.Report(logName)

try:
    # Test Phase: Action
    # ResumeProfiling() will make the logger start profiling
    # in Start().
    logger.ResumeProfiling()

    createAccounts()

    for case in SEND_TEST_CASES:
        type, logName = case
        sendMail(type, logName)

except Exception, e:
    import logging
    logging.exception(e)

finally:
    logger.Close()
