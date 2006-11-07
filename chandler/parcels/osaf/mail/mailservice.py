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

#Twisted imports
from twisted.internet import reactor

#Chandler imports
import osaf.pim.mail as Mail
from repository.persistence.RepositoryError \
    import RepositoryError, VersionConflictError

from repository.persistence.RepositoryView import RepositoryView

#Chandler Mail Service import
from smtp import SMTPClient
from imap import IMAPClient
from pop import  POPClient
from errors import MailException
from utils import trace
import constants

"""
XXX: Not thread safe code
"""

__all__ = ['MailService']

class MailService(object):
    """
    Central control point for all mail related code.
    For each IMAP, POP, and SMTP account it creates
    a client instance to handle requests and stores
    the client in its queue.

    The MailService is started with Chandler in the
    application codes and shutdown with Chandler.

    It employees the lazy loading model where
    no clients are created until one is requested.

    Example:

    A user wants to send an SMTP message via an C{SMTPAccount}.
    When the user hits send the MailService receives a request:
    mailService.getSMTPInstance(smtpAccount)

    The MailService looks in its cache to see if
    it has a C{SMTPClient} instance for the given account.
    If none is found it creates the instance and passes
    back to the requestor.

    If one exists in the cache it returns that instance.

    Caching instances allows finite control of C{RepositoryView} creation
    and client pipelining.
    """

    def __init__(self, view):
        assert isinstance(view, RepositoryView)

        self._view = view
        self._started = False
        self._clientInstances = None

    def startup(self):
        """Initializes the MailService and creates the cache for
           suppported protocols POP, SMTP, IMAP"""

        self._clientInstances = {"SMTP": {}, "IMAP": {}, "POP": {}}

        if self._started:
            raise MailException("MailService is currently started")

        self._started = True

    def shutdown(self):
        """Shutsdown the MailService and deletes any clients in the
           MailServices cache"""

        if self._started:
            for clients in self._clientInstances.values():
                for client in clients.values():
                    reactor.callFromThread(client.shutdown)

            del self._clientInstances

            self._started = False

    def takeOnline(self):
        constants.OFFLINE = False
        self._view.refresh()

        for account in Mail.SMTPAccount.getActiveAccounts(self._view):
            if len(account.messageQueue):
                self.getSMTPInstance(account).takeOnline()

    def takeOffline(self):
        #set the online flag to false
        constants.OFFLINE = True

    def isOnline(self):
        return not constants.OFFLINE

    def refreshMailServiceCache(self):
        """Refreshs the MailService Cache checking for
           any client instances that are associated with
           an inactive or deleted account."""

        #XXX: Could move this in to an item collection notification
        #     listen for changes on accounts

        self.refreshIMAPClientCache()
        self.refreshSMTPClientCache()
        self.refreshPOPClientCache()

    def refreshIMAPClientCache(self):
        """Refreshes the C{IMAPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self._refreshCache("IMAP")

    def refreshSMTPClientCache(self):
        """Refreshes the C{SMTPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self._refreshCache("SMTP")

    def refreshPOPClientCache(self):
        """Refreshes the C{POPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self._refreshCache("POP")

    def getSMTPInstance(self, account):
        """
        Returns a C{SMTPClient} instance
        for the given account

        @param account: A SMTPAccount
        @type account: C{SMTPAccount}

        @return: C{SMTPClient}
        """

        assert isinstance(account, Mail.SMTPAccount)

        smtpInstances = self._clientInstances.get("SMTP")

        if account.itsUUID in smtpInstances:
            return smtpInstances.get(account.itsUUID)

        #XXX Just pass self._view
        s = SMTPClient(self._createView("SMTPClient", account), account)
        smtpInstances[account.itsUUID] = s

        return s

    def getIMAPInstance(self, account):
        """Returns a C{IMAPClient} instance
           for the given account

           @param account: A IMAPAccount
           @type account: C{IMAPAccount}

           @return: C{IMAPClient}
        """

        assert isinstance(account, Mail.IMAPAccount)

        imapInstances = self._clientInstances.get("IMAP")

        if account.itsUUID in imapInstances:
            return imapInstances.get(account.itsUUID)

        #XXX Just pass self._view
        i = IMAPClient(self._createView("IMAPClient", account), account)
        imapInstances[account.itsUUID] = i

        return i

    def getPOPInstance(self, account):
        """Returns a C{POPClient} instance
           for the given account

           @param account: A POPAccount
           @type account: C{POPAccount}

           @return: C{POPClient}
        """

        assert isinstance(account, Mail.POPAccount)

        popInstances = self._clientInstances.get("POP")

        if account.itsUUID in popInstances:
            return popInstances.get(account.itsUUID)

        #XXX Just pass self._view
        i = POPClient(self._createView("POPClient", account), account)
        popInstances[account.itsUUID] = i

        return i

    def _refreshCache(self, protocol):
        instances = None
        method = None

        if protocol in Mail.ACCOUNT_TYPES:
            instances = self._clientInstances.get(protocol)
            method = Mail.ACCOUNT_TYPES[protocol].getActiveAccounts

        self._view.refresh()

        uuidList = []
        delList  = []

        for acc in method(self._view):
            uuidList.append(acc.itsUUID)

        for accUUID in instances.keys():
            if not accUUID in uuidList:
                client = instances.get(accUUID)
                instances.pop(accUUID)
                del client
                delList.append(accUUID)

        if __debug__:
            s = len(delList)

            if s > 0:
                c = s > 1 and "Clients" or "Client"
                a = s > 1 and "accountUUID's" or "accountUUID"
                trace("removed %s%s with %s %s" % (protocol, c, a, delList))

    def _createView(self, clientName, account):
        #Assign a unique name to the view
        viewName = "%s for account: %s" % (clientName, str(account.itsUUID))
        return self._view.repository.createView(viewName)

