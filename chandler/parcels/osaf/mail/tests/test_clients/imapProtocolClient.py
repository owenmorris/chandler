#!/usr/local/bin/python

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys
from twisted.internet import defer
from twisted.internet import stdio


from twisted.protocols import basic

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

    def dataReceived(self, data):
        print "\n", data
        self.io.display()

    def sendCommand(self, cmd):
        cmd = "%d %s" % (self._cmdNumber, cmd)
        self.sendLine(cmd)
        self._cmdNumber += 1

    def disconnect(self): 
        self.transport.loseConnection()

class ClientConnectorFactory(ClientFactory):
    protocol = ImapProtocolClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print '\n================ %s =====================\n' % reason.getErrorMessage()
        reactor.stop()


print "\n=========================== Imap Protocol Client ========================\n"

host = raw_input(">>> Hostname: ")
factory = ClientConnectorFactory()
reactor.connectTCP(host, 143, factory)
reactor.run()
