import twisted.mail.smtp as smtp
import application.Globals as Globals
import twisted.internet.reactor as reactor
import twisted.internet.error as error
import twisted.internet.defer as defer
import twisted.internet.ssl as ssl
import email.Message as Message
import logging as logging
import smtp as smtp
import common as common
import errors as errorCode
import message as message
import osaf.contentmodel.mail.Mail as Mail
import repository.persistence.RepositoryView as RepositoryView
import repository.util.UUID as UUID
import mx.DateTime as DateTime
import osaf.framework.sharing as chandlerSharing

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def receivedInvitation(url, collectionName, fromAddress):
    """
       Calls osaf.framework.sharing.anounceSharingUrl.

       @param url: The url to share
       @type url: C{str}

       @param collectionName: The name of the collection
       @type collectionName: C{str}

       @param fromAddress: The email address of the person sending the invite
       @type: C{str} or C{EmailAddress}
    """
    if not isinstance(url, str):
        raise SharingException("URL must be a String")

    if not isinstance(collectionName, str):
        raise SharingException("collectionName must be a String")

    if isinstance(fromAddress, Mail.EmailAddress):
        fromAddress = message.format_addr(fromAddress)

    elif not isinstance(fromAddress, str):
        raise SharingException("fromAddress must be a String or a Mail.EmailAddress")

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

def NotifyUIAsync(message, **keys):
    """Temp method for posting a event to the CPIA layer. This
       method will be refactored soon"""
    if Globals.wxApplication is not None: # test framework has no wxApplication
        Globals.wxApplication.CallItemMethodAsync(Globals.mainView,
                                                  'setStatusMessage',
                                                   message, **keys)

class SharingConstants(object):
    """Contants used by the sharing code"""
    SHARING_HEADER  = "Sharing-URL"
    SHARING_DIVIDER = ";"

class SharingException(Exception):
    """Base class for all Chqndler Sharing related exceptions"""
    pass

class SMTPInvitationSender(RepositoryView.AbstractRepositoryViewManager):
    """Sends an invitation via SMTP. Use the osaf.mail.sharing.sendInvitation
       method do not call this class directly"""

    def __init__(self, url, collectionName, sendToList, account=None):
        if account is not None and not account.isItemOf(Mail.MailParcel.getSMTPAccountKind()):
            raise SharingException("You must pass a SMTPAccount instance")

        if not isinstance(url, str):
            raise SharingException("URL must be a String")

        if isinstance(collectionName, unicode):
            collectionName = str(collectionName)

        elif not isinstance(collectionName, str):
            raise SharingException("collectionName must be a String or Unicode")

        if not isinstance(sendToList, list):
            raise SharingException("sendToList must be of a list of email addresses")

        viewName = "SMTPInvitationSender_%s" % str(UUID.UUID())

        super(SMTPInvitationSender, self).__init__(Globals.repository, viewName)

        self.account = None
        self.from_addr = None
        self.url = url
        self.collectionName = collectionName
        self.sendToList = sendToList
        self.accountUUID = None
        self.factory = None

        if account is not None:
            self.accountUUID = account.itsUUID

    def sendInvitation(self):
        if __debug__:
            self.printCurrentView("sendInvitation")

        reactor.callFromThread(self.__sendInvitation)

    def __sendInvitation(self):
        self.setViewCurrent()

        try:
            if __debug__:
                self.printCurrentView("__sendInvitation")

            self.__getData()

            username     = self.account.username
            password     = self.account.password
            host         = self.account.host
            port         = self.account.port
            useSSL       = self.account.useSSL
            useAuth      = self.account.useAuth
            retries      = self.account.numRetries
            authRequired = True
            sslContext   = None
            heloFallback = False

            if not useAuth:
                authRequired = False
                heloFallback = True
                username     = None
                password     = None

            if useSSL:
                sslContext = ssl.ClientContextFactory(useM2=1)

            messageText = self.__createMessageText()

            d = defer.Deferred().addCallbacks(self.__invitationSuccessCheck, self.__invitationFailure)
            msg = StringIO(messageText)

        finally:
            self.restorePreviousView()

        self.factory = smtp.ChandlerESMTPSenderFactory(username, password, self.from_addr,
                                                       self.sendToList, msg, d, retries,
                                                       sslContext, heloFallback, authRequired, 
                                                       useSSL, useSSL)

        reactor.connectTCP(host, port, self.factory)

    def __invitationSuccessCheck(self, result):
        if __debug__:
            self.printCurrentView("__invitationSuccessCheck")

        self.factory.done = True

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
                if code == smtp.SMTPConstants.SUCCESS:
                    continue

                e = "Failed to send invitation | (%s: %s) | %s | %s | %s |" % (self.collectionName, 
                                                                               self.url, 
                                                                               email, code, str)
                errorText.append(e)

            err = '\n'.join(errorText)

            self.log.error(err)
            NotifyUIAsync(_(err), alert=True)

        self.__cleanup()

    def __invitationFailure(self, result):
        if __debug__:
            self.printCurrentView("__invitationFailure")

        self.factory.done = True

        try:
            desc = result.value.resp
        except:
            desc = result.value

        e = "Failed to send invitation | (%s: %s) | %s |" % (self.collectionName, self.url,
                                                             desc)
        self.log.error(e)
        NotifyUIAsync(e, alert=True)
        self.__cleanup()

    def __cleanup(self):
        self.account = None
        self.url = None
        self.collectionName = None
        self.from_addr = None
        self.sendToList = None

    def __createMessageText(self):
        sendStr = "%s%s%s" % (self.url, SharingConstants.SHARING_DIVIDER, self.collectionName)

        messageObject = common.getChandlerTransportMessage()
        messageObject[getChandlerSharingHeader()] = sendStr
        messageObject['From'] = self.from_addr
        messageObject['To'] = ', '.join(self.sendToList)
        messageObject['Message-ID'] = message.createMessageID()
        messageObject['User-Agent'] = common.CHANDLER_USERAGENT

        return messageObject.as_string()

    def __getData(self):
        """If accountUUID is None will return the first SMTPAccount found""" 
        self.account, replyToAddress = smtp.getSMTPAccount(self.accountUUID)
        self.from_addr = replyToAddress.emailAddress


def getChandlerSharingHeader():
    return message.createChandlerHeader(SharingConstants.SHARING_HEADER)
