#!/usr/bin/python
from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet import reactor

"""
TESTS:
1. Connection error
2. Invalid return in lineRecieved
3. Transfer and protocol error
4. Timeout
5. Bad TLS Start
6. Bad Auth Challenge
7. No Auth
8. No TLS
9. No EHLO
10. Transfer Error
11. Invalid login
12. Bad auth string from client
"""

PORT = 2500
ACCEPT_LIST = ["brian@test.com", "osafuser@code-bear.com", "brian@localhost"]

"""Base 64 encoding of username: testuser passworf: testuser 
[0] = username\0password form
[1] = username\0username\0password
"""
LOGIN_PLAIN_BASE_64 = ["DGVZDHVZZXIADGVZDHVZZXI=", "dGVzdHVzZXIAdGVzdHVzZXIAdGVzdHVzZXI="]

"""Support Flags"""
EHLO_SUPPORT = True
SSL_SUPPORT = True
AUTH_SUPPORT = True

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

def config(ehlo, ssl, auth):
    global EHLO_SUPPORT, SSL_SUPPORT, AUTH_SUPPORT
    EHLO_SUPPORT = ehlo
    SSL_SUPPORT = ssl
    AUTH_SUPPORT = auth


class SMTPTestServer(basic.LineReceiver):

    def __init__(self):
        self.in_data = False
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
        self.sendLine(CONNECTION_MADE)

    def lineReceived(self, line):
        if self.in_data:
            if TERMINATOR == line:
                self.in_data = False
                self.sendLine(OK_STRING)
            return

        if "EHLO" in line.upper():
            if EHLO_SUPPORT:
                self.sendCapabilities()
            else:
                self.sendLine(UNKNOWN_COMMAND)

        elif "HELO" in line.upper():
            self.sendCapabilities(True)

        elif "MAIL FROM:" in line.upper() or "RCPT TO:" in line.upper():
            found = False

            for accept in ACCEPT_LIST:
                if accept.upper() in line.upper():
                    found = True
                    continue

            if found:
                self.sendLine(OK_STRING)

            else:
                if "MAIL FROM:" in line.upper():
                    self.sendLine(NO_USER)

                else:
                    self.sendLine(NO_RELAY)

        elif "DATA" in line.upper():
            self.sendLine(DATA_STRING)
            self.in_data = True

        elif "QUIT" in line.upper():
            self.sendLine(DISCONNECT_STRING)
            self.disconnect()

        elif "STARTTLS" in line.upper() and SSL_SUPPORT:
            #XXX: Send a bad TLS handshake
            pass

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


def main():
    f = Factory()
    f.protocol = SMTPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
