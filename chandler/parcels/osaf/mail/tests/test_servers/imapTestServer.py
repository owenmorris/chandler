#!/usr/bin/python
from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet import reactor
import sys
import os

"""
TODO:
1. Add in actual SSL Handshake support
2. Add in real PLAIN Login support
"""

PORT = 1430

LOGIN_PLAIN = "testuser testuser"

"""Support Flags"""
SSL_SUPPORT = True

"""DEBUG_FLAGS"""
INVALID_SERVER_RESPONSE = False
DENY_CONNECTION = False
DROP_CONNECTION = False
BAD_TRANSFER_RESPONSE = False
BAD_TLS_RESPONSE = False
TIMEOUT_RESPONSE = False
SLOW_GREETING = False
NO_MAILBOX = False

"""Commands"""
CONNECTION_MADE = "* OK Twisted Test Server Ready"
CAP  = "CAPABILITY IMAP4REV1 LOGIN-REFERRALS"
CAP_AUTH  = "CAPABILITY IMAP4REV1 LOGIN-REFERRALS AUTH=PLAIN"
CAP_SSL   = "CAPABILITY IMAP4REV1 LOGIN-REFERRALS STARTTLS AUTH=PLAIN"
AUTH_ACCEPTED = "user testuser authenticated"
NOOP_OK = "OK NOOP completed"
AUTH_DECLINED = "NO LOGIN failed"
UNKNOWN_COMMAND = " Bad Command unrecognized"
TLS_ERROR = "server side error start TLS handshake"
NO_MAILBOX_ERROR = "NO SELECT failed"
LOGOUT_COMPLETE = "OK LOGOUT completed"

INBOX_SELECTED = [
"* 0 EXISTS",
"* 0 RECENT",
"* OK [UIDVALIDITY 1092939128] UID validity status",
"* OK [UIDNEXT 2] Predicted next UID",
"* FLAGS (Junk \Answered \Flagged \Deleted \Draft \Seen)",
"* OK [PERMANENTFLAGS (Junk \* \Answered \Flagged \Deleted \Draft \Seen)] Permanent flags",

INBOX_SELECT_COMPLETE = "OK [READ-WRITE] SELECT completed"

class IMAPTestServer(basic.LineReceiver):
    def __init__(self):
        pass

    def getCode(self, str):
        return str.split(" ")[0]

    def sendSelectResp(self, req):
        #XXX: need to refine this
        self.sendLine("\r\n".join(INBOX_SELECTED))
        self.sendResponse(INBOX_SELECT_COMPLETE, req)

    def sendCapabilities(self, req):
        caps = CAP

        if AUTH_SUPPORT:
            caps = CAP_AUTH

        if SSL_SUPPORT:
            cap = CAP_SSL

        self.sendResponse(caps, req)

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
        self.sendLine(CONNECTION_MADE)

    def lineReceived(self, line):
        """Error Conditions"""
        if TIMEOUT_RESPONSE:
            """Do not respond to clients request"""
            return

        if DROP_CONNECTION:
            self.transport.loseConnection()
            return

        if INVALID_SERVER_RESPONSE:
            self.sendResponse("%s The IMAP Server is sending you a invalid RFC response", line)
            return

        if "CAPABILITY" in line.upper():

        elif "NOOP" in line.upper():
            self.sendResponse(NOOP_OK, line)

        elif "LOGIN" in line.upper():`
            resp = None
            if LOGIN_PLAIN in line.upper():
                resp = AUTH_ACCEPTED
            else:
                resp = AUTH_DECLINED 

            self.sendResponse(resp, line)

        elif "SELECT" in line.upper():
            if NO_MAILBOX or "INBOX" not in line.upper():
                self.sendResponse(NO_MAILBOX_ERROR, line)
            else:
                self.sendSelectResp(line);

        elif "LOGOUT" in line.upper():
            self.sendResponse(LOGOUT_COMPLETE, line) 
            self.disconnect()

        elif "STARTTLS" in line.upper() and SSL_SUPPORT:
            self.sendLine(TLS_ERROR)

        else:
            self.sendResponse(UNKNOWN_COMMAND, line)

    def disconnect(self):
        self.transport.loseConnection()


def config(ehlo, ssl, auth):
    global EHLO_SUPPORT, SSL_SUPPORT, AUTH_SUPPORT
    EHLO_SUPPORT = ehlo
    SSL_SUPPORT = ssl
    AUTH_SUPPORT = auth

def no_ssl_support():
    config(True, False, True)

def no_auth_support():
    config(True, True, False)

def basic_smtp_server():
    config(False, False, False)


usage = """ smtpServer.py [arg] (default is ESMTP | AUTH | SSL support)
no_ssl - Start with no SSL support
no_auth - Start with no AUTH support
smtp - Start with no EHLO, SSL, or AUTH support
bad_resp - Send a non-RFC compliant response to the Client
deny - Deny the connection 
drop - Drop the connection after sending the greeting
bad_tran - Send a bad response to a Mail From request
bad_tls - Send a bad response to a STARTTLS
timeout - Do not return a response to a Client request
slow - Wait 20 seconds after the connection is made to return a Server Greeting
"""

def printMessage(msg):
    print "Server Starting in %s mode" % msg

def processArgs():

    if len(sys.argv) < 2:
        printMessage("ESMTP | SSL | AUTH")
        return

    arg = sys.argv[1]

    if arg.lower() == 'no_ssl':
        no_ssl_support()
        printMessage("NON-SSL")

    elif arg.lower() == 'no_auth':
        no_auth_support()
        printMessage("NON-AUTH")

    elif arg.lower() == 'smtp':
        basic_smtp_server()
        printMessage("SMTP Only")

    elif arg.lower() == 'bad_resp':
        global INVALID_SERVER_RESPONSE
        INVALID_SERVER_RESPONSE = True
        printMessage("Invalid Server Response")

    elif arg.lower() == 'deny':
        global DENY_CONNECTION 
        DENY_CONNECTION = True
        printMessage("Deny Connection")

    elif arg.lower() == 'drop':
        global DROP_CONNECTION 
        DROP_CONNECTION = True
        printMessage("Drop Connection")

    elif arg.lower() == 'bad_tran':
        global BAD_TRANSFER_RESPONSE 
        BAD_TRANSFER_RESPONSE = True
        printMessage("Bad Transfer Response")

    elif arg.lower() == 'bad_tls':
        global BAD_TLS_RESPONSE 
        BAD_TLS_RESPONSE = True
        printMessage("Bad TLS Response")

    elif arg.lower() == 'timeout':
        global TIMEOUT_RESPONSE
        TIMEOUT_RESPONSE = True
        printMessage("Timeout Response")

    elif arg.lower() == 'slow':
        global SLOW_GREETING
        SLOW_GREETING = True
        printMessage("Slow Greeting")

    elif arg.lower() == '--help':
        print usage

    elif arg.lower() == '--help':
        print usage
        sys.exit()

    else:
        print usage
        sys.exit()

def main():
    processArgs()

    f = Factory()
    f.protocol = SMTPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
