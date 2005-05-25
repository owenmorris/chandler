__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"



"""Contains base classes utilized by the Mail Service concrete classes"""
#twisted imports
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.internet.error as error
import twisted.protocols.policies as policies
import twisted.internet.protocol as protocol
import twisted.python.failure as failure

#python / mx imports
import logging as logging

#Chandler imports
import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import repository.item.Query as Query
import osaf.contentmodel.mail.Mail as Mail
import application.Globals as Globals
import M2Crypto.SSL.TwistedProtocolWrapper as wrapper
import M2Crypto.SSL as SSL

#Chandler Mail Service imports
import errors as errors
import constants as constants
import utils as utils

class AbstractDownloadClientFactory(protocol.ClientFactory):
    """ Base class for Chandler download transport factories(IMAP, POP, etc.).
        Encapsulates boiler plate logic for working with Twisted Client Factory
        disconnects and Twisted protocol creation"""

    """Base exception that will be raised on error.
       can be overiden for use by subclasses"""
    exception = errors.MailException

    def __init__(self, delegate):
        """
            @param delegate: A Chandler protocol class containing:
                  1. An account object inherited from c{Mail.AccountBase}
                  2. A loginClient method implementation callback
                  3. A catchErrors method implementation errback
            @type delegate: c{object}

        @return: C{None}
        """

        self.delegate = delegate
        self.connectionLost = False
        self.sendFinished = 0
        self.useTLS = (delegate.account.connectionSecurity == 'TLS')

        retries = delegate.account.numRetries

        assert isinstance(retries, (int, long))
        self.retries = -retries

    def buildProtocol(self, addr):
        """Builds a Twisted Protocol instance assigning factory
           and delegate as variables on the protocol instance

          @param addr: an object implementing L{twisted.internet.interfaces.IAddress}

          @return: an object extending  L{twisted.internet.protocol.Protocol}
        """
        p = protocol.ClientFactory.buildProtocol(self, addr)
        p.delegate = self.delegate
        p.factory  = self

        return p

    def clientConnectionFailed(self, connector, err):
        """
          Called when a connection has failed to connect.

          @type err: L{twisted.python.failure.Failure}
        """
        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        """
          Called when an established connection is lost.

          @type err: L{twisted.python.failure.Failure}
        """
        self._processConnectionError(connector, err)


    def _processConnectionError(self, connector, err):
        self.connectionLost = True

        if self.retries < self.sendFinished <= 0:
            #XXX: Can remove this at some point
            logging.warn("**Connection Lost** Retrying \
                          server. Retry: %s" % -self.retries)

            connector.connect()
            self.retries += 1

        elif self.sendFinished <= 0:
            if err.check(error.ConnectionDone):
                err.value = self.exception(errors.STR_CONNECTION_ERROR)

            self.delegate.catchErrors(err)


class AbstractDownloadClient(TwistedRepositoryViewManager.RepositoryViewManager):
    """ Base class for Chandler download transports (IMAP, POP, etc.)
        Encapsulates logic for interactions between Twisted protocols (POP, IMAP)
        and Chandler protocol clients"""

    """Subclasses overide these constants"""
    accountType = Mail.AccountBase
    clientType  = "AbstractDownloadClient"
    factoryType = AbstractDownloadClientFactory
    defaultPort = 0

    def __init__(self, repository, account):
        """
        @param repository: An Instance of C{DBRepository}
        @type repository: C{DBRepository}
        @param account: An Instance of C{DownloadAccountBase}
        @type account: C{DownloadAccount}
        @return: C{None}
        """
        assert isinstance(account, self.accountType)

        super(AbstractDownloadClient, self).__init__(repository)

        """These values exist for life of client"""
        self.accountUUID = account.itsUUID
        self.account = None
        self.inProcess = False
        self.testing = False

        """These values are reassigned per request"""
        self.factory = None
        self.proto = None
        self.lastUID = 0
        self.totalDownloaded = 0
        self.pending = []

        """These values are reassigned per fetch"""
        self.numDownloaded = 0
        self.numToDownload = 0


    def getMail(self):
        """Retrieves mail from a download protocol (POP, IMAP)"""
        if __debug__:
            self.printCurrentView("getMail")

        """Move code execution path from current thread
           to Reactor Asynch thread"""

        reactor.callFromThread(self.execInView, self._getMail)


    def testAccountSettings(self):
        """Tests the account settings for a download protocol (POP, IMAP).
           Raises an error if unable to establish or communicate properly
           with the a server.
        """

        if __debug__:
            self.printCurrentView("testAccountSettings")

        self.testing = True

        reactor.callFromThread(self.execInView, self._getMail)

    def printCurrentView(self, viewStr = None):
        """Prints the current view as well the clientType and
           viewStr to the log.

           @type viewStr: C{str}, C{unicode}, or None
        """

        if viewStr is None:
            str = self.clientType
        else:
            str = "%s.%s" % (self.clientType, viewStr)

        super(AbstractDownloadClient, self).printCurrentView(str)

    def _getMail(self):
        if __debug__:
            self.printCurrentView("_getMail")

        if self.inProcess:
            if self.testing:
                self.log.warn("%s currently testing account \
                               settings" % self.clientType)

            else:
                self.log.warn("%s currently downloading mail" % self.clientType)

            return

        self.inProcess = True

        try:
            self.view.refresh()

        except Exception, e:
            return self.catchErrors(e)

        """Overidden method"""
        self._getAccount()

        self.factory = self.factoryType(self)

        if self.account.connectionSecurity == 'SSL':
            #XXX: This method actually begins the SSL exchange. Confusing name!
            self.factory.startTLS   = True
            self.factory.getContext = lambda : Globals.crypto.getSSLContext(repositoryView=self.view)
            self.factory.sslChecker = SSL.Checker.Checker()

        wrappingFactory = policies.WrappingFactory(self.factory)
        wrappingFactory.protocol = wrapper.TLSProtocolWrapper
        reactor.connectTCP(self.account.host, self.account.port, wrappingFactory)

    def catchErrors(self, err):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread.
        @param err: The error thrown
        @type err: C{failure.Failure} or c{Exception}

        @return: C{None}
        """
        if __debug__:
            self.printCurrentView("catchErrors")

        if isinstance(err, failure.Failure):
            err.printBriefTraceback()
            err = err.value

        errorType = str(err.__class__)
        errorStr  = err.__str__()

        if errorType == errors.M2CRYPTO_ERROR:
            try:
                if err.args[0] == errors.M2CRYPTO_CERTIFICATE_VERIFY_FAILED:
                    errorStr = errors.STR_SSL_CERTIFICATE_ERROR

            except:
               errStr = errors.STR_SSL_ERROR

        if self.testing:
            utils.alert(constants.TEST_ERROR, \
                        self.account.displayName, errorStr)
        else:
            utils.alert(constants.DOWNLOAD_ERROR, errorStr)

        self._actionCompleted()

    def loginClient(self):
        """
        Called after serverGreeting to log in a client to the server via
        a protocol (IMAP, POP)

        @return: C{None}
        """
        self.execInView(self._loginClient)

    def _loginClient(self):
        raise NotImplementedError()

    def shutdown(self):
        """Called by the C{MailService} before Mail Transport Client
           is unitialized. Overide this method to add any custom
           behavior required before shutdown"""
        if __debug__:
            self.printCurrentView("%s shutdown" % self.clientType)


    def _beforeDisconnect(self):
        """Overide this method to place any protocol specific
           logic to be handled before disconnect i.e. send a 'Quit'
           command.
        """

        if __debug__:
            self.printCurrentView("_beforeDisconnect")

        return defer.succeed(True)

    def _disconnect(self, result=None):
        """Disconnects a client from a server.
           Has logic to make sure that the client is actually
           connected.
        """

        if __debug__:
            self.printCurrentView("_disconnect")

        self.factory.sendFinished = 1

        if not self.factory.connectionLost and self.proto:
            self.proto.transport.loseConnection()


    def _commitDownloadedMail(self):
        """Commits mail to the C{Repository}.
           If there are more messages to download
           calls C{_getNextMessageSet} otherwise
           calls C{_actionCompleted} to clean up
           client references
        """
        if __debug__:
            self.printCurrentView("_commitDownloadedMail")

        self.view.commit()
        self.view.prune(1000)

        msg = constants.DOWNLOAD_MESSAGES % self.totalDownloaded

        utils.NotifyUIAsync(msg)

        """We have downloaded the last batch of messages if the
           number downloaded is less than the max"""
        if self.numDownloaded < constants.DOWNLOAD_MAX:
            self._actionCompleted()

        else:
            self.numDownloaded = 0
            self.numToDownload = 0

            self._getNextMessageSet()

    def _getNextMessageSet(self):
        """Overide this to add retrieval of
           message set logic for POP. IMAP, etc
        """
        raise NotImplementedError()

    def _actionCompleted(self):
        """Handles clean up after mail downloaded
           by calling:
               1. _beforeDisconnectClient
               2. _disconnect
               3. _resetClient
        """

        if __debug__:
            self.printCurrentView("_actionCompleted")

        d = self._beforeDisconnect()
        d.addBoth(self._disconnect)
        d.addCallback(lambda _: self._resetClient())

    def _resetClient(self):
        """Resets Client object state variables to
           default state.
        """

        if __debug__:
            self.printCurrentView("_resetClient")

        """Release the inProcess lock"""
        self.inProcess = False

        """Reset testing to False"""
        self.testing = False

        """Clear out per request values"""
        self.factory         = None
        self.proto           = None
        self.lastUID         = 0
        self.totalDownloaded = 0
        self.pending         = []

        self.numToDownload  = 0
        self.numDownloaded  = 0

    def _getAccount(self):
        """Overide this method to add custom account
           look up logic. Accounts can not be passed across
           threads so the C{UUID} must be used to fetch the 
           account's data
        """

        raise NotImplementedError()

    def _printInfo(self, info):
        """Print tracing infor to the Chandler log
           including host, port, and username

           @param info: String data to add to the log message
           @type info: C{String}
        """
        if self.account.port != self.defaultPort:
            str = "[Server: %s:%d User: %s] %s" % (self.account.host,
                                                   self.account.port,
                                                   self.account.username, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.host,
                                                self.account.username, info)

        self.log.info(str)

