__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.defer as defer
import twisted.mail.imap4 as imap4

#python imports
import email as email

#Chandler imports
import osaf.contentmodel.mail.Mail as Mail
import crypto.ssl as ssl

#Chandler Mail Service imports
import message as message
import errors as errors
import constants as constants
import utils as utils
import base as base

"""
    TODO:
    2. Keep \\Deleted flags in sync with IMAP Server (Look at best syntax for this)

    TO DO: 
    1. Look in to pluging the Python email 3.0 Feedparser in to the
       rawDataReceived method of IMAP4Client for better performance.
       Or Twisted Feedparser

    4. Look at Spambayes for its message parsing python alogrithm,
       Quotient mail parser 

NOTES:
1. Will need to just get the basic headers of subject, message id, message size
   to, from, cc. Then have a callback to sync the rest
   when downloading an individual mail use the feedparser for performance

3. Fix the getEmailAddress method to be much more performant in content model
4. Start thinking about offline mode. Does the content model need any changes.
"""

class _TwistedIMAP4Client(imap4.IMAP4Client):
    """Overides C{imap4.IMAP4Client} to add
       Chandler specific functionality including startTLS management
       and Timeout management"""

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.
        It assigns itself as the protocol for its delegate.

        If caps is None does an explicit request to the
        IMAP server for its capabilities.

        Entry point for STARTTLS logic. Will call delegate.loginClient
        or delegate.catchErrors if an error occurs.

        @param caps: The list of server CAPABILITIES or None
        @type caps: C{dict} or C{None}
        @return C{defer.Deferred}
        """

        self.delegate.proto = self

        if caps is None:
            """If no capabilities returned in server greeting then get
               the server capabilities """
            d = self.getCapabilities()

            d.addCallbacks(self.__getCapabilities, self.delegate.catchErrors)

            return d

        self.__getCapabilities(caps)

    def __getCapabilities(self, caps):
        if self.factory.useTLS:
            """The Twisted IMAP4Client will check to make sure the server can STARTTLS
               and raise an error if it can not"""
            d = self.startTLS(self.factory.sslContext)

            d.addCallbacks(lambda _: self.delegate.loginClient(), \
                                     self.delegate.catchErrors)
            return d

        if 'LOGINDISABLED' in caps:
            e = errors.IMAPException(constants.DOWNLOAD_REQUIRES_TLS)
            self.delegate.catchErrors(e)

        else:
            """Remove the STARTTLS from capabilities"""
            self._capCache = utils.disableTwistedTLS(caps)
            self.delegate.loginClient()

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           The method generates an C{IMAPException} and
           forward to delegate.catchErrors
        """
        exc = errors.IMAPException(errors.STR_TIMEOUT_ERROR)
        """We have timed out so do not send any more commands to
           the server just disconnect """
        self.factory.timedOut = True
        self.delegate.catchErrors(exc)


class IMAPClientFactory(base.AbstractDownloadClientFactory):
    """Inherits from C{base.AbstractDownloadClientFactory}
       and overides default protocol and exception values
       with IMAP specific values"""

    protocol  = _TwistedIMAP4Client
    """The exception to raise when an error occurs"""
    exception = errors.IMAPException


class IMAPClient(base.AbstractDownloadClient):
    """Provides support for Downloading mail from an
       IMAP mail 'Inbox' as well as test Account settings.
       This functionality will be enhanced to be a more
       robust IMAP client in the near future"""

    """Overides default values in base class to provide
       IMAP specific functionality"""
    accounType  = Mail.IMAPAccount
    clientType  = "IMAPClient"
    factoryType = IMAPClientFactory
    defaultPort = 143

    def _loginClient(self):
        """Logs a client in to an IMAP servier using the CramMD6, Login, or
           Plain authentication"""

        if __debug__:
            self.printCurrentView("_loginClient")

        assert self.account is not None

        """Twisted expects ascii values so encode the utf-8 username and password"""
        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)

        self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
        self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))

        return self.proto.authenticate(password
                     ).addCallback(self.__selectInbox
                     ).addErrback(self.loginClientInsecure, username, password)


    def loginClientInsecure(self, error, username, password):
        """If the IMAP4 Server does not support MD5 or Login authentication
           will attempt to login in via plain text login.
           This method is called as a result of a failure to login
           via an authentication mechanism. If the error.value
           is not of C{imap4.NoSupportAuthentication} then
           there was actually an error such as incorrect username
           or password. In this case the method forward the error to
           self.catchErrors.

           @param error: A Twisted Failure
           @type error: C{failure.Failure}

           @param username: The username to log in with
           @type username: C{str}

           @param password: The password to log in with
           @type passord: C{str}
        """

        if __debug__:
            self.printCurrentView("loginClientInsecure")

        """There was an error during login"""
        if not isinstance(error.value, imap4.NoSupportedAuthentication):
            self.catchErrors(error)
            return

        return self.proto.login(username, password
                          ).addCallbacks(self.__selectInbox, self.catchErrors)


    def __selectInbox(self, result):
        if __debug__:
            self.printCurrentView("__selectInbox")

        if self.testing:
            utils.alert(constants.TEST_SUCCESS, self.account.displayName)
            self._actionCompleted()
            return

        utils.NotifyUIAsync(constants.DOWNLOAD_CHECK_MESSAGES)

        d = self.proto.select("INBOX")
        d.addCallbacks(self.__checkForNewMessages, self.catchErrors)
        return d

    def __checkForNewMessages(self, msgs):
        if __debug__:
            self.printCurrentView("checkForNewMessages")

            #XXX: Need to store and compare UIDVALIDITY
        #if not msgs['UIDVALIDITY']:
        #    print "server: %s has no UUID Validity:\n%s" % (self.account.host, msgs)

        if msgs['EXISTS'] == 0:
            utils.NotifyUIAsync(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        if self.__getNextUID() == 0:
            msgSet = imap4.MessageSet(1, None)
        else:
            msgSet = imap4.MessageSet(self.__getNextUID(), None)

        d = self.proto.fetchFlags(msgSet, uid=True)

        d.addCallback(self.__getMessagesFlagsUID).addErrback(self.catchErrors)

        return d

    def __getMessagesFlagsUID(self, msgs):
        if __debug__:
            self.printCurrentView("__getMessagesFlagsUIDS")

        nextUID = self.__getNextUID()

        for message in msgs.itervalues():
            luid = long(message['UID'])

            if luid < nextUID:
                continue

            if luid > self.lastUID:
                self.lastUID = luid

            if not "\\Deleted" in message['FLAGS']:
                self.pending.append([luid, message['FLAGS']])

        if len(self.pending) == 0:
            utils.NotifyUIAsync(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        self.execInView(self._getNextMessageSet)

    def _getNextMessageSet(self):
        """Overides base class to add IMAP specific logic.
           If the pending queue has one or messages to download
           for n messages up to C{IMAPAccount.downloadMax} fetches
           the mail from the IMAP server. If no message pending
           calls actionCompleted() to clean up client resources.
        """
        if __debug__:
            self.printCurrentView("_getNextMessageSet")

        self.numToDownload = len(self.pending)

        if self.numToDownload == 0:
            return self._actionCompleted()

        if self.numToDownload > self.downloadMax:
            self.numToDownload =self.downloadMax 

        m = self.pending.pop(0)
        d = self.proto.fetchMessage(str(m[0]), uid=True)
        d.addCallback(self.execInViewDeferred, self.__fetchMessage, m)
        d.addErrback(self.catchErrors)


    def __fetchMessage(self, msgs, curMessage):
        if __debug__:
            self.printCurrentView("fetchMessage")

        msg = msgs.keys()[0]

        messageText = msgs[msg]['RFC822']

        #XXX: Need a more perforrmant way to do this
        messageObject = email.message_from_string(messageText)

        repMessage = message.messageObjectToKind(self.view,
                                                 messageObject, messageText)

        """Set the message as incoming"""
        repMessage.incomingMessage(self.account)

        """Save IMAP Delivery info in Repository"""
        repMessage.deliveryExtension.folder = "INBOX"
        repMessage.deliveryExtension.uid = curMessage[0]
        repMessage.deliveryExtension.flags = curMessage[1]

        self.numDownloaded += 1

        if self.numDownloaded == self.numToDownload:
            self.__setNextUID(self.lastUID + 1)
            self.totalDownloaded += self.numDownloaded
            self._commitDownloadedMail()

        else:
            m = self.pending.pop(0)
            d = self.proto.fetchMessage(str(m[0]), uid=True)
            d.addCallback(self.execInViewDeferred, self.__fetchMessage, m)
            d.addErrback(self.catchErrors)


    def __expunge(self, result):
        if __debug__:
            self.printCurrentView("_expunge")

        return self.proto.expunge()

    def __getNextUID(self):
        return self.account.messageDownloadSequence

    def __setNextUID(self, uid):
        self.account.messageDownloadSequence = uid

    def _beforeDisconnect(self):
        """Overides base class to send a IMAP 'LOGOUT' command
           before disconnecting from the IMAP server"""

        if __debug__:
            self.printCurrentView("_beforeDisconnect")

        if self.factory.connectionLost or self.factory.timedOut:
            return defer.succeed(True)

        d = self.proto.sendCommand(imap4.Command('LOGOUT', wantResponse=('BYE',)))

        return d

    def _getAccount(self):
        """Retrieves a C{Mail.IMAPAccount} instance from its C{UUID}"""
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
