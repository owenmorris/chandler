""" Classes used for Mail parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class MailParcel(application.Parcel.Parcel):
    def startupParcel(self):
        super(MailParcel, self).startupParcel()
        self._setUUIDs()

    def onItemLoad(self):
        super(MailParcel, self).onItemLoad()
        self._setUUIDs()

    def _setUUIDs(self):
        attachmentKind = self['Attachment']
        MailParcel.attachmentKindID = attachmentKind.itsUUID
        
        emailAccountKind = self['EmailAccount']
        MailParcel.emailAccountKindID = emailAccountKind.itsUUID
        
        emailAddressKind = self['EmailAddress']
        MailParcel.emailAddressKindID = emailAddressKind.itsUUID
        
        mailMessageKind = self['MailMessage']
        MailParcel.mailMessageKindID = mailMessageKind.itsUUID

    def getAttachmentKind(cls):
        assert cls.attachmentKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.attachmentKindID]

    getAttachmentKind = classmethod(getAttachmentKind)

    def getEmailAccountKind(cls):
        assert cls.emailAccountKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.emailAccountKindID]

    getEmailAccountKind = classmethod(getEmailAccountKind)

    def getEmailAddressKind(cls):
        assert cls.emailAddressKindID, "Mail parcel not yet loaded"
        return Globals.repository[cls.emailAddressKindID]

    getEmailAddressKind = classmethod(getEmailAddressKind)

    def getMailMessageKind(cls):
        assert cls.mailMessageKindID, "Mail message not yet loaded"
        return Globals.repository[cls.mailMessageKindID]

    getMailMessageKind = classmethod(getMailMessageKind)

    attachmentKindID = None
    emailAccountKindID = None
    emailAddressKindID = None
    mailMessageKindID = None

class MailMessage(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = MailParcel.getMailMessageKind()
        super (MailMessage, self).__init__(name, parent, kind)

class Attachment(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getAttachmentKind()
        super (Attachment, self).__init__(name, parent, kind)

class EmailAccount(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getEmailAccountKind()
        super (EmailAccount, self).__init__(name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getEmailAddressKind()
        super (EmailAddress, self).__init__(name, parent, kind)



