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
import twisted.internet.defer as defer
import twisted.mail.pop3client as pop3

#python imports
import email as email

#Chandler imports
import osaf.pim.mail as Mail
from osaf.framework.certstore import ssl

#Chandler Mail Service imports
import errors
import constants
import base
from utils import *
from message import *

__all__ = ['POPClient']

"""
1. Will need to just get the basic headers via a
   top, can also use a list [msg] to get the size.
   Then have a callback to sync the rest
   when downloading an individual mail use the feedparser for performance

   Make POP downloading IMAP like in approach
   XXX: Use a List, ***ref collection, or Item Collection to maintain Account refs

    Think about caching the capabilities of server when set (This could change though).
    What happens if no CAPA returned by the server?
    Should I test for top and uidl since these are extensions?
"""


class _TwistedPOP3Client(pop3.POP3Client):
    """Overides C{pop3.PO3Client} to add
       Chandler specific functionality including startTLS management
       and Timeout management"""

    allowInsecureLogin = True

    def serverGreeting(self, challenge):
        """
        This method overides C{pop3.POP3Client}.
        It assigns itself as the protocol for its delegate.

        Does an explicit request to the POP server for its capabilities.

        Entry point for STARTTLS logic. Will call delegate.loginClient
        or delegate.catchErrors if an error occurs.


        @param challenge: The server challenge for APOP or None
        @type challenge: C{str} or C{None}
        @return C{defer.Deferred}
        """

        d = self.capabilities()
        d.addCallbacks(self._getCapabilities, self.delegate.catchErrors)


    def _getCapabilities(self, caps):
        if self._timedOut:
            #If we have already timed out then gracefully exit the function
            return defer.succeed(True)

        if self.factory.useTLS:
            # The Twisted POP3Client will check to make sure the server can STARTTLS
            # and raise an error if it can not
            d = self.startTLS(self.transport.contextFactory.getContext())
            d.addCallbacks(lambda _: self.delegate.loginClient(), self.delegate.catchErrors)
            return d

        else:
            # Remove the STLS from capabilities
            self._capCache = disableTwistedTLS(caps, "STLS")
            self.delegate.loginClient()

    def connectionLost(self, reason):
        if __debug__:
            trace("connectionLost")

        if self.timeout > 0:
            self.setTimeout(None)

        if self._timedOut:
            #The errback was already fired in the timeoutConnection method.
            return

        #This will fire an errback on all deferred objects in the queue
        return pop3.POP3Client.connectionLost(self, reason)

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           The method generates an C{POPException} and
           forward to delegate.catchErrors
        """
        if __debug__:
            trace("timeoutConnection")

        self._timedOut = True
        self.factory.timedOut = True

        d = []
        error = errors.POPException(errors.STR_TIMEOUT_ERROR)

        if self._waiting is not None:
            d.append(self._waiting)
            self._waiting = None

        if self._blockedQueue is not None:
            d.extend([deferred for (deferred, f, a) in self._blockedQueue])
            self._blockedQueue = None

        for w in d:
            w.errback(error)

class POPClientFactory(base.AbstractDownloadClientFactory):
    """Inherits from C{base.AbstractDownloadClientFactory}
       and overides default protocol and exception values
       with POP specific values"""

    protocol  = _TwistedPOP3Client
    # The exception to raise when an error occurs
    exception = errors.POPException


class POPClient(base.AbstractDownloadClient):
    """Provides support for Downloading mail from an
       POP3 Server as well as test Account settings.
    """

    # Overides default values in base class to provide
    # POP specific functionality
    accounType  = Mail.POPAccount
    clientType  = "POPClient"
    factoryType = POPClientFactory
    defaultPort = 110

    def _loginClient(self):
        """Logs a client in to an POP servier using APOP (if available or plain text
           login"""

        if __debug__:
            trace("_loginClient")

        if self.cancel:
            return self._actionCompleted()

        assert self.account is not None

        # Twisted expects 8-bit values so encode the utf-8 username and password
        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)


        d = self.proto.login(username, password)
        #XXX: Can handle the failed login case here and prompt user to re-enter username 
        #     and password
        d.addCallbacks(self._statServer, self.catchErrors)
        return d


    def _statServer(self, result):
        if __debug__:
            trace("_statServer")

        if self.cancel:
            return self._actionCompleted()

        if self.testing:
            callMethodInUIThread(self.callback, (1, None))
            return self._actionCompleted()

        setStatusMessage(constants.DOWNLOAD_CHECK_MESSAGES)

        d = self.proto.stat()
        d.addCallbacks(self._serverHasMessages, self.catchErrors)


    def _serverHasMessages(self, stat):
        if __debug__:
            trace("_serverHasMessages")

        if self.cancel:
            return self._actionCompleted()

        if stat[0] == 0:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        d = self.proto.listUID()
        d.addCallbacks(self._checkForNewMessages, self.catchErrors)


    def _checkForNewMessages(self, uidList):
        if __debug__:
            trace("_checkForNewMessages")

        if self.cancel:
            return self._actionCompleted()

        total = len(uidList)

        for i in xrange(total):
            uid = uidList[i]

            if not uid in self.account.downloadedMessageUIDS:
                self.pending.append((i, uid))

        if len(self.pending) == 0:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES)
            return self._actionCompleted()

        self._getNextMessageSet()

    def _getNextMessageSet(self):
        """Overides base class to add POP specific logic.
           If the pending queue has one or messages to download
           for n messages up to C{POPAccount.downladMax} fetches
           the mail from the POP server. If no message pending
           calls actionCompleted() to clean up client resources.
        """
        if __debug__:
            trace("_getNextMessageSet")

        if self.cancel:
            return self._actionCompleted()

        self.numToDownload = len(self.pending)

        if self.numToDownload == 0:
            return self._actionCompleted()

        if self.numToDownload > self.downloadMax:
            self.numToDownload = self.downloadMax

        msgNum, uid = self.pending.pop(0)

        d = self.proto.retrieve(msgNum)
        d.addCallback(self._retrieveMessage, msgNum, uid)
        d.addErrback(self.catchErrors)

    def _retrieveMessage(self, msg, msgNum, uid):
        if __debug__:
            trace("_retrieveMessage")

        if self.cancel:
            try:
                #We call cancel() here since there may be
                #in memory mail message items which we want to
                #deallocate from the current view.
                self.view.cancel()
            except:
                pass

            return self._actionCompleted()


        messageText = "\n".join(msg)

        #XXX: Need a more performant way to do this
        messageObject = email.message_from_string(messageText)

        repMessage = messageObjectToKind(self.view, messageObject, messageText)

        # Set the message as incoming
        repMessage.incomingMessage(self.account, "POP")

        repMessage.deliveryExtension.uid = uid
        #XXX: This is temporary will need a better way
        #XXX: Could use an item collection with an index
        self.account.downloadedMessageUIDS[uid] = "True"

        self.numDownloaded += 1
        self.pruneCounter  += 1

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
            d.addCallback(self._retrieveMessage, msgNum, uid)

            return d

    def _beforeDisconnect(self):
        """Overides base class to send a POP 'QUIT' command
           before disconnecting from the POP server"""
        if __debug__:
            trace("_beforeDisconnect")

        if self.factory.connectionLost or self.factory.timedOut:
            return defer.succeed(True)

        return self.proto.quit()

    def _getAccount(self):
        """Retrieves a C{Mail.POPAccount} instance from its C{UUID}"""
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
