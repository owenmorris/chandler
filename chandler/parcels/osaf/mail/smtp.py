__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.persistence.RepositoryView as RepositoryView
import application.Globals as Globals
import twisted.mail.smtp as smtp
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import email.Message as Message
import logging as logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class SMTPSender(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self):
        super(SMTPSender, self).__init__(Globals.repository, None)

    def sendmail(self):
        username = None 
        password = None 
        smtphost = "localhost"
        from_addr = "brian"
        to_addrs = ["brian"]

        msg = Message.Message()

        if len(to_addrs) > 1:
            msg['To'] = ', '.join(to_addrs)
        else:
            msg['To'] = to_addrs[0]

        msg['From'] = from_addr
        msg['Subject'] = "ESMTPTest"
        msg.set_payload("This is body text")

        msg = StringIO(msg.as_string())

        d = defer.Deferred().addCallbacks(self.mailSuccess, self.mailFailure)

        factory = smtp.ESMTPSenderFactory(username, password, from_addr, to_addrs, msg, d, 
                                          0, requireAuthentication=False, requireTransportSecurity=False)

        reactor.callFromThread(reactor.connectTCP, smtphost, 25, factory)

    def mailSuccess(self, result):
        addrs = []

        for address in result[1]:
            addrs.append(address[0])

        str = "SMTP Message sent to %d recipients[%s]" % (result[0], ", ".join(addrs))
        self.log.info(str)

    #TODO: Figure out what exc is for all cases
    def mailFailure(self, exc):
        self.log.error("SMTP send failed: %s" % exc)
