__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer

#python / mx imports
import mx.DateTime as DateTime

#Chandler imports
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ItemCollection as ItemCollection
import repository.item.ItemError as ItemError

#Chandler Mail Service imports
import smtp as smtp
import constants as constants
import message as message
import utils as utils

"""
TO DO:
 1. Need to encode Chandler Sharing Header for Transport to account from i18n collection names
 """


def sendInvitation(repository, url, itemCollection, sendToList):
    """Sends a sharing invitation via SMTP to a list of recipients

       @param repository: The repository we're using
       @type repository: C{Repository}

       @param url: The url to share
       @type url: C{str}

       @param itemCollection: An ItemCollection Instance
       @type itemCollection: C{itemCollection}

       @param sendToList: List of EmailAddress Items
       @type: C{list}
    """
    SMTPInvitationSender(repository, url, itemCollection, sendToList).sendInvitation()


class SMTPInvitationSender:
    """Sends an invitation via SMTP."""

    def __init__(self, repository, url, itemCollection, sendToList, account=None):
        assert isinstance(url, basestring), "URL must be a String"
        assert isinstance(sendToList, list), "sendToList must be of a list of email addresses"
        assert len(sendToList) > 0, "sendToList must contain at least one email address"
        assert isinstance(itemCollection, ItemCollection.ItemCollection), \
                          "itemCollection must be of type osaf.contentmodel.ItemCollection"


        #XXX: Theses may eventual need i18n decoding
        self.fromAddress = None
        self.url = url
        self.sendToList = sendToList
        self.repository = repository

        if isinstance(itemCollection.displayName, unicode):
            self.collectionName = itemCollection.displayName.encode(constants.DEFAULT_CHARSET)

        else:
            self.collectionName = itemCollection.displayName


        try:
            self.collectionBody = utils.textToStr(itemCollection.body)

        except ItemError.NoValueForAttributeError:
            self.collectionBody = u""

        if account is None:
            accountUUID = None

        else:
            accountUUID = account.itsUUID

        self.account, self.fromAddress = Mail.MailParcel.getSMTPAccount(self.repository.view, \
                                         accountUUID)

    def sendInvitation(self):
        smtp.SMTPSender(self.repository, self.account, self.__createMessage()).sendMail()

    def __createMessage(self):
        self.repository.view.refresh()

        #XXX: Tnis needs to be base 64 encoded
        sendStr = "%s%s%s" % (self.url, constants.SHARING_DIVIDER, self.collectionName)

        m = Mail.MailMessage(view=self.repository.view)

        #XXX: Try commenting out see what happens
        #m.toAddress = []
        #m.chandlerHeaders = {}

        m.subject = self.__createSubject()
        m.fromAddress = self.fromAddress

        m.chandlerHeaders[message.createChandlerHeader(constants.SHARING_HEADER)] = sendStr

        for address in self.sendToList:
            assert isinstance(address, Mail.EmailAddress), \
            "sendToList can only contain EmailAddres Object"
            m.toAddress.append(address)

        m.body = utils.strToText(m, "body", self.collectionBody)

        self.repository.view.commit()

        return m

    def __createSubject(self):
        try:
            name = self.fromAddress.fullName
        except AttributeError:
            name = self.FromAddress.emailAddress

        return "%s has invited you to share the %s collection" % (name, self.collectionName)
