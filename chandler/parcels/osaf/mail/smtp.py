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


class SMTPMailException(common.MailException):
    pass

class SMTPSender(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self, account, mailMessage):
        if account is None or not account.isItemOf(Mail.MailParcel.getSMTPAccountKind()):
            raise SMTPMailException("You must pass in a SMTPAccount instance")

        if mailMessage is None or not mailMessage.isItemOf(Mail.MailParcel.getMailMessageKind()):
            raise SMTPMailException("You must pass in a mailParcel instance")

        viewName = "%s_%s" % (account.displayName, str(UUID.UUID()))

        super(SMTPSender, self).__init__(Globals.repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.mailMessageUUID = mailMessage.itsUUID
        self.mailMessage = None

    #in thread
    def sendMail(self):
        if __debug__:
            self.printCurrentView("sendmail")

        reactor.callFromThread(self.__sendMail)

    #IN Twisted
    def __sendMail(self):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__sendMail")

            self.__getMessageAndAccount()

            """ Refresh our view before adding items to our mail Message
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.commit()

            username  = self.account.username
            passsword = self.account.password
            host    = self.account.host
            port    = self.account.port
            portSSL = self.account.portSSL
            useSSL  = self.account.useSSL
            useAuth = self.account.useAuth
            authRequired = True
            sslRequired = False

            if useSSL = 'SSL':
                sslRequired = True

            if not useAuth:
                authRequired = False
                username = None
                password = None

            self.mailMessage.outgoingMessage(account=self.account)

            messageObject = message.kindToMessageObject(self.mailMessage)
            messageText = messageObject.as_string()
            self.mailMessage.rfc2882Message = message.strToText("rfc2822Message", messageText)

            msg = StringIO(messageText)
            d = defer.Deferred().addCallbacks(self.__mailSuccess, self.__mailFailure)

            #XXX: perhaps commit here

            #XXX: Look in to Bcc Cc
            to_addrs = messageObject['To']
            from_addr = messageObject['From']

        finally:
           self.restorePreviousView()

        if useSSL = 'SSL':
            factory = smtp.ESMTPSenderFactory(username, password, from_addr, to_addrs, msg, d,
                                              0, requireAuthentication=authRequired, requireTransportSecurity=False)

             """Won't see StartTLS here"""
            reactor.connectSSL(host, portSSL, factory,
                               ssl.ClientContextFactory(useM2=1))

        else:
            #pass the context Factory in trySSL
            factory = smtp.ESMTPSenderFactory(username, password, from_addr, to_addrs, msg, d,
                                              0, requireAuthentication=authRequired, requireTransportSecurity=False)

            reactor.connectTCP(host, port, factory)


    """ 
        Set the mail as sent 
        set dateSent perhaps (need a string api for date sent)
        commit mail
    """
    def __mailSuccess(self, result):
        addrs = []

        for address in result[1]:
            addrs.append(address[0])

        self.log.info("SMTP Message sent to %d recipients[%s]" % (result[0], ", ".join(addrs))

        date = DateTime.now()
        self.mailMessage.dateSent = date
        self.mailMessage.dateSentString = message.dateTimeToRFC2882Date(date)

        self.mailMessage.deliveryExtension.sendSucceeded()

        ### NOW Commit the message in a viewThread

    #TODO: Figure out what exc is for all cases
    def __mailFailure(self, exc):
        self.log.error("SMTP send failed: %s" % exc)

        self.mailMessage.deliveryExtension.sendFailed()
        ### Now Commit then post a event back to Don to Display

    def __getMessageAndAccount(self):

        accountKind = Mail.MailParcel.getSMTPAccountKind()
        self.account = accountKind.findUUID(self.accountUUID)

        mailMessageKind = Mail.MailParcel.getMailMessageKind()
        self.mailMessage = mailMessageKind.findUUID(self.mailMessageUUID)

        if self.account is None:
            raise SMTPException("No Account for UUID: %s" % self.account.itsUUID)

        if self.mailMessage is None:
            raise SMTPException("No MailMessage for UUID: %s" % self.mailMessage.itsUUID)

        self.account.setPinned()
        self.mailMessage.setPinned()

