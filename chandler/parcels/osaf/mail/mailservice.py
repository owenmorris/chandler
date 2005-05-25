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
    def __init__(self, repository):
        self.__repository = repository
        self.__view = repository.view
        self.__started = False

    def startup(self):
        if self.__started:
            raise errors.MailException("MailService is currently started")

        self.__smtpInstances = {}
        self.__imapInstances = {}
        self.__popInstances  = {}

        self.__started = True

    def shutdown(self):
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
        self.refreshIMAPClientCache()
        self.refreshSMTPClientCache()
        self.refreshPOPClientCache()

    def refreshIMAPClientCache(self):
        self.__refreshClientCache("IMAP")

    def refreshSMTPClientCache(self):
        self.__refreshClientCache("SMTP")

    def refreshPOPClientCache(self):
        self.__refreshClientCache("POP")

    def getSMTPInstance(self, account):
        assert isinstance(account, Mail.SMTPAccount)

        if account.itsUUID in self.__smtpInstances:
            return self.__smtpInstances.get(account.itsUUID)

        s = smtp.SMTPClient(self.__repository, account)
        self.__smtpInstances[account.itsUUID] = s

        return s

    def getIMAPInstance(self, account):
        assert isinstance(account, Mail.IMAPAccount)

        if account.itsUUID in self.__imapInstances:
            return self.__imapInstances.get(account.itsUUID)

        i = imap.IMAPClient(self.__repository, account)
        self.__imapInstances[account.itsUUID] = i

        return i

    def getPOPInstance(self, account):
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

