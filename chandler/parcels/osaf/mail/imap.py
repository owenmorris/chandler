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
import twisted.mail.imap4 as imap4

#python imports
import email

#Chandler imports
import osaf.pim.mail as Mail
from osaf.framework.certstore import ssl

#Chandler Mail Service imports
import message
import errors
import constants
import base
from utils import *
from message import *

__all__ = ['IMAPClient']

"""
    TODO:
    1. Look in to pluging the Python email 3.0 Feedparser in to the
       rawDataReceived method of IMAP4Client for better performance.
       Or Twisted Feedparser (For 1.0)
    2. Will need to just get the basic headers of subject, message id,
       message size to, from, cc. Then have a callback to sync the rest
       when downloading an individual mail use the feedparser for performance
    3. Start thinking about offline mode. Does the domain model need any changes.
       Offline mode for email is simply adding MailMessages to a queue and executing
       the queue when online. The queue need to be persisted in the repository
"""

class _TwistedIMAP4Client(imap4.IMAP4Client):
    """
    Overrides C{imap4.IMAP4Client} to add Chandler specific functionality
    including startTLS management and Timeout management.
    """

    def serverGreeting(self, caps):
        """
        This method overrides C{imap4.IMAP4Client}.
        It assigns itself as the protocol for its delegate.

        If caps is None does an explicit request to the
        IMAP server for its capabilities.

        Entry point for STARTTLS logic. Will call delegate.loginClient
        or delegate.catchErrors if an error occurs.

        @param caps: The list of server CAPABILITIES or None
        @type caps: C{dict} or C{None}
        @return C{defer.Deferred}
        """
        if __debug__:
            trace("serverGreeting")

        if caps is None:
            # If no capabilities returned in server greeting then get
            # the server capabilities
            d = self.getCapabilities()

            return d.addCallback(self._getCapabilities
                     ).addErrback(self.delegate.catchErrors)

        self._getCapabilities(caps)

    def _getCapabilities(self, caps):
        if __debug__:
            trace("_getCapabilities")

        if self.factory.useTLS:
            # The Twisted IMAP4Client will check to make sure the server can STARTTLS
            # and raise an error if it can not
            d = self.startTLS(self.transport.contextFactory.getContext())

            return d.addCallback(lambda _: self.delegate.loginClient()
                                 ).addErrback(self.delegate.catchErrors)

        if 'LOGINDISABLED' in caps:
            self._raiseException(errors.IMAPException(constants.DOWNLOAD_REQUIRES_TLS))

        else:
            # Remove the STARTTLS from capabilities
            self._capCache = disableTwistedTLS(caps)
            self.delegate.loginClient()

    def timeoutConnection(self):
        """
        Called by C{policies.TimeoutMixin} base class.
        The method generates an C{IMAPException} and forward
        to delegate.catchErrors.
        """
        if __debug__:
            trace("timeoutConnection")

        # We have timed out so do not send any more commands to
        # the server just disconnect
        exc = errors.IMAPException(errors.STR_TIMEOUT_ERROR)
        self.factory.timedOut = True
        self._raiseException(exc)

    def _raiseException(self, exception):
        if __debug__:
            trace("_raiseException")

        raised = False

        if self._lastCmd and self._lastCmd.defer is not None:
            d, self._lastCmd.defer = self._lastCmd.defer, None
            d.errback(exception)
            raised = True

        if self.queued:
            for cmd in self.queued:
                if cmd.defer is not None:
                    d, cmd.defer = cmd.defer, d
                    d.errback(exception)
                    raised = True

        if not raised:
            d = defer.Deferred().addErrback(self.delegate.catchErrors)
            d.errback(exception)

class IMAPClientFactory(base.AbstractDownloadClientFactory):
    """
    Inherits from C{base.AbstractDownloadClientFactory}
    and overides default protocol and exception values
    with IMAP specific values
    """

    protocol  = _TwistedIMAP4Client

    # The exception to raise when an error occurs
    exception = errors.IMAPException


class IMAPClient(base.AbstractDownloadClient):
    """
    Provides support for Downloading mail from an
    IMAP mail 'Inbox' as well as test Account settings.

    This functionality will be enhanced to be a more
    robust IMAP client in the near future
    """

    # Overides default values in base class to provide
    # IMAP specific functionality
    accounType  = Mail.IMAPAccount
    clientType  = "IMAPClient"
    factoryType = IMAPClientFactory
    defaultPort = 143

    def _loginClient(self):
        """
        Logs a client in to an IMAP servier using the CramMD6, Login, or
        Plain authentication
        """

        if __debug__:
            trace("_loginClient")

        if self.cancel:
            return self._actionCompleted()

        assert self.account is not None

        #Twisted expects ascii values so encode the utf-8 username and password
        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)

        self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
        self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))

        return self.proto.authenticate(password
                     ).addCallback(self._selectInbox
                     ).addErrback(self.loginClientInsecure, username, password
                     ).addErrback(self.catchErrors)


    def loginClientInsecure(self, error, username, password):
        """
        If the IMAP4 Server does not support MD5 or Login authentication
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
        @type username: C{string}

        @param password: The password to log in with
        @type password: C{string}
        """

        if __debug__:
            trace("loginClientInsecure")

        if self.cancel:
            return self._actionCompleted()

        error.trap(imap4.NoSupportedAuthentication)

        return self.proto.login(username, password
                    ).addCallback(self._selectInbox
                    ).addErrback(self.catchErrors)


    def _selectInbox(self, result):
        if __debug__:
            trace("_selectInbox")

        if self.cancel:
            return self._actionCompleted()

        if self.testing:
            callMethodInUIThread(self.callback, (1, None))
            return self._actionCompleted()

        setStatusMessage(constants.DOWNLOAD_CHECK_MESSAGES % \
                        {'accountName': self.account.displayName})

        d = self.proto.select("INBOX"
                   ).addCallback(self._checkForNewMessages
                   ).addErrback(self.catchErrors)


        return d

    def _checkForNewMessages(self, msgs):
        if __debug__:
            trace("_checkForNewMessages")

        #XXX: Need to store and compare UIDVALIDITY
        #if not msgs['UIDVALIDITY']:
        #    print "server: %s has no UUID Validity:\n%s" % (self.account.host, msgs)

        if self.cancel:
            return self._actionCompleted()

        if msgs['EXISTS'] == 0:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            return self._actionCompleted()

        if self._getNextUID() == 0:
            msgSet = imap4.MessageSet(1, None)
        else:
            msgSet = imap4.MessageSet(self._getNextUID(), None)

        return self.proto.fetchFlags(msgSet, uid=True
                   ).addCallback(self._getMessagesFlagsUID
                   ).addErrback(self.catchErrors)

    def _getMessagesFlagsUID(self, msgs):
        if __debug__:
            trace("_getMessagesFlagsUIDS")

        if self.cancel:
            return self._actionCompleted()

        nextUID = self._getNextUID()

        for message in msgs.itervalues():
            luid = long(message['UID'])

            if luid < nextUID:
                continue

            if not "\\Deleted" in message['FLAGS']:
                self.pending.append([luid, message['FLAGS']])

        numPending = len(self.pending)

        if numPending == 0:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            return self._actionCompleted()

        setStatusMessage(constants.DOWNLOAD_START_MESSAGES % \
                         {"accountName": self.account.displayName,
                          "numberOfMessages": numPending})

        self._getNextMessageSet()

    def _getNextMessageSet(self):
        """
        Overides base class to add IMAP specific logic.

        If the pending queue has one or messages to download
        for n messages up to C{IMAPAccount.downloadMax} fetches
        the mail from the IMAP server. If no message pending
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

        m = self.pending.pop(0)

        return self.proto.fetchMessage(str(m[0]), uid=True
                      ).addCallback(self._fetchMessage, m
                      ).addErrback(self.catchErrors)


    def _fetchMessage(self, msgs, curMessage):
        if __debug__:
            trace("_fetchMessage")

        if self.cancel:
            try:
                #We call cancel() here since there may be
                #in memory mail message items which we want to
                #deallocate from the current view.
                self.view.cancel()
            except:
                pass

            return self._actionCompleted()

        msg = msgs.keys()[0]

        #Check if the uid of the message is greater than
        #last message fetched
        if curMessage[0] > self.lastUID:
            self.lastUID = curMessage[0]

        if  "\\Seen" in curMessage[1]:
            callback = defer.succeed(True)
        else:
            callback = self.proto.removeFlags(curMessage[0], ["\Seen"], uid=True)

        messageText = msgs[msg]['RFC822']

        #XXX: Need a more performant way to do this
        messageObject = email.message_from_string(messageText)

        repMessage = messageObjectToKind(self.view, messageObject, messageText)

        # Set the message as incoming
        repMessage.incomingMessage(self.account)

        # Save IMAP Delivery info in Repository
        repMessage.deliveryExtension.folder = u"INBOX"
        repMessage.deliveryExtension.uid = curMessage[0]
        #Commented out for Preview
        #repMessage.deliveryExtension.flags = curMessage[1]

        self.numDownloaded += 1
        self.pruneCounter  += 1

        if self.numDownloaded == self.numToDownload:
            self._setNextUID(self.lastUID + 1)
            self.totalDownloaded += self.numDownloaded

            return callback.addBoth(lambda x: self._commitDownloadedMail())

        else:
            m = self.pending.pop(0)

            return callback.addBoth(lambda x: self.proto.fetchMessage(str(m[0]), uid=True
                                        ).addCallback(self._fetchMessage, m
                                        ).addErrback(self.catchErrors)
                                    )
    def _expunge(self, result):
        if __debug__:
            trace("_expunge")

        return self.proto.expunge()

    def _getNextUID(self):
        return self.account.messageDownloadSequence

    def _setNextUID(self, uid):
        self.account.messageDownloadSequence = uid

    def _beforeDisconnect(self):
        """
        Overides base class to send a IMAP 'LOGOUT' command
        before disconnecting from the IMAP server
        """

        if __debug__:
            trace("_beforeDisconnect")

        if self.factory is None or self.proto is None or \
           self.factory.connectionLost or self.factory.timedOut or \
           self.proto.queued is None:
            return defer.succeed(True)

        if self.testing:
            # In testing mode no mailbox is open
            return self.proto.sendCommand(imap4.Command('LOGOUT', wantResponse=('BYE',)))

        else:
            d = self.proto.close()
            d.addBoth(lambda x: self.proto.sendCommand(imap4.Command('LOGOUT', wantResponse=('BYE',))))

            return d

    def _getAccount(self):
        """
        Retrieves a C{Mail.IMAPAccount} instance from its C{UUID}.
        """
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
