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
import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import crypto.ssl as ssl
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper

#Chandler Mail Service imports
import message as message
import sharing as sharing
import errors as errors
import constants as constants
import utils as utils

"""
  Bug:
   1. If the server times out which fetching messages the last UID can get lost
      should set last uid locally before fetch then save on commit to prevent
      change if no messages downloaded
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
                err.value = errors.IMAPException( "Unable to connect to IMAP server. Please try again later.")

            self.imapDownloader.catchErrors(err)


class IMAPDownloader(TwistedRepositoryViewManager.RepositoryViewManager):

    def __init__(self, account):
        """
        Creates a C{IMAPDownload} instance
        @param account: An Instance of C{IMAPAccount}
        @type account: C{IMAPAccount}
        @return: C{None}
        """
        assert account is not None, "You must pass in an IMAPAccount instance"

        viewName = "%s_%s_%s" % (account.displayName, str(UUID.UUID()), DateTime.now())
        super(IMAPDownloader, self).__init__(Globals.repository, viewName)

        self.accountUUID = account.itsUUID
        self.account = None
        self.downloadedStr = None
        self.factory = None
        self.proto = None


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
        self.factory.getContext = lambda : ssl.getSSLContext()
        reactor.connectTCP(self.account.host, self.account.port, self.wrappingFactory)

    def catchErrors(self, err):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread.
        @return: C{None}
        """
        if __debug__:
            self.printCurrentView("catchErrors")

        if isinstance(err, failure.Failure):
            err = err.value

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

        username = str(self.account.username)
        password = str(self.account.password)

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

        exists = msgs['EXISTS']

        if exists != 0:
            """ Fetch everything newer than the last UID we saw. """

            if self.__getLastUID() == 0:
                msgSet = imap4.MessageSet(1, None)
            else:
                msgSet = imap4.MessageSet(self.__getLastUID(), None)

            d = self.proto.fetchUID(msgSet, uid=True)
            d.addCallback(self.execInViewDeferred, self.__getMessagesFromUIDS).addErrback(self.catchErrors)

            return d

        else:
            self.__disconnect()
            utils.NotifyUIAsync(_("No messages present to download"), self.__printInfo)


    def __getMessagesFromUIDS(self, msgs):

        if __debug__:
            self.printCurrentView("getMessagesFromUIDS")

        try:
            v = [int(v['UID']) for v in msgs.itervalues()]

            low = min(v)
            high = max(v)

        except:
            str = "The IMAP Server returned invalid information"
            self.catchErrors(errors.IMAPException(str))
            return

        if high <= self.__getLastUID():
            self.__disconnect()
            utils.NotifyUIAsync(_("No new messages found"), self.__printInfo)

        else:
            if self.__getLastUID() == 0:
                msgSet = imap4.MessageSet(low, high)
            else:
                msgSet = imap4.MessageSet(max(low, self.__getLastUID() + 1), high)

            d = self.proto.fetchMessage(msgSet, uid=True)
            d.addCallback(self.execInViewThenCommitInThreadDeferred, self.__fetchMessages
             ).addErrback(self.catchErrors)

    def __disconnect(self, result=None):

        if __debug__:
            self.printCurrentView("__disconnect")

        self.factory.sendFinished = 1
        self.proto.transport.loseConnection()

    def __fetchMessages(self, msgs):

        if __debug__:
            self.printCurrentView("fetchMessages")

        """ Refresh our view before adding items to our mail account
            and commiting. Will not cause merge conflicts since
            no data changed in view in yet """
        self.view.refresh()

        totalDownloaded = 0
        foundInvitation = False
        sharingInvitations = {}
        sharingHeader = sharing.getChandlerSharingHeader()
        div = constants.SHARING_DIVIDER

        for msg in msgs:
            messageText = msgs[msg]['RFC822']
            uid  = long(msgs[msg]['UID'])

            try:
                flags = msgs[msg]['FLAGS']
            except KeyError:
                flags = []

            messageObject = email.message_from_string(messageText)

            if messageObject[sharingHeader] is not None:
                url, collectionName = messageObject[sharingHeader].split(div)
                fromAddress = messageObject['From']
                sharingInvitations[uid] = (url, collectionName, fromAddress)
                foundInvitation = True
                continue

            repMessage = message.messageObjectToKind(messageObject, messageText)

            """Set the message as incoming"""
            repMessage.incomingMessage(account=self.account)

            """Save IMAP Delivery info in Repository"""
            repMessage.deliveryExtension.folder = "INBOX"
            repMessage.deliveryExtension.uid = uid

            for flag in flags:
                repMessage.deliveryExtension.flags.append(flag)

            if uid > self.__getLastUID():
                self.__setLastUID(uid)
                totalDownloaded += 1

        self.downloadedStr = _("%d messages downloaded to Chandler") % (totalDownloaded)

        if foundInvitation:
            uids = ','.join(map(str, sharingInvitations.keys()))

            return self.proto.setFlags(uids, ['\\Deleted'], uid=True
                              ).addCallback(self.__expunge
                              ).addCallback(self.__disconnect
                              ).addCallback(self.__processSharingRequests,
                                            sharingInvitations.values()
                              ).addErrback(self.catchErrors)
        else:
            self.__disconnect()

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

    def __processSharingRequests(self, result, invites):
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
        self.account = Mail.MailParcel.getIMAPAccount(self.accountUUID)

    def __printInfo(self, info):

        if self.account.port != 143:
            str = "[Server: %s:%d User: %s] %s" % (self.account.host,
                                                   self.account.port,
                                                   self.account.username, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.host,
                                                self.account.username, info)

        self.log.info(str)


