""" Classes used for Mail parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class MailParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        self._setUUIDs()

    def onItemLoad(self):
        Parcel.Parcel.onItemLoad(self)
        self._setUUIDs()

    def _setUUIDs(self):
        attachmentKind = self.find('Attachment')
        MailParcel.attachmentKindID = attachmentKind.getUUID()
        
        emailAccountKind = self.find('EmailAccount')
        MailParcel.emailAccountKindID = emailAccountKind.getUUID()
        
        emailAddressKind = self.find('EmailAddress')
        MailParcel.emailAddressKindID = emailAddressKind.getUUID()
        
        mailMessageKind = self.find('MailMessage')
        MailParcel.mailMessageKindID = mailMessageKind.getUUID()

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
        ContentModel.ContentItem.__init__(self, name, parent, kind)

        self.whoAttribute = "replyAddress"
        self.aboutAttribute = "subject"
        self.dateAttribute = "dateRecieved"

class Attachment(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getAttachmentKind()
        Item.Item.__init__(self, name, parent, kind)

class EmailAccount(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getEmailAccountKind()
        Item.Item.__init__(self, name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = MailParcel.getEmailAddressKind()
        Item.Item.__init__(self, name, parent, kind)



