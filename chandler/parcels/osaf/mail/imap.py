__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.protocol as protocol
import twisted.internet.ssl as ssl
import twisted.mail.imap4 as imap4
import repository.persistence.RepositoryView as RepositoryView
import mx.DateTime as DateTime
import message as message
import sharing as sharing
import email as email
import email.Utils as Utils
import logging as logging
import repository.util.UUID as UUID
import common as common
import repository.item.Query as Query

#XXX: Need to make sure all the flags are in place to prevent a non-ssl session if 
#     ssl required

class ChandlerIMAP4Client(imap4.IMAP4Client):

    def __init__(self, contextFactory=None, useSSL=False):
        imap4.IMAP4Client.__init__(self, contextFactory)
        self.useSSL = useSSL

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.

        It creates a C{defer.Deferred} and adds its factory callback and errorback
        methods to the C{defer.Deferred}.

        @param caps: The list of server CAPABILITIES
        @type caps: dict
        @return C{None}
        """

        if not self.useSSL:
            self.serverCapabilities =  common.disableTwistedTLS(caps)

        self.factory.deferred.callback(self)

        return self.factory.deferred


class ChandlerIMAP4Factory(protocol.ClientFactory):
    protocol = ChandlerIMAP4Client

    def __init__(self, deferred, useSSL=False):
        """
        A C{protocol.ClientFactory} that creates C{ChandlerIMAP4Client} instances
        and stores the callback and errback to be used by the C{ChandlerIMAP4Client} instances

        @param: deferred: A C{defer.Deferred} to callback when connected to the IMAP server 
                          and errback if no connection or command failed
        @type deferred: C{defer.Deferred}
        @return: C{None}
        """

        if not isinstance(deferred, defer.Deferred):
            raise IMAPException("deferred must be a defer.Deferred instance")

        self.deferred = deferred
        self.useSSL = useSSL

    def buildProtocol(self, addr):
        if not self.useSSL:
            p = self.protocol()
        else:
            p = self.protocol(ssl.ClientContextFactory(useM2=1), True)

        p.factory = self
        return p

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)


class IMAPException(common.MailException):
    pass

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

        viewName = "%s_%s" % (account.displayName, str(UUID.UUID()))
        super(IMAPDownloader, self).__init__(Globals.repository, viewName)

        self.proto = None
        self.accountUUID = account.itsUUID
        self.account = None
        self.downloadedStr = None


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

        d = defer.Deferred()
        d.addCallback(self.loginClient)
        d.addErrback(self.catchErrors)

        factory = ChandlerIMAP4Factory(d, useSSL)

        if useSSL:
            reactor.connectSSL(host, port, factory, ssl.ClientContextFactory(useM2=1))
        else:
            reactor.connectTCP(host, port, factory)
 
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

        self.log.error("Twisted Error %s" % error)

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

            return self.proto.login(username, password
                          ).addCallback(self.__selectInbox)


    def __selectInbox(self, result):
        if __debug__:
            self.printCurrentView("selectInbox ***Could be wrong view***")

        self.__printInfo("Checking Inbox for new mail messages")

        return self.proto.select("INBOX").addCallback(self.__checkForNewMessages)

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
                d.addCallback(self.__getMessagesFromUIDS)

                return d

            self.__printInfo("No messages present to download")

        finally:
            self.restorePreviousView()


    def __getMessagesFromUIDS(self, msgs):

        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("getMessagesFromUIDS")

            v = [int(v['UID']) for v in msgs.itervalues()]
            low = min(v)
            high = max(v)

            if high <= self.__getLastUID():
                self.__printInfo("No new messages found")

            else:
                if self.__getLastUID() == 0:
                    msgSet = imap4.MessageSet(low, high)
                else:
                    msgSet = imap4.MessageSet(max(low, self.__getLastUID() + 1), high)

                d = self.proto.fetchMessage(msgSet, uid=True)
                d.addCallback(self.__fetchMessages).addCallback(self.__disconnect)

        finally:
            self.restorePreviousView()

    def __disconnect(self, result = None):

        if __debug__:
            self.printCurrentView("disconnect")

        self.proto.close()
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
            self.view.commit()

            totalDownloaded = 0
            foundInvitation = False
            sharingInvitations = {}
            sharingHeader = sharing.getChandlerSharingHeader() 

            for msg in msgs:

                messageText = msgs[msg]['RFC822']
                uid = long(msgs[msg]['UID'])

                messageObject = email.message_from_string(messageText)

                if messageObject[sharingHeader] is not None:
                    sharingInvitations[uid] = messageObject[sharingHeader]
                    foundInvitation = True
                    continue

                repMessage = message.messageObjectToKind(messageObject, messageText)

                repMessage.incomingMessage(account=self.account)
                repMessage.deliveryExtension.folder = "INBOX"
                repMessage.deliveryExtension.uid = uid

                if uid > self.__getLastUID():
                    self.__setLastUID(uid)
                    totalDownloaded += 1

            self.downloadedStr = "%d messages downloaded to Chandler" % (totalDownloaded)

        finally:
            self.restorePreviousView()

        """Commit the view in a thread to prevent blocking"""
        self.commitView(True)

        if foundInvitation:
            uids = ','.join(map(str, sharingInvitations.keys()))

            return self.proto.setFlags(uids, ['\\Deleted'], uid=True
                              ).addCallback(self._expunge
                              ).addCallback(self._processSharingRequests,
                                            sharingInvitations.values())

    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{EmailAccountKind} from
        memory, and writes commit info to the logger
        @return: C{None}
        """

        Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

        self.__printInfo(self.downloadedStr)
        self.downloadedStr = None

        self.account.setPinned(False)
        self.account = None

    def _expunge(self, result):
        if __debug__:
            self.printCurrentView("_expunge")

        return self.proto.expunge()

    def _processSharingRequests(self, result, urls):
        if __debug__:
            self.printCurrentView("_processSharingRequests")

        sharing.receivedInvitation(urls)

    def __getLastUID(self):
        return self.account.messageDownloadSequence

    def __setLastUID(self, uid):
        self.account.messageDownloadSequence = uid

    def __getAccount(self):

        accountKind = Mail.MailParcel.getIMAPAccountKind()
        self.account = accountKind.findUUID(self.accountUUID)

        if self.account is None: 
            raise IMAPException("No Account for UUID: %s"% self.account.itsUUID)

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
        if not isinstance(UUID.UUID):
            raise IMAPException("The UUID argument must be of type UUID.UUID")

        account = accountKind.findUUID(UUID)

    else:
        for acc in Query.KindQuery().run([accountKind]):
            account = acc
            break

    if account is None:
        raise IMAPException("No IMAP Account exists in Repository")

    return account
