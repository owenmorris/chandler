__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#twisted imports
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer

#python / mx imports
import email.Message as Message
import mx.DateTime as DateTime

#Chandler imports
import application.Globals as Globals
import osaf.contentmodel.mail.Mail as Mail
import osaf.framework.twisted.TwistedRepositoryViewManager as TwistedRepositoryViewManager
import osaf.framework.sharing as chandlerSharing
import chandlerdb.util.UUID as UUID

#Chandler Mail Service imports
import smtp as smtp
import common as common
import message as message

"""
TO DO:
 1. Need to encode Chandler Sharing Header for Transport to account from i18n collection names
"""


def receivedInvitation(url, collectionName, fromAddress):
    """
       Calls osaf.framework.sharing.anounceSharingUrl.

       @param url: The url to share
       @type url: C{str}

       @param collectionName: The name of the collection
       @type collectionName: C{str}

       @param fromAddress: The email address of the person sending the invite
       @type: C{str}
    """
    assert isinstance(url, str), "URL must be a String"
    assert isinstance(collectionName, str), "collectionName must be a String"
    assert isinstance(fromAddress, str), "fromAddress  must be a String"

    chandlerSharing.Sharing.announceSharingInvitation(url.strip(), collectionName.strip(), fromAddress.strip())

def sendInvitation(url, collectionName, sendToList):
    """Sends a sharing invitation via SMTP to a list of recipients

       @param url: The url to share
       @type url: C{str}

       @param collectionName: The name of the collection
       @type collectionName: C{str}

       @param sendToList: List of email addresses to invite
       @type: C{list}
    """
    SMTPInvitationSender(url, collectionName, sendToList).sendInvitation()


class SMTPInvitationSender(TwistedRepositoryViewManager.RepositoryViewManager):
    """Sends an invitation via SMTP. Use the osaf.mail.sharing.sendInvitation
       method do not call this class directly"""

    def __init__(self, url, collectionName, sendToList, account=None):

        assert isinstance(url, str), "URL must be a String"
        assert isinstance(sendToList, list), "sendToList must be of a list of email addresses"
        assert len(sendToList) > 0, "sendToList must contain at least one email address"

        #XXX: This needs to be intenationalized with a char conversion
        collectionName = str(collectionName)

        assert isinstance(collectionName, str), "collectionName must be a String or Unicode"

        viewName = "SMTPInvitationSender_%s" % str(UUID.UUID())

        super(SMTPInvitationSender, self).__init__(Globals.repository, viewName)

        self.account = None
        self.from_addr = None
        self.url = url
        self.collectionName = collectionName
        self.sendToList = sendToList
        self.accountUUID = None

        if account is not None:
             self.accountUUID = account.itsUUID

    def sendInvitation(self):
        if __debug__:
            self.printCurrentView("sendInvitation")

        reactor.callFromThread(self.execInView, self.__sendInvitation)

    def __sendInvitation(self):

        if __debug__:
            self.printCurrentView("__sendInvitation")

        self.__getData()

        messageText = self.__createMessageText()

        d = defer.Deferred().addCallbacks(self.__invitationSuccessCheck, self.__invitationFailure)

        smtp.SMTPSender.sendMailMessage(self.from_addr, self.sendToList, messageText, d, self.account)


    def __invitationSuccessCheck(self, result):
        if __debug__:
            self.printCurrentView("__invitationSuccessCheck")

        if result[0] == len(result[1]):
            addrs = []

            for address in result[1]:
                addrs.append(address[0])

            info = "Sharing invitation (%s: %s) sent to [%s]" % (self.collectionName, self.url, ", ".join(addrs))
            self.log.info(info)

        else:
            errorText = []
            for recipient in result[1]:
                email, code, str = recipient

                """If the recipient was accepted skip"""
                if code == common.SMTPConstants.SUCCESS:
                    continue

                e = "Failed to send invitation | (%s: %s) | %s | %s | %s |" % (self.collectionName,
                                                                               self.url, 
                                                                               email, code, str)
                errorText.append(e)

            err = '\n'.join(errorText)

            common.NotifyUIAsync(_(err), self.log.error, alert=True)

    def __invitationFailure(self, result):
        if __debug__:
            self.printCurrentView("__invitationFailure")

        try:
            desc = result.value.resp
        except:
            desc = result.value

        e = "Failed to send invitation | (%s: %s) | %s |" % (self.collectionName, self.url,
                                                             desc)

        common.NotifyUIAsync(e, self.log.error, alert=True)

    def __createMessageText(self):
        sendStr = "%s%s%s" % (self.url, common.SharingConstants.SHARING_DIVIDER, self.collectionName)

        messageObject = common.getChandlerTransportMessage()

        """Add the chandler sharing header"""
        messageObject[getChandlerSharingHeader()] = sendStr

        """populate the standard static mail message headers"""
        message.populateStaticHeaders(messageObject)

        return messageObject.as_string()

    def __getData(self):
        """If accountUUID is None will return the first SMTPAccount found"""
        self.account, replyToAddress = Mail.MailParcel.getSMTPAccount(self.accountUUID)
        self.from_addr = replyToAddress.emailAddress


def getChandlerSharingHeader():
    return message.createChandlerHeader(common.SharingConstants.SHARING_HEADER)
