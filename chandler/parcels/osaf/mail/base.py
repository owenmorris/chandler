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


"""Contains base classes utilized by the Mail Service concrete classes"""

#twisted imports
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.internet.error as error
import twisted.protocols.policies as policies
import twisted.internet.protocol as protocol
import twisted.python.failure as failure
from twisted.internet import threads

#python imports
import logging

#Chandler imports
from application import Globals
from repository.persistence.RepositoryError \
    import RepositoryError, VersionConflictError
from repository.persistence.RepositoryView import RepositoryView
import osaf.pim.mail as Mail
from osaf.framework.certstore import ssl
import application.Utility as Utility
from osaf import messages

#Chandler Mail Service imports
import errors
import constants
from utils import *

#Call RepositoryView.prune(1000) after commit when the number of
# downloaded messages exceeds PRUNE_MIN
PRUNE_MIN = 25


"""
ISSUES:
1. If an account is testing while a background sync of that account is happening then
   this will be an issue. Especially on a cancel. Need to think about this during
   folder refactoring for preview. Solutions are don't persist testing values or
   don't cache mail clients or always create a new mail client per testing try this
   avoids affecting the cached client used for download.
"""



class AbstractDownloadClientFactory(protocol.ClientFactory):
    """ Base class for Chandler download transport factories(IMAP, POP, etc.).
        Encapsulates boiler plate logic for working with Twisted Client Factory
        disconnects and Twisted protocol creation"""

    # Base exception that will be raised on error.
    # can be overiden for use by subclasses.
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
        self.timeout = delegate.account.timeout
        self.timedOut = False

        retries = delegate.account.numRetries

        assert isinstance(retries, (int, long))
        self.retries = -retries

    def buildProtocol(self, addr):
        """
        Builds a Twisted Protocol instance assigning factory
        and delegate as variables on the protocol instance

        @param addr: an object implementing L{twisted.internet.interfaces.IAddress}

        @return: an object extending  L{twisted.internet.protocol.Protocol}
        """
        p = protocol.ClientFactory.buildProtocol(self, addr)

        #Set up a reference so delegate can call the proto and proto
        #can call the delegate.

        p.delegate = self.delegate
        self.delegate.proto = p

        #Set the protocol timeout value to that specified in the account
        p.timeout = self.timeout
        p.factory  = self

        return p

    def clientConnectionFailed(self, connector, err):
        """
          Called when a connection has failed to connect.

          @type err: L{twisted.python.failure.Failure}
        """
        if __debug__:
            trace("ClientConnectionFailed")

        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        """
          Called when an established connection is lost.

          @type err: L{twisted.python.failure.Failure}
        """
        if __debug__:
            trace("ClientConnectionLost")

        self._processConnectionError(connector, err)


    def _processConnectionError(self, connector, err):
        self.connectionLost = True

        if self.delegate.complete:
            self.delegate._resetClient()

        elif self.retries < self.sendFinished <= 0:
            trace("**Connection Lost** Retrying server. Retry: %s" % -self.retries)

            connector.connect()
            self.retries += 1

        elif self.sendFinished <= 0:
            if err.check(error.ConnectionDone):
                err.value = self.exception(errors.STR_CONNECTION_ERROR)

            if __debug__:
                trace("_processConnectionError manual call to catchErrors")

            self.delegate.catchErrors(err)

class AbstractDownloadClient(object):
    """ Base class for Chandler download transports (IMAP, POP, etc.)
        Encapsulates logic for interactions between Twisted protocols (POP, IMAP)
        and Chandler protocol clients"""


    #Subclasses overide these constants
    accountType = Mail.AccountBase
    clientType  = "AbstractDownloadClient"
    factoryType = AbstractDownloadClientFactory
    defaultPort = 0

    def __init__(self, view, account):
        """
        @param view: An Instance of C{RepositoryView}
        @type view: C{RepositoryView}
        @param account: An Instance of C{DownloadAccountBase}
        @type account: C{DownloadAccount}
        @return: C{None}
        """
        assert isinstance(account, self.accountType)
        assert isinstance(view, RepositoryView)

        self.view = view

        #These values exist for life of client
        self.accountUUID = account.itsUUID
        self.account = None
        self.currentlyDownloading = False
        self.testing = False
        self.callback = None
        self.cancel = False
        self.shuttingDown = False

        #These values are reassigned per request
        self.factory = None
        self.proto = None
        self.lastUID = 0
        self.totalDownloaded = 0
        self.pruneCounter = 0
        self.pending = []
        self.downloadMax = 0
        self.complete = False

        #These values are reassigned per fetch
        self.numDownloaded = 0
        self.numToDownload = 0

    def getMail(self):
        """Retrieves mail from a download protocol (POP, IMAP)"""
        if __debug__:
            trace("getMail")

        # Move code execution path from current thread
        # to Reactor Asynch thread
        reactor.callFromThread(self._getMail)

    def testAccountSettings(self, callback):
        """Tests the account settings for a download protocol (POP, IMAP).
           Raises an error if unable to establish or communicate properly
           with the a server.
        """
        if __debug__:
            trace("testAccountSettings")


        if Globals.options.offline:
            return

        assert(callback is not None)
        self.callback = callback
        self.testing = True

        reactor.callFromThread(self._getMail)

    def _getMail(self):
        if __debug__:
            trace("_getMail")

        if self.cancel:
            return self._resetClient()

        try:
            self.view.refresh()

        except VersionConflictError, e:
            log.exception("Repository raised a VersionConflictError")
            return self.catchErrors(e)

        except RepositoryError, e1:
            log.exception("Repository raised a RepositoryError")
            return self.catchErrors(e1)

        #Overidden method
        self._getAccount()

        if Globals.options.offline:
            msg = constants.DOWNLOAD_OFFLINE % {"accountName": self.account.displayName}
            setStatusMessage(msg)
            return

        if self.currentlyDownloading:
            if self.testing:
                trace("%s currently testing account settings" % self.clientType)

            else:
                trace("%s currently downloading mail" % self.clientType)

            return

        self.currentlyDownloading = True

        msg = constants.DOWNLOAD_START \
                      % {"accountName": self.account.displayName,
                         "serverDNSName": self.account.host}

        setStatusMessage(msg)

        self.factory = self.factoryType(self)

        #Cache the maximum number of messages to download before forcing a commit
        self.downloadMax = self.account.downloadMax

        if self.testing:
            # If in testing mode then do not want to retry connection or
            # wait a long period for a timeout
            self.factory.retries = 0
            self.factory.timeout = constants.TESTING_TIMEOUT

        if self.account.connectionSecurity == 'SSL':
            ssl.connectSSL(self.account.host, self.account.port,
                           self.factory, self.view)
        else:
            ssl.connectTCP(self.account.host, self.account.port,
                           self.factory, self.view)

    def catchErrors(self, err):
        """
        This method captures all errors thrown while in the Twisted Reactor Thread as well
        as errors raised by non-Twisted code while in the Twisted Reactor Thread.
        catchErrors will print a stacktrace of C{failure.Failure} objects to the chandler.log.
        catchErrors also handles c{Exception}s but will not log the stacktrace to the chandler.log
        since this method is out of the scope of the original c{Exception}. The caller must log 
        its c{Exception} via the logging.exception method.

        @param err: The error thrown
        @type err: C{failure.Failure} or c{Exception}

        @return: C{None}
        """
        if __debug__:
            trace("catchErrors")

        self.complete = True

        try:
            #On error cancel any changes done in the view
            self.view.cancel()
        except:
            pass

        # In this case don't try to clean up the transport connection
        # but do reset the client variables
        if self.shuttingDown or Globals.options.offline or \
           self.factory is None:
            self._resetClient()
            return

        # If we cancelled the request then gracefully disconnect from
        # the server and reset the client variables but do not display
        # the error.
        if self.cancel:
            return self._actionCompleted()

        if isinstance(err, failure.Failure):
            if err.check(error.ConnectionDone):
                if self.factory.retries < self.factory.sendFinished <= 0:
                    #The error processing for lost connections is in the Factory
                    #class so return here and let the Factory handle the reconnection logic.
                    return

                #set the value of the error to something more meaningful than
                #'Connection closed cleanly.'
                err.value = self.factory.exception(errors.STR_CONNECTION_ERROR)

            try:
                err.raiseException()
            except:
                log.exception("Exception raised in Twisted Framework Layer. \
                               More information may be available in the twisted.log.")

            err = err.value

        #Get the str representation of Python class
        errorType   = str(err.__class__)

        if self.testing:
            reconnect = self.testAccountSettings
        else:
            reconnect = self.getMail
            #Clear the previous message in the status bar.
            #But only if we are not in testing mode since it
            #does not leverage the status bar.
            setStatusMessage(u"")

        if isinstance(err, Utility.CertificateVerificationError):
            assert err.args[1] == 'certificate verify failed'

            # Reason why verification failed is stored in err.args[0], see
            # codes at http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS


            # Post an asynchronous event to the main thread where
            # we ask the user if they would like to trust this
            # certificate. The main thread will then initiate a retry
            # when the new certificate has been added.
            if err.args[0] in ssl.unknown_issuer:
                displaySSLCertDialog(err.untrustedCertificates[0], reconnect)
            else:
                displayIgnoreSSLErrorDialog(err.untrustedCertificates[0], err.args[0],
                                                  reconnect)

            self._actionCompleted()
            return

        if errorType == errors.M2CRYPTO_CHECKER_ERROR:
            # Post an asynchronous event to the main thread where
            # we ask the user if they would like to continue even though
            # the certificate identifies a different host.
            displayIgnoreSSLErrorDialog(err.pem,
                                        messages.SSL_HOST_MISMATCH % {'expectedHost': err.expectedHost, 'actualHost': err.actualHost},
                                        reconnect)

            self._actionCompleted()
            return

        #Convert error messages to unicode objects for display
        try:
            errorText = unicode(err.__str__(), 'utf8', 'replace')
        except (UnicodeEncodeError, TypeError), e:
            logging.exception("Unable to convert Exception string text to Unicode")
            #XXX If the conversion fails add a more detailed message
            # such "Please look at log to view the error"
            errorText = u""

        if self.testing:
            callMethodInUIThread(self.callback, (0, errorText))
        else:
            alertMailError(constants.DOWNLOAD_ERROR, self.account, \
                          {'error': errorText})

        self._actionCompleted()

        return

    def loginClient(self):
        """
        Called after serverGreeting to log in a client to the server via
        a protocol (IMAP, POP)

        @return: C{None}
        """

        if self.cancel:
            return self._actionCompleted()

        return self._loginClient()

    def cancelLastRequest(self):
        if __debug__:
            trace("cancelLastRequest")

        if self.currentlyDownloading or self.testing:
            self.cancel = True

    def shutdown(self):
        if __debug__:
            trace("shutdown")

        self.shuttingDown = True

    def _loginClient(self):
        """Overide this method to place any protocol specific
           logic to be handle logging in to client
        """

        raise NotImplementedError()

    def _beforeDisconnect(self):
        """Overide this method to place any protocol specific
           logic to be handled before disconnect i.e. send a 'Quit'
           command.
        """

        if __debug__:
            trace("_beforeDisconnect")

        return defer.succeed(True)

    def _disconnect(self, result=None):
        """Disconnects a client from a server.
           Has logic to make sure that the client is actually
           connected.
        """

        if __debug__:
            trace("_disconnect")

        if not self.factory:
            return

        self.factory.sendFinished = 1

        if not self.factory.connectionLost and self.proto:
            self.proto.transport.loseConnection()

    def _commitDownloadedMail(self, callback=None):
        """Commits mail to the C{Repository}.
           If there are more messages to download
           calls C{_getNextMessageSet} otherwise
           calls C{_actionCompleted} to clean up
           client references
        """
        if __debug__:
            trace("_commitDownloadedMail")

        def _tryCommit():
            try:
                self.view.commit()

                # Prune the view to free up memory if the number downloaded is equal
                # to or exceeds the PRUNE_MIN. If the numDownloaded is less than the
                # download maximum before a commit it means that all messages have been downloaded
                # from the server in which case we prune to free every ounce of memory we can
                # get :)

                if self.pruneCounter >= PRUNE_MIN or \
                   self.numDownloaded < self.downloadMax:
                    self.view.prune(1000)

                    if __debug__:
                        trace("Prunning %s messages" % self.pruneCounter)

                    #reset the counter
                    self.pruneCounter = 0
            except RepositoryError, e:
                raise

            except VersionConflictError, e1:
                raise

        d = threads.deferToThread(_tryCommit)

        if callback:
            d.addCallback(callback)
            d.addCallback(lambda _: self._postCommit())
            d.addErrback(self.catchErrors)

            return d

        else:
            return d.addCallback(lambda _: self._postCommit()
                                ).addErrback(self.catchErrors)


    def _postCommit(self):
        if __debug__:
            trace("_postCommit")

        msg = constants.DOWNLOAD_MESSAGES % {'accountName': self.account.displayName,
                                             'numberOfMessages': self.totalDownloaded}

        setStatusMessage(msg)

        # We have downloaded the last batch of messages if the
        # number downloaded is less than the max.
        # Add a check to make sure the account was not
        # deactivated during the last fetch.

        if self.numDownloaded < self.downloadMax or not self.account.isActive:
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
               1. _beforeDisconnect
               2. _disconnect
               3. _resetClient
        """

        if __debug__:
            trace("_actionCompleted")

        d = self._beforeDisconnect()
        d.addBoth(self._disconnect)
        d.addBoth(lambda _: self._resetClient())
        return d

    def _resetClient(self):
        """Resets Client object state variables to
           default state.
        """
        if __debug__:
            trace("_resetClient")

        #Release the currentlyDownloading lock
        self.currentlyDownloading = False

        #Reset testing to False
        self.testing = False

        #Reset callback to None
        self.callback = None

        #reset the cancel flag
        self.cancel = False

        #Clear out per request values
        self.factory         = None
        self.proto           = None
        self.lastUID         = 0
        self.totalDownloaded = 0
        self.pruneCounter    = 0
        self.pending         = []
        self.downloadMax     = 0
        self.complete        = False

        self.numToDownload  = 0
        self.numDownloaded  = 0

    def _getAccount(self):
        """Overide this method to add custom account
           look up logic. Accounts can not be passed across
           threads so the C{UUID} must be used to fetch the 
           account's data
        """
        raise NotImplementedError()
