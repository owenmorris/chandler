__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.persistence.RepositoryView as RepositoryView
import application.Globals as Globals
import twisted.mail.smtp as smtp
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.internet.ssl as ssl
import email.Message as Message
import logging as logging
import common as common
import message as message
import osaf.contentmodel.mail.Mail as Mail
import repository.util.UUID as UUID
import mx.DateTime as DateTime

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class ChandlerESMTPSender(smtp.ESMTPSender):

    def tryTLS(self, code, resp, items):
        if not self.factory.useSSL:
            items = common.disableTwistedTLS(items)

        smtp.ESMTPSender.tryTLS(self, code, resp, items)

class ChandlerESMTPSenderFactory(smtp.ESMTPSenderFactory):

    protocol = ChandlerESMTPSender

    def __init__(self, username, password, fromEmail, toEmail, file, deferred, retries=5, contextFactory=None,
                 heloFallback=False, requireAuthentication=True, requireTransportSecurity=True, useSSL=False):

        self.useSSL = useSSL

        smtp.ESMTPSenderFactory.__init__(self, username, password, fromEmail, toEmail, file, deferred, retries,
                                         contextFactory, heloFallback, requireAuthentication, requireTransportSecurity)


class SMTPException(common.MailException):
    pass

class SMTPSender(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self, account, mailMessage):
        #XXX: Perhaps get the first account if None
        if account is None or not account.isItemOf(Mail.MailParcel.getSMTPAccountKind()):
            raise SMTPMailException("You must pass in a SMTPAccount instance")

        if mailMessage is None or not isinstance(mailMessage, Mail.MailMessage):
            raise SMTPMailException("You must pass in a mailParcel instance")

        id = "STMPSender Mail ", DateTime.now().ticks()
        viewName = "%s_%s_%s" % (id, account.displayName, str(UUID.UUID()))

        super(SMTPSender, self).__init__(Globals.repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.mailMessage = None 
        self.mailMessageUUID = mailMessage.itsUUID
        self.sent = False

    #in thread
    def sendMail(self):
        if __debug__:
            self.printCurrentView("sendMail")

        reactor.callFromThread(self.__sendMail)

    #IN Twisted
    def __sendMail(self):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__sendMail")

            self.__getKinds()

            """ Refresh our view before adding items to our mail Message
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.commit()

            username     = self.account.username
            password     = self.account.password
            host         = self.account.host
            port         = self.account.port
            useSSL       = self.account.useSSL
            useAuth      = self.account.useAuth
            authRequired = True
            sslContext   = None

            if not useAuth:
                authRequired = False
                username     = None
                password     = None

            if useSSL:
                sslContext = ssl.ClientContextFactory(useM2=1)

            self.mailMessage.outgoingMessage(account=self.account)

            messageObject = message.kindToMessageObject(self.mailMessage)
            messageText = messageObject.as_string()
            self.mailMessage.rfc2882Message = message.strToText(self.mailMessage, "rfc2822Message", messageText)
            d = defer.Deferred().addCallbacks(self.__mailSuccess, self.__mailFailure)
            msg = StringIO(messageText)

            to_addrs = []

            for address in self.mailMessage.toAddress:
                to_addrs.append(address.emailAddress)

            if self.mailMessage.replyToAddress is not None:
                from_addr = self.mailMessage.replyToAddress.emailAddress

            else:
                from_addr = self.mailMessage.fromAddress.emailAddress

        finally:
           self.restorePreviousView()

        factory = ChandlerESMTPSenderFactory(username, password, from_addr, to_addrs, msg, d,
                                             0, sslContext, False, authRequired, useSSL, useSSL)
        #XXX: Is this correct
        #if useSSL:
        #    reactor.connectSSL(host, port, factory, sslContext)
        reactor.connectTCP(host, port, factory)


    def __mailSuccess(self, result):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailSuccess")

            addrs = []

            for address in result[1]:
                addrs.append(address[0])

            str = "recipients"

            if len(addrs) == 1:
                str = "recipient"

            info = "SMTP Message sent to %d %s [%s]" % (result[0], str, ", ".join(addrs))
            self.log.info(info)

            self.mailMessage.dateSent = DateTime.now()
            self.mailMessage.dateSentString = message.dateTimeToRFC2882Date(DateTime.now())

            self.mailMessage.deliveryExtension.sendSucceeded()
            self.sent = True 

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)

    def __mailFailure(self, exc):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailFailure")

            print exc
            self.log.error("SMTP send failed: %s" % exc)

            self.mailMessage.deliveryExtension.sendFailed()
            self.sent = False

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)


    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{SMTPAccountKind} and
        C{MailMessageKind} from memory, and writes commit info to the logger
        @return: C{None}
        """

        #XXX: Post a failure event back to the Gui
        #XXX: Could just look at the message Delivery Extension state as well
        if not self.sent:
            pass

        self.account.setPinned(False)
        self.mailMessage.setPinned(False)
        self.account = None
        self.mailMessage = None

        Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

    def __getKinds(self):

        accountKind = Mail.MailParcel.getSMTPAccountKind()
        self.account = accountKind.findUUID(self.accountUUID)

        mailMessageKind = Mail.MailParcel.getMailMessageKind()
        self.mailMessage = mailMessageKind.findUUID(self.mailMessageUUID)

        if self.account is None:
            raise SMTPException("No Account for UUID: %s" % self.accountUUID)

        if self.mailMessage is None:
            raise SMTPException("No MailMessage for UUID: %s" % self.mailMessageUUID)

        self.account.setPinned()
        self.mailMessage.setPinned()
