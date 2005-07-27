""" Classes used for Mail parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.mail"

import application
from application import schema
import repository.item.Item as Item
from osaf.contentmodel import ContentModel, Notes
import osaf.current.Current as Current
import application.Globals as Globals
import repository.query.Query as Query
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

MAIL_DEFAULT_PATH = "//userdata"


def getCurrentSMTPAccount(view, uuid=None, includeInactives=False):
    """
        This function returns a tuple containing:
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
                if acc.isActive or includeInactives:
                    if acc.host and acc.username and \
                       hasattr(acc, 'replyToAddress'):
                        replyToAddress = acc.replyToAddress
                        break

        return (smtpAccount, replyToAddress)

    """Get the default Mail Account"""
    parentAccount = Current.get(view, "MailAccount")

    if parentAccount is not None:
        if hasattr(parentAccount, 'replyToAddress'):
            replyToAddress = parentAccount.replyToAddress

        """Get the default SMTP Account"""
        try:
            smtpAccount = parentAccount.defaultSMTPAccount

        except ItemError.NoValueForAttributeError:
            pass

    return(smtpAccount, replyToAddress)


def getCurrentMailAccount(view, uuid=None):
    """
    This function returns either an C{IMAPAccount} or C{POPAccount} in the
    Repository. If uuid is not None will try and retrieve the account that
    has the uuid passed.  Otherwise the method will try and retrieve the
    current C{IMAPAccount} or C{POPAccount}.

    @param uuid: The C{uuid} of the account. If no C{uuid} passed will return the current account
    @type uuid: C{uuid}
    @return C{IMAPAccount} or C{POPAccount}
    """

    if uuid is not None:
        account = view.findUUID(uuid)

    else:
        account = Current.get(view, "MailAccount")

    return account


class connectionSecurityEnum(schema.Enumeration):
    schema.kindInfo(displayName="Connection Security Enumeration")
    values = "NONE", "TLS", "SSL"


class AccountBase(ContentModel.ContentItem):

    schema.kindInfo(
        displayName="Account base kind",
        description="The base kind for various account kinds, such as "
                    "IMAP, SMTP, WebDav"
    )

    numRetries = schema.One(
        schema.Integer,
        displayName = 'Number of Retries',
        doc = 'How many times to retry before giving up',
        initialValue = 1,
    )
    username = schema.One(
        schema.String,
        displayName = 'Username',
        doc = 'The account login name',
        initialValue = '',
    )
    password = schema.One(
        schema.String,
        displayName = 'Password',
        doc = 'This could either be a password or some other sort of '
              'authentication info. We can use it for whatever is needed '
              'for this account type.',
        issues = [
            'This should not be a simple string. We need some solution for '
            'encrypting it.'
        ],
        initialValue = '',
    )
    host = schema.One(
        schema.String,
        displayName = 'Host',
        doc = 'The hostname of the account',
        initialValue = '',
    )
    port = schema.One(
        schema.Integer, displayName = 'Port', doc = 'The port number to use',
    )
    connectionSecurity = schema.One(
        connectionSecurityEnum,
        displayName = 'Connection Security',
        doc = 'The security mechanism to leverage for a network connection',
        initialValue = 'NONE',
    )
    pollingFrequency = schema.One(
        schema.Integer,
        displayName = 'Polling frequency',
        doc = 'Frequency in seconds',
        initialValue = 300,
    )
    mailMessages = schema.Sequence(
        'MailMessageMixin',
        displayName = 'Mail Messages',
        doc = 'Mail Messages sent or retrieved with this account ',
        initialValue = [],
        inverse = 'parentAccount',
    )
    timeout = schema.One(
        schema.Integer,
        displayName = 'Timeout',
        doc = 'The number of seconds before timing out a stalled connection',
        initialValue = 60,
    )
    isActive = schema.One(
        schema.Boolean,
        displayName = 'Is active',
        doc = 'Whether or not an account should be used for sending or '
              'fetching email',
        initialValue = True,
    )

    __default_path__ = MAIL_DEFAULT_PATH

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host and item.username:
                yield item


class DownloadAccountBase(AccountBase):

    schema.kindInfo(
        displayName="Download Account Base",
        description="Base Account for protocols that download mail",
    )

    defaultSMTPAccount = schema.One(
        'SMTPAccount',
        displayName = 'Default SMTP Account',
        doc = 'Which SMTP account to use for sending mail from this account',
        initialValue = None,
        inverse = 'accounts',
    )
    downloadMax = schema.One(
        schema.Integer,
        displayName = 'Download Max',
        doc = 'The maximum number of messages to download before forcing a repository commit',
        initialValue = 50,
    )
    replyToAddress = schema.One(
        'EmailAddress',
        displayName = 'Reply-To Address',
        initialValue = None,
        inverse = 'accounts',
    )
    emailAddress = schema.One(
        displayName = 'Reply-To Address (Redirect)',
        redirectTo = 'replyToAddress.emailAddress',
    )
    fullName = schema.One(
        displayName = 'Full Name (Redirect)',
        redirectTo = 'replyToAddress.fullName',
    )


class SMTPAccount(AccountBase):

    accountType = "SMTP"

    schema.kindInfo(
        displayName="SMTP Account",
        description="An SMTP Account",
    )

    port = schema.One(
        schema.Integer,
        displayName = 'Port',
        doc = 'The non-SSL port number to use',
        issues = [
            "In order to get a custom initialValue for this attribute for an "
            "SMTPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase",
        ],
        initialValue = 25,
    )
    useAuth = schema.One(
        schema.Boolean,
        displayName = 'Use Authentication',
        doc = 'Whether or not to use authentication when sending mail',
        initialValue = False,
    )
    accounts = schema.Sequence(
        DownloadAccountBase,
        displayName = 'Accounts',
        doc = 'Which accounts use this SMTP account as their default',
        initialValue = [],
        inverse = DownloadAccountBase.defaultSMTPAccount,
    )
    signature = schema.One(
        schema.String,
        issues = [
            'Basic signiture addition to an outgoing message will be refined '
            'in future releases',
        ],
    )


class IMAPAccount(DownloadAccountBase):

    accountType = "IMAP"

    schema.kindInfo(
        displayName = "IMAP Account",
        description = "An IMAP Account",
    )

    port = schema.One(
        schema.Integer,
        displayName = 'Port',
        doc = 'The non-SSL port number to use',
        issues = [u"In order to get a custom initialValue for this attribute for an IMAPAccount, I defined a 'duplicate' attribute, also named 'port', which normally would have been inherited from AccountBase"],
        initialValue = 143,
    )
    messageDownloadSequence = schema.One(
        schema.Long,
        displayName = 'Message Download Sequence',
        initialValue = 0L,
    )


class POPAccount(DownloadAccountBase):

    accountType = "POP"

    schema.kindInfo(
        displayName = "POP Account",
        description = "An POP Account",
    )
    port = schema.One(
        schema.Integer,
        displayName = 'Port',
        doc = 'The non-SSL port number to use',
        issues = [u"In order to get a custom initialValue for this attribute for a POPAccount, I defined a 'duplicate' attribute, also named 'port', which normally would have been inherited from AccountBase"],
        initialValue = 110,
    )
    downloadedMessageUIDS = schema.Mapping(
        schema.String,
        displayName = 'Downloaded Message UID',
        doc = 'Used for quick look up to discover if a message has already been downloaded',
        initialValue = {},
    )
    leaveOnServer = schema.One(
        schema.Boolean,
        displayName = 'Leave Mail On Server',
        doc = 'Whether or not to leave messages on the server after downloading',
        initialValue = True,
    )


class MailDeliveryError(ContentModel.ContentItem):

    schema.kindInfo(
        displayName="Mail Delivery Error kind",
        description=
            "Contains the error data associated with a MailDelivery Type"
    )

    errorCode = schema.One(
        schema.Integer,
        displayName = 'The Error Code',
        doc = 'The Error Code returned by the Delivery Transport',
        initialValue = 0,
    )
    errorString = schema.One(schema.String, initialValue = '')
    errorDate = schema.One(schema.DateTime)
    mailDelivery = schema.One(
        'MailDeliveryBase',
        displayName = 'Mail Delivery',
        doc = 'The Mail Delivery that cause this error',
        initialValue = None,
        inverse = 'deliveryErrors',
    )

    __default_path__ = MAIL_DEFAULT_PATH

    def __str__(self):
        if self.isStale():
            return super(MailDeliveryError, self).__str__()
            # Stale items shouldn't go through the code below

        return "| %d | %s | %s |" % (self.errorCode, self.errorString, str(self.errorDate))


class MailDeliveryBase(ContentModel.ContentItem):

    schema.kindInfo(
        displayName = "Mail Delivery base kind",
        description =
            "Parent kind for delivery-specific attributes of a MailMessage"
    )

    mailMessage = schema.One(
        'MailMessageMixin',
        displayName = 'Message',
        doc = 'Message which this delivery item refers to',
        initialValue = None,
        inverse = 'deliveryExtension',
    )
    deliveryErrors = schema.Sequence(
        MailDeliveryError,
        displayName = 'Mail Delivery Errors',
        doc = 'Mail Delivery Errors associated with this transport',
        initialValue = [],
        inverse = MailDeliveryError.mailDelivery,
    )

    __default_path__ = MAIL_DEFAULT_PATH


class historyEnum(schema.Enumeration):
    values = "QUEUED", "FAILED", "SENT"

class stateEnum(schema.Enumeration):
    values = "DRAFT", "QUEUED", "SENT", "FAILED"


class SMTPDelivery(MailDeliveryBase):

    schema.kindInfo(
        displayName = "SMTP Delivery",
        description = "Tracks the status of an outgoing message",
        issues = [
            "Currently the parcel loader can't set a default value for the "
            "state attribute",
        ]
    )

    history = schema.Sequence(
        historyEnum,
        displayName = 'History',
        initialValue = [],
    )
    tries = schema.One(
        schema.Integer,
        displayName = 'Number of tries',
        doc = 'How many times we have tried to send it',
        initialValue = 0,
    )
    state = schema.One(
        stateEnum,
        displayName = 'State',
        doc = 'The current state of the message',
        issues = [
            "We don't appear to be able to set an initialValue for an "
            "attribute whose enumeration is defined in the same file "
            "(a deficiency in the parcel loader)",
        ],
    )
   
    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(SMTPDelivery, self).__init__(name, parent, kind, view)
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

    schema.kindInfo(
        displayName = "IMAP Delivery",
        description = "Tracks the state of an inbound message",
    )

    folder = schema.One(
        schema.String, displayName = 'Folder', initialValue = '',
    )
    uid = schema.One(
        schema.Long,
        displayName = 'IMAP UID',
        doc = 'The unique IMAP ID for the message',
        initialValue = 0,
    )
    namespace = schema.One(
        schema.String,
        displayName = 'Namespace',
        doc = 'The namespace of the message',
        initialValue = '',
    )
    flags = schema.Sequence(
        schema.String, displayName = 'Flags', initialValue = [],
    )


class POPDelivery(MailDeliveryBase):

    schema.kindInfo(
        displayName = "POP Delivery",
        description = "Tracks the state of an inbound message",
    )

    uid = schema.One(
        schema.String,
        displayName = 'POP UID',
        doc = 'The unique POP ID for the message',
        initialValue = '',
    )


class MIMEBase(ContentModel.ContentItem):
    schema.kindInfo(
        displayName="MIME Base Kind",
        description="Super kind for MailMessage and the various MIME kinds",
    )

    mimeType = schema.One(schema.String, initialValue = '')
    mimeContainer = schema.One(
        'MIMEContainer', initialValue = None, inverse = 'mimeParts',
    )

    schema.addClouds(
        sharing = schema.Cloud(mimeType),
    )

    __default_path__ = MAIL_DEFAULT_PATH


class MIMENote(MIMEBase):
    # @@@MOR This used to subclass Notes.Note also, but since that superKind
    # was removed from MIMENote's superKinds list

    schema.kindInfo(
        displayName="MIME Note",
        description="MIMEBase and Note, rolled into one",
    )

    filename = schema.One(
        schema.String, displayName = 'File name', initialValue = '',
    )
    filesize = schema.One(schema.Long, displayName = 'File Size')

    schema.addClouds(
        sharing = schema.Cloud(filename, filesize),
    )


class MIMEContainer(MIMEBase):

    schema.kindInfo(displayName="MIME Container Kind")

    hasMimeParts = schema.One(schema.Boolean, initialValue = False)
    mimeParts = schema.Sequence(
        MIMEBase,
        displayName = 'MIME Parts',
        initialValue = [],
        inverse = MIMEBase.mimeContainer,
    )
    schema.addClouds(sharing = schema.Cloud(hasMimeParts, mimeParts))


class MailMessageMixin(MIMEContainer):
    """
      Mail Message Mixin is the bag of Message-specific attributes.

    """
    schema.kindInfo(
        displayName="Mail Message Mixin",
        displayAttribute="subject",
        description="Used to mixin mail message attributes into a content item",
        issues=[
            "Once we have attributes and a cloud defined for Attachment, "
            "we need to include attachments by cloud, and not by value.",

            "Really not sure what to do with the 'downloadAccount' attribute "
            "and how it should be included in the cloud.  For now it's by "
            "value.",
        ]
    )
    deliveryExtension = schema.One(
        MailDeliveryBase,
        initialValue = None,
        inverse = MailDeliveryBase.mailMessage,
    )
    isOutbound = schema.One(schema.Boolean, initialValue = False)
    isInbound = schema.One(schema.Boolean, initialValue = False)
    parentAccount = schema.One(
        AccountBase, initialValue = None, inverse = AccountBase.mailMessages,
    )
    spamScore = schema.One(schema.Float, initialValue = 0.0)
    rfc2822Message = schema.One(schema.Lob)
    dateSentString = schema.One(schema.String, initialValue = '')
    dateSent = schema.One(schema.DateTime)
    messageId = schema.One(schema.String, initialValue = '')
    toAddress = schema.Sequence(
        'EmailAddress',
        displayName = 'to',
        initialValue = [],
        inverse = 'messagesTo',
    )
    fromAddress = schema.One(
        'EmailAddress',
        displayName = 'from',
        initialValue = None,
        inverse = 'messagesFrom',
    )
    replyToAddress = schema.One(
        'EmailAddress', initialValue = None, inverse = 'messagesReplyTo',
    )
    bccAddress = schema.Sequence(
        'EmailAddress', initialValue = [], inverse = 'messagesBcc',
    )
    ccAddress = schema.Sequence(
        'EmailAddress', initialValue = [], inverse = 'messagesCc',
    )
    subject = schema.One(schema.String, initialValue = '')
    headers = schema.Mapping(
        schema.String, doc = 'Catch-all for headers', initialValue = {},
    )
    chandlerHeaders = schema.Mapping(schema.String, initialValue = {})
    who = schema.One(
        doc = "Redirector to 'toAddress'", redirectTo = 'toAddress',
    )
    whoFrom = schema.One(
        doc = "Redirector to 'fromAddress'", redirectTo = 'fromAddress',
    )
    about = schema.One(
        doc = "Redirector to 'subject'", redirectTo = 'subject',
    )
    date = schema.One(
        doc = "Redirector to 'dateSent'", redirectTo = 'dateSent',
    )

    mimeType = schema.One(schema.String, initialValue = 'message/rfc822')

    schema.addClouds(
        sharing = schema.Cloud(
            fromAddress, toAddress, ccAddress, bccAddress, replyToAddress,
            subject
        ),
        copying = schema.Cloud(
            fromAddress, toAddress, ccAddress, bccAddress, replyToAddress,
            byCloud = [MIMEContainer.mimeParts]
        ),
    )

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
    schema.kindInfo(
        displayName = "Mail Message",
        displayAttribute = "subject",
        description = "MailMessageMixin, and Note, all rolled up into one",
    )


class MIMEBinary(MIMENote):

    schema.kindInfo(displayName = "MIME Binary Kind")


class MIMEText(MIMENote):

    schema.kindInfo(displayName = "MIME Text Kind")

    charset = schema.One(
        schema.String,
        displayName = 'Character set encoding',
        initialValue = 'utf-8',
    )
    lang = schema.One(
        schema.String,
        displayName = 'Character set Language',
        initialValue = 'en',
    )


class MIMESecurity(MIMEContainer):

    schema.kindInfo(displayName="MIME Security Kind")


class EmailAddress(ContentModel.ContentItem):
    
    schema.kindInfo(
        displayName = "Email Address Kind",
        displayAttribute = "emailAddress",
        examples = ["abe@osafoundation.org"],
        description = "An item that represents a simple email address, plus "
                      "all the info we might want to associate with it, like "
                      "lists of message to and from this address.",
        issues = [
            "Someday we might want to have other attributes.  One example "
            "might be an 'is operational' flag that tells whether this "
            "address is still in service, or whether mail to this has been "
            "bouncing lately. Another example might be a 'superceded by' "
            "attribute, which would point to another Email Address item.",

            "Depending on how we end up using the 'emailAddress' attribute, "
            "we might want to break it into two attributes, one for the 'Abe "
            "Lincoln' part, and one for the 'abe@osafoundation.org' part. "
            "Alternatively, we might want to use one of Andi's compound "
            "types, with two fields.",
        ]
    )

    emailAddress = schema.One(
        schema.String,
        displayName = 'Email Address',
        doc = 'An RFC 822 email address.',
        examples = [
            '"abe@osafoundation.org"',
            '"Abe Lincoln {abe@osafoundation.org}" (except with angle '
                'brackets instead of \'{\' and \'}\')'
        ],
        initialValue = '',
    )
    fullName = schema.One(
        schema.String,
        displayName = 'Full Name',
        doc = 'A first and last name associated with this email address',
        initialValue = '',
    )
    vcardType = schema.One(
        schema.String,
        displayName = 'vCard type',
        doc = "Typical vCard types are values like 'internet', 'x400', and "
              "'pref'. Chandler will use this attribute when doing "
              "import/export of Contact records in vCard format.",
        initialValue = '',
    )
    accounts = schema.Sequence(
        DownloadAccountBase,
        displayName = 'Used as Return Address by Email Account',
        doc = 'A list of Email Accounts that use this Email Address as the '
              'reply address for mail sent from the account.',
        initialValue = [],
        inverse = DownloadAccountBase.replyToAddress,
    )
    messagesBcc = schema.Sequence(
        MailMessageMixin,
        displayName = 'Messages Bcc',
        doc = 'A list of messages with their Bcc: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.bccAddress,
    )
    messagesCc = schema.Sequence(
        MailMessageMixin,
        displayName = 'Messages cc',
        doc = 'A list of messages with their cc: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.ccAddress,
    )
    messagesFrom = schema.Sequence(
        MailMessageMixin,
        displayName = 'Messages From',
        doc = 'A list of messages with their From: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.fromAddress,
    )
    messagesReplyTo = schema.Sequence(
        MailMessageMixin,
        displayName = 'Messages Reply To',
        doc = 'A list of messages with their Reply-To: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.replyToAddress,
    )
    messagesTo = schema.Sequence(
        MailMessageMixin,
        displayName = 'Messages To',
        doc = 'A list of messages with their To: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.toAddress,
    )
    inviteeOf = schema.Sequence(
        'osaf.contentmodel.ItemCollection.ItemCollection',
        displayName = 'Invitee Of',
        doc = 'List of collections that the user is about to be invited to share with.',
        inverse = 'invitees',
    )

    schema.addClouds(
        sharing = schema.Cloud(emailAddress, fullName)
    )

    __default_path__ = MAIL_DEFAULT_PATH

    def __init__(self, name=None, parent=None, kind=None, view=None,
        clone=None, **kw
    ):
        super(EmailAddress, self).__init__(name, parent, kind, view, **kw)

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

    @classmethod
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
            addresses = []
            for candidate in EmailAddress.iterItems(view):
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

    @classmethod
    def format(cls, emailAddress):
        assert isinstance(emailAddress, EmailAddress), "You must pass an EmailAddress Object"

        if emailAddress.fullName is not None and len(emailAddress.fullName.strip()) > 0:
            return emailAddress.fullName + " <" + emailAddress.emailAddress + ">"

        return emailAddress.emailAddress

    @classmethod
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

    @classmethod
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


    @classmethod
    def getCurrentMeEmailAddress(cls, view):
        """
          Lookup the "me" EmailAddress.
        The "me" EmailAddress is whichever entry is the current IMAP default
        address.
        """

        account = getCurrentMailAccount(view)

        if account is not None and hasattr(account, 'replyToAddress'):
            return account.replyToAddress

        return None


# Map from account type strings to account types

ACCOUNT_TYPES = {
    'POP': POPAccount,
    'SMTP': SMTPAccount,
    'IMAP': IMAPAccount,
}
