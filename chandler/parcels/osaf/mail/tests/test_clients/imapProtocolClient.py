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
from twisted.internet import defer
from twisted.internet import stdio
from twisted.internet import ssl
from twisted.protocols import basic
import sys

USER=None
PASS=None
TIMER=3*60 #3 minutes

class TerminalIO(LineReceiver):
    from os import linesep as delimiter

    def __init__(self, proto):
        self.proto = proto

    def display(self):
        self.transport.write(">>> ")

    def lineReceived(self, line):
        self.proto.sendCommand(line)

class ImapProtocolClient(LineReceiver):

    def __init__(self):
        self._cmdNumber = 1
        self.io = TerminalIO(self)
        stdio.StandardIO(self.io)
        self.first = True
        self.stop  = False

    def sendNoop(self):
        if not self.stop:
            cmd = "NOOP"
            self.sendCommand(cmd)
            self.io.transport.write(cmd)
            reactor.callLater(TIMER, self.sendNoop)

    def dataReceived(self, data):
        print "\n", data
        self.io.display()

        if self.first:
            reactor.callLater(TIMER, self.sendNoop)

            if USER and PASS:
                cmd = "login %s %s" % (USER, PASS)
                self.sendCommand(cmd)
                self.io.transport.write(cmd)
                self.first = False

    def sendCommand(self, cmd):
        cmd = "%d %s" % (self._cmdNumber, cmd)
        self.sendLine(cmd)
        self._cmdNumber += 1

    def disconnect(self):
        self.stop = True
        self.transport.loseConnection()

class ClientConnectorFactory(ClientFactory):
    protocol = ImapProtocolClient

    def clientConnectionFailed(self, connector, reason):
        self.stop = True
        try:
            reactor.stop()
        except:
            pass

    def clientConnectionLost(self, connector, reason):
        self.stop = True
        try:
            reactor.stop()
        except:
            pass

if len(sys.argv) >= 4:
    #program name, host, port, useSSL
    host = sys.argv[1]
    port = int(sys.argv[2])
    useSSL = sys.argv[3]

    if len(sys.argv) == 6:
        USER = sys.argv[4]
        PASS = sys.argv[5]

    print "\n=========================== IMAP4 Protocol Client [%s] ==============\n" % host

else:
    print "\n=========================== IMAP4 Protocol Client ========================\n"
    host = raw_input(">>> Hostname: ")
    port = int(raw_input(">>> Port: "))
    useSSL = raw_input(">>> SSL (y/n): ")

factory = ClientConnectorFactory()

if useSSL.startswith("y"):
    context = ssl.ClientContextFactory()
    context.method = ssl.SSL.TLSv1_METHOD
    reactor.connectSSL(host, port, factory, context)
else:
    reactor.connectTCP(host, port, factory)

reactor.run()
