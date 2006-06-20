#!/usr/local/bin/python
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

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.mail.smtp import sendmail
from twisted.internet import defer
from twisted.internet import stdio
import email
import re
from email import Encoders, Parser, Message
from twisted.protocols import basic

class SMTPMessageInput(LineReceiver):
    from os import linesep as delimiter

    (HOST, TO, FROM, SUBJECT, BODY) = range(5)

    def __init__(self, debug=0):
        self._host = None
        self._to = None
        self._from = None
        self._subject = None
        self._body = []
        self._flag = 0
        self._debug = debug
        self._re = re.compile(r'^\s*\.\s*$')

    def connectionMade(self):
       self.display()

    def printMsg(self, msg): 
        msg += "\n" 
        self.transport.write(msg)

    def display(self):
        msg = ""

        if self._flag == self.HOST:
            msg = "Hostname: "

        elif self._flag == self.TO:
            msg = "To: "

        elif self._flag == self.FROM:
            msg = "From: "

        elif self._flag == self.SUBJECT:
            msg = "Subject: "

        else:
            msg = "================ Message Body ==============\n"

        self.transport.write(msg)

    def lineReceived(self, line): 
        if self._debug: 
             str = "Flag: %d, Received: %s" % (self._flag, line)
             self.printMsg(str)

        if self._flag == self.HOST:
            self._host = line
        elif self._flag == self.TO:
            self._to = line
        elif self._flag == self.FROM:
            self._from = line
        elif self._flag == self.SUBJECT:
           self._subject = line

        elif self._flag == self.BODY:

          if self._re.search(line):
              d = defer.Deferred().addCallback(self._sendMail)
              d.callback(True)

          else:
             self._body.append(line)

        if self._flag != self.BODY:
            self._flag += 1
            self.display()


    def _sendMail(self, result):
        body = "\r\n".join(self._body)

        m = Message.Message()
        m.set_payload(body)
        m['Subject'] = self._subject
        m['From'] = self._from
        m['To'] = self._to

        s = m.as_string()

        if self._debug:
             self.printMsg("Message:\n %s" % s)

        return sendmail(self._host, self._from, self._to, s
                      ).addCallback(self._messageSent).addErrback(self._sendError)

    def _messageSent(self, result):
            msg = "\n\n==================== MESSAGE SENT ================\n\n"
            self.printMsg(msg)
            reactor.stop()

    def _sendError(self, reason): 
            self.printMsg("\n===================SMTP ERROR ==================")
            print reason
            reactor.stop()


print "\n=========================== SMTP Protocol Client ========================\n"

smtpInput = SMTPMessageInput()
stdio.StandardIO(smtpInput)
reactor.run()


