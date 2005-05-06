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
import osaf.current.Current as Current
import application.Globals as Globals
import repository.query.Query as Query
import repository.item.Query as ItemQuery
import chandlerdb.util.uuid as UUID
import email.Utils as Utils
import re as re
import chandlerdb.item.ItemError as ItemError

from repository.util.Path import Path

"""
Design Issues:
      1. Is tries really needed
      2. Date sent string could probally be gotten rid of
"""



class MailParcel(application.Parcel.Parcel):

    def startupParcel(self):
        super(MailParcel, self).startupParcel()

        itemKind = self.findPath('//Schema/Core/Item')
        contentitemsPath = ContentModel.ContentModel.contentItemsPath

        def makeContainer(parent, name, child):
            if child is None:
                return itemKind.newItem(name, parent)
            else:
                return child

        self.walk(Path(contentitemsPath, 'mailItems'),
                  makeContainer)


    def getMailItemParent(cls, view, inbound=False):
        return ContentModel.ContentModel.getContentItemParent(view)['mailItems']

    getMailItemParent = classmethod(getMailItemParent)

    def getSMTPAccount(cls, view, uuid=None):
        """
            This method returns a tuple containing:
            1. The an C{SMTPAccount} account
            2. The ReplyTo C{EmailAddress} associated with the C{SMTPAccounts}
               parent which will either be a POP or IMAP Acccount.

        @param uuid: The C{uuid} of the C{SMTPAccount}. If no C{uuid} passed will return
                     the current  C{SMTPAccount}
        @type uuid: C{uuid}
        @return C{tuple} in the form (C{SMTPAccount}, C{EmailAddress})
        """

        smtpAccount = None
        replyToAddress = None

        if uuid is not None:
            smtpAccount = view.findUUID(uuid)

            if smtpAccount is not None:
                for acc in smtpAccount.accounts:
                    if acc.isActive and acc.host and \
                       acc.username and hasattr(acc, 'replyToAddress'):
                        replyToAddress = acc.replyToAddress
                        break

            return (smtpAccount, replyToAddress)

        """Get the default IMAP Account"""
        parentAccount = Current.Current.get(view, "IMAPAccount")

        if parentAccount is None:
            """Get the default POP Account"""
            parentAccount = Current.Current.get(view, "POPAccount")

        if parentAccount is not None:
            if hasattr(parentAccount, 'replyToAddress'):
                replyToAddress = parentAccount.replyToAddress

            """Get the default SMTP Account"""
            try:
                smtpAccount = parentAccount.defaultSMTPAccount

            except ItemError.NoValueForAttributeError:
                pass

        return(smtpAccount, replyToAddress)

    getSMTPAccount = classmethod(getSMTPAccount)


    def getPOPAccount(cls, view, uuid=None):
        """
        This method returns a C{POPAccount} in the Repository. If uuid is not
        None will try and retrieve the C{POPAccount} that has the uuid passed.
        Otherwise the method will try and retrieve the current C{POPAccount}.

        @param uuid: The C{uuid} of the C{POPAccount}. If no C{uuid} passed will return
                 the current C{POPAccount}
        @type uuid: C{uuid}
        @return C{POPAccount}
        """

        if uuid is not None:
            account = view.findUUID(uuid)

        else:
            account = Current.Current.get(view, "POPAccount")

        return account

    getPOPAccount = classmethod(getPOPAccount)


    def getIMAPAccount(cls, view, uuid=None):
        """
        This method returns a C{IMAPAccount} in the Repository. If uuid is not
        None will try and retrieve the C{IMAPAccount} that has the uuid passed.
        Otherwise the method will try and retrieve the current C{IMAPAccount}.

        @param uuid: The C{uuid} of the C{IMAPAccount}. If no C{uuid} passed will return
                 the current C{IMAPAccount}
        @type uuid: C{uuid}
        @return C{IMAPAccount}
        """

        if uuid is not None:
            account = view.findUUID(uuid)

        else:
            account = Current.Current.get(view, "IMAPAccount")

        return account

    getIMAPAccount = classmethod(getIMAPAccount)


    def getActivePOPAccounts(cls, view):
        kind = "//parcels/osaf/contentmodel/mail/POPAccount"
        for item in ItemQuery.KindQuery().run([view.findPath(kind)]):
            if item.isActive and item.host and item.username:
                yield item

    getActivePOPAccounts = classmethod(getActivePOPAccounts)


    def getActiveIMAPAccounts(cls, view):
        kind = "//parcels/osaf/contentmodel/mail/IMAPAccount"
        for item in ItemQuery.KindQuery().run([view.findPath(kind)]):
            if item.isActive and item.host and item.username:
                yield item

    getActiveIMAPAccounts = classmethod(getActiveIMAPAccounts)


    def getActiveSMTPAccounts(cls, view):
        kind = "//parcels/osaf/contentmodel/mail/SMTPAccount"
        for item in ItemQuery.KindQuery().run([view.findPath(kind)]):
            if item.isActive and item.host and item.username:
                yield item

    getActiveSMTPAccounts = classmethod(getActiveSMTPAccounts)


class AccountBase(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/AccountBase"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(AccountBase, self).__init__(name, parent, kind, view)


class DownloadAccountBase(AccountBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/DownloadAccountBase"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(DownloadAccountBase, self).__init__(name, parent, kind, view)

class SMTPAccount(AccountBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/SMTPAccount"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(SMTPAccount, self).__init__(name, parent, kind, view)

        self.accountType = "SMTP"

class IMAPAccount(DownloadAccountBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/IMAPAccount"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(IMAPAccount, self).__init__(name, parent, kind, view)

        self.accountType = "IMAP"


class POPAccount(DownloadAccountBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/POPAccount"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(POPAccount, self).__init__(name, parent, kind, view)

        self.accountType = "POP"


class MailDeliveryError(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MailDeliveryError"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(MailDeliveryError, self).__init__(name, parent, kind, view)

    def __str__(self):
        if self.isStale():
            return super(MailDeliveryError, self).__str__()
            # Stale items shouldn't go through the code below

        return "| %d | %s | %s |" % (self.errorCode, self.errorString, self.errorDate.strftime())


class MailDeliveryBase(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MailDeliveryBase"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(MailDeliveryBase, self).__init__(name, parent, kind, view)


class SMTPDelivery(MailDeliveryBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/SMTPDelivery"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)
        super(SMTPDelivery, self).__init__(name, parent, kind, view)


        self.deliveryType = "SMTP"
        self.state = "DRAFT"

    def sendFailed(self):
        """
          Called from the Twisted thread to log errors in Send.
        """
        self.history.append("FAILED")
        self.state = "FAILED"

        self.tries += 1

    def sendSucceeded(self):
        """
          Called from the Twisted thread to log successes in Send.
        """
        self.history.append("SENT")
        self.state = "SENT"
        self.tries += 1


class IMAPDelivery(MailDeliveryBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/IMAPDelivery"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(IMAPDelivery, self).__init__(name, parent, kind, view)

        self.deliveryType = "IMAP"


class POPDelivery(MailDeliveryBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/POPDelivery"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(POPDelivery, self).__init__(name, parent, kind, view)

        self.deliveryType = "POP"


class MIMEBase(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMEBase"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMEBase, self).__init__(name, parent, kind, view)

class MIMENote(MIMEBase):
    # @@@MOR This used to subclass Notes.Note also, but since that superKind
    # was removed from MIMENote's superKinds list

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMENote"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMENote, self).__init__(name, parent, kind, view)

class MIMEContainer(MIMEBase):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMEContainer"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMEContainer, self).__init__(name, parent, kind, view)

class MailMessageMixin(MIMEContainer):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MailMessageMixin"

    """
      Mail Message Mixin is the bag of Message-specific attributes.

    """
    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MailMessageMixin, self).__init__(name, parent, kind, view)

        self.mimeType = "message/rfc822"

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
        # default the fromAddress to any super class "whoFrom" definition
        try:
            whoFrom = self.getAnyWhoFrom()

            # I only want an EmailAddress
            if not isinstance(whoFrom, EmailAddress):
                whoFrom = EmailAddress.getCurrentMeEmailAddress(self.itsView)

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

        #self.outgoingMessage() # default to outgoing message
        self.isOutbound = True

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


    def outgoingMessage(self, account, type='SMTP'):
        assert type == "SMTP", "Only SMTP currently supported"

        assert isinstance(account, SMTPAccount)

        if self.deliveryExtension is None:
            self.deliveryExtension = SMTPDelivery(view=self.itsView)

        self.isOutbound = True
        self.parentAccount = account

    def incomingMessage(self, account, type="IMAP"):
        assert isinstance(account, DownloadAccountBase)

        if self.deliveryExtension is None:
            if type == "IMAP":
                 self.deliveryExtension = IMAPDelivery(view=self.itsView)
            elif type == "POP":
                 self.deliveryExtension = POPDelivery(view=self.itsView)

        self.isInbound = True
        self.parentAccount = account

    def getAttachments(self):
        """ First pass at API will be expanded upon later """
        return self.mimeParts

    def getNumberOfAttachments(self):
        """ First pass at API will be expanded upon later """
        return len(self.mimeParts)

    def hasAttachments(self):
        """ First pass at API will be expanded upon later """
        return self.hasMimeParts


    def shareSend(self):
        """
        Share this item, or Send if it's an Email
        We assume we want to send this MailMessage here.
        """
        # message the main view to do the work
        Globals.views[0].postEventByName('SendMail', {'item': self})

class MailMessage(MailMessageMixin, Notes.Note):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MailMessage"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(MailMessage, self).__init__(name, parent, kind, view)

class MIMEBinary(MIMENote):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMEBinary"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMEBinary, self).__init__(name, parent, kind, view)

class MIMEText(MIMENote):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMEText"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMEText, self).__init__(name, parent, kind, view)


class MIMESecurity(MIMEContainer):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/MIMESecurity"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(MIMESecurity, self).__init__(name, parent, kind, view)

class EmailAddress(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/mail/EmailAddress"

    def __init__(self, name=None, parent=None, kind=None, view=None, clone=None):
        if parent is None:
            if view is None:
                view = kind.itsView
            parent = MailParcel.getMailItemParent(view)

        super(EmailAddress, self).__init__(name, parent, kind, view)

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
            if self is self.getCurrentMeEmailAddress(self.itsView):
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

    def getEmailAddress(cls, view, nameOrAddressString, fullName=''):
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
            return cls.getCurrentMeEmailAddress(view)

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
            addrQuery = Query.Query(view.repository, queryString)
            addrQuery.args = [ address, name ]
            addresses = addrQuery

        else:
            # old slow query method
            emailAddressKind = EmailAddress.getKind(view)
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
                newAddress = EmailAddress(view=view)
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
        assert isinstance(emailAddressOne, (str, unicode))
        assert isinstance(emailAddressTwo, (str, unicode))

        emailAddressOne = Utils.parseaddr(emailAddressOne)[1]
        emailAddressTwo = Utils.parseaddr(emailAddressTwo)[1]

        return emailAddressOne.lower() == emailAddressTwo.lower()

    emailAddressesAreEqual = classmethod(emailAddressesAreEqual)

    def getCurrentMeEmailAddress(cls, view):
        """
          Lookup the "me" EmailAddress.
        The "me" EmailAddress is whichever entry is the current IMAP default
        address.
        """

        account = MailParcel.getIMAPAccount(view)

        if account is None:
            account = MailParcel.getPOPAccount(view)

        if account is not None and hasattr(account, 'replyToAddress'):
            return account.replyToAddress

        return None

    getCurrentMeEmailAddress = classmethod(getCurrentMeEmailAddress)


