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
import chandlerdb.util.UUID as UUID
import repository.item.Query as Query
import mx.DateTime as DateTime
import twisted.protocols.policies as policies


"""
 Notes:
 ------
 8. Upgrade history logic
 9. Reuse delivery errors and Delivery Method so not recreated on each send
    so they do not get orphaned or delete previous errors a better idea perhaps
 17. Look in to what happens when you resend a message multiple times that succeeds each time
 19. May want to implement own timer
 20. fix conectionLost to self.deferred.errback(err.value)
"""

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class SMTPConstants(object):
    SUCCESS = 250

class ChandlerESMTPSender(smtp.ESMTPSender, policies.TimeoutMixin):
    """The number of seconds before calling C{self.timeout}"""
    timeout = 25

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           If the connection is not Done the method will
           send a C{twisted.mail.smtp.SMTPConnectError}
        """

        if not self.factory.done:
             self.sendError(smtp.SMTPConnectError(-1, "Connection with SMTP server timed out. Please try again later.",
                                                  self.log))
    def connectionMade(self):
        """Sets the timeout timer then calls
           C{twisted.mail.smtp.ESMTPSender.connectionMade}
        """
        self.setTimeout(self.timeout)
        smtp.ESMTPSender.connectionMade(self)

    def sendLine(self, line):
        """Resets the timeout timer then calls
           C{twisted.mail.smtp.ESMTPSender.sendLine}
        """
        self.resetTimeout()
        smtp.ESMTPSender.sendLine(self, line)

    def lineReceived(self, line):
        """Resets the timeout timer then calls
           C{twisted.mail.smtp.ESMTPSender.lineReceived}
        """
        self.resetTimeout()
        smtp.ESMTPSender.lineReceived(self, line)

    def tryTLS(self, code, resp, items):
        """Checks if the client has requested
           a secure SSL connection with the SMTP server.
           If not removes 'STARTTLS' from the servers
           capabilities list. Twisted automatically
           starts a TLS session if it sees a 'STARTTLS'
           in the server capabilities. This is not the
           desired behavior we want.

           Calls C{twisted.mail.smtp.ESMTPSender.tryTLS}
        """
        if not self.factory.useSSL:
            items = common.disableTwistedTLS(items)

        smtp.ESMTPSender.tryTLS(self, code, resp, items)

class ChandlerESMTPSenderFactory(smtp.ESMTPSenderFactory):
    """Overrides C{twisted.mail.smtp.ESMTPSenderFactory} to
       to add a couple of additional parameters useSSL and done
    """

    protocol = ChandlerESMTPSender

    def __init__(self, username, password, fromEmail, toEmail, file, deferred,
                 retries, contextFactory=None, heloFallback=False,
                 requireAuthentication=True, requireTransportSecurity=True,
                 useSSL=False):

        self.useSSL = useSSL
        self.done = False

        smtp.ESMTPSenderFactory.__init__(self, username, password, fromEmail, toEmail,
                                         file, deferred, retries, contextFactory,
                                         heloFallback, requireAuthentication,
                                         requireTransportSecurity)


class SMTPException(common.MailException):
    """Base class for all Chandler SMTP related exceptions"""
    pass


class SMTPSender(RepositoryView.AbstractRepositoryViewManager):
    """Sends a Chandler mail message via SMTP"""

    def __init__(self, account, mailMessage):
        """
           @param account: An SMTP Account content model object
           @type account: C{Mail.MailParcel.SMTPAccountKind}

           @param mailMessage: A MailMessage content model object
           @type account: C{Mail.MailMessageMixin}
        """

        if account is None or not account.isItemOf(Mail.MailParcel.getSMTPAccountKind()):
            raise SMTPMailException("You must pass an SMTPAccount instance")

        if mailMessage is None or not isinstance(mailMessage, Mail.MailMessageMixin):
            raise SMTPMailException("You must pass a MailMessage instance")

        """Create a unique view string to prevent multiple sends using same view"""
        viewName = "SMTPSender_%s_%s" % (str(UUID.UUID()), DateTime.now())

        super(SMTPSender, self).__init__(Globals.repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.mailMessage = None
        self.mailMessageUUID = mailMessage.itsUUID
        self.factory = None

    def sendMail(self):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method"""
        if __debug__:
            self.printCurrentView("sendMail")

        reactor.callFromThread(self.__sendMail)

    def __sendMail(self):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method using the Twisted Asych Reactor"""

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__sendMail")

            self.__getKinds()

            """ Refresh our view before adding items to our mail Message
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """

            self.view.refresh()

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

            #XXX update this
            self.mailMessage.outgoingMessage(account=self.account)

            messageText = message.kindToMessageText(self.mailMessage)

            self.mailMessage.rfc2882Message = message.strToText(self.mailMessage, "rfc2822Message", messageText)
            d = defer.Deferred().addCallbacks(self.__mailSuccessCheck, self.__mailFailure)
            msg = StringIO(messageText)

            to_addrs = []
            from_addr = None

            for address in self.mailMessage.toAddress:
                to_addrs.append(address.emailAddress)

            if self.mailMessage.replyToAddress is not None:
                from_addr = self.mailMessage.replyToAddress.emailAddress

            elif self.mailMessage.fromAddress is not None:
                from_addr = self.mailMessage.fromAddress.emailAddress

        finally:
            self.restorePreviousView()

        """Perform error checking to make sure To, From, and retries have values"""
        if len(to_addrs) == 0:
            self.__fatalError("To Address")
            return

        if from_addr is None or len(from_addr.strip()) == 0:
            self.__fatalError("From Address")
            return

        """Basic retry logic check. Will refine as GUI support for retries is added"""
        if not isinstance(retries, (int, long)) or (retries < 0 or retries > 5):
            self.__fatalError("valid retry number between 0 and 5")
            return

        self.factory = ChandlerESMTPSenderFactory(username, password, from_addr, to_addrs, msg,
                                                  d, retries, sslContext, heloFallback, 
                                                  authRequired, useSSL, useSSL)

        reactor.connectTCP(host, port, self.factory)

    def __mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However
           if at least one recipent is denied by the smtp server we need to
           treat the message as failed for .4B and possibly beyond"""

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailSuccessCheck")

            self.factory.done = True

            """ Refresh our view before adding items to our mail Message
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.refresh()

            if result[0] == len(result[1]):
                self.__mailSuccess(result)

            else:
                self.__mailSomeFailed(result)

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)


    def __mailSuccess(self, result):
        """If the message was send successfully update the
           mailMessage"""

        if __debug__:
            self.printCurrentView("__mailSuccess")

        now = DateTime.now()
        self.mailMessage.dateSent = now
        self.mailMessage.dateSentString = message.dateTimeToRFC2882Date(now)

        self.mailMessage.deliveryExtension.sendSucceeded()

        addrs = []

        for address in result[1]:
            addrs.append(address[0])

        info = "SMTP Message sent to [%s]" % (", ".join(addrs))
        self.log.info(info)

    def __mailSomeFailed(self, result):
        """
            If one of more recipients were not send an SMTP message update mailMessage object.

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

        s = []
        s.append("SMTP Send failed for the following recipients:")

        for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
            s.append(deliveryError.__str__())

        self.log.error("\n".join(s))

    def __mailFailure(self, exc):
        """If the mail message was not sent update the mailMessage object"""

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__mailFailure")

            self.factory.done = True

            """ Refresh our view before adding items to our mail Message
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.refresh()

            self.__recordError(exc.value)
            self.mailMessage.deliveryExtension.sendFailed()

            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s = "SMTP send failed: %s" % deliveryError
                self.log.error(s)

        finally:
           self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)

    def __recordError(self, err):
        """Helper method to record the errors to the mailMessage object"""

        deliveryError = Mail.MailDeliveryError()
        deliveryError.errorDate = DateTime.now()

        """Clear out any errors from a previous attempt"""
        self.mailMessage.deliveryExtension.deliveryErrors = []

        if isinstance(err, smtp.SMTPClientError):
            """Base type for all SMTP Related Errors.
               Capture all the errors that may return -1 as the
               error code and record the actual error code. Those
               SMTPClientError's that slip through will have the
               correct error code from the smtp server.
            """

            if __debug__ and self.account.useSSL and err.log is not None:
                self.log.error("\n%s" % err.log)

            #if isinstance(err, smtp.AUTHDeclinedError):
                #print "AUTHENTICATION ERROR Display a password dialog"

            #if isinstance(err, smtp.TLSError):
                #print "TLS failed to start display a dialog saying would you like to try non-TLS mode"

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

        elif isinstance(err, SMTPException):
            deliveryError.errorCode = errorCode.MISSING_VALUE_ERROR
            deliveryError.errorString = err.__str__()

        elif isinstance(err, error.ConnectError):
            """ Record the error code of a  ConnectionError.
                If a ConnectionError occurs then there was
                a problem communicating with an SMTP server
                and no error code will be returned by the
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

        elif isinstance(err, error.DNSLookupError):
            deliveryError.errorCode = errorCode.DNS_LOOKUP_ERROR
            deliveryError.errorString = err.__str__()

        elif isinstance(err, Exception):
            deliveryError.errorCode = errorCode.UNKNOWN_ERROR
            deliveryError.errorString = err.__str__()
            s = "Unknown Exception encountered docString: %s module: %s" % (err.__doc__, err.__module__)
            self.log.error(s)

        else:
            deliveryError.errorCode = errorCode.UNKNOWN_ERROR
            deliveryError.errorString = err.__str__() + " UNKNOWN TYPE NOT AN EXCEPTION"
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

        if not self.account.itsView.isRefCounted():
            self.account.setPinned(False)
            self.mailMessage.setPinned(False)
        self.account = None
        self.mailMessage = None

        Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

    def __fatalError(self, str):
        """If a fatal error occurred before sending the message i.e. no To Address
           then record the error, log it, and commit the mailMessage containing the
           error info"""

        e = SMTPException("A %s is required to send an SMTP Mail Message." % str)
        self.__recordError(e)
        self.mailMessage.deliveryExtension.sendFailed()

        for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
            s = "SMTP send failed: %s" % deliveryError
            self.log.error(s)

        self.commitView(True)

    def __getKinds(self):
        """Returns instances of C{SMTPAccount} and C{MailMessage}
           based on C{UUID}'s"""

        accountKind = Mail.MailParcel.getSMTPAccountKind()
        self.account = accountKind.findUUID(self.accountUUID)

        mailMessageKind = Mail.MailParcel.getMailMessageKind()
        self.mailMessage = mailMessageKind.findUUID(self.mailMessageUUID)

        if self.account is None:
            raise SMTPException("No Account for UUID: %s" % self.accountUUID)

        if self.mailMessage is None:
            raise SMTPException("No MailMessage for UUID: %s" % self.mailMessageUUID)

        if not self.account.itsView.isRefCounted():
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
