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
import twisted.internet.error as error
import errors as errorCode
import message as message
import osaf.contentmodel.mail.Mail as Mail
import repository.util.UUID as UUID
import repository.item.Query as Query
import mx.DateTime as DateTime

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class SMTPConstants(object):
    SUCCESS = 250

class ChandlerESMTPSender(smtp.ESMTPSender):

    def sendLine(self, line):
        """This method utilized for debugging SSL IMAP4 Communications"""
        if __debug__ and self.factory.useSSL:
            self.factory.log.info(">>> %s" % line)

        smtp.ESMTPSender.sendLine(self, line)

    def lineReceived(self, line):
        """This method utilized for debugging SSL IMAP4 Communications"""
        if __debug__ and self.factory.useSSL:
            self.factory.log.info("<<< %s" % line)

        smtp.ESMTPSender.lineReceived(self, line)

    def tryTLS(self, code, resp, items):
        if not self.factory.useSSL:
            items = common.disableTwistedTLS(items)

        smtp.ESMTPSender.tryTLS(self, code, resp, items)

class ChandlerESMTPSenderFactory(smtp.ESMTPSenderFactory):

    protocol = ChandlerESMTPSender

    def __init__(self, username, password, fromEmail, toEmail, file, deferred, log,
                 retries=5, contextFactory=None, heloFallback=False, 
                 requireAuthentication=True, requireTransportSecurity=True, 
                 useSSL=False):

        self.useSSL = useSSL
        self.log = log

        smtp.ESMTPSenderFactory.__init__(self, username, password, fromEmail, toEmail,
                                         file, deferred, retries, contextFactory, 
                                         heloFallback, requireAuthentication, 
                                         requireTransportSecurity)


class SMTPException(common.MailException):
    pass


class SMTPSender(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self, account, mailMessage, deferred=None):
        if account is None or not account.isItemOf(Mail.MailParcel.getSMTPAccountKind()):
            raise SMTPMailException("You must pass an SMTPAccount instance")

        if mailMessage is None or not isinstance(mailMessage, Mail.MailMessageMixin):
            raise SMTPMailException("You must pass a MailMessage instance")

        viewName = "SMTPSender_%s" % str(UUID.UUID())

        super(SMTPSender, self).__init__(Globals.repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.mailMessage = None
        self.mailMessageUUID = mailMessage.itsUUID
        self.deferred = deferred
        self.failure = None
        self.success = None

    def sendMail(self):
        if __debug__:
            self.printCurrentView("sendMail")

        reactor.callFromThread(self.__sendMail)

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
            retries      = self.account.numRetries
            authRequired = True
            sslContext   = None
            heloFallback = False

            if not useAuth:
                authRequired = False
                heloFallback = True
                username     = None
                password     = None

            if useSSL:
                sslContext = ssl.ClientContextFactory(useM2=1)

            self.mailMessage.outgoingMessage(account=self.account)

            messageText = message.kindToMessageText(self.mailMessage)

            self.mailMessage.rfc2882Message = message.strToText(self.mailMessage, "rfc2822Message", messageText)
            d = defer.Deferred().addCallbacks(self.__mailSuccessCheck, self.__mailFailure)
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

        factory = ChandlerESMTPSenderFactory(username, password, from_addr, to_addrs, msg, 
                                             d, self.log, retries, sslContext, 
                                             heloFallback, authRequired, useSSL, useSSL)

        reactor.connectTCP(host, port, factory)

    def __mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However 
           if at least one recipent is denied by the smtp server we need to 
           treat the message as failed for .4B and possibly beyond"""

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailSuccessCheck")

            if result[0] == len(result[1]):
                self.__mailSuccess(result)

            else:
                self.__mailSomeFailed(result)

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)


    def __mailSuccess(self, result):
        if __debug__:
            self.printCurrentView("__mailSuccess")

        self.mailMessage.dateSent = DateTime.now()
        self.mailMessage.dateSentString = message.dateTimeToRFC2882Date(DateTime.now())

        self.mailMessage.deliveryExtension.sendSucceeded()

        addrs = []

        for address in result[1]:
            addrs.append(address[0])

        info = "SMTP Message sent to [%s]" % (", ".join(addrs))
        self.log.info(info)

        self.success = result

    def __mailSomeFailed(self, result):
        """
            result: (NumOk, [(emailAddress, serverStatusCode, serverResponseString)])
            Collect all results that do not have a 250 and form a string for .4B
        """

        if __debug__:
            self.printCurrentView("__mailSomeFailed")

        """Clear out any errors from a previous attempt"""
        self.mailMessage.deliveryExtension.deliveryErrors = []

        errorDate = DateTime.now()

        for recipient in result[1]:
            email, code, str = recipient
            if recipient[1] != SMTPConstants.SUCCESS:
                deliveryError = Mail.MailDeliveryError()
                deliveryError.errorCode = code
                deliveryError.errorString = str
                deliveryError.errorDate = errorDate
                self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)

        self.mailMessage.deliveryExtension.sendFailed()

        #XXX: Need to revisit this logic
        self.failure = result[1]

        s = []
        s.append("SMTP Send failed for the following recipients:")

        for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
            s.append(deliveryError.__str__())

        self.log.error("\n".join(s))


    def __mailFailure(self, exc):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailFailure")

            self.__recordError(exc.value)
            self.mailMessage.deliveryExtension.sendFailed()

            #XXX Not sure we need this anymore
            self.failure = exc.value

            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s = "SMTP send failed: %s" % deliveryError
                self.log.error(s)

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)

    def __recordError(self, err):
        deliveryError = Mail.MailDeliveryError()

        """Clear out any errors from a previous attempt"""
        self.mailMessage.deliveryExtension.deliveryErrors = []

        if isinstance(err, smtp.SMTPClientError):
            """Base type for all SMTP Related Errors.
               Capture all the errors that may return -1 as the
               error code and record the actual error code. Those
               SMTPClientError's that slip through will have the
               correct error code from the smtp server.
            """

            if isinstance(err, smtp.SMTPDeliveryError):
                if err.code == -1:
                    deliveryError.errorCode = errorCode.DELIVERY_ERROR

            elif isinstance(err, smtp.SMTPConnectError):
                if err.code == -1:
                    deliveryError.errorCode = errorCode.CONNECTION_ERROR

            elif isinstance(err, smtp.SMTPProtocolError):
                if err.code == -1:
                    deliveryError.errorCode = errorCode.PROTOCOL_ERROR

            if err.code != -1:
                deliveryError.errorCode = err.code

            deliveryError.errorString = err.resp
            deliveryError.errorDate = DateTime.now()

        elif isinstance(err, error.ConnectError):
            """ Record the error code of a  ConnectionError.
                If a ConnectionError occurs then there was
                a problem communicating with a SMTP server
                and no error code will be returned by theA
                server."""

            if isinstance(err, error.ConnectBindError):
                deliveryError.errorCode = errorCode.BIND_ERROR

            elif isinstance(err, error.UnknownHostError):
                deliveryError.errorCode = errorCode.UNKNOWN_HOST_ERROR

            elif isinstance(err, error.TimeoutError):
                deliveryError.errorCode = errorCode.TIMEOUT_ERROR

            elif isinstance(err, error.SSLError):
                deliveryError.errorCode = errorCode.SSL_ERROR

            elif isinstance(err, error.ConnectionRefusedError):
                deliveryError.errorCode = errorCode.CONNECTION_REFUSED_ERROR

            else:
                deliveryError.errorCode = errorCode.UNKNOWN_ERROR
                self.log.error("Unknown TCP Error encountered docString: ", err.__doc__)


            deliveryError.errorString = err.__str__()
            deliveryError.errorDate = DateTime.now()

        elif isinstance(err, error.DNSLookupError):
            deliveryError.errorCode = errorCode.DNS_LOOKUP_ERROR
            deliveryError.errorString = err.__str__()
            deliveryError.errorDate = DateTime.now()

        elif isinstance(err, Exception):
            deliveryError.errorCode = errorCode.UNKNOWN_ERROR
            deliveryError.errorString = err.__str__()
            deliveryError.errorDate = DateTime.now()
            s = "Unknown Exception encountered docString: %s module: %s" % (err.__doc__, err.__module__)
            self.log.error(s)

        else:
            deliveryError.errorCode = errorCode.UNKNOWN_ERROR
            deliveryError.errorString = err.__str__() + " UNKNOWN TYPE NOT A EXCEPTION"
            deliveryError.errorDate = DateTime.now()
            s = "Unknown Non-Exception encountered docString: %s module: %s" % (err.__doc__, err.__module__)
            self.log.error(s)

        self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)


    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{SMTPAccountKind} and
        C{MailMessageKind} from memory, and writes commit info to the logger
        @return: C{None}
        """

        self.account.setPinned(False)
        self.mailMessage.setPinned(False)
        self.account = None
        self.mailMessage = None

        Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

        #XXX: Post a failure event back to the Gui
        #XXX: Could just look at the message Delivery Extension state as well
        if self.failure is not None:
            if self.deferred is not None:
                self.deferred.errback(self.failure)

        elif self.success is not None:
            if self.deferred is not None:
                self.deferred.callback(self.success)

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

def getSMTPAccount(UUID=None):
    """
    This method returns a tuple containing:
        1. An C{SMTPAccount} account in the Repository.
        2. The ReplyTo C{EmailAddress} associated with the C{SMTPAccounts}
           parent which will either be a POP or IMAP Acccount.

    The method will throw a C{SMTPException} if:
    1. No C{SMTPAccount} in the Repository
    2. No parent account associated with the C{SMTPAccount}
    3. The replyToAddress of the parent account is None

    @param UUID: The C{UUID} of the C{SMTPAccount}. If no C{UUID} passed will return
                 the default (first) C{SMTPAccount}
    @type UUID: C{UUID}
    @return C{tuple} in the form (C{SMTPAccount}, C{EmailAddress})
    """

    accountKind = Mail.MailParcel.getSMTPAccountKind()
    account = None
    replyToAddress = None

    if UUID is not None:
        if not isinstance(UUID.UUID):
            raise SMTPException("The UUID argument must be of type UUID.UUID")

        account = accountKind.findUUID(UUID)

    else:
        """Get the first SMTP Account"""
        for acc in Query.KindQuery().run([accountKind]):
            account = acc
            break

    if account is None:
        raise SMTPException("No SMTP Account found")

    accList = account.accounts

    if accList is None:
        raise SMTPException("No Parent Accounts associated with the SMTP account. Can not get replyToAddress.")

    """Get the first IMAP Account"""
    for parentAccount in accList:
        replyToAddress = parentAccount.replyToAddress
        break

    if replyToAddress is None:
        raise SMTPException("No replyToAddress found for IMAP Account")

    return (account, replyToAddress)
