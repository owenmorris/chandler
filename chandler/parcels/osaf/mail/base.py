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
    """Base exception can be overiden for use by subclasses"""
    exception = errors.MailException

    def __init__(self, delegate):
        """
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
        p = protocol.ClientFactory.buildProtocol(self, addr)
        p.delegate = self.delegate

        return p

    def clientConnectionFailed(self, connector, err):
        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        self._processConnectionError(connector, err)

    def _processConnectionError(self, connector, err):
        self.connectionLost = True

        if self.retries < self.sendFinished <= 0:
            logging.warn("**Connection Lost** Retrying server. Retry: %s" % -self.retries)
            connector.connect()
            self.retries += 1

        elif self.sendFinished <= 0:
            if err.check(error.ConnectionDone):
                err.value = self.exception(errors.STR_CONNECTION_ERROR)

            self.delegate.catchErrors(err)


class AbstractDownloadClient(TwistedRepositoryViewManager.RepositoryViewManager):
    """Subclasses overide these constants"""
    accountType = Mail.AccountBase
    clientType  = "AbstractDownloadClient"
    factoryType = AbstractDownloadClientFactory
    defaultPort = 0

    def __init__(self, repository, account):
        """
        Creates a C{TwistedDownloadClient} instance
        @param account: An Instance of C{IMAPAccount}
        @type account: C{IMAPAccount}
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
        if __debug__:
            self.printCurrentView("getMail")

        """Move code execution path from current thread in to the Reactor Asynch thread"""
        reactor.callFromThread(self.execInView, self._getMail)


    def testAccountSettings(self):
        if __debug__:
            self.printCurrentView("testAccountSettings")

        self.testing = True

        reactor.callFromThread(self.execInView, self._getMail)

    def printCurrentView(self, viewStr = None):
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
                self.log.warn("%s currently testing account settings" % self.clientType)

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
        @return: C{None}

        #XXX will need to be in a view when we store errors to repository
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
        This method is a Twisted C{defer.Deferred} callback that logs in to an IMAP Server
        based on the account information stored in a C{EmailAccountKind}.
        @return: C{None}
        """
        """Overidden method"""
        self.execInView(self._loginClient)

    def _loginClient(self):
        raise NotImplementedError()

    def shutdown(self):
        if __debug__:
            self.printCurrentView("%s shutdown" % self.clientType)


    def _beforeDisconnect(self):
        if __debug__:
            self.printCurrentView("_beforeDisconnect")

        return defer.succeed(True)

    def _disconnect(self, result=None):
        if __debug__:
            self.printCurrentView("_disconnect")

        self.factory.sendFinished = 1

        if not self.factory.connectionLost and self.proto:
            self.proto.transport.loseConnection()


    def _commitDownloadedMail(self):
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
        raise NotImplementedError()

    def _actionCompleted(self, success=True):
        if __debug__:
            self.printCurrentView("_actionCompleted")

        d = self._beforeDisconnect()
        d.addBoth(self._disconnect)
        d.addCallback(lambda _: self._resetClient())

    def _resetClient(self):
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
        raise NotImplementedError()

    def _printInfo(self, info):
        if self.account.port != self.defaultPort:
            str = "[Server: %s:%d User: %s] %s" % (self.account.host,
                                                   self.account.port,
                                                   self.account.username, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.host,
                                                self.account.username, info)

        self.log.info(str)

