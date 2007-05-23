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
import twisted.internet.reactor as reactor

#python imports
import email

#Chandler imports
from osaf.pim.mail import POPAccount

#Chandler Mail Service imports
import errors
import constants
import base
from utils import *
import message
import mailworker

__all__ = ['POPClient']

"""
1. Add in AUTH LOGIN to twisted pop3client.py

TO DO:
1. Post preview find a better means to store the
   seenMessageUIDs then a dict on the account
"""

class POPVars(base.DownloadVars):
    def __init__(self):
        super(POPVars, self).__init__()
        self.headerCheckList = []

        # The list of POP UIDs that
        # have been seen since the last
        # repository refresh.
        # The commiting of seen UIDs is
        # handled by the Mail Worker so
        # the POP Client needs to keep
        # its own cache since commits
        # are async from download.
        self.newSeenUIDS = {}

        # indicates whether the server supports
        # the optional TOP command
        self.top = False

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
            # The Twisted POP3Client will check to make sure the server
            # can STARTTLS
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
        if __debug__ and constants.DEBUG_CLIENT_SERVER:
            txt = ">>> C: %s" % line

            if constants.DEBUG_CLIENT_SERVER == 1:
                self.delegate._saveToBuffer(txt)

            elif constants.DEBUG_CLIENT_SERVER == 2:
                print txt

        return pop3.POP3Client.sendLine(self, line)

    def rawDataReceived(self, data):
        if __debug__ and constants.DEBUG_CLIENT_SERVER:
            txt = ">>> S: %s" % data

            if constants.DEBUG_CLIENT_SERVER == 1:
                self.delegate._saveToBuffer(txt)

            elif constants.DEBUG_CLIENT_SERVER == 2:
                print txt

        return pop3.POP3Client.rawDataReceived(self, data)


    def lineReceived(self, line):
        if __debug__ and constants.DEBUG_CLIENT_SERVER:
            txt = ">>> S: %s" % line

            if constants.DEBUG_CLIENT_SERVER == 1:
                self.delegate._saveToBuffer(txt)

            elif constants.DEBUG_CLIENT_SERVER == 2:
                print txt

        return pop3.POP3Client.lineReceived(self, line)

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

    def _loginClient(self):
        """Logs a client in to an POP servier using APOP 
           (if available or plain text login"""

        if __debug__:
            trace("_loginClient")

        if self.cancel:
            return self._actionCompleted()

        # Twisted expects 8-bit values so encode the 
        # utf-8 username and password
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
                trace("[%s] Max number of messages %s reached." % \
                  (self.account.displayName.encode("utf-8"), max))

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

        uidLen = len(uidList)

        for i in xrange(uidLen):
            uid = uidList[i]

            if not uid in self.account.seenMessageUIDS and \
               not self.vars.newSeenUIDS.has_key(uid):
                self.vars.headerCheckList.append((i, uid))

        if len(self.vars.headerCheckList) > 0:
            total = len(self.vars.headerCheckList)
            start = 0
            cur   = 0
            end   = constants.MAX_POP_SEARCH_NUM 

            if end > total:
                end = total

            msgNum, uid = self.vars.headerCheckList.pop(0)

            # Print the searching for Chandler messages
            # status bar message
            self._printSearchNum(start, end, total)

            if self.vars.top:
                # This sends a TOP msgNum 0 command to the 
                #  POP3 server
                d = self.proto.retrieve(msgNum, lines=0)
            else:
                d = self.proto.retrieve(msgNum)

            d.addCallback(self._isNewChandlerMessage,
                          msgNum, uid, cur,
                          start, end, total)
            d.addErrback(self.catchErrors)

            return None

        if self.statusMessages:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                         {'accountName': self.account.displayName})

        return self._actionCompleted()

    def _printSearchNum(self, start, end, total):
        if self.statusMessages:
            setStatusMessage(constants.POP_SEARCH_STATUS %
                  {'accountName': self.account.displayName,
                  'start': start,
                  'end': end,
                  'total': total})


    def _isNewChandlerMessage(self, msg, msgNum, uid, 
                              cur, start, end, total):
        if __debug__:
            trace("_isNewChandlerMessage")

        if cur >= end and cur < total: 
            start = end
            end = start + constants.MAX_POP_SEARCH_NUM

            if end > total:
                end = total

            # Print the searching for Chandler messages
            # status bar message
            self._printSearchNum(start, end, total)

        if self.vars.top and "X-Chandler-Mailer: True" in msg:
            # If the server supports top and the msg (which is
            # a list of message headers) has the Chandler Header
            # flag in it add it to the pending list
            self.vars.pending.append((msgNum, uid))

        elif not self.vars.top:
            # In this case message is a list of all headers 
            # and body parts so we join the list and convert 
            # it to a Python email object
            msgObj = email.message_from_string("\n".join(msg))

            if msgObj.get("X-Chandler-Mailer", "") == "True":
                # Since the message text was already downloaded and
                # converted to a email.Message to check if the
                # Chandler header is present, create a Mail
                # Worker request here to prevent having to
                # redownload the message later.
                req = message.previewQuickParse(msgObj, 
                                                isObject=True)

                # This is a Chandler Message so add it to
                # the list of pending messages to be downloaded
                self.vars.pending.append((msgNum, uid, req))

        # Record that this message has now been seen
        self.vars.newSeenUIDS[uid] = True

        if len(self.vars.headerCheckList) > 0:
            msgNum, uid = self.vars.headerCheckList.pop(0)

            if self.vars.top:
                # This sends a TOP msgNum 0 command to the 
                # POP3 server
                d = self.proto.retrieve(msgNum, lines=0)
            else:
                d = self.proto.retrieve(msgNum)

            d.addCallback(self._isNewChandlerMessage, 
                          msgNum, uid, cur+1, start,
                          end, total)
            d.addErrback(self.catchErrors)

            return None

        # Check if there is a maximum number of messages
        # that can be download for this account and
        # if so reduce the self.vars.pending list.
        self.vars.totalToDownload = self._checkDownloadMax()

        if self.vars.totalToDownload == 0:
            if self.statusMessages:
                setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            if self.vars.newSeenUIDS:
                self.mailWorker.queueRequest((mailworker.UID_REQUEST, 
                                              self,
                                              self.accountUUID,
                                              self.vars.newSeenUIDS.keys()))
            return self._actionCompleted()

        # Ok lets go fetch the new mail containing
        # Chandler headers

        if self.statusMessages:
            # This is a PyICU.ChoiceFormat class
            txt = constants.DOWNLOAD_START_MESSAGES.format(
                                         self.vars.totalToDownload)

            setStatusMessage(txt % \
                             {"accountName": self.account.displayName,
                              "numberOfMessages": self.vars.totalToDownload})

        self._getNextMessageSet()

    def _checkForNewMessages(self, uidList):
        if __debug__:
            trace("_checkForNewMessages")

        if self.cancel:
            return self._actionCompleted()

        total = len(uidList)

        for i in xrange(total):
            uid = uidList[i]

            if not uid in self.account.seenMessageUIDS and \
               not self.vars.newSeenUIDS.has_key(uid):
                self.vars.pending.append((i, uid))
                self.vars.newSeenUIDS[uid] = True

        # Check if there is a maximum number of messages
        # that can be download for this account and
        # if so reduce the self.vars.pending list.
        self.vars.totalToDownload = self._checkDownloadMax()

        if self.vars.totalToDownload == 0:
            if self.statusMessages:
                setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                             {'accountName': self.account.displayName})

            return self._actionCompleted()

        if self.statusMessages:
            # This is a PyICU.ChoiceFormat class
            txt = constants.DOWNLOAD_START_MESSAGES.format(
                                        self.vars.totalToDownload)

            setStatusMessage(txt % \
                             {"accountName": self.account.displayName,
                              "numberOfMessages": self.vars.totalToDownload})

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

        commitNumber = self.calculateCommitNumber()

        if self.vars.numToDownload > commitNumber:
            self.vars.numToDownload = commitNumber

        return self._processNextPending()

    def _retrieveMessage(self, msg, msgNum, uid, mRequest=None):
        if __debug__:
            trace("_retrieveMessage")

        if self.cancel:
            return self._actionCompleted()

        if not mRequest:
            mRequest = message.previewQuickParse("\n".join(msg))

        self.vars.messages.append(
                            # Tuple containing
                            # 0: Mail Request
                            # 1: POP UID of message
                            (mRequest, uid)
                            )

        # this value is used to determine
        # when to post a MAIL_REQUEST to
        # the MailWorker ot commit downloaded
        # mail
        self.vars.numDownloaded += 1

        if self.vars.numDownloaded == self.vars.numToDownload: 
            args = self._getStatusStats()
            statusMsg = constants.POP_COMMIT_MESSAGES % args
            self._commitMail(statusMsg)

            # Increment the totalDownloaded counter
            # by the number of messages in 
            # the self.vars.messages queue
            self.vars.totalDownloaded = args["end"]
        else:
            self._processNextPending()

    def _processNextPending(self):
        next = self.vars.pending.pop(0)

        if len(next) == 3:
            # In this case the server did not support TOP
            # and the POP account was configured for Chandler
            # Headers. In order to determine which messages
            # have Chandler Headers, the messages had to be
            # downloaded in full. For performance the
            # message already has been converted to a 
            # MailWorker request.
            msgNum, uid, mRequest = next
            return self._retrieveMessage(None, msgNum, uid, 
                                         mRequest)
        else:
            msgNum, uid = next

            d = self.proto.retrieve(msgNum)

            d.addCallback(self._retrieveMessage, msgNum, uid)
            d.addErrback(self.catchErrors)

            return d

    def nextAction(self):
        if __debug__:
            trace("nextAction")
        #if self.account.deleteOnDownload and len(self.vars.delList):
        #    dList = []
        #
        #    for msgNum in self.vars.delList:
        #        dList.append(self.proto.delete(msgNum))
        #    # Reset the delList
        #    self.vars.delList = []
        #    d = defer.DeferredList(dList)
        #d.addErrback(self.catchErrors)
        self._nextAction()

        if len(self.vars.pending) == 0:

            
            if self.vars.newSeenUIDS:
                #If there are new seen UID's then
                # save the UID's to prevent redownloading
                # or re-searching the same messages.
                self.mailWorker.queueRequest(
                                (mailworker.UID_REQUEST, 
                                self,
                                self.accountUUID,
                                self.vars.newSeenUIDS.keys()))


            # There is no more mail to download so send a DONE
            # request
            self.mailWorker.queueRequest((mailworker.DONE_REQUEST, 
                                          self, self.accountUUID))

            # Calling _actionCompleted with a False argument
            # keeps the performingAction lock. The
            # processing of the DONE_REQUEST in the MailWorker
            # will result in the performingAction lock being released.
            reactor.callLater(0, self._actionCompleted, False)
        else:
            reactor.callLater(0, self._getNextMessageSet)

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
