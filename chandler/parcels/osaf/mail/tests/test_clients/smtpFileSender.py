#!/usr/local/bin/python
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

from twisted.internet import reactor
from twisted.mail.smtp import sendmail
from twisted.internet import defer
import sys

class TransportInfo:
    hostname  = "localhost"
    rcpt_to   = ["testuser@kauai.osafoundation.org"]
    mail_from = "brian@test.com"

def sendMail(file):
    fp = open(file)
    data = fp.read()
    fp.close()

    return sendmail(TransportInfo.hostname,
                    TransportInfo.mail_from,
                    TransportInfo.rcpt_to,
                    data, port=2500
                    ).addCallback(_messageSent, file).addErrback(_sendError, file)

def _messageSent(result, file):
    print "\n==================== MESSAGE SENT: '%s' ================\n" % file
    reactor.stop()

def _sendError(reason, file):
    print "\n===================SMTP ERROR: '%s' ==================\n" % file
    reactor.stop()

reactor.callLater(0, sendMail, sys.argv[1])
reactor.run()


