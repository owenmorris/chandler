__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.protocol as protocol
import twisted.python.failure as failure
import twisted.internet.error as error
import twisted.mail.imap4 as imap4
import twisted.protocols.policies as policies

#python / mx imports
import mx.DateTime as DateTime
import email as email
import logging as logging

#Chandler imports
import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import chandlerdb.util.UUID as UUID
import repository.item.Query as Query
import osaf.contentmodel.mail.Mail as Mail
import application.Globals as Globals
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL as SSL

#Chandler Mail Service imports
import message as message
import sharing as sharing
import errors as errors
import constants as constants
import utils as utils

"""
  Bug:
    TODO:
    1. Print warning message if UID validity is bad (Where to store UID Validity 
       since on folder)
    2. Batch fetch of 30 messages followed by commit and memory clear and prune
    3. Keep \\Deleted flags in sync with IMAP Server

    FUTURE:
    1. Look in to pluging the Python email 3.0 Feedparser in to the
       rawDataReceived method of IMAP4Client for better performance.
"""

class ChandlerIMAP4Client(imap4.IMAP4Client):
    timeout = constants.TIMEOUT

    def serverGreeting(self, caps):
        """
        This method overides C{imap4.IMAP4Client}.

        It calls back the factory registered deferred passing a reference to self(protocol) and
        a reference to the Server capbilities

        @param caps: The list of server CAPABILITIES
        @type caps: dict
        @return C{None}
        """

        self.factory.imapDownloader.proto = self

        if caps is None:
            d = self.getCapabilities()

            """If no capabilities returned in server greeting then get
               the server capabilities to remove STARTTLS if not
               in TLS mode"""
            d.addCallbacks(self.__getCapabilities, self.factory.imapDownloader.catchErrors)

            return d

        self.__getCapabilities(caps)

    def timeoutConnection(self):
        """Called by C{policies.TimeoutMixin} base class.
           If the connection is not Done the method will
           errback a C{IMAPException}
        """
        exc = errors.IMAPException("Communication with IMAP Server timed out. Please try again later.")
        self.factory.imapDownloader.catchErrors(exc)

    def __getCapabilities(self, caps):
        self._capCache = utils.disableTwistedTLS(caps)
        self.factory.imapDownloader.loginClient()


class ChandlerIMAP4Factory(protocol.ClientFactory):
    protocol = ChandlerIMAP4Client

    def __init__(self, imapDownloader):
        """
        @return: C{None}
        """
        self.imapDownloader = imapDownloader
        self.connectionLost = False
        self.sendFinished = 0

        retries = self.imapDownloader.account.numRetries

        assert isinstance(retries, (int, long))
        self.retries = -retries

    def clientConnectionFailed(self, connector, err):
        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        self._processConnectionError(connector, err)

    def _processConnectionError(self, connector, err):
        self.connectionLost = True

        if self.retries < self.sendFinished <= 0:
            logging.info("IMAP Client Retrying server. Retry: %s" % -self.retries)
            connector.connect()
            self.retries += 1

        elif self.sendFinished <= 0:
            if err.check(error.ConnectionDone):
                err.value = errors.IMAPException( \
                            "Unable to connect to IMAP server. Please try again later.")

            self.imapDownloader.catchErrors(err)


class IMAPDownloader(TwistedRepositoryViewManager.RepositoryViewManager):

    def __init__(self, repository, account):
        """
        Creates a C{IMAPDownload} instance
        @param account: An Instance of C{IMAPAccount}
        @type account: C{IMAPAccount}
        @return: C{None}
        """
        assert account is not None, "You must pass in an IMAPAccount instance"

        viewName = "%s_%s_%s" % (account.displayName, str(UUID.UUID()), DateTime.now())
        super(IMAPDownloader, self).__init__(repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.downloadedStr = None
        self.factory = None
        self.proto = None

        """
           KEY: UID
           Value: [FLAGS, MaiMessage]
        """
        self.messages = {}
        self.numMessages = 0
        self.totalDownloaded = 0
        self.lastUID = 0

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

        """Move code execution path from current thread in to the Reactor Asynch thread"""
        reactor.callFromThread(self.execInView, self.__getMail)

    def __getMail(self):
        if __debug__:
            self.printCurrentView("__getMail")

        self.__getAccount()

        self.factory = ChandlerIMAP4Factory(self)

        self.wrappingFactory = policies.WrappingFactory(self.factory)
        self.wrappingFactory.protocol = wrapper.TLSProtocolWrapper
        self.factory.startTLS = self.account.useSSL
        self.factory.getContext = lambda : Globals.crypto.getSSLContext()
        self.factory.sslChecker = SSL.Checker.Checker()
        reactor.connectTCP(self.account.host, self.account.port, self.wrappingFactory)

    def catchErrors(self, err):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread.
        @return: C{None}
        """

        if isinstance(err, failure.Failure):
            err = err.value

        if __debug__:
            self.printCurrentView("catchErrors: %s " % str(err))

        if not self.factory.connectionLost:
            self.__disconnect()

        #XXX: When IMAP Errors are saved to Repository will need to
        #     wait for commit to complete before doing a Notification
        utils.NotifyUIAsync(_("Error: %s") % err, self.log.error, alert=True)

    def loginClient(self):
        """
        This method is a Twisted C{defer.Deferred} callback that logs in to an IMAP Server
        based on the account information stored in a C{EmailAccountKind}.
        @return: C{None}
        """
        self.execInView(self.__loginClient)

    def __loginClient(self):
        if __debug__:
            self.printCurrentView("__loginClient")

        assert self.account is not None, "Account is None can not login client"

        username = self.account.username.encode(constants.DEFAULT_CHARSET)
        password = self.account.password.encode(constants.DEFAULT_CHARSET)

        self.proto.registerAuthenticator(imap4.CramMD5ClientAuthenticator(username))
        self.proto.registerAuthenticator(imap4.LOGINAuthenticator(username))

        return self.proto.authenticate(password
                     ).addCallback(self.__selectInbox
                     ).addErrback(self.loginClientInsecure, username, password)


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

        utils.NotifyUIAsync(_("Checking Inbox for new mail messages"), self.__printInfo)

        return self.proto.select("INBOX").addCallbacks(self.__checkForNewMessages, self.catchErrors)

    def __checkForNewMessages(self, msgs):
        if __debug__:
            self.printCurrentView("checkForNewMessages")

        #XXX: Store and compare msgs['UIDVALIDITY']

        exists = msgs['EXISTS']

        if exists != 0:
            """ Fetch everything newer than the last UID we saw. """
            if self.__getNextUID() == 0:
                 msgSet = imap4.MessageSet(1, None)
            else:
                 msgSet = imap4.MessageSet(self.__getNextUID(), None)

            d = self.proto.fetchFlags(msgSet, uid=True)

            d.addCallback(self.__getMessagesFlagsUID).addErrback(self.catchErrors)

            return d

        self.__noMessages()

    def __getMessagesFlagsUID(self, msgs):
        if __debug__:
            self.printCurrentView("getMessagesFlagsUIDS")

        if len(msgs.keys()) == 0:
            return self.__noMessages()

        uidList = []

        for message in msgs.itervalues():
            uid = message['UID']
            luid = long(uid)

            if luid < self.__getNextUID():
                continue

            if luid > self.lastUID:
                self.lastUID = luid

            if not "\\Deleted" in message['FLAGS']:
                self.messages[uid] = [message['FLAGS']]
                uidList.append(luid)


        self.numMessages = len(uidList)

        if self.numMessages == 0:
            return self.__noMessages()

        """Sort the uid's from lowest to highest"""
        uidList.sort()

        for uid in uidList:
            d = self.proto.fetchMessage(str(uid), uid=True)
            d.addCallback(self.__fetchMessage).addErrback(self.catchErrors)

    def __noMessages(self):
        self.__disconnect()
        utils.NotifyUIAsync(_("No new messages found"), self.__printInfo)
        return None

    def __disconnect(self, result=None):
        if __debug__:
            self.printCurrentView("__disconnect")

        self.factory.sendFinished = 1

        if self.proto is not None:
            self.proto.transport.loseConnection()

    def __fetchMessage(self, msgs):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("fetchMessage")

            """ Refresh our view before adding items to our mail account
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """
            self.view.refresh()

            msg = msgs.keys()[0]

            messageText = msgs[msg]['RFC822']
            strUID = msgs[msg]['UID']
            uid = long(strUID)

            messageObject = email.message_from_string(messageText)

            repMessage = message.messageObjectToKind(self.getCurrentView(),
                                                     messageObject, messageText)

            """Set the message as incoming"""
            repMessage.incomingMessage(account=self.account)

            """Save IMAP Delivery info in Repository"""
            repMessage.deliveryExtension.folder = "INBOX"
            repMessage.deliveryExtension.uid = uid
            repMessage.deliveryExtension.flags = self.messages[strUID][0]

            self.messages[strUID].append(repMessage)
            self.totalDownloaded += 1

        finally:
            self.restorePreviousView()

        if self.totalDownloaded == self.numMessages:
            self.__setNextUID(self.lastUID + 1)
            self.downloadedStr = _("%d messages downloaded to Chandler") % \
                                   (self.totalDownloaded)
            self.__disconnect()
            self.commitInView(True)


    def _viewCommitSuccess(self):
        """
        Overides C{RepositoryView.AbstractRepositoryViewManager}.
        It posts a commit event to the GUI thread, unpins the C{EmailAccountKind} from
        memory, and writes commit info to the logger
        @return: C{None}
        """

        utils.NotifyUIAsync(self.downloadedStr, self.__printInfo)
        self.downloadedStr = None
        self.account = None

    def __expunge(self, result):
        if __debug__:
            self.printCurrentView("_expunge")

        return self.proto.expunge()

    def __getNextUID(self):
        return self.account.messageDownloadSequence

    def __setNextUID(self, uid):
        self.account.messageDownloadSequence = uid

    def __getAccount(self):
        self.account = Mail.MailParcel.getIMAPAccount(self.getCurrentView(),
                                                      self.accountUUID)

    def __printInfo(self, info):

        if self.account.port != 143:
            str = "[Server: %s:%d User: %s] %s" % (self.account.host,
                                                   self.account.port,
                                                   self.account.username, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.host,
                                                self.account.username, info)

        self.log.info(str)


