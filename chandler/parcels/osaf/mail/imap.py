__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.error as error
import twisted.mail.imap4 as imap4

#python / mx imports
import email as email
import logging as logging

#Chandler imports
import repository.item.Query as Query
import osaf.contentmodel.mail.Mail as Mail
import application.Globals as Globals
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL as SSL

#Chandler Mail Service imports
import message as message
import errors as errors
import constants as constants
import utils as utils
import base as base

"""
    TODO:
    1. Print warning message if UID validity is bad (Where to store UID Validity 
       since on folder)
    2. Keep \\Deleted flags in sync with IMAP Server (Look at best syntax for this)

    TO DO: 
    1. Look in to pluging the Python email 3.0 Feedparser in to the
       rawDataReceived method of IMAP4Client for better performance.
       Or Twisted Feedparser

    4. Look at Spambayes for its message parsing python alogrithm,
       Quotient mail parser 
    5. Hotshot and timeit

NOTES:
1. Will need to just get the basic headers of subject, message id, message size
   to, from, cc. Then have a callback to sync the rest
   when downloading an individual mail use the feedparser for performance

2. LOOK AT THE RFC IS UUID ALWAYS A LONG
3. Fix the getEmailAddress method to be much more performant in content model
"""

class _TwistedIMAP4Client(imap4.IMAP4Client):
    timeout  = constants.TIMEOUT

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.

        It calls back the factory registered deferred passing a reference to self(protocol) and
        a reference to the Server capbilities

        @param caps: The list of server CAPABILITIES
        @type caps: dict
        @return C{None}
        """

        self.delegate.proto = self

        if caps is None:
            """If no capabilities returned in server greeting then get
               the server capabilities """
            d = self.getCapabilities()

            d.addCallbacks(self.__getCapabilities.delegate.catchErrors)

            return d

        self.__getCapabilities(caps)

    def __getCapabilities(self, caps):

        if self.factory.useTLS:
            """The Twisted IMAP4Client will check to make sure the server can STARTTLS
               and raise an error if it can not"""
            d = self.startTLS(Globals.crypto.getSSLContext())
            d.addCallbacks(lambda _: self.delegate.loginClient(), self.delegate.catchErrors)
            return d

        if 'LOGINDISABLED' in caps:
            self.delegate.catchErrors(errors.IMAPException(constants.DOWNLOAD_REQUIRES_TLS))

        else:
            """Remove the STARTTLS from capabilities"""
            self._capCache = utils.disableTwistedTLS(caps)
            self.delegate.loginClient()

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           If the connection is not Done the method will
           generate an C{IMAPException} and forward to delegate
           errback
        """
        exc = errors.IMAPException(errors.STR_TIMEOUT_ERROR)
        self.delegate.catchErrors(exc)


class IMAPClientFactory(base.AbstractDownloadClientFactory):
    protocol  = _TwistedIMAP4Client
    exception = errors.IMAPException


class IMAPClient(base.AbstractDownloadClient):
    accounType  = Mail.IMAPAccount
    clientType  = "IMAPClient"
    factoryType = IMAPClientFactory
    defaultPort = 143

    def _loginClient(self):
        if __debug__:
            self.printCurrentView("_loginClient")

        assert self.account is not None

        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)

        self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
        self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))

        return self.proto.authenticate(password
                     ).addCallback(self.__selectInbox
                     ).addErrback(self.loginClientInsecure, username, password)


    def loginClientInsecure(self, error, username, password):
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

        #XXX: Store and compare msgs['UIDVALIDITY']

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

        """Reorder highest to lowest UID for popping"""
        self.pending.reverse()
        self.execInView(self._getNextMessageSet)

    def _getNextMessageSet(self):
        if __debug__:
            self.printCurrentView("_getNextMessageSet")

        self.numToDownload = len(self.pending)

        if self.numToDownload == 0:
            return self._actionCompleted()

        if self.numToDownload > constants.DOWNLOAD_MAX:
            self.numToDownload = constants.DOWNLOAD_MAX

        m = self.pending.pop()
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
            m = self.pending.pop()
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
        if __debug__:
            self.printCurrentView("_beforeDisconnect")

        if self.factory.connectionLost:
            return defer.succeed(True)

        d = self.proto.sendCommand(imap4.Command('LOGOUT', wantResponse=('BYE',)))

        return d

    def _getAccount(self):
        if self.account is None:
            self.account = Mail.MailParcel.getIMAPAccount(self.view,
                                                          self.accountUUID)

        return self.account
