""" Classes used for Mail parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel

# Module globals for Kinds
# AttachmentKind ==> //parcels/OSAF/contentmodel/mail/Attachment
# EmailAccountKind ==> //parcels/OSAF/contentmodel/mail/EmailAccount
# EmailAddressKind ==> //parcels/OSAF/contentmodel/mail/EmailAddress
# MailMessageKind ==> //parcels/OSAF/contentmodel/mail/MailMessage

class MailParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)

        global AttachmentKind
        AttachmentKind = self.find('Attachment')
        assert AttachmentKind

        global EmailAccountKind
        EmailAccountKind = self.find('EmailAccount')
        assert EmailAccountKind

        global EmailAddressKind
        EmailAddressKind = self.find('EmailAddress')
        assert EmailAddressKind

        global MailMessageKind
        MailMessageKind = self.find('MailMessage')
        assert MailMessageKind

class MailMessage(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = MailMessageKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class Attachment(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = AttachmentKind
        Item.Item.__init__(self, name, parent, kind)

class EmailAccount(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = EmailAccountKind
        Item.Item.__init__(self, name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = EmailAddressKind
        Item.Item.__init__(self, name, parent, kind)



