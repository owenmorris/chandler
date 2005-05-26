__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#python imports
import logging as logging

#Chandler imports
import osaf.contentmodel.mail.Mail as Mail

#Chandler Mail Service imports
import smtp as smtp
import imap as imap
import pop as pop
import errors as errors

class MailService(object):
    """Central control point for all mail related code.
       For each IMAP, POP, and SMTP account it creates
       a client instance to handle requests and stores
       the client in its queue.

       The MailService is started with Chandler in the
       application codes and shutdown with Chandler.

       It employees the lazy loading model where
       no clients are created until one is requested.

       Example:
          A user wants to send an SMTP message via an C{SMTPAccount}.
          When the user hits send the mailservice receives a request:
          mailService.getSMTPInstance(smtpAccount)

          The MailService looks in its cache to see if
          it has a C{SMTPClient} instance for the given account.
          If none is found it creates the instance and passes
          back to the requestor.

          If one exists in the cache it returns that instance.


      Caching instances allows finite control of C{RepositoryView} creation
      and client pipelining.
    """

    def __init__(self, repository):
        self.__repository = repository
        self.__view = repository.view
        self.__started = False

    def startup(self):
        """Initializes the MailService and creates the cache for
           suppported protocols POP, SMTP, IMAP"""

        if self.__started:
            raise errors.MailException("MailService is currently started")

        self.__smtpInstances = {}
        self.__imapInstances = {}
        self.__popInstances  = {}

        self.__started = True

    def shutdown(self):
        """Shutsdown the MailService and any clients in the 
           MailServices cache"""

        for smtpInstance in self.__smtpInstances.values():
            #XXX: Not crazy about the termonology
            smtpInstance.shutdown()

        self.__smtpInstances = None

        for imapInstance in self.__imapInstances.values():
            #XXX: Not crazy about the termonology
            imapInstance.shutdown()

        self.__imapInstances = None

        for popInstance in self.__popInstances.values():
            #XXX: Not crazy about the termonology
            popInstance.shutdown()

        self.__popInstances = None

        self.__started = False

    def refreshMailServiceCache(self):
        """Refreshs the MailService Cache checking for
           any client instances that are associated with
           an inactive or deleted account."""

        self.refreshIMAPClientCache()
        self.refreshSMTPClientCache()
        self.refreshPOPClientCache()

    def refreshIMAPClientCache(self):
        """Refreshes the C{IMAPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self.__refreshClientCache("IMAP")

    def refreshSMTPClientCache(self):
        """Refreshes the C{SMTPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self.__refreshClientCache("SMTP")

    def refreshPOPClientCache(self):
        """Refreshes the C{POPClient} cache
           removing any instances associated with
           inactive or deleted accounts"""

        self.__refreshClientCache("POP")

    def getSMTPInstance(self, account):
        """Returns a C{SMTPClient} instance
           for the given account

           @param account: A SMTPAccount
           @type account: C{SMTPAccount}

           @return: C{SMTPClient}
        """

        assert isinstance(account, Mail.SMTPAccount)

        if account.itsUUID in self.__smtpInstances:
            return self.__smtpInstances.get(account.itsUUID)

        s = smtp.SMTPClient(self.__repository, account)
        self.__smtpInstances[account.itsUUID] = s

        return s

    def getIMAPInstance(self, account):
        """Returns a C{IMAPClient} instance
           for the given account

           @param account: A IMAPAccount
           @type account: C{IMAPAccount}

           @return: C{IMAPClient}
        """

        assert isinstance(account, Mail.IMAPAccount)

        if account.itsUUID in self.__imapInstances:
            return self.__imapInstances.get(account.itsUUID)

        i = imap.IMAPClient(self.__repository, account)
        self.__imapInstances[account.itsUUID] = i

        return i

    def getPOPInstance(self, account):
        """Returns a C{POPClient} instance
           for the given account

           @param account: A POPAccount
           @type account: C{POPAccount}

           @return: C{POPClient}
        """

        assert isinstance(account, Mail.POPAccount)

        if account.itsUUID in self.__popInstances:
            return self.__popInstances.get(account.itsUUID)

        i = pop.POPClient(self.__repository, account)
        self.__popInstances[account.itsUUID] = i

        return i

    def __refreshClientCache(self, type):
        instances = None
        method = None

        if type == "SMTP":
            instances = self.__smtpInstances
            method = Mail.MailParcel.getActiveSMTPAccounts

        elif type == "IMAP":
            instances = self.__imapInstances
            method = Mail.MailParcel.getActiveIMAPAccounts

        elif type == "POP":
            instances = self.__popInstances
            method = Mail.MailParcel.getActivePOPAccounts

        self.__view.refresh()

        uuidList = []
        delList  = []

        for acc in method(self.__view):
            uuidList.append(acc.itsUUID)

        for accUUID in instances.keys():
            if not accUUID in uuidList:
                client = instances.get(accUUID)
                instances.pop(accUUID)
                client.shutdown()
                del client
                delList.append(accUUID)

        if __debug__:
            s = len(delList)

            if s > 0:
                c = s > 1 and "Clients" or "Client"
                a = s > 1 and "accountUUID's" or "accountUUID"
                logging.warn("removed %s%s with %s %s" % (type, c, a, delList))

