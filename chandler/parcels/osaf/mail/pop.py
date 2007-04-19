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
import twisted.internet.defer as defer
import twisted.mail.pop3client as pop3

#python imports
import email

#Chandler imports
from osaf.pim.mail import POPAccount

#Chandler Mail Service imports
import errors
import constants
import base
from utils import *
from message import *

__all__ = ['POPClient']

"""
1. Add in AUTH LOGIN to twisted pop3client.py
"""

# When set to True and in __debug__ mode
# This flag will signal whether to print
# the communications between the client
# and server. This is especially handy
# when the traffic is encrypted (SSL/TLS).
DEBUG_CLIENT_SERVER = False

class POPVars(base.DownloadVars):
    def __init__(self):
        super(POPVars, self).__init__()
        self.headerCheckList = []
        self.addedUIDS = False

        # indicates whether the server supports
        # the optional TOP command
        self.top = False

        # The number of new items downloaded
        self.totalNewDownloaded = 0

        # The number of updated items downloaded
        self.totalUpdateDownloaded = 0

        # The number of ignored messages downloaded
        self.totalIgnoreDownloaded = 0


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

        # For Preview the optional UIDL command
        # is required. It is very hard to
        # determine what mail has already been
        # downloaded with out it.
        if 'UIDL' not in caps:
            txt = constants.POP_UIDL_ERROR
            return self.delegate.catchErrors(errors.POPException(txt))

        if self.factory.useTLS:
            # The Twisted POP3Client will check to make sure the server can STARTTLS
            # and raise an error if it can not
            d = self.startTLS(self.transport.contextFactory.getContext())
            d.addCallbacks(lambda _: self.delegate.loginClient(),
                                     self.delegate.catchErrors)
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

    def sendLine(self, line):
        pop3.POP3Client.sendLine(self, line)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "C: %s" % line

    def rawDataReceived(self, data):
        pop3.POP3Client.rawDataReceived(self, data)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "S: %s" % data

    def lineReceived(self, line):
        pop3.POP3Client.lineReceived(self, line)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "S: %s" % line


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
        username = self.account.username.encode("utf-8")
        
        deferredPassword = self.account.password.decryptPassword()

        def callback(password):
            password = password.encode("utf-8")
            d = self.proto.login(username, password)
            #XXX: Can handle the failed login case here
            #     and prompt user to re-enter username
            #     and password.
            d.addCallbacks(self.cb, self.catchErrors)
            return d

        return deferredPassword.addCallback(callback
                              ).addErrback(self.catchErrors)

    def _getMail(self, result):
        if __debug__:
            trace("_getMail")

        if self.cancel:
            return self._actionCompleted()

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_CHECK_MESSAGES % \
                            {'accountName': self.account.displayName})


        self.vars = POPVars()

        if self.proto._capCache.has_key("TOP"):
            # The server supports TOP
            self.vars.top = True

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
        downloaded = self.account.downloaded

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

            if self.vars.top:
                # This sends a TOP msgNum 0 command to the POP3 server
                d = self.proto.retrieve(msgNum, lines=0)
            else:
                d = self.proto.retrieve(msgNum)

            d.addCallback(self._isNewChandlerMessage, msgNum, uid)
            d.addErrback(self.catchErrors)

            return d

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                         {'accountName': self.account.displayName})

        return self._actionCompleted()

    def _isNewChandlerMessage(self, msg, msgNum, uid):
        if __debug__:
            trace("_isNewChandlerMessage")

        if self.vars.top and "X-Chandler-Mailer: True" in msg:
            # If the server supports top and the msg (which is
            # a list of message headers) has the Chandler Header flag
            # in it add it to the pending list
            self.vars.pending.append((msgNum, uid))

        elif not self.vars.top:
            # In this case message is a list of all headers and body
            # parts so we join the list and convert it to a Python
            # email object

            #XXX this case is extremely inefficient since
            # the same message is downloaded twice if it
            # contains Chandler Headers.
            # Post-Preview this will probally be refactored.

            msgText = "\n".join(msg)
            messageObject = email.message_from_string(msgText)

            if messageObject.get("X-Chandler-Mailer", "") == "True":
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

            if self.vars.top:
                # This sends a TOP msgNum 0 command to the POP3 server
                d = self.proto.retrieve(msgNum, lines=0)
            else:
                d = self.proto.retrieve(msgNum)

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
            # This is a PyICU.ChoiceFormat class
            txt = constants.POP_START_MESSAGES.format(numPending)

            setStatusMessage(txt % \
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
            # This is a PyICU.ChoiceFormat class
            txt = constants.DOWNLOAD_START_MESSAGES.format(numPending)

            setStatusMessage(txt % \
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
            try:
                # We call cancel() here since there may be
                # in memory mail message items which we want to
                # deallocate from the current view.
                self.view.cancel()
            except:
                pass

            return self._actionCompleted()


        messageText = "\n".join(msg)

        #XXX: Need a more performant way to do this
        repMessage = messageTextToKind(self.view, messageText)

        if repMessage:
            # If the message contained an eimml attachment
            # that was older then the current state or
            # contained bogus data then repMessage will be
            # None

            if repMessage.isAnUpdate():
                # This is an update to an existing Chandler item
                # so increment the updatecounter
                self.vars.totalUpdateDownloaded += 1
            else:
                # This is a new Chandler item so increment the
                # new counter
                self.vars.totalNewDownloaded += 1

            repMessage.incomingMessage()
            self.account.downloaded += 1

        else:
            # The message downloaded contained eimml that
            # for what ever reason was ignored.
            self.vars.totalIgnoreDownloaded += 1

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

            if self.statusMessages:
                # This is a PyICU.ChoiceFormat class
                txt = constants.DOWNLOAD_CHANDLER_MESSAGES.format(self.vars.totalDownloaded)

                setStatusMessage(txt % \
                                 {'accountName': self.account.displayName,
                                  'numberTotal': self.vars.totalDownloaded,
                                  'numberNew': self.vars.totalNewDownloaded,
                                  'numberUpdates': self.vars.totalUpdateDownloaded,
                                  'numberDuplicates': self.vars.totalIgnoreDownloaded})

        else:
            meth = self._getNextMessageSet

        self.vars.numDownloaded = 0
        self.vars.numToDownload = 0

        return d.addCallback(lambda x: meth())

    def _checkDownloadMax(self):
        numPending = len(self.vars.pending)

        if numPending > 0:
            max = self.account.downloadMax
            downloaded = self.account.downloaded

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

