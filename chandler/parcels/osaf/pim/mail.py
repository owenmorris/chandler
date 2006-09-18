#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Classes used for Mail parcel kinds.
"""

__all__ = [
    'AccountBase', 'DownloadAccountBase', 'EmailAddress', 'IMAPAccount',
    'IMAPDelivery', 'MIMEBase', 'MIMEBinary', 'MIMEContainer', 'MIMENote',
    'MIMESecurity', 'MIMEText', 'MailDeliveryBase', 'MailDeliveryError',
    'MailMessage', 'MailMessageMixin', 'POPAccount', 'POPDelivery',
    'SMTPAccount', 'SMTPDelivery', 'replyToMessage', 'replyAllToMessage',
    'forwardMessage', 'getCurrentSMTPAccount', 'getCurrentMailAccount', 'ACCOUNT_TYPES']


import application
from application import schema
import repository.item.Item as Item
import items, notes
import email.Utils as Utils
import re as re
import chandlerdb.item.ItemError as ItemError
import PyICU

from repository.util.Path import Path
from i18n import ChandlerMessageFactory as _
from osaf import messages
from repository.persistence.RepositoryError import RepositoryError, VersionConflictError

"""
Design Issues:
      1. Is tries really needed
      2. Date sent string could probally be gotten rid of
"""

def __actionOnMessage(view, mailMessage, action="REPLY"):
    assert(isinstance(mailMessage, MailMessageMixin))
    assert(action == "REPLY" or action == "REPLYALL" or action == "FORWARD")

    newMessage = MailMessage(itsView=view)

    #This could be None
    newMessage.fromAddress = EmailAddress.getCurrentMeEmailAddress(view)

    if action == "REPLY" or action == "REPLYALL":
        if mailMessage.subject:
            #XXX could use case insensitive compare
            if mailMessage.subject.startswith(u"Re: "):
                newMessage.subject = mailMessage.subject
            else:
                newMessage.subject = u"Re: %s" % mailMessage.subject

        newMessage.inReplyTo = mailMessage.messageId

        newMessage.referencesMID.extend(mailMessage.referencesMID)
        newMessage.referencesMID.append(mailMessage.messageId)
        origBody = mailMessage.body.split(u"\n")
        buffer = [u"\n"]

        addr = mailMessage.fromAddress

        if addr.fullName:
            txt = addr.fullName
        else:
            txt = addr.emailAddress

        m = PyICU.DateFormat.createDateInstance(PyICU.DateFormat.kMedium)

        buffer.append(_(u"on %(date)s, %(emailAddress)s wrote:\n") % \
                        {'date': m.format(mailMessage.dateSent),
                         'emailAddress': txt})

        for line in origBody:
            if line.startswith(u">"):
                buffer.append(u">%s" % line)
            else:
                buffer.append(u"> %s" % line)

        newMessage.body = u"\n".join(buffer)

        to = mailMessage.replyToAddress and mailMessage.replyToAddress or \
             mailMessage.fromAddress

        newMessage.toAddress.append(to)

        if action == "REPLYALL":
            addresses = {}

            #The from address can be empty if no account info has been
            #configured
            if newMessage.fromAddress:
                addresses[newMessage.fromAddress.emailAddress] = True

            for addr in newMessage.toAddress:
                addresses[addr.emailAddress] = True

            for addr in mailMessage.toAddress:
                if not addresses.has_key(addr.emailAddress):
                    newMessage.ccAddress.append(addr)
                    addresses[addr.emailAddress] = True

            for addr in mailMessage.ccAddress:
                if not addresses.has_key(addr.emailAddress):
                    newMessage.ccAddress.append(addr)
                    addresses[addr.emailAddress] = True
    else:
        #action == FORWARD
        if mailMessage.subject:
            if mailMessage.subject.startswith(u"Fwd: ") or \
               mailMessage.subject.startswith(u"[Fwd: "):
                newMessage.subject = mailMessage.subject
            else:
                newMessage.subject = u"Fwd: %s" % mailMessage.subject

        newMessage.mimeParts.append(mailMessage)

    try:
        view.commit()
    except RepositoryError, e:
        raise
    except VersionConflictError, e:
        raise

    return newMessage

def replyToMessage(view, mailMessage):
    return __actionOnMessage(view, mailMessage, "REPLY")

def replyAllToMessage(view, mailMessage):
    return __actionOnMessage(view, mailMessage, "REPLYALL")

def forwardMessage(view, mailMessage):
    return __actionOnMessage(view, mailMessage, "FORWARD")


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

    """
    Get the default Mail Account
    """
    parentAccount = schema.ns('osaf.pim', view).currentMailAccount.item

    if parentAccount is not None:
        if hasattr(parentAccount, 'replyToAddress'):
            replyToAddress = parentAccount.replyToAddress

        """
        Get the default SMTP Account
        """
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

    @param uuid: The C{uuid} of the account.
                 If no C{uuid} passed will return the current account
    @type uuid: C{uuid}
    @return C{IMAPAccount} or C{POPAccount}
    """

    if uuid is not None:
        account = view.findUUID(uuid)

    else:
        account = schema.ns('osaf.pim', view).currentMailAccount.item

    return account


class connectionSecurityEnum(schema.Enumeration):
    values = "NONE", "TLS", "SSL"


class AccountBase(items.ContentItem):

    schema.kindInfo(
        description="The base kind for various account kinds, such as "
                    "IMAP, SMTP, WebDav"
    )

    numRetries = schema.One(
        schema.Integer,
        doc = 'How many times to retry before giving up',
        initialValue = 1,
    )
    username = schema.One(
        schema.Text,
        doc = 'The account login name',
        initialValue = u'',
    )
    password = schema.One(
        schema.Text,
        doc = 'This could either be a password or some other sort of '
              'authentication info. We can use it for whatever is needed '
              'for this account type.\n\n'
            'Issues:\n'
            '   This should not be a simple string. We need some solution for '
            'encrypting it.\n',
        initialValue = u'',
    )
    host = schema.One(
        schema.Text,
        doc = 'The hostname of the account',
        initialValue = u'',
    )
    port = schema.One(
        schema.Integer, doc = 'The port number to use',
    )
    connectionSecurity = schema.One(
        connectionSecurityEnum,
        doc = 'The security mechanism to leverage for a network connection',
        initialValue = 'NONE',
    )
    pollingFrequency = schema.One(
        schema.Integer,
        doc = 'Frequency in seconds',
        initialValue = 300,
    )
    mailMessages = schema.Sequence(
        'MailMessageMixin',
        doc = 'Mail Messages sent or retrieved with this account ',
        initialValue = [],
        inverse = 'parentAccount',
    )
    timeout = schema.One(
        schema.Integer,
        doc = 'The number of seconds before timing out a stalled connection',
        initialValue = 60,
    )
    isActive = schema.One(
        schema.Boolean,
        doc = 'Whether or not an account should be used for sending or '
              'fetching email',
        initialValue = True,
    )

    @classmethod
    def getActiveAccounts(cls, view):
        for item in cls.iterItems(view):
            if item.isActive and item.host and item.username:
                yield item


class DownloadAccountBase(AccountBase):

    schema.kindInfo(
        description="Base Account for protocols that download mail",
    )

    defaultSMTPAccount = schema.One(
        'SMTPAccount',
        doc = 'Which SMTP account to use for sending mail from this account',
        initialValue = None,
        inverse = 'accounts',
    )
    downloadMax = schema.One(
        schema.Integer,
        doc = 'The maximum number of messages to download before forcing a repository commit',
        initialValue = 20,
    )
    replyToAddress = schema.One(
        'EmailAddress',
        initialValue = None,
        inverse = 'accounts',
    )
    emailAddress = schema.One(
        redirectTo = 'replyToAddress.emailAddress',
    )
    fullName = schema.One(
        redirectTo = 'replyToAddress.fullName',
    )


class SMTPAccount(AccountBase):

    accountType = "SMTP"

    schema.kindInfo(
        description="An SMTP Account",
    )

    fromAddress = schema.One(
        'EmailAddress',
        initialValue = None
    )
    emailAddress = schema.One(
        redirectTo = 'fromAddress.emailAddress',
    )
    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for an "
            "SMTPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 25,
    )
    useAuth = schema.One(
        schema.Boolean,
        doc = 'Whether or not to use authentication when sending mail',
        initialValue = False,
    )
    accounts = schema.Sequence(
        DownloadAccountBase,
        doc = 'Which accounts use this SMTP account as their default',
        initialValue = [],
        inverse = DownloadAccountBase.defaultSMTPAccount,
    )
    signature = schema.One(
        schema.Text,
        description =
            "Issues:\n"
            '   Basic signiture addition to an outgoing message will be refined '
            'in future releases\n',
    )


class IMAPAccount(DownloadAccountBase):

    accountType = "IMAP"

    schema.kindInfo(
        description = "An IMAP Account",
    )

    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "an IMAPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 143,
    )
    messageDownloadSequence = schema.One(
        schema.Long,
        initialValue = 0L,
    )


class POPAccount(DownloadAccountBase):

    accountType = "POP"

    schema.kindInfo(
        description = "An POP Account",
    )
    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use\n\n'
            "Issues:\n"
            "   In order to get a custom initialValue for this attribute for "
            "a POPAccount, I defined a 'duplicate' attribute, also named "
            "'port', which normally would have been inherited from AccountBase\n",
        initialValue = 110,
    )
    downloadedMessageUIDS = schema.Mapping(
        schema.Text,
        doc = 'Used for quick look up to discover if a message has already been downloaded',
        initialValue = {},
    )
    leaveOnServer = schema.One(
        schema.Boolean,
        doc = 'Whether or not to leave messages on the server after downloading',
        initialValue = True,
    )


class MailDeliveryError(items.ContentItem):

    schema.kindInfo(
        description=
            "Contains the error data associated with a MailDelivery Type"
    )

    errorCode = schema.One(
        schema.Integer,
        doc = 'The Error Code returned by the Delivery Transport',
        initialValue = 0,
    )
    errorString = schema.One(schema.Text, initialValue = u'')
    errorDate = schema.One(schema.DateTime)
    mailDelivery = schema.One(
        'MailDeliveryBase',
        doc = 'The Mail Delivery that cause this error',
        initialValue = None,
        inverse = 'deliveryErrors',
    )


class MailDeliveryBase(items.ContentItem):

    schema.kindInfo(
        description =
            "Parent kind for delivery-specific attributes of a MailMessage"
    )

    mailMessage = schema.One(
        'MailMessageMixin',
        doc = 'Message which this delivery item refers to',
        initialValue = None,
        inverse = 'deliveryExtension',
    )
    deliveryErrors = schema.Sequence(
        MailDeliveryError,
        doc = 'Mail Delivery Errors associated with this transport',
        initialValue = [],
        inverse = MailDeliveryError.mailDelivery,
    )


class historyEnum(schema.Enumeration):
    values = "QUEUED", "FAILED", "SENT"

class stateEnum(schema.Enumeration):
    values = "DRAFT", "QUEUED", "SENT", "FAILED"


class SMTPDelivery(MailDeliveryBase):

    schema.kindInfo(
        description = "Tracks the status of an outgoing message\n\n"
            "Issues:\n\n"
            "   Currently the parcel loader can't set a default value for the "
            "state attribute\n",
    )

    history = schema.Sequence(
        historyEnum,
        initialValue = [],
    )
    tries = schema.One(
        schema.Integer,
        doc = 'How many times we have tried to send it',
        initialValue = 0,
    )
    state = schema.One(
        stateEnum,
        doc = 'The current state of the message\n\n'
        "Issues:\n"
        "   We don't appear to be able to set an initialValue for an "
            "attribute whose enumeration is defined in the same file "
            "(a deficiency in the parcel loader)\n",
        initialValue = "DRAFT",
    )

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
        description = "Tracks the state of an inbound message",
    )

    folder = schema.One(
        schema.Text, initialValue = u'',
    )
    uid = schema.One(
        schema.Long,
        doc = 'The unique IMAP ID for the message',
        initialValue = 0,
    )
    namespace = schema.One(
        schema.Text,
        doc = 'The namespace of the message',
        initialValue = u'',
    )
    flags = schema.Sequence(
        schema.Text, initialValue = [],
    )


class POPDelivery(MailDeliveryBase):

    schema.kindInfo(
        description = "Tracks the state of an inbound message",
    )

    uid = schema.One(
        schema.Text,
        doc = 'The unique POP ID for the message',
        initialValue = '',
    )


class MIMEBase(items.ContentItem):
    schema.kindInfo(
        description="Super kind for MailMessage and the various MIME kinds",
    )

    mimeType = schema.One(schema.Text, initialValue = '')

    mimeContainer = schema.One(
        'MIMEContainer', initialValue = None, inverse = 'mimeParts',
    )

    schema.addClouds(
        sharing = schema.Cloud(mimeType),
    )


class MIMENote(MIMEBase):
    # @@@MOR This used to subclass notes.Note also, but since that superKind
    # was removed from MIMENote's superKinds list

    schema.kindInfo(
        description="MIMEBase and Note, rolled into one",
    )

    filename = schema.One(
        schema.Text, initialValue = u'',
    )
    filesize = schema.One(schema.Long)

    schema.addClouds(
        sharing = schema.Cloud(filename, filesize),
    )


class MIMEContainer(MIMEBase):

    hasMimeParts = schema.One(schema.Boolean, initialValue = False)
    mimeParts = schema.Sequence(
        MIMEBase,
        initialValue = [],
        inverse = MIMEBase.mimeContainer,
    )
    schema.addClouds(sharing = schema.Cloud(hasMimeParts, mimeParts))


class MailMessageMixin(MIMEContainer):
    """
    MailMessageMixin is the bag of Message-specific attributes.

    Used to mixin mail message attributes into a content item.

    Issues:
      - Once we have attributes and a cloud defined for Attachment,
        we need to include attachments by cloud, and not by value.
      - Really not sure what to do with the 'downloadAccount' attribute
        and how it should be included in the cloud.  For now it's byValue.
    """
    deliveryExtension = schema.One(
        MailDeliveryBase,
        initialValue = None,
        inverse = MailDeliveryBase.mailMessage,
    )
    isOutbound = schema.One(schema.Boolean, initialValue = True)
    parentAccount = schema.One(
        AccountBase, initialValue = None, inverse = AccountBase.mailMessages,
    )
    spamScore = schema.One(schema.Float, initialValue = 0.0)
    rfc2822Message = schema.One(schema.Lob, indexed=False)
    dateSentString = schema.One(schema.Text, initialValue = '')
    dateSent = schema.One(schema.DateTimeTZ, indexed=True)
    messageId = schema.One(schema.Text, initialValue = '')
    toAddress = schema.Sequence(
        'EmailAddress',
        initialValue = [],
        inverse = 'messagesTo',
    )
    fromAddress = schema.One(
        'EmailAddress',
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
    subject = schema.One(schema.Text, indexed=True)
    inReplyTo = schema.One(schema.Text, indexed=False)
    referencesMID = schema.Sequence(schema.Text, initialValue = [])

    headers = schema.Mapping(
        schema.Text, doc = 'Catch-all for headers', initialValue = {},
    )
    chandlerHeaders = schema.Mapping(schema.Text, initialValue = {})
    who = schema.One(
        doc = "Redirector to 'toAddress'", redirectTo = 'toAddress',
    )
    whoFrom = schema.One(
        doc = "Redirector to 'fromAddress'", redirectTo = 'fromAddress',
    )
    about = schema.One(
        doc = "Redirector to 'subject'", redirectTo = 'subject',
    )

    mimeType = schema.One(schema.Text, initialValue = 'message/rfc822')

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
        """
        Init any attributes on ourself that are appropriate for
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
        # default the fromAddress to "me"
        self.fromAddress = EmailAddress.getCurrentMeEmailAddress(self.itsView)

        # default the subject to any super class "about" definition
        try:
            self.subject = self.getAnyAbout()
        except AttributeError:
            pass

    @schema.observer(dateSent)
    def onDateSentChanged(self, op, name):
        # Update our relevant-date attribute
        self.updateRelevantDate(op, name)

    def addRelevantDates(self, dates):
        super(MailMessageMixin, self).addRelevantDates(dates)
        dateSent = getattr(self, 'dateSent', None)
        if dateSent is not None:
            dates.append((dateSent, 'dateSent'))

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

    def outgoingMessage(self, account, type='SMTP'):
        assert type == "SMTP", "Only SMTP currently supported"

        assert isinstance(account, SMTPAccount)

        if self.deliveryExtension is None:
            self.deliveryExtension = SMTPDelivery(itsView=self.itsView)

        self.isOutbound = True
        self.parentAccount = account

    def incomingMessage(self, account, type="IMAP"):
        assert isinstance(account, DownloadAccountBase)

        if self.deliveryExtension is None:
            if type == "IMAP":
                 self.deliveryExtension = IMAPDelivery(itsView=self.itsView)
            elif type == "POP":
                 self.deliveryExtension = POPDelivery(itsView=self.itsView)

        self.isOutbound = False
        self.parentAccount = account

    def getAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        return self.mimeParts

    def getNumberOfAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        return len(self.mimeParts)

    def hasAttachments(self):
        """
        First pass at API will be expanded upon later.
        """
        return self.hasMimeParts

    def getSendability(self, ignoreAttr=None):
        """
        Return whether this item is ready to send: 'sendable', 'sent',
        or 'not'. if ignoreAttr is specified, don't verify that value
        (because it's being edited in the UI and is known to be valid,
        and will get saved before sending).
        """
        # Not outbound?
        if not self.isOutbound:
            return 'not'

        # Already sent?
        try:
            sent = self.deliveryExtension.state == "SENT"
        except AttributeError:
            sent = False
        if sent:
            return 'sent'

        # Addressed?
        # (This test will get more complicated when we add cc, bcc, etc.)
        sendable = ((ignoreAttr == 'toAddress' or len(self.toAddress) > 0) and
                    (ignoreAttr == 'fromAddress' or self.fromAddress is not None))
        return sendable and 'sendable' or 'not'

class MailMessage(MailMessageMixin, notes.Note):
    schema.kindInfo(
        displayAttribute = "subject",
        description = "MailMessageMixin, and Note, all rolled up into one",
    )


class MIMEBinary(MIMENote):

    data = schema.One(schema.Lob, indexed=False)


class MIMEText(MIMENote):

    charset = schema.One(
        schema.Text,
        initialValue = 'utf-8',
    )
    lang = schema.One(
        schema.Text,
        initialValue = 'en',
    )


class MIMESecurity(MIMEContainer):
    pass

class EmailAddress(items.ContentItem):

    schema.kindInfo(
        displayAttribute = "emailAddress",
        description = "An item that represents a simple email address, plus "
                      "all the info we might want to associate with it, like "
                      "lists of message to and from this address.\n\n"
            "Example: abe@osafoundation.org\n\n"
            "Issues:\n"
            "   Someday we might want to have other attributes.  One example "
            "might be an 'is operational' flag that tells whether this "
            "address is still in service, or whether mail to this has been "
            "bouncing lately. Another example might be a 'superceded by' "
            "attribute, which would point to another Email Address item.\n",
    )

    emailAddress = schema.One(
        schema.Text,
        doc = 'The email address.\n\n'
            "Examples:\n"
            '   "abe@osafoundation.org"\n',
        indexed = True,
        initialValue = u'',
    )
    fullName = schema.One(
        schema.Text,
        doc = 'A first and last name associated with this email address',
        indexed = True,
        initialValue = u'',
    )
    vcardType = schema.One(
        schema.Text,
        doc = "Typical vCard types are values like 'internet', 'x400', and "
              "'pref'. Chandler will use this attribute when doing "
              "import/export of Contact records in vCard format.",
        initialValue = u'',
    )
    accounts = schema.Sequence(
        DownloadAccountBase,
        doc = 'A list of Email Accounts that use this Email Address as the '
              'reply address for mail sent from the account.',
        initialValue = [],
        inverse = DownloadAccountBase.replyToAddress,
    )
    messagesBcc = schema.Sequence(
        MailMessageMixin,
        doc = 'A list of messages with their Bcc: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.bccAddress,
    )
    messagesCc = schema.Sequence(
        MailMessageMixin,
        doc = 'A list of messages with their cc: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.ccAddress,
    )
    messagesFrom = schema.Sequence(
        MailMessageMixin,
        doc = 'A list of messages with their From: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.fromAddress,
    )
    messagesReplyTo = schema.Sequence(
        MailMessageMixin,
        doc = 'A list of messages with their Reply-To: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.replyToAddress,
    )
    messagesTo = schema.Sequence(
        MailMessageMixin,
        doc = 'A list of messages with their To: header referring to this address',
        initialValue = [],
        inverse = MailMessageMixin.toAddress,
    )
    inviteeOf = schema.Sequence(
        'osaf.pim.collections.ContentCollection',
        doc = 'List of collections that the user is about to be invited to share with.',
        inverse = 'invitees',
    )

    schema.addClouds(
        sharing = schema.Cloud(emailAddress, fullName)
    )

    def __init__(self, itsName=None, itsParent=None, itsKind=None,
        itsView=None, clone=None, **kw
    ):
        super(EmailAddress, self).__init__(
            itsName, itsParent, itsKind, itsView, **kw
        )

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
        if self.isStale():
            return super(EmailAddress, self).__str__()

        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        """
        User readable string version of this address.
        """
        if self.isStale():
            return super(EmailAddress, self).__unicode__()
            # Stale items shouldn't go through the code below

        fullName = getattr(self, 'fullName', u'')
        if len(fullName) > 0:
            if self.emailAddress:
                return fullName + u' <' + self.emailAddress + u'>'
            else:
                return fullName
        elif self is self.getCurrentMeEmailAddress(self.itsView):
            return messages.ME
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
    def getEmailAddress(cls, view, nameOrAddressString, fullName='', inbound=False):
        """
        Lookup or create an EmailAddress based on the supplied string.

        If a matching EmailAddress object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.

        There are two ways to call this method:
          1. with something the user typed in nameOrAddressString, which
             will be parsed, and no fullName is needed
          2. with an plain email address in the nameOrAddressString, and a
             full name in the fullName field

        If a match is found for both name and address then it will be used.

        If there is no name specified, a match on address will be returned.

        If there is no address specified, a match on name will be returned.

        If both name and address are specified, but there's no entry that
        matches both, then a new entry is created.

        @param nameOrAddressString: emailAddress string, or fullName for lookup,
        or both in the form "name <address>"
        @type nameOrAddressString: C{unicode}
        @param fullName: optional explict fullName when not using the
        "name <address>" form of the nameOrAddressString parameter
        @type fullName: C{unicode}
        @param inbound: Indicates that even if the email address is not valid still
                        save it as an C{EmailAddress} Object. When mail enters Chandler
                        via IMAP, POP, Sharing, etc the email address may not be valid
                        or in a valid format ie. "name <emailaddress>". We still want to
                        capture as much information as possible for display to the user.
                        When sending, Chandler does not allow a user to send a message
                        with an invalid email address.
        @type inbound: C{bool}


        @return: C{EmailAddress} or None if not found, and nameOrAddressString is\
        not a valid email address.
        """
        # @@@DLD remove when we better sort out creation of "me" address w/o an account setup
        if nameOrAddressString is None:
            nameOrAddressString = u''

        # strip the address string of whitespace and question marks
        address = nameOrAddressString.strip ().strip(u'?')

        # check for "me"
        if address == messages.ME:
            return cls.getCurrentMeEmailAddress(view)

        # if no fullName specified, parse apart the name and address if we can
        if fullName != u'':
            name = fullName
        else:
            try:
                address.index(u'<')
            except ValueError:
                name = address
            else:
                name, address = address.split(u'<')
                address = address.strip(u'>').strip()
                name = name.strip()
                # ignore a name of "me"
                if name == messages.ME:
                    name = u''

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

        addresses = []
        for candidate in EmailAddress.iterItems(view):
            if isValidAddress:
                if cls.emailAddressesAreEqual(candidate.emailAddress, address):
                    # found an existing address!
                    addresses.append(candidate)
            elif name != u'' and name == candidate.fullName:
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
            if name != u'' and name == candidate.fullName:
                # full name match
                nameMatch = candidate
                if addressMatch is not None:
                    # matched both
                    return addressMatch
        else:
            # no double-matches found
            if name == address:
                name = u''
            if addressMatch is not None and name == u'':
                return addressMatch
            if nameMatch is not None and address is None:
                return nameMatch
            if isValidAddress or inbound:
                # make a new EmailAddress
                if address is None:
                    address = u""
                if name is None:
                    name = u""
                newAddress = EmailAddress(itsView=view,
                                          emailAddress=address,
                                          fullName=name)
                return newAddress
            else:
                return None

    def _compareAddr(self, other):
        return cmp(self.emailAddress.lower(), other.emailAddress.lower())

    def _compareFullName(self, other):
        return cmp(self.fullName.lower(), other.fullName.lower())

    @classmethod
    def findEmailAddress(cls, view, emailAddress):
        """
        Find a single EmailAddress that exactly matches this one.
        """
        collection = schema.ns("osaf.pim", view).emailAddressCollection
        emailAddress = emailAddress.lower()

        def compareAddr(uuid):
            return cmp(emailAddress,
                       view.findValue(uuid, 'emailAddress').lower())

        uuid = collection.findInIndex('emailAddress', 'exact', compareAddr)
        if uuid is None:
            return None

        return view[uuid]

    @classmethod
    def generateMatchingEmailAddresses(cls, view, partialAddress):
        """
        Generate any EmailAddresses whose emailAddress or fullName starts
        with this.
        """
        collection = schema.ns("osaf.pim", view).emailAddressCollection
        partialAddress = unicode(partialAddress).lower()
        for indexName in ('emailAddress', 'fullName'):
            def _compare(uuid):
                attrValue = view.findValue(uuid, indexName).lower()
                if attrValue.startswith(partialAddress):
                    return 0
                return cmp(partialAddress, attrValue)
            firstUUID = collection.findInIndex(indexName, 'first', _compare)

            if firstUUID is None:
                continue

            lastUUID = collection.findInIndex(indexName, 'last', _compare)
            for uuid in collection.iterindexkeys(indexName, firstUUID, lastUUID):
                yield view[uuid]

    @classmethod
    def format(cls, emailAddress, encode=False):
        assert isinstance(emailAddress, EmailAddress), "You must pass an EmailAddress Object"

        if emailAddress.fullName is not None and len(emailAddress.fullName.strip()) > 0:
            if encode:
                from email.Header import Header
                return Header(emailAddress.fullName).encode() + u" <" + emailAddress.emailAddress + u">"
            else:
                return emailAddress.fullName + u" <" + emailAddress.emailAddress + u">"

        return emailAddress.emailAddress

    @classmethod
    def isValidEmailAddress(cls, emailAddress):
        """
        This method tests an email address for valid syntax as defined RFC 822.
        The method validates addresses in the form 'John Jones <john@test.com>'
        and 'john@test.com'

        @param emailAddress: A string containing a email address to validate.
        @type emailAddress: C{String}
        @return: C{Boolean}
        """

        assert isinstance(emailAddress, (str, unicode)), "Email Address must be in string or unicode format"

        #XXX: Strip any name information. i.e. John test <john@test.com>`from the email address
        emailAddress = Utils.parseaddr(emailAddress)[1]

        return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", emailAddress) is not None

    @classmethod
    def parseEmailAddresses(cls, view, addressesString):
        """
        Parse the email addresses in addressesString and return
        a tuple with: (the processed string, a list of EmailAddress
        items created/found for those addresses, the number of
        invalid addresses we found).
        """
        # If we got nothing or whitespace, return it as-is.
        if len(addressesString.strip()) == 0:
            return (addressesString, [], 0)

        validAddresses = []
        processedAddresses = []
        invalidCount = 0

        # get the user's address strings into a list; tolerate
        # commas or semicolons as separators
        addresses = [ address.strip() for address in \
                      addressesString.replace('?','').replace(';', ',').split(',') ]

        # build a list of all processed addresses, and all valid addresses
        for address in addresses:
            ea = EmailAddress.getEmailAddress(view, address)
            if ea is None:
                processedAddresses.append(address + '?')
                invalidCount += 1
            else:
                processedAddresses.append(unicode(ea))
                validAddresses.append(ea)

        # prepare the processed addresses return value
        processedResultString = ', '.join (processedAddresses)
        return (processedResultString, validAddresses, invalidCount)

    @classmethod
    def emailAddressesAreEqual(cls, emailAddressOne, emailAddressTwo):
        """
        This method tests whether two email addresses are the same.
        Addresses can be in the form john@jones.com or John Jones <john@jones.com>.

        The method strips off the username and <> brakets if they exist and
        just compares the actual email addresses for equality. It will not
        look to see if each address is RFC 822 compliant only that the strings
        match. Use C{EmailAddress.isValidEmailAddress} to test for validity.

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

        # See if an IMAP/POP account is configured:
        account = getCurrentMailAccount(view)
        if account is None or not account.replyToAddress or not account.replyToAddress.emailAddress:
            # No IMAP/POP set up, so check SMTP:
            account, replyTo = getCurrentSMTPAccount(view)
            if account is None or not account.fromAddress or not account.fromAddress.emailAddress:
                return None
            else:
                return account.fromAddress
        else:
            return account.replyToAddress


# Map from account type strings to account types

ACCOUNT_TYPES = {
    'POP': POPAccount,
    'SMTP': SMTPAccount,
    'IMAP': IMAPAccount,
}
