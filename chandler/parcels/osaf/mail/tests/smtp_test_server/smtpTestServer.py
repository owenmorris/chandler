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
"""

PORT = 2500
ACCEPT_LIST = ["brian@test.com", "osafuser@code-bear.com", "brian@localhost"]

"""Support Flags"""
ESMTP_SUPPORT = True
SSL_SUPPORT = True
AUTH_SUPPORT = True

"""TOKENS"""
TERMINATOR = "."

"""Commands"""
CONNECTION_MADE = "220 localhost ESMTP TWISTED_SMTP_TEST_SERVER"
DISCONNECT_STRING = "221 Bye"
OK_STRING = "250 OK"
DATA_STRING = "354 End data with <CR><LF>.<CR><LF>"


CAPABILITIES = [
"250-localhost",
"250-PIPELINING",
"250-SIZE",
"250-VRFY",
"250-ETRN",
"250-XVERP",
"250 8BITMIME"
]

CAPABILITIES_SSL = "250-STARTTLS"
CAPABILITIES_AUTH = "250-AUTH LOGIN PLAIN"

"""MAY want to be a line reciever"""

class SMTPTestServer(basic.LineReceiver):

    def __init__(self):
        self.in_data = False

    def sendCapabilities(self, helo=False):
        for cap in CAPABILITIES:
            self.sendLine(cap)

        if AUTH_SUPPORT and not helo:
            self.sendLine(CAPABILITIES_AUTH)

        if SSL_SUPPORT and not helo:
            self.sendLine(CAPABILITIES_SSL)


    def connectionMade(self):
        self.sendLine(CONNECTION_MADE)

    def lineReceived(self, line):
        print "I got ", line

        if self.in_data:
            print "IN DATA"
            if TERMINATOR == line:
                self.in_data = False
                self.sendLine(OK_STRING)
            return

        """COMMAND HANDLING"""

        if "EHLO" in line.upper():
            if ESMTP_SUPPORT:
                self.sendCapabilities()
            else:
                """XXX: Put in bad command"""
                print "NO ELHO SUPPORT"

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
                """XXX PUT IN BAD CODE HERE"""
                print "NO ALLOWED USERS"

        elif "DATA" in line.upper():
            self.sendLine(DATA_STRING)
            self.in_data = True

        elif "QUIT" in line.upper():
            self.sendLine(DISCONNECT_STRING)
            self.disconnect()

        else:
            print "UNKNOWN COMMAND RECEIVED: ", line

    def disconnect(self):
        self.transport.loseConnection()


def main():
    f = Factory()
    f.protocol = SMTPTestServer
    reactor.listenTCP(PORT, f)
    reactor.run()

if __name__ == '__main__':
    main()
