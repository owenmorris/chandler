__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.protocol as protocol
import twisted.protocols.imap4 as imap4
import repository.persistence.RepositoryView as RepositoryView
import mx.DateTime as DateTime
import message as message
import email as email
import email.Utils as Utils
import logging as logging
import repository.util.UUID as UUID


class ChandlerIMAP4Client(imap4.IMAP4Client):

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.

        It creates a C{defer.Deferred} and adds its factory callback and errorback
        methods to the C{defer.Deferred}.

        @param caps: The list of server CAPABILITIES
        @type caps: dict
        @return C{None}
        """

        self.serverCapabilities =  self.__disableTLS(caps)

        d = defer.Deferred()
        d.addCallback(self.factory.callback, self)
        d.addErrback(self.factory.errback)

        d.callback(True)


    def __disableTLS(self, caps):
        """Disables SSL support for debugging so
           a tcpflow trace can be done on the Client / Server
           command exchange"""

        if caps != None:
            try:
                del caps["STARTTLS"]

            except KeyError:
                pass

        return caps


class ChandlerIMAP4Factory(protocol.ClientFactory):
    protocol = ChandlerIMAP4Client

    def __init__(self, callback, errback):
        """
        A C{protocol.ClientFactory} that creates C{ChandlerIMAP4Client} instances
        and stores the callback and errback to be used by the C{ChandlerIMAP4Client} instances

        @param callback: A method name to call when a C{ChandlerIMAP4Client} connects
                        to a IMAP Server
        @type callback: string
        @param errback: A method name to call if an error is thrown in the C{ChandlerIMAPClient}
                        C{defer.Deferred} callback chain
        @type errback: string
        @return: C{None}
        """

        self.callback = callback
        self.errback = errback

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        return p

    def clientConnectionFailed(self, connector, reason):
        logging.error("Unable to connect to server; reason: '%s'", reason)


class MailException(Exception):
    pass

class IMAPDownloader(RepositoryView.AbstractRepositoryViewManager):

    def __init__(self, account):
        """
        Creates a C{IMAPDownload} instance
        @param account: An Instance of C{EmailAccountKind}
        @type account: C{EmailAccountKind}
        @return: C{None}
        """

        if account is None:
            raise MailException("You must pass in a Mail Account instance")

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

            self.account = self.__getAccount()
            assert self.account is not None, "Account is None"

            self.account.setPinned()

            serverName = self.account.serverName
            serverPort = self.account.serverPort

            if __debug__: 
                self.printAccount()

        finally:
            self.restorePreviousView()

        factory = ChandlerIMAP4Factory(self.loginClient, self.catchErrors)
        reactor.connectTCP(serverName, serverPort, factory)
 
    def printAccount(self):
        """
        Utility method that prints out C{EmailAccountKind} information for debugging
        purposes
        @return: C{None}
        """

        self.printCurrentView("printAccount")

        if self.account is None:
            return

        str  = "\nHost: %s\n" % self.account.serverName
        str += "Port: %d\n" % self.account.serverPort
        str += "Username: %s\n" % self.account.accountName
        str += "Password: %s\n" % self.account.password

        self.log.info(str)

    def catchErrors(self, result):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread.
        @return: C{None}
        """

        self.log.error("Twisted Error %s" % result)

    def loginClient(self, result, proto):
        """
        This method is a Twisted C{defer.Deferred} callback that logs in to an IMAP Server
        based on the account information stored in a C{EmailAccountKind}.

        @param result: A Twisted callback result 
        @type result: Could be anything
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

            """ Login using plain text login """

            assert self.account is not None, "Account is None can not login client"

            return self.proto.login(str(self.account.accountName), 
                                    str(self.account.password)).addCallback(self.__selectInbox)
        finally:
           self.restorePreviousView()


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

            for msg in msgs:
                repMessage = message.make_message(msgs[msg]['RFC822'])
                self.account.downloadedMail.append(repMessage)

                uid = long(msgs[msg]['UID'])

                if uid > self.__getLastUID():
                    self.__setLastUID(uid)
                    totalDownloaded += 1

            self.downloadedStr = "%d messages downloaded to Chandler" % (totalDownloaded)

        finally:
            self.restorePreviousView()

        """Commit the view in a thread to prevent blocking""" 
        self.commitView(True)


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


    def __getLastUID(self):
        return self.account.messageDownloadSequence

    def __setLastUID(self, uid):
        self.account.messageDownloadSequence = uid

    def __getAccount(self):

        accountKind = Mail.MailParcel.getEmailAccountKind()
        account = accountKind.findUUID(self.accountUUID)

        if account is None: 
            self.log.error("No Account for UUID: %s"% self.account.itsUUID)

        return account

    def __printInfo(self, info):

        if self.account.serverPort != 143:
            str = "[Server: %s:%d User: %s] %s" % (self.account.serverName,
                                                   self.account.serverPort, 
                                                   self.account.accountName, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.serverName,
                                                self.account.accountName, info)

        self.log.info(str)
