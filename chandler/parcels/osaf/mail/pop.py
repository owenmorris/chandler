__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.mail.pop3client as pop3

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
1. Will need to just get the basic headers via a 
   top, can also use a list [msg] to get the size.
   Then have a callback to sync the rest
   when downloading an individual mail use the feedparser for performance
"""


class _TwistedPOP3Client(pop3.POP3Client):
    timeout  = constants.TIMEOUT
    allowInsecureLogin = True

    def serverGreeting(self, challenge):

        self.delegate.proto = self

        d = self.capabilities()
        d.addCallbacks(self.__getCapabilities, self.delegate.catchErrors)
        return d


    def __getCapabilities(self, caps):
        if self.factory.useTLS:
            """The Twisted POP3Client will check to make sure the server can STARTTLS
               and raise an error if it can not"""
            d = self.startTLS(Globals.crypto.getSSLContext(protocol='sslv3'))
            d.addCallbacks(lambda _: self.delegate.loginClient(), self.delegate.catchErrors)
            return d

        else:
            """Remove the STLS from capabilities"""
            self._capCache = utils.disableTwistedTLS(caps, "STLS")
            self.delegate.loginClient()


class POPClientFactory(base.AbstractDownloadClientFactory):
    protocol  = _TwistedPOP3Client
    exception = errors.POPException


class POPClient(base.AbstractDownloadClient):
    accounType  = Mail.POPAccount
    clientType  = "POPClient"
    factoryType = POPClientFactory
    defaultPort = 110

    def _loginClient(self):
        if __debug__:
            self.printCurrentView("_loginClient")

        assert self.account is not None

        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)


        d = self.proto.login(username, password)
        #XXX: Can handle the failed login case here
        d.addCallbacks(self.__statServer, self.catchErrors)
        return d


    def __statServer(self, result):
        if __debug__:
            self.printCurrentView("__statServer")

        if self.testing:
            utils.alert(constants.TEST_SUCCESS, self.account.displayName)
            return self._actionCompleted()

        utils.NotifyUIAsync(constants.DOWNLOAD_CHECK_MESSAGES)

        d = self.proto.stat()
        d.addCallbacks(self.__serverHasMessages, self.catchErrors)


    def __serverHasMessages(self, stat):
        if __debug__:
            self.printCurrentView("_hasMessages")

        if stat[0] == 0:
            utils.NotifyUIAsync(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        d = self.proto.listUID()
        d.addCallbacks(self.__checkForNewMessages, self.catchErrors)


    def __checkForNewMessages(self, uidList):
        if __debug__:
            self.printCurrentView("__checkForNewMessages")

        total = len(uidList)

        for i in range(total):
            uid = uidList[i]

            if not uid in self.account.downloadedMessageUIDS:
                self.pending.append((i, uid))

        if len(self.pending) == 0:
            utils.NotifyUIAsync(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        self.execInView(self._getNextMessageSet)

    def _getNextMessageSet(self):
        if __debug__:
            self.printCurrentView("_getNextMessageSet")

        self.numToDownload = len(self.pending)

        if self.numToDownload == 0:
            return self._actionCompleted()

        if self.numToDownload > constants.DOWNLOAD_MAX:
            self.numToDownload = constants.DOWNLOAD_MAX

        msgNum, uid = self.pending.pop(0)

        d = self.proto.retrieve(msgNum)
        d.addCallback(self.execInViewDeferred, self.__retrieveMessage, msgNum, uid)
        d.addErrback(self.catchErrors)

    def __retrieveMessage(self, msg, msgNum, uid):
        if __debug__:
            self.printCurrentView("retrieveMessage")

        messageText = "\n".join(msg)

        #XXX: Need a more perforrmant way to do this
        messageObject = email.message_from_string(messageText)

        repMessage = message.messageObjectToKind(self.view,
                                                 messageObject, messageText)

        """Set the message as incoming"""
        repMessage.incomingMessage(self.account, "POP")

        repMessage.deliveryExtension.uid = uid
        #XXX: This is temporary will need a better way
        self.account.downloadedMessageUIDS[uid] = "True"

        self.numDownloaded += 1

        if not self.account.leaveOnServer:
            d = self.proto.delete(msgNum)

        else:
            d = defer.succeed(True)

        d.addErrback(self.catchErrors)

        if self.numDownloaded == self.numToDownload:
            self.totalDownloaded += self.numDownloaded
            d.addCallback(lambda _: self._commitDownloadedMail())

        else:
            msgNum, uid = self.pending.pop(0)

            d.addCallback(lambda _: self.proto.retrieve(msgNum))
            d.addCallback(self.execInViewDeferred, self.__retrieveMessage, msgNum, uid)

        return d

    def _beforeDisconnect(self):
        if __debug__:
            self.printCurrentView("_beforeDisconnect")

        if self.factory.connectionLost:
            return defer.succeed(True)

        return self.proto.quit()

    def _getAccount(self):
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
