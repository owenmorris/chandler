"""
@copyright: Copyright (c) 2005-2006 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

#twisted imports
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer

#Chandler imports
from osaf import pim
import osaf.pim.mail as Mail
import chandlerdb.item.ItemError as ItemError

#Chandler Mail Service imports
import smtp 
import constants
import message
import utils

"""
TODO:
 1. Need to encode Chandler Sharing Header for Transport to account
    from i18n collection names
"""


def sendInvitation(repository, url, collection, sendToList):
    """
    Sends a sharing invitation via SMTP to a list of recipients

    @param repository: The repository we're using
    @type repository: C{Repository}

    @param url: The url to share
    @type url: C{str}

    @param collection: An ContentCollection Instance
    @type collection: C{ContentCollection}

    @param sendToList: List of EmailAddress Items
    @type sendToList: C{list}
    """
    SMTPInvitationSender(repository, url, collection, sendToList).sendInvitation()


class SMTPInvitationSender(object):
    """
    Sends an invitation via SMTP.
    """

    def __init__(self, repository, url, collection, sendToList, account=None):
        assert isinstance(url, basestring), "URL must be a String"
        assert isinstance(sendToList, list), "sendToList must be of a list of email addresses"
        assert len(sendToList) > 0, "sendToList must contain at least one email address"
        assert isinstance(collection, pim.ContentCollection), \
                          "collection must be of type osaf.pim.ContentCollection"


        #XXX: Theses may eventual need i18n decoding
        self.fromAddress = None
        self.url = url
        self.sendToList = sendToList
        self.repository = repository

        self.collectionName = collection.displayName.encode(constants.DEFAULT_CHARSET)


        try:
            self.collectionBody = utils.textToStr(collection.body)

        except ItemError.NoValueForAttributeError:
            self.collectionBody = u""

        if account is None:
            accountUUID = None

        else:
            accountUUID = account.itsUUID

        self.account, self.fromAddress = Mail.getCurrentSMTPAccount(self.repository.view, \
                                         accountUUID)

    def sendInvitation(self):
        #XXX Use Mail Service
        smtp.SMTPClient(self.repository, self.account).sendMail(self.__createMessage())

    def __createMessage(self):
        self.repository.view.refresh()

        m = Mail.MailMessage(itsView=self.repository.view)

        m.subject = self.__createSubject()
        m.fromAddress = self.fromAddress

        sendStr = makeSharingHeaderValue(self.url, self.collectionName)
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

def makeSharingHeaderValue(url, collectionName):
    #XXX: Tnis needs to be base 64 encoded; also, see below.
    return "%s%s%s" % (url, constants.SHARING_DIVIDER, collectionName)

def getSharingHeaderInfo(mailItem):
    """
    Return the Chandler sharing header's values, split into a
    handy list: (url, collectionName)

    Throws KeyError if not present.
    Used by Main and the detail view.
    """
    sharingHeaderName = message.createChandlerHeader(constants.SHARING_HEADER)

    #XXX: Tnis needs to be base 64 unencoded; also, see above.
    sharingHeaderValue = mailItem.chandlerHeaders[sharingHeaderName]
 
    urlAndCollectionName = sharingHeaderValue.split(constants.SHARING_DIVIDER)
    return urlAndCollectionName 

