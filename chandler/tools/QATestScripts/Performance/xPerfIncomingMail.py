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
import os
from osaf.mail.message import messageTextToKind, parseEventInfo, parseTaskInfo
from osaf.pim import MailStamp

# Globals
app_ns = app_ns()
view = app_ns.itsView

INCOMING_TEST_CASES = [
("EIMMLMessageTest.eml", "EIMMLMessage"),
("EIMMLTaskTest.eml", "EIMMLTask"),
("EIMMLEventTest.eml", "EIMMLEvent"),
("EIMMLEventRecurringTest.eml", "EIMMLEventRecurring"),
("EIMMLTaskEventTest.eml", "EIMMLTaskEvent"),
("ChandlerMailFolderTest.eml", "ChandlerMailFolder"),
("ChandlerMailFolderAttachmentTest.eml", "ChandlerMailFolderAttachmentTest"),
("ChandlerTaskFolderTest.eml", "ChandlerTaskFolder", "T"),
("ChandlerEventFolderTest.eml", "ChandlerEventFolder", "E"),
("ICSTaskTest.eml", "ICSTask"),
("ICSEventTest.eml", "ICSEvent"),
("ICSRecurringEventTest.eml", "ICSRecurringEvent"),
("ICSTaskEventTest.eml", "ICSTaskEvent"),
]

logger = QAUITestAppLib.QALogger("PerfIncomingMail.log", "message.messageTextToKind")


# If running with --catsProfile, we don't want to include
# all the setup code in the output profile.
logger.SuspendProfiling()

def loadMailFile(fileName):
    mailFile = os.path.join(os.getenv('CHANDLERHOME'),"tools", "cats",
                            "DataFiles", "MailDataFiles", fileName)

    f = open(mailFile, "r")
    mailText = f.read()
    f.close()

    return mailText

try:
    # Test Phase: Action
    # ResumeProfiling() will make the logger start profiling
    # in Start().
    logger.ResumeProfiling()

    for case in INCOMING_TEST_CASES:
        try:
            action = None

            if len(case) == 3:
                file, logName, action = case
            else:
                file, logName = case

            mailText = loadMailFile(file)

            logger.Start(logName)

            item = messageTextToKind(view, mailText)
            ms = MailStamp(item)

            if action:
                if action == "E":
                    parseEventInfo(ms)
                elif action == "T":
                    parseTaskInfo(ms)

            ms.incomingMessage()

            # Commiting of a parsed message is
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
