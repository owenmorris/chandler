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

PORT = 1430
LOGIN_PLAIN = "testuser testuser"

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
NO_MAILBOX = False
SEND_CAPABILITY_IN_GREETING = False

"""Commands"""
CONNECTION_MADE = "OK Twisted Test Server Ready"
CAP  = "CAPABILITY IMAP4REV1 IDLE NAMESPACE MAILBOX-REFERRALS BINARY UNSELECT SCAN SORT THREAD=REFERENCES THREAD=ORDEREDSUBJECT MULTIAPPEND LOGIN-REFERRALS"
CAP_SSL   = CAP + " STARTTLS"


INVALID_RESPONSE = "The IMAP Server is sending you an invalid RFC response"
AUTH_ACCEPTED = "OK user testuser authenticated"
NOOP_OK = "OK NOOP completed"
AUTH_DECLINED = "NO LOGIN failed"
UNKNOWN_COMMAND = "Bad Command unrecognized"
TLS_ERROR = "server side error start TLS handshake"
NO_MAILBOX_ERROR = "NO SELECT failed"
LOGOUT_COMPLETE = "OK LOGOUT completed"
CAPABILITY_COMPLETE = "OK CAPABILITY completed"
BAD_REQUEST = "BAD Missing command"
NOT_LOGGED_IN = "BAD Command unrecognized/login please: INBOX"

INBOX_SELECTED = [
"* 0 EXISTS",
"* 0 RECENT",
"* OK [UIDVALIDITY 1092939128] UID validity status",
"* OK [UIDNEXT 2] Predicted next UID",
"* FLAGS (Junk \Answered \Flagged \Deleted \Draft \Seen)",
"* OK [PERMANENTFLAGS (Junk \* \Answered \Flagged \Deleted \Draft \Seen)] Permanent flags"
]

INBOX_SELECT_COMPLETE = "OK [READ-WRITE] SELECT completed"

class IMAPTestServer(basic.LineReceiver):
    def __init__(self):
        self.loggedIn = False

    def getCode(self, str):
        return str.split(" ")[0]

    def isValidRequest(self, str):
        try:
            int(self.getCode(str))
            return True
        except ValueError:
            return False

    def sendSelectResp(self, req):
        #XXX: need to refine this
        self.sendLine("\r\n".join(INBOX_SELECTED))
        self.sendResponse(INBOX_SELECT_COMPLETE, req)

    def sendCapabilities(self, req):
        caps = SSL_SUPPORT and CAP_SSL or CAP

        self.sendLine("* %s" % caps)
        self.sendResponse(CAPABILITY_COMPLETE, req)

    def sendResponse(self, resp, req):
        self.sendLine("%s %s" % (self.getCode(req), resp))

    def connectionMade(self):
        if DENY_CONNECTION:
            self.transport.loseConnection()
            return

        if SLOW_GREETING:
            reactor.callLater(20, self.sendGreeting)

        else:
            self.sendGreeting()

    def sendGreeting(self):
        line = CONNECTION_MADE

        if SEND_CAPABILITY_IN_GREETING:
            caps = SSL_SUPPORT and CAP_SSL or CAP
            line += " [%s]" % caps

        self.sendLine("* %s" % line)

    def lineReceived(self, line):
        """Error Conditions"""
        if TIMEOUT_RESPONSE:
            """Do not respond to clients request"""
            return

        if DROP_CONNECTION:
            self.transport.loseConnection()
            return

        if not self.isValidRequest(line):
            self.sendLine("%s %s" % (line, UNKNOWN_COMMAND))

        elif "CAPABILITY" in line.upper():
            if INVALID_CAPABILITY_RESPONSE:
                self.sendResponse(INVALID_RESPONSE, line)
            else:
                self.sendCapabilities(line)

        elif "STARTTLS" in line.upper() and SSL_SUPPORT:
            self.sendResponse(TLS_ERROR, line)

        elif "LOGIN" in line.upper():
            if INVALID_LOGIN_RESPONSE:
                self.sendResponse(INVALID_RESPONSE, line)

            else:
                resp = None

                if LOGIN_PLAIN in line:
                    resp = AUTH_ACCEPTED
                    self.loggedIn = True
                else:
                    resp = AUTH_DECLINED
                    self.loggedIn = False

                self.sendResponse(resp, line)

        elif "LOGOUT" in line.upper():
            self.loggedIn = False
            self.sendResponse(LOGOUT_COMPLETE, line)
            self.disconnect()

        elif INVALID_SERVER_RESPONSE:
            self.sendLine(INVALID_RESPONSE)

        elif not self.loggedIn:
            self.sendResponse(NOT_LOGGED_IN, line)

        elif "NOOP" in line.upper():
            self.sendResponse(NOOP_OK, line)

        elif "SELECT" in line.upper():
            if TIMEOUT_DEFERRED:
                return 

            if NO_MAILBOX or "INBOX" not in line.upper():
                self.sendResponse(NO_MAILBOX_ERROR, line)
            else:
                self.sendSelectResp(line)

        else:
            self.sendResponse(UNKNOWN_COMMAND, line)

    def disconnect(self):
        self.transport.loseConnection()


usage = """imapServer.py [arg] (default is Standard IMAP Server with no messages in Inbox)
cap_greeting - send the IMAP Server 'CAPABILITY' list in the Server Greeting response
no_ssl - Start with no SSL support
no_mailbox - Start with no Inbox
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

def processArg(arg):

    if arg.lower() == 'cap_greeting':
        global SEND_CAPABILITY_IN_GREETING
        SEND_CAPABILITY_IN_GREETING = True
        printMessage("Send Capability in Greeting")

    elif arg.lower() == 'no_ssl':
        global SSL_SUPPORT
        SSL_SUPPORT = False
        printMessage("NON-SSL")

    elif arg.lower() == 'no_mailbox':
        global NO_MAILBOX
        NO_MAILBOX = True 
        printMessage("NON-MAILBOX")

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
    if len(sys.argv) < 2:
        printMessage("Inbox with no messages")

    else:
        args = sys.argv[1:]

        for arg in args:
            processArg(arg)

    f = Factory()
    f.protocol = IMAPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
