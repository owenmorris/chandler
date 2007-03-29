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
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.mail.imap4 as imap4
import twisted.python.failure as failure

#python imports
import email
import PyICU

#Chandler imports
from osaf.pim.mail import IMAPAccount, IMAPFolder
from osaf.framework.certstore import ssl
from application import Globals

#Chandler Mail Service imports
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
       Or Twisted Feedparser (For 1.0). *** By lowering the in memory
       limit the messgeFile IMAP4Client API will be used to create a tmp file.
       This is useful for memory management
    2. Will need to just get the basic headers of subject, message id,
       message size to, from, cc. Then have a callback to sync the rest
       when downloading an individual mail use the feedparser for performance
    3. Could fetch UID's then build a sorted list and use pop to get the newest
       messages first
"""

# When set to True and in __debug__ mode
# This flag will signal whether to print
# the communications between the client
# and server. This is especially handy
# when the traffic is encrypted (SSL/TLS).
DEBUG_CLIENT_SERVER = False

# The maximum number of message UID's to
# include in a search for Chandler Headers.
MAX_SEARCH_NUM = 650

#Place holder for displaying more info to
# the user on large mailbox searches
#MIN_SEARCH_ALERT = 1500

class FolderVars(base.DownloadVars):
    """
       This class contains the non-persisted
       IMAPFolder variables that are used
       during the downloading of mail from an
       IMAP folder.
    """ 
    def __init__(self):
        super(FolderVars, self).__init__()

        # The C{osaf.pim.mail.IMAPFolder} item
        # that contains the persisted folder info
        self.folderItem   = None

        # The IMAP UID of the last message
        # downloaded from the folder.
        # This is used to cache the highest
        # downloaded message uid up to point
        # just before a commit takes place.
        # At that point the lastUID is saved
        # in the IMAPFolder.lastMessageUID
        # attribute
        self.lastUID = 0

        # The index position of the
        # IMAP folder in the IMAPAccount.folders
        # sequence.
        self.indexNumber = 0

        # The list of UID's to search
        # for Chandler Headers
        self.searchUIDs = []

        # The list of UID's of messages
        # that contain Chandler Headers
        # and should be downloaded.
        self.foundUIDs  = []


    def getNextUID(self):
        return self.folderItem.lastMessageUID

    def setNextUID(self, uid):
        self.folderItem.lastMessageUID = uid


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
            self._raiseException(errors.IMAPException(constants.MAIL_PROTOCOL_REQUIRES_TLS))

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
        exc = errors.IMAPException(constants.MAIL_PROTOCOL_TIMEOUT_ERROR)
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

    def sendLine(self, line):
        imap4.IMAP4Client.sendLine(self, line)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "C: %s" % line

    def rawDataReceived(self, data):
        imap4.IMAP4Client.rawDataReceived(self, data)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "S: %s" % data

    def lineReceived(self, line):
        imap4.IMAP4Client.lineReceived(self, line)

        if __debug__ and DEBUG_CLIENT_SERVER:
            print "S: %s" % line

    def _fetch(self, messages, useUID=0, **terms):
        # The fastmail messaging engine server
        # returns flags on unread messages
        # when a UID FETCH mNum (RFC822) is requested.
        # This is a bug on the twisted side.
        # The twisted IMAP4Server does not have an API
        # for requesting just the FLAGS and the RFC822.
        # This workaround makes that possible.
        # By requesting the FLAGS everytime we avoid
        # the case where the server on its own
        # returns FLAGS on unread messages.
        if 'rfc822' in terms:
            terms['flags'] = True

        return imap4.IMAP4Client._fetch(self, messages, useUID, **terms)

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
    accountType  = IMAPAccount
    clientType   = "IMAPClient"
    factoryType  = IMAPClientFactory
    defaultPort  = 143

    def __init__(self, view, account):
        super(IMAPClient, self).__init__(view, account)

        # This is the total number of mail messages
        # downloaded for all folders including
        # new items and updated items
        self.totalDownloaded = 0
        self.totalNewDownloaded = 0
        self.totalUpdateDownloaded = 0
        self.totalIgnoreDownloaded = 0

    def createChandlerFolders(self, callback, reconnect):
        if __debug__:
            trace("createChandlerFolders")

        assert(callback is not None)
        assert(reconnect is not None)

        self.cb = self._createChandlerFolders

        # The method to call in the UI Thread
        # when the testing is complete.
        # This method is called for both success and failure.
        self.callback = callback

        # Tells whether to print status messages
        self.statusMessages = False

        # Tell what method to call on reconnect
        # when a SSL dialog is displayed.
        # When the dialog is shown the
        # protocol code terminates the
        # connection and calls reconnect
        # if the cert has been accepted
        self.reconnect = reconnect

        # Move code execution path from current thread
        # to Reactor Asynch thread
        reactor.callFromThread(self._connectToServer)

    def removeChandlerFolders(self, callback, reconnect):
        if __debug__:
            trace("removeChandlerFolders")

        assert(callback is not None)
        assert(reconnect is not None)

        self.cb = self._removeChandlerFolders

        # The method to call in the UI Thread
        # when the testing is complete.
        # This method is called for both success and failure.
        self.callback = callback

        # Tells whether to print status messages
        self.statusMessages = False

        # Tell what method to call on reconnect
        # when a SSL dialog is displayed.
        # When the dialog is shown the
        # protocol code terminates the
        # connection and calls reconnect
        # if the cert has been accepted
        self.reconnect = reconnect

        # Move code execution path from current thread
        # to Reactor Asynch thread
        reactor.callFromThread(self._connectToServer)

    def _removeChandlerFolders(self, results):
        if __debug__:
            trace("_removeChandlerFolders")

        d = self._getChandlerFoldersStatus()
        d.addCallback(self._cbRemoveChandlerFolders)
        d.addErrback(self.catchErrors)

        return d

    def _cbRemoveChandlerFolders(self, status):
        m = status[constants.CHANDLER_MAIL_FOLDER]
        t = status[constants.CHANDLER_TASKS_FOLDER]
        e = status[constants.CHANDLER_EVENTS_FOLDER]

        d = defer.succeed(1)

        self._addFolderToDeferred(m, d)
        self._addFolderToDeferred(t, d)
        self._addFolderToDeferred(e, d)

        d.addCallback(self._folderingFinished, status)
        return d

    def _addFolderToDeferred(self, folder, d):
        name, exists, subscribed = folder

        if exists:
            #XXX This logic can be refined to first do a status on the
            # folder and determine if there are any messages in the folder.
            # If no messages then just do a delete otherwise select the
            # folder, add the \Deleted flag on all messages, expunge,
            # close, and then delete folder.

            msgSet = imap4.MessageSet(1, None)
            d.addCallback(lambda x: self.proto.select(folder[0]))
            d.addCallback(lambda x: self.proto.addFlags(msgSet, ("\\Deleted",), uid=True))
            d.addCallback(lambda x: self.proto.expunge())
            d.addCallback(lambda x: self.proto.close())
            d.addCallback(lambda x: self.proto.delete(folder[0]))

        if subscribed:
            d.addCallback(lambda x: self.proto.unsubscribe(folder[0]))

    def _getChandlerFoldersStatus(self):
        if __debug__:
            trace("_getChandlerFoldersStatus")

        m = constants.CHANDLER_MAIL_FOLDER
        t = constants.CHANDLER_TASKS_FOLDER
        e = constants.CHANDLER_EVENTS_FOLDER

        status = {
            #pos 0: The Unicode name of the folder on the IMAP Server
            #pos 1: Boolean whether to folder exists on the server already
            #pos 2: Boolean whether the folder is currently subscribe to already
            m: [m, False, False],
            t: [t, False, False],
            e: [e, False, False]
        }

        if self.proto._capCache.has_key("CHILDREN"):
            # This list command will return the mailbox
            # delimiter for the IMAP4 server
            # and is needed to add the Chandler folders
            # under the Inbox.
            d = self.proto.list("", "")
            d.addCallback(self._getFolderDelimiter, status)

            # Get the list of all directories under the Inbox.
            # The '*" is used instead of the "%" due to an
            # issue with fastmail returning the wrong results
            # with "%" :(
            d.addCallback(lambda x: self.proto.list("INBOX", "*"))

            #List the subscribe sub-folders in the Inbox
            lsub = lambda x: self.proto.lsub("INBOX", "*")

        else:
            # List all root level mailboxes
            d = self.proto.list("", "%")
            # List all subscribed root folders
            lsub = lambda x: self.proto.lsub("", "%")

        d.addCallback(self._updateStatus, status, 0)
        d.addCallback(lsub)
        d.addCallback(self._updateStatus, status, 1)
        d.addCallback(lambda x: status)

        return d

    def _getFolderDelimiter(self, result, status):
        try:
            delim = result[0][1]
        except:
            # This error should never be raised but a
            # safeguard is put in place just in case.
            # Raising an IMAPException will result in
            # a clearer error message to the user
            # than just letting the index out of range
            # error be raised and show to the user.
            self._raiseException(errors.IMAPException(constants.IMAP_DELIMITER_ERROR))

        m = constants.CHANDLER_MAIL_FOLDER
        t = constants.CHANDLER_TASKS_FOLDER
        e = constants.CHANDLER_EVENTS_FOLDER

        #The folders are children of the Inbox
        status[m][0] = u"INBOX%s%s" % (delim, m)
        status[t][0] = u"INBOX%s%s" % (delim, t)
        status[e][0] = u"INBOX%s%s" % (delim, e)

    def _updateStatus(self, results, status, type):
        #type 0: list
        #type 1: lsub
        m = status[constants.CHANDLER_MAIL_FOLDER]
        t = status[constants.CHANDLER_TASKS_FOLDER]
        e = status[constants.CHANDLER_EVENTS_FOLDER]

        for folder in results:
            (flags, dir, name) = folder

            # A lower case comparison is done here
            # since the casing of "INBOX" returned
            # can differ depending on IMAP server
            # implementation

            if name.lower() == m[0].encode("imap4-utf-7").lower():
                #The chandler mail folder already
                #exists on the server or is
                #already subscribed to.
                if type:
                    m[2] = True
                else:
                    m[1] = True

            elif name.lower() == t[0].encode("imap4-utf-7").lower():
                #The chandler tasks folder already
                #exists on the server or is
                #already subscribed to.
                if type:
                    t[2] = True
                else:
                    t[1] = True

            elif name.lower() == e[0].encode("imap4-utf-7").lower():
                #The chandler events folder already
                #exists on the server or is
                #already subscribed to.
                if type:
                    e[2] = True
                else:
                    e[1] = True

    def _createChandlerFolders(self, results):
        if __debug__:
            trace("_createChandlerFolders")

        d = self._getChandlerFoldersStatus()
        d.addCallback(self._cbCreateChandlerFolders)
        d.addErrback(self.catchErrors)
        return d

    def _cbCreateChandlerFolders(self, status):
        d = defer.succeed(1)

        d.addCallback(self._createOrSubscribe, status, 0)
        d.addCallback(self._createOrSubscribe, status, 1)
        d.addCallback(self._folderingFinished, status)
        d.addErrback(self.catchErrors)

        return d

    def _createOrSubscribe(self, results, status, type):
        #type 0: list
        #type 1: lsub
        m = status[constants.CHANDLER_MAIL_FOLDER]
        t = status[constants.CHANDLER_TASKS_FOLDER]
        e = status[constants.CHANDLER_EVENTS_FOLDER]

        dList = []

        if type:
            if not m[2]:
                dList.append(self.proto.subscribe(m[0]))

            if not t[2]:
                dList.append(self.proto.subscribe(t[0]))

            if not e[2]:
                dList.append(self.proto.subscribe(e[0]))
        else:
            if not m[1]:
                dList.append(self.proto.create(m[0]))

            if not t[1]:
                dList.append(self.proto.create(t[0]))

            if not e[1]:
                dList.append(self.proto.create(e[0]))


        if len(dList):
            return defer.DeferredList(dList)

    def _folderingFinished(self, results, status):
        m = status[constants.CHANDLER_MAIL_FOLDER]
        t = status[constants.CHANDLER_TASKS_FOLDER]
        e = status[constants.CHANDLER_EVENTS_FOLDER]

        # Store the value of the calback locally since
        # actionCompleted will set self.callback to None
        cb = self.callback
        self._actionCompleted()

        # Pass the IMAP server folder names back to the 
        # caller.
        created = False

        for (name, exists, subscribed) in (m, t, e):
            if not exists or not subscribed:
                created = True
                break

        callMethodInUIThread(cb, ( 1, (m[0], t[0], e[0], created)))

    def _actionCompleted(self):
       # Reset the total downloaded counter
        self.totalDownloaded = 0
        self.totalNewDownloaded = 0
        self.totalUpdateDownloaded = 0
        self.totalIgnoreDownloaded = 0

        super(IMAPClient, self)._actionCompleted()

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

        #Twisted expects 8-bit values so encode the utf-8 username and password
        username = self.account.username.encode("utf-8")

        deferredPassword = self.account.password.decryptPassword()

        def callback(password):
            password = password.encode("utf-8")
            self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
            self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))
    
            return self.proto.authenticate(password
                         ).addCallback(self.cb
                         ).addErrback(self.loginClientInsecure, username, password
                         ).addErrback(self.catchErrors)
         
        return deferredPassword.addCallback(callback
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
                    ).addCallback(self.cb
                    ).addErrback(self.catchErrors)


    def _getMail(self, result):
        if __debug__:
            trace("_getMail")

        if self.cancel:
            return self._actionCompleted()

        if self.account.folders.isEmpty():
            # Since the accounts may have been
            # saved or restored with a
            # pre-Preview version of Chandler,
            # the Mail Service plays nice and
            # adds the Inbox folder to the
            # IMAPAccount. This feature
            # will go away in the future
            # since not having a folder in the
            # IMAP account will signal an 
            # error or a bug.
            from i18n import ChandlerMessageFactory as _
            inbox = IMAPFolder(itsView=self.view)
            inbox.displayName = _(u"Inbox")
            inbox.folderName  = u"INBOX"
            inbox.folderType  = "CHANDLER_HEADERS"
            self.account.folders.append(inbox)
            self.view.commit()

        self.vars = FolderVars()
        self.vars.folderItem = self.account.folders.first()

        d = self.proto.select(self.vars.folderItem.folderName
                   ).addCallback(self._checkForNewMessages
                   ).addErrback(self.catchErrors)

        return d

    def _getNextFolder(self):
        if __debug__:
            trace("_getNextFolder")

        i = self.vars.indexNumber + 1

        # Temp variable needed to get the
        # next folder in the sequence
        f = self.vars.folderItem

        # Free the mem refs of the previous
        # FolderVars instance
        self.vars = None

        # Close the current folder
        d = self.proto.close()

        if i >= len(self.account.folders):
            # All folders for the IMAPAccount have been
            # scanned so call actionCompleted
            if self.statusMessages:
                if self.totalDownloaded > 0:
                    # This is a PyICU.ChoiceFormat class
                    txt = constants.DOWNLOAD_CHANDLER_MESSAGES.format(self.totalDownloaded)

                    setStatusMessage(txt % \
                                     {'accountName': self.account.displayName,
                                      'numberTotal': self.totalDownloaded,
                                      'numberNew': self.totalNewDownloaded,
                                      'numberUpdates': self.totalUpdateDownloaded,
                                      'numberDuplicates': self.totalIgnoreDownloaded})
                else:
                    setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                                    {'accountName': self.account.displayName})

            d.addBoth(lambda x: self._actionCompleted())
            return d

        self.vars = FolderVars()
        self.vars.folderItem  = self.account.folders.next(f)
        self.vars.indexNumber = i

        d.addCallback(lambda x: self.proto.select(self.vars.folderItem.folderName))

        d.addCallback(self._checkForNewMessages)
        d.addErrback(self.catchErrors)

        return d

    def _checkForNewMessages(self, msgs):
        if __debug__:
            trace("_checkForNewMessages")

        #XXX: Need to store and compare UIDVALIDITY.
        #     The issue is what does Chandler do if the
        #     UIDVALIDITY has changed. Not being a
        #     traditional mail client we could not
        #     just refetch the messages since the
        #     Message Items may have changed dramatically
        #     i.e. unstamped as Mail and stamped as an Event
        #     and shared with other users. Or altered as
        #     part of an Edit / Update workflow.
        #     For now UIDVALIDITY will be ignored :(
        #if not msgs['UIDVALIDITY']:
        #    print "server: %s has no UUID Validity:\n%s" % (self.account.host, msgs)

        if self.cancel:
            return self._actionCompleted()

        if msgs['EXISTS'] == 0:
            return self._getNextFolder()

        # Check that we have not already downloaded the max
        # number of messages for the folder
        max = self.vars.folderItem.downloadMax
        downloaded = self.vars.folderItem.downloaded

        if max > 0 and max == downloaded:
            if __debug__:
                trace("Max number of messages %s reached. No new mail will be \
                       downloaded from '%s'" % (max, self.vars.folderItem.displayName))

            return self._getNextFolder()

        lastUID = 1

        if self.vars.getNextUID() > 0:
            lastUID = self.vars.getNextUID()

        msgSet = imap4.MessageSet(lastUID, None)

        if self.vars.folderItem.folderType == "CHANDLER_HEADERS":
            return self.proto.fetchUID(msgSet, uid=1
                    ).addCallbacks(self._searchForChandlerMessages, self.catchErrors)
        else:
            return self.proto.fetchFlags(msgSet, uid=True
                       ).addCallback(self._getMessagesFlagsUID
                       ).addErrback(self.catchErrors)

    def _searchForChandlerMessages(self, msgs):
        if __debug__:
            trace("_searchForChandlerHeaders")

        for uidDict in msgs.values():
           self.vars.searchUIDs.append(int(uidDict['UID']))

        # Sort the uids since the ordering returned from the
        # dict may not be sequential
        self.vars.searchUIDs.sort()

        size = len(self.vars.searchUIDs)


        # Placeholder for displaying additionaly information
        # to the user when searching a folder with a huge number
        # of messages
        #if size > MIN_SEARCH_ALERT:
        #    print "show an alert that messages will take a while to download"

        if size == 0:
            # There are no uids greater than the lastUID so
            # scan the next folder
            return self._getNextFolder()

        if self.statusMessages:
            # This is a PyICU.ChoiceFormat class
            txt = constants.IMAP_SEARCH_MESSAGES.format(size)

            setStatusMessage(txt % \
                             {'accountName': self.account.displayName,
                              'folderDisplayName': self.vars.folderItem.displayName,
                              'numberOfMessages': size})

        # The last position in the sorted searchUIDs list
        # is the highest uid in the folder.
        self.vars.lastUID = self.vars.searchUIDs[size-1]


        # mset will never be None here since the check to
        # make sure the self.vars.searchUIDs list is not
        # empty has already been done a few lines up.

        mset = self._getSearchMessageSet()

        # Find all mail in the folder that contains the header
        # X-Chandler-Mailer: True, does not contain the \Deleted
        # flag and is greater than the IMAP UID of the last
        # message downloaded from the folder.

        query = imap4.Query(header=('X-Chandler-Mailer', 'True'), undeleted=True,
                            uid=mset)

        return self.proto.search(query, uid=1
                        ).addCallbacks(self._findChandlerMessages, \
                                       self.catchErrors)


    def _findChandlerMessages(self, msgUIDs):
        if __debug__:
            trace("_findChandlerMessages")

        for msgUID in msgUIDs:
            # Add all messages that match the
            # search criteria to the foundUIDs
            # list.
            self.vars.foundUIDs.append(msgUID)

        mset = self._getSearchMessageSet()

        if mset:
            query = imap4.Query(header=('X-Chandler-Mailer', 'True'), undeleted=True,
                                uid=mset)

            return self.proto.search(query, uid=1
                        ).addCallbacks(self._findChandlerMessages, \
                                       self.catchErrors)


        # This point is reached when self._getSearchMessageSet()
        # returns None indicating that there are no more message
        # uids to search for Chandler Headers.

        if len(self.vars.foundUIDs) == 0:
            # If the search returned no message uids
            # then first commit the lastUID then
            # scan the next folder
            self.vars.setNextUID(self.vars.lastUID + 1)
            self.view.commit()
            return self._getNextFolder()

        msgSet = imap4.MessageSet()

        for uid in self.vars.foundUIDs:
            msgSet.add(uid)

        # FYI: Since there are messages to download the incrementing of
        # the lastUID to highest uid of the searched messages
        # will automatically get commited.
        return self.proto.fetchFlags(msgSet, uid=True
                   ).addCallbacks(self._getMessagesFlagsUID, \
                                  self.catchErrors)

    def _getSearchMessageSet(self):
        size = len(self.vars.searchUIDs)

        if size == 0:
            return None

        num = size > MAX_SEARCH_NUM and \
              MAX_SEARCH_NUM or \
              size

        mset = imap4.MessageSet()

        for i in xrange(0, num):
            mset.add(self.vars.searchUIDs[i])

        # Reduce the list removing all uids that have been
        # added to the message set
        self.vars.searchUIDs = self.vars.searchUIDs[num:]

        return mset


    def _getMessagesFlagsUID(self, msgs):
        if __debug__:
            trace("_getMessagesFlagsUIDS")

        if self.cancel:
            return self._actionCompleted()

        nextUID = self.vars.getNextUID()

        for message in msgs.itervalues():
            uid = int(message['UID'])

            if uid < nextUID:
                continue

            if not "\\Deleted" in message['FLAGS']:
                self.vars.pending.append([uid, message['FLAGS']])

        numPending = len(self.vars.pending)

        if numPending == 0:
            return self._getNextFolder()

        max = self.vars.folderItem.downloadMax
        downloaded = self.vars.folderItem.downloaded

        if max > 0 and (numPending + downloaded > max):
            # If the number of pending messages exceeds the
            # maximum number of messages that should be downloaded
            # for this folder as specified in c{IMAPFolder.downloadMax}
            # then reduce the pending list to that maximum number.
            #
            # A c{IMAPFolder.downladMax} value <= 0 indicated that
            # there is no limit on the number of messages that
            # can be downloaded from this folder.
            self.vars.pending = self.vars.pending[:max - downloaded]
            numPending = len(self.vars.pending)

        if self.statusMessages:
            # This is a PyICU.ChoiceFormat class
            txt = constants.IMAP_START_MESSAGES.format(numPending)

            setStatusMessage(txt % \
                             {"accountName": self.account.displayName,
                              "numberOfMessages": numPending,
                              "folderDisplayName": self.vars.folderItem.displayName})

        self._getNextMessageSet()

    def _getNextMessageSet(self):
        """
        Overides base class to add IMAP specific logic.

        If the pending queue has one or messages to download
        for n messages up to C{IMAPAccount.commitNumber} fetches
        the mail from the IMAP server. If no message pending
        calls actionCompleted() to clean up client resources.
        """
        if __debug__:
            trace("_getNextMessageSet")

        if self.cancel:
            return self._actionCompleted()

        self.vars.numToDownload = len(self.vars.pending)

        if self.vars.numToDownload == 0:
            return self._getNextFolder()

        if self.vars.numToDownload > self.commitNumber:
            self.vars.numToDownload = self.commitNumber

        m = self.vars.pending.pop(0)

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
        if curMessage[0] > self.vars.lastUID:
            self.vars.lastUID = curMessage[0]

        if  "\\Seen" in curMessage[1]:
            d = defer.succeed(True)
        else:
            d = self.proto.removeFlags(curMessage[0], ["\Seen"], uid=True)

        messageText = msgs[msg]['RFC822']

        #XXX: Need a more performant way to do this
        repMessage = messageTextToKind(self.view, messageText)

        if repMessage:
            # If the message contained an eimml attachment
            # that was older then the current state or
            # contained bogus data then repMessage will be
            # None and the Mail Service will igore the message.

            if repMessage.isAnUpdate():
                # This is an update to an existing Chandler item
                # so increment the updatecounter
                self.totalUpdateDownloaded += 1

            else:
                # This is a new Chandler item so increment the
                # new counter
                self.totalNewDownloaded += 1

            if self.vars.folderItem.folderType == "EVENT":
                parseEventInfo(repMessage)

            elif self.vars.folderItem.folderType == "TASK":
                parseTaskInfo(repMessage)

            repMessage.incomingMessage()

            self.vars.folderItem.downloaded += 1

        else:
            # The message downloaded contained eimml that
            # for what ever reason was ignored.
            self.totalIgnoreDownloaded += 1

        self.vars.numDownloaded += 1

        if self.vars.folderItem.deleteOnDownload:
            # If the user elects to delete mail
            # from the IMAP Server that has been
            # downloaded to Chandler from this
            # IMAP folder then add the message UID
            # to the delete list. The \\Deleted flag
            # flag will be added to the message on the
            # IMAP Server after the corresponding MailStamp
            # has been committed to the Repository.
            self.vars.delList.append(curMessage[0])

        if self.vars.numDownloaded == self.vars.numToDownload:
            # Set the next uid on the IMAPFolder item since
            # this information is about to be committed.
            # The setting of this value is delayed till the
            # last possible point. If an error happens
            # during download we want to make sure that
            # the correct next UID is saved.
            self.vars.setNextUID(self.vars.lastUID + 1)

            # Track the total number of messages downloaded from
            # this IMAP Folder
            self.vars.totalDownloaded += self.vars.numDownloaded

            # Track the total number of messages downloaded for
            # this IMAP Account as well as the total number
            # of new and updated Chandler items.
            self.totalDownloaded += self.vars.numDownloaded

            return d.addBoth(lambda x: self._commitDownloadedMail())

        else:
            m = self.vars.pending.pop(0)

            return d.addBoth(lambda x: self.proto.fetchMessage(str(m[0]), uid=True
                                     ).addCallback(self._fetchMessage, m
                                     ).addErrback(self.catchErrors)
                            )

    def _performNextAction(self):
        if __debug__:
            trace("_performNextAction")

        if self.vars.folderItem.deleteOnDownload and len(self.vars.delList):
            msgSet = imap4.MessageSet()

            for uid in self.vars.delList:
                msgSet.add(uid)

            # Reset the delList
            self.vars.delList = []

            # Since the flags are silent this should never raise an error
            d = self.proto.addFlags(msgSet, ("\\Deleted",), uid=True)

        else:
            d = defer.succeed(True)

        if len(self.vars.pending) == 0:
           # We have downloaded all the pending messages for this folder
            meth = self._getNextFolder
        else:
           # There are more messages to download from this folder
            meth = self._getNextMessageSet

            # Reset the download counter variables
            self.vars.numDownloaded = 0
            self.vars.numToDownload = 0

        return d.addCallback(lambda x: meth())

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

        if self.vars and self.vars.folderItem:
            # If the vars instance is not None and the
            # folderItem is not None then a cancel,
            # shutdown, or error occurred in which case
            # we want to close the open folder
            d = self.proto.close()
            d.addBoth(lambda x: self.proto.sendCommand(imap4.Command('LOGOUT', \
                                wantResponse=('BYE',))))

        else:
             d = self.proto.sendCommand(imap4.Command('LOGOUT', wantResponse=('BYE',)))

        return d

    def _getAccount(self):
        """
        Retrieves a C{IMAPAccount} instance from its C{UUID}.
        """
        if self.account is None:
            self.account = self.view.findUUID(self.accountUUID)

        return self.account
