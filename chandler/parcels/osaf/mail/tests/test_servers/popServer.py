#!/usr/local/bin/python
from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet import reactor
import sys
import os

"""
Notes:
1. Add bad Auth sharing
2. TLS
"""

USER = "brian"
PASS = "1234Osaf"

PORT = 1100

SSL_SUPPORT = True
INVALID_SERVER_RESPONSE = False
INVALID_CAPABILITY_RESPONSE = False
INVALID_LOGIN_RESPONSE = False
DENY_CONNECTION = False
DROP_CONNECTION = False
BAD_TLS_RESPONSE = False
TIMEOUT_RESPONSE = False
TIMEOUT_DEFERRED = False
SLOW_GREETING = False

"""Commands"""
CONNECTION_MADE = "+OK POP3 localhost v2003.83 server ready" 

CAPABILITIES = [
"TOP",
"LOGIN-DELAY 180",
"USER",
"SASL LOGIN"
]

CAPABILITIES_SSL = "STLS"

 
INVALID_RESPONSE = "-ERR Unknown request"
VALID_RESPONSE = "+OK Command Completed"
AUTH_DECLINED = "-ERR LOGIN failed"
AUTH_ACCEPTED = "+OK Mailbox open, 0 messages"
TLS_ERROR = "-ERR server side error start TLS handshake"
LOGOUT_COMPLETE = "+OK quit completed"
NOT_LOGGED_IN = "-ERR Unknown AUHORIZATION state command"
STAT = "+OK 0 0"
UIDL = "+OK Unique-ID listing follows\r\n."
LIST = "+OK Mailbox scan listing follows\r\n."
CAP_START = "+OK Capability list follows:"


class POPTestServer(basic.LineReceiver):
    def __init__(self):
        self.loggedIn = False
        self.caps = None
        self.tmpUser = None

    def sendSTATResp(self, req):
        self.sendLine(STAT)

    def sendUIDLResp(self, req):
        self.sendLine(UIDL)

    def sendLISTResp(self, req):
        self.sendLine(LIST)

    def sendCapabilities(self):
        if self.caps is None:
            self.caps = [CAP_START]

        if SSL_SUPPORT:
            self.caps.append(CAPABILITIES_SSL)

        for cap in CAPABILITIES:
            self.caps.append(cap)

        self.caps.append(".")

        self.sendLine('\r\n'.join(self.caps))


    def connectionMade(self):
        if DENY_CONNECTION:
            self.transport.loseConnection()
            return

        if SLOW_GREETING:
            reactor.callLater(20, self.sendGreeting)

        else:
            self.sendGreeting()

    def sendGreeting(self):
        self.sendLine(CONNECTION_MADE)

    def lineReceived(self, line):
        """Error Conditions"""
        if TIMEOUT_RESPONSE:
            """Do not respond to clients request"""
            return

        if DROP_CONNECTION:
            self.transport.loseConnection()
            return

        elif "CAPA" in line.upper():
            if INVALID_CAPABILITY_RESPONSE:
                self.sendLine(INVALID_RESPONSE)
            else:
                self.sendCapabilities()

        elif "STLS" in line.upper() and SSL_SUPPORT:
            self.sendLine(TLS_ERROR)

        elif "USER" in line.upper():
            if INVALID_LOGIN_RESPONSE:
                self.sendLine(INVALID_RESPONSE)
                return

            resp = None
            try:
                self.tmpUser = line.split(" ")[1]
                resp = VALID_RESPONSE
            except:
                resp = AUTH_DECLINED

            self.sendLine(resp)

        elif "PASS" in line.upper():
            resp = None
            try:
                pwd = line.split(" ")[1]

                if self.tmpUser is None or pwd is None:
                    resp = AUTH_DECLINED
                elif self.tmpUser == USER and pwd == PASS:
                    resp = AUTH_ACCEPTED
                    self.loggedIn = True
                else:
                    resp = AUTH_DECLINED
            except:
                resp = AUTH_DECLINED

            self.sendLine(resp)

        elif "QUIT" in line.upper():
            self.loggedIn = False
            self.sendLine(LOGOUT_COMPLETE)
            self.disconnect()

        elif INVALID_SERVER_RESPONSE:
            self.sendLine(INVALID_RESPONSE)

        elif not self.loggedIn:
            self.sendLine(NOT_LOGGED_IN)

        elif "NOOP" in line.upper():
            self.sendLine(VALID_RESPONSE)

        elif "STAT" in line.upper():
            if TIMEOUT_DEFERRED:
                return
            self.sendLine(STAT)

        elif "LIST" in line.upper():
            if TIMEOUT_DEFERRED:
                return
            self.sendLine(LIST)

        elif "UIDL" in line.upper():
            if TIMEOUT_DEFERRED:
                return
            self.sendLine(UIDL)


    def disconnect(self):
        self.transport.loseConnection()


usage = """popServer.py [arg] (default is Standard POP Server with no messages)
no_ssl - Start with no SSL support
bad_resp - Send a non-RFC compliant response to the Client
bad_cap_resp - send a non-RFC compliant response when the Client sends a 'CAPABILITY' request
bad_login_resp - send a non-RFC compliant response when the Client sends a 'LOGIN' request
deny - Deny the connection
drop - Drop the connection after sending the greeting
bad_tls - Send a bad response to a STARTTLS
timeout - Do not return a response to a Client request
to_deferred - Do not return a response on a 'Select' request. This
              will test Deferred callback handling
slow - Wait 20 seconds after the connection is made to return a Server Greeting
"""

def printMessage(msg):
    print "Server Starting in %s mode" % msg

def processArgs():

    if len(sys.argv) < 2:
        printMessage("POP3 with no messages")
        return

    arg = sys.argv[1]

    if arg.lower() == 'no_ssl':
        global SSL_SUPPORT
        SSL_SUPPORT = False
        printMessage("NON-SSL")

    elif arg.lower() == 'bad_resp':
        global INVALID_SERVER_RESPONSE
        INVALID_SERVER_RESPONSE = True
        printMessage("Invalid Server Response")

    elif arg.lower() == 'bad_cap_resp':
        global INVALID_CAPABILITY_RESPONSE
        INVALID_CAPABILITY_RESPONSE = True
        printMessage("Invalid Capability Response")

    elif arg.lower() == 'bad_login_resp':
        global INVALID_LOGIN_RESPONSE
        INVALID_LOGIN_RESPONSE = True
        printMessage("Invalid Capability Response")

    elif arg.lower() == 'deny':
        global DENY_CONNECTION 
        DENY_CONNECTION = True
        printMessage("Deny Connection")

    elif arg.lower() == 'drop':
        global DROP_CONNECTION 
        DROP_CONNECTION = True
        printMessage("Drop Connection")


    elif arg.lower() == 'bad_tls':
        global BAD_TLS_RESPONSE 
        BAD_TLS_RESPONSE = True
        printMessage("Bad TLS Response")

    elif arg.lower() == 'timeout':
        global TIMEOUT_RESPONSE
        TIMEOUT_RESPONSE = True
        printMessage("Timeout Response")

    elif arg.lower() == 'to_deferred':
        global TIMEOUT_DEFERRED
        TIMEOUT_DEFERRED = True
        printMessage("Timeout Deferred Response")

    elif arg.lower() == 'slow':
        global SLOW_GREETING
        SLOW_GREETING = True
        printMessage("Slow Greeting")

    elif arg.lower() == '--help':
        print usage
        sys.exit()

    else:
        print usage
        sys.exit()

def main():
    processArgs()

    f = Factory()
    f.protocol = POPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
