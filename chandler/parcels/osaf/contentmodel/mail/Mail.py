""" Classes used for Mail parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import application.Globals as Globals

class MailParcel(application.Parcel.Parcel):

    def startupParcel(self):
        super(MailParcel, self).startupParcel()
        self._setUUIDs()

    def onItemLoad(self):
        super(MailParcel, self).onItemLoad()
        self._setUUIDs()

    def _setUUIDs(self):
        accountBaseKind = self['AccountBase']
        MailParcel.accountBaseKindID = accountBaseKind.itsUUID

        imapAccountKind = self['IMAPAccount']
        MailParcel.imapAccountKindID = imapAccountKind.itsUUID

        smtpAccountKind = self['SMTPAccount']
        MailParcel.smtpAccountKindID = smtpAccountKind.itsUUID

        mailDeliveryErrorKind = self['MailDeliveryError']
        MailParcel.mailDeliveryErrorKindID = mailDeliveryErrorKind.itsUUID

        mailDeliveryBaseKind = self['MailDeliveryBase']
        MailParcel.mailDeliveryBaseKindID = mailDeliveryBaseKind.itsUUID

        smtpDeliveryKind = self['SMTPDelivery']
        MailParcel.smtpDeliveryKindID = smtpDeliveryKind.itsUUID

        imapDeliveryKind = self['IMAPDelivery']
        MailParcel.imapDeliveryKindID = imapDeliveryKind.itsUUID

        mimeBaseKind = self['MIMEBase']
        MailParcel.mimeBaseKindID = mimeBaseKind.itsUUID

        mimeNoteKind = self['MIMENote']
        MailParcel.mimeNoteKindID = mimeNoteKind.itsUUID

        mailMessageKind = self['MailMessage']
        MailParcel.mailMessageKindID = mailMessageKind.itsUUID

        mailMessageMixinKind = self['MailMessageMixin']
        MailParcel.mailMessageMixinKindID = mailMessageMixinKind.itsUUID

        mimeBinaryKind = self['MIMEBinary']
        MailParcel.mimeBinaryKindID = mimeBinaryKind.itsUUID

        mimeTextKind = self['MIMEText']
        MailParcel.mimeTextKindID = mimeTextKind.itsUUID

        mimeContainerKind = self['MIMEContainer']
        MailParcel.mimeContainerKindID = mimeContainerKind.itsUUID

        mimeSecurityKind = self['MIMESecurity']
        MailParcel.mimeSecurityKindID = mimeSecurityKind.itsUUID

        emailAddressKind = self['EmailAddress']
        MailParcel.emailAddressKindID = emailAddressKind.itsUUID

    def getAccountBaseKind(cls):
        assert cls.accountBaseKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.accountBaseKindID]

    getAccountBaseKind = classmethod(getAccountBaseKind)

    def getIMAPAccountKind(cls):
        assert cls.imapAccountKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.imapAccountKindID]

    getIMAPAccountKind = classmethod(getIMAPAccountKind)

    def getSMTPAccountKind(cls):
        assert cls.smtpAccountKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.smtpAccountKindID]

    getSMTPAccountKind = classmethod(getSMTPAccountKind)

    def getMailDeliveryErrorKind(cls):
        assert cls.mailDeliveryErrorKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mailDeliveryErrorKindID]

    getMailDeliveryErrorKind = classmethod(getMailDeliveryErrorKind)

    def getMailDeliveryBaseKind(cls):
        assert cls.mailDeliveryBaseKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mailDeliveryBaseKindID]

    getMailDeliveryBaseKind = classmethod(getMailDeliveryBaseKind)


    def getSMTPDeliveryKind(cls):
        assert cls.smtpDeliveryKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.smtpDeliveryKindID]

    getSMTPDeliveryKind = classmethod(getSMTPDeliveryKind)

    def getIMAPDeliveryKind(cls):
        assert cls.imapDeliveryKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.imapDeliveryKindID]

    getIMAPDeliveryKind = classmethod(getIMAPDeliveryKind)

    def getMIMEBaseKind(cls):
        assert cls.mimeBaseKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeBaseKindID]

    getMIMEBaseKind = classmethod(getMIMEBaseKind)

    def getMIMENoteKind(cls):
        assert cls.mimeNoteKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeNoteKindID]

    getMIMENoteKind = classmethod(getMIMENoteKind)

    def getMailMessageKind(cls):
        assert cls.mailMessageKindID, "Mail message not yet loaded"
        return Globals.repository[cls.mailMessageKindID]

    getMailMessageKind = classmethod(getMailMessageKind)

    def getMailMessageMixinKind(cls):
        assert cls.mailMessageMixinKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mailMessageMixinKindID]

    getMailMessageMixinKind = classmethod(getMailMessageMixinKind)

    def getMIMEBinaryKind(cls):
        assert cls.mimeBinaryKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeBinaryKindID]

    getMIMEBinaryKind = classmethod(getMIMEBinaryKind)

    def getMIMETextKind(cls):
        assert cls.mimeTextKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeTextKindID]

    getMIMETextKind = classmethod(getMIMETextKind)

    def getMIMEContainerKind(cls):
        assert cls.mimeContainerKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeContainerKindID]

    getMIMEContainerKind = classmethod(getMIMEContainerKind)

    def getMIMESecurityKind(cls):
        assert cls.mimeSecurityKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.mimeSecurityKindID]

    getMIMESecurityKind = classmethod(getMIMESecurityKind)

    def getEmailAddressKind(cls):
        assert cls.emailAddressKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.emailAddressKindID]

    getEmailAddressKind = classmethod(getEmailAddressKind)

    accountBaseKindID = None
    imapAccountKindID = None
    smtpAccountKindID = None
    mailDeliveryErrorKindID = None
    mailDeliveryBaseKindID = None
    smtpDeliveryKindID = None
    imapDeliveryKindID = None
    mimeBaseKindID = None
    mimeNoteKindID = None
    mailMessageKindID = None
    mailMessageMixinKindID = None
    mimeBinaryKindID = None
    mimeTextKindID = None
    mimeContainerKindID = None
    mimeSecurityKindID = None
    emailAddressKindID = None

class AccountBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getAccountBaseKind()
        super (AccountBase, self).__init__(name, parent, kind)

class SMTPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getSMTPAccountKind()
        super (SMTPAccount, self).__init__(name, parent, kind)

        self.accountType = "SMTP"

class IMAPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getIMAPAccountKind()
        super (IMAPAccount, self).__init__(name, parent, kind)

        self.accountType = "IMAP"


class MailDeliveryError(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMailDeliveryErrorKind()
        super (MailDeliveryError, self).__init__(name, parent, kind)

    def __str__(self):
        return "Error Code: %d Error: %s Error Date: %s" % (self.errorCode, self.errorString, self.errorDate.strftime())


class MailDeliveryBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMailDeliveryBaseKind()
        super (MailDeliveryBase, self).__init__(name, parent, kind)


class SMTPDelivery(MailDeliveryBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getSMTPDeliveryKind()
        super (SMTPDelivery, self).__init__(name, parent, kind)

        self.deliveryType = "SMTP"
        self.state = "DRAFT"

    #XXX: Will want to expand state to an object with error or sucess code 
    #     desc string, and date
    def sendFailed(self):
        self.history.append("FAILED")
        self.state = "FAILED"
        self.tries += 1

    #XXX: See comments above
    def sendSucceeded(self):
        self.history.append("SENT")
        self.state = "SENT"
        self.tries += 1


class IMAPDelivery(MailDeliveryBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getIMAPDeliveryKind()
        super (IMAPDelivery, self).__init__(name, parent, kind)

        self.deliveryType = "IMAP"

class MIMEBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMEBaseKind()
        super (MIMEBase, self).__init__(name, parent, kind)

class MIMENote(Notes.Note, MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMENoteKind()
        super (MIMENote, self).__init__(name, parent, kind)

class MIMEContainer(MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMEContainerKind()
        super (MIMEContainer, self).__init__(name, parent, kind)

class MailMessageMixin(MIMEContainer):
    """
      Mail Message Mixin is the bag of Message-specific attributes.

    """
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMailMessageMixinKind()
        super (MailMessageMixin, self).__init__(name, parent, kind)

        self.mimeType = "MESSAGE"

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(MailMessageMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.outgoingMessage()


    def outgoingMessage(self, type="SMTP", account=None):
        if type != "SMTP":
            raise TypeError("Only SMTP currently supported")

        if account is None:
            accountKind = MailParcel.getSMTPAccountKind()

            """Get the first SMTP Account"""
            for acc in Query.KindQuery().run([accountKind]):
                acccount = acc
                break

            if account is None:
                raise Exception("No SMTP Account exists in the Repository")

        #XXX:SAdd test to make sure it is an item
        elif not account.isItemOf(MailParcel.getSMTPAccountKind()):
            raise TypeError("Only SMTP Accounts Supported")

        self.deliveryExtension = SMTPDelivery()
        self.isOutbound = True
        self.parentAccount = account


    def incomingMessage(self, type="IMAP", account=None):
        if type != "IMAP":
            raise TypeError("Only IMAP currently supported")

        if account is None:
            accountKind = MailParcel.getIMAPAccountKind()

            """Get the first IMAP Account"""
            for acc in Query.KindQuery().run([accountKind]):
                acccount = acc
                break

            if account is None:
                raise Exception("No IMAP Account exists in the Repository")

        #XXX:SAdd test to make sure it is an item
        elif not account.isItemOf(MailParcel.getIMAPAccountKind()):
            raise TypeError("Only IMAP Accounts Supported")

        self.deliveryExtension = IMAPDelivery()
        self.isInbound = True
        self.parentAccount = account


class MailMessage(Notes.Note, MailMessageMixin):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = MailParcel.getMailMessageKind()
        super (MailMessage, self).__init__(name, parent, kind)

class MIMEBinary(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMEBinaryKind()
        super (MIMEBinary, self).__init__(name, parent, kind)

class MIMEText(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMETextKind()
        super (MIMEText, self).__init__(name, parent, kind)


class MIMESecurity(MIMEContainer):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getMIMESecurityKind()
        super (MIMESecurity, self).__init__(name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getEmailAddressKind()
        super (EmailAddress, self).__init__(name, parent, kind)



