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

#python imports
import cStringIO as StringIO
import logging as logging
from datetime import datetime

#Chandler imports
import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import osaf.contentmodel.mail.Mail as Mail
import application.Globals as Globals
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL as SSL

#Chandler Mail Service imports
import constants as constants
import errors as errors
import message as message
import utils as utils


class _TwistedESMTPSender(smtp.ESMTPSender):

    """Turn off Twisted SMTPClient logging if not in __debug__ mode"""
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

        return smtp.ESMTPSender.tryTLS(self, code, resp, items)

    def smtpState_from(self, code, resp):
        """Overides C{smtp.ESMTPSender} to disconnects from the
           SMTP server before sending the 'MAIL FROM:' command
           to the server when in account testing mode
        """

        if self.factory.testing:
            """
               If in testing mode, Overload the Twisted SMTPClient
               to instead of sending an 'MAIL FROM:' request,
               send a 'QUIT' request and disconnect from the Server.
               This is followed by a call to sentMail which is a Twisted
               method indicating the mail was sent successfully
               method
            """

            self._disconnectFromServer()
            return self.sentMail(200, None, None, None, None)

        return smtp.ESMTPSender.smtpState_from(self, code, resp)


class SMTPClient(TwistedRepositoryViewManager.RepositoryViewManager):
    """Sends a Chandler mail message via SMTP"""

    def __init__(self, repository, account):
        """
           @param repository: A C{DBRepository} instance
           @type repository: C{DBRepository}

           @param account: An SMTP Account content model object
           @type account: C{Mail.MailParcel.SMTPAccountKind}
        """
        assert isinstance(account, Mail.SMTPAccount)

        super(SMTPClient, self).__init__(repository)

        self.accountUUID = account.itsUUID
        self.account = None
        self.curTransport = None
        self.pending = []
        self.testing = False

    def shutdown(self):
        """Cleans up resources before being deleted"""
        if __debug__:
            self.log.warn("SMTPClient shutdown")


    def sendMail(self, mailMessage):
        """
           Sends a mail message via SMTP using the C{SMTPAccount}
           passed to this classes __init__ method

           @param mailMessage: A MailMessage content model object
           @type mailMessage: C{Mail.MailMessageMixin}

           @return: C{None}
        """
        if __debug__:
            self.printCurrentView("sendMail")

        assert isinstance(mailMessage, Mail.MailMessageMixin)

        reactor.callFromThread(self.execInView, self.__sendMail, mailMessage.itsUUID)

    def testAccountSettings(self):
        """Tests the user entered settings for C{SMTPAccount}"""

        if __debug__:
            self.printCurrentView("testAccountSettings")

        reactor.callFromThread(self.execInView, self.__testAccountSettings)

    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryViewManager.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{SMTPAccountKind} and
        C{MailMessageKind} from memory, and writes commit info to the logger
        @return: C{None}
        """
        if __debug__:
            self.printCurrentView("_viewCommitSuccess")

        reactor.callFromThread(self.__actionComplete)

    def __actionComplete(self):
        if __debug__:
            self.printCurrentView("__actionComplete")

        key = None

        mailMessage = self.curTransport.mailMessage

        if mailMessage.deliveryExtension.state == "FAILED":
            key = "displaySMTPSendError"
        else:
            key = "displaySMTPSendSuccess"

        utils.NotifyUIAsync(mailMessage, callable=key)

        self.curTransport = None

        """If there are messages send the next one in the Queue"""
        if len(self.pending) > 0:
            mUUID = self.pending.pop()

            if __debug__:
                self.log.warn("SMTPClient sending next message in Queue %s" % mUUID)

            """Yield to Twisted Event Loop"""
            reactor.callLater(0, self.__sendMail, mUUID)


    def __sendMail(self, mailMessageUUID):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method using the Twisted Asych Reactor"""

        if __debug__:
            self.printCurrentView("__sendMail")

        """If currently sending a message put the next request in the Queue"""
        if self.curTransport is not None:

            sending = (self.curTransport.mailMessage.itsUUID == mailMessageUUID)

            """Check that the mailMessage in not already Queued"""
            if mailMessageUUID in self.pending:
                if __debug__:
                    self.log.warn("SMTPClient Queue already contains message: %s" % mailMessageUUID)

            elif sending:
                """Check that the mailMessage in not currently being sent"""
                if __debug__:
                    self.log.warn("SMTPClient currently sending message: %s" % mailMessageUUID)

            else:
                self.pending.insert(0, mailMessageUUID)

                if __debug__:
                    self.log.warn("SMTPClient adding to the Queue message: %s" % mailMessageUUID)

            return

        """ Refresh our view before retrieving Account info"""
        self.view.refresh()

        """Get the account, get the mail message and hand off to an instance to send
           if someone already sending them put in a queue"""

        self.__getAccount()
        mailMessage = self.__getMailMessage(mailMessageUUID)

        self.curTransport = _SMTPTransport(self)
        self.curTransport.transportMail(mailMessage)

    def __testAccountSettings(self):
        if __debug__:
            self.printCurrentView("__testAccountSettings")

        """ Refresh our view before retrieving Account info"""
        self.view.refresh()

        """Get the account, get the mail message and hand off to an instance to send
           if someone already sending them put in a queue"""
        self.__getAccount()

        self.testing = True
        _SMTPTransport(self).testAccountSettings()

    def __getAccount(self):
        """Returns instances of C{SMTPAccount} based on C{UUID}'s"""

        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)
            assert self.account is not None, "No Account for UUID: %s" % self.accountUUID


    def __getMailMessage(self, mailMessageUUID):
        m = self.view.findUUID(mailMessageUUID)

        assert m is not None, "No MailMessage for UUID: %s" % mailMessageUUID
        return m


class _SMTPTransport(object):
    """Protocol Transportation Delegate used by the C{SMTPClient} to upload a message
       to a Server via the SMTP protocol"""

    def __init__(self, parent):
        """
        @param parent: A SMTP Client
        @type parent: C{SMTPClient}
        """

        self.parent = parent
        self.mailMessage = None

    def transportMail(self, mailMessage):
        """
           Sends a mail message via SMTP using the C{SMTPAccount}
           passed to this classes parent

           @param mailMessage: A MailMessage content model object
           @type mailMessage: C{Mail.MailMessageMixin}

           @return: C{None}
        """

        if __debug__:
            self.parent.printCurrentView("transport.transportMail")

        self.mailMessage = mailMessage

        self.mailMessage.outgoingMessage(self.parent.account)

        """Clear out any previous DeliveryErrors from a previous attempt"""
        for item in self.mailMessage.deliveryExtension.deliveryErrors:
            item.delete()

        """Get the sender's Email Address will either be the Reply-To or From field"""
        sender = self.__getSender()

        if self.__mailMessageHasErrors(sender):
            return


        messageText = message.kindToMessageText(self.mailMessage)

        d = defer.Deferred()
        d.addCallback(self.parent.execInViewThenCommitInThreadDeferred, self.__mailSuccessCheck)
        d.addErrback(self.parent.execInViewThenCommitInThreadDeferred,  self.__mailFailure)

        self.__sendMail(sender.emailAddress, self.__getRcptTo(), messageText, d)


    def testAccountSettings(self):
        """Tests the user entered settings for the parents C{SMTPAccount}"""

        if __debug__:
            self.parent.printCurrentView("transport.testSettings")

        d = defer.Deferred()
        d.addCallback(self.__testSuccess)
        d.addErrback(self.__testFailure)

        self.__sendMail("", [], "", d, True)


    def __sendMail(self, from_addr, to_addrs, messageText, deferred, testing=False):
        if __debug__:
            self.parent.printCurrentView("transport.__sendMail")

        account = self.parent.account

        username         = None
        password         = None
        authRequired     = False
        tlsContext       = None
        securityRequired = False
        heloFallback     = True

        if account.useAuth:
            username     = account.username
            password     = account.password
            authRequired = True
            heloFallback = False

        if account.connectionSecurity == 'TLS':
            tlsContext = Globals.crypto.getSSLContext(self.parent.view)
            securityRequired = True

        msg = StringIO.StringIO(messageText)

        factory = smtp.ESMTPSenderFactory(username, password, from_addr, to_addrs, msg,
                                          deferred, account.numRetries, constants.TIMEOUT,
                                          tlsContext, heloFallback, authRequired, securityRequired)


        if account.connectionSecurity == 'SSL':
            #XXX: This method actually begins the SSL exchange. Confusing name!
            factory.startTLS = True
            factory.sslChecker = SSL.Checker.Checker()
            factory.getContext = lambda : Globals.crypto.getSSLContext(self.parent.view)

        factory.protocol = _TwistedESMTPSender
        factory.testing  = testing

        wrappingFactory = policies.WrappingFactory(factory)
        wrappingFactory.protocol = wrapper.TLSProtocolWrapper

        reactor.connectTCP(account.host, account.port, wrappingFactory)


    def __testSuccess(self, result):
        self.testing = False
        utils.alert(constants.TEST_SUCCESS, self.parent.account.displayName)

    def __testFailure(self, exc):
        self.testing = False

        """Just get the error string do not need the error code"""
        err = self.__getError(exc.value)[1]
        utils.alert(constants.TEST_ERROR, self.parent.account.displayName, err)


    def __mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However
           if at least one recipent is denied by the smtp server we need to
           treat the message as failed for .4B and possibly beyond"""

        if __debug__:
            self.parent.printCurrentView("transport.__mailSuccessCheck")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """

        self.parent.view.refresh()

        if result[0] == len(result[1]):
            self.__mailSuccess(result)

        else:
            self.__mailSomeFailed(result)

    def __mailSuccess(self, result):
        """If the message was send successfully update the
           mailMessage"""

        if __debug__:
            self.parent.printCurrentView("transport.__mailSuccess")

        now = datetime.now()
        self.mailMessage.dateSent = now
        self.mailMessage.dateSentString = utils.dateTimeToRFC2882Date(now)

        self.mailMessage.deliveryExtension.sendSucceeded()

        if __debug__:
            addrs = []

            for address in result[1]:
                addrs.append(address[0])

            self.parent.log.info(constants.UPLOAD_SUCCESS % (", ".join(addrs)))

    def __mailSomeFailed(self, result):
        """
            If one of more recipients were not send an SMTP message update mailMessage object.

            result: (NumOk, [(emailAddress, serverStatusCode, serverResponseString)])
            Collect all results that do not have a 250 and form a string for .4B
        """

        if __debug__:
            self.parent.printCurrentView("transport.__mailSomeFailed")

        errorDate = datetime.now()

        for recipient in result[1]:
            email, code, str = recipient

            if recipient[1] != constants.SMTP_SUCCESS:
                deliveryError = Mail.MailDeliveryError(view=self.parent.view)
                deliveryError.errorCode = code
                deliveryError.errorString = "%s: %s" % (email, str)
                deliveryError.errorDate = errorDate
                self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)

        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            s = [constants.UPLOAD_FAILED_FOR_RECIPIENTS]

            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s.append(deliveryError.__str__())

            self.parent.log.error("\n".join(s))


    def __mailFailure(self, exc):
        """If the mail message was not sent update the mailMessage object"""

        if __debug__:
            self.parent.printCurrentView("transport.__mailFailure")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """
        self.parent.view.refresh()

        self.__recordError(exc.value)
        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s = constants.UPLOAD_FAILED % deliveryError
                self.parent.log.error(s)

    def __recordError(self, err):
        """Helper method to record the C{DeliveryErrors} to the C{SMTPDelivery} object"""

        result = self.__getError(err)

        deliveryError = Mail.MailDeliveryError(view=self.parent.view)

        deliveryError.errorDate   = datetime.now()
        deliveryError.errorCode   = result[0]
        deliveryError.errorString = result[1]

        self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)

    def __getError(self, err):
        errorCode   = None
        errorString = None
        errorType   = str(err.__class__)

        if isinstance(err, smtp.SMTPClientError):
            """Base type for all SMTP Related Errors.
               Capture all the errors that may return -1 as the
               error code and record the actual error code. Those
               SMTPClientError's that slip through will have the
               correct error code from the smtp server.
            """

            errorCode = err.code
            errorString = err.resp

            #if errorType == errors.AUTH_DECLINED_ERROR:
            #if errorType == errors.TLS_ERROR:

            if err.code == -1:
                if errorType == errors.SMTP_DELIVERY_ERROR:
                    errorCode = errors.DELIVERY_CODE

                elif errorType == errors.SMTP_CONNECT_ERROR:
                    errorCode = errors.CONNECTION_CODE

                elif errorType == errors.SMTP_PROTOCOL_ERROR:
                    errorCode = errors.PROTOCOL_CODE

        elif errorType == errors.SMTP_EXCEPTION:
            errorCode = errors.MISSING_VALUE_CODE
            errorString = err.__str__()

        elif isinstance(err, error.ConnectError):
            """ Record the error code of a ConnectionError.
                If a ConnectionError occurs then there was
                a problem communicating with an SMTP server
                and no error code will be returned by the
                server."""

            errorString = err.__str__()

            if errorType == errors.CONNECT_BIND_ERROR:
                errorCode = errors.BIND_CODE

            elif errorType == errors.UNKNOWN_HOST_ERROR:
                errorCode = errors.HOST_UNKNOWN_CODE

            elif errorType == errors.TIMEOUT_ERROR:
                errorCode = errors.TIMEOUT_CODE

            elif errorType == errors.SSL_ERROR:
                errorCode = errors.SSL_CODE

            elif errorType == errors.CONNECTION_REFUSED_ERROR:
                errorCode = errors.CONNECTION_REFUSED_CODE

        elif errorType == errors.DNS_LOOKUP_ERROR:
            errorCode = errors.DNS_LOOKUP_CODE
            errorString = err.__str__()

        elif errorType == errors.M2CRYPTO_ERROR:
            errorCode = errors.M2CRYPTO_CODE

            try:
                #XXX: Special Case should be caught prompting the message to be resend
                #     if the user adds the cert to the chain
                if err.args[0] == errors.M2CRYPTO_CERTIFICATE_VERIFY_FAILED:
                    errorString =  errors.STR_SSL_CERTIFICATE_ERROR
                else:
                    errorString = errors.STR_SSL_ERROR

            except:
               errorString = errors.STR_SSL_ERROR

        else:
            errorCode = errors.UNKNOWN_CODE
            errorString = errors.STR_UNKNOWN_ERROR % (err.__module__, err.__doc__)


        return (errorCode, errorString)


    def __fatalError(self, str):
        """If a fatal error occurred before sending the message i.e. no To Address
           then record the error, log it, and commit the mailMessage containing the
           error info"""
        if __debug__:
            self.parent.printCurrentView("transport.__fatalError")

        e = errors.SMTPException(str)
        self.__recordError(e)
        self.mailMessage.deliveryExtension.sendFailed()

        if __debug__:
            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                self.log.error(constants.UPLOAD_FAILED % deliveryError)


    def __getSender(self):
        """Get the sender of the message"""
        if self.mailMessage.replyToAddress is not None:
            return self.mailMessage.replyToAddress

        elif self.mailMessage.fromAddress is not None:
            return self.mailMessage.fromAddress

        return None

    def __getRcptTo(self):
        """Get all the recipients of this message (to, cc, bcc)"""
        to_addrs = []

        for address in self.mailMessage.toAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.ccAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.bccAddress:
            to_addrs.append(address.emailAddress)

        return to_addrs

    def __mailMessageHasErrors(self, sender):
        """Make sure that the Mail Message has a sender"""
        if sender is None:
            reactor.callLater(0, self.parent.execInViewThenCommitInThread, self.__fatalError, \
                              constants.UPLOAD_FROM_REQUIRED)
            return True

        """Make sure the sender's Email Address is valid"""
        if not Mail.EmailAddress.isValidEmailAddress(sender.emailAddress):
            reactor.callLater(0, self.parent.execInViewThenCommitInThread, self.__fatalError, \
                              constants.UPLOAD_BAD_FROM_ADDRESS % \
                              Mail.EmailAddress.format(sender))
            return True

        """Make sure there is at least one Email Address to send the message to"""
        if len(self.mailMessage.toAddress) == 0:
            reactor.callLater(0, self.parent.execInViewThenCommitInThread, self.__fatalError, \
                              constants.UPLOAD_TO_REQUIRED)
            return True

        errs = []
        errStr = constants.INVALID_EMAIL_ADDRESS

        """Make sure that each Recipients Email Address is valid"""
        for toAddress in self.mailMessage.toAddress:
            if not Mail.EmailAddress.isValidEmailAddress(toAddress.emailAddress):
                errs.append(errStr % ("To", Mail.EmailAddress.format(toAddress)))

        for ccAddress in self.mailMessage.ccAddress:
            if not Mail.EmailAddress.isValidEmailAddress(ccAddress.emailAddress):
                errs.append(errStr % ("Cc", Mail.EmailAddress.format(ccAddress)))

        for bccAddress in self.mailMessage.bccAddress:
            if not Mail.EmailAddress.isValidEmailAddress(bccAddress.emailAddress):
                errs.append(errStr % ("Bcc", Mail.EmailAddress.format(bccAddress)))

        if len(errs) > 0:
            reactor.callLater(0, self.parent.execInViewThenCommitInThread, self.__fatalError, \
                              "\n".join(errs))
            return True

        return False 
