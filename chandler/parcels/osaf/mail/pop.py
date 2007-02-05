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
from osaf.pim.mail import POPAccount
from osaf.framework.certstore import ssl

#Chandler Mail Service imports
import errors
import constants
import base
from utils import *
from message import *

__all__ = ['POPClient']

"""
1. Remove the 'TOP' and 'UIDL' requirements
2. Add in AUTH LOGIN to twisted pop3client.py
"""

class POPVars(base.DownloadVars):
    def __init__(self):
        super(POPVars, self).__init__()
        self.headerCheckList = []
        self.addedUIDS = False

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

        # Check that the server supports both TOP and UIDL.
        # Although they are not required by the POP3 Spec
        # They are common in the majority of POP3 servers.
        # For Preview Chandler requires that the POP3 Server
        # support both the 'TOP' and 'UIDL' commands.

        if 'TOP' not in caps:
            txt = constants.POP_TOP_ERROR
            return self.delegate.catchErrors(errors.POPException(txt))

        if 'UIDL' not in caps:
            txt = constants.POP_UIDL_ERROR
            return self.delegate.catchErrors(errors.POPException(txt))

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
        error = errors.POPException(constants.MAIL_PROTOCOL_TIMEOUT_ERROR)

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
    accountType  = POPAccount
    clientType   = "POPClient"
    factoryType  = POPClientFactory
    defaultPort  = 110

    def __init__(self, view, account):
        super(POPClient, self).__init__(view, account)

    def _actionCompleted(self):
        super(POPClient, self)._actionCompleted()

    def _loginClient(self):
        """Logs a client in to an POP servier using APOP (if available or plain text
           login"""

        if __debug__:
            trace("_loginClient")

        if self.cancel:
            return self._actionCompleted()

        # Twisted expects 8-bit values so encode the utf-8 username and password
        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)


        d = self.proto.login(username, password)
        #XXX: Can handle the failed login case here
        #     and prompt user to re-enter username
        #     and password.
        d.addCallbacks(self.cb, self.catchErrors)
        return d

    def _getMail(self, result):
        if __debug__:
            trace("_getMail")

        if self.cancel:
            return self._actionCompleted()

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_CHECK_MESSAGES % \
                            {'accountName': self.account.displayName})


        self.vars = POPVars()

        d = self.proto.stat()
        d.addCallbacks(self._serverHasMessages, self.catchErrors)

        return d

    def _serverHasMessages(self, stat):
        if __debug__:
            trace("_serverHasMessages")

        if self.cancel:
            return self._actionCompleted()

        if stat[0] == 0:
            if self.statusMessages:
                setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            return self._actionCompleted()

        # Check that we have not already downloaded the max
        # number of messages for the account
        max = self.account.downloadMax
        downloaded = len(self.account.mailMessages)

        if max > 0 and max == downloaded:
            if __debug__:
                trace("Max number of messages %s reached. No new mail will be \
                       downloaded from '%s'" % (max, self.account.displayName.encode("utf-8")))

            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                         {'accountName': self.account.displayName})

            return self._actionCompleted()

        # For Preview UIDL is required
        d = self.proto.listUID()

        if self.account.actionType == "CHANDLER_HEADERS":
            d.addCallback(self._checkForNewChandlerMessages)
        else:
            d.addCallback(self._checkForNewMessages)
        d.addErrback(self.catchErrors)

        return d

    def _checkForNewChandlerMessages(self, uidList):
        if __debug__:
            trace("_checkForNewChandlerMessages")

        if self.cancel:
            return self._actionCompleted()

        total = len(uidList)

        for i in xrange(total):
            uid = uidList[i]

            if not uid in self.account.seenMessageUIDS:
                self.vars.headerCheckList.append((i, uid))

        if len(self.vars.headerCheckList) > 0:
            msgNum, uid = self.vars.headerCheckList.pop(0)

            # This sends a TOP msgNum 0 command to the POP3 server
            d = self.proto.retrieve(msgNum, lines=0)
            d.addCallback(self._isNewChandlerMessage, msgNum, uid)
            d.addErrback(self.catchErrors)

            return d

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                         {'accountName': self.account.displayName})

        return self._actionCompleted()

    def _isNewChandlerMessage(self, msgHeaders, msgNum, uid):
        if __debug__:
            trace("_isNewChandlerMessage")

        if "X-Chandler-Mailer: True" in msgHeaders:
            # This is a Chandler Message so add it to
            # the list of pending messages to be downloaded
            self.vars.pending.append((msgNum, uid))

        else:
            # Now that we know that this is not a Chandler message,
            # add it to the seenMessageUIDS list so we don't
            # download the headers again.
            self.account.seenMessageUIDS[uid] = "True"
            self.vars.addedUIDS = True

        if len(self.vars.headerCheckList) > 0:
            msgNum, uid = self.vars.headerCheckList.pop(0)

            # This sends a TOP msgNum 0 command to the POP3 server
            d = self.proto.retrieve(msgNum, lines=0)
            d.addCallback(self._isNewChandlerMessage, msgNum, uid)
            d.addErrback(self.catchErrors)

            return d

        # Check if there is a maximum number of messages
        # that can be download for this account and
        # if so reduce the self.vars.pending list.
        numPending = self._checkDownloadMax()

        if numPending == 0:
            if self.statusMessages:
                setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            if self.vars.addedUIDS:
                #Commit the change to C{POPAccount.seenMessageUIDS}
                self.view.commit()

            return self._actionCompleted()

        # Ok lets go fetch the new mail containing
        # Chandler headers

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_START_MESSAGES % \
                             {"accountName": self.account.displayName,
                              "numberOfMessages": numPending})

        self._getNextMessageSet()

    def _checkForNewMessages(self, uidList):
        if __debug__:
            trace("_checkForNewMessages")

        if self.cancel:
            return self._actionCompleted()

        total = len(uidList)

        for i in xrange(total):
            uid = uidList[i]

            if not uid in self.account.seenMessageUIDS:
                self.vars.pending.append((i, uid))

        # Check if there is a maximum number of messages
        # that can be download for this account and
        # if so reduce the self.vars.pending list.
        numPending = self._checkDownloadMax()

        if numPending == 0:
            if self.statusMessages:
                setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            return self._actionCompleted()

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_START_MESSAGES % \
                             {"accountName": self.account.displayName,
                              "numberOfMessages": numPending})

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

        self.vars.numToDownload = len(self.vars.pending)

        if self.vars.numToDownload == 0:
            return self._actionCompleted()

        if self.vars.numToDownload > self.commitNumber:
            self.vars.numToDownload = self.commitNumber

        msgNum, uid = self.vars.pending.pop(0)

        d = self.proto.retrieve(msgNum)

        d.addCallback(self._retrieveMessage, msgNum, uid)
        d.addErrback(self.catchErrors)

        return d

    def _retrieveMessage(self, msg, msgNum, uid):
        if __debug__:
            trace("_retrieveMessage")

        if self.cancel:
            #XXX Think about this some more
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
        self.account.seenMessageUIDS[uid] = "True"
        self.vars.numDownloaded += 1

        if self.account.deleteOnDownload:
            self.vars.delList.append(msgNum)

        if self.vars.numDownloaded == self.vars.numToDownload:
            self.vars.totalDownloaded += self.vars.numDownloaded
            return self._commitDownloadedMail()

        msgNum, uid = self.vars.pending.pop(0)

        d = self.proto.retrieve(msgNum)
        d.addCallback(self._retrieveMessage, msgNum, uid)
        d.addErrback(self.catchErrors)

        return d

    def _performNextAction(self):
        if __debug__:
            trace("_performNextAction")

        if self.statusMessages:
            msg = constants.DOWNLOAD_MESSAGES % {'accountName': self.account.displayName,
                                                 'numberOfMessages': self.vars.totalDownloaded}
            setStatusMessage(msg)

        if self.account.deleteOnDownload and len(self.vars.delList):
            dList = []

            for msgNum in self.vars.delList:
                dList.append(self.proto.delete(msgNum))

            # Reset the delList
            self.vars.delList = []

            d = defer.DeferredList(dList)

        else:
            d = defer.succeed(True)

        d.addErrback(self.catchErrors)

        if len(self.vars.pending) == 0:
            meth = self._actionCompleted

        else:
            meth = self._getNextMessageSet

        self.vars.numDownloaded = 0
        self.vars.numToDownload = 0

        return d.addCallback(lambda x: meth())

    def _checkDownloadMax(self):
        numPending = len(self.vars.pending)

        if numPending > 0:
            max = self.account.downloadMax
            downloaded = len(self.account.mailMessages)

            if max > 0 and (numPending + downloaded > max):
                # If the number of pending messages exceeds the
                # maximum number of messages that should be downloaded,
                # then reduce the pending list to that maximum number.
                #
                # A c{POPAccount.downladMax} value <= 0 indicated that
                # there is no limit on the number of messages that
                # can be downloaded.

                self.vars.pending = self.vars.pending[:max - downloaded]
                numPending = len(self.vars.pending)

        return numPending

    def _beforeDisconnect(self):
        """Overides base class to send a POP 'QUIT' command
           before disconnecting from the POP server"""
        if __debug__:
            trace("_beforeDisconnect")

        if self.factory is None or self.proto is None or \
           self.factory.connectionLost or self.factory.timedOut:
            return defer.succeed(True)

        return self.proto.quit()

    def _getAccount(self):
        """Retrieves a C{POPAccount} instance from its C{UUID}"""
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
