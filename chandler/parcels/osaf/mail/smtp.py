__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.mail.smtp as smtp
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.internet.error as error
import twisted.protocols.policies as policies

#python / mx imports
import email.Message as Message
import mx.DateTime as DateTime
import cStringIO as StringIO
import logging as logging

#Chandler imports
import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import osaf.contentmodel.mail.Mail as Mail
import chandlerdb.util.UUID as UUID
import crypto.ssl as ssl
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper

#Chandler Mail Service imports
import constants as constants
import errors as errors
import message as message
import utils as utils


"""
 Notes:
 ------
1. Should sending use a pool or a queue
2. Do we really need the error codes (Perhaps not)
3. Could make smtp class just a transport and pass around a tuple of the account, message, and view).
   Else need safeguards to make sure smtp not called 2x at same time. Can have a parent account class
   that spawns an SMTPSender for each request
   
"""

class ChandlerESMTPSender(smtp.ESMTPSender):

    """Turn off SMTPClient logging if not in __debug__ mode"""
    if not __debug__:
        debug = False

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
        if not self.requireTransportSecurity:
            items = utils.disableTwistedTLS(items)

        smtp.ESMTPSender.tryTLS(self, code, resp, items)


class SMTPSender(TwistedRepositoryViewManager.RepositoryViewManager):
    """Sends a Chandler mail message via SMTP"""

    def __init__(self, repository, account, mailMessage):
        """
           @param account: An SMTP Account content model object
           @type account: C{Mail.MailParcel.SMTPAccountKind}

           @param mailMessage: A MailMessage content model object
           @type account: C{Mail.MailMessageMixin}
        """

        assert account is not None and account.isItemOf(Mail.SMTPAccount.getKind(repository.view))
        assert mailMessage is not None and isinstance(mailMessage, Mail.MailMessageMixin)

        """Create a unique view string to prevent multiple sends using same view"""
        viewName = "SMTPSender_%s_%s" % (str(UUID.UUID()), DateTime.now())

        super(SMTPSender, self).__init__(repository, viewName)

        self.accountUUID = account.itsUUID
        self.mailMessageUUID = mailMessage.itsUUID
        self.account = None
        self.mailMessage = None

    def sendMail(self):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method"""
        if __debug__:
            self.printCurrentView("sendMail")

        reactor.callFromThread(self.execInView, self.__sendMail)

    def __sendMail(self):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method using the Twisted Asych Reactor"""

        if __debug__:
            self.printCurrentView("__sendMail")

        self.__getKinds()

        """Clear out any previous DeliveryErrors from a previous attempt"""
        for item in self.mailMessage.deliveryExtension.deliveryErrors:
            item.delete()

        self.mailMessage.outgoingMessage(account=self.account)

        messageText = message.kindToMessageText(self.mailMessage)

        d = defer.Deferred()
        d.addCallback(self.execInViewThenCommitInThreadDeferred, self.__mailSuccessCheck)
        d.addErrback(self.execInViewThenCommitInThreadDeferred,  self.__mailFailure)

        to_addrs = self.__getRcptTo()
        from_addr = self.__getMailFrom()

        """Perform error checking to make sure To, From have values"""
        if len(to_addrs) == 0:
            self.execInViewThenCommitInThread(self.__fatalError("To Address"))
            return

        if from_addr is None or len(from_addr.strip()) == 0:
            self.execInViewThenCommitInThread(self.__fatalError("From Address"))
            return

        SMTPSender.sendMailMessage(from_addr, to_addrs, messageText, d, self.account)

    def __mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However
           if at least one recipent is denied by the smtp server we need to
           treat the message as failed for .4B and possibly beyond"""

        if __debug__:
            self.printCurrentView("__mailSuccessCheck")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """

        self.view.refresh()

        if result[0] == len(result[1]):
            self.__mailSuccess(result)

        else:
            self.__mailSomeFailed(result)

    def __mailSuccess(self, result):
        """If the message was send successfully update the
           mailMessage"""

        if __debug__:
            self.printCurrentView("__mailSuccess")

        now = DateTime.now()
        self.mailMessage.dateSent = now
        self.mailMessage.dateSentString = utils.dateTimeToRFC2882Date(now)

        self.mailMessage.deliveryExtension.sendSucceeded()

        if __debug__:
            addrs = []

            for address in result[1]:
                addrs.append(address[0])

            self.log.info("SMTP Message sent to [%s]" % (", ".join(addrs)))

    def __mailSomeFailed(self, result):
        """
            If one of more recipients were not send an SMTP message update mailMessage object.

            result: (NumOk, [(emailAddress, serverStatusCode, serverResponseString)])
            Collect all results that do not have a 250 and form a string for .4B
        """

        if __debug__:
            self.printCurrentView("__mailSomeFailed")

        errorDate = DateTime.now()

        for recipient in result[1]:
            email, code, str = recipient

            if recipient[1] != constants.SMTP_SUCCESS:
                deliveryError = Mail.MailDeliveryError(view=self.getCurrentView())
                deliveryError.errorCode = code
                deliveryError.errorString = "%s: %s" % (email, str)
                deliveryError.errorDate = errorDate
                self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)

        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            s = []
            s.append("SMTP Send failed for the following recipients:")

            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s.append(deliveryError.__str__())

            self.log.error("\n".join(s))


    def __mailFailure(self, exc):
        """If the mail message was not sent update the mailMessage object"""

        if __debug__:
            self.printCurrentView("__mailFailure")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """
        self.view.refresh()

        self.__recordError(exc.value)
        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s = "SMTP send failed: %s" % deliveryError
                self.log.error(s)

    def __recordError(self, err):
        """Helper method to record the errors to the mailMessage object"""

        deliveryError = Mail.MailDeliveryError(view=self.getCurrentView())
        deliveryError.errorDate = DateTime.now()
        errorType = str(err.__class__)

        if isinstance(err, smtp.SMTPClientError):
            """Base type for all SMTP Related Errors.
               Capture all the errors that may return -1 as the
               error code and record the actual error code. Those
               SMTPClientError's that slip through will have the
               correct error code from the smtp server.
            """

            #XXX: Users password may get logged will need to enhance in a 
            #     future release to prevent this from happening
            if __debug__ and self.account.useSSL and err.log is not None:
                self.log.error("\n%s" % err.log)

            deliveryError.errorCode = err.code
            deliveryError.errorString = err.resp

            #if errorType == errors.AUTH_DECLINED_ERROR:
            #if errorType == errors.TLS_ERROR:

            if err.code == -1:
                if errorType == errors.SMTP_DELIVERY_ERROR:
                    deliveryError.errorCode = errors.DELIVERY_CODE

                elif errorType == errors.SMTP_CONNECT_ERROR:
                    deliveryError.errorCode = errors.CONNECTION_CODE

                elif errorType == errors.SMTP_PROTOCOL_ERROR:
                    deliveryError.errorCode = errors.PROTOCOL_CODE

        elif errorType == errors.SMTP_EXCEPTION:
            deliveryError.errorCode = errors.MISSING_VALUE_CODE
            deliveryError.errorString = err.__str__()

        elif isinstance(err, error.ConnectError):
            """ Record the error code of a ConnectionError.
                If a ConnectionError occurs then there was
                a problem communicating with an SMTP server
                and no error code will be returned by the
                server."""

            deliveryError.errorString = err.__str__()

            if errorType == errors.CONNECT_BIND_ERROR:
                deliveryError.errorCode = errors.BIND_CODE

            elif errorType == errors.UNKNOWN_HOST_ERROR:
                deliveryError.errorCode = errors.HOST_UNKNOWN_CODE

            elif errorType == errors.TIMEOUT_ERROR:
                deliveryError.errorCode = errors.TIMEOUT_CODE

            elif errorType == errors.SSL_ERROR:
                deliveryError.errorCode = errors.SSL_CODE

            elif errorType == errors.cONNECTION_REFUSED_ERROR:
                deliveryError.errorCode = errors.CONNECTION_REFUSED_CODE

        elif errorType == errors.DNS_LOOKUP_ERROR:
            deliveryError.errorCode = errors.DNS_LOOKUP_CODE
            deliveryError.errorString = err.__str__()

        else:
            deliveryError.errorCode = errors.UNKNOWN_CODE
            s = "Unknown Exception encountered docString: %s module: %s" % (err.__doc__, err.__module__)
            deliveryError.errorString = s

        self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)


    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{SMTPAccountKind} and
        C{MailMessageKind} from memory, and writes commit info to the logger
        @return: C{None}
        """

        if __debug__:
            self.printCurrentView("_viewCommitSuccess")

        key = None

        if self.mailMessage.deliveryExtension.state == "FAILED":
            key = "displaySMTPSendError"
        else:
            key = "displaySMTPSendSuccess"

        utils.NotifyUIAsync(self.mailMessage, callable=key)
        self.account = None
        self.mailMessage = None

    def __fatalError(self, str):
        """If a fatal error occurred before sending the message i.e. no To Address
           then record the error, log it, and commit the mailMessage containing the
           error info"""
        if __debug__:
            self.printCurrentView("__fatalError")

        e = errors.SMTPException("A %s is required to send an SMTP Mail Message." % str)
        self.__recordError(e)
        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s = "SMTP send failed: %s" % deliveryError
                self.log.error(s)

    def __getKinds(self):
        """Returns instances of C{SMTPAccount} and C{MailMessage}
           based on C{UUID}'s"""

        view = self.getCurrentView()
        accountKind = Mail.SMTPAccount.getKind(view)
        self.account = accountKind.findUUID(self.accountUUID)

        mailMessageKind = Mail.MailMessage.getKind(view)
        self.mailMessage = mailMessageKind.findUUID(self.mailMessageUUID)

        assert self.account is not None, "No Account for UUID: %s" % self.accountUUID
        assert self.mailMessage is not None, "No MailMessage for UUID: %s" % self.mailMessageUUID

    def __getMailFrom(self):
        #XXX: Will want to refine how this look is done when mail preferences are in place
        if self.mailMessage.replyToAddress is not None:
            return self.mailMessage.replyToAddress.emailAddress

        elif self.mailMessage.fromAddress is not None:
            return self.mailMessage.fromAddress.emailAddress

        return None

    def __getRcptTo(self):
        to_addrs = []

        for address in self.mailMessage.toAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.ccAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.bccAddress:
            to_addrs.append(address.emailAddress)

        return to_addrs

    def sendMailMessage(cls, from_addr, to_addrs, messageText, deferred, account):
        #XXX: Perform some error checking
        username     = None
        password     = None
        authRequired = False
        sslContext   = None
        heloFallback = True

        if account.useAuth:
            username     = account.username
            password     = account.password
            authRequired = True
            heloFallback = False

        if account.useSSL:
            sslContext = ssl.getSSLContext()

        msg = StringIO.StringIO(messageText)

        factory = smtp.ESMTPSenderFactory(username, password, from_addr, to_addrs, msg,
                                          deferred, account.numRetries, constants.TIMEOUT,
                                          sslContext, heloFallback, authRequired, account.useSSL)

        factory.protocol = ChandlerESMTPSender
        wrappingFactory = policies.WrappingFactory(factory)
        wrappingFactory.protocol = wrapper.TLSProtocolWrapper

        reactor.connectTCP(account.host, account.port, wrappingFactory)

    sendMailMessage = classmethod(sendMailMessage)
