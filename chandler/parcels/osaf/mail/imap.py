__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.protocol as protocol
import twisted.protocols.policies as policies
import twisted.python.failure as failure
import twisted.internet.ssl as ssl
import twisted.internet.error as error
import twisted.mail.imap4 as imap4
import repository.persistence.RepositoryView as RepositoryView
import mx.DateTime as DateTime
import message as message
import sharing as sharing
import email as email
import email.Utils as Utils
import logging as logging
import chandlerdb.util.UUID as UUID
import common as common
import repository.item.Query as Query

"""
   Notes:
   ------
   1. Move event notification in to a listener class outside of main mail code
      this will break the mails api's dependence on CPIA
   2. Perhaps should show invitations inline before all IMAP cleaning for performance
"""

def NotifyUIAsync(message, logger=logging.info, **keys):
    """Temp method for posting a event to the CPIA layer. This
       method will be refactored soon"""
    logger(message)
    if Globals.wxApplication is not None: # test framework has no wxApplication
        Globals.wxApplication.CallItemMethodAsync(Globals.mainView,
                                                  'setStatusMessage',
                                                   message, **keys)

class IMAPException(common.MailException):
    """Base class for all Chandler IMAP based exceptions"""
    pass

class ChandlerIMAP4Client(imap4.IMAP4Client, policies.TimeoutMixin):

    """The number of seconds before calling C{self.timeout}"""
    timeout = 25 #seconds

    def __init__(self, contextFactory=None):
        imap4.IMAP4Client.__init__(self, contextFactory)

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           If the connection is not Done the method will
           errbacki a C{IMAPException}
        """

        if __debug__:
           self.factory.log.info("timeoutConnection method called")

        if not self.factory.done:
            exc = IMAPException("Communication with IMAP Server timed out. Please try again later.")
            self.factory.deferred.errback(exc)

    def connectionMade(self):
        """Sets the timeout timer then calls
           C{twisted.mail.imap4.IMAP4Client.connectionMade}
        """
        self.setTimeout(self.timeout)
        imap4.IMAP4Client.connectionMade(self)

    def sendLine(self, line):
        """Resets the timeout timer then calls
           C{twisted.mail.imap4.IMAP4Client.sendLine}
        """
        self.resetTimeout()

        """This method utilized for debugging SSL IMAP4 Communications"""
        if __debug__ and self.factory.useSSL:
            self.factory.log.info(">>> %s" % line)

        imap4.IMAP4Client.sendLine(self, line)

    def lineReceived(self, line):
        """Resets the timeout timer then calls
           C{twisted.mail.imap4.IMAP4Client.lineReceived}
        """
        self.resetTimeout()

        """This method utilized for debugging SSL IMAP4 Communications"""
        if __debug__ and self.factory.useSSL:
            self.factory.log.info("<<< %s" % line)

        imap4.IMAP4Client.lineReceived(self, line)

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.

        It creates a C{defer.Deferred} and adds its factory callback and errorback
        methods to the C{defer.Deferred}.

        @param caps: The list of server CAPABILITIES
        @type caps: dict
        @return C{None}
        """

        if caps is None:
            d = self.getCapabilities()

            """If no capabilities returned in server greeting then get
               the server capabilities to remove STARTTLS if not
               in TLS mode"""
            d.addCallbacks(self.__getCapabilities, self.__imap4Error)

            return d

        self.__getCapabilities(caps)

    def __imap4Error(self, error):
        self.factory.deferred.errback(error)

    def __getCapabilities(self, caps):

        if not self.factory.useSSL:
            self._capCache = common.disableTwistedTLS(caps)
        else:
            self._capCache = caps

        self.factory.deferred.callback(self)

        return self.factory.deferred


class ChandlerIMAP4Factory(protocol.ClientFactory):
    protocol = ChandlerIMAP4Client

    def __init__(self, deferred, log, useSSL=False):
        """
        A C{protocol.ClientFactory} that creates C{ChandlerIMAP4Client} instances
        and stores the callback and errback to be used by the C{ChandlerIMAP4Client} instances

        @param: deferred: A C{defer.Deferred} to callback when connected to the IMAP server 
                          and errback if no connection or command failed
        @type deferred: C{defer.Deferred}

        @param: useSSL: A boolean to indicate whether to run in SSL mode
        @type useSSL: C{boolean}

        @return: C{None}
        """
        if not isinstance(deferred, defer.Deferred):
            raise IMAPException("deferred must be a defer.Deferred instance")

        self.deferred = deferred
        self.useSSL = useSSL
        self.log = log
        self.done = False
        self.connectionLost = False

    def buildProtocol(self, addr):
        if not self.useSSL:
            p = self.protocol()
        else:
            p = self.protocol(ssl.ClientContextFactory(useM2=1))

        p.factory = self
        return p

    def clientConnectionFailed(self, connector, err):
        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        self._processConnectionError(connector, err)

    #XXX: put retry logic here
    def _processConnectionError(self, connector, err):
        self.connectionLost = True

        if not self.done:
            if isinstance(err.value, error.ConnectionDone):
                err.value = IMAPException( "Unable to connect to IMAP server. Please try again later.")

            self.deferred.errback(err.value)

class IMAPDownloader(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self, account):
        """
        Creates a C{IMAPDownload} instance
        @param account: An Instance of C{IMAPAccount}
        @type account: C{IMAPAccount}
        @return: C{None}
        """

        if account is None or not account.isItemOf(Mail.MailParcel.getIMAPAccountKind()):
            raise IMAPMailException("You must pass in a IMAPAccount instance")

        viewName = "%s_%s_%s" % (account.displayName, str(UUID.UUID()), DateTime.now())
        super(IMAPDownloader, self).__init__(Globals.repository, viewName)

        self.proto = None
        self.accountUUID = account.itsUUID
        self.account = None
        self.downloadedStr = None
        self.factory = None


    def getMail(self):
        """
        This method retrieves all mail in an IMAP Server INBOX that has a
        UID (RFC3501) greater than the UID of the last message downloaded.

        If this is the first time downloading mail, all mail in the INBOX will
        be downloaded. On the next check only mail greater than the last UID
        will be downloaded.

        This method is executed in the current thread and calls C{reactor.callFromThread}
        to utilize a C{imap4.IMAP4Client} via the C{TwistedReactorManager} to connect to an
        IMAP Server.

        @return: C{None}

        """
        if __debug__:
            self.printCurrentView("getMail")

        reactor.callFromThread(self.__getMail)

    def __getMail(self):

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__getMail")

            self.__getAccount()

            host    = self.account.host
            port    = self.account.port
            useSSL  = self.account.useSSL

        finally:
            self.restorePreviousView()

        d = defer.Deferred().addCallbacks(self.loginClient, self.catchErrors)

        self.factory = ChandlerIMAP4Factory(d, self.log, useSSL)

        if useSSL:
            reactor.connectSSL(host, port, self.factory, ssl.ClientContextFactory(useM2=1))
        else:
            reactor.connectTCP(host, port, self.factory)

    def printAccount(self):
        """
        Utility method that prints out C{IMAPAccount} information for debugging
        purposes
        @return: C{None}
        """

        self.printCurrentView("printAccount")

        if self.account is None:
            return

        str  = "\nHost: %s\n" % self.account.host
        str += "Port: %d\n" % self.account.port
        str += "SSL: %s\n" % self.account.useSSL
        str += "Username: %s\n" % self.account.username
        str += "Password: %s\n" % self.account.password

        self.log.info(str)

    def catchErrors(self, error):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread.
        @return: C{None}
        """
        if __debug__:
            self.printCurrentView("catchErrors")

        self._setDone()

        if not self.factory.connectionLost:
            self.__disconnect()

        NotifyUIAsync(_("Error: %s") % error.value, self.log.error, alert=True)

        """Continue the errback chain"""
        return error


    def loginClient(self, proto):
        """
        This method is a Twisted C{defer.Deferred} callback that logs in to an IMAP Server
        based on the account information stored in a C{EmailAccountKind}.

        @param proto: The C{ChandlerIMAP4Client} protocol instance
        @type proto: C{ChandlerIMAP4Client}
        @return: C{None}
        """

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("loginClient")

            """ Save the IMAP4Client instance """
            self.proto = proto

            assert self.account is not None, "Account is None can not login client"

            username = str(self.account.username)
            password = str(self.account.password)

            self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
            self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))

            return self.proto.authenticate(password
                         ).addCallback(self.__selectInbox
                         ).addErrback(self.loginClientInsecure, username, password)

        finally:
            self.restorePreviousView()

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
            self.printCurrentView("selectInbox ***Could be wrong view***")

        NotifyUIAsync(_("Checking Inbox for new mail messages"), self.__printInfo)

        return self.proto.select("INBOX").addCallbacks(self.__checkForNewMessages, self.catchErrors)

    def __checkForNewMessages(self, msgs):

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("checkForNewMessages")

            exists = msgs['EXISTS']

            if exists != 0:
                """ Fetch everything newer than the last UID we saw. """

                if self.__getLastUID() == 0:
                    msgSet = imap4.MessageSet(1, None)
                else:
                    msgSet = imap4.MessageSet(self.__getLastUID(), None)

                d = self.proto.fetchUID(msgSet, uid=True)
                d.addCallbacks(self.__getMessagesFromUIDS, self.catchErrors)

                return d

            else:
                self._setDone()
                self.__disconnect()
                NotifyUIAsync(_("No messages present to download"), self.__printInfo)

        finally:
            self.restorePreviousView()


    def __getMessagesFromUIDS(self, msgs):

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("getMessagesFromUIDS")

            try:
                v = [int(v['UID']) for v in msgs.itervalues()]

                low = min(v)
                high = max(v)

            except:
                str = "The IMAP Server returned invalid information"
                self.catchErrors(failure.Failure(IMAPException(str)))
                return

            if high <= self.__getLastUID():
                self._setDone()
                self.__disconnect()
                NotifyUIAsync(_("No new messages found"), self.__printInfo)

            else:
                if self.__getLastUID() == 0:
                    msgSet = imap4.MessageSet(low, high)
                else:
                    msgSet = imap4.MessageSet(max(low, self.__getLastUID() + 1), high)

                d = self.proto.fetchMessage(msgSet, uid=True)
                d.addCallbacks(self.__fetchMessages, self.catchErrors)

        finally:
            self.restorePreviousView()

    def _setDone(self, result=None):
        if __debug__:
            self.printCurrentView("_setDone")

        self.factory.done = True

    def __disconnect(self, result=None):

        if __debug__:
            self.printCurrentView("__disconnect")

        self.proto.transport.loseConnection()

    def __fetchMessages(self, msgs):

        if __debug__:
            self.printCurrentView("fetchMessages")

        assert self.account is not None, "Can not fetchMessages Email Account is None"

        self.setViewCurrent()

        try:
            """ Refresh our view before adding items to our mail account
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.refresh()

            totalDownloaded = 0
            foundInvitation = False
            sharingInvitations = {}
            sharingHeader = sharing.getChandlerSharingHeader()
            div = sharing.SharingConstants.SHARING_DIVIDER

            for msg in msgs:

                messageText = msgs[msg]['RFC822']
                uid = long(msgs[msg]['UID'])

                messageObject = email.message_from_string(messageText)

                if messageObject[sharingHeader] is not None:
                    url, collectionName = messageObject[sharingHeader].split(div)
                    fromAddress = messageObject['From']
                    sharingInvitations[uid] = (url, collectionName, fromAddress)
                    foundInvitation = True
                    continue

                repMessage = message.messageObjectToKind(messageObject, messageText)

                repMessage.incomingMessage(account=self.account)
                repMessage.deliveryExtension.folder = "INBOX"
                repMessage.deliveryExtension.uid = uid

                if uid > self.__getLastUID():
                    self.__setLastUID(uid)
                    totalDownloaded += 1

            self.downloadedStr = _("%d messages downloaded to Chandler") % (totalDownloaded)

        finally:
            self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)

        if foundInvitation:
            uids = ','.join(map(str, sharingInvitations.keys()))

            return self.proto.setFlags(uids, ['\\Deleted'], uid=True
                              ).addCallback(self._expunge
                              ).addCallback(self._setDone
                              ).addCallback(self.__disconnect
                              ).addCallback(self._processSharingRequests,
                                            sharingInvitations.values()
                              ).addErrback(self.catchErrors)


        else:
            self._setDone()
            self.__disconnect()

    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{EmailAccountKind} from
        memory, and writes commit info to the logger
        @return: C{None}
        """

        Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

        NotifyUIAsync(self.downloadedStr, self.__printInfo)
        self.downloadedStr = None

        if not self.account.itsView.isRefCounted():
            self.account.setPinned(False)
        self.account = None

    def _expunge(self, result):
        if __debug__:
            self.printCurrentView("_expunge")

        return self.proto.expunge()

    def _processSharingRequests(self, result, invites):
        if __debug__:
            self.printCurrentView("_processSharingRequests")

        for invite in invites:
            url, collectionName, fromAddress = invite

            if __debug__:
                s = "url: %s collectionName: %s fromAddress: %s" % (url, collectionName, fromAddress)
                self.log.info(s)

            sharing.receivedInvitation(url, collectionName, fromAddress)

    def __getLastUID(self):
        return self.account.messageDownloadSequence

    def __setLastUID(self, uid):
        self.account.messageDownloadSequence = uid

    def __getAccount(self):

        self.account = getIMAPAccount(self.accountUUID)
        if not self.account.itsView.isRefCounted():
            self.account.setPinned()


    def __printInfo(self, info):

        if self.account.port != 143:
            str = "[Server: %s:%d User: %s] %s" % (self.account.host,
                                                   self.account.port,
                                                   self.account.username, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.host,
                                                self.account.username, info)

        self.log.info(str)


def getIMAPAccount(UUID=None):
    """
    This method returns a C{IMAPAccount} in the Repository. If UUID is not
    None will try and retrieve the C{IMAPAccount} that has the UUID passed.
    Otherwise the method will try and retrieve the first C{IMAPAccount}
    found in the Repository.

    It will throw a C{IMAPException} if there is either no C{IMAPAccount}
    matching the UUID passed or if there is no C{IMAPAccount}
    at all in the Repository.

    @param UUID: The C{UUID} of the C{IMAPAccount}. If no C{UUID} passed will return
                 the first C{IMAPAccount}
    @type UUID: C{UUID}
    @return C{IMAPAccount}
    """

    accountKind = Mail.MailParcel.getIMAPAccountKind()
    account = None

    if UUID is not None:
        account = accountKind.findUUID(UUID)

    else:
        for acc in Query.KindQuery().run([accountKind]):
            account = acc
            break

    if account is None:
        message = _("No IMAP Account exists in Repository")
        NotifyUIAsync(message, alert=True)
        raise IMAPException(message)

    return account
