#!/usr/local/bin/python
from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet import reactor
import sys
import os
import time

"""
TODO:
1. Add in actual SSL Handshake support
2. Add in real PLAIN Login support
"""

PORT = 2500
FROM_ACCEPT_LIST = ["brian@test.com", "osafuser@code-bear.com"]
TO_ACCEPT_LIST = ["brian@test.com", "osafuser@code-bear.com"]

DIR = "testbox"

"""Base 64 encoding of username: testuser password: testuser
[0] = username\0password form
[1] = username\0username\0password
"""
LOGIN_PLAIN_BASE_64 = ["DGVZDHVZZXIADGVZDHVZZXI=", "dGVzdHVzZXIAdGVzdHVzZXIAdGVzdHVzZXI="]

"""Support Flags"""
EHLO_SUPPORT = True
SSL_SUPPORT = True
AUTH_SUPPORT = True

"""DEBUG_FLAGS"""
INVALID_SERVER_RESPONSE = False
DENY_CONNECTION = False
DROP_CONNECTION = False
BAD_TRANSFER_RESPONSE = False
BAD_TLS_RESPONSE = False
TIMEOUT_RESPONSE = False
SLOW_GREETING = False

"""TOKENS"""
TERMINATOR = "."

"""Commands"""
CONNECTION_MADE = "220 localhost ESMTP TWISTED_SMTP_TEST_SERVER"
DISCONNECT_STRING = "221 Bye"
OK_STRING = "250 OK"
DATA_STRING = "354 End data with <CR><LF>.<CR><LF>"
AUTH_SUCCESS = "235 Authenication Successful"

"""ERRORS"""
NO_RELAY = "550 relaying prohibited by administrator"
NO_USER =  "550 recipient address denied"
UNKNOWN_COMMAND = "502 command not implemented"
MALFORMED_AUTH = "501 Authenication Failed: mailformed initial response"
UNSUPPORTED_AUTH = "504 Unsupported authenication mechanism"
AUTH_DECLINED = "535 authentication failed"
TLS_ERROR = "451 server side error start TLS handshake"



CAPABILITIES = [
"250-localhost",
"250-SIZE",
"250-VRFY",
"250-ETRN",
"250-XVERP",
"250 8BITMIME"
]

CAPABILITIES_SSL = "250-STARTTLS"
CAPABILITIES_AUTH = "250-AUTH PLAIN"


class SMTPTestServer(basic.LineReceiver):

    def __init__(self):
        self.in_data = False
        self.data = []
        self.caps = None

    def sendCapabilities(self, helo=False):
        if self.caps is None:
            self.caps = []

            if AUTH_SUPPORT and not helo:
                self.caps.append(CAPABILITIES_AUTH)

            if SSL_SUPPORT and not helo:
                self.caps.append(CAPABILITIES_SSL)

            for cap in CAPABILITIES:
                self.caps.append(cap)

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

        if INVALID_SERVER_RESPONSE:
            self.sendLine("The SMTP Server is sending you an invalid RFC response")
            return

        if self.in_data:
            if TERMINATOR == line:
                self.in_data = False
                self.sendLine(OK_STRING)
                #self.writeMessage("\r\n".join(self.data))
                self.data = []

            else:
                self.data.append(line)

            return

        """SMTP Commands"""
        if "EHLO" in line.upper():
            if EHLO_SUPPORT:
                self.sendCapabilities()
            else:
                self.sendLine(UNKNOWN_COMMAND)

        elif "RSET" in line.upper():
            self.sendLine(OK_STRING)

        elif "HELO" in line.upper():
            self.sendCapabilities(True)

        elif "MAIL FROM:" in line.upper():
            if BAD_TRANSFER_RESPONSE:
                self.sendLine("-1 This is a bad response to a MAIL FROM:")
                return

            found = False

            for accept in FROM_ACCEPT_LIST:
                if accept.upper() in line.upper():
                    found = True
                    continue

            if found:
                self.sendLine(OK_STRING)

            else:
                self.sendLine(NO_USER)


        elif "RCPT TO:" in line.upper():
            found = False

            for accept in TO_ACCEPT_LIST:
                if accept.upper() in line.upper():
                    found = True
                    continue

            if found:
                self.sendLine(OK_STRING)

            else:
                self.sendLine(NO_RELAY)

        elif "DATA" in line.upper():
            self.sendLine(DATA_STRING)
            self.in_data = True

        elif "QUIT" in line.upper():
            self.sendLine(DISCONNECT_STRING)
            self.disconnect()

        elif "STARTTLS" in line.upper() and SSL_SUPPORT:
            self.sendLine(TLS_ERROR)

        elif "AUTH" in line.upper() and AUTH_SUPPORT:
            if "PLAIN" in line.upper():

                if line[-1] != '=':
                    """It is not a base64 encoded string"""
                    self.sendLine(MALFORMED_AUTH)
                    return

                for key in LOGIN_PLAIN_BASE_64:
                    if key in line:
                        self.sendLine(AUTH_SUCCESS)
                        return

                self.sendLine(AUTH_DECLINED)
            else:
                 self.sendLine(UNSUPPORTED_AUTH)

        else:
            self.sendLine(UNKNOWN_COMMAND)

    def disconnect(self):
        self.transport.loseConnection()

    def writeMessage(self, message):
        global DIR

        fileName = "./%s/%s.message" % (DIR, time.time())

        out = open(fileName, "w")
        out.write(message)
        out.close()



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

def processArg(arg):

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
        sys.exit()

    else:
        print usage
        sys.exit()

def dirCheck():
    found = False

    for root, dirs, files in  os.walk("."):
        if DIR in dirs:
            found = True

    if not found: 
        d = os.mkdir(DIR)

def main():
    if len(sys.argv) < 2:
        printMessage("ESMTP | SSL | AUTH")
    else:
        args = sys.argv[1:]
        for arg in args:
            processArg(arg)

    dirCheck()

    f = Factory()
    f.protocol = SMTPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
