#!/usr/bin/python

# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Simple IMAP4 client which displays the subjects of all messages in a 
particular mailbox.
"""

import sys

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.test.ssl_helpers import ClientTLSContext
from twisted.internet import ssl
from twisted.internet import defer
from twisted.internet import stdio
from twisted.mail import pop3client
from twisted.protocols import basic
from twisted.python import util
from twisted.python import log

class TrivialPrompter(basic.LineReceiver):
    from os import linesep as delimiter

    promptDeferred = None
    
    def prompt(self, msg):
        assert self.promptDeferred is None
        self.display(msg)
        self.promptDeferred = defer.Deferred()
        return self.promptDeferred
    
    def display(self, msg):
        self.transport.write(msg)
    
    def lineReceived(self, line):    
        if self.promptDeferred is None:
            return
        d, self.promptDeferred = self.promptDeferred, None
        d.callback(line)

class SimplePOP3Client(pop3client.POP3Client):
    greetDeferred = None
    allowInsecureLogin = True
    
    def serverGreeting(self, challenge):
        if self.greetDeferred is not None:
            d, self.greetDeferred = self.greetDeferred, None
            self.context = ClientTLSContext()
            d.callback(self)

class SimplePOP3ClientFactory(protocol.ClientFactory):
    usedUp = False

    protocol = SimplePOP3Client

    def __init__(self, username, onConn):
        self.ctx = ssl.ClientContextFactory()
        
        self.username = username
        self.onConn = onConn

    def buildProtocol(self, addr):
        assert not self.usedUp
        self.usedUp = True
        
        p = self.protocol(self.ctx)
        p.factory = self
        p.greetDeferred = self.onConn

        return p
    
    def clientConnectionFailed(self, connector, reason):
        d, self.onConn = self.onConn, None
        d.errback(reason)

# Initial callback - invoked after the server sends us its greet message
def cbServerGreeting(proto, username, password):
    # Hook up stdio
    tp = TrivialPrompter()
    stdio.StandardIO(tp)
    
    # And make it easily accessible
    proto.prompt = tp.prompt
    proto.display = tp.display

    # Try to authenticate securely
    return proto.login(username, password
        ).addCallback(cbLoggedIn, proto
        ).addErrback(ebError, proto)

# Fallback error-handler.  If anything goes wrong, log it and quit.
def ebConnection(reason):
    log.startLogging(sys.stdout)
    log.err(reason)
    reactor.stop()

def cleanup(result, proto):
    proto.transport.loseConnection()
    reactor.stop()


# Callback after authentication has succeeded
def cbLoggedIn(result, proto):
    # List a bunch of mailboxes
    return proto.quit().addBoth(cleanup, proto)

def ebError(err, proto):
    print "error %s", err
    proto.transport.loseConnection()


def main():
    hostname = "localhost" #raw_input('POP3 Server Hostname: ')
    port = 1100 #raw_input('POP3 port: ')
    username = "test" #raw_input('POP3 Username: ')
    password = "test" #util.getPassword('POP3 Password: ')

    onConn = defer.Deferred(
        ).addCallback(cbServerGreeting, username, password
        ).addErrback(ebConnection
        )

    factory = SimplePOP3ClientFactory(username, onConn)
    
    conn = reactor.connectTCP(hostname, int(port), factory)
    #conn = reactor.connectSSL(hostname, int(port), factory, ClientTLSContext())
    reactor.run()

if __name__ == '__main__':
    main()
