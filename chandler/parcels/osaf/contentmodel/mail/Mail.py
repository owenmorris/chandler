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
import email.Utils as Utils
import re as re

from repository.util.Path import Path

"""
   Notes:
      1. if message is marked already as inbound do not sent
      2. Need to revisit inbound outbound logic
      3. What should and should not be in this layer (Meeting with CPIA and Service Team)
      4. Seems like email address logic is not performant
      5. If not moving email logic here then
         create address api class to handle all email address
         parsing and look up

Design Issues:
      1. Is account type really needed
      2. Is delivery type really needed
      3. Is tries really needed
      4. Are the specific headers really needed or can we just lookup (Save space)
      5. Date sent string could probally be gotten rid of
      6. Can isOutbound isInbound can be replaced by the collection it is in
"""


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


    def getSMTPAccount(cls, UUID=None):
        """
            This method returns a tuple containing:
            1. An C{SMTPAccount} account in the Repository.
            2. The ReplyTo C{EmailAddress} associated with the C{SMTPAccounts}
               parent which will either be a POP or IMAP Acccount.

        The method will throw a C{SMTPException} if:
        1. No C{SMTPAccount} in the Repository
        2. No parent account associated with the C{SMTPAccount}
        3. The replyToAddress of the parent account is None

        @param UUID: The C{UUID} of the C{SMTPAccount}. If no C{UUID} passed will return
                     the default (first) C{SMTPAccount}
        @type UUID: C{UUID}
        @return C{tuple} in the form (C{SMTPAccount}, C{EmailAddress})
        """

        accountKind = MailParcel.getSMTPAccountKind()
        account = None
        replyToAddress = None

        if UUID is not None:
            assert isinstance(UUID.UUID), "The UUID argument must be of type UUID.UUID"
            account = accountKind.findUUID(UUID)

        else:
            """Get the first SMTP Account"""
            for acc in ItemQuery.KindQuery().run([accountKind]):
                account = acc
                if account.isDefault:
                    break

        assert account is not None, "No SMTP Account found"

        accList = account.accounts

        assert accList is not None, "No Parent Accounts associated with the SMTP account. Can not get replyToAddress."

        """Get the first IMAP Account"""
        for parentAccount in accList:
            replyToAddress = parentAccount.replyToAddress
            break

        assert replyToAddress is not None, "No replyToAddress found for IMAP Account"

        return(account, replyToAddress)

    getSMTPAccount = classmethod(getSMTPAccount)

    def getIMAPAccount(cls, UUID=None):
        """
        This method returns a C{IMAPAccount} in the Repository. If UUID is not
        None will try and retrieve the C{IMAPAccount} that has the UUID passed.
        Otherwise the method will try and retrieve the first C{IMAPAccount}
        found in the Repository.

        It will throw a C{IMAPException} if there is either no C{IMAPAccount}
        matching the UUID passed or if there is no C{IMAPAccount}
        at all in the Repository.

        @param UUID: The C{UUID} of the C{IMAPAccount}. If no C{UUID} passed will return
                 the first C{IMAPAccount}
        @type UUID: C{UUID}
        @return C{IMAPAccount}
        """

        accountKind = MailParcel.getIMAPAccountKind()
        account = None

        if UUID is not None:
            account = accountKind.findUUID(UUID)

        else:
            for acc in ItemQuery.KindQuery().run([accountKind]):
                account = acc
                if account.isDefault:
                    break

        assert account is not None, "No IMAP Account exists in Repository"

        return account

    getIMAPAccount = classmethod(getIMAPAccount)


class AccountBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getAccountBaseKind()
        super(AccountBase, self).__init__(name, parent, kind)

class SMTPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getSMTPAccountKind()
        super(SMTPAccount, self).__init__(name, parent, kind)


        #XXX: Is account type really needed
        self.accountType = "SMTP"

class IMAPAccount(AccountBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getIMAPAccountKind()
        super(IMAPAccount, self).__init__(name, parent, kind)

        #XXX: Is account type really needed
        self.accountType = "IMAP"


class MailDeliveryError(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMailDeliveryErrorKind()
        super(MailDeliveryError, self).__init__(name, parent, kind)

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
        super(MailDeliveryBase, self).__init__(name, parent, kind)


class SMTPDelivery(MailDeliveryBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getSMTPDeliveryKind()
        super(SMTPDelivery, self).__init__(name, parent, kind)


        #XXX: Is account type really needed
        self.deliveryType = "SMTP"
        self.state = "DRAFT"

    def sendFailed(self):
        """
          Called from the Twisted thread to log errors in Send.
        """
        self.history.append("FAILED")
        self.state = "FAILED"

        #XXX: Not sure we need this
        self.tries += 1

    def sendSucceeded(self):
        """
          Called from the Twisted thread to log successes in Send.
        """
        self.history.append("SENT")
        self.state = "SENT"
        self.tries += 1


class IMAPDelivery(MailDeliveryBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getIMAPDeliveryKind()

        super(IMAPDelivery, self).__init__(name, parent, kind)

        self.deliveryType = "IMAP"

class MIMEBase(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEBaseKind()

        super(MIMEBase, self).__init__(name, parent, kind)

class MIMENote(Notes.Note, MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMENoteKind()

        super(MIMENote, self).__init__(name, parent, kind)

class MIMEContainer(MIMEBase):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEContainerKind()

        super(MIMEContainer, self).__init__(name, parent, kind)

class MailMessageMixin(MIMEContainer):
    """
      Mail Message Mixin is the bag of Message-specific attributes.

    """
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMailMessageMixinKind()

        super(MailMessageMixin, self).__init__(name, parent, kind)

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(MailMessageMixin, self).InitOutgoingAttributes()
        except AttributeError:
            pass
        MailMessageMixin._initMixin(self) # call our init, not the method of a subclass

    def _initMixin(self):
        """
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        self.mimeType = "MESSAGE"

        # default the fromAddress to any super class "whoFrom" definition
        try:
            whoFrom = self.getAnyWhoFrom()

            # I only want an EmailAddress
            if not isinstance(whoFrom, EmailAddress):
                whoFrom = EmailAddress.getCurrentMeEmailAddress()

            self.fromAddress = whoFrom
        except AttributeError:
            pass # no from address

        # default the toAddress to any super class "who" definition
        try:
            # need to shallow copy the list
            self.toAddress = self.getAnyWho()
        except AttributeError:
            pass

        # default the subject to any super class "about" definition
        try:
            self.subject = self.getAnyAbout()
        except AttributeError:
            pass

        self.outgoingMessage() # default to outgoing message

    def getAnyAbout(self):
        """
        Get any non-empty definition for the "about" attribute.
        """
        try:
            # don't bother returning our default: an empty string 
            if self.subject:
                return self.subject

        except AttributeError:
            pass
        return super(MailMessageMixin, self).getAnyAbout()

    def getAnyWho(self):
        """
        Get any non-empty definition for the "who" attribute.
        """
        try:
            return self.toAddress
        except AttributeError:
            pass

        return super(MailMessageMixin, self).getAnyWho()

    def getAnyWhoFrom(self):
        """
        Get any non-empty definition for the "whoFrom" attribute.
        """
        try:
            return self.fromAddress
        except AttributeError:
            pass

        return super(MailMessageMixin, self).getAnyWhoFrom()



    def outgoingMessage(self, type="SMTP", account=None):
        assert type == "SMTP", "Only SMTP currently supported"

        if account is None:
            account, replyAddress = MailParcel.getSMTPAccount()

        assert account.isItemOf(MailParcel.getSMTPAccountKind()), "Only SMTP Accounts Supported"

        if self.deliveryExtension is None:
            self.deliveryExtension = SMTPDelivery()

        self.isOutbound = True
        self.parentAccount = account

    def incomingMessage(self, type="IMAP", account=None):
        assert type == "IMAP", "Only IMAP currently supported"

        if account is None:
            account = MailParcel.getIMAPAccount()

        assert account.isItemOf(MailParcel.getIMAPAccountKind()), "Only IMAP Accounts Supported"

        if self.deliveryExtension is None:
            self.deliveryExtension = IMAPDelivery()

        self.isInbound = True
        self.parentAccount = account

    def shareSend(self):
        """
        Share this item, or Send if it's an Email
        We assume we want to send this MailMessage here.
        """
        # message the main view to do the work
        targetView = self.itsView.findPath('//parcels/osaf/views/main/MainView')
        targetView.PostEventByName('SendMail', {'item': self})

class MailMessage(MailMessageMixin, Notes.Note):

    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = MailParcel.getMailMessageKind()

        super(MailMessage, self).__init__(name, parent, kind)

class MIMEBinary(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMEBinaryKind()

        super(MIMEBinary, self).__init__(name, parent, kind)

class MIMEText(MIMENote):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMETextKind()

        super(MIMEText, self).__init__(name, parent, kind)


class MIMESecurity(MIMEContainer):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getMIMESecurityKind()

        super(MIMESecurity, self).__init__(name, parent, kind)

class EmailAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None, clone=None):
        if not parent:
            parent = MailParcel.getMailItemParent()
        if not kind:
            kind = MailParcel.getEmailAddressKind()

        super(EmailAddress, self).__init__(name, parent, kind)

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

    def __str__(self):
        """
          User readable string version of this address
        """
        if self.isStale():
            return super(EmailAddress, self).__str__()
            # Stale items shouldn't go through the code below

        try:
            if self is self.getCurrentMeEmailAddress():
                fullName = 'me'
            else:
                fullName = self.fullName
        except AttributeError:
            fullName = ''

        if fullName is not None and len(fullName) > 0:
            if self.emailAddress:
                return fullName + ' <' + self.emailAddress + '>'
            else:
                return fullName
        else:
            return self.getItemDisplayName()

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

    def getEmailAddress(cls, nameOrAddressString, fullName=''):
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
        # @@@DLD remove when we better sort out creation of "me" address w/o an account setup
        if nameOrAddressString is None:
            nameOrAddressString = ''

        # strip the address string of whitespace and question marks
        address = nameOrAddressString.strip ().strip('?')

        # check for "me"
        if address == 'me':
            return cls.getCurrentMeEmailAddress()

        # if no fullName specified, parse apart the name and address if we can
        if fullName != '':
            name = fullName
        else:
            try:
                address.index('<')
            except ValueError:
                name = address
            else:
                name, address = address.split('<')
                address = address.strip('>').strip()
                name = name.strip()
                # ignore a name of "me"
                if name == 'me':
                    name = ''

        # check if the address looks like a valid emailAddress
        isValidAddress = cls.isValidEmailAddress(address)
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
        # @@@DLD - switch on the better queries
        # Need to override compare operators to use emailAddressesAreEqual, 
        #  deal with name=='' cases, name case sensitivity, etc
        useBetterQuery = False

        if useBetterQuery:

            # get all addresses whose emailAddress or fullName match the param
            queryString = u'for i in "//parcels/osaf/contentmodel/mail/EmailAddress" \
                          where i.emailAddress =="$0" or i.fullName =="$1"'
            addrQuery = Query.Query(Globals.repository, queryString)
            addrQuery.args = [ address, name ]
            addresses = addrQuery

        else:
            # old slow query method
            emailAddressKind = MailParcel.getEmailAddressKind()
            allAddresses = ItemQuery.KindQuery().run([emailAddressKind])
            addresses = []
            for candidate in allAddresses:
                if isValidAddress:
                    if cls.emailAddressesAreEqual(candidate.emailAddress, address):
                        # found an existing address!
                        addresses.append(candidate)
                elif name != '' and name == candidate.fullName:
                    # full name match
                    addresses.append(candidate)

        # process the result(s)
        # Hope for a match of both name and address
        # fall back on a match of the address, then name
        addressMatch = None
        nameMatch = None
        for candidate in addresses:
            if isValidAddress:
                if cls.emailAddressesAreEqual(candidate.emailAddress, address):
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

    getEmailAddress = classmethod(getEmailAddress)

    def format(cls, emailAddress):
        assert isinstance(emailAddress, EmailAddress), "You must pass an EmailAddress Object"

        if emailAddress.fullName is not None and len(emailAddress.fullName.strip()) > 0:
            return emailAddress.fullName + " <" + emailAddress.emailAddress + ">"

        return emailAddress.emailAddress

    format = classmethod(format)


    def isValidEmailAddress(cls, emailAddress):
        """
        This method tests an email address for valid syntax as defined RFC 822.
        The method validates addresses in the form 'John Jones <john@test.com>'
        and 'john@test.com'

        @param emailAddress: A string containing a email address to validate.
        @type addr: C{String}
        @return: C{Boolean}
        """

        assert isinstance(emailAddress, (str, unicode)), "Email Address must be in string or unicode format"

        #XXX: Strip any name information. i.e. John test <john@test.com>`from the email address
        emailAddress = Utils.parseaddr(emailAddress)[1]

        return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", emailAddress) is not None


    isValidEmailAddress = classmethod(isValidEmailAddress)

    def emailAddressesAreEqual(cls, emailAddressOne, emailAddressTwo):
        """
        This method tests whether two email addresses are the same.
        Addresses can be in the form john@jones.com or John Jones <john@jones.com>.
        The method strips off the username and <> brakets if they exist and just compares
        the actual email addresses for equality. It will not look to see if each
        address is RFC 822 compliant only that the strings match. Use C{EmailAddress.isValidEmailAddress}
        to test for validity.

        @param emailAddressOne: A string containing a email address to compare.
        @type emailAddressOne: C{String}
        @param emailAddressTwo: A string containing a email address to compare.
        @type emailAddressTwo: C{String}
        @return: C{Boolean}
        """
        assert isinstance(emailAddressOne, (str, unicode)), "Email Address must be in string or unicode format"
        assert isinstance(emailAddressTwo, (str, unicode)), "Email Address must be in string or unicode format"

        emailAddressOne = Utils.parseaddr(emailAddressOne)[1]
        emailAddressTwo = Utils.parseaddr(emailAddressTwo)[1]

        return emailAddressOne.lower() == emailAddressTwo.lower()

    emailAddressesAreEqual = classmethod(emailAddressesAreEqual)

    def getCurrentMeEmailAddress(cls):
        """
          Lookup the "me" EmailAddress.
        The "me" EmailAddress is whichever entry is the current IMAP default
        address.
        """
        return MailParcel.getIMAPAccount().replyToAddress

    getCurrentMeEmailAddress = classmethod(getCurrentMeEmailAddress)


