#!/usr/local/bin/python
from twisted.internet import reactor
from twisted.mail.smtp import sendmail
from twisted.internet import defer
import sys

class TransportInfo:
    hostname  = "localhost"
    rcpt_to   = ["brian@test.com"]
    mail_from = "brian@test.com"

def sendMail(file):
    fp = open(file)
    data = fp.read()
    fp.close()

    return sendmail(TransportInfo.hostname,
                    TransportInfo.mail_from,
                    TransportInfo.rcpt_to,
                    data
                    ).addCallback(_messageSent, file).addErrback(_sendError, file)

def _messageSent(result, file):
    print "\n==================== MESSAGE SENT: '%s' ================\n" % file
    reactor.stop()

def _sendError(reason, file):
    print "\n===================SMTP ERROR: '%s' ==================\n" % file
    reactor.stop()

reactor.callLater(0, sendMail, sys.argv[1])
reactor.run()


