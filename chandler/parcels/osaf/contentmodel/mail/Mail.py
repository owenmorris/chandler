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
import repository.query.Query as Query
import repository.item.Query as ItemQuery
import chandlerdb.util.UUID as UUID

from repository.util.Path import Path


class MailParcel(application.Parcel.Parcel):

    def startupParcel(self):
        super(MailParcel, self).startupParcel()

        repository = self.itsView
        itemKind = repository.findPath('//Schema/Core/Item')
        contentitemsPath = ContentModel.ContentModel.contentitemsPath
        
        def makeContainer(parent, name, child):
            if child is None:
                return itemKind.newItem(name, parent)
            else:
                return child
        
        repository.walk(Path(contentitemsPath, 'inboundMailItems'),
                        makeContainer)
        repository.walk(Path(contentitemsPath, 'outboundMailItems'),
                        makeContainer)
            
        self._setUUIDs()
        
    def getMailItemParent(cls, inbound=False):

        parent = ContentModel.ContentModel.getContentItemParent()
        if inbound:
            return parent['inboundMailItems']
        else:
            return parent['outboundMailItems']

    getMailItemParent = classmethod(getMailItemParent)

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
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getAccountBaseKind()
        super (AccountBase, self).__init__(name, parent, kind)

class SMTPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getSMTPAccountKind()
        super (SMTPAccount, self).__init__(name, parent, kind)

        self.accountType = "SMTP"

class IMAPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getIMAPAccountKind()
        super (IMAPAccount, self).__init__(name, parent, kind)

        self.accountType = "IMAP"


class MailDeliveryError(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMailDeliveryErrorKind()
        super (MailDeliveryError, self).__init__(name, parent, kind)

    def __str__(self):
        if self.isStale():
            return super(MailDeliveryError, self).__str__()
            # Stale items shouldn't go through the code below

        return "| %d | %s | %s |" % (self.errorCode, self.errorString, self.errorDate.strftime())


class MailDeliveryBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMailDeliveryBaseKind()
        super (MailDeliveryBase, self).__init__(name, parent, kind)


class SMTPDelivery(MailDeliveryBase):
    """
    SMTP Delivery Notification Class
    Some of these methods are called from Twisted, some from 
    the UI Thread.
    """
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getSMTPDeliveryKind()
        super (SMTPDelivery, self).__init__(name, parent, kind)

        self.deliveryType = "SMTP"
        self.state = "DRAFT"

    #XXX: Will want to expand state to an object with error or sucess code 
    #     desc string, and date
    def sendFailed(self):
        """
          Called from the Twisted thread to log errors in Send.
        """
        self.history.append("FAILED")
        self.state = "FAILED"
        self.tries += 1

        # announce to the UI thread that an error occurred
        Globals.wxApplication.CallItemMethodAsync (Globals.mainView,
                                                   'displaySMTPSendError',
                                                   self.mailMessage)

    #XXX: See comments above
    def sendSucceeded(self):
        """
          Called from the Twisted thread to log successes in Send.
        """
        self.history.append("SENT")
        self.state = "SENT"
        self.tries += 1

        # announce to the UI thread that an error occurred
        Globals.wxApplication.CallItemMethodAsync (Globals.mainView,
                                                   'displaySMTPSendSuccess',
                                                   self.mailMessage)


class IMAPDelivery(MailDeliveryBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getIMAPDeliveryKind()
        super (IMAPDelivery, self).__init__(name, parent, kind)

        self.deliveryType = "IMAP"

class MIMEBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEBaseKind()
        super (MIMEBase, self).__init__(name, parent, kind)

class MIMENote(Notes.Note, MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMENoteKind()
        super (MIMENote, self).__init__(name, parent, kind)

class MIMEContainer(MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEContainerKind()
        super (MIMEContainer, self).__init__(name, parent, kind)

class MailMessageMixin(MIMEContainer):
    """
      Mail Message Mixin is the bag of Message-specific attributes.

    """
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMailMessageMixinKind()
        super (MailMessageMixin, self).__init__(name, parent, kind)

        # @@@DLD remove this line, it's being done in _initMixin
        self.mimeType = "MESSAGE"

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(MailMessageMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass
        MailMessageMixin._initMixin (self) # call our init, not the method of a subclass

    def _initMixin (self):
        """ 
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        self.mimeType = "MESSAGE"

        # default the fromAddress to any super class "whoFrom" definition
        try:
            self.fromAddress = self.getAnyWhoFrom ()
        except AttributeError:
            pass # no from address

        # default the toAddress to any super class "who" definition
        try:
            # need to shallow copy the list
            self.toAddress = self.copyValue (self.getAnyWho ())
        except AttributeError:
            pass

        # default the subject to any super class "about" definition
        try:
            self.subject = self.getAnyAbout ()
        except AttributeError:
            pass

        self.outgoingMessage() # default to outgoing message

    def getAnyAbout (self):
        """
        Get any non-empty definition for the "about" attribute.
        """
        try:
            subject = self.subject
            # don't bother returning our default: an empty string 
            if subject:
                return subject
        except AttributeError:
            pass
        return super (MailMessageMixin, self).getAnyAbout ()
    
    def getAnyWho (self):
        """
        Get any non-empty definition for the "who" attribute.
        """
        try:
            return self.toAddress
        except AttributeError:
            pass
        return super (MailMessageMixin, self).getAnyWho ()
    
    def getAnyWhoFrom (self):
        """
        Get any non-empty definition for the "whoFrom" attribute.
        """
        try:
            return self.fromAddress
        except AttributeError:
            pass
        return super (MailMessageMixin, self).getAnyWhoFrom ()

    def defaultSMTPAccount (self):
        import osaf.mail.smtp as smtp

        try:
            account, replyAddress = smtp.getSMTPAccount ()
        except:
            account = None
        return account

    def outgoingMessage(self, type="SMTP", account=None):
        if type != "SMTP":
            raise TypeError("Only SMTP currently supported")

        if account is None:
            account = self.defaultSMTPAccount ()

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
            import osaf.mail.imap as imap
            account = imap.getIMAPAccount ()

        #XXX:SAdd test to make sure it is an item
        elif not account.isItemOf(MailParcel.getIMAPAccountKind()):
            raise TypeError("Only IMAP Accounts Supported")

        self.deliveryExtension = IMAPDelivery()
        self.isInbound = True
        self.parentAccount = account

    def shareSend (self):
        """
          Share this item, or Send if it's an Email
        We assume we want to send this MailMessage here.
        
        """
        # put a "committing" message into the status bar
        self.setStatusMessage ('Committing changes...')

        # commit changes, since we'll be switching to Twisted thread
        Globals.repository.commit()
    
        # get default SMTP account
        account = self.defaultSMTPAccount ()

        # put a sending message into the status bar
        self.setStatusMessage ('Sending mail...')

        # Now send the mail
        import osaf.mail.smtp as smtp
        smtp.SMTPSender(account, self).sendMail()

class MailMessage(MailMessageMixin, Notes.Note):
    
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = MailParcel.getMailMessageKind()
        super (MailMessage, self).__init__(name, parent, kind)

class MIMEBinary(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEBinaryKind()
        super (MIMEBinary, self).__init__(name, parent, kind)

class MIMEText(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMETextKind()
        super (MIMEText, self).__init__(name, parent, kind)


class MIMESecurity(MIMEContainer):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMESecurityKind()
        super (MIMESecurity, self).__init__(name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None, clone=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getEmailAddressKind()
        super (EmailAddress, self).__init__(name, parent, kind)

        # copy the attributes if a clone was supplied
        if clone is not None:
            try:
                self.emailAddress = clone.emailAddress[:]
            except AttributeError:
                pass
            try:
                self.fullName = clone.fullName[:]
            except AttributeError:
                pass

    def __str__ (self):
        """
          User readable string version of this address
        """
        if self.isStale():
            return super(EmailAddress, self).__str__()
            # Stale items shouldn't go through the code below

        if self is self.getCurrentMeEmailAddress():
            fullName = 'me'
        else:
            try:
                fullName = self.fullName
            except AttributeError:
                fullName = ''
        if fullName is not None and len (fullName) > 0:
            if self.emailAddress:
                return fullName + ' <' + self.emailAddress + '>'
            else:
                return fullName
        else:
            return self.getItemDisplayName ()

        """
        Factory Methods
        --------------
        When creating a new EmailAddress, we check for an existing item first.
        We do look them up in the repository to prevent duplicates, but there's
        nothing to keep bad ones from accumulating, although repository
        garbage collection should eventually remove them.
        The "me" entity is used for Items created by the user, and it
        gets a reasonable emailaddress filled in when a send is done.
        This code needs to be reworked!
        """
        
    def getEmailAddress (cls, nameOrAddressString, fullName=''):
        """
          Lookup or create an EmailAddress based on the supplied string.
        If a matching EmailAddress object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.  
        There are two ways to call this method:
            1) with something the user typed in nameOrAddressString, which
                 will be parsed, and no fullName is needed
            2) with an plain email address in the nameOrAddressString, and a 
                 full name in the fullName field
        If a match is found for both name and address then it will be used.
        If there is no name specified, a match on address will be returned.
        If there is no address specified, a match on name will be returned.
        If both name and address are specified, but there's no entry that
          matches both, then a new entry is created.
        @param nameOrAddressString: emailAddress string, or fullName for lookup,
           or both in the form "name <address>"
        @type nameOrAddressString: C{String}
        @param fullName: optional explict fullName when not using the
           "name <address>" form of the nameOrAddressString parameter
        @type fullName: C{String}
        @return: C{EmailAddress} or None if not found, and nameOrAddressString is\
               not a valid email address.
        """
        import osaf.mail.message as message # avoid circularity

        # @@@DLD remove when we better sort out creation of "me" address w/o an account setup
        if nameOrAddressString is None:
            nameOrAddressString = ''

        # strip the address string of whitespace and question marks
        address = nameOrAddressString.strip ().strip ('?')

        # check for "me"
        if address == 'me':
            return cls.getCurrentMeEmailAddress ()

        # if no fullName specified, parse apart the name and address if we can
        if fullName != '':
            name = fullName
        else:
            try:
                address.index ('<')
            except ValueError:
                name = address
            else:
                name, address = address.split ('<')
                address = address.strip ('>').strip ()
                name = name.strip ()
                # ignore a name of "me"
                if name == 'me':
                    name = ''

        # check if the address looks like a valid emailAddress
        isValidAddress = message.isValidEmailAddress (address)
        if not isValidAddress:
            address = None

        """
        At this point we should have:
            name - the name to search for, or ''
            address - the address to search for, or None
        If the user specified a single word which could also be a valid
        email address, we could have that word in both the address and
        name variables.
        """
        # DLDTBD - switch on the better queries
        # Need to override compare operators to use emailAddressesAreEqual, 
        #  deal with name=='' cases, name case sensitivity, etc
        useBetterQuery = False
        if useBetterQuery:

            # get all addresses whose emailAddress or fullName match the param
            queryString = u'for i in "//parcels/osaf/contentmodel/mail/EmailAddress" \
                          where i.emailAddress =="$0" or i.fullName =="$1"'
            addrQuery = Query.Query (Globals.repository, queryString)
            addrQuery.args = [ address, name ]
            addresses = addrQuery

        else:
            # old slow query method
            emailAddressKind = MailParcel.getEmailAddressKind ()
            allAddresses = ItemQuery.KindQuery().run([emailAddressKind])
            addresses = []
            for candidate in allAddresses:
                if isValidAddress:
                    if message.emailAddressesAreEqual(candidate.emailAddress, address):
                        # found an existing address!
                        addresses.append (candidate)
                elif name != '' and name == candidate.fullName:
                    # full name match
                    addresses.append (candidate)

        # process the result(s)
        # Hope for a match of both name and address
        # fall back on a match of the address, then name
        addressMatch = None
        nameMatch = None
        for candidate in addresses:
            if isValidAddress:
                if message.emailAddressesAreEqual(candidate.emailAddress, address):
                    # found an existing address match
                    addressMatch = candidate
            if name != '' and name == candidate.fullName:
                # full name match
                nameMatch = candidate
                if addressMatch is not None:
                    # matched both
                    return addressMatch
        else:
            # no double-matches found
            if name == address:
                name = ''
            if addressMatch is not None and name == '':
                return addressMatch
            if nameMatch is not None and address is None:
                return nameMatch
            if isValidAddress:
                # make a new EmailAddress
                newAddress = EmailAddress()
                newAddress.emailAddress = address
                newAddress.fullName = name
                return newAddress
            else:
                return None
    getEmailAddress = classmethod (getEmailAddress)


    def getCurrentMeEmailAddress (cls):
        """
          Lookup the "me" EmailAddress.
        The "me" EmailAddress is whichever entry is the current IMAP default 
        address.
        """
        import osaf.mail.imap as imap

        return imap.getIMAPAccount().replyToAddress
    getCurrentMeEmailAddress = classmethod (getCurrentMeEmailAddress)
