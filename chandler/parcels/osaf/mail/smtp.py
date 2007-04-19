#   Copyright (c) 2005-2007 Open Source Applications Foundation
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
from twisted.internet import threads

#python imports
import cStringIO as StringIO

#PyICU imports

#Chandler imports
from application import Globals, Utility
from osaf.pim.mail import SMTPAccount, MailStamp
from osaf.pim import Modification
from osaf.framework.certstore import ssl
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryError \
    import RepositoryError, VersionConflictError

from osaf.sharing import hasConflicts, SharedItem

#Chandler Mail Service imports
import constants
import errors
from utils import *
from message import kindToMessageText


__all__ = ['SMTPClient']

SMTP_SUCCESS = 250

class _TwistedESMTPSender(smtp.ESMTPSender):

    # Turn off Twisted SMTPClient logging
    debug = False

    def connectionMade(self):
        #twisted.internet.address.IPv4Address Object
        ipAddr = self.transport.getHost()

        if ipAddr:
            # Get the IPv4 address and use instead
            # of the DNS name for EHLO / HELO
            # commands.
            # This is a workaround for SMTP servers
            # that require fully qualified domains.
            # Windows and Linux clients do not
            # provide fully qualified domains by
            # default which means with out this
            # feature users would manually have
            # to set his or her domain settings.

            self.identity = "[%s]" % ipAddr.host

        return smtp.ESMTPSender.connectionMade(self)

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
            # We want to use the M2Crypto SSL context so assign it here
            self.context = self.transport.contextFactory.getContext()

        return smtp.ESMTPSender.tryTLS(self, code, resp, items)

    def smtpState_from(self, code, resp):
        """Overides C{smtp.ESMTPSender} to disconnects from the
           SMTP server before sending the 'MAIL FROM:' command
           to the server when in account testing mode
        """

        if self.factory.testing:
            # If in testing mode, Overload the Twisted SMTPClient
            #   to instead of sending an 'MAIL FROM:' request,
            #   send a 'QUIT' request and disconnect from the Server.
            #   This is followed by a call to sentMail which is a Twisted
            #   method indicating the mail was sent successfully
            #   method

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
           @type account: C{SMTPAccount}
        """
        assert isinstance(account, SMTPAccount)
        assert isinstance(view, RepositoryView)

        self.view = view

        self.accountUUID = account.itsUUID
        self.account = None

        #These values are reset per request
        self.testing = False
        self.callback = None
        self.reconnect = None
        self.cancel = False
        self.displayed = False

        self.mailMessage = None
        self.shuttingDown = False

    def sendMail(self, mailMessage):
        """
           Sends a mail message via SMTP using the C{SMTPAccount}
           passed to this classes __init__ method

           @param mailMessage: A MailMessage domain model object
           @type mailMessage: C{MailStamp}

           @return: C{None}
        """
        assert isinstance(mailMessage, MailStamp)

        if __debug__:
            trace("sendMail")

        mailItem = mailMessage.itsItem
        self.reconnect = lambda: self.sendMail(mailMessage)

        reactor.callFromThread(self._prepareForSend, mailItem.itsUUID)

    def testAccountSettings(self, callback, reconnect):
        """Tests the user entered settings for C{SMTPAccount}"""

        if __debug__:
            trace("testAccountSettings")

        if not Globals.mailService.isOnline():
            return self._resetClient()

        assert(callback is not None)
        assert(reconnect is not None)

        # The method to call in the UI Thread
        # when the testing is complete.
        # This method is called for both success and failure.
        self.callback = callback

        # Tell what method to call on reconnect
        # when a SSL dialog is displayed.
        # When the dialog is shown the
        # protocol code terminates the
        # connection and calls reconnect
        # if the cert has been accepted
        self.reconnect = reconnect

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
        d.addCallbacks(lambda _: self._actionCompleted())
        return d

    def _actionCompleted(self):
        if __debug__:
            trace("_actionCompleted")

        if not self.displayed and not self.shuttingDown and \
           Globals.mailService.isOnline() and not self.cancel:
            if self.mailMessage.itsItem.error:
                 key = "displaySMTPSendError"
            else:
                 key = "displaySMTPSendSuccess"

            NotifyUIAsync(self.mailMessage, None, key, self.account)

            #see if there are any messages in the queue to send
            self._processQueue()

        self._resetClient()


    def _resetClient(self):
        self.mailMessage = None
        self.displayed  = False
        self.cancel = False
        self.callback = None
        self.testing = False

    def _prepareForSend(self, mailMessageUUID):
        """Sends a mail message via SMTP using the account and mailMessage
           passed to this classes __init__ method using the Twisted Asych Reactor"""

        if __debug__:
            trace("_prepareForSend")

        if self.cancel:
            return self._resetClient()

        # Refresh our view before retrieving Account info
        self.view.refresh()

        self._getAccount()

        # If currently sending a message put the next request in the Queue.
        try:
            # Just in case a cancel was requested after the above cancel check
            # return here instead of seeing if the message should go in the queue
            if self.cancel:
                return self._resetClient()

            if self.mailMessage is not None or not Globals.mailService.isOnline():
                newMessage = self._getMailMessage(mailMessageUUID)

                if hasConflicts(newMessage.itsItem):
                    # If the new message has a conflict display
                    # a warning to the user and do not
                    # add the message to the queue
                    return alertConflictError(newMessage, self.account)

                try:
                    sending = (self.mailMessage.itsItem is newMessage.itsItem)
                except:
                    sending = False

                inQueue = False

                # Check that the mailMessage in not already Queued
                for item in self.account.messageQueue:
                    if item is newMessage.itsItem:
                        if __debug__:
                            trace("SMTPClient Queue already contains message: %s" % mailMessageUUID)
                        inQueue = True

                #Sending should always be False in offline mode
                if not inQueue and sending:
                    # Check that the mailMessage in not currently being sent
                    if __debug__:
                        trace("SMTPClient currently sending message: %s" % mailMessageUUID)

                elif not inQueue:
                    self.account.messageQueue.insert(0, newMessage.itsItem)

                    # Update the item state
                    newMessage.itsItem.changeEditState(Modification.queued,
                                                       who=newMessage.getSender())
                    self.view.commit()

                    if __debug__:
                        trace("SMTPClient adding to the Queue message: %s" % mailMessageUUID)

                if not Globals.mailService.isOnline():
                    setStatusMessage(constants.UPLOAD_OFFLINE % \
                                    {'accountName': self.account.displayName,
                                     'subject': newMessage.subject})

                return

            self.mailMessage = self._getMailMessage(mailMessageUUID)

            if hasConflicts(self.mailMessage.itsItem):
               # If the mail message has a conflict it
               # will not be sent
                return alertConflictError(self.mailMessage, self.account)

            setStatusMessage(constants.UPLOAD_START % \
                             {'accountName': self.account.displayName,
                              'subject': self.mailMessage.subject})

            # handles all MailStamp level logic  to support general sending
            # of mail as well as edit / update workflows
            self.mailMessage.outgoingMessage()

            sender = self.mailMessage.getSender()

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

        if self.cancel or self.shuttingDown:
            return self._resetClient()

        # Refresh our view before retrieving Account info
        self.view.refresh()

        # Get the account, get the mail message and hand off to an instance to send
        # if someone already sending them put in a queue
        self._getAccount()

        self.testing = True

        d = defer.Deferred()

        d.addCallback(self._testSuccess)
        d.addErrback(self._testFailure)

        self._sendingMail("", [], "", d, True)


    def _sendingMail(self, from_addr, to_addrs, messageText, deferred, testing=False):
        if __debug__:
            trace("_sendingMail")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        username         = None
        authRequired     = False
        securityRequired = False
        heloFallback     = True

        if self.account.useAuth:
            username         = self.account.username
            deferredPassword = self.account.password.decryptPassword()
            authRequired     = True
            heloFallback     = False
        else:
            deferredPassword = defer.Deferred()
            deferredPassword.callback(None)

        if testing:
            retries = 0
            timeout = constants.TESTING_TIMEOUT
        else:
            retries = self.account.numRetries
            timeout = self.account.timeout

        if self.account.connectionSecurity == 'TLS':
            securityRequired = True

        msg = StringIO.StringIO(messageText)

        def callback(password):
            # Note that we cheat with the context factory here (value=1),
            # because ssl.connectSSL does it automatically, and in the
            # case of STARTTLS we override esmtpState_starttls above
            # to supply the correct SSL context.
            factory = smtp.ESMTPSenderFactory(username, password, from_addr,
                                              to_addrs, msg,
                                              deferred, retries, timeout,
                                              1, heloFallback, authRequired,
                                              securityRequired)

            factory.protocol = _TwistedESMTPSender
            factory.testing  = testing

            if self.account.connectionSecurity == 'SSL':
                ssl.connectSSL(self.account.host, self.account.port, factory,
                               self.view)
            else:
                ssl.connectTCP(self.account.host, self.account.port, factory,
                               self.view)

        deferredPassword.addCallback(callback)

    def _testSuccess(self, result):
        if __debug__:
            trace("_testSuccess")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        callMethodInUIThread(self.callback, (1, None))
        self._resetClient()


    def _testFailure(self, exc):
        if __debug__:
            trace("_testFailure")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        exc = exc.value

        if self.displayedRecoverableSSLErrorDialog(exc, dryRun=True):
            # Send the message to destroy the progress dialog first. This needs
            # to be done in this order on Linux because otherwise killing
            # the progress dialog will also kill the SSL error dialog.
            # Weird, huh? Welcome to the world of wx...
            callMethodInUIThread(self.callback, (2, None))

        if not self.displayedRecoverableSSLErrorDialog(exc):
            # Just get the error string do not need the error code
            err = self._getError(exc)[1]
            callMethodInUIThread(self.callback, (0, err))

        self._resetClient()

    def _mailSuccessCheck(self, result):
        """Twisted smtp.py will call the deferred callback (this method) if
           one or more recipients are accepted by the mail server. However
           if at least one recipent is denied by the smtp server we need to
           treat the message as failed for .4B and possibly beyond"""

        if __debug__:
            trace("_mailSuccessCheck")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        # Refresh our view before adding items to our mail Message
        # and commit. Will not cause merge conflicts since
        # no data changed in view in yet
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
        self.mailMessage.itsItem.error = u""

    def _mailSomeFailed(self, result):
        """
            If one of more recipients were not send an SMTP message update mailMessage object.

            result: (NumOk, [(emailAddress, serverStatusCode, serverResponseString)])
            Collect all results that do not have a 250 and form a string for .4B
        """

        if __debug__:
            trace("_mailSomeFailed")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        try:
            #On error cancel any changes done in the view
            self.view.cancel()
        except:
            pass

        errors = []

        for recipient in result[1]:
            email, code, st = recipient

            if recipient[1] != SMTP_SUCCESS:
                errors.append( u"%s: %s" % (email, st))

        if errors:
            # Add the error strings to the items error attribute
            self.mailMessage.itsItem.error = u", ".join(errors)

    def _mailFailure(self, exc):
        if __debug__:
            trace("_mailFailure")

        if self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel:
            return self._resetClient()

        try:
            #On error cancel any changes done in the view
            self.view.cancel()
        except:
            pass

        exc = exc.value

        displayed = self.displayedRecoverableSSLErrorDialog(exc, self.mailMessage)

        if not displayed:
            # Only record errors if the add cert is not displayed.
            # The state of a add cert will remain draft until a
            # user actually adds a cert at which point the mail code
            # will be called again and the state will be updated

            self._recordError(exc)

            return self._commit()

        else:
            # Clear the status bar message
            self.displayed = True
            setStatusMessage(u"")

            # Reset the SMTPClient
            self._actionCompleted()

    def _recordError(self, err):
        result = self._getError(err)
        self.mailMessage.itsItem.error = result[1]


    def displayedRecoverableSSLErrorDialog(self, err, mailMessage=None,
                                           dryRun=False):
        if __debug__:
            trace("displayedRecoverableSSLErrorDialog")

        if not dryRun and (self.shuttingDown or not Globals.mailService.isOnline() or \
           self.cancel):
            return self._resetClient()

        if isinstance(err, Utility.CertificateVerificationError):
            assert err.args[1] == 'certificate verify failed'
            # Reason why verification failed is stored in err.args[0], see
            # codes at http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS

            # Post an asynchronous event to the main thread where
            # we ask the user if they would like to trust this
            # certificate. The main thread will then initiate a retry
            # when the new certificate has been added.
            try:
                if not dryRun:
                    if err.args[0] in ssl.unknown_issuer:
                        displaySSLCertDialog(err.untrustedCertificates[0],
                                                   self.reconnect)
                    else:
                        displayIgnoreSSLErrorDialog(err.untrustedCertificates[0],
                                                          err.args[0],
                                                          self.reconnect)
                return True
            except Exception, e:
                # There is a bug in the M2Crypto code that needs to be 
                # fixed
                log.exception('This should never happen')
                return False

        elif str(err.__class__) == errors.M2CRYPTO_CHECKER_ERROR:
            if not dryRun:
                displayIgnoreSSLErrorDialog(err.pem,
                                            messages.SSL_HOST_MISMATCH % \
                                            {'expectedHost': err.expectedHost, 
                                            'actualHost': err.actualHost},
                                             self.reconnect)
            return True

        return False

    def cancelLastRequest(self):
        if __debug__:
            trace("cancelLastRequest")

        # This feature is still experimental

        if self.mailMessage or self.testing:
            self.cancel = True

    def shutdown(self):
        if __debug__:
            trace("shutdown")

        self.shuttingDown = True

    def _getError(self, err):
        errorCode = errors.UNKNOWN_CODE
        errorType   = str(err.__class__)

        if isinstance(err, errors.SMTPException):
            #SMTPExceptions inherits from ChandlerException
            #which contains translated unicode error messages
            errorString = err.__unicode__()
            errorCode = errors.SMTP_EXCEPTION_CODE

        elif isinstance(err, smtp.SMTPClientError):
            # Base type for all SMTP Related Errors.
            # Capture all the errors that may return -1 as the
            # error code and record the actual error code. Those
            # SMTPClientError's that slip through will have the

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

        else:
            errorString = unicode(err.__str__())
            errorCode = errors.MISSING_VALUE_CODE

        if isinstance(err, error.ConnectError):
            # Record the error code of a ConnectionError.
            # If a ConnectionError occurs then there was
            # a problem communicating with an SMTP server
            # and no error code will be returned by the
            # server.

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
                # Host does not match cert
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

        return self._commit()

    def takeOnline(self):
        #Move to twisted thread
        reactor.callFromThread(self._takeOnline)

    def _takeOnline(self):
        self._getAccount()
        self._processQueue()

    def _processQueue(self):
        """If there are messages send the next one in the Queue
           and we have not displayed the Add Certificate Dialog"""

        size = len(self.account.messageQueue)

        if size:
            for i in xrange(0, size):
                item = self.account.messageQueue.pop()

                if item is not None and item.isLive():
                    mUUID = item.itsUUID

                    if __debug__:
                        trace("SMTPClient sending next message in Queue %s" % mUUID)

                    # Yield to Twisted Event Loop
                    reactor.callLater(0, self._prepareForSend, mUUID)
                    break

    def _getRcptTo(self):
        """Get all the recipients of this message (to, cc, bcc, originators)"""

        recipients = self.mailMessage.getRecipients()

        rcptTo = []

        for address in recipients:
            rcptTo.append(address.emailAddress)

        # This feature sends a Bcc copy of the message to
        # the sender
        #ea = self.mailMessage.getSender()
        #if ea and ea.emailAddress is not None:
        #    if ea.emailAddress not in to_addrs:
        #        to_addrs.append(ea.emailAddress)

        return rcptTo

    def _getAccount(self):
        """Returns instances of C{SMTPAccount} based on C{UUID}'s"""

        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)
            assert self.account is not None


    def _getMailMessage(self, mailMessageUUID):
        m = self.view.findUUID(mailMessageUUID)

        assert m is not None
        return MailStamp(m)

def alertConflictError(mailStamp, account):
    buf = []

    shared = SharedItem(mailStamp.itsItem)

    for conflict in shared.getConflicts():
        buf.append("%s: %s" % (conflict.field, conflict.value))

    txt = _(u"Unable to send '%(mailSubject)s' via '%(accountName)s'.\nThe following conflicts exist:\n%(conflicts)s") \
            % {'mailSubject': mailStamp.subject,
               'accountName': account.displayName,
               'conflicts': "\n".join(buf)}

    alert(txt)

