#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


#twisted imports
import twisted.mail.smtp as smtp
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.internet.error as error
import twisted.protocols.policies as policies
from twisted.internet import threads

#python imports
import cStringIO as StringIO
from datetime import datetime

#PyICU imports
from PyICU import ICUtzinfo

#Chandler imports
import osaf.pim.mail as Mail
from osaf.framework.certstore import ssl
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryError \
    import RepositoryError, VersionConflictError
import application.Utility as Utility

#Chandler Mail Service imports
import constants
import errors
from utils import *
from message import *
import message

__all__ = ['SMTPClient']


class _TwistedESMTPSender(smtp.ESMTPSender):

    """Turn off Twisted SMTPClient logging """
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
            items = disableTwistedTLS(items)
        else:
            """We want to use the M2Crypto SSL context so assign it here"""
            self.context = self.transport.contextFactory.getContext()

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

class SMTPClient(object):
    """Sends a Chandler mail message via SMTP"""

    def __init__(self, view, account):
        """
           @param view: A C{RepositoryView} instance
           @type view: C{RepositoryView}

           @param account: An SMTP Account domain model object
           @type account: C{Mail.SMTPAccount}
        """
        assert isinstance(account, Mail.SMTPAccount)
        assert isinstance(view, RepositoryView)

        self.view = view

        self.accountUUID = account.itsUUID
        self.account = None
        self.pending = []
        self.testing = False
        self.displayed = False
        self.mailMessage = None

    def sendMail(self, mailMessage):
        """
           Sends a mail message via SMTP using the C{SMTPAccount}
           passed to this classes __init__ method

           @param mailMessage: A MailMessage domain model object
           @type mailMessage: C{Mail.MailStamp}

           @return: C{None}
        """
        assert isinstance(mailMessage, Mail.MailStamp)

        if __debug__:
            trace("sendMail")

        reactor.callFromThread(self._prepareForSend, mailMessage.itsItem.itsUUID)

    def testAccountSettings(self):
        """Tests the user entered settings for C{SMTPAccount}"""

        if __debug__:
            trace("testAccountSettings")

        reactor.callFromThread(self._testAccountSettings)

    def _commit(self):
        if __debug__:
            trace("_commit")

        def _tryCommit():
            try:
                self.view.commit()
            except RepositoryError, e:
                #Place holder for commit rollback
                trace(e)
                raise
            except VersionConflictError, e1:
                #Place holder for commit rollback
                trace(e1)
                raise

        d = threads.deferToThread(_tryCommit)
        #XXX: May want to handle the case where the Repository fails
        #     to commit. For example, role back transaction or display
        #     Repository error to the user
        d.addCallbacks(lambda _: self._actionCompleted())
        return d

    def _actionCompleted(self):
        if __debug__:
            trace("_actionCompleted")

        if not self.displayed:
            if self.mailMessage.deliveryExtension.state == "FAILED":
                 key = "displaySMTPSendError"
            else:
                 key = "displaySMTPSendSuccess"

            NotifyUIAsync(self.mailMessage, cl=key)


            """If there are messages send the next one in the Queue
               and we have not displayed the Add Certificate Dialog"""
            if len(self.pending) > 0:
                mUUID = self.pending.pop()

                if __debug__:
                    trace("SMTPClient sending next message in Queue %s" % mUUID)

                """Yield to Twisted Event Loop"""
                reactor.callLater(0, self._prepareForSend, mUUID)

        self.mailMessage = None
        self.displayed  = False

    def _prepareForSend(self, mailMessageUUID):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method using the Twisted Asych Reactor"""

        if __debug__:
            trace("_prepareForSend")

        """If currently sending a message put the next request in the Queue."""

        try:
            if self.mailMessage is not None:
                sending = (self.mailMessage.itsItem.itsUUID == mailMessageUUID)
    
                """Check that the mailMessage in not already Queued"""
                if mailMessageUUID in self.pending:
                    if __debug__:
                        trace("SMTPClient Queue already contains message: %s" % mailMessageUUID)
    
                elif sending:
                    """Check that the mailMessage in not currently being sent"""
                    if __debug__:
                        trace("SMTPClient currently sending message: %s" % mailMessageUUID)
    
                else:
                    self.pending.insert(0, mailMessageUUID)
    
                    if __debug__:
                        trace("SMTPClient adding to the Queue message: %s" % mailMessageUUID)
    
                return
    
            """ Refresh our view before retrieving Account info"""
            self.view.refresh()
    
            """Get the account, get the mail message and hand off to an instance to send
               if someone already sending them put in a queue"""
    
            self._getAccount()
            self.mailMessage = self._getMailMessage(mailMessageUUID)
    
            self.mailMessage.outgoingMessage(self.account)
            now = datetime.now(ICUtzinfo.default)
            self.mailMessage.dateSent = now
            self.mailMessage.dateSentString = dateTimeToRFC2822Date(now)
    
            """Clear out any previous DeliveryErrors from a previous attempt"""
            for item in self.mailMessage.deliveryExtension.deliveryErrors:
                item.delete()
    
            """Get the sender's Email Address will either be the Reply-To or From field"""
            sender = self._getSender()
    
            if self._mailMessageHasErrors(sender):
                return
    
            messageText = kindToMessageText(self.mailMessage)
        except Exception, e:
            if __debug__:
                trace(e)
            raise

        d = defer.Deferred()
        d.addCallback(self._mailSuccessCheck)
        d.addErrback(self._mailFailure)

        self._sendingMail(sender.emailAddress, self._getRcptTo(), messageText, d)

    def _testAccountSettings(self):
        if __debug__:
            trace("_testAccountSettings")

        """ Refresh our view before retrieving Account info"""
        self.view.refresh()

        """Get the account, get the mail message and hand off to an instance to send
           if someone already sending them put in a queue"""
        self._getAccount()

        self.testing = True

        d = defer.Deferred()
        d.addCallback(self._testSuccess)
        d.addErrback(self._testFailure)

        self._sendingMail("", [], "", d, True)


    def _sendingMail(self, from_addr, to_addrs, messageText, deferred, testing=False):
        if __debug__:
            trace("_sendingMail")

        username         = None
        password         = None
        authRequired     = False
        securityRequired = False
        heloFallback     = True

        if self.account.useAuth:
            username     = self.account.username
            password     = self.account.password
            authRequired = True
            heloFallback = False

        if testing:
            retries = 0
            timeout = constants.TESTING_TIMEOUT
        else:
            retries = self.account.numRetries
            timeout = self.account.timeout

        if self.account.connectionSecurity == 'TLS':
            securityRequired = True

        msg = StringIO.StringIO(messageText)

        # Note that we cheat with the context factory here (value=1),
        # because ssl.connectSSL does it automatically, and in the
        # case of STARTTLS we override esmtpState_starttls above
        # to supply the correct SSL context.
        factory = smtp.ESMTPSenderFactory(username, password, from_addr,
                                          to_addrs, msg,
                                          deferred, retries, timeout,
                                          1, heloFallback, authRequired,
                                          securityRequired)

        factory.protocol   = _TwistedESMTPSender
        factory.testing    = testing

        if self.account.connectionSecurity == 'SSL':
            ssl.connectSSL(self.account.host, self.account.port, factory,
                           self.view)
        else:
            ssl.connectTCP(self.account.host, self.account.port, factory,
                           self.view)

    def _testSuccess(self, result):
        if __debug__:
            trace("_testSuccess")

        alert(constants.TEST_SUCCESS, {'accountName': self.account.displayName})

        self.testing = False


    def _testFailure(self, exc):
        if __debug__:
            trace("_testFailure")

        exc = exc.value

        if not self.displayedRecoverableSSLErrorDialog(exc):
            """Just get the error string do not need the error code"""
            err = self._getError(exc)[1]
            alert(constants.TEST_ERROR, {'accountName': self.account.displayName, 'error': err})

        self.testing = False

    def _mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However
           if at least one recipent is denied by the smtp server we need to
           treat the message as failed for .4B and possibly beyond"""

        if __debug__:
            trace("_mailSuccessCheck")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """

        self.view.refresh()

        if result[0] == len(result[1]):
            self._mailSuccess(result)

        else:
            self._mailSomeFailed(result)

        return self._commit()


    def _mailSuccess(self, result):
        """If the message was send successfully update the
           mailMessage"""

        if __debug__:
            trace("_mailSuccess")

        self.mailMessage.deliveryExtension.sendSucceeded()

    def _mailSomeFailed(self, result):
        """
            If one of more recipients were not send an SMTP message update mailMessage object.

            result: (NumOk, [(emailAddress, serverStatusCode, serverResponseString)])
            Collect all results that do not have a 250 and form a string for .4B
        """

        if __debug__:
            trace("_mailSomeFailed")

        errorDate = datetime.now()

        for recipient in result[1]:
            email, code, st = recipient

            if recipient[1] != constants.SMTP_SUCCESS:
                deliveryError = Mail.MailDeliveryError(itsView=self.view)
                deliveryError.errorCode = code
                deliveryError.errorString = u"%s: %s" % (email, st)
                deliveryError.errorDate = errorDate
                self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)

        self.mailMessage.deliveryExtension.sendFailed()
        # Unset the date-sent info in the message
        del self.mailMessage.dateSent
        self.mailMessage.dateSentString = ''

        if __debug__:
            s = ["Send failed for the following recipients"]

            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                s.append(deliveryError.__str__())

            trace("\n".join(s))


    def _mailFailure(self, exc):
        """If the mail message was not sent update the mailMessage object"""

        if __debug__:
            trace("_mailFailure")

        """ Refresh our view before adding items to our mail Message
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """
        self.view.refresh()

        # Unset the date-sent info in the message
        del self.mailMessage.dateSent
        self.mailMessage.dateSentString = ''

        exc = exc.value

        displayed = self.displayedRecoverableSSLErrorDialog(exc, self.mailMessage)

        if not displayed:
            """Only record errors if the add cert is not displayed.
               The state of a add cert will remain draft until a
               user actually adds a cert at which point the mail code
               will be called again and the state will be updated"""

            self._recordError(exc)

            if __debug__:
                for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                    trace("Unable to send %s" % deliveryError)

            return self._commit()

        else:
            """Clear the status bar message"""
            self.displayed = True
            NotifyUIAsync("", cl='setStatusMessage')

            """Reset the SMTPClient"""
            self._actionCompleted()

    def _recordError(self, err):
        """Helper method to record the C{DeliveryErrors} to the C{SMTPDelivery} object"""

        result = self._getError(err)

        deliveryError = Mail.MailDeliveryError(itsView=self.view)

        deliveryError.errorDate   = datetime.now()
        deliveryError.errorCode   = result[0]
        deliveryError.errorString = result[1]

        self.mailMessage.deliveryExtension.deliveryErrors.append(deliveryError)
        self.mailMessage.deliveryExtension.sendFailed()

    def displayedRecoverableSSLErrorDialog(self, err, mailMessage=None):
        if __debug__:
            trace("displayedRecoverableSSLErrorDialog")

        if self.testing:
            reconnect = self.testAccountSettings
        else:
            reconnect = lambda: self.sendMail(mailMessage)

        if isinstance(err, Utility.CertificateVerificationError):
            assert err.args[1] == 'certificate verify failed'
            # Reason why verification failed is stored in err.args[0], see
            # codes at http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS

            # Post an asynchronous event to the main thread where
            # we ask the user if they would like to trust this
            # certificate. The main thread will then initiate a retry
            # when the new certificate has been added.
            if err.args[0] in ssl.unknown_issuer:
                displaySSLCertDialog(err.untrustedCertificates[0],
                                           reconnect)
            else:
                displayIgnoreSSLErrorDialog(err.untrustedCertificates[0],
                                                  err.args[0],
                                                  reconnect)

            return True
        elif str(err.__class__) == errors.M2CRYPTO_CHECKER_ERROR:
            displayIgnoreSSLErrorDialog(err.pem,
                                        messages.SSL_HOST_MISMATCH % {'expectedHost': err.expectedHost, 'actualHost': err.actualHost},
                                        reconnect)

            return True
        return False


    def _getError(self, err):
        errorCode = errors.UNKNOWN_CODE
        errorType   = str(err.__class__)

        if errorType == errors.SMTP_EXCEPTION:
            #SMTPExceptions inherits from ChandlerException
            #which contains translated unicode error messages
            errorString = err.__unicode__()
            errorCode = errors.SMTP_EXCEPTION_CODE
        else:
            errorString = unicode(err.__str__())

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

        elif isinstance(err, error.ConnectError):
            """ Record the error code of a ConnectionError.
                If a ConnectionError occurs then there was
                a problem communicating with an SMTP server
                and no error code will be returned by the
                server."""

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

        elif errorType.startswith(errors.M2CRYPTO_PREFIX):
            errorCode = errors.M2CRYPTO_CODE

            if errorType == errors.M2CRYPTO_BIO_ERROR:
                #XXX: pleace holder for future code enhancement
                pass

            if errorType == errors.M2CRYPTO_CHECKER_ERROR:
                """Host does not match cert"""
                #XXX: pleace holder for future code enhancement
                pass


        return (errorCode, errorString)


    def _fatalError(self, st):
        """If a fatal error occurred before sending the message i.e. no To Address
           then record the error, log it, and commit the mailMessage containing the
           error info"""
        if __debug__:
            trace("_fatalError")

        e = errors.SMTPException(st)
        self._recordError(e)

        if __debug__:
            for deliveryError in self.mailMessage.deliveryExtension.deliveryErrors:
                trace("Unable to send: %s" % deliveryError)

        return self._commit()

    def _getSender(self):
        """Get the sender of the message"""
        if self.mailMessage.replyToAddress is not None:
            return self.mailMessage.replyToAddress

        elif self.mailMessage.fromAddress is not None:
            return self.mailMessage.fromAddress

        return None

    def _getRcptTo(self):
        """Get all the recipients of this message (to, cc, bcc)"""
        to_addrs = []

        for address in self.mailMessage.toAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.ccAddress:
            to_addrs.append(address.emailAddress)

        for address in self.mailMessage.bccAddress:
            to_addrs.append(address.emailAddress)

        return to_addrs

    def _mailMessageHasErrors(self, sender):
        """Make sure that the Mail Message has a sender"""
        if sender is None:
            self._fatalError(constants.UPLOAD_FROM_REQUIRED)
            return True

        """Make sure the sender's Email Address is valid"""
        if not Mail.EmailAddress.isValidEmailAddress(sender.emailAddress):
            self._fatalError(constants.INVALID_EMAIL_ADDRESS % \
                              {'emailAddress': Mail.EmailAddress.format(sender)})
            return True

        """Make sure there is at least one Email Address to send the message to"""
        if len(self.mailMessage.toAddress) == 0:
            self._fatalError(constants.UPLOAD_TO_REQUIRED)
            return True

        errs = []
        errStr = constants.INVALID_EMAIL_ADDRESS

        """Make sure that each Recipients Email Address is valid"""
        for toAddress in self.mailMessage.toAddress:
            if not Mail.EmailAddress.isValidEmailAddress(toAddress.emailAddress):
                errs.append(errStr % {'emailAddress': Mail.EmailAddress.format(toAddress)})

        for ccAddress in self.mailMessage.ccAddress:
            if not Mail.EmailAddress.isValidEmailAddress(ccAddress.emailAddress):
                errs.append(errStr % {'emailAddress': Mail.EmailAddress.format(ccAddress)})

        for bccAddress in self.mailMessage.bccAddress:
            if not Mail.EmailAddress.isValidEmailAddress(bccAddress.emailAddress):
                errs.append(errStr % {'emailAddress': Mail.EmailAddress.format(bccAddress)})

        if len(errs) > 0:
            self._fatalError(u"\n".join(errs))
            return True

        return False

    def _getAccount(self):
        """Returns instances of C{SMTPAccount} based on C{UUID}'s"""

        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)
            assert self.account is not None, "No Account for UUID: %s" % self.accountUUID


    def _getMailMessage(self, mailMessageUUID):
        m = self.view.findUUID(mailMessageUUID)

        assert m is not None, "No MailMessage for UUID: %s" % mailMessageUUID
        return Mail.MailStamp(m)
